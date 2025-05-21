import subprocess, sys, shutil
from pathlib import Path

def correct_with_docgeonet(docgeonet_dir, crops_dir, rec_dir):
    docgeonet_dir = Path(docgeonet_dir).resolve()              # mutlak yol
    DG_DIST = docgeonet_dir / "distorted"
    DG_REC  = docgeonet_dir / "rec"

    # 1) Klasör temizle
    for p in (DG_DIST, DG_REC):
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)

    # 2) Crop’ları kopyala
    for cimg in Path(crops_dir).glob("*"):
        shutil.copy(cimg, DG_DIST / cimg.name)

    # 3) DocGeoNet’i çağır
    cmd = [
        sys.executable,
        "inference.py",
        "--seg_model_path", str(docgeonet_dir / "model_pretrained" / "preprocess.pth"),
        "--rec_model_path", str(docgeonet_dir / "model_pretrained" / "DocGeoNet.pth"),
        "--distorrted_path", str(DG_DIST),
        "--save_path",       str(DG_REC),
    ]
    subprocess.run(cmd, cwd=docgeonet_dir, check=True)

    # 4) Çıktıları kopyala
    rec_dir = Path(rec_dir); rec_dir.mkdir(exist_ok=True, parents=True)
    rec_imgs = []
    for rimg in DG_REC.glob("*_rec.png"):
        shutil.copy(rimg, rec_dir / rimg.name)
        rec_imgs.append(str(rec_dir / rimg.name))
    print(f"{len(rec_imgs)} görüntü düzeltildi ➜ {rec_dir}")
    return sorted(rec_imgs)
