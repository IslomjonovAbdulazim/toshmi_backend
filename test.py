#!/usr/bin/env python3
"""
Database Connection Test Script with Retry Logic
Tests database connectivity with automatic retry mechanism
"""

import psycopg2
import time
import sys
from typing import Optional

DATABASE_URL = "postgresql://postgres:tehVJTDHftcSszXtnggXfdYGsXPIHTwC@gondola.proxy.rlwy.net:54324/railway"


def test_connection_with_retry(max_retries: int = 3, retry_delay: int = 2) -> Optional[psycopg2.extensions.connection]:
    """
    Test database connection with retry logic
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        Database connection if successful, None otherwise
    """
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔗 Connection attempt {attempt}/{max_retries}...")
            conn = psycopg2.connect(DATABASE_URL)
            print("✅ Database connection successful!")
            return conn
            
        except psycopg2.OperationalError as e:
            print(f"❌ Connection attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(f"⏳ Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("💥 All connection attempts failed!")
                
        except Exception as e:
            print(f"❌ Unexpected error on attempt {attempt}: {e}")
            if attempt < max_retries:
                print(f"⏳ Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("💥 All connection attempts failed!")
    
    return None


def test_basic_queries(conn: psycopg2.extensions.connection) -> bool:
    """
    Test basic database operations
    
    Args:
        conn: Database connection
        
    Returns:
        True if all tests pass, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        print("\n🧪 Testing basic queries...")
        
        # Test 1: Simple query
        cursor.execute("SELECT 1 as test_value")
        result = cursor.fetchone()
        if result[0] == 1:
            print("✅ Basic SELECT query working")
        else:
            print("❌ Basic SELECT query failed")
            return False
            
        # Test 2: Check current database
        cursor.execute("SELECT current_database()")
        db_name = cursor.fetchone()[0]
        print(f"✅ Connected to database: {db_name}")
        
        # Test 3: Check connection info
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL version: {version.split(',')[0]}")
        
        # Test 4: Check if we can see tables
        cursor.execute("""
            SELECT count(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]
        print(f"✅ Found {table_count} tables in public schema")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False


def main():
    print("🧪 Database Connection Test Starting...")
    print("=" * 50)
    
    # Test connection with retry
    conn = test_connection_with_retry(max_retries=3, retry_delay=2)
    
    if not conn:
        print("🚫 Could not establish database connection")
        sys.exit(1)
    
    try:
        # Test basic operations
        if test_basic_queries(conn):
            print("\n🎉 All database tests passed!")
        else:
            print("\n⚠️  Some database tests failed!")
            sys.exit(1)
            
    finally:
        conn.close()
        print("\n🔐 Database connection closed.")


if __name__ == "__main__":
    main()