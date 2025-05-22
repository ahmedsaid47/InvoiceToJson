from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import base64
from typing import Optional
import os
import time
from invoice_processor import InvoiceProcessor

# Initialize the FastAPI app
app = FastAPI(
    title="Invoice Processing API",
    description="API for processing invoice images and extracting structured data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the invoice processor
processor = InvoiceProcessor()

# Define request models
class Base64Request(BaseModel):
    base64_image: str
    filename: Optional[str] = None

# Define response model
class ProcessingResponse(BaseModel):
    status: str
    message: str
    process_id: str
    timestamp: int
    invoice_count: Optional[int] = None
    success_count: Optional[int] = None
    error_count: Optional[int] = None
    results: list

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Invoice Processing API is running",
        "docs": "/docs",
        "endpoints": [
            "/api/process-file",
            "/api/process-base64"
        ]
    }

# Process file endpoint
@app.post("/api/process-file", response_model=ProcessingResponse)
async def process_file(file: UploadFile = File(...)):
    try:
        # Create a temporary file
        timestamp = int(time.time())
        filename = f"upload_{timestamp}_{file.filename}"
        temp_path = os.path.join(os.getcwd(), filename)
        
        # Save the uploaded file
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process the image
        result = processor.process_image(temp_path)
        
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return result
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

# Process base64 endpoint
@app.post("/api/process-base64", response_model=ProcessingResponse)
async def process_base64(request: Base64Request):
    try:
        result = processor.process_base64_image(request.base64_image, request.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": int(time.time())}

# Run the app
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)