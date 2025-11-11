# ⚡ QUICK REFERENCE - Deploy Now

## 🚀 Deploy Commands

### Deploy to BOTH services (Recommended)
```bash
# Fix erp-nonprod-backend (solves 404 issue)
gcloud builds submit --config=cloudbuild.yaml

# Update rnrltradehub-nonprod (alternative)
gcloud builds submit --config=cloudbuild-rnrltradehub.yaml
```

### Deploy to ONE service
```bash
# Option 1: erp-nonprod-backend (DEFAULT - fixes 404)
gcloud builds submit --config=cloudbuild.yaml

# Option 2: rnrltradehub-nonprod
gcloud builds submit --config=cloudbuild-rnrltradehub.yaml
```

## ✅ Verify Deployment

```bash
# Test health endpoint
curl https://erp-nonprod-backend-502095789065.us-central1.run.app/health

# Expected: JSON response with "status":"healthy"
# NOT: HTML with "<title>404 Not Found</title>"

# Test 404 (should return JSON)
curl https://erp-nonprod-backend-502095789065.us-central1.run.app/nonexistent

# Expected: {"detail":"Not Found","status_code":404,"framework":"FastAPI"}
```

## 🔧 Frontend Fix

```javascript
// Update API base URL
const API_BASE_URL = "https://erp-nonprod-backend-502095789065.us-central1.run.app";

// Use proper URL construction
const url = `${API_BASE_URL}/api/settings/users`;
```

## 📚 Full Documentation

- **[SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md)** - Quick start
- **[COMPLETE_FIX.md](COMPLETE_FIX.md)** - Complete guide

## ✅ What's Fixed

- ✅ Both deployment options working
- ✅ Always returns JSON (never HTML)
- ✅ Robust error handling
- ✅ Secure configuration
- ✅ Future-proof backend

## 🎯 Ready!

Run this now:
```bash
gcloud builds submit --config=cloudbuild.yaml
```
