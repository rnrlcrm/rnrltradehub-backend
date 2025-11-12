-- Migration: Enhanced Access Control Schema (Phase 1)
-- Description: Adds new tables and columns for enhanced access control, business partner management,
--              amendment system, self-service onboarding, KYC management, and dynamic RBAC

-- ============================================================================
-- PHASE 1.1: Enhanced User Management
-- ============================================================================

-- Add new columns to existing users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS business_partner_id VARCHAR(36);
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_type_new VARCHAR(50) DEFAULT 'back_office';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_first_login BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_expiry_date TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMP;

-- Add foreign key constraint for business_partner_id (will be added after business_branches table is created)
-- ALTER TABLE users ADD CONSTRAINT fk_users_business_partner FOREIGN KEY (business_partner_id) REFERENCES business_partners(id);

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_users_business_partner_id ON users(business_partner_id);
CREATE INDEX IF NOT EXISTS idx_users_last_activity_at ON users(last_activity_at);

-- User branch assignments table
CREATE TABLE IF NOT EXISTS user_branches (
  id VARCHAR(36) PRIMARY KEY,
  user_id INTEGER NOT NULL,
  branch_id VARCHAR(36) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_user_branches_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_user_branches_branch FOREIGN KEY (branch_id) REFERENCES business_branches(id) ON DELETE CASCADE,
  UNIQUE(user_id, branch_id)
);

CREATE INDEX IF NOT EXISTS idx_user_branches_user_id ON user_branches(user_id);
CREATE INDEX IF NOT EXISTS idx_user_branches_branch_id ON user_branches(branch_id);

-- Sub-users table (max 2 per parent)
CREATE TABLE IF NOT EXISTS sub_users (
  id VARCHAR(36) PRIMARY KEY,
  parent_user_id INTEGER NOT NULL,
  sub_user_id INTEGER NOT NULL UNIQUE,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_sub_users_parent FOREIGN KEY (parent_user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_sub_users_sub_user FOREIGN KEY (sub_user_id) REFERENCES users(id) ON DELETE CASCADE,
  CHECK (parent_user_id != sub_user_id)
);

CREATE INDEX IF NOT EXISTS idx_sub_users_parent_id ON sub_users(parent_user_id);
CREATE INDEX IF NOT EXISTS idx_sub_users_sub_user_id ON sub_users(sub_user_id);

-- Function to enforce max 2 sub-users per parent
CREATE OR REPLACE FUNCTION check_max_sub_users()
RETURNS TRIGGER AS $$
BEGIN
  IF (SELECT COUNT(*) FROM sub_users 
      WHERE parent_user_id = NEW.parent_user_id AND is_active = true) >= 2 THEN
    RAISE EXCEPTION 'Maximum 2 sub-users allowed per parent user';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to enforce max sub-users constraint
DROP TRIGGER IF EXISTS enforce_max_sub_users ON sub_users;
CREATE TRIGGER enforce_max_sub_users
  BEFORE INSERT ON sub_users
  FOR EACH ROW
  EXECUTE FUNCTION check_max_sub_users();

-- ============================================================================
-- PHASE 1.2: Business Branches (Multi-Branch Support)
-- ============================================================================

CREATE TABLE IF NOT EXISTS business_branches (
  id VARCHAR(36) PRIMARY KEY,
  partner_id VARCHAR(36) NOT NULL,
  branch_code VARCHAR(50) NOT NULL,
  branch_name VARCHAR(255) NOT NULL,
  state VARCHAR(100) NOT NULL,
  gst_number VARCHAR(15) UNIQUE NOT NULL,
  address JSONB NOT NULL,
  contact_person JSONB,
  bank_details JSONB,
  is_head_office BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_business_branches_partner FOREIGN KEY (partner_id) REFERENCES business_partners(id) ON DELETE CASCADE,
  UNIQUE(partner_id, branch_code)
);

CREATE INDEX IF NOT EXISTS idx_business_branches_partner_id ON business_branches(partner_id);
CREATE INDEX IF NOT EXISTS idx_business_branches_gst_number ON business_branches(gst_number);

-- Ensure only one head office per partner
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_head_office_per_partner 
  ON business_branches(partner_id) 
  WHERE is_head_office = true;

-- ============================================================================
-- PHASE 1.3: Amendment System with Version Control
-- ============================================================================

CREATE TABLE IF NOT EXISTS amendment_requests (
  id VARCHAR(36) PRIMARY KEY,
  entity_type VARCHAR(50) NOT NULL,
  entity_id VARCHAR(36) NOT NULL,
  request_type VARCHAR(50) NOT NULL,
  reason TEXT NOT NULL,
  justification TEXT,
  requested_by INTEGER NOT NULL,
  requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(50) DEFAULT 'PENDING',
  reviewed_by INTEGER,
  reviewed_at TIMESTAMP,
  review_notes TEXT,
  changes JSONB NOT NULL,
  impact_assessment JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_amendment_requests_requester FOREIGN KEY (requested_by) REFERENCES users(id),
  CONSTRAINT fk_amendment_requests_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_amendment_requests_entity ON amendment_requests(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_amendment_requests_status ON amendment_requests(status);
CREATE INDEX IF NOT EXISTS idx_amendment_requests_requested_by ON amendment_requests(requested_by);

-- Version history for business partners
CREATE TABLE IF NOT EXISTS business_partner_versions (
  id VARCHAR(36) PRIMARY KEY,
  partner_id VARCHAR(36) NOT NULL,
  version INTEGER NOT NULL,
  data JSONB NOT NULL,
  changed_by INTEGER,
  change_reason TEXT,
  amendment_request_id VARCHAR(36),
  valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  valid_to TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_business_partner_versions_partner FOREIGN KEY (partner_id) REFERENCES business_partners(id) ON DELETE CASCADE,
  CONSTRAINT fk_business_partner_versions_user FOREIGN KEY (changed_by) REFERENCES users(id),
  CONSTRAINT fk_business_partner_versions_amendment FOREIGN KEY (amendment_request_id) REFERENCES amendment_requests(id),
  UNIQUE(partner_id, version)
);

CREATE INDEX IF NOT EXISTS idx_business_partner_versions_partner_id ON business_partner_versions(partner_id);
CREATE INDEX IF NOT EXISTS idx_business_partner_versions_version ON business_partner_versions(version);

-- ============================================================================
-- PHASE 1.4: Self-Service Onboarding
-- ============================================================================

CREATE TABLE IF NOT EXISTS onboarding_applications (
  id VARCHAR(36) PRIMARY KEY,
  application_number VARCHAR(50) UNIQUE NOT NULL,
  company_info JSONB NOT NULL,
  contact_info JSONB NOT NULL,
  compliance_info JSONB NOT NULL,
  branch_info JSONB,
  documents JSONB,
  status VARCHAR(50) DEFAULT 'SUBMITTED',
  review_notes TEXT,
  reviewed_by INTEGER,
  reviewed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_onboarding_applications_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_onboarding_applications_number ON onboarding_applications(application_number);
CREATE INDEX IF NOT EXISTS idx_onboarding_applications_status ON onboarding_applications(status);

-- ============================================================================
-- PHASE 1.5: User Profile & KYC Management
-- ============================================================================

-- User profile update requests
CREATE TABLE IF NOT EXISTS profile_update_requests (
  id VARCHAR(36) PRIMARY KEY,
  user_id INTEGER NOT NULL,
  partner_id VARCHAR(36),
  update_type VARCHAR(50) NOT NULL,
  old_values JSONB NOT NULL,
  new_values JSONB NOT NULL,
  reason TEXT,
  status VARCHAR(50) DEFAULT 'PENDING',
  reviewed_by INTEGER,
  reviewed_at TIMESTAMP,
  review_notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_profile_update_requests_user FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_profile_update_requests_partner FOREIGN KEY (partner_id) REFERENCES business_partners(id),
  CONSTRAINT fk_profile_update_requests_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_profile_update_requests_user_id ON profile_update_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_profile_update_requests_partner_id ON profile_update_requests(partner_id);
CREATE INDEX IF NOT EXISTS idx_profile_update_requests_status ON profile_update_requests(status);

-- KYC verification records
CREATE TABLE IF NOT EXISTS kyc_verifications (
  id VARCHAR(36) PRIMARY KEY,
  partner_id VARCHAR(36) NOT NULL,
  verification_date TIMESTAMP NOT NULL,
  verified_by INTEGER NOT NULL,
  documents_checked JSONB NOT NULL,
  status VARCHAR(50) NOT NULL,
  next_due_date TIMESTAMP NOT NULL,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_kyc_verifications_partner FOREIGN KEY (partner_id) REFERENCES business_partners(id),
  CONSTRAINT fk_kyc_verifications_verifier FOREIGN KEY (verified_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_kyc_verifications_partner_id ON kyc_verifications(partner_id);
CREATE INDEX IF NOT EXISTS idx_kyc_verifications_status ON kyc_verifications(status);
CREATE INDEX IF NOT EXISTS idx_kyc_verifications_next_due_date ON kyc_verifications(next_due_date);

-- KYC reminder logs
CREATE TABLE IF NOT EXISTS kyc_reminder_logs (
  id VARCHAR(36) PRIMARY KEY,
  partner_id VARCHAR(36) NOT NULL,
  reminder_type VARCHAR(50) NOT NULL,
  sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  recipient_email VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_kyc_reminder_logs_partner FOREIGN KEY (partner_id) REFERENCES business_partners(id)
);

CREATE INDEX IF NOT EXISTS idx_kyc_reminder_logs_partner_id ON kyc_reminder_logs(partner_id);
CREATE INDEX IF NOT EXISTS idx_kyc_reminder_logs_sent_at ON kyc_reminder_logs(sent_at);

-- ============================================================================
-- PHASE 1.6: Dynamic RBAC System
-- ============================================================================

-- Custom modules (extensible)
CREATE TABLE IF NOT EXISTS custom_modules (
  id VARCHAR(36) PRIMARY KEY,
  module_key VARCHAR(100) UNIQUE NOT NULL,
  display_name VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(50),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_custom_modules_key ON custom_modules(module_key);

-- Custom permissions
CREATE TABLE IF NOT EXISTS custom_permissions (
  id VARCHAR(36) PRIMARY KEY,
  module_id VARCHAR(36) NOT NULL,
  permission_key VARCHAR(100) NOT NULL,
  action VARCHAR(50) NOT NULL,
  description TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_custom_permissions_module FOREIGN KEY (module_id) REFERENCES custom_modules(id) ON DELETE CASCADE,
  UNIQUE(module_id, permission_key, action)
);

CREATE INDEX IF NOT EXISTS idx_custom_permissions_module_id ON custom_permissions(module_id);

-- Role permissions
CREATE TABLE IF NOT EXISTS role_permissions (
  id VARCHAR(36) PRIMARY KEY,
  role_id INTEGER NOT NULL,
  permission_id VARCHAR(36) NOT NULL,
  granted BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_role_permissions_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
  CONSTRAINT fk_role_permissions_permission FOREIGN KEY (permission_id) REFERENCES custom_permissions(id) ON DELETE CASCADE,
  UNIQUE(role_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id);

-- User-specific permission overrides
CREATE TABLE IF NOT EXISTS user_permission_overrides (
  id VARCHAR(36) PRIMARY KEY,
  user_id INTEGER NOT NULL,
  permission_id VARCHAR(36) NOT NULL,
  granted BOOLEAN NOT NULL,
  reason TEXT,
  granted_by INTEGER,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_user_permission_overrides_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_user_permission_overrides_permission FOREIGN KEY (permission_id) REFERENCES custom_permissions(id) ON DELETE CASCADE,
  CONSTRAINT fk_user_permission_overrides_granter FOREIGN KEY (granted_by) REFERENCES users(id),
  UNIQUE(user_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_user_permission_overrides_user_id ON user_permission_overrides(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permission_overrides_permission_id ON user_permission_overrides(permission_id);

-- ============================================================================
-- PHASE 1.7: Enhanced Audit Trail & Activity Monitoring
-- ============================================================================

-- Enhance existing audit_logs table with new columns
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS ip_address INET;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_agent TEXT;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS geo_location JSONB;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS session_id VARCHAR(255);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS entity_id VARCHAR(36);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS old_values JSONB;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS new_values JSONB;

CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(module, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_session_id ON audit_logs(session_id);

-- Suspicious activities table
CREATE TABLE IF NOT EXISTS suspicious_activities (
  id VARCHAR(36) PRIMARY KEY,
  user_id INTEGER NOT NULL,
  activity_type VARCHAR(50) NOT NULL,
  details JSONB NOT NULL,
  risk_score INTEGER NOT NULL,
  detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  reviewed BOOLEAN DEFAULT false,
  reviewed_by INTEGER,
  reviewed_at TIMESTAMP,
  action_taken TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_suspicious_activities_user FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_suspicious_activities_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(id),
  CHECK (risk_score >= 0 AND risk_score <= 100)
);

CREATE INDEX IF NOT EXISTS idx_suspicious_activities_user_id ON suspicious_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_suspicious_activities_type ON suspicious_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_suspicious_activities_detected_at ON suspicious_activities(detected_at);
CREATE INDEX IF NOT EXISTS idx_suspicious_activities_reviewed ON suspicious_activities(reviewed);

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE user_branches IS 'Maps users to business branches for multi-branch access control';
COMMENT ON TABLE sub_users IS 'Sub-users table with max 2 per parent user constraint';
COMMENT ON TABLE business_branches IS 'Business branches for multi-branch business partner support';
COMMENT ON TABLE amendment_requests IS 'Amendment requests with approval workflow for entities';
COMMENT ON TABLE business_partner_versions IS 'Version history for business partners with audit trail';
COMMENT ON TABLE onboarding_applications IS 'Self-service onboarding applications from business partners';
COMMENT ON TABLE profile_update_requests IS 'User profile update requests requiring approval';
COMMENT ON TABLE kyc_verifications IS 'KYC verification records with due date tracking';
COMMENT ON TABLE kyc_reminder_logs IS 'Logs of KYC reminders sent to business partners';
COMMENT ON TABLE custom_modules IS 'Dynamic modules for extensible RBAC system';
COMMENT ON TABLE custom_permissions IS 'Dynamic permissions for fine-grained access control';
COMMENT ON TABLE role_permissions IS 'Role-permission mappings for RBAC';
COMMENT ON TABLE user_permission_overrides IS 'User-specific permission overrides with expiration';
COMMENT ON TABLE suspicious_activities IS 'Suspicious activity logs for security monitoring';
