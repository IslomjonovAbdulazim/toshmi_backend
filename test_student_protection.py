#!/usr/bin/env python3
"""
Test script to verify student deletion protection is working
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"  # Adjust if your server runs on different port
ADMIN_PHONE = "+998990330919"
ADMIN_PASSWORD = "admin123"

def login_as_admin():
    """Login as admin and get access token"""
    login_data = {
        "phone": ADMIN_PHONE,
        "password": ADMIN_PASSWORD,
        "role": "admin"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Admin login successful")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_student_deletion_protection(token):
    """Test that student deletion is properly blocked"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # First, get list of students to find a student ID to test with
    try:
        response = requests.get(f"{BASE_URL}/admin/students", headers=headers)
        if response.status_code == 200:
            students = response.json()
            if students:
                student_id = students[0]["id"]
                student_name = students[0]["name"]
                print(f"📋 Found student to test with: {student_name} (ID: {student_id})")
                
                # Try to delete the student
                delete_response = requests.delete(f"{BASE_URL}/admin/students/{student_id}", headers=headers)
                
                if delete_response.status_code == 403:
                    print("✅ Student deletion properly blocked!")
                    print(f"📝 Response: {delete_response.json()['detail']}")
                    return True
                else:
                    print(f"❌ Expected 403 status, got {delete_response.status_code}")
                    print(f"📝 Response: {delete_response.text}")
                    return False
            else:
                print("⚠️  No students found to test with")
                return False
        else:
            print(f"❌ Failed to get students: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    print("🧪 Testing Student Deletion Protection...")
    print("=" * 50)
    
    # Login as admin
    token = login_as_admin()
    if not token:
        print("❌ Cannot proceed without admin access")
        return 1
    
    # Test student deletion protection
    if test_student_deletion_protection(token):
        print("\n✅ All tests passed! Student deletion is properly protected.")
        return 0
    else:
        print("\n❌ Tests failed! Student deletion protection may not be working.")
        return 1

if __name__ == "__main__":
    exit(main())