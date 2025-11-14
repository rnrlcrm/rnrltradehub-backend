"""
Test configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app

# Test database URL (SQLite in-memory for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "Test@123",
        "role_name": "Admin"
    }


@pytest.fixture
def sample_organization_data():
    """Sample organization data for testing."""
    return {
        "org_code": "ORG001",
        "org_name": "Test Organization",
        "business_type": "Trading",
        "is_active": True
    }


@pytest.fixture
def sample_commodity_data():
    """Sample commodity data for testing."""
    return {
        "commodity_code": "COTTON001",
        "commodity_name": "Cotton",
        "commodity_type": "Agricultural",
        "uom": "BALES"
    }


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        "trade_number": "TRD001",
        "buyer_id": "buyer123",
        "commodity_id": 1,
        "quantity": 100.0,
        "unit": "BALES",
        "created_by": "user123"
    }


@pytest.fixture
def auth_headers():
    """Mock authentication headers for testing."""
    # In real tests, generate actual JWT token
    return {
        "Authorization": "Bearer test_token_here"
    }
