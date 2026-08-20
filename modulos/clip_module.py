# clip_module.py
# Módulo para análisis de imágenes con CLIP (OpenAI)

import clip
import torch
from PIL import Image

def cargar_modelo():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    return model, preprocess, device

def analizar_imagen(ruta_imagen, texto_referencia):
    model, preprocess, device = cargar_modelo()
    image = preprocess(Image.open(ruta_imagen)).unsqueeze(0).to(device)
    text = clip.tokenize([texto_referencia]).to(device)
    with torch.no_grad():
        logits_per_image, _ = model(image, text)
        prob = logits_per_image.softmax(dim=1).cpu().numpy()
    return prob[0][0]
