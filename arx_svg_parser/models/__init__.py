from pydantic import BaseModel

class UploadResponse(BaseModel):
    status: str
    file_id: str

class HealthResponse(BaseModel):
    status: str 