import subprocess, sys, shutil, os, time
from pathlib import Path
import threading

# Thread-local storage to prevent race conditions when multiple threads call the function
thread_local = threading.local()

def correct_with_docgeonet(docgeonet_dir, crops_dir, rec_dir):
    """
    Correct document geometry using DocGeoNet.
    
    Args:
        docgeonet_dir: Path to DocGeoNet directory
        crops_dir: Directory containing cropped images
        rec_dir: Directory to save rectified images
        
    Returns:
        List of paths to rectified images
    """
    # Use thread-local storage to generate unique directory names
    if not hasattr(thread_local, 'counter'):
        thread_local.counter = 0
    thread_local.counter += 1
    
    # Generate unique directory names using timestamp and thread counter
    timestamp = int(time.time())
    thread_id = threading.get_ident()
    unique_suffix = f"{timestamp}_{thread_id}_{thread_local.counter}"
    
    docgeonet_dir = Path(docgeonet_dir).resolve()  # mutlak yol
    DG_DIST = docgeonet_dir / f"distorted_{unique_suffix}"
    DG_REC = docgeonet_dir / f"rec_{unique_suffix}"

    try:
        # 1) Klasör oluştur (temizleme yerine benzersiz klasörler kullan)
        for p in (DG_DIST, DG_REC):
            p.mkdir(parents=True, exist_ok=True)

        # 2) Crop'ları kopyala
        for cimg in Path(crops_dir).glob("*"):
            shutil.copy(cimg, DG_DIST / cimg.name)

        # 3) DocGeoNet'i çağır
        cmd = [
            sys.executable,
            "inference.py",
            "--seg_model_path", str(docgeonet_dir / "model_pretrained" / "preprocess.pth"),
            "--rec_model_path", str(docgeonet_dir / "model_pretrained" / "DocGeoNet.pth"),
            "--distorrted_path", str(DG_DIST),
            "--save_path", str(DG_REC),
        ]
        subprocess.run(cmd, cwd=docgeonet_dir, check=True)

        # 4) Çıktıları kopyala
        rec_dir = Path(rec_dir)
        rec_dir.mkdir(exist_ok=True, parents=True)
        rec_imgs = []
        for rimg in DG_REC.glob("*_rec.png"):
            shutil.copy(rimg, rec_dir / rimg.name)
            rec_imgs.append(str(rec_dir / rimg.name))
        print(f"{len(rec_imgs)} görüntü düzeltildi ➜ {rec_dir}")
        return sorted(rec_imgs)
    
    finally:
        # 5) Geçici klasörleri temizle
        for p in (DG_DIST, DG_REC):
            if p.exists():
                shutil.rmtree(p)