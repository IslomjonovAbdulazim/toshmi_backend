from .auth import router as auth_router
from .admin import router as admin_router
from .teacher import router as teacher_router
from .student import router as student_router
from .parent import router as parent_router
from .schedule import router as schedule_router

# Import optional routers with error handling
try:
    from .profile import router as profile_router
except ImportError:
    profile_router = None

try:
    from .search import router as search_router
except ImportError:
    search_router = None

try:
    from .bulk import router as bulk_router
except ImportError:
    bulk_router = None

__all__ = [
    "auth_router",
    "admin_router",
    "teacher_router",
    "student_router",
    "parent_router",
    "schedule_router",
    "profile_router",
    "search_router",
    "bulk_router"
]