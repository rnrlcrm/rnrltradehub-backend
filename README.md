# RNRL TradeHub Backend - NonProd v1.0.0

Secure FastAPI backend for Non-Production environment.
Includes Cloud Build CI/CD, PostgreSQL, and Vertex AI connectivity.

## Features

- ✅ FastAPI framework for high-performance async API
- ✅ CORS middleware configured for development
- ✅ Health check endpoint for monitoring
- ✅ Structured logging
- ✅ Docker containerization
- ✅ Google Cloud Run deployment ready
- ✅ Code quality checks (Pylint, Flake8, Bandit)

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

3. Access the API:
- Root: http://localhost:8080/
- Health: http://localhost:8080/health
- API Docs: http://localhost:8080/docs

### Docker

```bash
docker build -t rnrltradehub-nonprod .
docker run -p 8080:8080 rnrltradehub-nonprod
```

## Deployment

Deploy to Google Cloud Run:
```bash
gcloud builds submit --config cloudbuild.yaml
```

## Documentation

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guidelines, code quality standards, and security considerations.

## Code Quality

This project maintains high code quality standards:
- **Pylint Score**: 9.55/10
- **Flake8**: PEP 8 compliant
- **Bandit**: No security issues
- **Documentation**: Complete docstrings

Run quality checks:
```bash
pylint main.py
flake8 main.py
bandit -r main.py
```
