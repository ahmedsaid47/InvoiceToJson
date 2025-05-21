import torch
from PIL import Image
from transformers import DonutProcessor, VisionEncoderDecoderModel, utils as hf_utils
import logging, warnings, contextlib, io

hf_utils.logging.set_verbosity_error()
logging.getLogger("transformers").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

device = "cuda" if torch.cuda.is_available() else "cpu"
local_model_path = "./donut_cord_v2"  # Donut model klasörünü doğru göster!

TASK_TOKEN = "<s_cord-v2>"

with contextlib.redirect_stderr(io.StringIO()):
    processor = DonutProcessor.from_pretrained(local_model_path)
    model = VisionEncoderDecoderModel.from_pretrained(local_model_path).to(device).eval()

@torch.no_grad()
def img2json(img_path, max_len=512):
    img = Image.open(img_path).convert("RGB")
    pixel_values = processor(img, return_tensors="pt").pixel_values.to(device)
    start_ids = processor.tokenizer(TASK_TOKEN, add_special_tokens=False,
                                    return_tensors="pt").input_ids.to(device)
    out_ids = model.generate(pixel_values, decoder_input_ids=start_ids,
                             max_length=max_len, early_stopping=True)
    return processor.batch_decode(out_ids, skip_special_tokens=True)[0].strip()
