"""
İlk kez (ya da ağırlık dosyaları eksikse) çağır:
    python setup_docgeonet.py
Yalnızca eksik parçaları indirir; 2. kez çalıştırmak güvenlidir.
"""
from pathlib import Path
import subprocess, sys, shutil, os

ROOT = Path(__file__).parent.resolve()
DG_DIR = ROOT / "DocGeoNet"
WEIGHTS_ID = "1-OEvGQ36GEF9fI1BnAEHj_aByHorl7C7"   # Google Drive klasör ID
PY_CMD = [sys.executable, "-m", "pip", "install", "-q",
          "gdown", "opencv-python-headless", "einops", "timm"]

def sh(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True, shell=(os.name=="nt"))

def main():
    # 1) Hafif bağımlılıklar ↴
    print("• pip install gdown einops timm …")
    sh(PY_CMD)

    # 2) Repo ↴
    if not DG_DIR.is_dir():
        print("• DocGeoNet repo klonlanıyor…")
        sh(["git", "clone", "--depth", "1",
            "https://github.com/fh2019ustc/DocGeoNet.git", str(DG_DIR)])

    # 3) Ağırlıklar ↴
    mp = DG_DIR / "model_pretrained"
    if not mp.is_dir() or not any(mp.glob("*.pth")):
        print("• Ağırlıklar indiriliyor (≈53 MB)…")
        mp.mkdir(exist_ok=True)
        sh(["gdown", "--folder", "--quiet", WEIGHTS_ID, "-O", str(mp)])

    # 4) Örnek resim ↴  (isteğe bağlı)
    dist = DG_DIR / "distorted"; dist.mkdir(exist_ok=True)
    sample = dist / "sample.jpg"
    if not sample.exists():
        print("• Örnek resim indiriliyor…")
        sh(["wget", "-q",
            "https://raw.githubusercontent.com/fh2019ustc/DocGeoNet/main/distorted/025.jpg",
            "-O", str(sample)])

    print("✓ DocGeoNet hazır →", DG_DIR)

if __name__ == "__main__":
    main()
