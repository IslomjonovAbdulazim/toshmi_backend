#!/usr/bin/env python3
"""
Account Creation Script
Creates test accounts for teacher, student, parent, and admin roles
"""

import psycopg2
from passlib.context import CryptContext
from datetime import datetime

DATABASE_URL = "postgresql://postgres:tehVJTDHftcSszXtnggXfdYGsXPIHTwC@gondola.proxy.rlwy.net:54324/railway"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_tables(cursor):
    """Create all required tables"""
    print("🏗️  Creating database tables...")
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            phone VARCHAR UNIQUE NOT NULL,
            password_hash VARCHAR NOT NULL,
            role VARCHAR NOT NULL,
            first_name VARCHAR,
            last_name VARCHAR,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            profile_image_id INTEGER
        );
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);")
    
    # Groups table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id SERIAL PRIMARY KEY,
            name VARCHAR UNIQUE NOT NULL,
            academic_year VARCHAR,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_groups_name ON groups(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_groups_year ON groups(academic_year);")
    
    # Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id),
            group_id INTEGER REFERENCES groups(id),
            parent_phone VARCHAR,
            graduation_year INTEGER
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_user ON students(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_group ON students(group_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_parent ON students(parent_phone);")
    
    print("✅ Tables created successfully!")

def create_test_accounts(cursor):
    """Create test accounts with specified credentials"""
    print("👥 Creating test accounts...")
    
    accounts = [
        {
            "phone": "+998990000001",
            "password": "123456",
            "role": "teacher",
            "first_name": "Aziz",
            "last_name": "Toshmurodov"
        },
        {
            "phone": "+998990000002", 
            "password": "123456",
            "role": "student",
            "first_name": "Sardor",
            "last_name": "Karimov"
        },
        {
            "phone": "+998990000003",
            "password": "123456", 
            "role": "parent",
            "first_name": "Dilnoza",
            "last_name": "Karimova"
        },
        {
            "phone": "+998990330919",
            "password": "admin123",
            "role": "admin", 
            "first_name": "Admin",
            "last_name": "User"
        }
    ]
    
    created_users = []
    
    for account in accounts:
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE phone = %s", (account["phone"],))
        existing = cursor.fetchone()
        
        if existing:
            print(f"⚠️  User {account['phone']} ({account['role']}) already exists")
            created_users.append(existing[0])
            continue
            
        # Hash password
        password_hash = hash_password(account["password"])
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (phone, password_hash, role, first_name, last_name, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            account["phone"],
            password_hash, 
            account["role"],
            account["first_name"],
            account["last_name"],
            True,
            datetime.utcnow()
        ))
        
        user_id = cursor.fetchone()[0]
        created_users.append(user_id)
        print(f"✅ Created {account['role']}: {account['first_name']} {account['last_name']} ({account['phone']})")
        
        # If this is a student, create student profile
        if account["role"] == "student":
            cursor.execute("""
                INSERT INTO students (user_id, parent_phone, graduation_year)
                VALUES (%s, %s, %s)
            """, (user_id, "+998990000003", 2025))
            print(f"✅ Created student profile with parent phone: +998990000003")
    
    return created_users

def create_sample_group(cursor):
    """Create a sample group"""
    print("📚 Creating sample group...")
    
    cursor.execute("SELECT id FROM groups WHERE name = %s", ("10-A",))
    existing = cursor.fetchone()
    
    if existing:
        print("⚠️  Group '10-A' already exists")
        return existing[0]
    
    cursor.execute("""
        INSERT INTO groups (name, academic_year, created_at)
        VALUES (%s, %s, %s)
        RETURNING id
    """, ("10-A", "2024-2025", datetime.utcnow()))
    
    group_id = cursor.fetchone()[0]
    print("✅ Created group: 10-A")
    return group_id

def assign_student_to_group(cursor, group_id):
    """Assign the test student to the sample group"""
    print("🎓 Assigning student to group...")
    
    cursor.execute("""
        UPDATE students 
        SET group_id = %s 
        WHERE user_id = (SELECT id FROM users WHERE phone = %s AND role = %s)
    """, (group_id, "+998990000002", "student"))
    
    if cursor.rowcount > 0:
        print("✅ Student assigned to group 10-A")
    else:
        print("⚠️  Student not found or already assigned")

def main():
    print("👥 Account Creation Script Starting...")
    print("=" * 50)
    
    try:
        # Connect to database
        print("🔗 Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        print("✅ Database connection successful!")
        
        # Create tables
        create_tables(cursor)
        
        # Create test accounts
        created_users = create_test_accounts(cursor)
        
        # Create sample group
        group_id = create_sample_group(cursor)
        
        # Assign student to group
        assign_student_to_group(cursor, group_id)
        
        # Summary
        print("\n📋 ACCOUNT CREATION SUMMARY")
        print("=" * 40)
        print("Created accounts:")
        print("• Teacher: +998990000001 / 123456")
        print("• Student: +998990000002 / 123456") 
        print("• Parent:  +998990000003 / 123456")
        print("• Admin:   +998990330919 / admin123")
        print(f"\nTotal users in database: {len(created_users)}")
        print("✅ Account creation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
        
    finally:
        cursor.close()
        conn.close()
        print("\n🔐 Database connection closed.")
    
    return 0

if __name__ == "__main__":
    exit(main())