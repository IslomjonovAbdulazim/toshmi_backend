#!/usr/bin/env python3
"""
Quick fix script to reset database and create admin user
This will fix the SQLAlchemy relationship issues
"""

import sys
import os
from sqlalchemy import create_engine, text
from datetime import datetime
from passlib.context import CryptContext

# Database connection
DATABASE_URL = "postgresql://gen_user:(8Ah)S%24aY)lF6t@3d7780415a2721a636acfe11.twc1.net:5432/default_db?sslmode=prefer"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def quick_fix():
    """Quick fix for the relationship issues"""

    print("🔧 Quick fix for SQLAlchemy relationship issues...")

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            print("📋 Connected to database")

            # Drop all tables to clean slate
            print("🧹 Dropping all tables...")
            conn.execute(text("DROP SCHEMA public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            conn.commit()
            print("✅ All tables dropped")

            # Now we need to recreate tables using SQLAlchemy
            print("🏗️  Creating tables with clean models...")

            # Import models after clearing to avoid cached relationship issues
            sys.path.insert(0, '.')
            from app.models.models import Base

            # Create all tables
            Base.metadata.create_all(bind=engine)
            print("✅ Tables created successfully")

            # Create admin user
            print("👤 Creating admin user...")
            hashed_password = hash_password("admin123")

            conn.execute(text("""
                              INSERT INTO users (phone, password_hash, role, first_name, last_name, is_active,
                                                 created_at)
                              VALUES (:phone, :password_hash, :role, :first_name, :last_name, :is_active, :created_at)
                              """), {
                             "phone": "+998990330919",
                             "password_hash": hashed_password,
                             "role": "admin",
                             "first_name": "System",
                             "last_name": "Administrator",
                             "is_active": True,
                             "created_at": datetime.utcnow()
                         })

            conn.commit()

            print("✅ Admin user created successfully!")
            print("📋 Admin Credentials:")
            print("   Phone: +998990330919")
            print("   Password: admin123")
            print("   Role: admin")

            # Create sample data
            print("📊 Creating sample data...")

            # Sample group
            conn.execute(text("""
                              INSERT INTO groups (name, academic_year)
                              VALUES ('10-A', '2024-2025')
                              """))

            # Sample subject
            conn.execute(text("""
                              INSERT INTO subjects (name, code)
                              VALUES ('Mathematics', 'MATH101')
                              """))

            conn.commit()
            print("✅ Sample data created!")

            print("\n🎉 Quick fix completed successfully!")
            print("\nRestart your FastAPI server now:")
            print("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True


if __name__ == "__main__":
    quick_fix()