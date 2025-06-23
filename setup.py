#!/usr/bin/env python3
"""
Setup script for the Simplified School Management System
This script will install dependencies and prepare the environment
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main():
    """Main setup function"""
    print("🚀 Setting up Simplified School Management System")
    print("=" * 60)

    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)

    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")

    # Install/upgrade pip
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        print("⚠️  Pip upgrade failed, continuing anyway...")

    # Install dependencies with specific versions to avoid conflicts
    dependencies = [
        "fastapi==0.115.0",
        "uvicorn[standard]==0.32.0",
        "sqlalchemy==2.0.36",
        "pydantic==2.11.7",
        "python-jose[cryptography]==3.3.0",
        "bcrypt==4.0.1",  # Specific version to avoid compatibility issues
        "passlib[bcrypt]==1.7.4",
        "python-multipart==0.0.17",
        "python-dotenv==1.0.1",
        "alembic==1.13.1",
        "requests==2.31.0"
    ]

    print("\n📦 Installing dependencies...")
    for dep in dependencies:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep.split('==')[0]}"):
            print(f"⚠️  Failed to install {dep}, continuing...")

    # Check if .env file exists
    if not os.path.exists(".env"):
        print("\n📝 Creating .env file...")
        with open(".env", "w") as f:
            f.write("""DATABASE_URL=sqlite:///./school_management.sqlite
SECRET_KEY=lRz8vKzQ1mN7pX9sE2wA4fJ6hT3qY8nL5bM0cV7dS1gH9xP4rU6tI
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
""")
        print("✅ .env file created")
    else:
        print("✅ .env file already exists")

    # Test import of key modules
    print("\n🧪 Testing imports...")
    test_imports = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "passlib",
        "bcrypt",
        "jose"
    ]

    for module in test_imports:
        try:
            __import__(module)
            print(f"✅ {module} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {module}: {e}")

    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run migration: python comprehensive_migration_test.py")
    print("2. Start server: uvicorn app.main:app --reload")
    print("3. Visit docs: http://localhost:8000/docs")


if __name__ == "__main__":
    main()