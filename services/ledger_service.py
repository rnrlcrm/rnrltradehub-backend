"""
Ledger Service - Business logic for double-entry accounting.

Handles chart of accounts, ledger entries, vouchers, and reconciliation.
All financial transactions follow double-entry bookkeeping principles.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from models import (
    ChartOfAccounts, LedgerEntry, Voucher, Reconciliation,
    SalesContract, Invoice, Payment, AuditLog
)
from schemas import (
    ChartOfAccountsCreate, LedgerEntryCreate,
    VoucherCreate, VoucherUpdate, VoucherPost,
    ReconciliationCreate
)


class LedgerService:
    """Service for managing double-entry accounting."""

    @staticmethod
    def generate_account_code(db: Session, org_id: int, account_type: str) -> str:
        """Generate unique account code based on type."""
        type_prefixes = {
            'ASSET': '1',
            'LIABILITY': '2',
            'EQUITY': '3',
            'REVENUE': '4',
            'EXPENSE': '5'
        }
        prefix = type_prefixes.get(account_type, '9')
        
        count = db.query(ChartOfAccounts).filter(
            and_(
                ChartOfAccounts.organization_id == org_id,
                ChartOfAccounts.account_code.like(f"{prefix}%")
            )
        ).count()
        
        return f"{prefix}{org_id:03d}{(count + 1):04d}"

    @staticmethod
    def create_account(
        db: Session,
        account_data: ChartOfAccountsCreate,
        user_id: int
    ) -> ChartOfAccounts:
        """Create new account in chart of accounts."""
        # Validate parent account if provided
        if account_data.parent_account_id:
            parent = db.query(ChartOfAccounts).filter(
                ChartOfAccounts.id == account_data.parent_account_id
            ).first()
            if not parent:
                raise ValueError(f"Parent account {account_data.parent_account_id} not found")
            level = parent.level + 1
        else:
            level = 1

        # Generate account code
        account_code = LedgerService.generate_account_code(
            db,
            account_data.organization_id,
            account_data.account_type
        )

        account = ChartOfAccounts(
            id=str(uuid4()),
            account_code=account_code,
            account_name=account_data.account_name,
            organization_id=account_data.organization_id,
            account_type=account_data.account_type,
            account_subtype=account_data.account_subtype,
            parent_account_id=account_data.parent_account_id,
            level=level,
            description=account_data.description,
            is_active=True,
            is_system_account=False
        )

        db.add(account)

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Accountant",
            module="Accounting",
            action="CREATE",
            details=f"Created account {account_code} - {account_data.account_name}"
        )
        db.add(audit)

        db.commit()
        db.refresh(account)

        return account

    @staticmethod
    def generate_voucher_number(db: Session, org_id: int, fy: str, voucher_type: str) -> str:
        """Generate unique voucher number."""
        type_prefixes = {
            'JOURNAL': 'JV',
            'PAYMENT': 'PV',
            'RECEIPT': 'RV',
            'CONTRA': 'CV',
            'SALES': 'SV',
            'PURCHASE': 'PUV',
            'CREDIT_NOTE': 'CN',
            'DEBIT_NOTE': 'DN'
        }
        prefix = f"{type_prefixes.get(voucher_type, 'VO')}-{fy[-2:]}-{org_id}"
        
        count = db.query(Voucher).filter(
            and_(
                Voucher.organization_id == org_id,
                Voucher.financial_year == fy,
                Voucher.voucher_type == voucher_type,
                Voucher.voucher_number.like(f"{prefix}%")
            )
        ).count()
        
        return f"{prefix}-{(count + 1):05d}"

    @staticmethod
    def generate_entry_number(db: Session, org_id: int, fy: str) -> str:
        """Generate unique ledger entry number."""
        prefix = f"LE-{fy[-2:]}-{org_id}"
        count = db.query(LedgerEntry).filter(
            and_(
                LedgerEntry.organization_id == org_id,
                LedgerEntry.financial_year == fy,
                LedgerEntry.entry_number.like(f"{prefix}%")
            )
        ).count()
        return f"{prefix}-{(count + 1):06d}"

    @staticmethod
    def create_voucher(
        db: Session,
        voucher_data: VoucherCreate,
        user_id: int
    ) -> Voucher:
        """Create new voucher."""
        # Generate voucher number
        voucher_number = LedgerService.generate_voucher_number(
            db,
            voucher_data.organization_id,
            voucher_data.financial_year,
            voucher_data.voucher_type
        )

        voucher = Voucher(
            id=str(uuid4()),
            voucher_number=voucher_number,
            organization_id=voucher_data.organization_id,
            financial_year=voucher_data.financial_year,
            voucher_type=voucher_data.voucher_type,
            voucher_date=voucher_data.voucher_date,
            reference_number=voucher_data.reference_number,
            reference_date=voucher_data.reference_date,
            narration=voucher_data.narration,
            status='DRAFT',
            debit_total=0,
            credit_total=0,
            created_by=user_id
        )

        db.add(voucher)

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Accountant",
            module="Accounting",
            action="CREATE",
            details=f"Created {voucher_data.voucher_type} voucher {voucher_number}"
        )
        db.add(audit)

        db.commit()
        db.refresh(voucher)

        return voucher

    @staticmethod
    def add_ledger_entry(
        db: Session,
        entry_data: LedgerEntryCreate,
        user_id: int
    ) -> LedgerEntry:
        """Add ledger entry to a voucher."""
        # Validate account
        account = db.query(ChartOfAccounts).filter(
            and_(
                ChartOfAccounts.id == entry_data.account_id,
                ChartOfAccounts.is_active == True
            )
        ).first()
        if not account:
            raise ValueError(f"Invalid or inactive account {entry_data.account_id}")

        # Validate voucher if provided
        if entry_data.voucher_id:
            voucher = db.query(Voucher).filter(
                Voucher.id == entry_data.voucher_id
            ).first()
            if not voucher:
                raise ValueError(f"Voucher {entry_data.voucher_id} not found")
            if voucher.status != 'DRAFT':
                raise ValueError(f"Cannot add entries to {voucher.status} voucher")

        # Generate entry number
        entry_number = LedgerService.generate_entry_number(
            db,
            entry_data.organization_id,
            entry_data.financial_year
        )

        entry = LedgerEntry(
            id=str(uuid4()),
            entry_number=entry_number,
            organization_id=entry_data.organization_id,
            financial_year=entry_data.financial_year,
            transaction_date=entry_data.transaction_date,
            transaction_type=entry_data.transaction_type,
            source_type=entry_data.source_type,
            source_id=entry_data.source_id,
            voucher_id=entry_data.voucher_id,
            account_id=entry_data.account_id,
            entry_type=entry_data.entry_type,
            amount=entry_data.amount,
            party_type=entry_data.party_type,
            party_id=entry_data.party_id,
            narration=entry_data.narration,
            status='DRAFT'
        )

        db.add(entry)

        # Update voucher totals if linked
        if entry_data.voucher_id:
            if entry_data.entry_type == 'DEBIT':
                voucher.debit_total += entry_data.amount
            else:
                voucher.credit_total += entry_data.amount

        db.commit()
        db.refresh(entry)

        return entry

    @staticmethod
    def post_voucher(
        db: Session,
        voucher_id: str,
        user_id: int
    ) -> Voucher:
        """
        Post voucher and all its entries.
        
        Validates double-entry balance before posting.
        """
        voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
        if not voucher:
            raise ValueError(f"Voucher {voucher_id} not found")

        if voucher.status != 'DRAFT':
            raise ValueError(f"Voucher is already {voucher.status}")

        # Verify double-entry balance
        if abs(voucher.debit_total - voucher.credit_total) > 0.01:
            raise ValueError(
                f"Voucher not balanced: Debit={voucher.debit_total}, "
                f"Credit={voucher.credit_total}"
            )

        # Get all entries for this voucher
        entries = db.query(LedgerEntry).filter(
            LedgerEntry.voucher_id == voucher_id
        ).all()

        if not entries:
            raise ValueError("Cannot post voucher with no entries")

        # Post voucher
        voucher.status = 'POSTED'
        voucher.posted_by = user_id
        voucher.posted_at = datetime.utcnow()

        # Post all entries
        for entry in entries:
            entry.status = 'POSTED'
            entry.posted_by = user_id
            entry.posted_at = datetime.utcnow()

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Accountant",
            module="Accounting",
            action="POST_VOUCHER",
            details=f"Posted voucher {voucher.voucher_number} with {len(entries)} entries"
        )
        db.add(audit)

        db.commit()
        db.refresh(voucher)

        return voucher

    @staticmethod
    def auto_post_transaction(
        db: Session,
        source_type: str,
        source_id: str,
        org_id: int,
        fy: str,
        entries: List[Tuple[str, str, float, str]],  # (account_id, entry_type, amount, narration)
        user_id: int,
        narration: str = ""
    ) -> Voucher:
        """
        Auto-post transaction from source (contract, payment, etc.).
        
        Creates voucher and posts entries in one operation.
        Used by other services to automatically create accounting entries.
        """
        # Map source type to voucher type
        source_to_voucher = {
            'SALES_CONTRACT': 'SALES',
            'INVOICE': 'SALES',
            'PAYMENT': 'RECEIPT',
            'DISPUTE_RESOLUTION': 'JOURNAL'
        }
        voucher_type = source_to_voucher.get(source_type, 'JOURNAL')

        # Create voucher
        voucher_data = VoucherCreate(
            organization_id=org_id,
            financial_year=fy,
            voucher_type=voucher_type,
            voucher_date=datetime.utcnow(),
            narration=narration or f"Auto-posted from {source_type} {source_id}"
        )
        voucher = LedgerService.create_voucher(db, voucher_data, user_id)

        # Add entries
        for account_id, entry_type, amount, entry_narration in entries:
            entry_data = LedgerEntryCreate(
                organization_id=org_id,
                financial_year=fy,
                transaction_date=datetime.utcnow(),
                transaction_type=source_type,
                source_type=source_type,
                source_id=source_id,
                voucher_id=voucher.id,
                account_id=account_id,
                entry_type=entry_type,
                amount=amount,
                narration=entry_narration
            )
            LedgerService.add_ledger_entry(db, entry_data, user_id)

        # Refresh voucher to get updated totals
        db.refresh(voucher)

        # Post voucher
        voucher = LedgerService.post_voucher(db, voucher.id, user_id)

        return voucher

    @staticmethod
    def get_account_balance(
        db: Session,
        account_id: str,
        as_of_date: Optional[datetime] = None
    ) -> float:
        """Calculate account balance as of a specific date."""
        query = db.query(
            func.sum(
                func.case(
                    (LedgerEntry.entry_type == 'DEBIT', LedgerEntry.amount),
                    else_=-LedgerEntry.amount
                )
            )
        ).filter(
            and_(
                LedgerEntry.account_id == account_id,
                LedgerEntry.status == 'POSTED'
            )
        )

        if as_of_date:
            query = query.filter(LedgerEntry.transaction_date <= as_of_date)

        balance = query.scalar() or 0.0
        return balance

    @staticmethod
    def get_ledger_by_account(
        db: Session,
        account_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[LedgerEntry]:
        """Get ledger entries for an account with date filters."""
        query = db.query(LedgerEntry).filter(
            and_(
                LedgerEntry.account_id == account_id,
                LedgerEntry.status == 'POSTED'
            )
        )

        if from_date:
            query = query.filter(LedgerEntry.transaction_date >= from_date)
        if to_date:
            query = query.filter(LedgerEntry.transaction_date <= to_date)

        return query.order_by(
            LedgerEntry.transaction_date.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def reverse_entry(
        db: Session,
        entry_id: str,
        reason: str,
        user_id: int
    ) -> LedgerEntry:
        """Reverse a posted ledger entry."""
        entry = db.query(LedgerEntry).filter(LedgerEntry.id == entry_id).first()
        if not entry:
            raise ValueError(f"Entry {entry_id} not found")

        if entry.status != 'POSTED':
            raise ValueError(f"Can only reverse POSTED entries")

        # Mark as reversed
        entry.status = 'REVERSED'
        entry.reversed_by = user_id
        entry.reversed_at = datetime.utcnow()
        entry.reversal_reason = reason

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Accountant",
            module="Accounting",
            action="REVERSE_ENTRY",
            details=f"Reversed entry {entry.entry_number}",
            reason=reason
        )
        db.add(audit)

        db.commit()
        db.refresh(entry)

        return entry
