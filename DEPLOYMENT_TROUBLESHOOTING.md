# Deployment Troubleshooting Guide

This guide helps diagnose and fix common deployment issues with the RNRL TradeHub Backend.

## Quick Diagnostic

### Before Deploying

Run the startup verification script to ensure everything is configured correctly:

```bash
python verify_startup.py
```

This will check:
- ✓ All required packages are installed
- ✓ FastAPI application can be imported
- ✓ All critical endpoints are registered
- ✓ Database configuration is valid
- ✓ Environment variables are set

### Verify Application Type

**This repository contains a FastAPI application, NOT Flask.**

If you see a Flask-style 404 error page like:
```html
<!doctype html>
<html lang=en>
<title>404 Not Found</title>
<h1>Not Found</h1>
```

This means:
1. ❌ **Wrong application is deployed** - Check you're deploying from the correct repository
2. ❌ **Old deployment exists** - The service name might not match the current configuration
3. ❌ **Deployment failed** - Check Cloud Run logs

**Expected FastAPI 404 response:**
```json
{"detail":"Not Found"}
```

## Common Issues

### Issue 1: Flask 404 Page on Cloud Run

**Symptoms:**
```bash
curl https://your-service.run.app/health
# Returns HTML:
<!doctype html>
<html lang=en>
<title>404 Not Found</title>
```

**Root Cause:**
- Wrong application deployed to the service
- Service name mismatch (deployed to different service than expected)
- Old/stale deployment

**Solution:**

1. **Verify the correct repository is being deployed:**
   ```bash
   # Check current directory
   pwd
   # Should be in rnrltradehub-backend
   
   # Verify this is a FastAPI app
   python verify_startup.py
   ```

2. **Check Cloud Run service name:**
   ```bash
   # List all services
   gcloud run services list --region=us-central1
   
   # This repo deploys to: rnrltradehub-nonprod
   # NOT: erp-nonprod-backend or other names
   ```

3. **Redeploy with correct configuration:**
   ```bash
   # Using Cloud Build (recommended)
   gcloud builds submit --config=cloudbuild.yaml
   
   # Or manual deployment
   gcloud run deploy rnrltradehub-nonprod \
     --image=gcr.io/YOUR_PROJECT_ID/rnrltradehub-nonprod \
     --region=us-central1 \
     --platform=managed \
     --allow-unauthenticated \
     --port=8080
   ```

4. **Verify deployment:**
   ```bash
   # Get service URL
   SERVICE_URL=$(gcloud run services describe rnrltradehub-nonprod \
     --region=us-central1 \
     --format='value(status.url)')
   
   # Test health endpoint (should return JSON)
   curl $SERVICE_URL/health
   # Expected: {"status":"healthy","service":"rnrltradehub-nonprod",...}
   
   # Test root (should return JSON)
   curl $SERVICE_URL/
   # Expected: {"message":"RNRL TradeHub NonProd API is running!"}
   ```

### Issue 2: Application Not Starting

**Symptoms:**
- Cloud Run shows "Service Unavailable"
- Logs show "Container failed to start"
- Health checks failing

**Diagnosis:**

1. **Check logs:**
   ```bash
   gcloud run services logs read rnrltradehub-nonprod \
     --region=us-central1 \
     --limit=100
   ```

2. **Look for startup banner:**
   ```
   ============================================================
   RNRL TradeHub Backend API - Starting Up
   ============================================================
   Application: RNRL TradeHub NonProd API v1.0.0
   Framework: FastAPI
   Total Routes: 88
   Health Endpoint: /health
   ```

   If you don't see this, the app isn't starting.

**Solutions:**

1. **Test locally first:**
   ```bash
   # Run verification
   python verify_startup.py
   
   # Start server locally
   export DATABASE_URL="sqlite:///./test.db"
   python main.py
   
   # In another terminal, test
   curl http://localhost:8080/health
   ```

2. **Test Docker build:**
   ```bash
   # Build image
   docker build -t test-backend .
   
   # Run locally
   docker run -p 8080:8080 \
     -e DATABASE_URL="sqlite:///./test.db" \
     test-backend
   
   # Test
   curl http://localhost:8080/health
   ```

3. **Check environment variables:**
   ```bash
   gcloud run services describe rnrltradehub-nonprod \
     --region=us-central1 \
     --format='value(spec.template.spec.containers[0].env)'
   ```

   Required:
   - `DATABASE_URL` (or DB_HOST, DB_NAME, DB_USER, DB_PASSWORD separately)
   - `PORT` (automatically set to 8080 by Cloud Run)

### Issue 3: Database Connection Issues

**Symptoms:**
- `/health` returns `"database": "disconnected"`
- Application starts but database queries fail

**Solutions:**

1. **Check database connectivity:**
   ```bash
   # From Cloud Shell or local machine with access
   psql "postgresql://user:pass@host:5432/dbname"
   ```

2. **Verify Cloud SQL connection (if using Cloud SQL):**
   ```bash
   gcloud run services update rnrltradehub-nonprod \
     --region=us-central1 \
     --add-cloudsql-instances=PROJECT:REGION:INSTANCE
   ```

3. **Check connection string format:**
   ```bash
   # PostgreSQL
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   
   # Cloud SQL (using Unix socket)
   DATABASE_URL=postgresql://user:password@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE
   ```

### Issue 4: Service Name Mismatch

**Problem:**
The service URL in the problem statement (`erp-nonprod-backend-*`) doesn't match the configured service name in this repository (`rnrltradehub-nonprod`).

**Verification:**
```bash
# Check what's actually deployed
gcloud run services list --region=us-central1

# Should show: rnrltradehub-nonprod
# NOT: erp-nonprod-backend
```

**Solution:**

If deploying to a different service name, update `cloudbuild.yaml`:
```yaml
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
  entrypoint: gcloud
  args:
    [
      'run', 'deploy', 'YOUR-ACTUAL-SERVICE-NAME',  # Change this
      '--image=gcr.io/$PROJECT_ID/rnrltradehub-nonprod',
      # ... rest of config
    ]
```

### Issue 5: Wrong Repository Deployed

**Problem:**
A different repository (possibly a Flask app) is deployed to the target service.

**Verification:**

1. **Check current service:**
   ```bash
   gcloud run services describe YOUR-SERVICE-NAME \
     --region=us-central1 \
     --format='value(spec.template.spec.containers[0].image)'
   ```

2. **Check what's in the image:**
   ```bash
   # Pull the image
   docker pull gcr.io/PROJECT/IMAGE:TAG
   
   # List files
   docker run --rm gcr.io/PROJECT/IMAGE:TAG ls -la /app
   
   # Check if it's FastAPI or Flask
   docker run --rm gcr.io/PROJECT/IMAGE:TAG python -c "import sys; import main; print(type(main.app))"
   ```

**Solution:**

Deploy the correct repository:
```bash
cd /path/to/rnrltradehub-backend
gcloud builds submit --config=cloudbuild.yaml
```

## Verification Checklist

Before considering deployment successful:

- [ ] `verify_startup.py` passes all checks
- [ ] Application is FastAPI (not Flask)
- [ ] Service name matches configuration
- [ ] `/health` endpoint returns JSON (not HTML)
- [ ] `/` endpoint returns JSON message
- [ ] `/docs` shows Swagger UI
- [ ] Database connectivity works
- [ ] Logs show startup banner with "FastAPI"

## Expected Responses

### Healthy /health Endpoint
```bash
curl https://your-service.run.app/health
```
**Response (HTTP 200):**
```json
{
  "status": "healthy",
  "service": "rnrltradehub-nonprod",
  "version": "1.0.0",
  "database": "connected"
}
```

### Root Endpoint
```bash
curl https://your-service.run.app/
```
**Response (HTTP 200):**
```json
{
  "message": "RNRL TradeHub NonProd API is running!"
}
```

### API Documentation
```bash
open https://your-service.run.app/docs
```
**Response:**
Should show Swagger UI with all 88 endpoints documented.

## Getting Help

If issues persist:

1. **Run diagnostics:**
   ```bash
   python verify_startup.py > diagnostics.txt 2>&1
   ```

2. **Collect logs:**
   ```bash
   gcloud run services logs read rnrltradehub-nonprod \
     --region=us-central1 \
     --limit=200 > service-logs.txt
   ```

3. **Check service details:**
   ```bash
   gcloud run services describe rnrltradehub-nonprod \
     --region=us-central1 > service-details.txt
   ```

4. **Test locally:**
   ```bash
   docker build -t test-backend . && \
   docker run -p 8080:8080 -e DATABASE_URL="sqlite:///./test.db" test-backend
   ```

## Related Documentation

- [CLOUD_RUN_DEPLOYMENT.md](CLOUD_RUN_DEPLOYMENT.md) - Detailed deployment guide
- [QUICK_START.md](QUICK_START.md) - Local development setup
- [README.md](README.md) - Project overview
