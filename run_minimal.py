#!/usr/bin/env python3
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
