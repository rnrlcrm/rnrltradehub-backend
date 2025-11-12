#!/usr/bin/env python3
"""
Verification script for /api/settings/users endpoint fix.

This script can be run against a deployed instance to verify that the
500 Internal Server Error has been resolved.

Usage:
    python verify_settings_users_fix.py [BASE_URL]

Example:
    python verify_settings_users_fix.py https://erp-nonprod-backend-502095789065.us-central1.run.app
"""
import sys
import requests
import json


def verify_endpoint(base_url):
    """
    Verify that the /api/settings/users endpoint is working correctly.
    
    Args:
        base_url: Base URL of the API (e.g., https://api.example.com)
    
    Returns:
        bool: True if endpoint is working, False otherwise
    """
    endpoint = f"{base_url}/api/settings/users"
    
    print("=" * 70)
    print("Verifying /api/settings/users endpoint")
    print("=" * 70)
    print(f"\nEndpoint: {endpoint}")
    print("\nSending GET request...")
    
    try:
        response = requests.get(endpoint, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'access-control-allow-origin']:
                print(f"  {key}: {value}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS! Endpoint returned 200 OK")
            
            try:
                data = response.json()
                print(f"\nResponse Type: {type(data)}")
                print(f"Number of users: {len(data) if isinstance(data, list) else 'N/A'}")
                
                if isinstance(data, list) and len(data) > 0:
                    print("\nFirst user structure:")
                    first_user = data[0]
                    for key in ['id', 'name', 'email', 'role_id', 'role_name', 'is_active', 'user_type']:
                        if key in first_user:
                            print(f"  {key}: {first_user[key]}")
                    
                    # Verify role_name is present and properly formatted
                    if 'role_name' in first_user:
                        role_name = first_user['role_name']
                        if role_name is None or isinstance(role_name, str):
                            print("\n✅ role_name field is correctly formatted (string or null)")
                        else:
                            print(f"\n⚠️  role_name has unexpected type: {type(role_name)}")
                    
                    # Verify user_type is a string
                    if 'user_type' in first_user:
                        user_type = first_user['user_type']
                        if isinstance(user_type, str):
                            print("✅ user_type field is correctly formatted (string)")
                        else:
                            print(f"⚠️  user_type has unexpected type: {type(user_type)}")
                
                elif isinstance(data, list):
                    print("\n⚠️  No users found in response (empty list)")
                
                print("\n" + "=" * 70)
                print("VERIFICATION PASSED - Endpoint is working correctly!")
                print("=" * 70)
                return True
                
            except json.JSONDecodeError as e:
                print(f"\n❌ Failed to parse JSON response: {e}")
                print(f"Response content: {response.text[:200]}")
                return False
        
        elif response.status_code == 500:
            print("\n❌ FAILED! Endpoint still returning 500 Internal Server Error")
            print("\nThis indicates the fix has not been deployed or there's another issue.")
            print(f"\nResponse content: {response.text[:500]}")
            print("\n" + "=" * 70)
            print("VERIFICATION FAILED")
            print("=" * 70)
            return False
        
        else:
            print(f"\n⚠️  Unexpected status code: {response.status_code}")
            print(f"Response content: {response.text[:500]}")
            print("\n" + "=" * 70)
            print("VERIFICATION INCONCLUSIVE")
            print("=" * 70)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        print("\n" + "=" * 70)
        print("VERIFICATION FAILED - Unable to connect to endpoint")
        print("=" * 70)
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        base_url = "https://erp-nonprod-backend-502095789065.us-central1.run.app"
        print(f"No URL provided, using default: {base_url}")
        print("Usage: python verify_settings_users_fix.py [BASE_URL]\n")
    
    success = verify_endpoint(base_url)
    sys.exit(0 if success else 1)
