#!/usr/bin/env python3
"""
Test script to verify payment-based student deletion logic
"""

import psycopg2
from passlib.context import CryptContext
from datetime import datetime

DATABASE_URL = "postgresql://postgres:tehVJTDHftcSszXtnggXfdYGsXPIHTwC@gondola.proxy.rlwy.net:54324/railway"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_test_student_without_payments():
    """Create a test student with NO payment records"""
    print("🧪 Creating test student without payments...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create user
        cursor.execute("""
            INSERT INTO users (phone, password_hash, role, first_name, last_name, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            "+998990000099",  # Test phone
            hash_password("123456"),
            "student",
            "Test",
            "Student",
            True,
            datetime.utcnow()
        ))
        
        user_id = cursor.fetchone()[0]
        
        # Create student profile
        cursor.execute("""
            INSERT INTO students (user_id, parent_phone, graduation_year)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (user_id, "+998990000003", 2025))
        
        student_id = cursor.fetchone()[0]
        
        print(f"✅ Created test student: ID={student_id}, User ID={user_id}")
        print(f"📱 Phone: +998990000099")
        print(f"💰 Payment records: 0 (intentionally none)")
        
        # Verify no payments
        cursor.execute("SELECT COUNT(*) FROM payment_records WHERE student_id = %s", (student_id,))
        payment_count = cursor.fetchone()[0]
        print(f"✅ Confirmed: {payment_count} payment records")
        
        cursor.close()
        conn.close()
        
        return student_id, user_id
        
    except Exception as e:
        print(f"❌ Error creating test student: {e}")
        return None, None

def check_student_with_payments():
    """Check existing student that has payments"""
    print("\n🔍 Checking existing student with payments...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Find student with payments
        cursor.execute("""
            SELECT s.id, u.first_name, u.last_name, u.phone, COUNT(pr.id) as payment_count
            FROM students s
            JOIN users u ON s.user_id = u.id  
            LEFT JOIN payment_records pr ON s.id = pr.student_id
            GROUP BY s.id, u.first_name, u.last_name, u.phone
            HAVING COUNT(pr.id) > 0
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            student_id, first_name, last_name, phone, payment_count = result
            print(f"📋 Found student with payments:")
            print(f"   ID: {student_id}")
            print(f"   Name: {first_name} {last_name}")
            print(f"   Phone: {phone}")
            print(f"   💰 Payment records: {payment_count}")
            
            cursor.close()
            conn.close()
            return student_id
        else:
            print("⚠️  No students with payments found")
            cursor.close()
            conn.close()
            return None
            
    except Exception as e:
        print(f"❌ Error checking students: {e}")
        return None

def cleanup_test_student(student_id, user_id):
    """Manually cleanup test student if needed"""
    print(f"\n🧹 Cleaning up test student (ID: {student_id})...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Delete student and user
        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        print("✅ Test student cleaned up")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error cleaning up: {e}")

def main():
    print("🧪 Testing Payment-Based Student Deletion Logic...")
    print("=" * 60)
    
    # Check existing student with payments
    student_with_payments = check_student_with_payments()
    
    # Create test student without payments
    test_student_id, test_user_id = create_test_student_without_payments()
    
    if not test_student_id:
        print("❌ Could not create test student")
        return 1
    
    print(f"\n📋 TEST SUMMARY:")
    print(f"=" * 30)
    if student_with_payments:
        print(f"✅ Student with payments (ID: {student_with_payments}) - should be BLOCKED from deletion")
    print(f"✅ Test student without payments (ID: {test_student_id}) - should be ALLOWED to delete")
    
    print(f"\n🎯 EXPECTED BEHAVIOR:")
    print(f"- DELETE /admin/students/{student_with_payments if student_with_payments else 'N/A'} → 403 Forbidden (has payments)")
    print(f"- DELETE /admin/students/{test_student_id} → 200 Success (no payments)")
    
    print(f"\n⚠️  Remember to test with your API and then cleanup:")
    print(f"   Test student phone: +998990000099")
    print(f"   Manual cleanup: DELETE FROM students WHERE id = {test_student_id}")
    
    return 0

if __name__ == "__main__":
    exit(main())