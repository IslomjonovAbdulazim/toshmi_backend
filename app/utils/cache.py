import redis
import json
import pickle
from typing import Any, Optional, List
from functools import wraps
from datetime import timedelta
import hashlib
import os

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=False)


class Cache:
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            data = redis_client.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None

    @staticmethod
    def set(key: str, value: Any, expiry: int = 3600):
        """Set value in cache with expiry in seconds"""
        try:
            redis_client.setex(key, expiry, pickle.dumps(value))
        except Exception as e:
            print(f"Cache set error: {e}")

    @staticmethod
    def delete(key: str):
        """Delete key from cache"""
        try:
            redis_client.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")

    @staticmethod
    def delete_pattern(pattern: str):
        """Delete all keys matching pattern"""
        try:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
        except Exception as e:
            print(f"Cache delete pattern error: {e}")

    @staticmethod
    def exists(key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return redis_client.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False


# Cache decorators
def cache_result(expiry: int = 3600, key_prefix: str = ""):
    """Decorator to cache function results"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            func_args = str(args) + str(sorted(kwargs.items()))
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(func_args.encode()).hexdigest()}"

            # Try to get from cache
            cached_result = Cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            Cache.set(cache_key, result, expiry)
            return result

        # Add cache management methods
        wrapper.clear_cache = lambda pattern="": Cache.delete_pattern(f"{key_prefix}:{func.__name__}:*")
        wrapper.cache_key = lambda *args,
                                   **kwargs: f"{key_prefix}:{func.__name__}:{hashlib.md5((str(args) + str(sorted(kwargs.items()))).encode()).hexdigest()}"

        return wrapper

    return decorator


def invalidate_cache_on_change(cache_patterns: List[str]):
    """Decorator to invalidate cache when data changes"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Invalidate related cache patterns
            for pattern in cache_patterns:
                Cache.delete_pattern(pattern)

            return result

        return wrapper

    return decorator


# Specific cache functions for common queries
class QueryCache:
    @staticmethod
    @cache_result(expiry=1800, key_prefix="student")  # 30 minutes
    def get_student_grades(student_id: str):
        """Cache student grades"""
        from app.crud import get_homework_grades_by_student, get_exam_grades_by_student
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            homework_grades = get_homework_grades_by_student(db, student_id)
            exam_grades = get_exam_grades_by_student(db, student_id)
            return {
                "homework": [grade.__dict__ for grade in homework_grades],
                "exams": [grade.__dict__ for grade in exam_grades]
            }
        finally:
            db.close()

    @staticmethod
    @cache_result(expiry=3600, key_prefix="schedule")  # 1 hour
    def get_group_schedule(group_id: str):
        """Cache group schedule"""
        from app.crud import get_schedule_by_group
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            schedule = get_schedule_by_group(db, group_id)
            return [item.__dict__ for item in schedule]
        finally:
            db.close()

    @staticmethod
    @cache_result(expiry=7200, key_prefix="news")  # 2 hours
    def get_all_news():
        """Cache news"""
        from app.crud import get_all_news
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            news = get_all_news(db)
            return [item.__dict__ for item in news]
        finally:
            db.close()

    @staticmethod
    @cache_result(expiry=1800, key_prefix="attendance")  # 30 minutes
    def get_student_attendance(student_id: str):
        """Cache student attendance"""
        from app.crud import get_attendance_by_student
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            attendance = get_attendance_by_student(db, student_id)
            return [item.__dict__ for item in attendance]
        finally:
            db.close()


# Cache invalidation on data changes
class CacheInvalidator:
    @staticmethod
    def invalidate_student_cache(student_id: str):
        """Invalidate all caches related to a student"""
        patterns = [
            f"student:*{student_id}*",
            f"grades:*{student_id}*",
            f"attendance:*{student_id}*"
        ]
        for pattern in patterns:
            Cache.delete_pattern(pattern)

    @staticmethod
    def invalidate_group_cache(group_id: str):
        """Invalidate all caches related to a group"""
        patterns = [
            f"schedule:*{group_id}*",
            f"group:*{group_id}*"
        ]
        for pattern in patterns:
            Cache.delete_pattern(pattern)

    @staticmethod
    def invalidate_news_cache():
        """Invalidate news cache"""
        Cache.delete_pattern("news:*")


# Cache warming functions
class CacheWarmer:
    @staticmethod
    def warm_student_caches(student_ids: List[str]):
        """Pre-load common student data into cache"""
        for student_id in student_ids:
            QueryCache.get_student_grades(student_id)
            QueryCache.get_student_attendance(student_id)

    @staticmethod
    def warm_schedule_caches(group_ids: List[str]):
        """Pre-load schedule data into cache"""
        for group_id in group_ids:
            QueryCache.get_group_schedule(group_id)

    @staticmethod
    def warm_all_caches():
        """Warm up all common caches"""
        from app.database import SessionLocal
        from app.models import Student, Group

        db = SessionLocal()
        try:
            # Get all student and group IDs
            student_ids = [s.id for s in db.query(Student).all()]
            group_ids = [g.id for g in db.query(Group).all()]

            # Warm caches
            CacheWarmer.warm_student_caches(student_ids[:50])  # Limit to 50 most recent
            CacheWarmer.warm_schedule_caches(group_ids)
            QueryCache.get_all_news()
        finally:
            db.close()


# Cache middleware for FastAPI
class CacheMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Check if request should be cached
            path = scope["path"]
            method = scope["method"]

            # Only cache GET requests
            if method == "GET" and self._should_cache(path):
                # Generate cache key from path and query params
                query_string = scope.get("query_string", b"").decode()
                cache_key = f"http:{path}:{hashlib.md5(query_string.encode()).hexdigest()}"

                # Try to get from cache
                cached_response = Cache.get(cache_key)
                if cached_response:
                    await self._send_cached_response(cached_response, send)
                    return

        await self.app(scope, receive, send)

    def _should_cache(self, path: str) -> bool:
        """Determine if path should be cached"""
        cacheable_paths = [
            "/student/news",
            "/student/schedule",
            "/schedule/",
        ]
        return any(path.startswith(cp) for cp in cacheable_paths)

    async def _send_cached_response(self, cached_response, send):
        """Send cached response"""
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": json.dumps(cached_response).encode(),
        })