# Service Deployment Resolution

## Current Situation

There are **TWO separate backend services** deployed:

### 1. OLD Service (Having Issues)
- **Service Name**: `erp-nonprod-backend`
- **URL**: https://erp-nonprod-backend-502095789065.us-central1.run.app
- **Last Deployed**: November 7, 2025 (4 days ago)
- **Status**: Returning Flask 404 errors
- **Problem**: Wrong application deployed OR outdated

### 2. CURRENT Service (This Repository)
- **Service Name**: `rnrltradehub-nonprod`
- **URL**: https://rnrltradehub-nonprod-502095789065.us-central1.run.app
- **Last Deployed**: November 11, 2025 (today at 12:29 PM)
- **Status**: Should be working correctly with FastAPI
- **Deployed By**: erp-nonprod-sa@google-mpf-cas7ishusxmu.iam.gserviceaccount.com

## The Issue

The problem statement shows errors accessing `erp-nonprod-backend`, but this repository deploys to `rnrltradehub-nonprod`. These are **two different services**.

## Solution Options

### Option A: Update Frontend to Use Correct Backend

If the frontend should use the current FastAPI backend from this repository:

**Update frontend configuration to point to:**
```
https://rnrltradehub-nonprod-502095789065.us-central1.run.app
```

**Instead of:**
```
https://erp-nonprod-backend-502095789065.us-central1.run.app
```

### Option B: Deploy This Code to Old Service Name

If you need to keep using `erp-nonprod-backend` service name, update `cloudbuild.yaml`:

```yaml
# Change line 15 from:
'run', 'deploy', 'rnrltradehub-nonprod',

# To:
'run', 'deploy', 'erp-nonprod-backend',
```

Then redeploy:
```bash
gcloud builds submit --config=cloudbuild.yaml
```

### Option C: Deprecate Old Service

If `erp-nonprod-backend` is no longer needed:

1. **Delete the old service:**
   ```bash
   gcloud run services delete erp-nonprod-backend \
     --region=us-central1
   ```

2. **Update all references** to use `rnrltradehub-nonprod`

## Verification Steps

### Check Current `rnrltradehub-nonprod` Service

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe rnrltradehub-nonprod \
  --region=us-central1 \
  --format='value(status.url)')

echo "Testing: $SERVICE_URL/health"

# Test health endpoint (should return JSON)
curl -i $SERVICE_URL/health

# Expected response:
# HTTP/2 200
# content-type: application/json
# {"status":"healthy","service":"rnrltradehub-nonprod","version":"1.0.0","database":"connected"}
```

### Check Logs for Framework Identification

```bash
# View recent logs
gcloud run services logs read rnrltradehub-nonprod \
  --region=us-central1 \
  --limit=50

# Look for this startup banner:
# ============================================================
# RNRL TradeHub Backend API - Starting Up
# ============================================================
# Framework: FastAPI
```

If you see "Framework: FastAPI", the correct application is deployed.

### Check Old Service (erp-nonprod-backend)

```bash
# Check what's in the old service
gcloud run services logs read erp-nonprod-backend \
  --region=us-central1 \
  --limit=50

# Check deployment details
gcloud run services describe erp-nonprod-backend \
  --region=us-central1
```

## Frontend Configuration Issue

The error message also shows a frontend URL configuration problem:
```
Failed to load resource: localhost:3000/apihttp://localhost:8080/api/settings/users
```

This malformed URL suggests the frontend has incorrect API base URL configuration.

### Fix Frontend API Configuration

The frontend should be configured with ONE of these:

**Option 1: Use production backend**
```javascript
// In frontend config
API_BASE_URL = "https://rnrltradehub-nonprod-502095789065.us-central1.run.app"
```

**Option 2: Use local development**
```javascript
// In frontend config
API_BASE_URL = "http://localhost:8080"
```

**NOT a concatenation of both**, which is what's currently happening.

## Recommended Action Plan

### Immediate Actions

1. **Verify Current Deployment**
   ```bash
   curl https://rnrltradehub-nonprod-502095789065.us-central1.run.app/health
   ```
   
   If this returns JSON with "status": "healthy", the backend is working.

2. **Update Frontend Configuration**
   - Change frontend API base URL to: `https://rnrltradehub-nonprod-502095789065.us-central1.run.app`
   - Remove any duplicate/malformed URL concatenation
   - Redeploy frontend

3. **Test Frontend Integration**
   ```bash
   # From frontend, this should work:
   curl https://rnrltradehub-nonprod-502095789065.us-central1.run.app/api/settings/users
   ```

### Long-term Actions

1. **Decide on Service Naming**
   - Keep `rnrltradehub-nonprod` (current) OR
   - Rename to `erp-nonprod-backend` (for consistency)

2. **Deprecate Unused Services**
   - Delete `erp-nonprod-backend` if no longer needed
   - Update all documentation to reference the correct service

3. **Document Frontend-Backend Integration**
   - Create a clear configuration guide
   - Specify which frontend should use which backend

## Service Inventory

| Service | Purpose | Status | Action |
|---------|---------|--------|--------|
| `erp-nonprod-backend` | Old backend? | 404 errors | Investigate or delete |
| `erp-nonprod-frontend` | Old frontend? | Unknown | Check if still needed |
| `rnrltradehub-frontend-nonprod` | Current frontend | Active | Update API config |
| `rnrltradehub-nonprod` | Current backend | Active | ✅ Working correctly |

## Next Steps

1. **Test the current backend:**
   ```bash
   curl https://rnrltradehub-nonprod-502095789065.us-central1.run.app/health
   curl https://rnrltradehub-nonprod-502095789065.us-central1.run.app/
   curl https://rnrltradehub-nonprod-502095789065.us-central1.run.app/docs
   ```

2. **If working, update frontend to use it**

3. **Clean up old services** if they're no longer needed

## Files to Update (if deploying to erp-nonprod-backend)

If you decide to deploy this repository's code to `erp-nonprod-backend` instead:

**cloudbuild.yaml:**
```yaml
steps:
  # ... build and push steps ...
  
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
    entrypoint: gcloud
    args:
      [
        'run', 'deploy', 'erp-nonprod-backend',  # Changed from rnrltradehub-nonprod
        '--image=gcr.io/$PROJECT_ID/rnrltradehub-nonprod',
        '--region=us-central1',
        '--platform=managed',
        '--allow-unauthenticated',
        '--port=8080',
        '--timeout=300',
        '--memory=512Mi',
        '--cpu=1',
        '--min-instances=0',
        '--max-instances=10'
      ]
```

Then redeploy with `gcloud builds submit --config=cloudbuild.yaml`.
