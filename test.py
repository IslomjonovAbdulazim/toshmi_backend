#!/usr/bin/env python3
"""
Database Cleanup Script for Orphaned Records
Fixes the AttributeError: 'NoneType' object has no attribute 'id' issues
"""

import psycopg2
import sys
from urllib.parse import urlparse

# Database connection URL
DATABASE_URL = "postgresql://gen_user:(8Ah)S%24aY)lF6t@3d7780415a2721a636acfe11.twc1.net:5432/default_db?sslmode=prefer"


def connect_to_database():
    """Connect to PostgreSQL database"""
    try:
        print("🔗 Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        print("✅ Database connection successful!")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)


def execute_query(cursor, query, description):
    """Execute a query and return results"""
    try:
        print(f"🔄 {description}...")
        cursor.execute(query)
        if cursor.description:  # If query returns results
            results = cursor.fetchall()
            return results
        else:
            return cursor.rowcount
    except Exception as e:
        print(f"❌ Error {description.lower()}: {e}")
        return None


def main():
    print("🧹 Database Cleanup Script Starting...")
    print("=" * 50)

    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        # Step 1: Check current state before cleanup
        print("\n📊 CHECKING CURRENT STATE...")

        check_queries = [
            ("SELECT COUNT(*) FROM group_subjects WHERE group_id IS NULL",
             "Orphaned group_subjects with NULL group_id"),
            ("SELECT COUNT(*) FROM group_subjects gs LEFT JOIN groups g ON gs.group_id = g.id WHERE gs.group_id IS NOT NULL AND g.id IS NULL",
             "group_subjects with invalid group_id"),
            ("SELECT COUNT(*) FROM group_subjects gs LEFT JOIN subjects s ON gs.subject_id = s.id WHERE gs.subject_id IS NOT NULL AND s.id IS NULL",
             "group_subjects with invalid subject_id"),
            ("SELECT COUNT(*) FROM schedules WHERE group_subject_id NOT IN (SELECT id FROM group_subjects)",
             "Orphaned schedules"),
        ]

        issues_found = False
        for query, description in check_queries:
            result = execute_query(cursor, query, f"Checking {description}")
            if result and result[0][0] > 0:
                print(f"⚠️  Found {result[0][0]} {description}")
                issues_found = True
            else:
                print(f"✅ No {description}")

        if not issues_found:
            print("🎉 No issues found! Database is clean.")
            return

        # Step 2: Perform cleanup
        print("\n🧹 PERFORMING CLEANUP...")

        cleanup_queries = [
            # First, clean up records that depend on orphaned group_subjects
            ("DELETE FROM schedules WHERE group_subject_id IN (SELECT id FROM group_subjects WHERE group_id IS NULL)",
             "Cleaning schedules referencing group_subjects with NULL group_id"),
            ("DELETE FROM homework WHERE group_subject_id IN (SELECT id FROM group_subjects WHERE group_id IS NULL)",
             "Cleaning homework referencing group_subjects with NULL group_id"),
            ("DELETE FROM exams WHERE group_subject_id IN (SELECT id FROM group_subjects WHERE group_id IS NULL)",
             "Cleaning exams referencing group_subjects with NULL group_id"),
            ("DELETE FROM attendance WHERE group_subject_id IN (SELECT id FROM group_subjects WHERE group_id IS NULL)",
             "Cleaning attendance referencing group_subjects with NULL group_id"),

            # Then clean up the orphaned group_subjects themselves
            ("DELETE FROM group_subjects WHERE group_id IS NULL", "Cleaning group_subjects with NULL group_id"),
            ("DELETE FROM group_subjects gs WHERE NOT EXISTS (SELECT 1 FROM groups g WHERE g.id = gs.group_id)",
             "Cleaning group_subjects with invalid group_id"),
            ("DELETE FROM group_subjects gs WHERE NOT EXISTS (SELECT 1 FROM subjects s WHERE s.id = gs.subject_id)",
             "Cleaning group_subjects with invalid subject_id"),

            # Finally, clean up any remaining orphaned records
            ("DELETE FROM schedules WHERE group_subject_id NOT IN (SELECT id FROM group_subjects)",
             "Cleaning remaining orphaned schedules"),
            ("DELETE FROM homework WHERE group_subject_id NOT IN (SELECT id FROM group_subjects)",
             "Cleaning remaining orphaned homework"),
            ("DELETE FROM exams WHERE group_subject_id NOT IN (SELECT id FROM group_subjects)",
             "Cleaning remaining orphaned exams"),
            ("DELETE FROM attendance WHERE group_subject_id NOT IN (SELECT id FROM group_subjects)",
             "Cleaning remaining orphaned attendance records"),
        ]

        total_cleaned = 0
        for query, description in cleanup_queries:
            deleted_count = execute_query(cursor, query, description)
            if deleted_count and deleted_count > 0:
                print(f"🗑️  Deleted {deleted_count} records: {description}")
                total_cleaned += deleted_count
            else:
                print(f"✅ No records to clean: {description}")

        # Step 3: Verify cleanup
        print("\n🔍 VERIFYING CLEANUP...")

        for query, description in check_queries:
            result = execute_query(cursor, query, f"Re-checking {description}")
            if result and result[0][0] > 0:
                print(f"⚠️  Still found {result[0][0]} {description}")
            else:
                print(f"✅ Confirmed clean: {description}")

        # Step 4: Show summary
        print("\n📋 CLEANUP SUMMARY")
        print("=" * 30)
        print(f"Total records cleaned: {total_cleaned}")

        if total_cleaned > 0:
            print("✅ Cleanup completed successfully!")
            print("🔄 Please restart your FastAPI application to see the fixes.")
        else:
            print("ℹ️  No cleanup was needed.")

        # Step 5: Show remaining data
        print("\n📊 REMAINING DATA SUMMARY")
        print("-" * 30)

        summary_queries = [
            ("SELECT COUNT(*) FROM groups", "Total groups"),
            ("SELECT COUNT(*) FROM subjects", "Total subjects"),
            ("SELECT COUNT(*) FROM group_subjects", "Total group-subject assignments"),
            ("SELECT COUNT(*) FROM group_subjects WHERE teacher_id IS NOT NULL", "Assignments with teachers"),
            ("SELECT COUNT(*) FROM group_subjects WHERE teacher_id IS NULL", "Unassigned assignments"),
            ("SELECT COUNT(*) FROM schedules", "Total schedule entries"),
        ]

        for query, description in summary_queries:
            result = execute_query(cursor, query, description)
            if result:
                print(f"{description}: {result[0][0]}")

    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()
        print("\n🔐 Database connection closed.")


if __name__ == "__main__":
    main()