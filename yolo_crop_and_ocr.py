import os
import cv2
import logging
import traceback
from pathlib import Path
from ultralytics import YOLO
from donut_ocr import img2json
from docgeonet_correct import correct_with_docgeonet

# Import the centralized safe globals module
from torch_safe_globals import register_safe_globals

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("yolo_crop_and_ocr")

# ------------- Parametreler -------------
YOLO_MODEL_PATH = "best.pt"
DONUT_MODEL_PATH = "./donut_cord_v2"
TEST_IMAGES_DIR = "test_images"
CROP_DIR = "cropped"
REC_DIR = "rectified"  # DocGeoNet'ten çıkan düzeltmeler
DOCGEONET_DIR = "DocGeoNet"
CONF_THRESHOLD = 0.20
IMGSZ = 640
# --------------------------------------

# Register safe globals before loading any models
# This is automatically done when importing the module, but we call it again to be sure
register_safe_globals()
logger.info("PyTorch safe globals registered")

# Klasörleri oluştur
os.makedirs(CROP_DIR, exist_ok=True)
os.makedirs(REC_DIR, exist_ok=True)

# YOLOv8 modeli yükle
try:
    yolo_model = YOLO(YOLO_MODEL_PATH)
    device = 'cuda' if yolo_model.device.type == 'cuda' else 'cpu'
    logger.info(f"YOLOv8 loaded: {YOLO_MODEL_PATH} | Device: {device}")
except Exception as e:
    logger.error(f"Failed to load YOLO model: {str(e)}")
    logger.error(traceback.format_exc())
    raise


def clamp(v, lo, hi): return max(lo, min(v, hi))


def crop_invoices_from_img(img_path, crop_dir, conf_th=0.20, imgsz=640):
    try:
        results = yolo_model.predict(img_path, conf=conf_th, imgsz=imgsz, device=device, save=False, verbose=False)[0]
        n = len(results.boxes)
        logger.info(f"{Path(img_path).name} - {n} invoices found")
        orig = results.orig_img.copy()
        H, W = orig.shape[:2]
        crop_paths = []

        for idx, b in enumerate(results.boxes.xyxy.cpu().numpy().astype(int)):
            x1, y1, x2, y2 = [clamp(x, 0, W - 1 if i % 2 == 0 else H - 1) for i, x in enumerate([b[0], b[1], b[2], b[3]])]
            crop = orig[y1:y2, x1:x2]
            cpath = Path(crop_dir) / f"crop_{Path(img_path).stem}_{idx:02d}.jpg"
            cv2.imwrite(str(cpath), crop)
            crop_paths.append(str(cpath))
            logger.debug(f"Cropped invoice {idx+1}/{n} saved to {cpath}")
        return crop_paths
    except Exception as e:
        logger.error(f"Error cropping invoices from {img_path}: {str(e)}")
        logger.error(traceback.format_exc())
        return []


def main():
    try:
        logger.info("Starting invoice processing")
        img_files = sorted(
            [str(p) for p in Path(TEST_IMAGES_DIR).glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")])
        logger.info(f"Found {len(img_files)} image files to process")

        all_jsons = []
        for img_path in img_files:
            logger.info(f"Processing image: {img_path}")
            crop_paths = crop_invoices_from_img(img_path, CROP_DIR, CONF_THRESHOLD, IMGSZ)
            logger.info(f"Created {len(crop_paths)} crops from {img_path}")

        # Tüm kırpmalar bitince topluca düzeltme yapıyoruz
        logger.info("Starting document rectification with DocGeoNet")
        rectified_imgs = correct_with_docgeonet(DOCGEONET_DIR, CROP_DIR, REC_DIR)
        logger.info(f"Rectified {len(rectified_imgs)} images")

        success_count = 0
        error_count = 0

        for rec_img_path in rectified_imgs:
            logger.info(f"Starting OCR for: {rec_img_path}")
            try:
                ocr_result = img2json(rec_img_path)
                logger.info(f"OCR successful for: {rec_img_path}")
                logger.debug(f"JSON Output:\n{ocr_result}")
                all_jsons.append((rec_img_path, ocr_result))
                success_count += 1
            except Exception as e:
                logger.error(f"OCR error for {rec_img_path}: {str(e)}")
                logger.error(traceback.format_exc())
                error_count += 1

        logger.info(f"All processing completed. Total: {len(all_jsons)} invoices processed successfully, {error_count} errors.")
        return all_jsons
    except Exception as e:
        logger.error(f"Error in main processing: {str(e)}")
        logger.error(traceback.format_exc())
        return []


if __name__ == "__main__":
    # InvoiceProcessor sınıfını kullanarak da çağırılabilir
    # from invoice_processor import InvoiceProcessor
    # processor = InvoiceProcessor()
    # for img_path in Path(TEST_IMAGES_DIR).glob("*.[jp][pn]g"):
    #     processor.process_image(str(img_path))

    # Veya doğrudan orijinal işlevselliği çalıştır
    main()
