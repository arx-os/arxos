from fastapi import APIRouter, HTTPException
from typing import List
from services.svg_writer import write_svg
from models.annotate import Annotation, AnnotateRequest, AnnotateResponse

router = APIRouter()

@router.post("/annotate", response_model=AnnotateResponse)
def annotate_svg(request: AnnotateRequest):
    # Convert Pydantic models to dicts for write_svg
    annotations = [a.dict() for a in request.annotations]
    result = write_svg(request.svg_xml, annotations)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"modified_svg": result} 