from fastapi import Request, status
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, public_paths: List[str] = None):
        super().__init__(app)
        self.public_paths = public_paths or [
            "/auth/login",
            "/auth/register",
            "/docs",
            "/openapi.json",
            "/static"
        ]
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Пропускаем публичные пути
        for public in self.public_paths:
            if path.startswith(public):
                return await call_next(request)
        
        # Проверяем токен
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
        
        if not token:
            accept = request.headers.get("accept", "")
            if "text/html" in accept or "application/xhtml+xml" in accept:
                return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
        
        return await call_next(request)