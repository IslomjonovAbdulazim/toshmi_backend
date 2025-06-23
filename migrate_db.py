#!/usr/bin/env python3
"""
Comprehensive Database Migration and API Testing Script
This script will:
1. Reset the database
2. Create sample data
3. Test all API endpoints
4. Provide detailed results
"""

import sys
import os
import time
import requests
import json
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, create_tables, Base
from app.models import User, Student, Parent, Teacher, Group, Subject, GroupSubject
import uuid


class DatabaseMigrator:
    """Handle database migration"""

    def __init__(self):
        self.db = SessionLocal()

    def reset_database(self):
        """Drop all tables and recreate them"""
        print("🔄 Dropping all tables...")
        Base.metadata.drop_all(bind=engine)

        print("🔧 Creating fresh tables...")
        create_tables()
        print("✅ Database structure created successfully")

    def create_admin_user(self):
        """Create admin account"""
        try:
            from app.utils.password import hash_password

            admin_user = User(
                id=str(uuid.uuid4()),
                role="admin",
                phone=990330919,
                password_hash=hash_password("admin123"),
                full_name="System Administrator"
            )

            self.db.add(admin_user)
            self.db.commit()
            self.db.refresh(admin_user)

            # Store phone number before session issues
            admin_phone = admin_user.phone
            admin_name = admin_user.full_name

            print(f"👤 Created admin user: {admin_name}")
            return {"phone": admin_phone, "name": admin_name}

        except Exception as e:
            print(f"❌ Error creating admin: {e}")
            self.db.rollback()
            return None

    def create_sample_data(self):
        """Create basic subjects and groups"""
        try:
            # Create subjects
            subjects_data = [
                "Mathematics", "English Literature", "Physics",
                "Chemistry", "Biology", "History", "Geography"
            ]

            created_subjects = []
            for subject_name in subjects_data:
                subject = Subject(
                    id=str(uuid.uuid4()),
                    name=subject_name
                )
                self.db.add(subject)
                created_subjects.append(subject)

            # Create groups
            groups_data = ["Grade 10A", "Grade 10B", "Grade 11A", "Grade 11B", "Grade 12A"]

            created_groups = []
            for group_name in groups_data:
                group = Group(
                    id=str(uuid.uuid4()),
                    name=group_name
                )
                self.db.add(group)
                created_groups.append(group)

            self.db.commit()
            print(f"📚 Created {len(created_subjects)} subjects")
            print(f"👥 Created {len(created_groups)} groups")

            # Create group-subject relationships
            for group in created_groups:
                for subject in created_subjects[:5]:
                    group_subject = GroupSubject(
                        id=str(uuid.uuid4()),
                        group_id=group.id,
                        subject_id=subject.id
                    )
                    self.db.add(group_subject)

            self.db.commit()
            print("🔗 Created group-subject relationships")

            return created_groups, created_subjects

        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
            self.db.rollback()
            return [], []

    def create_sample_users(self, groups):
        """Create sample users for testing"""
        try:
            from app.utils.password import hash_password

            users_created = []

            # Create teacher
            teacher_user = User(
                id=str(uuid.uuid4()),
                role="teacher",
                phone=1234567890,
                password_hash=hash_password("teacher123"),
                full_name="John Teacher"
            )
            self.db.add(teacher_user)
            self.db.flush()

            teacher = Teacher(
                id=str(uuid.uuid4()),
                user_id=teacher_user.id
            )
            self.db.add(teacher)
            users_created.append(("teacher", teacher_user))

            # Create parent
            parent_user = User(
                id=str(uuid.uuid4()),
                role="parent",
                phone=9876543210,
                password_hash=hash_password("parent123"),
                full_name="Jane Parent"
            )
            self.db.add(parent_user)
            self.db.flush()

            parent = Parent(
                id=str(uuid.uuid4()),
                user_id=parent_user.id
            )
            self.db.add(parent)
            self.db.flush()
            users_created.append(("parent", parent_user))

            # Create student linked to parent
            student_user = User(
                id=str(uuid.uuid4()),
                role="student",
                phone=5555555555,
                password_hash=hash_password("student123"),
                full_name="Alex Student"
            )
            self.db.add(student_user)
            self.db.flush()

            first_group = groups[0] if groups else None
            if first_group:
                student = Student(
                    id=str(uuid.uuid4()),
                    user_id=student_user.id,
                    group_id=first_group.id,
                    parent_id=parent.id,
                    graduation_year=2025
                )
                self.db.add(student)
                users_created.append(("student", student_user))

            self.db.commit()
            print("👥 Created sample users:")
            for role, user in users_created:
                print(f"   {role.title()}: {user.full_name} (Phone: {user.phone})")

            return users_created

        except Exception as e:
            print(f"❌ Error creating sample users: {e}")
            self.db.rollback()
            return []

    def close(self):
        self.db.close()


class APITester:
    """Test all API endpoints"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.tokens = {}
        self.test_results = []

    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status} {test_name}")
        if details and not success:
            print(f"    Details: {details}")

    def test_login(self, phone, role, password):
        """Test login endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"phone": phone, "role": role, "password": password}
            )

            if response.status_code == 200:
                token = response.json()["access_token"]
                self.tokens[role] = token
                self.log_test(f"Login as {role}", True)
                return True
            else:
                self.log_test(f"Login as {role}", False, f"Status: {response.status_code}")
                return False

        except Exception as e:
            self.log_test(f"Login as {role}", False, str(e))
            return False

    def test_endpoint(self, method, endpoint, role=None, json_data=None, expected_status=200):
        """Generic endpoint tester"""
        try:
            headers = {}
            if role and role in self.tokens:
                headers["Authorization"] = f"Bearer {self.tokens[role]}"

            if method.upper() == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
            elif method.upper() == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", headers=headers, json=json_data)
            elif method.upper() == "DELETE":
                response = requests.delete(f"{self.base_url}{endpoint}", headers=headers)
            else:
                self.log_test(f"{method} {endpoint}", False, "Unsupported method")
                return False

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            if not success and response.status_code != expected_status:
                try:
                    details += f", Response: {response.json()}"
                except:
                    details += f", Text: {response.text[:100]}"

            self.log_test(f"{method} {endpoint}", success, details if not success else "")
            return success, response

        except Exception as e:
            self.log_test(f"{method} {endpoint}", False, str(e))
            return False, None

    def run_comprehensive_tests(self):
        """Run all endpoint tests"""
        print("\n🧪 Starting API Tests...")
        print("=" * 50)

        # Test authentication
        print("\n🔐 Testing Authentication:")
        self.test_login(990330919, "admin", "admin123")
        self.test_login(1234567890, "teacher", "teacher123")
        self.test_login(9876543210, "parent", "parent123")
        self.test_login(5555555555, "student", "student123")

        # Test basic endpoints
        print("\n📊 Testing Basic Endpoints:")
        self.test_endpoint("GET", "/", None)
        self.test_endpoint("GET", "/health", None)
        self.test_endpoint("GET", "/api-info", None)

        # Test admin endpoints
        print("\n👨‍💼 Testing Admin Endpoints:")
        self.test_endpoint("GET", "/admin/students", "admin")
        self.test_endpoint("GET", "/admin/parents", "admin")
        self.test_endpoint("GET", "/admin/teachers", "admin")
        self.test_endpoint("GET", "/admin/groups", "admin")
        self.test_endpoint("GET", "/admin/subjects", "admin")
        self.test_endpoint("GET", "/admin/group-subjects", "admin")

        # Test reports
        print("\n📈 Testing Reports:")
        self.test_endpoint("GET", "/admin/reports/overview", "admin")

        # Test user creation
        print("\n👤 Testing User Creation:")

        # Get a real group ID first
        success, response = self.test_endpoint("GET", "/admin/groups", "admin")
        if success and response:
            try:
                groups = response.json()
                if groups:
                    real_group_id = groups[0]["id"]
                    new_student_data = {
                        "phone": 1111111111,
                        "full_name": "Test Student",
                        "password": "password123",
                        "group_id": real_group_id,
                        "graduation_year": 2025
                    }
                    self.test_endpoint("POST", "/admin/students", "admin", new_student_data, 200)
                else:
                    print("⚠️  No groups found for student creation test")
            except:
                print("⚠️  Could not parse groups response for student creation test")
        else:
            print("⚠️  Could not fetch groups for student creation test")

        # Test password reset
        print("\n🔑 Testing Password Reset:")
        reset_data = {
            "phone": 5555555555,
            "role": "student",
            "new_password": "newpassword123"
        }
        self.test_endpoint("POST", "/auth/reset-password", None, reset_data)

        # Test student endpoints (if student login worked)
        if "student" in self.tokens:
            print("\n🎓 Testing Student Endpoints:")
            self.test_endpoint("GET", "/student/homework-grades", "student")
            self.test_endpoint("GET", "/student/exam-grades", "student")
            self.test_endpoint("GET", "/student/attendance", "student")
            self.test_endpoint("GET", "/student/schedule", "student")

        # Test parent endpoints (if parent login worked)
        if "parent" in self.tokens:
            print("\n👨‍👩‍👧‍👦 Testing Parent Endpoints:")
            self.test_endpoint("GET", "/parent/children", "parent")

        # Test teacher endpoints (if teacher login worked)
        if "teacher" in self.tokens:
            print("\n🧑‍🏫 Testing Teacher Endpoints:")
            self.test_endpoint("GET", "/teacher/homework", "teacher",
                               expected_status=422)  # Missing required query param
            self.test_endpoint("GET", "/teacher/exams", "teacher", expected_status=422)  # Missing required query param

        # Test logout
        print("\n🚪 Testing Logout:")
        self.test_endpoint("POST", "/auth/logout", None)

    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['details']}")


def main():
    """Main function"""
    print("🚀 Comprehensive Migration and Testing Script")
    print("=" * 70)

    # Database Migration
    migrator = DatabaseMigrator()

    print("\n📀 Database Migration:")
    migrator.reset_database()
    admin = migrator.create_admin_user()
    groups, subjects = migrator.create_sample_data()
    users = migrator.create_sample_users(groups)
    migrator.close()

    print("\n✅ Database migration completed!")

    # Wait a moment for any server to be ready
    print("\n⏳ Waiting 3 seconds for server startup...")
    time.sleep(3)

    # API Testing
    print("\n🧪 Starting API Tests...")
    print("Make sure the server is running: uvicorn app.main:app --reload")
    input("Press Enter when server is ready, or Ctrl+C to skip tests...")

    try:
        tester = APITester()
        tester.run_comprehensive_tests()
        tester.print_summary()
    except KeyboardInterrupt:
        print("\n⏭️  API tests skipped by user")
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")

    # Final Summary
    print("\n" + "=" * 70)
    print("🎉 MIGRATION AND TESTING COMPLETE!")
    print("=" * 70)

    if admin:
        print("\n🔐 LOGIN CREDENTIALS:")
        print(f"   Admin: Phone {admin['phone']}, Password 'admin123'")

    print("\n📝 SAMPLE CREDENTIALS:")
    print("   Teacher: Phone 1234567890, Password 'teacher123'")
    print("   Parent: Phone 9876543210, Password 'parent123'")
    print("   Student: Phone 5555555555, Password 'student123'")

    print("\n🌐 SERVER COMMANDS:")
    print("   Start: uvicorn app.main:app --reload")
    print("   Docs: http://localhost:8000/docs")
    print("   API: http://localhost:8000")


if __name__ == "__main__":
    main()