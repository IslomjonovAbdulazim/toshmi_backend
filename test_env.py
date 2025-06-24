#!/usr/bin/env python3
"""
Test script to verify .env file loading
Run this to check if your environment variables are being loaded correctly
"""

import os
from pathlib import Path


def test_env_file_exists():
    """Check if .env file exists"""
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file found")
        return True
    else:
        print("❌ .env file not found")
        return False


def test_manual_env_loading():
    """Manually load and test .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()

        print("\n🔍 Environment variables loaded:")
        env_vars = [
            "DATABASE_URL",
            "SECRET_KEY",
            "ALGORITHM",
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "UPLOAD_DIR",
            "MAX_FILE_SIZE",
            "MAX_PROFILE_IMAGE_SIZE",
            "ENVIRONMENT",
            "DEBUG",
            "HOST",
            "PORT"
        ]

        for var in env_vars:
            value = os.getenv(var)
            if value:
                if var == "DATABASE_URL":
                    print(f"  {var}: {value[:50]}...")
                elif var == "SECRET_KEY":
                    print(f"  {var}: {value[:20]}...")
                else:
                    print(f"  {var}: {value}")
            else:
                print(f"  {var}: ❌ NOT FOUND")

    except ImportError:
        print("❌ python-dotenv not installed")
        return False

    return True


def test_pydantic_settings():
    """Test pydantic settings loading"""
    try:
        from app.config import settings

        print("\n📋 Pydantic Settings loaded:")
        print(f"  database_url: {settings.database_url[:50]}...")
        print(f"  secret_key: {settings.secret_key[:20]}...")
        print(f"  algorithm: {settings.algorithm}")
        print(f"  access_token_expire_minutes: {settings.access_token_expire_minutes}")
        print(f"  upload_dir: {settings.upload_dir}")
        print(f"  max_file_size: {settings.max_file_size}")
        print(f"  max_profile_image_size: {settings.max_profile_image_size}")
        print(f"  environment: {settings.environment}")
        print(f"  debug: {settings.debug}")
        print(f"  host: {settings.host}")
        print(f"  port: {settings.port}")

        # Test database URL parsing
        if "gen_user" in settings.database_url:
            print("✅ Your production database URL is loaded correctly!")
        else:
            print("⚠️  Using default database URL, .env might not be loading")

        return True

    except Exception as e:
        print(f"❌ Error loading pydantic settings: {e}")
        return False


def main():
    """Main test function"""
    print("🧪 Testing Environment Variable Loading")
    print("=" * 50)

    # Test 1: Check if .env file exists
    env_exists = test_env_file_exists()

    if not env_exists:
        print("\n💡 Create a .env file in the project root with your configuration")
        return

    # Test 2: Manual loading
    print("\n" + "-" * 30)
    manual_success = test_manual_env_loading()

    # Test 3: Pydantic settings
    print("\n" + "-" * 30)
    pydantic_success = test_pydantic_settings()

    print("\n" + "=" * 50)
    if manual_success and pydantic_success:
        print("🎉 SUCCESS: Environment variables are loading correctly!")
    else:
        print("❌ FAILED: Some issues found with environment loading")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure .env file is in the project root")
        print("2. Check that variable names match exactly")
        print("3. Ensure no spaces around = in .env file")
        print("4. Install python-dotenv: pip install python-dotenv")


if __name__ == "__main__":
    main()