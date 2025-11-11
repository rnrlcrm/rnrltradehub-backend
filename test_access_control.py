"""
Unit tests for access control functionality.

Tests cover:
- User type based data filtering
- Sub-user permission inheritance
- Sub-user limit enforcement
- Business partner ID resolution
- Contract access validation
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Import models and utilities
from database import Base
import models
from access_control import (
    get_effective_business_partner_id,
    check_contract_access,
    validate_sub_user_limit,
    filter_contracts_by_user_type,
    filter_invoices_by_user_type,
    get_portal_url
)


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_business_partners(db_session):
    """Create sample business partners for testing."""
    client_bp = models.BusinessPartner(
        id="bp-client-001",
        bp_code="CLIENT001",
        legal_name="Client Company Ltd",
        organization="Client Org",
        business_type="BUYER",
        status="ACTIVE",
        contact_person="John Client",
        contact_email="client@example.com",
        contact_phone="+1234567890",
        address_line1="123 Client St",
        city="Client City",
        state="Client State",
        pincode="12345",
        country="USA",
        pan="CLIENTPAN01"
    )
    
    vendor_bp = models.BusinessPartner(
        id="bp-vendor-001",
        bp_code="VENDOR001",
        legal_name="Vendor Company Ltd",
        organization="Vendor Org",
        business_type="SELLER",
        status="ACTIVE",
        contact_person="Jane Vendor",
        contact_email="vendor@example.com",
        contact_phone="+0987654321",
        address_line1="456 Vendor Ave",
        city="Vendor City",
        state="Vendor State",
        pincode="54321",
        country="USA",
        pan="VENDORPAN01"
    )
    
    db_session.add(client_bp)
    db_session.add(vendor_bp)
    db_session.commit()
    
    return {"client": client_bp, "vendor": vendor_bp}


@pytest.fixture
def sample_users(db_session, sample_business_partners):
    """Create sample users for testing."""
    # Back office user
    back_office_user = models.User(
        id=1,
        name="Admin User",
        email="admin@example.com",
        password_hash="hashed_password",
        user_type="BACK_OFFICE",
        is_parent=True,
        is_active=True
    )
    
    # Client parent user
    client_parent = models.User(
        id=2,
        name="Client Parent",
        email="client.parent@example.com",
        password_hash="hashed_password",
        user_type="CLIENT",
        business_partner_id=sample_business_partners["client"].id,
        is_parent=True,
        is_active=True
    )
    
    # Client sub-user
    client_sub = models.User(
        id=3,
        name="Client Sub",
        email="client.sub@example.com",
        password_hash="hashed_password",
        user_type="CLIENT",
        business_partner_id=sample_business_partners["client"].id,
        parent_user_id=2,
        is_parent=False,
        is_active=True
    )
    
    # Vendor parent user
    vendor_parent = models.User(
        id=4,
        name="Vendor Parent",
        email="vendor.parent@example.com",
        password_hash="hashed_password",
        user_type="VENDOR",
        business_partner_id=sample_business_partners["vendor"].id,
        is_parent=True,
        is_active=True
    )
    
    db_session.add_all([back_office_user, client_parent, client_sub, vendor_parent])
    db_session.commit()
    
    return {
        "back_office": back_office_user,
        "client_parent": client_parent,
        "client_sub": client_sub,
        "vendor_parent": vendor_parent
    }


@pytest.fixture
def sample_contracts(db_session, sample_business_partners):
    """Create sample sales contracts for testing."""
    contract1 = models.SalesContract(
        id="contract-001",
        sc_no="SC001",
        version=1,
        date=datetime.utcnow(),
        organization="Test Org",
        financial_year="2023-24",
        client_id=sample_business_partners["client"].id,
        client_name="Client Company Ltd",
        vendor_id=sample_business_partners["vendor"].id,
        vendor_name="Vendor Company Ltd",
        variety="Cotton",
        quantity_bales=100,
        rate=5000.0,
        trade_type="Domestic",
        bargain_type="Fixed",
        weightment_terms="As per agreement",
        passing_terms="Standard",
        delivery_terms="FOB",
        payment_terms="30 days",
        location="Mumbai",
        status="Active"
    )
    
    contract2 = models.SalesContract(
        id="contract-002",
        sc_no="SC002",
        version=1,
        date=datetime.utcnow(),
        organization="Test Org",
        financial_year="2023-24",
        client_id=sample_business_partners["vendor"].id,  # Reverse: vendor is client
        client_name="Vendor Company Ltd",
        vendor_id=sample_business_partners["client"].id,  # Reverse: client is vendor
        vendor_name="Client Company Ltd",
        variety="Cotton",
        quantity_bales=50,
        rate=5500.0,
        trade_type="Domestic",
        bargain_type="Fixed",
        weightment_terms="As per agreement",
        passing_terms="Standard",
        delivery_terms="FOB",
        payment_terms="30 days",
        location="Delhi",
        status="Active"
    )
    
    db_session.add_all([contract1, contract2])
    db_session.commit()
    
    return [contract1, contract2]


class TestGetEffectiveBusinessPartnerId:
    """Test get_effective_business_partner_id function."""
    
    def test_back_office_user_returns_none(self, db_session, sample_users):
        """Back office users should return None for business partner ID."""
        bp_id = get_effective_business_partner_id(sample_users["back_office"], db_session)
        assert bp_id is None
    
    def test_parent_user_returns_own_bp_id(self, db_session, sample_users):
        """Parent users should return their own business partner ID."""
        bp_id = get_effective_business_partner_id(sample_users["client_parent"], db_session)
        assert bp_id == sample_users["client_parent"].business_partner_id
    
    def test_sub_user_inherits_parent_bp_id(self, db_session, sample_users):
        """Sub-users should inherit their parent's business partner ID."""
        bp_id = get_effective_business_partner_id(sample_users["client_sub"], db_session)
        assert bp_id == sample_users["client_parent"].business_partner_id


class TestCheckContractAccess:
    """Test check_contract_access function."""
    
    def test_back_office_has_access_to_all(self, db_session, sample_users, sample_contracts):
        """Back office users should have access to all contracts."""
        assert check_contract_access(sample_users["back_office"], sample_contracts[0], db_session) == True
        assert check_contract_access(sample_users["back_office"], sample_contracts[1], db_session) == True
    
    def test_client_has_access_as_buyer(self, db_session, sample_users, sample_contracts):
        """Client users should have access to contracts where they are the buyer."""
        # Contract 1: client is buyer
        assert check_contract_access(sample_users["client_parent"], sample_contracts[0], db_session) == True
        # Contract 2: client is seller (no access)
        assert check_contract_access(sample_users["client_parent"], sample_contracts[1], db_session) == False
    
    def test_vendor_has_access_as_seller(self, db_session, sample_users, sample_contracts):
        """Vendor users should have access to contracts where they are the seller."""
        # Contract 1: vendor is seller
        assert check_contract_access(sample_users["vendor_parent"], sample_contracts[0], db_session) == True
        # Contract 2: vendor is buyer (no access)
        assert check_contract_access(sample_users["vendor_parent"], sample_contracts[1], db_session) == False
    
    def test_sub_user_inherits_parent_access(self, db_session, sample_users, sample_contracts):
        """Sub-users should have same access as their parent."""
        # Parent access
        parent_access_1 = check_contract_access(sample_users["client_parent"], sample_contracts[0], db_session)
        parent_access_2 = check_contract_access(sample_users["client_parent"], sample_contracts[1], db_session)
        
        # Sub-user access
        sub_access_1 = check_contract_access(sample_users["client_sub"], sample_contracts[0], db_session)
        sub_access_2 = check_contract_access(sample_users["client_sub"], sample_contracts[1], db_session)
        
        assert parent_access_1 == sub_access_1
        assert parent_access_2 == sub_access_2


class TestValidateSubUserLimit:
    """Test validate_sub_user_limit function."""
    
    def test_parent_can_create_first_sub_user(self, db_session, sample_users):
        """Parent user with 1 sub-user should be allowed to create another."""
        # Client parent has 1 sub-user already
        # Should not raise exception
        try:
            validate_sub_user_limit(sample_users["client_parent"], db_session)
        except Exception as e:
            pytest.fail(f"Should not raise exception: {e}")
    
    def test_parent_cannot_exceed_limit(self, db_session, sample_users):
        """Parent user with 2 sub-users should not be allowed to create more."""
        # Create a second sub-user
        sub_user_2 = models.User(
            id=10,
            name="Client Sub 2",
            email="client.sub2@example.com",
            password_hash="hashed_password",
            user_type="CLIENT",
            business_partner_id=sample_users["client_parent"].business_partner_id,
            parent_user_id=sample_users["client_parent"].id,
            is_parent=False,
            is_active=True
        )
        db_session.add(sub_user_2)
        db_session.commit()
        
        # Now should raise exception
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_sub_user_limit(sample_users["client_parent"], db_session)
        
        assert exc_info.value.status_code == 400
        assert "Maximum 2 sub-users" in str(exc_info.value.detail)
    
    def test_sub_user_cannot_create_sub_users(self, db_session, sample_users):
        """Sub-users should not be allowed to create other sub-users."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_sub_user_limit(sample_users["client_sub"], db_session)
        
        assert exc_info.value.status_code == 403
        assert "cannot create other sub-users" in str(exc_info.value.detail)


class TestFilterContractsByUserType:
    """Test filter_contracts_by_user_type function."""
    
    def test_back_office_sees_all_contracts(self, db_session, sample_users, sample_contracts):
        """Back office users should see all contracts."""
        query = db_session.query(models.SalesContract)
        filtered_query = filter_contracts_by_user_type(query, sample_users["back_office"], db_session)
        results = filtered_query.all()
        
        assert len(results) == 2
    
    def test_client_sees_only_buyer_contracts(self, db_session, sample_users, sample_contracts):
        """Client users should only see contracts where they are the buyer."""
        query = db_session.query(models.SalesContract)
        filtered_query = filter_contracts_by_user_type(query, sample_users["client_parent"], db_session)
        results = filtered_query.all()
        
        assert len(results) == 1
        assert results[0].client_id == sample_users["client_parent"].business_partner_id
    
    def test_vendor_sees_only_seller_contracts(self, db_session, sample_users, sample_contracts):
        """Vendor users should only see contracts where they are the seller."""
        query = db_session.query(models.SalesContract)
        filtered_query = filter_contracts_by_user_type(query, sample_users["vendor_parent"], db_session)
        results = filtered_query.all()
        
        assert len(results) == 1
        assert results[0].vendor_id == sample_users["vendor_parent"].business_partner_id
    
    def test_sub_user_sees_same_as_parent(self, db_session, sample_users, sample_contracts):
        """Sub-users should see the same contracts as their parent."""
        query_parent = db_session.query(models.SalesContract)
        filtered_parent = filter_contracts_by_user_type(query_parent, sample_users["client_parent"], db_session)
        parent_results = filtered_parent.all()
        
        query_sub = db_session.query(models.SalesContract)
        filtered_sub = filter_contracts_by_user_type(query_sub, sample_users["client_sub"], db_session)
        sub_results = filtered_sub.all()
        
        assert len(parent_results) == len(sub_results)
        assert set([c.id for c in parent_results]) == set([c.id for c in sub_results])


class TestGetPortalUrl:
    """Test get_portal_url function."""
    
    def test_back_office_portal_url(self):
        """Back office users should get back office portal URL."""
        url = get_portal_url("BACK_OFFICE")
        assert url == "/back-office/dashboard"
    
    def test_client_portal_url(self):
        """Client users should get client portal URL."""
        url = get_portal_url("CLIENT")
        assert url == "/client/dashboard"
    
    def test_vendor_portal_url(self):
        """Vendor users should get vendor portal URL."""
        url = get_portal_url("VENDOR")
        assert url == "/vendor/dashboard"
    
    def test_invalid_user_type_returns_root(self):
        """Invalid user types should return root URL."""
        url = get_portal_url("INVALID")
        assert url == "/"


class TestDataIsolation:
    """Integration tests for complete data isolation between user types."""
    
    def test_client_cannot_see_vendor_data(self, db_session, sample_users, sample_contracts):
        """Client users should not see contracts where they are the vendor."""
        query = db_session.query(models.SalesContract)
        filtered_query = filter_contracts_by_user_type(query, sample_users["client_parent"], db_session)
        results = filtered_query.all()
        
        # Should only see contract where they are client (contract 1)
        # Should NOT see contract where they are vendor (contract 2)
        assert len(results) == 1
        assert results[0].id == "contract-001"
        assert results[0].client_id == sample_users["client_parent"].business_partner_id
    
    def test_vendor_cannot_see_client_data(self, db_session, sample_users, sample_contracts):
        """Vendor users should not see contracts where they are the client."""
        query = db_session.query(models.SalesContract)
        filtered_query = filter_contracts_by_user_type(query, sample_users["vendor_parent"], db_session)
        results = filtered_query.all()
        
        # Should only see contract where they are vendor (contract 1)
        # Should NOT see contract where they are client (contract 2)
        assert len(results) == 1
        assert results[0].id == "contract-001"
        assert results[0].vendor_id == sample_users["vendor_parent"].business_partner_id
    
    def test_complete_data_separation(self, db_session, sample_users, sample_contracts):
        """Verify complete data separation between different business partners."""
        # Get contracts for client
        client_query = db_session.query(models.SalesContract)
        client_contracts = filter_contracts_by_user_type(
            client_query, sample_users["client_parent"], db_session
        ).all()
        
        # Get contracts for vendor
        vendor_query = db_session.query(models.SalesContract)
        vendor_contracts = filter_contracts_by_user_type(
            vendor_query, sample_users["vendor_parent"], db_session
        ).all()
        
        # They should see the same contract (001) but from different perspectives
        assert len(client_contracts) == 1
        assert len(vendor_contracts) == 1
        assert client_contracts[0].id == vendor_contracts[0].id
        
        # But the relationship is different
        assert client_contracts[0].client_id == sample_users["client_parent"].business_partner_id
        assert vendor_contracts[0].vendor_id == sample_users["vendor_parent"].business_partner_id
