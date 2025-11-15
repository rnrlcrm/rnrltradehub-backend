"""
Accounting & Ledger API Routes - Double-Entry Bookkeeping.

Provides endpoints for:
- Chart of accounts management
- Voucher creation and posting
- Ledger entry management
- Account balance queries
- Reconciliation
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import (
    ChartOfAccountsCreate, ChartOfAccountsResponse,
    VoucherCreate, VoucherUpdate, VoucherResponse, VoucherPost,
    LedgerEntryCreate, LedgerEntryResponse,
    ReconciliationCreate, ReconciliationResponse
)
from services.ledger_service import LedgerService
from models import ChartOfAccounts, Voucher, LedgerEntry, Reconciliation

router = APIRouter(prefix="/api/accounting", tags=["Accounting & Ledger"])


# ============================================================================
# CHART OF ACCOUNTS ENDPOINTS
# ============================================================================

@router.post("/accounts", response_model=ChartOfAccountsResponse)
def create_account(
    account: ChartOfAccountsCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Create new account in chart of accounts.
    
    Account types:
    - ASSET
    - LIABILITY
    - EQUITY
    - REVENUE
    - EXPENSE
    """
    try:
        new_account = LedgerService.create_account(
            db=db,
            account_data=account,
            user_id=user_id
        )
        return new_account
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts", response_model=List[ChartOfAccountsResponse])
def list_accounts(
    org_id: int,
    account_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all accounts in chart of accounts."""
    query = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.organization_id == org_id
    )
    
    if account_type:
        query = query.filter(ChartOfAccounts.account_type == account_type)
    if is_active is not None:
        query = query.filter(ChartOfAccounts.is_active == is_active)
    
    accounts = query.order_by(ChartOfAccounts.account_code).offset(skip).limit(limit).all()
    return accounts


@router.get("/accounts/{account_id}", response_model=ChartOfAccountsResponse)
def get_account(
    account_id: str,
    db: Session = Depends(get_db)
):
    """Get account by ID."""
    account = db.query(ChartOfAccounts).filter(ChartOfAccounts.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.get("/accounts/{account_id}/balance")
def get_account_balance(
    account_id: str,
    as_of_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get current balance for an account.
    
    Returns balance as of specific date if provided.
    """
    try:
        balance = LedgerService.get_account_balance(
            db=db,
            account_id=account_id,
            as_of_date=as_of_date
        )
        return {
            "account_id": account_id,
            "balance": balance,
            "as_of_date": as_of_date or datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# VOUCHER ENDPOINTS
# ============================================================================

@router.post("/vouchers", response_model=VoucherResponse)
def create_voucher(
    voucher: VoucherCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Create new voucher.
    
    Voucher types:
    - JOURNAL
    - PAYMENT
    - RECEIPT
    - CONTRA
    - SALES
    - PURCHASE
    - CREDIT_NOTE
    - DEBIT_NOTE
    """
    try:
        new_voucher = LedgerService.create_voucher(
            db=db,
            voucher_data=voucher,
            user_id=user_id
        )
        return new_voucher
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vouchers", response_model=List[VoucherResponse])
def list_vouchers(
    org_id: int,
    fy: str,
    voucher_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List vouchers with filters."""
    query = db.query(Voucher).filter(
        Voucher.organization_id == org_id,
        Voucher.financial_year == fy
    )
    
    if voucher_type:
        query = query.filter(Voucher.voucher_type == voucher_type)
    if status:
        query = query.filter(Voucher.status == status)
    
    vouchers = query.order_by(Voucher.voucher_date.desc()).offset(skip).limit(limit).all()
    return vouchers


@router.get("/vouchers/{voucher_id}", response_model=VoucherResponse)
def get_voucher(
    voucher_id: str,
    db: Session = Depends(get_db)
):
    """Get voucher by ID."""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    return voucher


@router.put("/vouchers/{voucher_id}", response_model=VoucherResponse)
def update_voucher(
    voucher_id: str,
    voucher_update: VoucherUpdate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Update voucher (only DRAFT vouchers can be updated)."""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    if voucher.status != 'DRAFT':
        raise HTTPException(status_code=400, detail=f"Cannot update {voucher.status} voucher")
    
    update_data = voucher_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(voucher, field):
            setattr(voucher, field, value)
    
    db.commit()
    db.refresh(voucher)
    return voucher


@router.post("/vouchers/{voucher_id}/post")
def post_voucher(
    voucher_id: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Post voucher (DRAFT → POSTED).
    
    Validates double-entry balance before posting.
    Posts all associated ledger entries.
    """
    try:
        voucher = LedgerService.post_voucher(
            db=db,
            voucher_id=voucher_id,
            user_id=user_id
        )
        return {
            "message": "Voucher posted successfully",
            "voucher_id": voucher_id,
            "voucher_number": voucher.voucher_number,
            "status": voucher.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LEDGER ENTRY ENDPOINTS
# ============================================================================

@router.post("/ledger-entries", response_model=LedgerEntryResponse)
def create_ledger_entry(
    entry: LedgerEntryCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Add ledger entry to a voucher.
    
    Entry types:
    - DEBIT
    - CREDIT
    """
    try:
        new_entry = LedgerService.add_ledger_entry(
            db=db,
            entry_data=entry,
            user_id=user_id
        )
        return new_entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ledger-entries", response_model=List[LedgerEntryResponse])
def list_ledger_entries(
    org_id: int,
    fy: str,
    account_id: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List ledger entries with filters."""
    query = db.query(LedgerEntry).filter(
        LedgerEntry.organization_id == org_id,
        LedgerEntry.financial_year == fy
    )
    
    if account_id:
        query = query.filter(LedgerEntry.account_id == account_id)
    if from_date:
        query = query.filter(LedgerEntry.transaction_date >= from_date)
    if to_date:
        query = query.filter(LedgerEntry.transaction_date <= to_date)
    
    entries = query.order_by(LedgerEntry.transaction_date.desc()).offset(skip).limit(limit).all()
    return entries


@router.get("/ledger-entries/{entry_id}", response_model=LedgerEntryResponse)
def get_ledger_entry(
    entry_id: str,
    db: Session = Depends(get_db)
):
    """Get ledger entry by ID."""
    entry = db.query(LedgerEntry).filter(LedgerEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Ledger entry not found")
    return entry


@router.post("/ledger-entries/{entry_id}/reverse")
def reverse_entry(
    entry_id: str,
    reason: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Reverse a posted ledger entry."""
    try:
        entry = LedgerService.reverse_entry(
            db=db,
            entry_id=entry_id,
            reason=reason,
            user_id=user_id
        )
        return {
            "message": "Entry reversed successfully",
            "entry_id": entry_id,
            "entry_number": entry.entry_number,
            "status": entry.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ledger/by-account/{account_id}", response_model=List[LedgerEntryResponse])
def get_ledger_by_account(
    account_id: str,
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get ledger entries for a specific account."""
    entries = LedgerService.get_ledger_by_account(
        db=db,
        account_id=account_id,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit
    )
    return entries


# ============================================================================
# RECONCILIATION ENDPOINTS
# ============================================================================

@router.post("/reconciliations", response_model=ReconciliationResponse)
def create_reconciliation(
    reconciliation: ReconciliationCreate,
    db: Session = Depends(get_db)
):
    """Create new bank/ledger reconciliation."""
    from models import Reconciliation
    from uuid import uuid4
    
    new_recon = Reconciliation(
        id=str(uuid4()),
        organization_id=reconciliation.organization_id,
        financial_year=reconciliation.financial_year,
        reconciliation_date=reconciliation.reconciliation_date,
        account_id=reconciliation.account_id,
        book_balance=reconciliation.book_balance,
        bank_balance=reconciliation.bank_balance,
        difference=reconciliation.difference,
        reconciled_items=reconciliation.reconciled_items or {},
        unmatched_items=reconciliation.unmatched_items or {},
        notes=reconciliation.notes,
        status='IN_PROGRESS',
        performed_by=reconciliation.performed_by
    )
    
    db.add(new_recon)
    db.commit()
    db.refresh(new_recon)
    
    return new_recon


@router.get("/reconciliations", response_model=List[ReconciliationResponse])
def list_reconciliations(
    org_id: int,
    fy: str,
    account_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List reconciliations with filters."""
    query = db.query(Reconciliation).filter(
        Reconciliation.organization_id == org_id,
        Reconciliation.financial_year == fy
    )
    
    if account_id:
        query = query.filter(Reconciliation.account_id == account_id)
    if status:
        query = query.filter(Reconciliation.status == status)
    
    reconciliations = query.order_by(
        Reconciliation.reconciliation_date.desc()
    ).offset(skip).limit(limit).all()
    
    return reconciliations


# ============================================================================
# REPORTING ENDPOINTS
# ============================================================================

@router.get("/trial-balance")
def get_trial_balance(
    org_id: int,
    fy: str,
    as_of_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get trial balance report.
    
    Shows debit and credit balances for all accounts.
    """
    from sqlalchemy import func
    
    # Get all accounts
    accounts = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.organization_id == org_id,
        ChartOfAccounts.is_active == True
    ).all()
    
    trial_balance = []
    total_debit = 0.0
    total_credit = 0.0
    
    for account in accounts:
        balance = LedgerService.get_account_balance(
            db=db,
            account_id=account.id,
            as_of_date=as_of_date
        )
        
        if balance != 0:
            is_debit_balance = balance > 0
            abs_balance = abs(balance)
            
            trial_balance.append({
                "account_code": account.account_code,
                "account_name": account.account_name,
                "account_type": account.account_type,
                "debit": abs_balance if is_debit_balance else 0,
                "credit": abs_balance if not is_debit_balance else 0
            })
            
            if is_debit_balance:
                total_debit += abs_balance
            else:
                total_credit += abs_balance
    
    return {
        "organization_id": org_id,
        "financial_year": fy,
        "as_of_date": as_of_date or datetime.utcnow(),
        "accounts": trial_balance,
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "difference": round(total_debit - total_credit, 2)
    }
