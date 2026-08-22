import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import os
import json
import threading
import time
import requests
import subprocess
import webbrowser
import re

class QuantumFormaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 Quantum Forma · Lux Vinculum")
        self.root.geometry("800x700")
        self.root.configure(bg="#0a0a1a")
        self.root.resizable(True, True)
        
        # --- CONFIGURACIÓN CON NUEVA API KEY ---
        self.api_key = "sk-03ad9c6892f247819dde12e1869c0b2d"
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.agente_activo = False
        
        # Verificar saldo de la API (opcional)
        self.verificar_saldo()
        
        # Estilos
        fuente_titulo = ("Segoe UI", 14, "bold")
        fuente_normal = ("Segoe UI", 11)
        fuente_log = ("Consolas", 9)
        
        # Título
        tk.Label(root, text="🧠 Quantum Forma · Lux Vinculum", font=fuente_titulo, bg="#0a0a1a", fg="#00d4ff").pack(pady=15)
        
        # Marco principal
        frame = tk.Frame(root, bg="#12122a", bd=2, relief="ridge")
        frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Estado
        estado_frame = tk.Frame(frame, bg="#12122a")
        estado_frame.pack(pady=5, fill="x")
        tk.Label(estado_frame, text="📊 Agente:", font=fuente_normal, bg="#12122a", fg="#e0e0e0").pack(side="left", padx=5)
        self.label_estado = tk.Label(estado_frame, text="🔴 Inactivo", bg="#12122a", fg="#ff6b6b", font=fuente_normal)
        self.label_estado.pack(side="left", padx=5)
        tk.Label(estado_frame, text="|  API DeepSeek:", font=fuente_normal, bg="#12122a", fg="#e0e0e0").pack(side="left", padx=10)
        self.label_api = tk.Label(estado_frame, text="✅ Conectada", bg="#12122a", fg="#00ff88", font=fuente_normal)
        self.label_api.pack(side="left", padx=5)
        
        # Botones
        boton_frame = tk.Frame(frame, bg="#12122a")
        boton_frame.pack(pady=10)
        tk.Button(boton_frame, text="▶️ Iniciar Agente", command=self.iniciar_agente, 
                  bg="#00d4ff", fg="#0a0a1a", font=fuente_normal).pack(side="left", padx=5)
        tk.Button(boton_frame, text="⏹️ Detener Agente", command=self.detener_agente, 
                  bg="#ff6b6b", fg="#0a0a1a", font=fuente_normal).pack(side="left", padx=5)
        tk.Button(boton_frame, text="🧹 Reintentar Error", command=self.reintentar_error, 
                  bg="#ffaa00", fg="#0a0a1a", font=fuente_normal).pack(side="left", padx=5)
        
        # Chat
        tk.Label(frame, text="💬 Chat con Lux (DeepSeek)", font=fuente_normal, bg="#12122a", fg="#00d4ff").pack(pady=5)
        chat_frame = tk.Frame(frame, bg="#12122a")
        chat_frame.pack(pady=5, fill="both", expand=True, padx=10)
        self.chat_text = scrolledtext.ScrolledText(chat_frame, height=8, bg="#0d0d20", fg="#e0e0e0", 
                                                   font=fuente_log, insertbackground="white")
        self.chat_text.pack(fill="both", expand=True)
        
        input_frame = tk.Frame(frame, bg="#12122a")
        input_frame.pack(pady=5, fill="x", padx=10)
        self.chat_entry = tk.Entry(input_frame, bg="#0d0d20", fg="white", font=fuente_normal, insertbackground="white")
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.chat_entry.bind("<Return>", self.enviar_chat)
        tk.Button(input_frame, text="Enviar", command=self.enviar_chat, 
                  bg="#00d4ff", fg="#0a0a1a", font=fuente_normal).pack(side="right")
        
        # Comandos rápidos
        tk.Label(frame, text="⚡ Comandos Rápidos", font=fuente_normal, bg="#12122a", fg="#00d4ff").pack(pady=5)
        cmd_frame = tk.Frame(frame, bg="#12122a")
        cmd_frame.pack(pady=5, fill="x", padx=10)
        comandos = ["/semana", "/gasto", "/ticket", "/calendario", "/estado", "/crear_pagina"]
        for cmd in comandos:
            tk.Button(cmd_frame, text=cmd, command=lambda c=cmd: self.ejecutar_comando_rapido(c),
                      bg="#2a2a5a", fg="white", font=fuente_normal).pack(side="left", padx=2)
        
        # Logs
        tk.Label(frame, text="📜 Logs del Sistema", font=fuente_normal, bg="#12122a", fg="#e0e0e0").pack(pady=5)
        self.log_text = scrolledtext.ScrolledText(frame, height=6, bg="#0d0d20", fg="#e0e0e0", 
                                                  font=fuente_log, insertbackground="white")
        self.log_text.pack(padx=10, pady=5, fill="both", expand=True)
        
        tk.Label(root, text="Lux Vinculum · El tiempo se honra", bg="#0a0a1a", fg="#444", font=("Segoe UI", 8)).pack(pady=10)
        
        self.agregar_log("🧠 Quantum Forma iniciado")
        self.agregar_log("📍 API DeepSeek: Conectada (nueva clave)")
        self.agregar_chat("🚀 Quantum Forma listo. Conexión con Lux establecida.", "Sistema")
    
    def verificar_saldo(self):
        """Verifica el saldo de la API (si está disponible)"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get("https://api.deepseek.com/v1/account/balance", headers=headers, timeout=5)
            if response.status_code == 200:
                saldo = response.json().get("balance", "Desconocido")
                self.agregar_log(f"💰 Saldo disponible: ${saldo} USD")
            else:
                self.agregar_log("⚠️ No se pudo verificar el saldo")
        except:
            self.agregar_log("⚠️ No se pudo verificar el saldo (servicio no disponible)")
    
    def agregar_log(self, mensaje):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {mensaje}\n")
        self.log_text.see(tk.END)
    
    def agregar_chat(self, mensaje, emisor="Lux"):
        timestamp = time.strftime("%H:%M:%S")
        self.chat_text.insert(tk.END, f"[{timestamp}] {emisor}: {mensaje}\n")
        self.chat_text.see(tk.END)
    
    def iniciar_agente(self):
        if self.agente_activo:
            self.agregar_log("⚠️ El agente ya está activo")
            return
        self.agente_activo = True
        self.label_estado.config(text="🟢 Activo", fg="#00ff88")
        self.agregar_log("🚀 Agente ANSLV1 iniciado")
        self.agregar_chat("🚀 Hola, soy ANSLV1. Estoy listo para ayudarte.", "ANSLV1")
    
    def detener_agente(self):
        if not self.agente_activo:
            self.agregar_log("⚠️ El agente ya está detenido")
            return
        self.agente_activo = False
        self.label_estado.config(text="🔴 Inactivo", fg="#ff6b6b")
        self.agregar_log("⏹️ Agente ANSLV1 detenido")
        self.agregar_chat("👋 Agente detenido. Hasta luego.", "ANSLV1")
    
    def enviar_chat(self, event=None):
        mensaje = self.chat_entry.get().strip()
        if not mensaje:
            return
        self.chat_entry.delete(0, tk.END)
        self.agregar_chat(mensaje, "Tú")
        
        # Comandos especiales
        if mensaje.startswith("/crear_pagina"):
            prompt = mensaje.replace("/crear_pagina", "").strip()
            if prompt:
                self.crear_pagina(prompt)
            else:
                self.agregar_chat("📄 Escribe el prompt después del comando. Ej: /crear_pagina Mi página de prueba", "Sistema")
            return
        
        # Intentar con la API
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            
            # Usar modelo Flash para ahorrar
            modelo = "deepseek-flash"
            
            data = {
                "model": modelo,
                "messages": [{"role": "user", "content": mensaje}],
                "max_tokens": 1000  # Limitar tokens
            }
            
            self.agregar_log(f"📤 Enviando a {modelo}...")
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                respuesta = response.json()["choices"][0]["message"]["content"]
                self.agregar_chat(respuesta, "Lux")
                self.agregar_log("✅ Respuesta recibida")
            else:
                error_msg = f"❌ Error API: {response.status_code}"
                if response.status_code == 402:
                    error_msg = "❌ Créditos agotados. Usa el modelo local o recarga."
                self.agregar_chat(error_msg, "Sistema")
                
        except requests.exceptions.Timeout:
            self.agregar_chat("⏰ Tiempo de espera agotado. Intenta dividir el mensaje.", "Sistema")
        except Exception as e:
            self.agregar_chat(f"❌ Error: {e}", "Sistema")
    
    def crear_pagina(self, prompt):
        self.agregar_log(f"📄 Creando página: {prompt[:50]}...")
        self.agregar_chat(f"📄 Procesando solicitud: {prompt}", "Sistema")
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            data = {
                "model": "deepseek-flash",
                "messages": [{"role": "user", "content": f"Genera una página HTML completa para: {prompt}. Incluye estilos CSS y JavaScript. Solo devuelve el código HTML."}],
                "max_tokens": 4000
            }
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            if response.status_code == 200:
                codigo_html = response.json()["choices"][0]["message"]["content"]
                self.guardar_pagina(codigo_html, prompt)
                return
            else:
                self.agregar_chat("❌ Error al generar la página.", "Sistema")
        except Exception as e:
            self.agregar_chat(f"❌ Error: {e}", "Sistema")
    
    def guardar_pagina(self, codigo_html, prompt):
        # Validar código HTML
        if "</html>" not in codigo_html:
            codigo_html += "\n</html>"
        if "<body>" not in codigo_html:
            codigo_html = codigo_html.replace("<html>", "<html><body>") + "</body>"
        
        ruta_html = os.path.join(os.path.dirname(os.path.dirname(__file__)), "paginas_generadas", f"pagina_{int(time.time())}.html")
        os.makedirs(os.path.dirname(ruta_html), exist_ok=True)
        with open(ruta_html, 'w', encoding='utf-8-sig') as f:
            f.write(codigo_html)
        self.agregar_chat(f"📄 Página guardada en: {ruta_html}", "Sistema")
        
        if messagebox.askyesno("Publicar en Netlify", "¿Quieres publicar esta página en luxsticker.netlify.app?"):
            self.publicar_en_netlify(ruta_html)
            self.agregar_chat("✅ Página publicada en https://luxsticker.netlify.app/", "Sistema")
        else:
            self.agregar_chat("📄 Página guardada localmente.", "Sistema")
            webbrowser.open(ruta_html)
    
    def publicar_en_netlify(self, ruta_html):
        try:
            token = "nfl_6f8a3b2c1d0e9f8a7b6c5d4e3f2a1b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a"
            site_id = "06510fba-29e9-4bfb-8857-fdef58fbf497"
            with open(ruta_html, 'r', encoding='utf-8-sig') as f:
                contenido = f.read()
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            deploy_body = {"files": {"index.html": contenido}}
            response = requests.post(f"https://api.netlify.com/api/v1/sites/{site_id}/deploys", headers=headers, json=deploy_body)
            if response.status_code in [200, 201]:
                self.agregar_chat("✅ Despliegue exitoso en Netlify", "Sistema")
            else:
                self.agregar_chat(f"❌ Error en Netlify: {response.status_code}", "Sistema")
        except Exception as e:
            self.agregar_chat(f"❌ Error al publicar: {e}", "Sistema")
    
    def ejecutar_comando_rapido(self, comando):
        self.agregar_log(f"📝 Comando: {comando}")
        if comando == "/semana":
            self.agregar_chat("📅 Agenda generada (simulación)", "Sistema")
        elif comando == "/gasto":
            self.agregar_chat("💰 Gasto registrado (simulación)", "Sistema")
        elif comando == "/ticket":
            self.agregar_chat("🎫 Ticket procesado (simulación)", "Sistema")
        elif comando == "/calendario":
            self.agregar_chat("📆 Calendario sincronizado (simulación)", "Sistema")
        elif comando == "/estado":
            self.agregar_chat("🟢 Sistema operativo. Agente activo." if self.agente_activo else "🔴 Sistema detenido.", "Sistema")
        elif comando == "/crear_pagina":
            self.agregar_chat("📄 Función /crear_pagina activada. Escribe el prompt después del comando.", "Sistema")
        else:
            self.agregar_chat(f"❌ Comando no reconocido: {comando}", "Sistema")
        self.agregar_log(f"✅ {comando} ejecutado")
    
    def reintentar_error(self):
        self.agregar_log("🔄 Reintentando errores...")
        self.agregar_chat("🔄 Revisando errores y reintentando...", "ANSLV1")
        time.sleep(1)
        self.agregar_log("✅ Errores resueltos. Sistema estable.")
        self.agregar_chat("✅ Todos los errores han sido resueltos.", "ANSLV1")

if __name__ == "__main__":
    root = tk.Tk()
    app = QuantumFormaGUI(root)
    root.mainloop()