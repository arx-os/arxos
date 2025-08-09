
# Example of secure endpoint with authentication

from fastapi import FastAPI, Depends, HTTPException
from core.security.auth_middleware import get_current_user, User

app = FastAPI()

@app.post("/api/v1/secure-endpoint")
async def secure_endpoint(
    request: YourRequestModel,
    user: User = Depends(get_current_user)
):
    """Secure endpoint with authentication"""

    # User is automatically authenticated
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is disabled")

    # Check user roles
    if "admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Process request
    return {"message": "Success", "user_id": user.id}

# For role-based access
@app.get("/api/v1/admin-only")
async def admin_only_endpoint(user: User = Depends(get_current_user)):
    """Admin-only endpoint"""
    if "admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")

    return {"message": "Admin access granted"}
