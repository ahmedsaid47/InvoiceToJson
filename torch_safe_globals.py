"""
PyTorch safe globals için merkezi sağlayıcı modül.
Bu modül tüm projenin tek bir yerden safe globals kaydı yapmasını sağlar.

Usage:
    from torch_safe_globals import register_safe_globals
    
    # Application startup
    register_safe_globals()
"""
import torch
import torch.serialization
from typing import Dict, Set, Optional, Any, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("torch_safe_globals")

# Kayıt edilmiş global'leri takip eder
_REGISTERED_GLOBALS: Set[str] = set()

# Public API için SAFE_GLOBALS değişkeni
SAFE_GLOBALS: Set[str] = _REGISTERED_GLOBALS

def register_safe_globals() -> bool:
    """
    PyTorch güvenli globals kaydı yapar.
    Ultralytics modelleri için gerekli sınıfları güvenli hale getirir.

    Returns:
        bool: Kayıt yapıldıysa True, zaten yapılmışsa False
    """
    global _REGISTERED_GLOBALS
    
    # PyTorch sürümünü kontrol et
    try:
        torch_version = torch.__version__
        logger.info(f"PyTorch version: {torch_version}")
        
        # PyTorch 2.2+ gerekli
        major, minor = map(int, torch_version.split('.')[:2])
        if major < 2 or (major == 2 and minor < 2):
            logger.warning(f"PyTorch version {torch_version} is less than 2.2.0. "
                          "Safe globals may not work correctly.")
    except Exception as e:
        logger.error(f"Failed to check PyTorch version: {str(e)}")

    # add_safe_globals fonksiyonunu kontrol et
    add_safe_fn = getattr(torch.serialization, "add_safe_globals", None)
    if not callable(add_safe_fn):
        logger.warning("torch.serialization.add_safe_globals not found; "
                      "could not add safe globals.")
        return False

    # Ultralytics sınıflarını güvenli hale getir
    try:
        # Önce gerekli modülleri import et
        from ultralytics.nn.tasks import DetectionModel
        from ultralytics.nn.modules import Conv, C2f, SPPF, Bottleneck
        
        # Güvenli globals listesi
        safe_classes = [
            DetectionModel,
            Conv,
            C2f, 
            SPPF,
            Bottleneck
        ]
        
        # Sadece henüz kaydedilmemiş olanları filtrele
        new_classes = []
        for cls in safe_classes:
            class_path = f"{cls.__module__}.{cls.__name__}"
            if class_path not in _REGISTERED_GLOBALS:
                new_classes.append(cls)
                _REGISTERED_GLOBALS.add(class_path)
        
        if not new_classes:
            logger.info("All safe globals are already registered.")
            return False
            
        # Yeni globals'leri kaydet
        add_safe_fn(new_classes)
        
        logger.info(f"Successfully registered {len(new_classes)} safe globals: {[cls.__name__ for cls in new_classes]}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to register safe globals: {str(e)}")
        # Fallback: Ultralytics'i tamamen güvenli hale getir
        try:
            import ultralytics
            add_safe_fn([ultralytics])
            logger.info("Added ultralytics module as safe global (fallback)")
            return True
        except Exception as fallback_e:
            logger.error(f"Fallback registration also failed: {str(fallback_e)}")
            return False

def get_registered_globals() -> Set[str]:
    """
    Returns the set of registered global class paths.
    
    Returns:
        Set[str]: Set of registered global class paths
    """
    return _REGISTERED_GLOBALS.copy()

def is_safe_globals_available() -> bool:
    """
    Checks if the PyTorch version supports safe globals.
    
    Returns:
        bool: True if safe globals are supported, False otherwise
    """
    return callable(getattr(torch.serialization, "add_safe_globals", None))

def disable_weights_only_loading():
    """
    PyTorch weights_only yüklemesini devre dışı bırakır.
    Bu geçici bir çözümdür ve güvenlik riskli olabilir.
    """
    try:
        # PyTorch'un default weights_only ayarını değiştir
        torch.serialization.set_default_load_endianness(torch.serialization.LoadEndianness.NATIVE)
        logger.info("Disabled PyTorch weights_only loading")
        return True
    except Exception as e:
        logger.error(f"Failed to disable weights_only loading: {str(e)}")
        return False

# Otomatik olarak import edildiğinde globals'leri kaydet
if __name__ != "__main__":
    register_safe_globals()