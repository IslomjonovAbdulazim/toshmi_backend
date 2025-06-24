#!/usr/bin/env python3
"""
Education Center Management System - Deployment Script
Handles initial setup, database initialization, and environment configuration
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description=""):
    """Run shell command and handle errors"""
    print(f"🔄 {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None


def create_directories():
    """Create necessary directories"""
    print("📁 Creating upload directories...")
    directories = [
        "uploads",
        "uploads/profiles",
        "uploads/documents",
        "uploads/news",
        "logs"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def check_environment():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")

    if not env_file.exists():
        print("❌ .env file not found!")
        print("Creating sample .env file...")

        sample_env = """# Education Center Management System - Environment Configuration

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost/education_center_db

# Security Configuration  
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload Configuration
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
MAX_PROFILE_IMAGE_SIZE=3145728

# Environment Settings
ENVIRONMENT=development
DEBUG=True

# Server Configuration
HOST=0.0.0.0
PORT=8000
"""

        with open(".env", "w") as f:
            f.write(sample_env)

        print("✅ Sample .env file created. Please update it with your configuration.")
        return False

    print("✅ .env file found")
    return True


def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")

    # Check if we're in a virtual environment
    if sys.prefix == sys.base_prefix:
        print("⚠️  Warning: Not in a virtual environment")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Deployment cancelled")
            return False

    return run_command("pip install -r requirements.txt", "Installing dependencies")


def setup_database():
    """Setup database and create initial data"""
    print("🗄️  Setting up database...")

    # Try to run the database initialization script
    result = run_command("python scripts/init_database.py", "Initializing database")

    if result is None:
        print("❌ Database initialization failed")
        print("💡 Make sure your database server is running and the DATABASE_URL in .env is correct")
        return False

    return True


def run_tests():
    """Run basic tests to ensure everything is working"""
    print("🧪 Running basic tests...")

    # Test if the application starts
    print("Testing application startup...")

    try:
        # Import main modules to check for import errors
        from app.main import app
        from app.database import engine
        from app.models import User

        print("✅ All imports successful")
        return True

    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        return False


def display_startup_info():
    """Display information about how to start the application"""
    print("\n" + "=" * 60)
    print("🎉 Deployment completed successfully!")
    print("=" * 60)

    print("\n🚀 To start the application:")
    print("   Development: python run.py")
    print("   Production:  uvicorn app.main:app --host 0.0.0.0 --port 8000")

    print("\n📖 API Documentation:")
    print("   Swagger UI: http://localhost:8000/docs")
    print("   ReDoc:      http://localhost:8000/redoc")

    print("\n🔐 Default Admin Credentials:")
    print("   Phone: 998901234567")
    print("   Role: admin")
    print("   Password: admin123")
    print("   ⚠️  CHANGE THE PASSWORD AFTER FIRST LOGIN!")

    print("\n📝 Important Notes:")
    print("   • Update your .env file with production settings")
    print("   • Set up SSL certificates for production")
    print("   • Configure your reverse proxy (nginx)")
    print("   • Set up regular database backups")

    print("\n🐛 If you encounter issues:")
    print("   • Check the logs in the logs/ directory")
    print("   • Verify your database connection")
    print("   • Ensure all environment variables are set")
    print("   • Check file permissions for upload directories")


def main():
    """Main deployment function"""
    print("🚀 Education Center Management System - Deployment")
    print("=" * 60)

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    print(f"📂 Working directory: {os.getcwd()}")

    # Check environment file
    if not check_environment():
        print("❌ Please configure your .env file and run the deployment again")
        return 1

    # Create directories
    create_directories()

    # Install dependencies
    if install_dependencies() is None:
        print("❌ Failed to install dependencies")
        return 1

    # Setup database
    if not setup_database():
        print("❌ Database setup failed")
        return 1

    # Run tests
    if not run_tests():
        print("❌ Tests failed")
        return 1

    # Display startup information
    display_startup_info()

    return 0


if __name__ == "__main__":
    sys.exit(main())