#!/usr/bin/env python3
"""
Database Connection Test Script
Tests the database connection and provides debugging information
"""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


def test_basic_connection():
    """Test basic psycopg2 connection"""
    try:
        import psycopg2
        from app.config import settings

        print("🔍 Testing basic psycopg2 connection...")
        print(f"Database URL: {settings.database_url[:50]}...")

        # Extract connection parameters
        db_url = settings.database_url

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        print(f"✅ PostgreSQL connection successful!")
        print(f"Database version: {version[0]}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Basic connection failed: {str(e)}")
        return False


def test_sqlalchemy_connection():
    """Test SQLAlchemy connection"""
    try:
        from sqlalchemy import create_engine, text
        from app.config import settings

        print("\n🔍 Testing SQLAlchemy connection...")

        engine = create_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 10,
                "sslmode": "require" if "twc1.net" in settings.database_url else "prefer"
            }
        )

        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()"))
            db_info = result.fetchone()

            print(f"✅ SQLAlchemy connection successful!")
            print(f"Database: {db_info[0]}")
            print(f"User: {db_info[1]}")
            print(f"Server: {db_info[2]}:{db_info[3]}")

        return True

    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {str(e)}")
        return False


def test_app_database():
    """Test app database configuration"""
    try:
        from app.database import SessionLocal, engine
        from sqlalchemy import text

        print("\n🔍 Testing app database configuration...")

        # Test engine connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            if result.scalar() == 1:
                print("✅ Engine connection successful!")

        # Test session
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT current_timestamp"))
            timestamp = result.scalar()
            print(f"✅ Session connection successful! Server time: {timestamp}")
        finally:
            db.close()

        return True

    except Exception as e:
        print(f"❌ App database test failed: {str(e)}")
        return False


def check_existing_tables():
    """Check what tables exist in the database"""
    try:
        from app.database import SessionLocal
        from sqlalchemy import text

        print("\n🔍 Checking existing tables...")

        db = SessionLocal()
        try:
            result = db.execute(text("""
                                     SELECT table_name
                                     FROM information_schema.tables
                                     WHERE table_schema = 'public'
                                     ORDER BY table_name;
                                     """))

            tables = [row[0] for row in result]

            if tables:
                print(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    print(f"   • {table}")
            else:
                print("⚠️  No tables found in database")

            return tables

        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error checking tables: {str(e)}")
        return []


def test_table_creation():
    """Test creating a simple table"""
    try:
        from app.database import engine
        from sqlalchemy import text

        print("\n🔍 Testing table creation permissions...")

        with engine.connect() as conn:
            # Try to create a test table
            conn.execute(text("""
                              CREATE TABLE IF NOT EXISTS test_table_temp
                              (
                                  id
                                  SERIAL
                                  PRIMARY
                                  KEY,
                                  test_column
                                  VARCHAR
                              (
                                  50
                              )
                                  );
                              """))

            # Insert test data
            conn.execute(text("""
                              INSERT INTO test_table_temp (test_column)
                              VALUES ('test_value');
                              """))

            # Read test data
            result = conn.execute(text("SELECT test_column FROM test_table_temp LIMIT 1"))
            test_value = result.scalar()

            # Clean up
            conn.execute(text("DROP TABLE test_table_temp;"))

            conn.commit()

            if test_value == 'test_value':
                print("✅ Table creation and manipulation successful!")
                return True
            else:
                print("❌ Table creation test failed")
                return False

    except Exception as e:
        print(f"❌ Table creation test failed: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🧪 Database Connection Test")
    print("=" * 50)

    try:
        # Load environment
        from app.config import settings
        print(f"Environment: {settings.environment}")
        print(f"Debug: {settings.debug}")

    except Exception as e:
        print(f"❌ Failed to load configuration: {str(e)}")
        return 1

    success_count = 0
    total_tests = 5

    # Test 1: Basic connection
    if test_basic_connection():
        success_count += 1

    # Test 2: SQLAlchemy connection
    if test_sqlalchemy_connection():
        success_count += 1

    # Test 3: App database
    if test_app_database():
        success_count += 1

    # Test 4: Check existing tables
    tables = check_existing_tables()
    if isinstance(tables, list):
        success_count += 1

    # Test 5: Test table creation
    if test_table_creation():
        success_count += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("🎉 All database tests passed!")
        print("\n💡 Your database is ready. You can now run:")
        print("   python scripts/init_database.py")
        return 0
    else:
        print("❌ Some database tests failed")
        print("\n💡 Troubleshooting suggestions:")

        if success_count == 0:
            print("   • Check your DATABASE_URL in .env file")
            print("   • Ensure database server is running")
            print("   • Verify network connectivity")
        elif success_count < 3:
            print("   • Check database permissions")
            print("   • Verify SSL configuration")
        else:
            print("   • Try running the database initialization")
            print("   • Check for existing table conflicts")

        return 1


if __name__ == "__main__":
    sys.exit(main())