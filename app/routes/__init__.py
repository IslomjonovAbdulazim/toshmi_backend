"""
Routes package for Education Center Management System
"""

# Import all routers for easy access
from . import auth, admin, teacher, student, parent, files

__all__ = ["auth", "admin", "teacher", "student", "parent", "files"]
