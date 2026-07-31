# Versión con pymupdf (no requiere Poppler)
# Analizador de Noticias · Lux Vinculum

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import requests
import os
import sys
from datetime import datetime

# ====================================================
# VERIFICAR DEPENDENCIAS
# ====================================================

DEPENDENCIAS_OK = True
try:
    import matplotlib
    import matplotlib.pyplot as plt
except ImportError:
    DEPENDENCIAS_OK = False
    print("⚠️ matplotlib no instalado. Algunas funciones no estarán disponibles.")

try:
    from wordcloud import WordCloud
except ImportError:
    DEPENDENCIAS_OK = False
    print("⚠️ wordcloud no instalado. Algunas funciones no estarán disponibles.")

try:
    from fpdf import FPDF
except ImportError:
    DEPENDENCIAS_OK = False
    print("⚠️ fpdf no instalado. Algunas funciones no estarán disponibles.")

# ====================================================
# OCR CON PYMUPDF (ALTERNATIVA - NO REQUIERE POPPLER)
# ====================================================

OCR_DISPONIBLE = False
try:
    import fitz  # pymupdf
    OCR_DISPONIBLE = True
except ImportError:
    print("⚠️ pymupdf no instalado. Ejecuta: pip install pymupdf")

def extraer_texto_desde_pdf(pdf_path):
    if not OCR_DISPONIBLE:
        return None, "❌ pymupdf no disponible. Instala: pip install pymupdf"
    
    try:
        doc = fitz.open(pdf_path)
        texto_completo = ""
        for i, page in enumerate(doc):
            texto_completo += f"--- Página {i+1} ---\n{page.get_text()}\n\n"
        doc.close()
        return texto_completo, None
    except Exception as e:
        return None, f"❌ Error al leer PDF: {str(e)}"

# ====================================================
# CONFIGURACIÓN API
# ====================================================

SERPER_KEY = "1d58d52768b9534c6c867e6c4600f372e73ddeec"
DEEPSEEK_KEY = "sk-23515b29bff54c93b1e6ad4479408b41"

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
            if not linea.startswith('--- Página') and not linea.isupper():
                titulares.append(linea)
    return titulares[:30]

def analizar_titular(titular):
    resultados = buscar_en_serper(titular)
    if "error" in resultados:
        return {"titular": titular, "error": resultados["error"], "eco": 0, "nivel": "❌ Error", "fuentes": []}
    
    organic = resultados.get("organic", [])
    total = len(organic)
    
    if total >= 10:
        nivel, color = "🔵 ALTO", "green"
    elif total >= 5:
        nivel, color = "🟡 MEDIO", "yellow"
    elif total >= 2:
        nivel, color = "🟠 BAJO", "orange"
    else:
        nivel, color = "🔴 MUY BAJO", "red"
    
    fuentes = [{"titulo": item.get("title", "Sin título"), "link": item.get("link", "#")} for item in organic[:5]]
    return {"titular": titular, "error": None, "eco": total, "nivel": nivel, "color": color, "fuentes": fuentes}

def generar_contexto(titulares_importantes):
    if not titulares_importantes:
        return "No hay noticias importantes para analizar."
    
    prompt = f"""
Eres analista de medios especializado en política mexicana. Resume estas noticias en un contexto general coherente.

Noticias:
{chr(10).join([t["titular"] for t in titulares_importantes])}

Genera un resumen ejecutivo que:
1. Identifique el tema central (político, económico o social).
2. Mencione las noticias clave.
3. Destaque coincidencias o contradicciones entre fuentes.
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
# FUNCIONES PARA GRÁFICOS E IMÁGENES
# ====================================================

def generar_grafico_eco(resultados, output_path):
    """Genera un gráfico de barras con el nivel de eco."""
    try:
        titulares = [r["titular"][:30] + "..." if len(r["titular"]) > 30 else r["titular"] for r in resultados[:10]]
        ecos = [r["eco"] for r in resultados[:10]]
        colores = ['#2ecc71' if e >= 10 else '#f1c40f' if e >= 5 else '#e67e22' if e >= 2 else '#e74c3c' for e in ecos]
        
        plt.figure(figsize=(10, 6))
        plt.barh(titulares, ecos, color=colores)
        plt.xlabel("Número de resultados (eco)")
        plt.title("Nivel de eco de las noticias")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path
    except Exception as e:
        print(f"⚠️ Error al generar gráfico: {e}")
        return None

def generar_nube_palabras(texto, output_path):
    """Genera una nube de palabras."""
    try:
        wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='viridis').generate(texto)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path
    except Exception as e:
        print(f"⚠️ Error al generar nube: {e}")
        return None

# ====================================================
# INTERFAZ GRÁFICA
# ====================================================

class AnalizadorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador de Noticias · Lux Vinculum")
        self.root.geometry("1250x900")
        self.root.configure(bg="#0a0a12")
        self.texto = ""
        self.resultados = []
        self.crear_widgets()
    
    def crear_widgets(self):
        titulo = tk.Label(self.root, text="📰 Analizador de Noticias · Lux Vinculum",
                         font=("Playfair Display", 18, "bold"), fg="#C9A84C", bg="#0a0a12")
        titulo.pack(pady=10)
        
        btn_frame = tk.Frame(self.root, bg="#0a0a12")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="📄 Cargar PDF (OCR)", command=self.cargar_pdf,
                  bg="#C9A84C", fg="#0a0a12", font=("Inter", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📂 Cargar TXT", command=self.cargar_archivo,
                  bg="#2a7a5a", fg="white", font=("Inter", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🔍 Analizar", command=self.ejecutar_analisis,
                  bg="#C9A84C", fg="#0a0a12", font=("Inter", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="💾 Guardar Reporte", command=self.guardar_reporte,
                  bg="#2a7a5a", fg="white", font=("Inter", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📊 Reporte con Imágenes", command=self.guardar_reporte_con_imagenes,
                  bg="#C9A84C", fg="#0a0a12", font=("Inter", 10, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        self.estado_label = tk.Label(self.root, text="✅ Listo", fg="#2ecc71", bg="#0a0a12", font=("Inter", 9))
        self.estado_label.pack(pady=5)
        
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#0a0a12")
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = tk.Frame(paned, bg="#1a1a2e")
        paned.add(left_frame, width=400)
        tk.Label(left_frame, text="📄 Previsualización", fg="#C9A84C", bg="#1a1a2e", font=("Inter", 10, "bold")).pack(pady=5)
        self.texto_preview = scrolledtext.ScrolledText(left_frame, height=30, bg="#1a1a2e", fg="#e0e0e0",
                                                       insertbackground="#C9A84C", font=("Courier", 9))
        self.texto_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = tk.Frame(paned, bg="#1a1a2e")
        paned.add(right_frame, width=750)
        tk.Label(right_frame, text="📊 Resultados del Análisis", fg="#C9A84C", bg="#1a1a2e", font=("Inter", 10, "bold")).pack(pady=5)
        self.resultados_texto = scrolledtext.ScrolledText(right_frame, height=30, bg="#1a1a2e", fg="#e0e0e0",
                                                          insertbackground="#C9A84C", font=("Courier", 9))
        self.resultados_texto.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
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
        self.texto_preview.delete(1.0, tk.END)
        self.texto_preview.insert(tk.END, texto[:2000] + ("\n\n..." if len(texto) > 2000 else ""))
        self.estado_label.config(text=f"✅ PDF procesado: {os.path.basename(archivo)}", fg="#2ecc71")
    
    def cargar_archivo(self):
        archivo = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt")])
        if archivo:
            with open(archivo, 'r', encoding='utf-8') as f:
                self.texto = f.read()
            self.texto_preview.delete(1.0, tk.END)
            self.texto_preview.insert(tk.END, self.texto[:2000] + ("\n\n..." if len(self.texto) > 2000 else ""))
            self.estado_label.config(text=f"✅ TXT cargado: {os.path.basename(archivo)}", fg="#2ecc71")
    
    def ejecutar_analisis(self):
        if not self.texto:
            messagebox.showwarning("Sin texto", "Carga un PDF o TXT primero.")
            return
        
        self.estado_label.config(text="⏳ Analizando... (Serper.dev)", fg="#f39c12")
        self.root.update()
        
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
        
        self.resultados_texto.delete(1.0, tk.END)
        
        # Título
        self.resultados_texto.insert(tk.END, "📊 NOTICIAS MÁS IMPORTANTES\n", "titulo")
        self.resultados_texto.insert(tk.END, "═" * 70 + "\n\n", "separador")
        
        # Contexto
        self.resultados_texto.insert(tk.END, "📌 CONTEXTO GENERAL:\n", "subtitulo")
        self.resultados_texto.insert(tk.END, contexto + "\n\n", "texto")
        self.resultados_texto.insert(tk.END, "═" * 70 + "\n\n", "separador")
        
        # Noticias destacadas
        self.resultados_texto.insert(tk.END, f"📋 NOTICIAS DESTACADAS (Top {len(importantes)}):\n\n", "subtitulo")
        for i, n in enumerate(importantes, 1):
            self.resultados_texto.insert(tk.END, f"{i}. [{n['nivel']}] {n['titular']}\n", "noticia")
            self.resultados_texto.insert(tk.END, f"   Eco: {n['eco']} resultados\n", "detalle")
            self.resultados_texto.insert(tk.END, "   Fuentes:\n", "detalle")
            for f in n["fuentes"][:3]:
                self.resultados_texto.insert(tk.END, f"     → {f['titulo']}\n", "fuente")
                self.resultados_texto.insert(tk.END, f"       {f['link']}\n", "link")
            self.resultados_texto.insert(tk.END, "\n", "texto")
        
        # Noticias sin eco
        if sin_eco:
            self.resultados_texto.insert(tk.END, "═" * 70 + "\n\n", "separador")
            self.resultados_texto.insert(tk.END, "🔇 NOTICIAS SIN ECO\n", "subtitulo")
            self.resultados_texto.insert(tk.END, "═" * 70 + "\n", "separador")
            for n in sin_eco[:10]:
                self.resultados_texto.insert(tk.END, f"• {n['titular']}\n", "sin_eco")
                self.resultados_texto.insert(tk.END, f"   Eco: {n['eco']} resultados\n", "detalle")
                if n.get("fuentes"):
                    self.resultados_texto.insert(tk.END, f"   Fuente: {n['fuentes'][0]['titulo'][:60]}\n", "fuente")
                else:
                    self.resultados_texto.insert(tk.END, "   Fuente: Ninguna\n", "fuente")
                self.resultados_texto.insert(tk.END, "\n", "texto")
            
            self.resultados_texto.insert(tk.END, "\n⚠️ POSIBLES CAUSAS:\n", "causa")
            self.resultados_texto.insert(tk.END, "   • Titular demasiado específico para tener eco en la web\n", "causa")
            self.resultados_texto.insert(tk.END, "   • Error de OCR (caracteres mal interpretados)\n", "causa")
            self.resultados_texto.insert(tk.END, "   • Noticia local sin cobertura nacional\n", "causa")
            self.resultados_texto.insert(tk.END, "   • Posible desinformación o noticia falsa\n", "causa")
        
        # Estilos
        self.resultados_texto.tag_config("titulo", foreground="#C9A84C", font=("Playfair Display", 14, "bold"))
        self.resultados_texto.tag_config("subtitulo", foreground="#2a7a5a", font=("Inter", 12, "bold"))
        self.resultados_texto.tag_config("noticia", foreground="#e0e0e0", font=("Inter", 11, "bold"))
        self.resultados_texto.tag_config("detalle", foreground="#aaaaaa", font=("Inter", 9))
        self.resultados_texto.tag_config("fuente", foreground="#cccccc", font=("Inter", 9))
        self.resultados_texto.tag_config("link", foreground="#666666", font=("Inter", 8))
        self.resultados_texto.tag_config("texto", foreground="#e0e0e0", font=("Inter", 10))
        self.resultados_texto.tag_config("separador", foreground="#444444", font=("Inter", 8))
        self.resultados_texto.tag_config("sin_eco", foreground="#e74c3c", font=("Inter", 10))
        self.resultados_texto.tag_config("causa", foreground="#f39c12", font=("Inter", 9))
        
        self.estado_label.config(text=f"✅ Análisis completado ({len(importantes)} importantes, {len(sin_eco)} sin eco)",
                               fg="#2ecc71")
    
    def guardar_reporte(self):
        if not self.resultados:
            messagebox.showwarning("Sin resultados", "Primero ejecuta un análisis.")
            return
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"C:/Users/roble/Desktop/reporte_analisis_{fecha}.txt"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.resultados_texto.get(1.0, tk.END))
        messagebox.showinfo("Guardado", f"✅ Reporte guardado en:\n{path}")
    
    def guardar_reporte_con_imagenes(self):
        if not self.resultados:
            messagebox.showwarning("Sin resultados", "Primero ejecuta un análisis.")
            return
        
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_path = f"C:/Users/roble/Desktop/reporte_{fecha}"
        
        # 1. Guardar TXT
        txt_path = f"{base_path}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(self.resultados_texto.get(1.0, tk.END))
        
        # 2. Generar gráfico de eco
        grafico_path = f"{base_path}_grafico.png"
        generar_grafico_eco(self.resultados, grafico_path)
        
        # 3. Generar nube de palabras
        nube_path = f"{base_path}_nube.png"
        texto_completo = " ".join([r["titular"] for r in self.resultados])
        generar_nube_palabras(texto_completo, nube_path)
        
        mensaje = f"✅ Reporte guardado en:\n{txt_path}\n\n📊 Gráfico: {grafico_path}\n☁️ Nube: {nube_path}"
        messagebox.showinfo("Guardado", mensaje)

# ====================================================
# MAIN
# ====================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalizadorGUI(root)
    root.mainloop()
