# Database Authentication Fix - Quick Reference

## What Was Fixed

The application was unable to connect to the Cloud SQL database because database credentials were not configured in the Cloud Run deployment. The error message was:

```
password authentication failed for user "postgres"
```

## Changes Made

### 1. Updated Cloud Build Configurations

Both `cloudbuild.yaml` and `cloudbuild-rnrltradehub.yaml` were updated to include:

**Added Cloud SQL Connection:**
```yaml
'--add-cloudsql-instances=google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db'
```

**Added Database Password from Secret Manager:**
```yaml
'--update-secrets=DB_PASSWORD=erp-nonprod-db-password:latest'
```

**Added Database Environment Variables:**
```yaml
'--set-env-vars=DB_HOST=/cloudsql/google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db,DB_NAME=erp_nonprod,DB_USER=erp_user,DB_PORT=5432'
```

### 2. Added Documentation

Created `DATABASE_CREDENTIALS_SETUP.md` with comprehensive instructions for:
- Setting up Secret Manager
- Configuring database credentials
- Troubleshooting connection issues
- Security best practices

## What You Need to Do

### Before Deploying

**1. Create the database password secret in Secret Manager:**

```bash
# Replace "your-actual-password" with the real password for your database user
echo -n "your-actual-password" | gcloud secrets create erp-nonprod-db-password \
    --data-file=- \
    --replication-policy="automatic"
```

**2. Grant Cloud Run access to the secret:**

```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe google-mpf-cas7ishusxmu --format="value(projectNumber)")

# Grant access
gcloud secrets add-iam-policy-binding erp-nonprod-db-password \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

**3. Verify your database configuration:**

The current configuration assumes:
- Database name: `erp_nonprod`
- Database user: `erp_user`
- Cloud SQL instance: `google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db`

If your actual values are different, update them in:
- `cloudbuild.yaml` (line 36)
- `cloudbuild-rnrltradehub.yaml` (line 36)

**4. Deploy:**

```bash
# Deploy to erp-nonprod-backend
gcloud builds submit --config=cloudbuild.yaml

# OR deploy to rnrltradehub-nonprod
gcloud builds submit --config=cloudbuild-rnrltradehub.yaml
```

### After Deploying

**Verify the database connection:**

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe erp-nonprod-backend \
    --region=us-central1 \
    --format='value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "rnrltradehub-nonprod",
  "version": "1.0.0",
  "database": "connected"
}
```

If `"database": "disconnected"`, check the logs:
```bash
gcloud run services logs read erp-nonprod-backend --region=us-central1 --limit=100
```

## Default Values Used

The configuration uses these default values based on the error message:

| Variable | Value | Source |
|----------|-------|--------|
| Cloud SQL Instance | `google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db` | From error message |
| Database Name | `erp_nonprod` | Inferred from instance name |
| Database User | `erp_user` | Inferred from instance name |
| Database Port | `5432` | PostgreSQL default |
| Connection Method | Unix socket | Cloud SQL best practice |

**Important:** If your actual database name, user, or password are different, you MUST update the configuration before deploying.

## Troubleshooting

See `DATABASE_CREDENTIALS_SETUP.md` for detailed troubleshooting steps.

Common issues:
- Secret not found → Create it using step 1 above
- Permission denied → Grant access using step 2 above
- Wrong password → Update the secret value
- Wrong database/user → Update cloudbuild.yaml files

## Security Notes

✅ **Good practices implemented:**
- Password stored in Secret Manager (not in code)
- Using Cloud SQL Unix socket (more secure than TCP)
- No credentials committed to repository
- Secret access granted only to Cloud Run service account

❌ **Don't do this:**
- Don't put passwords in cloudbuild.yaml
- Don't commit .env files with real credentials
- Don't use the default postgres user in production
