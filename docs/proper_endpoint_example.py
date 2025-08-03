
# Example of Proper Endpoint Definition with Authentication

from fastapi import FastAPI, Depends, HTTPException
from core.security.auth_middleware import get_current_user, User
from pydantic import BaseModel

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    user_id: str

@app.get("/health")
async def health_check(user: User = Depends(get_current_user)):
    """Health check endpoint with authentication"""
    return {
        "status": "healthy",
        "user_id": user.id,
        "service": "example"
    }

@app.post("/api/v1/query")
async def process_query(request: QueryRequest, user: User = Depends(get_current_user)):
    """Process query endpoint with authentication"""
    try:
        # Process the query
        return {
            "success": True,
            "query": request.query,
            "user_id": user.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
