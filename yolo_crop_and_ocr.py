import os
import cv2
from pathlib import Path
from ultralytics import YOLO
from donut_ocr import img2json
from docgeonet_correct import correct_with_docgeonet

# ------------- Parametreler -------------
YOLO_MODEL_PATH = "best.pt"
DONUT_MODEL_PATH = "./donut_cord_v2"
TEST_IMAGES_DIR = "test_images"
CROP_DIR = "cropped"
REC_DIR = "rectified"  # DocGeoNet'ten çıkan düzeltmeler
DOCGEONET_DIR = "DocGeoNet"
CONF_THRESHOLD = 0.20
IMGSZ = 640

# Klasörleri oluştur
os.makedirs(CROP_DIR, exist_ok=True)
os.makedirs(REC_DIR, exist_ok=True)

# YOLOv8 modeli yükle
yolo_model = YOLO(YOLO_MODEL_PATH)
device = 'cuda' if yolo_model.device.type == 'cuda' else 'cpu'
print(f"YOLOv8 yüklendi: {YOLO_MODEL_PATH} | Cihaz: {device}")


def clamp(v, lo, hi): return max(lo, min(v, hi))


def crop_invoices_from_img(img_path, crop_dir, conf_th=0.20, imgsz=640):
    results = yolo_model.predict(img_path, conf=conf_th, imgsz=imgsz, device=device, save=False, verbose=False)[0]
    n = len(results.boxes)
    print(f"{Path(img_path).name} - {n} fatura bulundu")
    orig = results.orig_img.copy()
    H, W = orig.shape[:2]
    crop_paths = []

    for idx, b in enumerate(results.boxes.xyxy.cpu().numpy().astype(int)):
        x1, y1, x2, y2 = [clamp(x, 0, W - 1 if i % 2 == 0 else H - 1) for i, x in enumerate([b[0], b[1], b[2], b[3]])]
        crop = orig[y1:y2, x1:x2]
        cpath = Path(crop_dir) / f"crop_{Path(img_path).stem}_{idx:02d}.jpg"
        cv2.imwrite(str(cpath), crop)
        crop_paths.append(str(cpath))
    return crop_paths


def main():
    img_files = sorted(
        [str(p) for p in Path(TEST_IMAGES_DIR).glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")])
    all_jsons = []
    for img_path in img_files:
        crop_paths = crop_invoices_from_img(img_path, CROP_DIR, CONF_THRESHOLD, IMGSZ)
    # Tüm kırpmalar bitince topluca düzeltme yapıyoruz
    rectified_imgs = correct_with_docgeonet(DOCGEONET_DIR, CROP_DIR, REC_DIR)
    for rec_img_path in rectified_imgs:
        print(f"OCR başlatılıyor: {rec_img_path}")
        try:
            ocr_result = img2json(rec_img_path)
            print(f"JSON Çıktı:\n{ocr_result}\n{'-' * 50}")
            all_jsons.append((rec_img_path, ocr_result))
        except Exception as e:
            print(f"Hata: {e}")
    print(f"\nTüm işlemler tamamlandı. Toplam {len(all_jsons)} adet fatura işlendi.")


if __name__ == "__main__":
    # InvoiceProcessor sınıfını kullanarak da çağırılabilir
    # from invoice_processor import InvoiceProcessor
    # processor = InvoiceProcessor()
    # for img_path in Path(TEST_IMAGES_DIR).glob("*.[jp][pn]g"):
    #     processor.process_image(str(img_path))

    # Veya doğrudan orijinal işlevselliği çalıştır
    main()