# Cloud Run Deployment Guide

This guide explains how to deploy the RNRL TradeHub backend to Google Cloud Run and troubleshoot common issues.

## Prerequisites

1. Google Cloud project with Cloud Run and Cloud Build enabled
2. Docker installed locally (for testing)
3. gcloud CLI installed and authenticated

## Deployment Process

### Option 1: Automated Deployment with Cloud Build

The repository includes a `cloudbuild.yaml` file that automates the deployment process.

```bash
# Trigger Cloud Build deployment
gcloud builds submit --config=cloudbuild.yaml

# Or set it up to trigger on git push
gcloud builds triggers create github \
  --repo-name=rnrltradehub-backend \
  --repo-owner=rnrlcrm \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

### Option 2: Manual Deployment

```bash
# 1. Build the Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/rnrltradehub-nonprod .

# 2. Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/rnrltradehub-nonprod

# 3. Deploy to Cloud Run
gcloud run deploy rnrltradehub-nonprod \
  --image=gcr.io/YOUR_PROJECT_ID/rnrltradehub-nonprod \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --timeout=300 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10
```

## Environment Variables

Set required environment variables in Cloud Run:

```bash
gcloud run services update rnrltradehub-nonprod \
  --region=us-central1 \
  --set-env-vars="DB_HOST=YOUR_DB_HOST,DB_NAME=YOUR_DB_NAME,DB_USER=YOUR_DB_USER" \
  --set-secrets="DB_PASSWORD=db-password:latest"
```

Or use the Cloud Console:
1. Go to Cloud Run > Select your service
2. Click "Edit & Deploy New Revision"
3. Under "Variables & Secrets" add:
   - `DB_HOST` - Your database host
   - `DB_PORT` - Database port (default: 5432)
   - `DB_NAME` - Database name
   - `DB_USER` - Database username
   - `DB_PASSWORD` - Database password (use Secret Manager)

## Testing the Deployment

### Check Service Health

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe rnrltradehub-nonprod \
  --region=us-central1 \
  --format='value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test root endpoint
curl $SERVICE_URL/

# Test API endpoints
curl $SERVICE_URL/api/settings/users
```

### Expected Responses

**Healthy Service:**
```bash
curl https://YOUR-SERVICE-URL/health
# Response:
{
  "status": "healthy",
  "service": "rnrltradehub-nonprod",
  "version": "1.0.0",
  "database": "connected"  # or "disconnected" if DB not configured
}
```

**Root Endpoint:**
```bash
curl https://YOUR-SERVICE-URL/
# Response:
{
  "message": "RNRL TradeHub NonProd API is running!"
}
```

## Troubleshooting

### Issue: 404 Not Found Error

**Symptoms:**
```
HTTP/2 404
content-type: text/html; charset=utf-8
<h1>Not Found</h1>
```

**Causes:**
1. Incorrect CMD in Dockerfile
2. Application not starting properly
3. Wrong port configuration

**Solutions:**

1. **Check Dockerfile CMD** (Fixed in commit fe9d4c4):
   ```dockerfile
   # Correct:
   CMD exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
   
   # Incorrect:
   CMD ["python", "main.py"]
   ```

2. **Verify logs:**
   ```bash
   gcloud run services logs read rnrltradehub-nonprod \
     --region=us-central1 \
     --limit=50
   ```

3. **Check container startup:**
   ```bash
   # View recent revisions
   gcloud run revisions list \
     --service=rnrltradehub-nonprod \
     --region=us-central1
   
   # Check specific revision logs
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=rnrltradehub-nonprod" \
     --limit=50 \
     --format=json
   ```

### Issue: 500 Internal Server Error

**Causes:**
1. Database connection issues
2. Missing environment variables
3. Application errors

**Solutions:**

1. **Check environment variables:**
   ```bash
   gcloud run services describe rnrltradehub-nonprod \
     --region=us-central1 \
     --format='value(spec.template.spec.containers[0].env)'
   ```

2. **Verify database connectivity:**
   - Ensure database host is accessible from Cloud Run
   - Check if database allows connections from Cloud Run IP ranges
   - Verify credentials are correct

3. **Check application logs:**
   ```bash
   gcloud run services logs read rnrltradehub-nonprod \
     --region=us-central1 \
     --limit=100
   ```

### Issue: Container fails to start

**Symptoms:**
- Service shows "FAILED" status
- Revisions never become "ACTIVE"

**Solutions:**

1. **Test container locally:**
   ```bash
   # Build the image
   docker build -t test-backend .
   
   # Run locally
   docker run -p 8080:8080 \
     -e DB_HOST=localhost \
     -e DB_NAME=testdb \
     -e DB_USER=testuser \
     -e DB_PASSWORD=testpass \
     test-backend
   
   # Test in another terminal
   curl http://localhost:8080/health
   ```

2. **Check dependency installation:**
   ```bash
   # Verify requirements.txt is complete
   cat requirements.txt
   
   # Test installation locally
   pip install -r requirements.txt
   ```

3. **Review Dockerfile:**
   - Ensure all COPY commands are correct
   - Verify WORKDIR is set properly
   - Check CMD/ENTRYPOINT syntax

### Issue: Slow cold starts

**Solutions:**

1. **Set minimum instances:**
   ```bash
   gcloud run services update rnrltradehub-nonprod \
     --region=us-central1 \
     --min-instances=1
   ```

2. **Optimize Docker image:**
   - Use `.dockerignore` to exclude unnecessary files (already added)
   - Use multi-stage builds if needed
   - Minimize dependencies

### Issue: Database connection timeout

**Solutions:**

1. **Increase timeout:**
   ```bash
   gcloud run services update rnrltradehub-nonprod \
     --region=us-central1 \
     --timeout=600
   ```

2. **Use Cloud SQL Proxy** (if using Cloud SQL):
   ```bash
   gcloud run services update rnrltradehub-nonprod \
     --region=us-central1 \
     --add-cloudsql-instances=PROJECT:REGION:INSTANCE
   ```

## Monitoring

### View Service Metrics

```bash
# CPU utilization
gcloud monitoring time-series list \
  --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="rnrltradehub-nonprod"' \
  --format=json

# Request count
gcloud run services describe rnrltradehub-nonprod \
  --region=us-central1 \
  --format='value(status.traffic)'
```

### Set up Alerts

1. Go to Cloud Console > Monitoring > Alerting
2. Create alert for:
   - Request latency > 1000ms
   - Error rate > 5%
   - Instance count > 8

## Performance Optimization

### Recommended Settings

```bash
gcloud run services update rnrltradehub-nonprod \
  --region=us-central1 \
  --memory=1Gi \
  --cpu=2 \
  --timeout=300 \
  --concurrency=80 \
  --min-instances=1 \
  --max-instances=100
```

### Connection Pooling

The application uses SQLAlchemy with connection pooling. Adjust in `database.py`:

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,           # Number of connections to maintain
    max_overflow=10,       # Additional connections when pool is full
    pool_timeout=30,       # Timeout for getting connection from pool
    pool_recycle=3600      # Recycle connections after 1 hour
)
```

## Security

### Best Practices

1. **Use Secret Manager for sensitive data:**
   ```bash
   # Create secret
   echo -n "your-db-password" | gcloud secrets create db-password --data-file=-
   
   # Grant Cloud Run access
   gcloud secrets add-iam-policy-binding db-password \
     --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   
   # Update service to use secret
   gcloud run services update rnrltradehub-nonprod \
     --region=us-central1 \
     --set-secrets="DB_PASSWORD=db-password:latest"
   ```

2. **Restrict access:**
   ```bash
   # Remove public access
   gcloud run services remove-iam-policy-binding rnrltradehub-nonprod \
     --region=us-central1 \
     --member="allUsers" \
     --role="roles/run.invoker"
   
   # Add specific user
   gcloud run services add-iam-policy-binding rnrltradehub-nonprod \
     --region=us-central1 \
     --member="user:email@example.com" \
     --role="roles/run.invoker"
   ```

3. **Enable VPC connector** (for private database access):
   ```bash
   gcloud run services update rnrltradehub-nonprod \
     --region=us-central1 \
     --vpc-connector=YOUR_VPC_CONNECTOR \
     --vpc-egress=private-ranges-only
   ```

## Rollback

If deployment fails, rollback to previous revision:

```bash
# List revisions
gcloud run revisions list \
  --service=rnrltradehub-nonprod \
  --region=us-central1

# Rollback to specific revision
gcloud run services update-traffic rnrltradehub-nonprod \
  --region=us-central1 \
  --to-revisions=REVISION_NAME=100
```

## Support

For issues or questions:
1. Check logs: `gcloud run services logs read`
2. Review this guide
3. Check the QUICK_START.md for local testing
4. Consult the SETTINGS_USERS_API.md for API documentation
