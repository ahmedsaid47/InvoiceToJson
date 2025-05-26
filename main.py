from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import base64
from typing import Optional
import os
import time
import logging
import traceback
from invoice_processor import InvoiceProcessor

# Import the centralized safe globals module
from torch_safe_globals import register_safe_globals

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main_api")

# Register safe globals before loading any models
# This is automatically done when importing the module, but we call it again to be sure
register_safe_globals()
logger.info("PyTorch safe globals registered")

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
    temp_path = None
    try:
        # Create a temporary file in /tmp directory (writable)
        timestamp = int(time.time())
        filename = f"upload_{timestamp}_{file.filename}"
        temp_path = os.path.join("/tmp", filename)

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
        if temp_path and os.path.exists(temp_path):
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
