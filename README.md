# Fatura İşleme ve JSON Dönüştürme Sistemi

Bu proje, fatura görüntülerini işleyerek JSON formatında veri çıktısı üreten bir sistemdir. .NET API'ye entegre edilmek üzere tasarlanmıştır.

## Sistem Bileşenleri

1. **YOLOv8 Modeli**: Görüntülerden faturaları tespit eder ve kırpar
2. **DocGeoNet**: Kırpılmış fatura görüntülerini düzeltir (eğik, bükülmüş vb. görüntüleri düzleştirir)
3. **Donut OCR**: Düzeltilmiş görüntülerden metin çıkarır ve JSON formatına dönüştürür

## Kullanım

Sistem üç farklı şekilde kullanılabilir:

### 1. Komut Satırı Kullanımı

```bash
python yolo_crop_and_ocr.py
```

Bu komut, `test_images` klasöründeki tüm görüntüleri işler.

### 2. Tek Dosya İşleme

```bash
python invoice_processor.py /path/to/image.jpg
```

### 3. API Entegrasyonu için InvoiceProcessor Sınıfı

```python
from invoice_processor import InvoiceProcessor

# Processor oluştur
processor = InvoiceProcessor()

# Dosya yolu ile işle
result = processor.process_image("path/to/image.jpg")

# Byte array ile işle
with open("path/to/image.jpg", "rb") as f:
    image_bytes = f.read()
result = processor.process_image_bytes(image_bytes)

# Base64 kodlu görüntü ile işle
import base64
with open("path/to/image.jpg", "rb") as f:
    base64_data = base64.b64encode(f.read()).decode('utf-8')
result = processor.process_base64_image(base64_data)
```

## .NET API Entegrasyonu

.NET API'ye entegrasyon için `InvoiceProcessor` sınıfı kullanılabilir. Örnek bir .NET Controller:

```csharp
[ApiController]
[Route("api/[controller]")]
public class InvoiceController : ControllerBase
{
    [HttpPost("process")]
    public async Task<IActionResult> ProcessInvoice(IFormFile file)
    {
        // Python process'i başlat
        var startInfo = new ProcessStartInfo
        {
            FileName = "python",
            Arguments = $"invoice_processor.py \"{file.FileName}\"",
            RedirectStandardOutput = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };
        
        using var process = Process.Start(startInfo);
        var output = await process.StandardOutput.ReadToEndAsync();
        await process.WaitForExitAsync();
        
        // JSON çıktıyı parse et
        var result = JsonConvert.DeserializeObject(output);
        return Ok(result);
    }
    
    [HttpPost("process-base64")]
    public async Task<IActionResult> ProcessBase64([FromBody] Base64Request request)
    {
        // Python process'i başlat ve base64 veriyi gönder
        // ...
    }
}
```

## API Yanıt Formatı

Tüm API çağrıları aşağıdaki formatta yanıt döndürür:

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
      "ocr_data": { ... }  // JSON formatında OCR sonuçları
    }
  ]
}
```

## Hata Durumları

Sistem, çeşitli hata durumlarını aşağıdaki şekilde ele alır:

- **Fatura tespit edilemedi**: `status: "warning"`, boş `results` dizisi
- **Geçersiz görüntü formatı**: `status: "error"`, hata detayları
- **OCR hatası**: Başarısız olan görüntüler için `status: "error"` olan sonuçlar
- **Kısmi başarı**: Bazı görüntüler başarılı, bazıları başarısız olduğunda `status: "partial_success"`

## Test

Sistemi test etmek için:

```bash
python test_api.py
```

Bu komut, hem dosya işleme hem de base64 işleme yöntemlerini test eder ve sonuçları karşılaştırır.