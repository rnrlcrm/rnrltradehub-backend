# Development Guide

## Code Quality Standards

This project follows Python best practices and includes several quality checks.

### Prerequisites

- Python 3.11+
- PostgreSQL 12+ (for database)
- pip

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install development tools:
```bash
pip install pylint flake8 black mypy bandit
```

3. Configure database:
```bash
# Copy environment template
cp .env.example .env

# Edit .env and update DATABASE_URL
# DATABASE_URL=postgresql://user:password@localhost:5432/rnrltradehub
```

### Running the Application

```bash
python main.py
```

The application will start on port 8080 by default. You can override this with the `PORT` environment variable:

```bash
PORT=9090 python main.py
```

### Database

#### Schema
The database schema is based on the frontend TypeScript types and includes:

- **Business Partners**: Vendors, clients, and agents with compliance tracking
- **Sales Contracts**: Contract management with version control
- **CCI Terms**: Cotton Corporation of India terms configuration
- **Users**: User authentication and role-based access
- **Invoices, Payments, Disputes, Commissions**: Transaction tracking
- **Audit Logs**: Complete audit trail

#### Automatic Migrations
Tables are automatically created on application startup. For production, consider using Alembic migrations:

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### Code Quality Checks

#### Linting with Pylint
```bash
pylint main.py database.py models.py schemas.py routes.py
```

#### Code Style with Flake8
```bash
flake8 main.py database.py models.py schemas.py routes.py
```

#### Security Scanning with Bandit
```bash
bandit -r main.py database.py models.py schemas.py routes.py
```

#### Auto-formatting with Black
```bash
black main.py database.py models.py schemas.py routes.py
```

### API Endpoints

#### Core Endpoints
- `GET /` - Root endpoint, returns API status
- `GET /health` - Health check endpoint with database connectivity check
- `GET /docs` - Swagger UI API documentation
- `GET /redoc` - ReDoc API documentation

#### Business Partner Endpoints
- `POST /api/business-partners/` - Create business partner
- `GET /api/business-partners/` - List all business partners
- `GET /api/business-partners/{id}` - Get specific business partner

#### Sales Contract Endpoints
- `POST /api/sales-contracts/` - Create sales contract
- `GET /api/sales-contracts/` - List all sales contracts
- `GET /api/sales-contracts/{id}` - Get specific sales contract

#### CCI Terms Endpoints
- `POST /api/cci-terms/` - Create CCI term
- `GET /api/cci-terms/` - List all CCI terms
- `GET /api/cci-terms/{id}` - Get specific CCI term

#### User Endpoints
- `POST /api/users/` - Create user
- `GET /api/users/` - List all users
- `GET /api/users/{id}` - Get specific user

### Testing Endpoints

```bash
# Root endpoint
curl http://localhost:8080/

# Health check with database status
curl http://localhost:8080/health

# Create a business partner
curl -X POST http://localhost:8080/api/business-partners/ \
  -H "Content-Type: application/json" \
  -d '{...}'

# List business partners
curl http://localhost:8080/api/business-partners/
```

## Security Considerations

### CORS Configuration
The application is configured with wildcard CORS origins (`["*"]`) for the non-production environment. This allows requests from any origin and is suitable for development and testing.

**⚠️ Important**: In production environments, you must replace the wildcard with specific allowed origins:

```python
origins = [
    "https://your-frontend-domain.com",
    "https://www.your-frontend-domain.com"
]
```

### Host Binding
The application binds to `0.0.0.0` to allow external access, which is required for containerized deployments like Cloud Run. This is marked with `# nosec B104` to suppress the Bandit security warning, as it's intentional and necessary for the deployment architecture.

### Database Security
- Never commit `.env` file with actual credentials
- Use environment variables for database URLs
- In production, use connection pooling and SSL
- Implement proper password hashing (bcrypt is included)

## Architecture

### Service Layer Pattern

This project uses a **service layer architecture** that separates business logic from route handlers:

```
Routes (HTTP) → Services (Business Logic) → Models (Database)
```

#### Benefits:
- **Separation of Concerns**: Routes handle HTTP, services handle business logic
- **Reusability**: Business logic can be reused across different endpoints
- **Testability**: Services can be unit tested independently
- **Maintainability**: Business rules are centralized in one place

#### Service Modules:

1. **BusinessPartnerService** (`services/business_partner_service.py`)
   - BP code uniqueness validation
   - Status management
   - Active contract checking
   - Search and filtering logic

2. **SalesContractService** (`services/sales_contract_service.py`)
   - Contract number generation
   - Status workflow management
   - Amendment logic (version control)
   - Cancellation validation

3. **FinancialService** (`services/financial_service.py`)
   - Invoice number generation
   - Payment processing logic
   - Commission calculations
   - Outstanding balance tracking

4. **UserService** (`services/user_service.py`)
   - Password hashing and verification
   - Email uniqueness validation
   - Role-based access control
   - Permission checking

5. **ComplianceService** (`services/compliance_service.py`)
   - GDPR data export/deletion
   - Consent management
   - Data retention policies
   - Security event logging

**See [SERVICE_LAYER.md](SERVICE_LAYER.md) for detailed documentation and examples.**

## Docker Build

```bash
docker build -t rnrltradehub-nonprod .
docker run -p 8080:8080 -e DATABASE_URL="postgresql://..." rnrltradehub-nonprod
```

## Deployment

The project uses Google Cloud Build for CI/CD:

```bash
gcloud builds submit --config cloudbuild.yaml
```
