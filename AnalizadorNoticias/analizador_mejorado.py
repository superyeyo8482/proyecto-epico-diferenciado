import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import requests
import re
import os
import sys
from datetime import datetime

# ====================================================
# OCR DISPONIBLE?
# ====================================================

OCR_DISPONIBLE = False
try:
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image
    OCR_DISPONIBLE = True
except ImportError:
    pass

# ====================================================
# CONFIGURACIÓN
# ====================================================

API_KEY = 'sk-23515b29bff54c93b1e6ad4479408b41'

# Ruta de Tesseract
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# ====================================================
# FUNCIONES OCR
# ====================================================

def extraer_texto_desde_pdf(pdf_path):
    if not OCR_DISPONIBLE:
        return None, "❌ OCR no disponible. Instala: pip install pdf2image pytesseract pillow"
    try:
        imagenes = convert_from_path(pdf_path, dpi=200)
        texto_completo = ""
        for i, img in enumerate(imagenes):
            texto_pagina = pytesseract.image_to_string(img, lang='spa+eng')
            texto_completo += f"--- Página {i+1} ---\n{texto_pagina}\n\n"
        return texto_completo, None
    except Exception as e:
        return None, f"❌ Error en OCR: {str(e)}"

# ====================================================
# FUNCIONES DEEPSEEK
# ====================================================

def consultar_deepseek(prompt):
    url = 'https://api.deepseek.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.1,
        'max_tokens': 2000
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"ERROR: {response.status_code}"
    except Exception as e:
        return f"ERROR: {e}"

def limpiar_respuesta(respuesta):
    """Limpia la respuesta de DeepSeek para obtener solo JSON."""
    # Eliminar texto antes del primer {
    inicio = respuesta.find('{')
    if inicio == -1:
        return respuesta
    # Eliminar texto después del último }
    fin = respuesta.rfind('}')
    if fin == -1:
        return respuesta[inicio:]
    return respuesta[inicio:fin+1]

def analizar_texto(texto):
    if not texto or len(texto.strip()) < 50:
        return {"error": "El texto está vacío o es demasiado corto"}
    
    # Dividir en fragmentos si es muy largo
    fragmentos = []
    if len(texto) > 6000:
        fragmentos = [texto[i:i+6000] for i in range(0, len(texto), 6000)]
    else:
        fragmentos = [texto]
    
    todas_noticias = []
    for i, fragmento in enumerate(fragmentos):
        prompt = f"""
Eres un analista de medios. Analiza este fragmento de primeras planas.
Fragmento {i+1} de {len(fragmentos)}:

{fragmento}

Devuelve SOLO JSON con esta estructura (si no hay noticias, devuelve arrays vacíos):
{{
    "periodicos_identificados": ["periódico1"],
    "noticias": [
        {{
            "titular": "...",
            "resumen": "...",
            "repeticion": 0-10,
            "coincidencia": 0-10,
            "atipicidad": 0-10,
            "puntuacion": 0-10,
            "indice_distorsion": 0-100,
            "razones_distorsion": ["razón1"]
        }}
    ],
    "sin_eco_web": [],
    "resumen_ejecutivo": "breve resumen",
    "alertas_distorsion": []
}}
"""
        respuesta = consultar_deepseek(prompt)
        respuesta_limpia = limpiar_respuesta(respuesta)
        try:
            datos = json.loads(respuesta_limpia)
            todas_noticias.extend(datos.get("noticias", []))
        except:
            pass
    
    # Consolidar resultados
    resultado = {
        "periodicos_identificados": [],
        "noticias": todas_noticias,
        "top_5": sorted(todas_noticias, key=lambda x: x.get("puntuacion", 0), reverse=True)[:5],
        "sin_eco_web": [],
        "resumen_ejecutivo": f"Se analizaron {len(fragmentos)} fragmentos con {len(todas_noticias)} noticias detectadas.",
        "alertas_distorsion": [n for n in todas_noticias if n.get("indice_distorsion", 0) > 40]
    }
    
    return resultado

# ====================================================
# INTERFAZ
# ====================================================

class AnalizadorNoticias:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador de Noticias · Lux Vinculum")
        self.root.geometry("1150x900")
        self.root.configure(bg="#0a0a12")
        
        self.texto = ""
        self.resultados = None
        self.archivo_actual = ""
        
        # Estilo
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("TNotebook", background="#0a0a12", foreground="#C9A84C")
        estilo.configure("TNotebook.Tab", background="#1a1a2e", foreground="#C9A84C", padding=[10, 5])
        estilo.map("TNotebook.Tab", background=[("selected", "#2a2a3e")])
        
        # Pestañas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tab_analisis = tk.Frame(self.notebook, bg="#0a0a12")
        self.notebook.add(self.tab_analisis, text="📰 Análisis")
        
        self.tab_resultados = tk.Frame(self.notebook, bg="#0a0a12")
        self.notebook.add(self.tab_resultados, text="📊 Resultados")
        
        self.tab_acerca = tk.Frame(self.notebook, bg="#0a0a12")
        self.notebook.add(self.tab_acerca, text="ℹ️ Acerca de")
        
        self.crear_tab_analisis()
        self.crear_tab_resultados()
        self.crear_tab_acerca()
    
    def crear_tab_analisis(self):
        frame = self.tab_analisis
        
        tk.Label(frame, text="📰 Analizador de Noticias Lux Vinculum",
                 font=("Playfair Display", 20, "bold"), fg="#C9A84C", bg="#0a0a12").pack(pady=10)
        
        tk.Label(frame, text="Carga un PDF (con OCR) o un TXT ya extraído",
                 font=("Inter", 10), fg="#aaaaaa", bg="#0a0a12").pack()
        
        btn_frame = tk.Frame(frame, bg="#0a0a12")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="📄 Cargar PDF (OCR)", command=self.cargar_pdf,
                  bg="#C9A84C", fg="#0a0a12", font=("Inter", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📂 Cargar TXT", command=self.cargar_txt,
                  bg="#2a7a5a", fg="white", font=("Inter", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🔍 Analizar", command=self.ejecutar_analisis,
                  bg="#C9A84C", fg="#0a0a12", font=("Inter", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Área de texto
        self.texto_preview = scrolledtext.ScrolledText(frame, height=18, bg="#1a1a2e", fg="#e0e0e0",
                                                       insertbackground="#C9A84C", font=("Courier", 10))
        self.texto_preview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Estado
        self.estado_label = tk.Label(frame, text="✅ Listo", fg="#2ecc71", bg="#0a0a12", font=("Inter", 9))
        self.estado_label.pack(pady=5)
    
    def crear_tab_resultados(self):
        frame = self.tab_resultados
        
        tk.Label(frame, text="📊 Resultados del Análisis",
                 font=("Playfair Display", 16, "bold"), fg="#C9A84C", bg="#0a0a12").pack(pady=10)
        
        self.resultados_texto = scrolledtext.ScrolledText(frame, height=28, bg="#1a1a2e", fg="#e0e0e0",
                                                          insertbackground="#C9A84C", font=("Courier", 10))
        self.resultados_texto.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        btn_frame = tk.Frame(frame, bg="#0a0a12")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="💾 Exportar JSON", command=self.exportar_json,
                  bg="#C9A84C", fg="#0a0a12", font=("Inter", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📄 Exportar TXT", command=self.exportar_txt,
                  bg="#2a7a5a", fg="white", font=("Inter", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📥 Descargar TXT", command=self.descargar_txt,
                  bg="#C9A84C", fg="#0a0a12", font=("Inter", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
    
    def crear_tab_acerca(self):
        frame = self.tab_acerca
        
        info = """
🧠 **Analizador de Noticias · Lux Vinculum**

📋 **Criterios de evaluación:**
1. Repetición en la web (0-10)
2. Coincidencia con áreas de interés (0-10)
3. Atipicidad (0-10)

⚠️ **Índice de Distorsión Estructural (IDE):**
- Contradicciones internas
- Falta de fuentes verificables
- Sesgo direccional claro

🖼️ **OCR integrado:** PDF → Imagen → Texto (Tesseract)

🔐 **Confiabilidad:** Análisis con DeepSeek API

📦 **Créditos disponibles:**  USD en Google Cloud (sin usar)

🌙 **Filosofía:** "La distorsión se esconde en la contradicción."
"""
        lbl = tk.Label(frame, text=info, font=("Inter", 10), fg="#cccccc", bg="#0a0a12", justify=tk.LEFT, wraplength=850)
        lbl.pack(padx=20, pady=20)
    
    # ====================================================
    # FUNCIONES DE CARGA
    # ====================================================
    
    def cargar_pdf(self):
        archivo = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if not archivo:
            return
        
        self.estado_label.config(text="⏳ Procesando PDF con OCR...", fg="#f39c12")
        self.root.update()
        
        texto, error = extraer_texto_desde_pdf(archivo)
        
        if error:
            messagebox.showerror("Error OCR", error)
            self.estado_label.config(text="❌ Error", fg="#e74c3c")
            return
        
        self.texto = texto
        self.archivo_actual = archivo
        self.texto_preview.delete(1.0, tk.END)
        self.texto_preview.insert(tk.END, texto[:5000] + ("\n\n..." if len(texto) > 5000 else ""))
        self.estado_label.config(text=f"✅ PDF procesado: {os.path.basename(archivo)}", fg="#2ecc71")
    
    def cargar_txt(self):
        archivo = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt")])
        if not archivo:
            return
        
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                self.texto = f.read()
            self.archivo_actual = archivo
            self.texto_preview.delete(1.0, tk.END)
            self.texto_preview.insert(tk.END, self.texto[:5000] + ("\n\n..." if len(self.texto) > 5000 else ""))
            self.estado_label.config(text=f"✅ TXT cargado: {os.path.basename(archivo)}", fg="#2ecc71")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")
    
    # ====================================================
    # FUNCIONES DE ANÁLISIS
    # ====================================================
    
    def ejecutar_analisis(self):
        if not self.texto:
            messagebox.showwarning("Sin texto", "Carga un PDF o TXT primero.")
            return
        
        self.estado_label.config(text="⏳ Analizando con DeepSeek...", fg="#f39c12")
        self.root.update()
        
        try:
            self.resultados = analizar_texto(self.texto)
            self.mostrar_resultados()
            self.estado_label.config(text="✅ Análisis completado", fg="#2ecc71")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.estado_label.config(text="❌ Error", fg="#e74c3c")
    
    def mostrar_resultados(self):
        self.resultados_texto.delete(1.0, tk.END)
        
        if "error" in self.resultados:
            self.resultados_texto.insert(tk.END, f"❌ Error:\n{self.resultados.get('respuesta_bruta', self.resultados['error'])}")
            return
        
        # Resumen
        self.resultados_texto.insert(tk.END, "📌 RESUMEN EJECUTIVO\n", "titulo")
        self.resultados_texto.insert(tk.END, f"{'═' * 60}\n", "separador")
        self.resultados_texto.insert(tk.END, f"{self.resultados.get('resumen_ejecutivo', 'Sin resumen')}\n\n", "texto")
        
        # Top 5
        top_5 = self.resultados.get("top_5", [])
        if top_5:
            self.resultados_texto.insert(tk.END, "🏆 TOP 5 NOTICIAS\n", "subtitulo")
            self.resultados_texto.insert(tk.END, f"{'═' * 60}\n", "separador")
            for i, item in enumerate(top_5[:5], 1):
                punt = item.get('puntuacion', 0)
                estrellas = "⭐" * int(punt / 2) if punt >= 2 else "☆"
                self.resultados_texto.insert(tk.END, f"{i}. {item.get('titular', 'Sin título')}\n", "texto")
                self.resultados_texto.insert(tk.END, f"   Puntuación: {punt}/10 {estrellas}\n\n", "detalle")
        
        # Alertas
        alertas = self.resultados.get("alertas_distorsion", [])
        if alertas:
            self.resultados_texto.insert(tk.END, "⚠️ ALERTAS DE DISTORSIÓN\n", "alerta")
            self.resultados_texto.insert(tk.END, f"{'═' * 60}\n", "separador")
            for a in alertas:
                ide = a.get('indice_distorsion', 0)
                color = "🟢" if ide < 30 else "🟡" if ide < 60 else "🔴"
                self.resultados_texto.insert(tk.END, f"{color} {a.get('titular', 'Sin título')}\n", "texto")
                self.resultados_texto.insert(tk.END, f"   IDE: {ide}%\n", "detalle")
                for r in a.get('razones_distorsion', []):
                    self.resultados_texto.insert(tk.END, f"   → {r}\n", "razon")
                self.resultados_texto.insert(tk.END, "\n", "texto")
        
        # Estilos
        self.resultados_texto.tag_config("titulo", foreground="#C9A84C", font=("Playfair Display", 14, "bold"))
        self.resultados_texto.tag_config("subtitulo", foreground="#2a7a5a", font=("Inter", 12, "bold"))
        self.resultados_texto.tag_config("alerta", foreground="#e74c3c", font=("Inter", 12, "bold"))
        self.resultados_texto.tag_config("texto", foreground="#e0e0e0", font=("Inter", 10))
        self.resultados_texto.tag_config("detalle", foreground="#aaaaaa", font=("Inter", 9))
        self.resultados_texto.tag_config("razon", foreground="#f39c12", font=("Inter", 9))
        self.resultados_texto.tag_config("separador", foreground="#444444", font=("Inter", 8))
    
    # ====================================================
    # FUNCIONES DE EXPORTACIÓN
    # ====================================================
    
    def exportar_json(self):
        if not self.resultados:
            messagebox.showwarning("Sin resultados", "Primero ejecuta un análisis.")
            return
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"C:/Users/roble/Desktop/resultados_{fecha}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.resultados, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Exportado", f"✅ JSON guardado en:\n{path}")
    
    def exportar_txt(self):
        if not self.resultados:
            messagebox.showwarning("Sin resultados", "Primero ejecuta un análisis.")
            return
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"C:/Users/roble/Desktop/resultados_{fecha}.txt"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.resultados_texto.get(1.0, tk.END))
        messagebox.showinfo("Exportado", f"✅ TXT guardado en:\n{path}")
    
    def descargar_txt(self):
        """Descarga el TXT actual (el texto original cargado)"""
        if not self.texto:
            messagebox.showwarning("Sin texto", "No hay texto para descargar.")
            return
        
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"C:/Users/roble/Desktop/texto_extraido_{fecha}.txt"
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.texto)
            messagebox.showinfo("Descargado", f"✅ TXT descargado en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{e}")

# ====================================================
# MAIN
# ====================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalizadorNoticias(root)
    root.mainloop()
