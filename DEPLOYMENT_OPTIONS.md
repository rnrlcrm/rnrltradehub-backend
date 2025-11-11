# Deployment Guide - Choose Your Service

## Two Deployment Options

This repository can be deployed to either service name. Choose based on your needs:

### Option 1: Deploy to `rnrltradehub-nonprod` (Default)

**Use this if:** Starting fresh or prefer the new naming convention.

```bash
gcloud builds submit --config=cloudbuild.yaml
```

**Service URL:** https://rnrltradehub-nonprod-502095789065.us-central1.run.app

---

### Option 2: Deploy to `erp-nonprod-backend` (Legacy Compatibility)

**Use this if:** You need to maintain compatibility with existing frontend configuration pointing to `erp-nonprod-backend`.

```bash
gcloud builds submit --config=cloudbuild-erp-backend.yaml
```

**Service URL:** https://erp-nonprod-backend-502095789065.us-central1.run.app

---

## Quick Deployment

### Prerequisites
- Google Cloud SDK installed and authenticated
- Correct project selected: `google-mpf-cas7ishusxmu`
- Permissions to deploy to Cloud Run

### Deploy to Default Service (rnrltradehub-nonprod)

```bash
# From repository root
gcloud builds submit --config=cloudbuild.yaml

# Verify deployment
gcloud run services describe rnrltradehub-nonprod \
  --region=us-central1 \
  --format='value(status.url)'

# Test health endpoint
SERVICE_URL=$(gcloud run services describe rnrltradehub-nonprod \
  --region=us-central1 --format='value(status.url)')
curl $SERVICE_URL/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "rnrltradehub-nonprod",
  "version": "1.0.0",
  "database": "connected"
}
```

### Deploy to Legacy Service (erp-nonprod-backend)

```bash
# From repository root
gcloud builds submit --config=cloudbuild-erp-backend.yaml

# Verify deployment
gcloud run services describe erp-nonprod-backend \
  --region=us-central1 \
  --format='value(status.url)'

# Test health endpoint
SERVICE_URL=$(gcloud run services describe erp-nonprod-backend \
  --region=us-central1 --format='value(status.url)')
curl $SERVICE_URL/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "rnrltradehub-nonprod",
  "version": "1.0.0",
  "database": "connected"
}
```

## Verification After Deployment

### 1. Check Deployment Status

```bash
# List all services
gcloud run services list --region=us-central1

# Check specific service
gcloud run services describe [SERVICE_NAME] --region=us-central1
```

### 2. View Deployment Logs

```bash
# Recent logs
gcloud run services logs read [SERVICE_NAME] \
  --region=us-central1 \
  --limit=50

# Look for startup banner:
# ============================================================
# RNRL TradeHub Backend API - Starting Up
# ============================================================
# Framework: FastAPI
# Total Routes: 88
```

### 3. Test All Critical Endpoints

```bash
# Set service URL
SERVICE_URL="https://[SERVICE_NAME]-502095789065.us-central1.run.app"

# Test health
curl $SERVICE_URL/health

# Test root
curl $SERVICE_URL/

# Test API endpoint
curl $SERVICE_URL/api/settings/users

# Test docs (should return HTML)
curl -I $SERVICE_URL/docs
```

### 4. Run Startup Verification Locally

Before deploying, always verify:

```bash
python verify_startup.py
```

Expected output:
```
✓ All checks passed - Application is ready to start
```

## Frontend Integration

After deploying the backend, update your frontend configuration:

### For rnrltradehub-nonprod

```javascript
// Frontend environment config
const API_BASE_URL = "https://rnrltradehub-nonprod-502095789065.us-central1.run.app";
```

### For erp-nonprod-backend

```javascript
// Frontend environment config
const API_BASE_URL = "https://erp-nonprod-backend-502095789065.us-central1.run.app";
```

### Important: Fix URL Configuration

Ensure your frontend is NOT concatenating URLs like this:
```javascript
// ❌ WRONG - causes "localhost:3000/apihttp://localhost:8080/..."
const url = frontendUrl + "api" + backendUrl + "/api/settings/users";

// ✅ CORRECT
const url = `${API_BASE_URL}/api/settings/users`;
```

## Environment Variables

Set these in Cloud Run (required for database connectivity):

```bash
gcloud run services update [SERVICE_NAME] \
  --region=us-central1 \
  --set-env-vars="DATABASE_URL=postgresql://user:pass@host:5432/dbname"
```

Or use Cloud Console:
1. Navigate to Cloud Run → Select service
2. Click "Edit & Deploy New Revision"
3. Add environment variables under "Variables & Secrets"

## Rollback

If deployment fails, rollback to previous version:

```bash
# List revisions
gcloud run revisions list \
  --service=[SERVICE_NAME] \
  --region=us-central1

# Rollback to specific revision
gcloud run services update-traffic [SERVICE_NAME] \
  --region=us-central1 \
  --to-revisions=[REVISION_NAME]=100
```

## Troubleshooting

### Issue: 404 Errors After Deployment

**Check:**
1. View logs for startup banner
2. Verify "Framework: FastAPI" appears
3. Check if container is actually running your code

**Solution:**
```bash
# Check what image is deployed
gcloud run services describe [SERVICE_NAME] \
  --region=us-central1 \
  --format='value(spec.template.spec.containers[0].image)'

# Verify it matches what you built
```

### Issue: Service Not Responding

**Check:**
```bash
# View recent logs
gcloud run services logs read [SERVICE_NAME] \
  --region=us-central1 \
  --limit=100

# Look for errors in startup
```

**Common fixes:**
- Ensure DATABASE_URL is set
- Check memory/CPU limits
- Verify port 8080 is exposed

### Issue: Database Connection Fails

**Check:**
```bash
# Health endpoint shows database status
curl https://[SERVICE_NAME]-502095789065.us-central1.run.app/health

# If "database": "disconnected", check:
# 1. DATABASE_URL is set correctly
# 2. Database allows connections from Cloud Run
# 3. Credentials are valid
```

## Comparison: Which Service to Use?

| Aspect | rnrltradehub-nonprod | erp-nonprod-backend |
|--------|---------------------|---------------------|
| **Age** | Current | Legacy (4 days old) |
| **Naming** | Consistent with repo | Legacy naming |
| **Recommended** | ✅ Yes (default) | Use only if needed |
| **Config File** | cloudbuild.yaml | cloudbuild-erp-backend.yaml |
| **Use Case** | New deployments | Maintain compatibility |

## Best Practices

1. **Before Deployment:**
   - Run `python verify_startup.py`
   - Run all tests: `python test_*.py`
   - Review changes with team

2. **During Deployment:**
   - Use Cloud Build (automatic via config file)
   - Monitor deployment progress
   - Check logs immediately after

3. **After Deployment:**
   - Test health endpoint
   - Verify startup logs show FastAPI
   - Test critical API endpoints
   - Update frontend configuration
   - Notify team

4. **Regular Maintenance:**
   - Review service logs weekly
   - Monitor error rates
   - Update dependencies monthly
   - Run security scans

## Additional Resources

- [CLOUD_RUN_DEPLOYMENT.md](CLOUD_RUN_DEPLOYMENT.md) - Detailed deployment guide
- [DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md) - Troubleshooting guide
- [SERVICE_DEPLOYMENT_RESOLUTION.md](SERVICE_DEPLOYMENT_RESOLUTION.md) - Service name resolution
- [README.md](README.md) - Project overview

## Support

If you encounter issues:

1. Run diagnostics: `python verify_startup.py`
2. Check logs: `gcloud run services logs read [SERVICE_NAME]`
3. Review troubleshooting guide: [DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md)
4. Contact: rnrl.crm@rnrltradehub.com
