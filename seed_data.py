"""
Seed data script for RNRL TradeHub backend.

This script populates the database with realistic sample data for testing and demonstration.
Run this script after database initialization to add master data and sample records.
"""
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import (
    Organization, FinancialYear, User, Role, Permission,
    BusinessPartner, Address, SalesContract,
    Invoice, Payment, Commission, Dispute,
    GstRate, Location, CciTerm, CommissionStructure,
    MasterDataItem, StructuredTerm, Setting,
    EmailTemplate, DataRetentionPolicy
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_organizations(db: Session):
    """Create sample organizations."""
    print("Creating organizations...")
    orgs = [
        Organization(
            legal_name="RNRL Trading Company Pvt Ltd",
            display_name="RNRL Trading",
            pan="AAACR5555K",
            gstin="27AAACR5555K1Z5",
            address={
                "line1": "123 Trade Center",
                "line2": "Andheri East",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400069",
                "country": "India"
            },
            settings={"currency": "INR", "timezone": "Asia/Kolkata"},
            is_active=True
        )
    ]
    db.add_all(orgs)
    db.commit()
    print(f"✓ Created {len(orgs)} organization(s)")
    return orgs


def create_financial_years(db: Session, org: Organization):
    """Create financial years."""
    print("Creating financial years...")
    current_year = datetime.now().year
    fys = []
    
    # Create last year (closed)
    fy1 = FinancialYear(
        organization_id=org.id,
        year_code=f"{current_year-2}-{str(current_year-1)[-2:]}",
        start_date=datetime(current_year-2, 4, 1),
        end_date=datetime(current_year-1, 3, 31),
        assessment_year=f"{current_year-1}-{str(current_year)[-2:]}",
        is_active=False,
        is_closed=True,
        opening_balances={}
    )
    fys.append(fy1)
    
    # Create current year (active)
    fy2 = FinancialYear(
        organization_id=org.id,
        year_code=f"{current_year-1}-{str(current_year)[-2:]}",
        start_date=datetime(current_year-1, 4, 1),
        end_date=datetime(current_year, 3, 31),
        assessment_year=f"{current_year}-{str(current_year+1)[-2:]}",
        is_active=True,
        is_closed=False,
        opening_balances={}
    )
    fys.append(fy2)
    
    db.add_all(fys)
    db.commit()
    print(f"✓ Created {len(fys)} financial year(s)")
    return fys


def create_roles_and_permissions(db: Session):
    """Create roles with permissions."""
    print("Creating roles and permissions...")
    
    roles_data = [
        {
            "name": "Admin",
            "description": "Full system access",
            "permissions": {
                "Sales Contracts": {"create": True, "read": True, "update": True, "delete": True, "approve": True, "share": True},
                "Business Partners": {"create": True, "read": True, "update": True, "delete": True, "approve": True, "share": True},
                "Invoices": {"create": True, "read": True, "update": True, "delete": True, "approve": True, "share": True},
                "Payments": {"create": True, "read": True, "update": True, "delete": True, "approve": True, "share": True},
                "Commissions": {"create": True, "read": True, "update": True, "delete": True, "approve": True, "share": True},
                "Disputes": {"create": True, "read": True, "update": True, "delete": True, "approve": True, "share": True},
            }
        },
        {
            "name": "Sales",
            "description": "Sales team access",
            "permissions": {
                "Sales Contracts": {"create": True, "read": True, "update": True, "delete": False, "approve": False, "share": True},
                "Business Partners": {"create": True, "read": True, "update": True, "delete": False, "approve": False, "share": True},
                "Invoices": {"create": False, "read": True, "update": False, "delete": False, "approve": False, "share": False},
                "Payments": {"create": False, "read": True, "update": False, "delete": False, "approve": False, "share": False},
            }
        },
        {
            "name": "Accounts",
            "description": "Accounts team access",
            "permissions": {
                "Sales Contracts": {"create": False, "read": True, "update": False, "delete": False, "approve": True, "share": False},
                "Invoices": {"create": True, "read": True, "update": True, "delete": True, "approve": True, "share": True},
                "Payments": {"create": True, "read": True, "update": True, "delete": True, "approve": True, "share": True},
                "Commissions": {"create": True, "read": True, "update": True, "delete": True, "approve": True, "share": True},
            }
        },
    ]
    
    roles = []
    for role_data in roles_data:
        role = Role(
            name=role_data["name"],
            description=role_data["description"],
            is_active=True
        )
        db.add(role)
        db.flush()
        
        for module, perms in role_data["permissions"].items():
            permission = Permission(
                role_id=role.id,
                module=module,
                can_create=perms.get("create", False),
                can_read=perms.get("read", False),
                can_update=perms.get("update", False),
                can_delete=perms.get("delete", False),
                can_approve=perms.get("approve", False),
                can_share=perms.get("share", False)
            )
            db.add(permission)
        
        roles.append(role)
    
    db.commit()
    print(f"✓ Created {len(roles)} role(s) with permissions")
    return roles


def create_users(db: Session, roles: list):
    """Create sample users."""
    print("Creating users...")
    
    users_data = [
        {"name": "Admin User", "email": "admin@rnrl.com", "role": "Admin", "password": "admin123"},
        {"name": "Sales Manager", "email": "sales@rnrl.com", "role": "Sales", "password": "sales123"},
        {"name": "Accounts Manager", "email": "accounts@rnrl.com", "role": "Accounts", "password": "accounts123"},
    ]
    
    users = []
    role_map = {r.name: r for r in roles}
    
    for user_data in users_data:
        role = role_map.get(user_data["role"])
        user = User(
            name=user_data["name"],
            email=user_data["email"],
            password_hash=get_password_hash(user_data["password"]),
            role_id=role.id if role else None,
            role_name=user_data["role"],
            is_active=True
        )
        users.append(user)
    
    db.add_all(users)
    db.commit()
    print(f"✓ Created {len(users)} user(s)")
    print("  Login credentials:")
    for user_data in users_data:
        print(f"    {user_data['email']} / {user_data['password']}")
    return users


def create_gst_rates(db: Session):
    """Create GST rate master data."""
    print("Creating GST rates...")
    
    gst_rates = [
        GstRate(rate=0.0, description="Nil Rate", hsn_code="0000"),
        GstRate(rate=5.0, description="5% GST", hsn_code="5201"),
        GstRate(rate=12.0, description="12% GST", hsn_code="5202"),
        GstRate(rate=18.0, description="18% GST", hsn_code="5203"),
    ]
    
    db.add_all(gst_rates)
    db.commit()
    print(f"✓ Created {len(gst_rates)} GST rate(s)")
    return gst_rates


def create_locations(db: Session):
    """Create location master data."""
    print("Creating locations...")
    
    locations = [
        Location(country="India", state="Maharashtra", city="Mumbai"),
        Location(country="India", state="Maharashtra", city="Nagpur"),
        Location(country="India", state="Gujarat", city="Ahmedabad"),
        Location(country="India", state="Gujarat", city="Rajkot"),
        Location(country="India", state="Punjab", city="Ludhiana"),
        Location(country="India", state="Haryana", city="Sirsa"),
    ]
    
    db.add_all(locations)
    db.commit()
    print(f"✓ Created {len(locations)} location(s)")
    return locations


def create_commission_structures(db: Session):
    """Create commission structure templates."""
    print("Creating commission structures...")
    
    structures = [
        CommissionStructure(name="Standard 2%", type="PERCENTAGE", value=2.0),
        CommissionStructure(name="Premium 3%", type="PERCENTAGE", value=3.0),
        CommissionStructure(name="Fixed ₹50 per bale", type="PER_BALE", value=50.0),
        CommissionStructure(name="Fixed ₹75 per bale", type="PER_BALE", value=75.0),
    ]
    
    db.add_all(structures)
    db.commit()
    print(f"✓ Created {len(structures)} commission structure(s)")
    return structures


def create_cci_terms(db: Session):
    """Create CCI terms configuration."""
    print("Creating CCI terms...")
    
    cci_terms = [
        CciTerm(
            name="Standard CCI Terms 2024",
            contract_period_days=90,
            emd_payment_days=7,
            cash_discount_percentage=2.0,
            carrying_charge_tier1_days=30,
            carrying_charge_tier1_percent=0.5,
            carrying_charge_tier2_days=60,
            carrying_charge_tier2_percent=1.0,
            additional_deposit_percent=10.0,
            deposit_interest_percent=6.0,
            free_lifting_period_days=15,
            late_lifting_tier1_days=30,
            late_lifting_tier1_percent=0.25,
            late_lifting_tier2_days=60,
            late_lifting_tier2_percent=0.5,
            late_lifting_tier3_percent=1.0
        )
    ]
    
    db.add_all(cci_terms)
    db.commit()
    print(f"✓ Created {len(cci_terms)} CCI term(s)")
    return cci_terms


def create_master_data(db: Session):
    """Create master data items."""
    print("Creating master data items...")
    
    items = [
        # Cotton varieties
        MasterDataItem(category="variety", name="Shankar-6", code="S6", is_active=True),
        MasterDataItem(category="variety", name="MCU-5", code="MCU5", is_active=True),
        MasterDataItem(category="variety", name="DCH-32", code="DCH32", is_active=True),
        
        # Trade types
        MasterDataItem(category="trade_type", name="Spot", is_active=True),
        MasterDataItem(category="trade_type", name="Forward", is_active=True),
        MasterDataItem(category="trade_type", name="Ready", is_active=True),
        
        # Bargain types
        MasterDataItem(category="bargain_type", name="Ex-Gin", is_active=True),
        MasterDataItem(category="bargain_type", name="Delivery", is_active=True),
        
        # Quality parameters
        MasterDataItem(category="quality_parameter", name="Staple Length", code="STAPLE", is_active=True),
        MasterDataItem(category="quality_parameter", name="Micronaire", code="MIC", is_active=True),
        MasterDataItem(category="quality_parameter", name="Trash %", code="TRASH", is_active=True),
    ]
    
    db.add_all(items)
    db.commit()
    print(f"✓ Created {len(items)} master data item(s)")
    return items


def create_structured_terms(db: Session):
    """Create structured terms for payments, delivery, etc."""
    print("Creating structured terms...")
    
    terms = [
        # Payment terms
        StructuredTerm(category="payment", name="Immediate", days=0, description="Payment on delivery"),
        StructuredTerm(category="payment", name="7 Days", days=7, description="Payment within 7 days"),
        StructuredTerm(category="payment", name="15 Days", days=15, description="Payment within 15 days"),
        StructuredTerm(category="payment", name="30 Days", days=30, description="Payment within 30 days"),
        
        # Delivery terms
        StructuredTerm(category="delivery", name="Immediate", days=0, description="Immediate delivery"),
        StructuredTerm(category="delivery", name="7 Days", days=7, description="Delivery within 7 days"),
        StructuredTerm(category="delivery", name="15 Days", days=15, description="Delivery within 15 days"),
        StructuredTerm(category="delivery", name="30 Days", days=30, description="Delivery within 30 days"),
    ]
    
    db.add_all(terms)
    db.commit()
    print(f"✓ Created {len(terms)} structured term(s)")
    return terms


def create_business_partners(db: Session):
    """Create sample business partners."""
    print("Creating business partners...")
    
    partners_data = [
        {
            "bp_code": "BP001",
            "legal_name": "ABC Textiles Pvt Ltd",
            "organization": "ABC Group",
            "business_type": "BUYER",
            "status": "ACTIVE",
            "contact_person": "Rajesh Kumar",
            "contact_email": "rajesh@abctextiles.com",
            "contact_phone": "+91-9876543210",
            "address": {
                "line1": "456 Industrial Area",
                "line2": "Phase 2",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "pincode": "380015"
            },
            "pan": "AABCA1234F",
            "gstin": "24AABCA1234F1Z5",
        },
        {
            "bp_code": "BP002",
            "legal_name": "XYZ Cotton Traders",
            "organization": "XYZ Enterprises",
            "business_type": "SELLER",
            "status": "ACTIVE",
            "contact_person": "Suresh Patel",
            "contact_email": "suresh@xyzcotton.com",
            "contact_phone": "+91-9123456789",
            "address": {
                "line1": "789 Market Road",
                "line2": "",
                "city": "Rajkot",
                "state": "Gujarat",
                "pincode": "360001"
            },
            "pan": "AABCX5678K",
            "gstin": "24AABCX5678K1Z8",
        },
        {
            "bp_code": "BP003",
            "legal_name": "PQR Trading Company",
            "organization": "PQR Group",
            "business_type": "BOTH",
            "status": "ACTIVE",
            "contact_person": "Amit Shah",
            "contact_email": "amit@pqrtrading.com",
            "contact_phone": "+91-9988776655",
            "address": {
                "line1": "123 Commerce Street",
                "line2": "Near Railway Station",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001"
            },
            "pan": "AABCP9876M",
            "gstin": "27AABCP9876M1Z1",
        },
        {
            "bp_code": "AG001",
            "legal_name": "LMN Commission Agents",
            "organization": "LMN Services",
            "business_type": "AGENT",
            "status": "ACTIVE",
            "contact_person": "Vikram Singh",
            "contact_email": "vikram@lmnagents.com",
            "contact_phone": "+91-9876512345",
            "address": {
                "line1": "567 Agent Complex",
                "line2": "Market Yard",
                "city": "Ludhiana",
                "state": "Punjab",
                "pincode": "141001"
            },
            "pan": "AABCL4321N",
            "gstin": "03AABCL4321N1Z9",
        },
    ]
    
    partners = []
    for data in partners_data:
        addr = data.pop("address")
        partner = BusinessPartner(
            id=str(uuid.uuid4()),
            **data,
            address_line1=addr["line1"],
            address_line2=addr.get("line2", ""),
            city=addr["city"],
            state=addr["state"],
            pincode=addr["pincode"],
            country="India",
            kyc_due_date=datetime.now() + timedelta(days=365),
            bank_name="State Bank of India",
            bank_account_no="1234567890",
            bank_ifsc="SBIN0001234"
        )
        partners.append(partner)
    
    db.add_all(partners)
    db.commit()
    print(f"✓ Created {len(partners)} business partner(s)")
    return partners


def create_sales_contracts(db: Session, org: Organization, fy: FinancialYear, 
                           partners: list, gst_rates: list, comm_structures: list):
    """Create sample sales contracts."""
    print("Creating sales contracts...")
    
    buyers = [p for p in partners if p.business_type in ["BUYER", "BOTH"]]
    sellers = [p for p in partners if p.business_type in ["SELLER", "BOTH"]]
    agents = [p for p in partners if p.business_type == "AGENT"]
    
    contracts = []
    for i in range(5):
        buyer = buyers[i % len(buyers)]
        seller = sellers[i % len(sellers)]
        agent = agents[0] if agents else None
        
        contract = SalesContract(
            id=str(uuid.uuid4()),
            sc_no=f"SC/{fy.year_code}/{str(i+1).zfill(4)}",
            version=1,
            date=datetime.now() - timedelta(days=30-i*5),
            organization=org.display_name,
            financial_year=fy.year_code,
            client_id=buyer.id,
            client_name=buyer.legal_name,
            vendor_id=seller.id,
            vendor_name=seller.legal_name,
            agent_id=agent.id if agent else None,
            variety=["Shankar-6", "MCU-5", "DCH-32"][i % 3],
            quantity_bales=100 + i * 50,
            rate=5000.0 + i * 100,
            gst_rate_id=gst_rates[1].id,  # 5% GST
            buyer_commission_id=comm_structures[0].id,  # 2%
            seller_commission_id=comm_structures[0].id,  # 2%
            buyer_commission_gst_id=gst_rates[3].id,  # 18% GST
            seller_commission_gst_id=gst_rates[3].id,  # 18% GST
            trade_type="Spot" if i % 2 == 0 else "Forward",
            bargain_type="Ex-Gin",
            weightment_terms="As per standard practice",
            passing_terms="As per EATM standards",
            delivery_terms="15 Days",
            payment_terms="30 Days",
            location="Mumbai",
            quality_specs={
                "staple_length": {"min": 28, "max": 30},
                "micronaire": {"min": 3.5, "max": 4.5},
                "trash_percent": {"max": 3.0}
            },
            status="Active" if i < 3 else "Completed",
            cci_contract_no=f"CCI/{fy.year_code}/{str(i+1).zfill(4)}"
        )
        contracts.append(contract)
    
    db.add_all(contracts)
    db.commit()
    print(f"✓ Created {len(contracts)} sales contract(s)")
    return contracts


def create_invoices(db: Session, org: Organization, fy: FinancialYear, contracts: list):
    """Create sample invoices."""
    print("Creating invoices...")
    
    invoices = []
    for i, contract in enumerate(contracts[:4]):  # Create invoices for first 4 contracts
        amount = contract.quantity_bales * contract.rate * 1.05  # Including 5% GST
        invoice = Invoice(
            id=str(uuid.uuid4()),
            invoice_no=f"INV/{fy.year_code}/{str(i+1).zfill(5)}",
            organization_id=org.id,
            financial_year=fy.year_code,
            sales_contract_id=contract.id,
            date=contract.date + timedelta(days=5),
            amount=amount,
            status="Paid" if i < 2 else "Partially Paid" if i == 2 else "Unpaid"
        )
        invoices.append(invoice)
    
    db.add_all(invoices)
    db.commit()
    print(f"✓ Created {len(invoices)} invoice(s)")
    return invoices


def create_payments(db: Session, org: Organization, fy: FinancialYear, invoices: list):
    """Create sample payments."""
    print("Creating payments...")
    
    payments = []
    for i, invoice in enumerate(invoices[:3]):  # Create payments for first 3 invoices
        payment_amount = invoice.amount if i < 2 else invoice.amount * 0.5  # Full or partial
        payment = Payment(
            id=str(uuid.uuid4()),
            payment_id=f"PAY/{fy.year_code}/{str(i+1).zfill(5)}",
            organization_id=org.id,
            financial_year=fy.year_code,
            invoice_id=invoice.id,
            date=invoice.date + timedelta(days=15),
            amount=payment_amount,
            method="Bank Transfer"
        )
        payments.append(payment)
    
    db.add_all(payments)
    db.commit()
    print(f"✓ Created {len(payments)} payment(s)")
    return payments


def create_commissions(db: Session, org: Organization, fy: FinancialYear, contracts: list):
    """Create sample commissions."""
    print("Creating commissions...")
    
    commissions = []
    for i, contract in enumerate(contracts[:3]):  # Create commissions for first 3 contracts
        if contract.agent_id:
            commission_amount = contract.quantity_bales * contract.rate * 0.02  # 2% commission
            commission = Commission(
                id=str(uuid.uuid4()),
                commission_id=f"COM/{fy.year_code}/{str(i+1).zfill(5)}",
                organization_id=org.id,
                financial_year=fy.year_code,
                sales_contract_id=contract.id,
                agent="LMN Commission Agents",
                amount=commission_amount,
                status="Paid" if i == 0 else "Due"
            )
            commissions.append(commission)
    
    db.add_all(commissions)
    db.commit()
    print(f"✓ Created {len(commissions)} commission(s)")
    return commissions


def create_disputes(db: Session, org: Organization, fy: FinancialYear, contracts: list):
    """Create sample disputes."""
    print("Creating disputes...")
    
    disputes = []
    if len(contracts) >= 4:
        dispute = Dispute(
            id=str(uuid.uuid4()),
            dispute_id=f"DIS/{fy.year_code}/0001",
            organization_id=org.id,
            financial_year=fy.year_code,
            sales_contract_id=contracts[3].id,
            reason="Quality specifications not met. Micronaire values out of range.",
            status="Open",
            date_raised=datetime.now() - timedelta(days=5)
        )
        disputes.append(dispute)
    
    db.add_all(disputes)
    db.commit()
    print(f"✓ Created {len(disputes)} dispute(s)")
    return disputes


def create_settings(db: Session):
    """Create system settings."""
    print("Creating system settings...")
    
    settings = [
        Setting(
            category="system",
            key="company_name",
            value="RNRL TradeHub",
            value_type="string",
            description="Company display name",
            is_public=True,
            is_editable=True
        ),
        Setting(
            category="system",
            key="currency",
            value="INR",
            value_type="string",
            description="Default currency",
            is_public=True,
            is_editable=False
        ),
        Setting(
            category="email",
            key="smtp_host",
            value="smtp.gmail.com",
            value_type="string",
            description="SMTP server host",
            is_public=False,
            is_editable=True
        ),
        Setting(
            category="email",
            key="smtp_port",
            value="587",
            value_type="number",
            description="SMTP server port",
            is_public=False,
            is_editable=True
        ),
    ]
    
    db.add_all(settings)
    db.commit()
    print(f"✓ Created {len(settings)} setting(s)")
    return settings


def create_email_templates(db: Session):
    """Create email templates."""
    print("Creating email templates...")
    
    templates = [
        EmailTemplate(
            name="contract_created",
            category="notification",
            subject="New Sales Contract Created - {{sc_no}}",
            body_html="""
            <html>
            <body>
                <h2>Sales Contract Created</h2>
                <p>Dear {{client_name}},</p>
                <p>A new sales contract has been created:</p>
                <ul>
                    <li>Contract No: <strong>{{sc_no}}</strong></li>
                    <li>Date: {{date}}</li>
                    <li>Variety: {{variety}}</li>
                    <li>Quantity: {{quantity_bales}} bales</li>
                    <li>Rate: ₹{{rate}} per bale</li>
                </ul>
                <p>Best regards,<br/>RNRL TradeHub Team</p>
            </body>
            </html>
            """,
            body_text="Contract {{sc_no}} created on {{date}}",
            variables=["sc_no", "client_name", "date", "variety", "quantity_bales", "rate"],
            is_active=True,
            description="Notification sent when a new sales contract is created"
        ),
        EmailTemplate(
            name="invoice_generated",
            category="notification",
            subject="Invoice Generated - {{invoice_no}}",
            body_html="""
            <html>
            <body>
                <h2>Invoice Generated</h2>
                <p>Dear {{client_name}},</p>
                <p>Invoice has been generated for contract {{sc_no}}:</p>
                <ul>
                    <li>Invoice No: <strong>{{invoice_no}}</strong></li>
                    <li>Amount: ₹{{amount}}</li>
                    <li>Due Date: {{due_date}}</li>
                </ul>
                <p>Please process payment at your earliest convenience.</p>
                <p>Best regards,<br/>RNRL TradeHub Team</p>
            </body>
            </html>
            """,
            body_text="Invoice {{invoice_no}} for ₹{{amount}}",
            variables=["invoice_no", "client_name", "sc_no", "amount", "due_date"],
            is_active=True,
            description="Notification sent when an invoice is generated"
        ),
    ]
    
    db.add_all(templates)
    db.commit()
    print(f"✓ Created {len(templates)} email template(s)")
    return templates


def create_retention_policies(db: Session):
    """Create data retention policies."""
    print("Creating data retention policies...")
    
    policies = [
        DataRetentionPolicy(
            entity_type="sales_contract",
            retention_days=3650,  # 10 years
            archive_after_days=1825,  # 5 years
            delete_after_days=3650,
            policy_type="legal",
            description="Sales contracts must be retained for 10 years as per tax regulations",
            is_active=True
        ),
        DataRetentionPolicy(
            entity_type="invoice",
            retention_days=3650,  # 10 years
            archive_after_days=1825,
            delete_after_days=3650,
            policy_type="legal",
            description="Invoices must be retained for 10 years for tax and audit purposes",
            is_active=True
        ),
        DataRetentionPolicy(
            entity_type="payment",
            retention_days=2555,  # 7 years
            archive_after_days=1825,
            delete_after_days=2555,
            policy_type="legal",
            description="Payment records retention for 7 years",
            is_active=True
        ),
    ]
    
    db.add_all(policies)
    db.commit()
    print(f"✓ Created {len(policies)} retention policy(ies)")
    return policies


def main():
    """Main function to seed the database."""
    print("\n" + "="*60)
    print("RNRL TradeHub - Database Seeding")
    print("="*60 + "\n")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create master data
        orgs = create_organizations(db)
        org = orgs[0]
        
        fys = create_financial_years(db, org)
        fy = fys[1]  # Current year
        
        roles = create_roles_and_permissions(db)
        users = create_users(db, roles)
        
        gst_rates = create_gst_rates(db)
        locations = create_locations(db)
        comm_structures = create_commission_structures(db)
        cci_terms = create_cci_terms(db)
        
        master_data = create_master_data(db)
        structured_terms = create_structured_terms(db)
        settings = create_settings(db)
        
        # Create transactional data
        partners = create_business_partners(db)
        contracts = create_sales_contracts(db, org, fy, partners, gst_rates, comm_structures)
        invoices = create_invoices(db, org, fy, contracts)
        payments = create_payments(db, org, fy, invoices)
        commissions = create_commissions(db, org, fy, contracts)
        disputes = create_disputes(db, org, fy, contracts)
        
        # Create compliance data
        email_templates = create_email_templates(db)
        retention_policies = create_retention_policies(db)
        
        print("\n" + "="*60)
        print("✅ Database seeding completed successfully!")
        print("="*60)
        print("\nSummary:")
        print(f"  • {len(orgs)} Organization(s)")
        print(f"  • {len(fys)} Financial Year(s)")
        print(f"  • {len(roles)} Role(s)")
        print(f"  • {len(users)} User(s)")
        print(f"  • {len(partners)} Business Partner(s)")
        print(f"  • {len(contracts)} Sales Contract(s)")
        print(f"  • {len(invoices)} Invoice(s)")
        print(f"  • {len(payments)} Payment(s)")
        print(f"  • {len(commissions)} Commission(s)")
        print(f"  • {len(disputes)} Dispute(s)")
        print(f"  • {len(gst_rates)} GST Rate(s)")
        print(f"  • {len(locations)} Location(s)")
        print(f"  • {len(comm_structures)} Commission Structure(s)")
        print(f"  • {len(cci_terms)} CCI Term(s)")
        print(f"  • {len(master_data)} Master Data Item(s)")
        print(f"  • {len(structured_terms)} Structured Term(s)")
        print(f"  • {len(settings)} Setting(s)")
        print(f"  • {len(email_templates)} Email Template(s)")
        print(f"  • {len(retention_policies)} Retention Policy(ies)")
        
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
