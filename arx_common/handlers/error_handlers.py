from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from arx_common.models.error import ErrorResponse
from typing import Optional

# Handler for HTTPException
async def http_exception_handler(request: Request, exc: HTTPException):
    response = ErrorResponse(
        error=exc.detail if exc.detail else "HTTP error",
        code=str(exc.status_code),
        details={"path": str(request.url)}
    )
    return JSONResponse(status_code=exc.status_code, content=response.dict())

# Handler for RequestValidationError
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    response = ErrorResponse(
        error="Validation error",
        code="422",
        details={"errors": exc.errors(), "path": str(request.url)}
    )
    return JSONResponse(status_code=422, content=response.dict())

# Handler for generic exceptions
async def generic_exception_handler(request: Request, exc: Exception):
    response = ErrorResponse(
        error="Internal Server Error",
        code="INTERNAL_ERROR",
        details={"path": str(request.url)}
    )
    return JSONResponse(status_code=500, content=response.dict()) 