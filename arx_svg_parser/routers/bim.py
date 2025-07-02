from fastapi import APIRouter
from pydantic import BaseModel, Field
from arx_svg_parser.models.system_elements import ExtractionResponse
from arx_svg_parser.services.bim_extractor import extract_bim_from_svg

router = APIRouter()

class BIMParseRequest(BaseModel):
    svg_xml: str = Field(..., min_length=10)
    building_id: str
    floor_id: str

@router.post("/bim/parse", response_model=ExtractionResponse)
def bim_parse(request: BIMParseRequest):
    return extract_bim_from_svg(request.svg_xml, request.building_id, request.floor_id) 