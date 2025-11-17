#!/bin/bash
# Cleanup Script for Duplicate Files
# This script removes all identified duplicate and unused files
# Generated from duplicate analysis

echo "RNRL TradeHub Backend - Cleanup Script"
echo "========================================"
echo ""
echo "This script will delete 29 files (1 code file + 28 documentation files)"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Starting cleanup..."
echo ""

# Function to delete file and report
delete_file() {
    local file=$1
    if [ -f "$file" ]; then
        rm "$file"
        echo "✓ Deleted: $file"
    else
        echo "⚠ Not found: $file"
    fi
}

# Delete code file
echo "=== Deleting Code Files ==="
delete_file "routes.py"
echo ""

# Delete database-related documentation
echo "=== Deleting Database-Related Documentation ==="
delete_file "DATABASE_CONNECTION_ERROR_FIX.md"
delete_file "DATABASE_CONNECTION_QUICK_SUMMARY.md"
delete_file "DATABASE_CONNECTION_VERIFICATION.md"
delete_file "DATABASE_FIX_QUICK_REFERENCE.md"
delete_file "NO_DUPLICATION_VERIFICATION.md"
echo ""

# Delete fix documentation
echo "=== Deleting Fix Documentation ==="
delete_file "COMPLETE_FIX.md"
delete_file "FIX_ENUM_SERIALIZATION_BUG.md"
delete_file "FIX_SETTINGS_USERS_500_ERROR.md"
delete_file "FIX_SUMMARY.md"
delete_file "README_SOLUTION.md"
delete_file "SETTINGS_USERS_API.md"
echo ""

# Delete deployment documentation
echo "=== Deleting Deployment Documentation ==="
delete_file "CLOUD_RUN_DEPLOYMENT.md"
delete_file "DEPLOYMENT_COMPLETE.md"
delete_file "SERVICE_DEPLOYMENT_RESOLUTION.md"
echo ""

# Delete implementation status documentation
echo "=== Deleting Implementation Status Documentation ==="
delete_file "IMPLEMENTATION_COMPLETE.md"
delete_file "IMPLEMENTATION_STATUS.md"
delete_file "IMPLEMENTATION_SUMMARY.md"
delete_file "PHASES_5_6_SUMMARY.md"
delete_file "PHASE_1_2_COMPLETE.md"
delete_file "SOLUTION_SUMMARY.md"
delete_file "SOLUTION_VERIFICATION.md"
echo ""

# Delete verification documents
echo "=== Deleting Verification Documents ==="
delete_file "VALIDATION_AND_EXPORT.md"
delete_file "QUICK_DEPLOY.md"
delete_file "EMAIL_SCHEDULER_SETUP.md"
echo ""

echo "========================================"
echo "Cleanup completed!"
echo ""
echo "Next steps:"
echo "1. Review the changes with 'git status'"
echo "2. Run tests to ensure nothing broke"
echo "3. Commit the changes with git"
echo ""
echo "Note: To delete branches, you need repository admin permissions."
echo "See FILES_TO_DELETE.md for the list of branches to delete."
