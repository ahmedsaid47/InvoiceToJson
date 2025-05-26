"""
PyTorch safe globals için merkezi sağlayıcı modül.
Bu modül tüm projenin tek bir yerden safe globals kaydı yapmasını sağlar.

Usage:
    from torch_safe_globals import register_safe_globals
    
    # Application startup
    register_safe_globals()
"""
import torch.serialization
from ultralytics.nn.tasks import DetectionModel
from typing import Dict, Set, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("torch_safe_globals")

# Kayıt edilmiş global'leri takip eder
_REGISTERED_GLOBALS: Set[str] = set()

# Kaydedilecek tüm sınıflar burada tanımlanır
SAFE_GLOBALS: Dict[str, Any] = {
    "ultralytics.nn.tasks.DetectionModel": DetectionModel
}

def register_safe_globals(globals_dict: Optional[Dict[str, Any]] = None) -> bool:
    """
    Tüm proje için tek bir yerden PyTorch güvenli globals kaydı yapar.
    Her çağrıda yalnızca bir kez kaydeder.

    Args:
        globals_dict: Optional dictionary of safe globals to register.
                     If None, uses the default SAFE_GLOBALS.

    Returns:
        bool: Kayıt yapıldıysa True, zaten yapılmışsa False
    """
    global _REGISTERED_GLOBALS
    
    if globals_dict is None:
        globals_dict = SAFE_GLOBALS
    
    # PyTorch sürümünü kontrol et
    try:
        import torch
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

    # Tüm globals'leri tek seferde kaydet (PyTorch 2.2+ için)
    try:
        # Sadece henüz kaydedilmemiş olanları filtrele
        new_globals = {k: v for k, v in globals_dict.items() if k not in _REGISTERED_GLOBALS}
        
        if not new_globals:
            logger.info("All safe globals are already registered.")
            return False
            
        # Yeni globals'leri kaydet
        add_safe_fn(new_globals)
        
        # Kaydedilenleri takip et
        _REGISTERED_GLOBALS.update(new_globals.keys())
        
        logger.info(f"Successfully registered {len(new_globals)} safe globals: {', '.join(new_globals.keys())}")
        return True
    except Exception as e:
        logger.error(f"Failed to register safe globals: {str(e)}")
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

# Otomatik olarak import edildiğinde globals'leri kaydet
if __name__ != "__main__":
    register_safe_globals()