#!/usr/bin/env python3
"""
Education Center Management System - Startup Script
Production-ready script with environment-specific configurations
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings


def run_development():
    """Run in development mode with hot reload"""
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        reload_dirs=["app"],
        log_level="debug",
        access_log=True
    )


def run_production():
    """Run in production mode with multiple workers"""
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=2,  # Adjust based on your server capacity
        log_level="info",
        access_log=True,
        loop="uvloop",  # Better performance on Linux
        http="httptools"  # Better performance
    )


def main():
    """Main entry point"""
    print(f"🚀 Starting Education Center Management System")
    print(f"Environment: {settings.environment}")
    print(f"Host: {settings.host}")
    print(f"Port: {settings.port}")
    print(f"Debug: {settings.debug}")
    print(f"Database: {settings.database_url[:30]}...")

    # Create upload directories if they don't exist
    upload_dirs = [
        settings.upload_dir,
        os.path.join(settings.upload_dir, "profiles"),
        os.path.join(settings.upload_dir, "documents"),
        os.path.join(settings.upload_dir, "news")
    ]

    for upload_dir in upload_dirs:
        os.makedirs(upload_dir, exist_ok=True)

    print(f"📁 Upload directories ensured: {settings.upload_dir}")

    if settings.environment == "development" or settings.debug:
        print("🔧 Running in DEVELOPMENT mode")
        run_development()
    else:
        print("🏭 Running in PRODUCTION mode")
        run_production()


if __name__ == "__main__":
    main()