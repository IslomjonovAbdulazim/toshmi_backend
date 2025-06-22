#!/usr/bin/env python3
"""
Test database setup script
Resets database and creates admin account
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, create_tables, Base
from app.models import User, Student, Parent, Teacher, Group, Subject, GroupSubject
from sqlalchemy import text
import uuid


def reset_database():
    """Drop all tables and recreate them with CASCADE"""
    print("Dropping all tables...")

    # Use raw SQL to drop all tables with CASCADE
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()

    print("Creating fresh tables...")
    create_tables()
    print("Database reset complete")


def create_admin_user():
    """Create admin account for testing"""
    db = SessionLocal()
    try:
        from app.utils.password import hash_password

        admin_user = User(
            id=str(uuid.uuid4()),
            role="admin",
            phone=990330919,
            password_hash=hash_password("admin123"),
            full_name="Admin User",
            avatar_url=None
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Created admin user: {admin_user.full_name} (Phone: {admin_user.phone})")
        return admin_user

    except Exception as e:
        print(f"Error creating admin: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def create_sample_data():
    """Create sample subjects and groups"""
    db = SessionLocal()
    try:
        # Create subjects
        subjects = [
            {"name": "Mathematics"},
            {"name": "English"},
            {"name": "Science"},
            {"name": "History"}
        ]

        created_subjects = []
        for subject_data in subjects:
            subject = Subject(
                id=str(uuid.uuid4()),
                name=subject_data["name"]
            )
            db.add(subject)
            created_subjects.append(subject)

        # Create groups
        groups = [
            {"name": "10A"},
            {"name": "10B"},
            {"name": "11A"}
        ]

        created_groups = []
        for group_data in groups:
            group = Group(
                id=str(uuid.uuid4()),
                name=group_data["name"]
            )
            db.add(group)
            created_groups.append(group)

        db.commit()
        print(f"Created {len(created_subjects)} subjects and {len(created_groups)} groups")

    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main setup function"""
    print("Resetting database completely...")
    reset_database()

    print("Creating admin user...")
    admin = create_admin_user()

    print("Creating sample data...")
    create_sample_data()

    print("\n" + "=" * 50)
    print("DATABASE RESET & SETUP COMPLETE")
    print("=" * 50)
    if admin:
        print(f"Admin Login Credentials:")
        print(f"  Phone: {admin.phone}")
        print(f"  Role: {admin.role}")
        print(f"  Password: admin123")
        print(f"  Name: {admin.full_name}")
    print("\nLogin via API:")
    print("POST /auth/login")
    print('{"phone": 990330919, "role": "admin", "password": "admin123"}')


if __name__ == "__main__":
    main()