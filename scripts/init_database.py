#!/usr/bin/env python3
"""
Database Initialization Script
Creates initial admin user and basic system data
"""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import SessionLocal, engine
from app.models import Base, User, Group, Subject
from app.utils.auth import hash_password
from app.utils.helpers import UserRole
from datetime import datetime


def create_tables_properly():
    """Create all database tables with proper error handling"""
    try:
        print("🔨 Creating database tables...")

        # Import all models to ensure they're registered
        from app import models

        # Drop all tables first (for clean setup)
        print("🧹 Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ Existing tables dropped")

        # Create all tables
        print("🏗️ Creating new tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")

        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                                       SELECT table_name
                                       FROM information_schema.tables
                                       WHERE table_schema = 'public'
                                       ORDER BY table_name;
                                       """))
            tables = [row[0] for row in result]

            print(f"📋 Tables created: {', '.join(tables)}")

            if 'users' not in tables:
                raise Exception("Users table was not created!")

        return True

    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        return False


def create_admin_user(db, phone: int = 990330919, password: str = "sWk}X2<1#5[\\",
                      full_name: str = "System Administrator"):
    """Create initial admin user"""

    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.phone == phone
        ).first()

        if existing_admin:
            print(f"✅ Admin user already exists: {existing_admin.full_name} ({existing_admin.phone})")
            return existing_admin

        # Create admin user
        admin_user = User(
            role=UserRole.ADMIN,
            phone=phone,
            password_hash=hash_password(password),
            full_name=full_name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print(f"✅ Admin user created successfully!")
        print(f"   Phone: {phone}")
        print(f"   Password: {password}")
        print(f"   Name: {full_name}")
        print(f"   ⚠️  IMPORTANT: Change the password after first login!")

        return admin_user

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {str(e)}")
        raise


def create_basic_groups(db):
    """Create some basic groups"""
    groups = [
        {"name": "Grade 10-A", "description": "10th grade students - Group A"},
        {"name": "Grade 10-B", "description": "10th grade students - Group B"},
        {"name": "Grade 11-A", "description": "11th grade students - Group A"},
        {"name": "Grade 11-B", "description": "11th grade students - Group B"},
        {"name": "IT Course", "description": "Information Technology course group"}
    ]

    created_groups = []

    try:
        for group_data in groups:
            # Check if group already exists
            existing_group = db.query(Group).filter(Group.name == group_data["name"]).first()

            if existing_group:
                print(f"📚 Group already exists: {existing_group.name}")
                created_groups.append(existing_group)
                continue

            # Create group
            group = Group(
                name=group_data["name"],
                description=group_data["description"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )

            db.add(group)
            created_groups.append(group)
            print(f"✅ Created group: {group_data['name']}")

        db.commit()
        return created_groups

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating groups: {str(e)}")
        raise


def create_basic_subjects(db):
    """Create some basic subjects"""
    subjects = [
        {"name": "Mathematics", "description": "Mathematical sciences and calculations"},
        {"name": "Physics", "description": "Physical sciences and natural laws"},
        {"name": "Chemistry", "description": "Chemical sciences and reactions"},
        {"name": "Biology", "description": "Life sciences and living organisms"},
        {"name": "English", "description": "English language and literature"},
        {"name": "Uzbek Language", "description": "Uzbek language and literature"},
        {"name": "Russian Language", "description": "Russian language and literature"},
        {"name": "History", "description": "World and national history"},
        {"name": "Geography", "description": "Physical and human geography"},
        {"name": "Computer Science", "description": "Programming and computer technologies"}
    ]

    created_subjects = []

    try:
        for subject_data in subjects:
            # Check if subject already exists
            existing_subject = db.query(Subject).filter(Subject.name == subject_data["name"]).first()

            if existing_subject:
                print(f"📖 Subject already exists: {existing_subject.name}")
                created_subjects.append(existing_subject)
                continue

            # Create subject
            subject = Subject(
                name=subject_data["name"],
                description=subject_data["description"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )

            db.add(subject)
            created_subjects.append(subject)
            print(f"✅ Created subject: {subject_data['name']}")

        db.commit()
        return created_subjects

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating subjects: {str(e)}")
        raise


def test_database_connection():
    """Test database connection before proceeding"""
    try:
        print("🔍 Testing database connection...")

        # Test basic connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()

            if test_value == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection test failed")
                return False

    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("💡 Check your DATABASE_URL in .env file")
        return False


def main():
    """Main initialization function"""
    print("🚀 Initializing Education Center Management System Database")
    print("=" * 60)

    try:
        # Test database connection first
        if not test_database_connection():
            print("❌ Cannot proceed without database connection")
            return 1

        # Create all tables with proper handling
        if not create_tables_properly():
            print("❌ Failed to create database tables")
            return 1

        # Get database session
        db = SessionLocal()

        try:
            # Create admin user
            print("\n👤 Creating admin user...")
            admin_user = create_admin_user(db)

            # Create basic groups
            print("\n📚 Creating basic groups...")
            groups = create_basic_groups(db)

            # Create basic subjects
            print("\n📖 Creating basic subjects...")
            subjects = create_basic_subjects(db)

            print("\n" + "=" * 60)
            print("🎉 Database initialization completed successfully!")
            print("\n📋 Summary:")
            print(f"   • Admin user: {admin_user.full_name}")
            print(f"   • Groups created: {len(groups)}")
            print(f"   • Subjects created: {len(subjects)}")
            print("\n🔐 Login credentials:")
            print(f"   • Phone: {admin_user.phone}")
            print(f"   • Role: admin")
            print(f"   • Password: admin123")
            print("\n⚠️  IMPORTANT: Change the admin password after first login!")
            print("\n🌐 Start the application with: python run.py")
            print("📖 API documentation: http://localhost:8000/docs")

        except Exception as e:
            print(f"❌ Error during database initialization: {str(e)}")
            return 1
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error during initialization: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())