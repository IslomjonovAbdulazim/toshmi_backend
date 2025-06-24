#!/usr/bin/env python3
"""
Quick Fix Script for Education Center Management System
Addresses the RecursionError by fixing circular references and imports
"""

import os
import sys
from pathlib import Path


def fix_init_files():
    """Fix __init__.py files that might have circular imports"""

    init_files = [
        "app/__init__.py",
        "app/routes/__init__.py",
        "app/schemas/__init__.py",
        "app/services/__init__.py",
        "app/utils/__init__.py"
    ]

    print("🔧 Fixing __init__.py files...")

    for init_file in init_files:
        if os.path.exists(init_file):
            # Clear the init file to avoid circular imports
            with open(init_file, 'w') as f:
                f.write("# Empty init file to avoid circular imports\n")
            print(f"✅ Fixed {init_file}")
        else:
            # Create empty init file
            os.makedirs(os.path.dirname(init_file), exist_ok=True)
            with open(init_file, 'w') as f:
                f.write("# Empty init file\n")
            print(f"✅ Created {init_file}")


def create_fixed_routes_init():
    """Create proper routes __init__.py"""

    routes_init_content = '''"""
Routes package for Education Center Management System
"""

# Import all routers for easy access
from . import auth, admin, teacher, student, parent, files

__all__ = ["auth", "admin", "teacher", "student", "parent", "files"]
'''

    with open("app/routes/__init__.py", "w") as f:
        f.write(routes_init_content)

    print("✅ Fixed app/routes/__init__.py")


def fix_database_connection():
    """Fix database connection issues"""

    database_fix_content = '''from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Create SQLAlchemy engine with proper configuration
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=300,    # Recycle connections every 5 minutes
    connect_args={
        "connect_timeout": 10,
        "sslmode": "require" if "twc1.net" in settings.database_url else "prefer"
    }
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create tables
def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        raise
'''

    with open("app/database.py", "w") as f:
        f.write(database_fix_content)

    print("✅ Fixed app/database.py")


def create_minimal_run_script():
    """Create a minimal run script for testing"""

    run_script_content = '''#!/usr/bin/env python3
"""
Minimal run script for testing the Education Center Management System
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main entry point with error handling"""
    try:
        print("🚀 Starting Education Center Management System (Minimal Mode)")

        # Create upload directories
        upload_dirs = ["uploads", "uploads/profiles", "uploads/documents", "uploads/news"]
        for upload_dir in upload_dirs:
            os.makedirs(upload_dir, exist_ok=True)

        # Start the server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload to avoid issues
            log_level="info"
        )

    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("💡 Try installing missing dependencies: pip install -r requirements.txt")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Startup error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

    with open("run_minimal.py", "w") as f:
        f.write(run_script_content)

    print("✅ Created run_minimal.py")


def check_and_fix_env():
    """Check and fix .env file"""

    if not os.path.exists(".env"):
        print("📝 Creating .env file from provided configuration...")

        env_content = '''# Education Center Management System - Production Environment
# Timeweb Cloud Configuration

# Database Configuration
DATABASE_URL=postgresql://gen_user:(8Ah)S$aY)lF6t@3d7780415a2721a636acfe11.twc1.net:5432/default_db?sslmode=require

# Security Configuration
SECRET_KEY=UgoxERiU-d3vFK8z-a9lU_mRrN12oWKcUu_zjn1CHZ0
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload Configuration
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
MAX_PROFILE_IMAGE_SIZE=3145728

# Environment Settings
ENVIRONMENT=production
DEBUG=False

# Server Configuration
HOST=0.0.0.0
PORT=8000
'''

        with open(".env", "w") as f:
            f.write(env_content)

        print("✅ Created .env file with production configuration")
    else:
        print("✅ .env file already exists")


def test_imports():
    """Test if the main imports work"""

    print("🧪 Testing imports...")

    try:
        # Test basic imports
        print("Testing basic imports...")

        # Add current directory to path
        sys.path.insert(0, str(Path.cwd()))

        # Test config import
        from app.config import settings
        print("✅ Config import successful")

        # Test database import
        from app.database import get_db
        print("✅ Database import successful")

        # Test models import
        from app.models import User, Student, Teacher, Parent
        print("✅ Models import successful")

        # Test main app import
        from app.main import app
        print("✅ Main app import successful")

        print("🎉 All imports successful!")
        return True

    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False


def main():
    """Main fix function"""
    print("🔧 Education Center Management System - Quick Fix")
    print("=" * 60)

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    print(f"📂 Working directory: {os.getcwd()}")

    # Fix init files
    fix_init_files()

    # Create proper routes init
    create_fixed_routes_init()

    # Fix database connection
    fix_database_connection()

    # Check and fix .env
    check_and_fix_env()

    # Create minimal run script
    create_minimal_run_script()

    # Test imports
    if test_imports():
        print("\n🎉 Quick fix completed successfully!")
        print("\n🚀 Try running the application:")
        print("   python run_minimal.py")
        print("\n📖 API Documentation will be available at:")
        print("   http://localhost:8000/docs")
    else:
        print("\n❌ Some issues remain. Check the error messages above.")
        print("\n💡 Suggestions:")
        print("   • Install dependencies: pip install -r requirements.txt")
        print("   • Check your Python version (3.8+ required)")
        print("   • Verify database connection settings")

    return 0


if __name__ == "__main__":
    sys.exit(main())
