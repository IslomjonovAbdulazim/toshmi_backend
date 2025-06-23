# app/crud/__init__.py
from .user_crud import *
from .academic_crud import *
from .grade_crud import *
from .misc_crud import *
from .recent_grades_crud import *

# Import bulk grade operations
try:
    from .bulk_grade_crud import *
except ImportError:
    pass