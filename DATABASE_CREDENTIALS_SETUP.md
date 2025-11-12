# Database Credentials Setup for Cloud Run

This guide explains how to configure database credentials for the RNRL TradeHub Backend when deploying to Google Cloud Run.

## Overview

The application connects to a Cloud SQL PostgreSQL database using environment variables. The database password is stored securely in Google Cloud Secret Manager to avoid exposing it in configuration files.

## Prerequisites

- Google Cloud SDK (`gcloud`) installed and configured
- Appropriate IAM permissions:
  - `secretmanager.admin` or `secretmanager.secretAccessor` for Secret Manager
  - `run.admin` for Cloud Run
  - `cloudsql.client` for Cloud SQL

## Database Configuration

The application uses the following environment variables for database connection:

- **DB_HOST**: The Cloud SQL instance connection path (Unix socket)
- **DB_NAME**: The database name
- **DB_USER**: The database username
- **DB_PASSWORD**: The database password (stored in Secret Manager)
- **DB_PORT**: The database port (default: 5432)

## Current Configuration

Based on the error message, the application is connecting to:

- **Cloud SQL Instance**: `google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db`
- **Database Name**: `erp_nonprod` (update if different)
- **Database User**: `erp_user` (update if different)
- **Connection Method**: Unix socket at `/cloudsql/google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db`

## Setup Instructions

### Step 1: Verify Cloud SQL Instance

First, verify your Cloud SQL instance exists and note its connection name:

```bash
# List Cloud SQL instances
gcloud sql instances list

# Get instance details
gcloud sql instances describe erp-nonprod-db --format="value(connectionName)"
```

Expected output: `google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db`

### Step 2: Verify Database and User

Connect to your Cloud SQL instance to verify the database and user exist:

```bash
# Connect to Cloud SQL
gcloud sql connect erp-nonprod-db --user=postgres

# In the PostgreSQL prompt:
# List databases
\l

# List users
\du

# Connect to your database
\c erp_nonprod

# Verify the user has appropriate permissions
```

If the database or user doesn't exist, create them:

```sql
-- Create database (if needed)
CREATE DATABASE erp_nonprod;

-- Create user (if needed)
CREATE USER erp_user WITH PASSWORD 'your-secure-password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE erp_nonprod TO erp_user;

-- Connect to the database
\c erp_nonprod

-- Grant schema privileges
GRANT ALL PRIVILEGES ON SCHEMA public TO erp_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO erp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO erp_user;
```

### Step 3: Store Database Password in Secret Manager

Create a secret in Google Cloud Secret Manager for the database password:

```bash
# Create the secret with the database password
echo -n "your-secure-password" | gcloud secrets create erp-nonprod-db-password \
    --data-file=- \
    --replication-policy="automatic"

# Verify the secret was created
gcloud secrets list | grep erp-nonprod-db-password
```

**Important**: Replace `your-secure-password` with the actual password for the `erp_user` database user.

### Step 4: Grant Cloud Run Access to Secret

The Cloud Run service account needs permission to access the secret:

```bash
# Get the project number
PROJECT_NUMBER=$(gcloud projects describe google-mpf-cas7ishusxmu --format="value(projectNumber)")

# Grant the Cloud Run service account access to the secret
gcloud secrets add-iam-policy-binding erp-nonprod-db-password \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 5: Deploy the Application

Deploy using Cloud Build, which will automatically configure the environment variables:

```bash
# Deploy to erp-nonprod-backend service
gcloud builds submit --config=cloudbuild.yaml

# OR deploy to rnrltradehub-nonprod service
gcloud builds submit --config=cloudbuild-rnrltradehub.yaml
```

The cloudbuild configuration will:
1. Connect Cloud Run to the Cloud SQL instance
2. Set environment variables for DB_HOST, DB_NAME, DB_USER, DB_PORT
3. Mount the DB_PASSWORD secret from Secret Manager

### Step 6: Verify the Deployment

After deployment, verify the database connection:

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe erp-nonprod-backend \
    --region=us-central1 \
    --format='value(status.url)')

# Test the health endpoint
curl $SERVICE_URL/health

# Expected response should show database as "connected":
# {
#   "status": "healthy",
#   "service": "rnrltradehub-nonprod",
#   "version": "1.0.0",
#   "database": "connected"
# }
```

## Updating Database Credentials

### Update the Database Password

If you need to update the database password:

```bash
# Update the password in Cloud SQL first
gcloud sql users set-password erp_user \
    --instance=erp-nonprod-db \
    --password=new-secure-password

# Update the secret in Secret Manager
echo -n "new-secure-password" | gcloud secrets versions add erp-nonprod-db-password \
    --data-file=-

# Redeploy the service (it will use the latest version of the secret)
gcloud builds submit --config=cloudbuild.yaml
```

### Update Database Name or User

If you need to change the database name or username:

1. Update the values in the cloudbuild.yaml file:

```yaml
'--set-env-vars=DB_HOST=/cloudsql/google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db,DB_NAME=new_database_name,DB_USER=new_user,DB_PORT=5432'
```

2. Update the secret name if needed (or create a new secret for the new user)

3. Redeploy using Cloud Build

## Troubleshooting

### Error: "password authentication failed"

This error means the database password is incorrect or not properly set. Check:

1. The secret exists and contains the correct password:
   ```bash
   gcloud secrets versions access latest --secret=erp-nonprod-db-password
   ```

2. The Cloud Run service has access to the secret:
   ```bash
   gcloud secrets get-iam-policy erp-nonprod-db-password
   ```

3. The database user has the correct password:
   ```bash
   # Connect to Cloud SQL and verify
   gcloud sql connect erp-nonprod-db --user=postgres
   # Then change password if needed:
   # ALTER USER erp_user WITH PASSWORD 'correct-password';
   ```

### Error: "could not connect to server"

This error means the Cloud SQL connection is not properly configured. Check:

1. The Cloud SQL instance connection is added to Cloud Run:
   ```bash
   gcloud run services describe erp-nonprod-backend \
       --region=us-central1 \
       --format='value(spec.template.metadata.annotations.run.googleapis.com/cloudsql-instances)'
   ```

2. The DB_HOST environment variable is correctly set:
   ```bash
   gcloud run services describe erp-nonprod-backend \
       --region=us-central1 \
       --format='value(spec.template.spec.containers[0].env)'
   ```

### Verify Environment Variables

To check all environment variables in Cloud Run:

```bash
gcloud run services describe erp-nonprod-backend \
    --region=us-central1 \
    --format='yaml(spec.template.spec.containers[0].env)'
```

Expected output should include:
- DB_HOST
- DB_NAME
- DB_USER
- DB_PORT
- DB_PASSWORD (shown as secret reference)

## Security Best Practices

1. **Never commit passwords**: Database passwords should never be committed to version control
2. **Use Secret Manager**: Always store sensitive credentials in Secret Manager
3. **Rotate passwords regularly**: Update database passwords periodically
4. **Use least privilege**: Grant only necessary permissions to database users
5. **Enable Cloud SQL IAM authentication**: Consider using Cloud SQL IAM authentication instead of password-based auth for enhanced security

## Alternative: Using DATABASE_URL

Instead of individual environment variables, you can also use a single DATABASE_URL:

1. Create a secret with the full connection string:
   ```bash
   echo -n "postgresql://erp_user:your-password@/erp_nonprod?host=/cloudsql/google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db" | \
       gcloud secrets create erp-nonprod-database-url --data-file=- --replication-policy="automatic"
   ```

2. Update cloudbuild.yaml to use the DATABASE_URL secret:
   ```yaml
   '--update-secrets=DATABASE_URL=erp-nonprod-database-url:latest'
   ```

## Support

For additional help:
- Review logs: `gcloud run services logs read erp-nonprod-backend --region=us-central1`
- Check [DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md)
- Verify startup: `python verify_startup.py`
