from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import re
import json
from typing import Dict, Any


class InputValidationMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Validate request size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                response = JSONResponse(
                    status_code=413,
                    content={"error": "Request too large"}
                )
                await response(scope, receive, send)
                return

            # Validate file uploads
            if request.headers.get("content-type", "").startswith("multipart/form-data"):
                await self._validate_file_upload(request, scope, receive, send)
                return

            # Validate JSON payloads
            if request.headers.get("content-type") == "application/json":
                body = await request.body()
                if body:
                    try:
                        data = json.loads(body)
                        await self._validate_json_payload(data, scope, receive, send)
                    except json.JSONDecodeError:
                        response = JSONResponse(
                            status_code=400,
                            content={"error": "Invalid JSON"}
                        )
                        await response(scope, receive, send)
                        return

        await self.app(scope, receive, send)

    async def _validate_file_upload(self, request: Request, scope, receive, send):
        """Validate file upload safety"""
        dangerous_extensions = ['.exe', '.bat', '.sh', '.php', '.asp', '.jsp']

        form = await request.form()
        for field_name, field_value in form.items():
            if hasattr(field_value, 'filename') and field_value.filename:
                filename = field_value.filename.lower()
                if any(filename.endswith(ext) for ext in dangerous_extensions):
                    response = JSONResponse(
                        status_code=400,
                        content={"error": f"File type not allowed: {filename}"}
                    )
                    await response(scope, receive, send)
                    return

    async def _validate_json_payload(self, data: Dict[str, Any], scope, receive, send):
        """Validate JSON for XSS and injection attacks"""
        if self._contains_suspicious_content(data):
            response = JSONResponse(
                status_code=400,
                content={"error": "Suspicious content detected"}
            )
            await response(scope, receive, send)
            return

    def _contains_suspicious_content(self, obj) -> bool:
        """Check for XSS and SQL injection patterns"""
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'(union|select|insert|delete|update|drop)\s+',
            r'--\s',
            r'/\*.*?\*/',
        ]

        def check_string(s: str) -> bool:
            s_lower = s.lower()
            return any(re.search(pattern, s_lower, re.IGNORECASE | re.DOTALL)
                       for pattern in suspicious_patterns)

        def check_recursive(obj) -> bool:
            if isinstance(obj, str):
                return check_string(obj)
            elif isinstance(obj, dict):
                return any(check_recursive(v) or check_string(str(k))
                           for k, v in obj.items())
            elif isinstance(obj, list):
                return any(check_recursive(item) for item in obj)
            return False

        return check_recursive(obj)