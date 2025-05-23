FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p cropped rectified

# Copy the application code
COPY main.py invoice_processor.py donut_ocr.py docgeonet_correct.py yolo_crop_and_ocr.py ./
COPY best.pt ./

# Copy model directories if they exist
COPY DocGeoNet/ ./DocGeoNet/
COPY donut_cord_v2/ ./donut_cord_v2/
COPY hf_docgeonet/ ./hf_docgeonet/

# Create volume for test images
VOLUME /app/test_images

# Expose the port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
