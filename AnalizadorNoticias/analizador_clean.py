# Analizador de Noticias · Lux Vinculum
# Versión limpia y funcional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import requests
import os
import sys
from datetime import datetime
import threading
import io
import re

# ====================================================
# CONFIGURAR TESSERACT
# ====================================================

try:
    import fitz  # pymupdf
    import pytesseract
    from PIL import Image
    
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    print("✅ Dependencias cargadas correctamente")
except ImportError as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# ====================================================
# CONFIGURACIÓN API
# ====================================================

SERPER_KEY = "1d58d52768b9534c6c867e6c4600f372e73ddeec"
DEEPSEEK_KEY = "sk-23515b29bff54c93b1e6ad4479408b41"

# ====================================================
# DETECCIÓN DE PERIÓDICO Y COLUMNISTA
# ====================================================

def detectar_periodico(texto):
    periodicos = [
        ("EL UNIVERSAL", ["el universal", "universal"]),
        ("MILENIO", ["milenio", "mileno"]),
        ("La Jornada", ["jornada", "la jornada"]),
        ("EL ECONOMISTA", ["economista", "el economista"]),
        ("El Sol de México", ["sol de méxico", "el sol"]),
        ("CRÓNICA", ["crónica", "cronica"]),
        ("EL HERALDO DE MÉXICO", ["heraldo", "el heraldo"]),
        ("ContraRéplica", ["contrareplica", "contra réplica"]),
        ("Reforma", ["reforma"]),
        ("El Financiero", ["financiero", "el financiero"]),
        ("Excelsior", ["excelsior"]),
    ]
    
    texto_lower = texto.lower()
    for nombre, patrones in periodicos:
        for patron in patrones:
            if patron in texto_lower:
                return nombre
    return "No identificado"

def detectar_columnista(texto):
    patrones = [
        r"Por\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+)\s+escribe",
        r"Columna\s+de\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+)\s+opina",
    ]
    
    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            return match.group(1)
    
    columnistas_conocidos = [
        "Carlos Loret", "Jorge Ramos", "Denise Maerker",
        "Pedro Ferriz", "Raymundo Riva Palacio", "Joaquín López-Dóriga",
        "Ciro Gómez Leyva", "Yuriria Sierra", "Héctor Aguilar Camín"
    ]
    
    for col in columnistas_conocidos:
        if col.lower() in texto.lower():
            return col
    
    return "No identificado"

def extraer_seccion(texto):
    secciones = [
        ("Política", ["política", "politica"]),
        ("Economía", ["economía", "economia", "negocios"]),
        ("Nacional", ["nacional"]),
        ("Internacional", ["internacional"]),
        ("Deportes", ["deportes"]),
        ("Cultura", ["cultura"]),
    ]
    
    texto_lower = texto.lower()
    for nombre, patrones in secciones:
        for patron in patrones:
            if patron in texto_lower:
                return nombre
    return "No identificado"

# ====================================================
# FUNCIÓN OCR CON DETECCIÓN
# ====================================================

def extraer_texto_desde_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        texto_completo = ""
        total_paginas = len(doc)
        metadatos_por_pagina = []
        
        for i, page in enumerate(doc):
            print(f"📄 Procesando página {i+1}/{total_paginas}...")
            
            pix = page.get_pixmap(dpi=200)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            texto_pagina = pytesseract.image_to_string(img, lang='spa+eng')
            
            periodico = detectar_periodico(texto_pagina)
            columnista = detectar_columnista(texto_pagina)
            seccion = extraer_seccion(texto_pagina)
            
            metadatos_por_pagina.append({
                "pagina": i+1,
                "periodico": periodico,
                "columnista": columnista,
                "seccion": seccion
            })
            
            texto_completo += f"--- Página {i+1} ---\n"
            texto_completo += f"📰 Periódico: {periodico}\n"
            if columnista != "No identificado":
                texto_completo += f"✍️ Columnista: {columnista}\n"
            if seccion != "No identificado":
                texto_completo += f"📂 Sección: {seccion}\n"
            texto_completo += f"{texto_pagina}\n\n"
        
        doc.close()
        return texto_completo, None, metadatos_por_pagina
    except Exception as e:
        return None, f"❌ Error en OCR: {str(e)}", None

# ====================================================
# FUNCIONES DE ANÁLISIS
# ====================================================

def buscar_en_serper(query):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": 10}
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def extraer_titulares(texto):
    lineas = texto.split('\n')
    titulares = []
    for linea in lineas:
        linea = linea.strip()
        if len(linea) > 20 and linea[0].isupper():
            if not linea.startswith('--- Página') and not linea.startswith('📰') and not linea.startswith('✍️') and not linea.startswith('📂'):
                titulares.append(linea)
    return titulares[:30]

def analizar_titular(titular):
    resultados = buscar_en_serper(titular)
    if "error" in resultados:
        return {"titular": titular, "error": resultados["error"], "eco": 0, "nivel": "❌ Error", "fuentes": []}
    
    organic = resultados.get("organic", [])
    total = len(organic)
    
    if total >= 10:
        nivel = "🔵 ALTO"
    elif total >= 5:
        nivel = "🟡 MEDIO"
    elif total >= 2:
        nivel = "🟠 BAJO"
    else:
        nivel = "🔴 MUY BAJO"
    
    fuentes = [{"titulo": item.get("title", "Sin título"), "link": item.get("link", "#")} for item in organic[:5]]
    return {"titular": titular, "error": None, "eco": total, "nivel": nivel, "fuentes": fuentes}

def generar_contexto(titulares_importantes):
    if not titulares_importantes:
        return "No hay noticias importantes para analizar."
    
    prompt = f"""
Eres analista de medios. Resume estas noticias en un contexto general coherente.

Noticias:
{chr(10).join([f"- {t['titular']}" for t in titulares_importantes])}

Genera un resumen ejecutivo que identifique el tema central y las noticias clave.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 500}
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return f"❌ Error: HTTP {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ====================================================
# INTERFAZ GRÁFICA
# ====================================================

class AnalizadorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador de Noticias · Lux Vinculum")
        self.root.geometry("1200x800")
        self.root.configure(bg="#0a0a12")
        self.texto = ""
        self.resultados = []
        self.metadatos = []
        self.crear_widgets()
    
    def crear_widgets(self):
        titulo = tk.Label(self.root, text="📰 Analizador de Noticias · Lux Vinculum",
                         font=("Arial", 18, "bold"), fg="#C9A84C", bg="#0a0a12")
        titulo.pack(pady=10)
        
        btn_frame = tk.Frame(self.root, bg="#0a0a12")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="📄 Cargar PDF", command=self.cargar_pdf,
                  bg="#C9A84C", fg="#0a0a12", font=("Arial", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📂 Cargar TXT", command=self.cargar_txt,
                  bg="#2a7a5a", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🔍 Analizar", command=self.analizar,
                  bg="#C9A84C", fg="#0a0a12", font=("Arial", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="💾 Guardar Reporte", command=self.guardar_reporte,
                  bg="#2a7a5a", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        self.estado_label = tk.Label(self.root, text="✅ Listo", fg="#2ecc71", bg="#0a0a12", font=("Arial", 10))
        self.estado_label.pack(pady=5)
        
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#0a0a12")
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = tk.Frame(paned, bg="#1a1a2e")
        paned.add(left_frame, width=400)
        tk.Label(left_frame, text="📄 Previsualización", fg="#C9A84C", bg="#1a1a2e").pack(pady=5)
        self.texto_preview = scrolledtext.ScrolledText(left_frame, height=30, bg="#1a1a2e", fg="#e0e0e0")
        self.texto_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = tk.Frame(paned, bg="#1a1a2e")
        paned.add(right_frame, width=700)
        tk.Label(right_frame, text="📊 Resultados", fg="#C9A84C", bg="#1a1a2e").pack(pady=5)
        self.resultados_texto = scrolledtext.ScrolledText(right_frame, height=30, bg="#1a1a2e", fg="#e0e0e0")
        self.resultados_texto.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def cargar_pdf(self):
        archivo = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if not archivo:
            return
        
        self.estado_label.config(text="⏳ Procesando PDF...", fg="#f39c12")
        self.root.update()
        
        def procesar():
            texto, error, metadatos = extraer_texto_desde_pdf(archivo)
            if error:
                self.root.after(0, lambda: self.mostrar_error(error))
                return
            self.texto = texto
            self.metadatos = metadatos
            self.root.after(0, lambda: self.mostrar_texto(texto, archivo))
        
        threading.Thread(target=procesar, daemon=True).start()
    
    def mostrar_error(self, error):
        messagebox.showerror("Error", error)
        self.estado_label.config(text="❌ Error", fg="#e74c3c")
    
    def mostrar_texto(self, texto, archivo):
        self.texto_preview.delete(1.0, tk.END)
        self.texto_preview.insert(tk.END, texto[:3000] + ("\n\n..." if len(texto) > 3000 else ""))
        self.estado_label.config(text=f"✅ PDF procesado: {os.path.basename(archivo)}", fg="#2ecc71")
    
    def cargar_txt(self):
        archivo = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt")])
        if archivo:
            with open(archivo, 'r', encoding='utf-8') as f:
                self.texto = f.read()
            self.texto_preview.delete(1.0, tk.END)
            self.texto_preview.insert(tk.END, self.texto[:3000] + ("\n\n..." if len(self.texto) > 3000 else ""))
            self.estado_label.config(text=f"✅ TXT cargado: {os.path.basename(archivo)}", fg="#2ecc71")
    
    def analizar(self):
        if not self.texto:
            messagebox.showwarning("Sin texto", "Carga un PDF o TXT primero.")
            return
        
        self.estado_label.config(text="⏳ Analizando...", fg="#f39c12")
        self.root.update()
        
        try:
            titulares = extraer_titulares(self.texto)
            self.resultados = []
            for t in titulares:
                analisis = analizar_titular(t)
                if not analisis["error"]:
                    self.resultados.append(analisis)
            
            importantes = sorted([r for r in self.resultados if "ALTO" in r["nivel"] or "MEDIO" in r["nivel"]],
                               key=lambda x: x["eco"], reverse=True)[:6]
            sin_eco = [r for r in self.resultados if r["eco"] <= 1]
            contexto = generar_contexto(importantes)
            
            self.mostrar_resultados(importantes, sin_eco, contexto)
            self.estado_label.config(text=f"✅ Análisis completado", fg="#2ecc71")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.estado_label.config(text="❌ Error", fg="#e74c3c")
    
            def mostrar_resultados(self, importantes, sin_eco, contexto):
        """Muestra los resultados del análisis en la interfaz."""
        self.resultados_texto.delete(1.0, tk.END)

        # Título
        self.resultados_texto.insert(tk.END, "📊 NOTICIAS MÁS IMPORTANTES\n", "titulo")
        self.resultados_texto.insert(tk.END, "═" * 70 + "\n\n", "separador")

        # Contexto
        self.resultados_texto.insert(tk.END, "📌 CONTEXTO GENERAL:\n", "subtitulo")
        self.resultados_texto.insert(tk.END, contexto + "\n\n", "texto")
        self.resultados_texto.insert(tk.END, "═" * 70 + "\n\n", "separador")

        # Noticias con eco
        self.resultados_texto.insert(tk.END, f"📋 NOTICIAS CON ECO (Top {len(importantes)}):\n\n", "subtitulo")
        for i, n in enumerate(importantes, 1):
            self.resultados_texto.insert(tk.END, f"{i}. [{n['nivel']}] {n['titular']}\n", "noticia")
            self.resultados_texto.insert(tk.END, f"   Eco: {n['eco']} resultados\n", "detalle")
            for f in n["fuentes"][:3]:
                self.resultados_texto.insert(tk.END, f"     → {f['titulo']}\n", "fuente")
                self.resultados_texto.insert(tk.END, f"       {f['link']}\n", "link")
            self.resultados_texto.insert(tk.END, "\n", "texto")

        # Noticias sin eco
        if sin_eco:
            self.resultados_texto.insert(tk.END, "═" * 70 + "\n\n", "separador")
            self.resultados_texto.insert(tk.END, "🔇 NOTICIAS SIN ECO (0-1 resultados)\n", "subtitulo")
            self.resultados_texto.insert(tk.END, "═" * 70 + "\n", "separador")
            for n in sin_eco[:10]:
                self.resultados_texto.insert(tk.END, f"• {n['titular']}\n", "sin_eco")
                self.resultados_texto.insert(tk.END, f"   Eco: {n['eco']} resultados\n", "detalle")
                self.resultados_texto.insert(tk.END, "\n", "texto")

            self.resultados_texto.insert(tk.END, "\n⚠️ POSIBLES CAUSAS:\n", "causa")
            self.resultados_texto.insert(tk.END, "   • Error de OCR (caracteres mal interpretados)\n", "causa")
            self.resultados_texto.insert(tk.END, "   • Noticia local sin cobertura nacional\n", "causa")
            self.resultados_texto.insert(tk.END, "   • Posible desinformación o noticia falsa\n", "causa")
            self.resultados_texto.insert(tk.END, "   • Titular demasiado específico\n", "causa")

        # Estilos
        self.resultados_texto.tag_config("titulo", foreground="#C9A84C", font=("Arial", 14, "bold"))
        self.resultados_texto.tag_config("subtitulo", foreground="#2a7a5a", font=("Arial", 12, "bold"))
        self.resultados_texto.tag_config("noticia", foreground="#e0e0e0", font=("Arial", 11, "bold"))
        self.resultados_texto.tag_config("detalle", foreground="#aaaaaa", font=("Arial", 9))
        self.resultados_texto.tag_config("fuente", foreground="#cccccc", font=("Arial", 9))
        self.resultados_texto.tag_config("link", foreground="#666666", font=("Arial", 8))
        self.resultados_texto.tag_config("texto", foreground="#e0e0e0", font=("Arial", 10))
        self.resultados_texto.tag_config("separador", foreground="#444444", font=("Arial", 8))
        self.resultados_texto.tag_config("sin_eco", foreground="#e74c3c", font=("Arial", 10))
        self.resultados_texto.tag_config("causa", foreground="#f39c12", font=("Arial", 9))    def guardar_reporte(self):
        if not self.resultados:
            messagebox.showwarning("Sin resultados", "Primero ejecuta un análisis.")
            return
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"C:/Users/roble/Desktop/reporte_{fecha}.txt"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.resultados_texto.get(1.0, tk.END))
        messagebox.showinfo("Guardado", f"✅ Reporte guardado en:\n{path}")

# ====================================================
# MAIN
# ====================================================

if __name__ == "__main__":
    print("🚀 Iniciando Analizador de Noticias...")
    root = tk.Tk()
    app = AnalizadorGUI(root)
    root.mainloop()






