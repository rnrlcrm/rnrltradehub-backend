# RNRL TradeHub Backend - NonProd v1.0.0

Secure FastAPI backend for Non-Production environment.
Includes Cloud Build CI/CD, PostgreSQL database, and comprehensive CRM API.

## Features

- ✅ FastAPI framework for high-performance async API
- ✅ PostgreSQL database with SQLAlchemy ORM
- ✅ Complete database schema matching frontend TypeScript types
- ✅ RESTful API endpoints for all entities
- ✅ CORS middleware configured for development
- ✅ Health check endpoint with database connectivity check
- ✅ Structured logging
- ✅ Docker containerization
- ✅ Google Cloud Run deployment ready
- ✅ Code quality checks (Pylint, Flake8, Bandit)
- ✅ Automatic database table creation
- ✅ Password hashing with bcrypt
- ✅ Comprehensive API documentation (Swagger/ReDoc)

## Database Schema

The backend implements a complete database schema for:

- **Business Partners**: Vendors, clients, agents with compliance tracking
- **Sales Contracts**: Full contract lifecycle management
- **CCI Terms**: Cotton Corporation of India terms
- **Invoices & Payments**: Financial transaction tracking
- **Disputes**: Dispute management and resolution
- **Commissions**: Agent commission tracking
- **Users**: Role-based access control
- **Audit Logs**: Complete audit trail

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure database:
```bash
cp .env.example .env
# Edit .env and set your DATABASE_URL
```

3. Run the application:
```bash
python main.py
```

4. Access the API:
- Root: http://localhost:8080/
- Health: http://localhost:8080/health
- API Docs: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

### Docker

```bash
docker build -t rnrltradehub-nonprod .
docker run -p 8080:8080 \
  -e DATABASE_URL="postgresql://user:password@host:5432/db" \
  rnrltradehub-nonprod
```

## API Endpoints

### Core
- `GET /` - API status
- `GET /health` - Health check with database status
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

### Business Partners
- `POST /api/business-partners/` - Create
- `GET /api/business-partners/` - List all
- `GET /api/business-partners/{id}` - Get by ID

### Sales Contracts
- `POST /api/sales-contracts/` - Create
- `GET /api/sales-contracts/` - List all
- `GET /api/sales-contracts/{id}` - Get by ID

### CCI Terms
- `POST /api/cci-terms/` - Create
- `GET /api/cci-terms/` - List all
- `GET /api/cci-terms/{id}` - Get by ID

### Users
- `POST /api/users/` - Create
- `GET /api/users/` - List all
- `GET /api/users/{id}` - Get by ID

## Deployment

Deploy to Google Cloud Run:
```bash
gcloud builds submit --config cloudbuild.yaml
```

## Documentation

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guidelines, code quality standards, security considerations, and database setup.

## Code Quality

This project maintains high code quality standards:
- **Pylint Score**: 9.55/10
- **Flake8**: PEP 8 compliant
- **Bandit**: No security issues
- **Documentation**: Complete docstrings

Run quality checks:
```bash
pylint main.py database.py models.py schemas.py routes.py
flake8 main.py database.py models.py schemas.py routes.py
bandit -r main.py database.py models.py schemas.py routes.py
```

## Environment Variables

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/rnrltradehub
PORT=8080
```

See `.env.example` for complete configuration template.
