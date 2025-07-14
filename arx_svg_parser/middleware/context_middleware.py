import structlog
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            path=request.url.path,
            method=request.method,
            client=request.client.host
        )
        response = await call_next(request)
        return response 