import os
import sys
import json
import tempfile
import base64
import io
from pathlib import Path
from PIL import Image
from ultralytics import YOLO
from donut_ocr import img2json
from docgeonet_correct import correct_with_docgeonet
import time
import traceback


class InvoiceProcessor:
    def __init__(self, yolo_model_path="best.pt", device=None):
        self.YOLO_MODEL_PATH = yolo_model_path
        self.DOCGEONET_DIR = "DocGeoNet"
        self.CONF_THRESHOLD = 0.20
        self.IMGSZ = 640

        # Always use temporary directories for processing
        self.use_temp_dirs = True

        # Create temporary directories that will be cleaned up after processing
        self.temp_base_dir = tempfile.mkdtemp(prefix="invoice_processor_")
        self.CROP_DIR = os.path.join(self.temp_base_dir, "cropped")
        self.REC_DIR = os.path.join(self.temp_base_dir, "rectified")
        os.makedirs(self.CROP_DIR, exist_ok=True)
        os.makedirs(self.REC_DIR, exist_ok=True)

        # YOLOv8 modelini yükle
        self.yolo_model = YOLO(self.YOLO_MODEL_PATH)
        self.device = device if device else ('cuda' if self.yolo_model.device.type == 'cuda' else 'cpu')
        print(f"YOLOv8 yüklendi: {self.YOLO_MODEL_PATH} | Cihaz: {self.device}")

    def __del__(self):
        """Destructor to ensure temporary directories are cleaned up when object is destroyed"""
        if hasattr(self, 'use_temp_dirs') and self.use_temp_dirs and hasattr(self, 'temp_base_dir'):
            if os.path.exists(self.temp_base_dir):
                try:
                    import shutil
                    shutil.rmtree(self.temp_base_dir)
                    print(f"Temporary directory cleaned up in destructor: {self.temp_base_dir}")
                except Exception as e:
                    print(f"Error cleaning up temporary directory in destructor: {str(e)}")

    def clamp(self, v, lo, hi):
        return max(lo, min(v, hi))

    def cleanup_temp_dirs(self):
        """Clean up temporary directories if they exist"""
        if hasattr(self, 'use_temp_dirs') and self.use_temp_dirs and hasattr(self, 'temp_base_dir'):
            if os.path.exists(self.temp_base_dir):
                try:
                    import shutil
                    shutil.rmtree(self.temp_base_dir)
                    print(f"Temporary directory cleaned up: {self.temp_base_dir}")
                except Exception as e:
                    print(f"Error cleaning up temporary directory: {str(e)}")

            # Create new temporary directories for next processing
            self.temp_base_dir = tempfile.mkdtemp(prefix="invoice_processor_")
            self.CROP_DIR = os.path.join(self.temp_base_dir, "cropped")
            self.REC_DIR = os.path.join(self.temp_base_dir, "rectified")
            os.makedirs(self.CROP_DIR, exist_ok=True)
            os.makedirs(self.REC_DIR, exist_ok=True)

    def crop_invoices_from_img(self, img_path):
        """Fatura görüntüsünü kırp"""
        results = self.yolo_model.predict(img_path, conf=self.CONF_THRESHOLD,
                                          imgsz=self.IMGSZ, device=self.device,
                                          save=False, verbose=False)[0]
        n = len(results.boxes)
        print(f"{Path(img_path).name} - {n} fatura bulundu")
        orig = results.orig_img.copy()
        H, W = orig.shape[:2]
        crop_paths = []

        for idx, b in enumerate(results.boxes.xyxy.cpu().numpy().astype(int)):
            x1, y1, x2, y2 = [self.clamp(x, 0, W - 1 if i % 2 == 0 else H - 1) for i, x in
                              enumerate([b[0], b[1], b[2], b[3]])]
            crop = orig[y1:y2, x1:x2]
            cpath = Path(self.CROP_DIR) / f"crop_{Path(img_path).stem}_{idx:02d}.jpg"
            os.makedirs(os.path.dirname(cpath), exist_ok=True)
            import cv2
            cv2.imwrite(str(cpath), crop)
            crop_paths.append(str(cpath))
        return crop_paths, n

    def process_image(self, image_path):
        """Tek bir fatura görüntüsünü işle"""
        try:
            # Girdi doğrulama
            if not image_path or not isinstance(image_path, str):
                return {
                    "status": "error",
                    "message": "Geçersiz görüntü yolu",
                    "error_details": "image_path parametresi geçerli bir string olmalıdır",
                    "timestamp": int(time.time()),
                    "results": []
                }

            if not os.path.exists(image_path):
                return {
                    "status": "error",
                    "message": f"Dosya bulunamadı: {image_path}",
                    "error_details": "Belirtilen dosya sistemde bulunamadı",
                    "timestamp": int(time.time()),
                    "results": []
                }

            # Benzersiz bir işlem ID'si oluştur
            process_id = f"process_{int(time.time())}_{hash(image_path) % 10000}"
            timestamp = int(time.time())

            # 1. Faturayı tespit et ve kırp
            crop_paths, invoice_count = self.crop_invoices_from_img(image_path)
            if not crop_paths:
                # Clean up temporary directories before returning
                if hasattr(self, 'use_temp_dirs') and self.use_temp_dirs:
                    self.cleanup_temp_dirs()
                return {
                    "status": "warning", 
                    "message": "Fatura tespit edilemedi", 
                    "process_id": process_id,
                    "timestamp": timestamp,
                    "input_image": image_path,
                    "invoice_count": 0,
                    "results": []
                }

            # 2. DocGeoNet ile düzelt
            rectified_imgs = correct_with_docgeonet(self.DOCGEONET_DIR, self.CROP_DIR, self.REC_DIR)

            # 3. OCR ile işle
            results = []
            success_count = 0
            error_count = 0

            for rec_img_path in rectified_imgs:
                print(f"OCR başlatılıyor: {rec_img_path}")
                try:
                    ocr_result = img2json(rec_img_path)
                    # JSON formatını doğrula
                    try:
                        # Eğer string JSON formatında ise, parse et
                        parsed_json = json.loads(ocr_result) if isinstance(ocr_result, str) else ocr_result
                        results.append({
                            "image_path": rec_img_path,
                            "status": "success",
                            "ocr_data": parsed_json
                        })
                        success_count += 1
                    except json.JSONDecodeError:
                        # JSON formatında değilse, düz metin olarak ekle
                        results.append({
                            "image_path": rec_img_path,
                            "status": "partial_success",
                            "ocr_text": ocr_result
                        })
                        success_count += 1
                except Exception as e:
                    error_msg = f"OCR hatası: {str(e)}"
                    print(error_msg)
                    results.append({
                        "image_path": rec_img_path,
                        "status": "error",
                        "error": error_msg
                    })
                    error_count += 1

            # Genel durumu belirle
            status = "success"
            if success_count == 0 and error_count > 0:
                status = "error"
            elif success_count > 0 and error_count > 0:
                status = "partial_success"

            # Prepare result
            result = {
                "status": status,
                "message": f"{invoice_count} fatura tespit edildi, {success_count} başarılı, {error_count} hatalı",
                "process_id": process_id,
                "timestamp": timestamp,
                "input_image": image_path,
                "invoice_count": invoice_count,
                "success_count": success_count,
                "error_count": error_count,
                "results": results
            }

            # Clean up temporary directories after processing
            if hasattr(self, 'use_temp_dirs') and self.use_temp_dirs:
                self.cleanup_temp_dirs()

            return result

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"İşleme hatası: {str(e)}\n{error_details}")

            # Clean up temporary directories even if an error occurs
            if hasattr(self, 'use_temp_dirs') and self.use_temp_dirs:
                self.cleanup_temp_dirs()

            return {
                "status": "error",
                "message": f"İşleme hatası: {str(e)}",
                "error_details": error_details,
                "timestamp": int(time.time()),
                "input_image": image_path if 'image_path' in locals() else None,
                "results": []
            }

    def process_image_bytes(self, image_bytes, filename=None):
        """Byte array olarak gelen görüntüyü işle - API için gerekli"""
        timestamp = int(time.time())
        process_id = f"process_{timestamp}_{hash(str(image_bytes)[:100]) % 10000}"

        # Girdi doğrulama
        if not image_bytes:
            return {
                "status": "error",
                "message": "Geçersiz görüntü verisi",
                "error_details": "image_bytes parametresi boş olamaz",
                "timestamp": timestamp,
                "process_id": process_id,
                "results": []
            }

        try:
            if filename is None:
                filename = f"upload_{timestamp}.jpg"

            # Geçici dosya oluştur
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, filename)

            try:
                with open(temp_path, "wb") as f:
                    f.write(image_bytes)

                # İşleme yap
                result = self.process_image(temp_path)

                # process_id ve timestamp ekle/güncelle
                if "process_id" not in result:
                    result["process_id"] = process_id
                if "timestamp" not in result:
                    result["timestamp"] = timestamp

                # Kaynak bilgisi ekle
                result["source_type"] = "bytes"

            finally:
                # Geçici dosyayı temizle (her durumda)
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception as cleanup_error:
                        print(f"Geçici dosya temizleme hatası: {str(cleanup_error)}")

            return result
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Byte işleme hatası: {str(e)}\n{error_details}")

            # Clean up temporary directories even if an error occurs
            if hasattr(self, 'use_temp_dirs') and self.use_temp_dirs:
                self.cleanup_temp_dirs()

            return {
                "status": "error",
                "message": f"Byte işleme hatası: {str(e)}",
                "error_details": error_details,
                "timestamp": timestamp,
                "process_id": process_id,
                "source_type": "bytes",
                "results": []
            }

    def process_base64_image(self, base64_string, filename=None):
        """Base64 kodlu görüntüyü işle - API için gerekli"""
        timestamp = int(time.time())
        process_id = f"process_{timestamp}_{hash(str(base64_string)[:100]) % 10000}"

        # Girdi doğrulama
        if not base64_string:
            return {
                "status": "error",
                "message": "Geçersiz base64 verisi",
                "error_details": "base64_string parametresi boş olamaz",
                "timestamp": timestamp,
                "process_id": process_id,
                "source_type": "base64",
                "results": []
            }

        try:
            # Base64 string'i decode et
            if "base64," in base64_string:
                # Eğer "data:image/jpeg;base64," gibi bir prefix varsa kaldır
                base64_string = base64_string.split("base64,")[1]

            try:
                image_bytes = base64.b64decode(base64_string)
            except Exception as decode_error:
                # Clean up temporary directories if an error occurs
                if hasattr(self, 'use_temp_dirs') and self.use_temp_dirs:
                    self.cleanup_temp_dirs()
                return {
                    "status": "error",
                    "message": f"Base64 decode hatası: {str(decode_error)}",
                    "error_details": traceback.format_exc(),
                    "timestamp": timestamp,
                    "process_id": process_id,
                    "source_type": "base64",
                    "results": []
                }

            # Görüntü formatını doğrula
            try:
                img = Image.open(io.BytesIO(image_bytes))
                # Eğer filename belirtilmemişse, formatı kullan
                if filename is None:
                    filename = f"upload_{timestamp}.{img.format.lower() if img.format else 'jpg'}"
            except Exception as img_error:
                # Clean up temporary directories if an error occurs
                if hasattr(self, 'use_temp_dirs') and self.use_temp_dirs:
                    self.cleanup_temp_dirs()
                return {
                    "status": "error",
                    "message": f"Geçersiz görüntü formatı: {str(img_error)}",
                    "error_details": traceback.format_exc(),
                    "timestamp": timestamp,
                    "process_id": process_id,
                    "source_type": "base64",
                    "results": []
                }

            # Byte array olarak işle
            result = self.process_image_bytes(image_bytes, filename)

            # Kaynak bilgisini güncelle
            result["source_type"] = "base64"

            return result
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Base64 işleme hatası: {str(e)}\n{error_details}")

            # Clean up temporary directories if an error occurs
            if hasattr(self, 'use_temp_dirs') and self.use_temp_dirs:
                self.cleanup_temp_dirs()

            return {
                "status": "error",
                "message": f"Base64 işleme hatası: {str(e)}",
                "error_details": error_details,
                "timestamp": timestamp,
                "process_id": process_id,
                "source_type": "base64",
                "results": []
            }


# Komut satırından çağrıldığında
if __name__ == "__main__":
    processor = InvoiceProcessor()

    if len(sys.argv) > 1:
        # Tek bir dosyayı işle
        image_path = sys.argv[1]
        if os.path.exists(image_path):
            result = processor.process_image(image_path)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Hata: Dosya bulunamadı: {image_path}")
    else:
        # Orijinal işlevsellik - tüm test klasörünü işle
        from yolo_crop_and_ocr import main as process_all

        process_all()
