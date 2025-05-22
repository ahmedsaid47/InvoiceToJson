import os
import sys
import json
import base64
import requests
from pathlib import Path

# API URL - change this if your API is running on a different host/port
API_URL = "http://localhost:8000"

def test_file_processing():
    """Test processing an image file using the FastAPI endpoint"""
    # Test with a sample image from the test_images directory
    test_images_dir = "test_images"
    if not os.path.exists(test_images_dir) or not os.listdir(test_images_dir):
        print(f"Uyarı: Test görüntüleri bulunamadı: {test_images_dir}")
        return

    test_image = next(Path(test_images_dir).glob("*.[jp][pn]g"), None)
    if not test_image:
        print(f"Uyarı: Test görüntüsü bulunamadı: {test_images_dir}")
        return

    print(f"Test görüntüsü: {test_image}")

    # Send the file to the API
    with open(test_image, "rb") as img_file:
        files = {"file": (test_image.name, img_file, "image/jpeg")}
        response = requests.post(f"{API_URL}/api/process-file", files=files)

    if response.status_code != 200:
        print(f"API Hatası: {response.status_code} - {response.text}")
        return None

    result = response.json()

    print("\n--- Dosya İşleme Sonucu ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result

def test_base64_processing():
    """Test processing a base64-encoded image using the FastAPI endpoint"""
    # Test with a sample image from the test_images directory
    test_images_dir = "test_images"
    if not os.path.exists(test_images_dir) or not os.listdir(test_images_dir):
        print(f"Uyarı: Test görüntüleri bulunamadı: {test_images_dir}")
        return

    test_image = next(Path(test_images_dir).glob("*.[jp][pn]g"), None)
    if not test_image:
        print(f"Uyarı: Test görüntüsü bulunamadı: {test_images_dir}")
        return

    # Görüntüyü base64'e dönüştür
    with open(test_image, "rb") as img_file:
        base64_data = base64.b64encode(img_file.read()).decode('utf-8')

    # Send the base64 data to the API
    print(f"Base64 test görüntüsü: {test_image}")
    payload = {"base64_image": base64_data, "filename": test_image.name}
    response = requests.post(f"{API_URL}/api/process-base64", json=payload)

    if response.status_code != 200:
        print(f"API Hatası: {response.status_code} - {response.text}")
        return None

    result = response.json()

    print("\n--- Base64 İşleme Sonucu ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result

def test_health_check():
    """Test the health check endpoint"""
    print("\n--- Sağlık Kontrolü ---")
    response = requests.get(f"{API_URL}/health")

    if response.status_code != 200:
        print(f"Sağlık Kontrolü Hatası: {response.status_code} - {response.text}")
        return False

    result = response.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return True

def main():
    """Run all tests"""
    print("=== Fatura İşleme API Testi ===")

    # Check if the API is running
    try:
        health_status = test_health_check()
        if not health_status:
            print("API çalışmıyor veya sağlık kontrolü başarısız oldu. Lütfen API'yi başlatın.")
            return
    except requests.exceptions.ConnectionError:
        print(f"API'ye bağlanılamıyor. Lütfen API'nin {API_URL} adresinde çalıştığından emin olun.")
        return

    # Dosya işleme testi
    file_result = test_file_processing()

    # Base64 işleme testi
    base64_result = test_base64_processing()

    # Sonuçları karşılaştır
    if file_result and base64_result:
        print("\n--- Karşılaştırma ---")
        file_status = file_result.get("status")
        base64_status = base64_result.get("status")

        if file_status == base64_status:
            print(f"İki işleme yöntemi de aynı durumu döndürdü: {file_status}")
        else:
            print(f"Farklı durumlar: Dosya={file_status}, Base64={base64_status}")

        file_count = len(file_result.get("results", []))
        base64_count = len(base64_result.get("results", []))

        if file_count == base64_count:
            print(f"İki işleme yöntemi de aynı sayıda sonuç döndürdü: {file_count}")
        else:
            print(f"Farklı sonuç sayıları: Dosya={file_count}, Base64={base64_count}")

    print("\nTest tamamlandı.")

if __name__ == "__main__":
    main()
