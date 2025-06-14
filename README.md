# Fatura İşleme ve JSON Dönüştürme API

Bu proje, fatura görüntülerini işleyerek JSON formatında veri çıktısı üreten bir FastAPI uygulamasıdır.

## Sistem Bileşenleri

1. **YOLOv8 Modeli**: Görüntülerden faturaları tespit eder ve kırpar
2. **DocGeoNet**: Kırpılmış fatura görüntülerini düzeltir (eğik, bükülmüş vb. görüntüleri düzleştirir)
3. **Donut OCR**: Düzeltilmiş görüntülerden metin çıkarır ve JSON formatına dönüştürür
4. **NER Modeli**: OCR çıktısından fatura ile ilgili varlıkları tespit eder
5. **FastAPI**: RESTful API sunmak için kullanılan modern, hızlı web framework

### Model Dosyalari
Bu repoda YOLOv8 icin **best.pt** agirligi ve Donut OCR modeli iceren `donut_cord_v2` klasoru yer alir. Eger farkli bir model kullanmak isterseniz `invoice_processor.py` icindeki `YOLO_MODEL_PATH` degiskenini guncelleyebilirsiniz.

## Kurulum

1. Depoyu klonlayin ve dizine gecin:
```bash
git clone <repository-url>
cd InvoiceToJson
```

2. Opsiyonel olarak bir sanal ortam olusturun:
```bash
python -m venv venv
source venv/bin/activate  # Windows icin venv\Scripts\activate
```

3. Gerekli paketleri kurun:
```bash
pip install -r requirements.txt
```

## Proje Yapisi
- `main.py`: FastAPI sunucusu
- `invoice_processor.py`: isleme pipeline
- `ner_processor.py`: OCR çıktısını analiz eden NER modülü
- `best.pt` ve `donut_cord_v2/`: model dosyalari
- `test_api.py`: ornek testler
- `test_images/`: ornek resimler
- `Dockerfile`, `docker-compose.yml`: Docker destek dosyalari

## API Kullanımı

### 1. API'yi Başlatma

```bash
# API'yi başlat
python main.py
```

Bu komut, API'yi `http://localhost:8000` adresinde başlatır. API dokümantasyonuna `http://localhost:8000/docs` adresinden erişebilirsiniz.

### 2. API Endpointleri

#### Dosya Yükleme ile İşleme

```
POST /api/process-file
```

Multipart form data ile bir görüntü dosyası yükleyerek işleme yapabilirsiniz.

**cURL Örneği:**
```bash
curl -X POST "http://localhost:8000/api/process-file" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@fatura.jpg"
```

#### Base64 Kodlu Görüntü ile İşleme

```
POST /api/process-base64
```

JSON body içinde base64 kodlu görüntü göndererek işleme yapabilirsiniz.

**cURL Örneği:**
```bash
curl -X POST "http://localhost:8000/api/process-base64" -H "accept: application/json" -H "Content-Type: application/json" -d '{"base64_image": "base64_encoded_image_data", "filename": "optional_filename.jpg"}'
```

#### Sağlık Kontrolü

```
GET /health
```

API'nin çalışıp çalışmadığını kontrol etmek için kullanabilirsiniz.

### 3. Programatik Kullanım

FastAPI uygulamasını programatik olarak da kullanabilirsiniz:

```python
import requests
import base64

# Dosya yükleme ile işleme
with open("path/to/image.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post("http://localhost:8000/api/process-file", files=files)
    result = response.json()

# Base64 kodlu görüntü ile işleme
with open("path/to/image.jpg", "rb") as f:
    base64_data = base64.b64encode(f.read()).decode('utf-8')
    payload = {"base64_image": base64_data}
    response = requests.post("http://localhost:8000/api/process-base64", json=payload)
    result = response.json()
```

## API Yanıt Formatı

Tüm API endpointleri aşağıdaki formatta yanıt döndürür:

```json
{
  "status": "success|warning|error|partial_success",
  "message": "İşlem açıklaması",
  "process_id": "benzersiz_islem_id",
  "timestamp": 1621234567,
  "input_image": "girdi_goruntu_yolu",
  "invoice_count": 1,
  "success_count": 1,
  "error_count": 0,
  "source_type": "file|bytes|base64",
  "results": [
    {
      "image_path": "islenmis_goruntu_yolu",
      "status": "success",
      "ocr_data": { ... },  // JSON formatında OCR sonuçları
      "entities": [ ... ]   // NER ile tespit edilen varlıklar
    }
  ]
}
```

## Hata Durumları

API, çeşitli hata durumlarını aşağıdaki şekilde ele alır:

- **Fatura tespit edilemedi**: `status: "warning"`, boş `results` dizisi
- **Geçersiz görüntü formatı**: `status: "error"`, hata detayları
- **OCR hatası**: Başarısız olan görüntüler için `status: "error"` olan sonuçlar
- **Kısmi başarı**: Bazı görüntüler başarılı, bazıları başarısız olduğunda `status: "partial_success"`
- **Sunucu hatası**: HTTP 500 yanıtı ve hata detayları

## Test

API'yi test etmek için:

```bash
# FastAPI uygulamasını başlat
python main.py

# Başka bir terminal penceresinde test et
python test_api.py
```

Bu test, hem dosya işleme hem de base64 işleme yöntemlerini test eder ve sonuçları karşılaştırır.

## Geliştirme

### Gereksinimler

Projeyi geliştirmek için aşağıdaki paketlere ihtiyacınız vardır:

- fastapi
- uvicorn
- python-multipart
- ultralytics (YOLOv8 için)
- torch
- transformers (Donut OCR için)
- Pillow
- opencv-python

### Docker ile Çalıştırma

Docker ile çalıştırma hakkında detaylı bilgi için [DockerReadme.md](DockerReadme.md) dosyasına bakınız.

```bash
# Docker imajı oluştur
docker build -t invoice-processor-api .

# Docker konteynerini çalıştır
docker run -p 8000:8000 -v ./test_images:/app/test_images invoice-processor-api
```

Alternatif olarak, Docker Compose ile çalıştırmak için:

```bash
# Docker Compose ile başlat
docker-compose up

# Arka planda çalıştırmak için
docker-compose up -d
```
