# ---------- 1. Aşama: Build ----------
FROM python:3.9-slim AS builder

# Çalışma dizini
WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Gereksinimler dosyasını kopyala
COPY requirements.txt .

# Sanal ortam oluştur
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Python bağımlılıklarını kur
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "torch>=2.2,<3" && \
    pip install --no-cache-dir protobuf sentencepiece && \
    pip install --no-cache-dir torch-safe-globals==0.1.5

# PyTorch sürümünü kontrol et
RUN python -c "import torch, sys; assert torch.__version__ >= '2.2.0', f'PyTorch {torch.__version__} < 2.2.0'; print('PyTorch version:', torch.__version__)"

# ---------- 2. Aşama: Runtime ----------
FROM python:3.9-slim

WORKDIR /app

# Uygulama kullanıcısı
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

# Runtime için gerekli kütüphaneler
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Sanal ortamı kopyala
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Klasörleri oluştur
RUN mkdir -p cropped rectified test_images && \
    chown -R appuser:appuser /app

# Uygulama kodunu kopyala
COPY --chown=appuser:appuser main.py invoice_processor.py donut_ocr.py docgeonet_correct.py yolo_crop_and_ocr.py ./
COPY --chown=appuser:appuser best.pt ./

# Model klasörleri
COPY --chown=appuser:appuser DocGeoNet/ ./DocGeoNet/
COPY --chown=appuser:appuser donut_cord_v2/ ./donut_cord_v2/
COPY --chown=appuser:appuser hf_docgeonet/ ./hf_docgeonet/

# Jupyter not defteri (opsiyonel)
COPY --chown=appuser:appuser torch_safe_globals.ipynb ./

# Volume
VOLUME /app/test_images

# Port
EXPOSE 8000

# Ortam değişkenleri
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TORCH_HOME=/app/.torch
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# Yetkisiz kullanıcıya geç
USER appuser

# Sağlık kontrolü
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Başlatma komutu
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "100", "--timeout-keep-alive", "30"]