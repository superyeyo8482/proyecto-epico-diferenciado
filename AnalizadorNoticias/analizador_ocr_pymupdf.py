# Analizador con pymupdf + OCR para PDF escaneado

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import requests
import os
import sys
from datetime import datetime
import io

# ====================================================
# OCR CON PYMUPDF + TESSERACT
# ====================================================

OCR_DISPONIBLE = False
try:
    import fitz  # pymupdf
    import pytesseract
    from PIL import Image
    OCR_DISPONIBLE = True
except ImportError:
    print("⚠️ Dependencias no instaladas. Ejecuta: pip install pymupdf pytesseract pillow")

def extraer_texto_desde_pdf(pdf_path):
    """Extrae texto de PDF usando pymupdf + OCR para páginas escaneadas."""
    if not OCR_DISPONIBLE:
        return None, "❌ Dependencias no disponibles. Instala: pip install pymupdf pytesseract pillow"
    
    try:
        doc = fitz.open(pdf_path)
        texto_completo = ""
        total_paginas = len(doc)
        
        for i, page in enumerate(doc):
            # Mostrar progreso en consola
            print(f"📄 Procesando página {i+1}/{total_paginas}...")
            
            # Convertir página a imagen (para OCR)
            pix = page.get_pixmap(dpi=200)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Aplicar OCR
            texto_pagina = pytesseract.image_to_string(img, lang='spa+eng')
            texto_completo += f"--- Página {i+1} ---\n{texto_pagina}\n\n"
            
            # Actualizar interfaz (opcional)
            # root.update() si se pasa root como argumento
        
        doc.close()
        return texto_completo, None
    except Exception as e:
        return None, f"❌ Error en OCR: {str(e)}"

# ====================================================
# RESTO DEL CÓDIGO (igual que antes)
# ====================================================

# ... (aquí va el resto del código de la interfaz y análisis)

