# Database Migrations

This directory contains SQL migration scripts for the RNRL TradeHub Backend database schema.

## Migration Files

### 001_enhanced_access_control_schema.sql
**Phase 1: Enhanced Access Control Schema**

This migration implements the database schema for:

1. **Enhanced User Management** (Phase 1.1)
   - Extended users table with new columns
   - User branch assignments for multi-branch access control
   - Sub-users table with max 2 per parent constraint

2. **Business Branches** (Phase 1.2)
   - Multi-branch support for business partners
   - GST number tracking per branch
   - Head office designation

3. **Amendment System** (Phase 1.3)
   - Amendment requests with approval workflow
   - Business partner version history
   - Complete audit trail

4. **Self-Service Onboarding** (Phase 1.4)
   - Onboarding applications table
   - Application status tracking

5. **User Profile & KYC Management** (Phase 1.5)
   - Profile update requests
   - KYC verifications with due dates
   - KYC reminder logs

6. **Dynamic RBAC System** (Phase 1.6)
   - Custom modules and permissions
   - Role-permission mappings
   - User-specific permission overrides

7. **Enhanced Audit Trail** (Phase 1.7)
   - Extended audit_logs table
   - Suspicious activities tracking

## How to Run Migrations

### Option 1: Using psql (Direct SQL execution)

```bash
# Connect to your PostgreSQL database
psql -h <host> -U <username> -d <database> -f migrations/001_enhanced_access_control_schema.sql
```

### Option 2: Using Alembic (Python migrations)

```bash
# Generate migration from models
alembic revision --autogenerate -m "Enhanced access control schema"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Option 3: Using Docker/Cloud SQL

```bash
# For Google Cloud SQL
gcloud sql connect <instance-name> --user=<username> < migrations/001_enhanced_access_control_schema.sql
```

## Migration Safety

All migrations in this directory are designed to be:

- **Idempotent**: Can be run multiple times without errors (using `IF NOT EXISTS`)
- **Non-destructive**: Do not drop or truncate existing tables
- **Backward compatible**: Add new tables/columns without breaking existing functionality

## Environment-Specific Migrations

For production deployments:

1. Always backup the database before running migrations
2. Test migrations in staging environment first
3. Run migrations during maintenance windows if possible
4. Monitor application logs after migration

## Rollback Plan

If you need to rollback migrations:

1. Restore from database backup
2. Or manually drop added tables/columns (see rollback SQL below)

### Rollback SQL for 001_enhanced_access_control_schema.sql

```sql
-- WARNING: This will delete all data in these tables!
-- Only use if you need to completely rollback the migration

DROP TABLE IF EXISTS suspicious_activities CASCADE;
DROP TABLE IF EXISTS user_permission_overrides CASCADE;
DROP TABLE IF EXISTS role_permissions CASCADE;
DROP TABLE IF EXISTS custom_permissions CASCADE;
DROP TABLE IF EXISTS custom_modules CASCADE;
DROP TABLE IF EXISTS kyc_reminder_logs CASCADE;
DROP TABLE IF EXISTS kyc_verifications CASCADE;
DROP TABLE IF EXISTS profile_update_requests CASCADE;
DROP TABLE IF EXISTS onboarding_applications CASCADE;
DROP TABLE IF EXISTS business_partner_versions CASCADE;
DROP TABLE IF EXISTS amendment_requests CASCADE;
DROP TABLE IF EXISTS business_branches CASCADE;
DROP TABLE IF EXISTS sub_users CASCADE;
DROP TABLE IF EXISTS user_branches CASCADE;

-- Remove added columns from users table
ALTER TABLE users DROP COLUMN IF EXISTS last_activity_at;
ALTER TABLE users DROP COLUMN IF EXISTS locked_until;
ALTER TABLE users DROP COLUMN IF EXISTS failed_login_attempts;
ALTER TABLE users DROP COLUMN IF EXISTS password_expiry_date;
ALTER TABLE users DROP COLUMN IF EXISTS is_first_login;
ALTER TABLE users DROP COLUMN IF EXISTS user_type_new;
ALTER TABLE users DROP COLUMN IF EXISTS business_partner_id;

-- Remove added columns from audit_logs table
ALTER TABLE audit_logs DROP COLUMN IF EXISTS new_values;
ALTER TABLE audit_logs DROP COLUMN IF EXISTS old_values;
ALTER TABLE audit_logs DROP COLUMN IF EXISTS entity_id;
ALTER TABLE audit_logs DROP COLUMN IF EXISTS session_id;
ALTER TABLE audit_logs DROP COLUMN IF EXISTS geo_location;
ALTER TABLE audit_logs DROP COLUMN IF EXISTS user_agent;
ALTER TABLE audit_logs DROP COLUMN IF EXISTS ip_address;

-- Drop trigger and function
DROP TRIGGER IF EXISTS enforce_max_sub_users ON sub_users;
DROP FUNCTION IF EXISTS check_max_sub_users();
```

## Verification

After running migrations, verify they were successful:

```sql
-- Check if new tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN (
    'user_branches', 'sub_users', 'business_branches',
    'amendment_requests', 'business_partner_versions',
    'onboarding_applications', 'profile_update_requests',
    'kyc_verifications', 'kyc_reminder_logs',
    'custom_modules', 'custom_permissions',
    'role_permissions', 'user_permission_overrides',
    'suspicious_activities'
  );

-- Check if new columns were added to users table
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
  AND column_name IN (
    'business_partner_id', 'user_type_new', 'is_first_login',
    'password_expiry_date', 'failed_login_attempts', 
    'locked_until', 'last_activity_at'
  );

-- Check if new columns were added to audit_logs table
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'audit_logs' 
  AND column_name IN (
    'ip_address', 'user_agent', 'geo_location',
    'session_id', 'entity_id', 'old_values', 'new_values'
  );
```

## Next Steps

After running this migration:

1. Update your application code to use the new tables
2. Implement API endpoints for the new features
3. Add business logic for amendments, KYC, and onboarding
4. Configure automation services (KYC reminders, auto-approval)
5. Set up email templates for notifications

## Support

For questions or issues with migrations:
- Review the SQL file comments for table documentation
- Check the main README.md for database connection details
- See DATABASE_SCHEMA.md for complete schema documentation
