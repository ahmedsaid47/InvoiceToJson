from transformers import pipeline
import logging

logger = logging.getLogger("ner_processor")

class NERProcessor:
    """Simple wrapper around a HuggingFace token-classification pipeline."""

    def __init__(self, model_name="akdeniz27/bert-base-turkish-cased-ner", device=None):
        self.model_name = model_name
        try:
            device_index = 0 if device and device.startswith("cuda") else -1
            self.pipeline = pipeline(
                "token-classification",
                model=model_name,
                aggregation_strategy="simple",
                device=device_index,
            )
            logger.info(f"NER model loaded: {model_name} | device_index={device_index}")
        except Exception as e:
            logger.error(f"Failed to load NER model {model_name}: {e}")
            raise

    def extract(self, text: str):
        """Run NER on the given text and return the extracted entities."""
        if not text:
            return []
        try:
            return self.pipeline(text)
        except Exception as e:
            logger.error(f"NER processing error: {e}")
            return []
