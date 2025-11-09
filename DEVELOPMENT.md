# Development Guide

## Code Quality Standards

This project follows Python best practices and includes several quality checks.

### Prerequisites

- Python 3.11+
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

### Running the Application

```bash
python main.py
```

The application will start on port 8080 by default. You can override this with the `PORT` environment variable:

```bash
PORT=9090 python main.py
```

### Code Quality Checks

#### Linting with Pylint
```bash
pylint main.py
```

#### Code Style with Flake8
```bash
flake8 main.py
```

#### Security Scanning with Bandit
```bash
bandit -r main.py
```

#### Auto-formatting with Black
```bash
black main.py
```

### API Endpoints

- `GET /` - Root endpoint, returns API status
- `GET /health` - Health check endpoint for monitoring

### Testing Endpoints

```bash
# Root endpoint
curl http://localhost:8080/

# Health check
curl http://localhost:8080/health
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

## Docker Build

```bash
docker build -t rnrltradehub-nonprod .
docker run -p 8080:8080 rnrltradehub-nonprod
```

## Deployment

The project uses Google Cloud Build for CI/CD:

```bash
gcloud builds submit --config cloudbuild.yaml
```
