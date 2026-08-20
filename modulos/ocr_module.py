# ocr_module.py
# Módulo para procesar imágenes con OCR (Tesseract)

import pytesseract
from PIL import Image

def extraer_texto(ruta_imagen):
    try:
        img = Image.open(ruta_imagen)
        texto = pytesseract.image_to_string(img, lang='spa')
        return texto.strip()
    except Exception as e:
        return f"Error OCR: {e}"
