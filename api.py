#!/usr/bin/env python3
"""
Quick API test to verify the server is working
Run this after starting the server to test basic functionality
"""

import requests
import json
import time


def test_server_connection():
    """Test if server is responding"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is responding")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False


def test_basic_endpoints():
    """Test basic endpoints that don't require authentication"""
    endpoints = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/api-info", "API info")
    ]

    print("\n🧪 Testing basic endpoints:")
    all_passed = True

    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {description}: {endpoint}")
            else:
                print(f"❌ {description}: {endpoint} (Status: {response.status_code})")
                all_passed = False
        except Exception as e:
            print(f"❌ {description}: {endpoint} (Error: {e})")
            all_passed = False

    return all_passed


def test_admin_login():
    """Test admin login"""
    print("\n🔐 Testing admin login:")

    try:
        login_data = {
            "phone": 990330919,
            "role": "admin",
            "password": "admin123"
        }

        response = requests.post(
            "http://localhost:8000/auth/login",
            json=login_data,
            timeout=5
        )

        if response.status_code == 200:
            token_data = response.json()
            if "access_token" in token_data:
                print("✅ Admin login successful")
                return token_data["access_token"]
            else:
                print("❌ Admin login failed: No access token in response")
                return None
        else:
            print(f"❌ Admin login failed: Status {response.status_code}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response text: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Admin login error: {e}")
        return None


def test_authenticated_endpoint(token):
    """Test an endpoint that requires authentication"""
    print("\n🔒 Testing authenticated endpoint:")

    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "http://localhost:8000/admin/students",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            students = response.json()
            print(f"✅ Admin/students endpoint: Found {len(students)} students")
            return True
        else:
            print(f"❌ Admin/students endpoint failed: Status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Authenticated endpoint error: {e}")
        return False


def main():
    """Run quick tests"""
    print("🚀 Quick API Test")
    print("=" * 40)

    # Test server connection
    if not test_server_connection():
        print("\n❌ Server is not accessible. Please:")
        print("1. Run: uvicorn app.main:app --reload")
        print("2. Wait for server to start")
        print("3. Run this test again")
        return

    # Test basic endpoints
    if not test_basic_endpoints():
        print("\n⚠️  Some basic endpoints failed")

    # Test authentication
    token = test_admin_login()
    if not token:
        print("\n❌ Authentication failed. Database might not be initialized.")
        print("Run: python comprehensive_migration_test.py")
        return

    # Test authenticated endpoint
    if test_authenticated_endpoint(token):
        print("\n🎉 All quick tests passed!")
        print("\nYour API is working correctly. You can now:")
        print("- Visit http://localhost:8000/docs for API documentation")
        print("- Run comprehensive_migration_test.py for full testing")
    else:
        print("\n⚠️  Authentication works but some endpoints failed")


if __name__ == "__main__":
    main()