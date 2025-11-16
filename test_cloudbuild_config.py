#!/usr/bin/env python3
"""
Test Cloud Build Configuration Files.

This script validates that the cloudbuild.yaml files are properly formatted
and contain the necessary configuration to fix the missing secrets error.
"""
import yaml
import sys


def test_cloudbuild_yaml():
    """Test cloudbuild.yaml configuration."""
    print("Testing cloudbuild.yaml...")
    
    with open('cloudbuild.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Check basic structure
    assert 'steps' in config, "Missing 'steps' in cloudbuild.yaml"
    assert len(config['steps']) == 3, f"Expected 3 steps, found {len(config['steps'])}"
    
    # Check the deploy step (step 3)
    deploy_step = config['steps'][2]
    assert deploy_step['name'] == 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
    
    args = deploy_step['args']
    args_str = ' '.join(args)
    
    # Verify the fix for missing secrets
    assert '--remove-secrets=SMTP_PASSWORD,CRON_SECRET' in args, \
        "Missing --remove-secrets flag to clear old secret references"
    
    # Verify environment variables are set
    env_vars_arg = [arg for arg in args if arg.startswith('--set-env-vars=')]
    assert len(env_vars_arg) == 1, "Missing --set-env-vars argument"
    
    env_vars = env_vars_arg[0]
    assert 'SMTP_PASSWORD=' in env_vars, "Missing SMTP_PASSWORD in env vars"
    assert 'CRON_SECRET=change-this-in-production' in env_vars, \
        "Missing CRON_SECRET in env vars"
    
    # Verify DB_PASSWORD is still using secrets (not affected by this fix)
    assert '--update-secrets=DB_PASSWORD=erp-nonprod-db-password:latest' in args, \
        "DB_PASSWORD secret configuration is missing"
    
    print("✓ cloudbuild.yaml is valid and contains the fix")
    return True


def test_cloudbuild_rnrltradehub_yaml():
    """Test cloudbuild-rnrltradehub.yaml configuration."""
    print("\nTesting cloudbuild-rnrltradehub.yaml...")
    
    with open('cloudbuild-rnrltradehub.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Check basic structure
    assert 'steps' in config, "Missing 'steps' in cloudbuild-rnrltradehub.yaml"
    assert len(config['steps']) == 3, f"Expected 3 steps, found {len(config['steps'])}"
    
    # Check the deploy step (step 3)
    deploy_step = config['steps'][2]
    assert deploy_step['name'] == 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
    
    args = deploy_step['args']
    args_str = ' '.join(args)
    
    # Verify the fix for missing secrets
    assert '--remove-secrets=SMTP_PASSWORD,CRON_SECRET' in args, \
        "Missing --remove-secrets flag to clear old secret references"
    
    # Verify environment variables are set
    env_vars_arg = [arg for arg in args if arg.startswith('--set-env-vars=')]
    assert len(env_vars_arg) == 1, "Missing --set-env-vars argument"
    
    env_vars = env_vars_arg[0]
    assert 'SMTP_PASSWORD=' in env_vars, "Missing SMTP_PASSWORD in env vars"
    assert 'CRON_SECRET=change-this-in-production' in env_vars, \
        "Missing CRON_SECRET in env vars"
    
    # Verify DB_PASSWORD is still using secrets (not affected by this fix)
    assert '--update-secrets=DB_PASSWORD=erp-nonprod-db-password:latest' in args, \
        "DB_PASSWORD secret configuration is missing"
    
    print("✓ cloudbuild-rnrltradehub.yaml is valid and contains the fix")
    return True


def main():
    """Run all tests."""
    try:
        test_cloudbuild_yaml()
        test_cloudbuild_rnrltradehub_yaml()
        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60)
        print("\nThe cloudbuild configurations are correct and should fix the")
        print("missing secrets error during deployment.")
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
