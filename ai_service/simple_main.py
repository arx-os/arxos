"""
Simplified Arxos AI Service - Just make it work!
"""

import os
import json
import time
import numpy as np
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from processors.pdf_processor import PDFProcessor

# Create FastAPI app
app = FastAPI(title="Arxos AI Service (Simple)")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processor
pdf_processor = PDFProcessor()


class NumpyEncoder(json.JSONEncoder):
    """Handle numpy types in JSON"""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, '__dict__'):
            return str(obj)
        return super().default(obj)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "arxos-ai-simple"}


@app.post("/api/v1/convert")
async def convert_pdf(file: UploadFile = File(...)):
    """Convert PDF to ArxObjects - simplified version"""
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Read file
        contents = await file.read()
        
        # Process PDF
        print(f"Processing PDF: {file.filename}")
        result = await pdf_processor.process_pdf(
            pdf_content=contents,
            building_type="general",
            confidence_threshold=0.3
        )
        
        # Build simple response
        response = {
            "arxobjects": [],
            "overall_confidence": 0.5,
            "processing_time": 1.0,
            "uncertainties": []
        }
        
        # Convert ArxObjects to simple dicts
        for obj in result.arxobjects[:500]:  # Limit to 500 objects for now
            try:
                simple_obj = {
                    "id": str(obj.id),
                    "type": "wall",  # Default to wall for now
                    "confidence": {"overall": 0.7},
                    "data": {},
                    "geometry": None,
                    "relationships": []
                }
                
                # Try to get type
                if hasattr(obj, 'type'):
                    if hasattr(obj.type, 'value'):
                        simple_obj["type"] = str(obj.type.value)
                    else:
                        simple_obj["type"] = str(obj.type)
                
                # Try to get confidence
                if hasattr(obj, 'confidence') and obj.confidence:
                    if hasattr(obj.confidence, 'overall'):
                        simple_obj["confidence"]["overall"] = float(obj.confidence.overall)
                
                # Try to get geometry
                if hasattr(obj, 'geometry') and obj.geometry:
                    simple_obj["geometry"] = obj.geometry
                
                # Try to get data
                if hasattr(obj, 'data') and obj.data:
                    # Convert numpy types in data
                    clean_data = {}
                    for k, v in obj.data.items():
                        if isinstance(v, (np.number, np.bool_)):
                            clean_data[k] = float(v)
                        else:
                            clean_data[k] = v
                    simple_obj["data"] = clean_data
                
                response["arxobjects"].append(simple_obj)
                
            except Exception as e:
                print(f"Error converting object: {e}")
                continue
        
        # Set overall stats
        if hasattr(result, 'overall_confidence'):
            response["overall_confidence"] = float(result.overall_confidence)
        if hasattr(result, 'processing_time'):
            response["processing_time"] = float(result.processing_time)
        
        print(f"Returning {len(response['arxobjects'])} objects")
        
        # Convert to JSON string with custom encoder, then parse back
        json_str = json.dumps(response, cls=NumpyEncoder)
        return JSONResponse(content=json.loads(json_str))
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("Starting Arxos AI Service (Simple) on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)