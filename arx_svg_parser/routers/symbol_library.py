from fastapi import APIRouter, Query, HTTPException
from services.svg_symbol_library import load_symbol_library

router = APIRouter()

@router.get("/symbols")
def list_symbols(q: str = Query(None, description="Search string"), category: str = Query(None, description="Category filter")):
    symbols = load_symbol_library(search=q, category=category)
    return {"results": symbols, "count": len(symbols)}

@router.get("/symbols/{symbol_id}")
def get_symbol(symbol_id: str):
    symbols = load_symbol_library()
    for s in symbols:
        if s.get('symbol_id') == symbol_id:
            return s
    raise HTTPException(status_code=404, detail="Symbol not found") 