# Fix for Missing Secrets Error in Cloud Run Deployment

## Problem

The Cloud Run deployment was failing with the following error:

```
ERROR: (gcloud.run.deploy) spec.template.spec.containers[0].env[1].value_from.secret_key_ref.name: 
Secret projects/502095789065/secrets/smtp-password/versions/latest was not found

spec.template.spec.containers[0].env[2].value_from.secret_key_ref.name: 
Secret projects/502095789065/secrets/cron-secret/versions/latest was not found
```

## Root Cause

The existing Cloud Run service had environment variables configured to reference secrets (`smtp-password` and `cron-secret`) in Google Secret Manager, but these secrets were never created. When redeploying, Cloud Run attempted to maintain these secret references, causing the deployment to fail.

## Solution

Updated both `cloudbuild.yaml` and `cloudbuild-rnrltradehub.yaml` files to:

1. **Remove secret references**: Added `--remove-secrets=SMTP_PASSWORD,CRON_SECRET` flag to explicitly clear the old secret references from the Cloud Run service.

2. **Set as environment variables**: Added `SMTP_PASSWORD=` and `CRON_SECRET=change-this-in-production` to `--set-env-vars` to provide these values as regular environment variables instead of secrets.

## Changes Made

### Files Modified

1. **cloudbuild.yaml** (erp-nonprod-backend service)
2. **cloudbuild-rnrltradehub.yaml** (rnrltradehub-nonprod service)
3. **test_cloudbuild_config.py** (new test file)

### Key Changes

```yaml
# Before
'--update-secrets=DB_PASSWORD=erp-nonprod-db-password:latest',
'--set-env-vars=DB_HOST=...,DB_NAME=...'

# After
'--update-secrets=DB_PASSWORD=erp-nonprod-db-password:latest',
'--remove-secrets=SMTP_PASSWORD,CRON_SECRET',
'--set-env-vars=DB_HOST=...,DB_NAME=...,SMTP_PASSWORD=,CRON_SECRET=change-this-in-production'
```

## Why This Works

1. **Matches code defaults**: The values match the fallback defaults in the application code:
   - `services/smtp_service.py`: `SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")`
   - `routes_scheduler.py`: `CRON_SECRET = os.getenv("CRON_SECRET", "change-this-in-production")`

2. **Safe for disabled features**: 
   - SMTP is disabled by default (`SMTP_ENABLED=false`), so an empty password is safe
   - CRON_SECRET has a placeholder value that can be updated when the scheduler is enabled

3. **Explicit secret removal**: The `--remove-secrets` flag ensures Cloud Run removes the old secret references before applying the new configuration

## Testing

A test script was added to validate the configuration:

```bash
python3 test_cloudbuild_config.py
```

This test verifies:
- ✓ Both cloudbuild files have the `--remove-secrets` flag
- ✓ Both files set `SMTP_PASSWORD` and `CRON_SECRET` as environment variables
- ✓ `DB_PASSWORD` still uses Secret Manager (not affected by this fix)

## Deployment

To deploy with the fix:

```bash
# For erp-nonprod-backend service
gcloud builds submit --config=cloudbuild.yaml

# For rnrltradehub-nonprod service
gcloud builds submit --config=cloudbuild-rnrltradehub.yaml
```

Or use the deployment script:

```bash
./deploy.sh
```

## Verification Steps

After deployment succeeds:

1. **Verify the service is running**:
   ```bash
   gcloud run services describe erp-nonprod-backend --region=us-central1
   ```

2. **Check environment variables**:
   ```bash
   gcloud run services describe erp-nonprod-backend --region=us-central1 --format="value(spec.template.spec.containers[0].env)"
   ```

3. **Verify secrets are removed**:
   The output should NOT show any references to `smtp-password` or `cron-secret` secrets.

4. **Test the endpoints**:
   ```bash
   SERVICE_URL=$(gcloud run services describe erp-nonprod-backend --region=us-central1 --format='value(status.url)')
   curl $SERVICE_URL/health
   ```

## Future: Enabling SMTP and Scheduler with Secrets

When ready to enable SMTP and scheduler with proper secrets:

### 1. Create the secrets in Secret Manager

```bash
# Generate a secure CRON_SECRET
CRON_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Create smtp-password secret
echo -n "YOUR_GMAIL_APP_PASSWORD" | gcloud secrets create smtp-password \
  --data-file=- \
  --project=google-mpf-cas7ishusxmu \
  --replication-policy=automatic

# Create cron-secret
echo -n "$CRON_SECRET" | gcloud secrets create cron-secret \
  --data-file=- \
  --project=google-mpf-cas7ishusxmu \
  --replication-policy=automatic

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding smtp-password \
  --member="serviceAccount:502095789065-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=google-mpf-cas7ishusxmu

gcloud secrets add-iam-policy-binding cron-secret \
  --member="serviceAccount:502095789065-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=google-mpf-cas7ishusxmu
```

### 2. Update cloudbuild.yaml

Change the configuration to use secrets:

```yaml
'--update-secrets=DB_PASSWORD=erp-nonprod-db-password:latest,SMTP_PASSWORD=smtp-password:latest,CRON_SECRET=cron-secret:latest',
'--set-env-vars=DB_HOST=...,SMTP_ENABLED=true,...'
```

### 3. Redeploy

```bash
gcloud builds submit --config=cloudbuild.yaml
```

## References

- Google Cloud Run Documentation: https://cloud.google.com/run/docs/configuring/secrets
- EMAIL_SCHEDULER_SETUP.md: Complete guide for SMTP and scheduler configuration
- DATABASE_CREDENTIALS_SETUP.md: Guide for database secrets setup

## Summary

The fix ensures successful deployment by:
1. Removing references to non-existent secrets
2. Providing default values as environment variables
3. Maintaining backward compatibility with the application code
4. Allowing future migration to Secret Manager when needed

The deployment should now succeed without errors.
