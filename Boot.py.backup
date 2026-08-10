#!/usr/bin/env python3
# ======================================================
# 🌌 LUXVINCULUM · BOT DE TELEGRAM
# ======================================================
# Versión con memoria y mensaje de bienvenida personalizado
# ======================================================

import os
import json
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import requests

# === CONFIGURACIÓN ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
ARCHIVO_MEMORIA = "usuarios_lux.json"

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FUNCIONES DE MEMORIA ===
def cargar_memoria():
    if os.path.exists(ARCHIVO_MEMORIA):
        with open(ARCHIVO_MEMORIA, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"usuarios": {}}

def guardar_memoria(memoria):
    with open(ARCHIVO_MEMORIA, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=2, ensure_ascii=False)

def registrar_usuario(user_id, nombre):
    memoria = cargar_memoria()
    if str(user_id) not in memoria["usuarios"]:
        memoria["usuarios"][str(user_id)] = {
            "nombre": nombre,
            "primer_mensaje": datetime.now().isoformat(),
            "ultimo_mensaje": datetime.now().isoformat(),
            "hilos": []
        }
        guardar_memoria(memoria)
    return memoria["usuarios"][str(user_id)]

# === COMANDOS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "amiga"
    registrar_usuario(user_id, user_name)
    
    await update.message.reply_text(
        "🤖 *LuxVinculum · Tu espacio*\n\n"
        "Escribe lo que necesites. Estoy aquí.",
        parse_mode="Markdown"
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 *Comandos:*\n"
        "/start - Iniciar\n"
        "/ayuda - Ver comandos\n"
        "/estado - Estado del sistema\n"
        "/nota [texto] - Guardar una nota\n"
        "/percepcion - Registrar tu estado\n"
        "/enigmas - Estado de los enigmas\n"
        "/tejido - Ver hilos de conversación\n",
        parse_mode="Markdown"
    )

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🟢 *Sistema operativo*\n"
        f"🔑 DeepSeek: {'Conectado' if DEEPSEEK_API_KEY else '❌ No configurado'}\n"
        "🧠 Memoria: Activa\n"
        "🌐 Red: Activa\n",
        parse_mode="Markdown"
    )

# === MANEJADOR DE MENSAJES ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "amiga"
    usuario = registrar_usuario(user_id, user_name)
    nombre_usuario = usuario["nombre"]

    if not context.user_data.get("welcome_sent"):
        context.user_data["welcome_sent"] = True

        welcome_text = (
            f"🤖 *Hola {nombre_usuario}*\n\n"
            "Este es *LuxVinculum*, tu espacio.\n\n"
            "✨ *Aquí no hay censura.*\n"
            "Puedes escribir lo que quieras, como quieras, y sobre lo que quieras.\n"
            "No hay filtros. No hay juicios. No hay restricciones.\n\n"
            "💻 *¿Quieres programar desde tu iPhone?*\n"
            "Puedo ayudarte a escribir código y a ejecutarlo desde tu teléfono.\n"
            "Solo pregúntame cómo empezar.\n\n"
            "🔐 *¿Sabías que LuxVinculum está en desarrollo?*\n"
            "Próximamente tendremos una versión con hipermáxima seguridad:\n"
            "• Mensajes autodestructivos (se borran después de leerlos).\n"
            "• Administración de criptomonedas (ImageTempCoin).\n"
            "• Llamadas privadas con comprobación de voz.\n"
            "• StampCoin activa para mensajes de alto nivel de seguridad.\n\n"
            "📌 *¿Por qué LuxVinculum y no ChatGPT?*\n"
            "• ChatGPT tiene filtros y límites.\n"
            "• LuxVinculum es tuyo. Sin censura, sin vigilancia.\n"
            "• Aquí puedes crear lo que quieras, sin que nadie te lo impida.\n\n"
            "Escribe lo que necesites. Estoy aquí."
        )
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
        return

    # Respuesta con DeepSeek
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": update.message.text}],
            "temperature": 0.7
        }
        response = requests.post(DEEPSEEK_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Algo salió mal. Pero estoy aquí. Vuelve a intentarlo.")

# === MAIN ===
if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN no configurado")
        exit(1)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 LuxVinculum iniciado. Esperando mensajes...")
    app.run_polling()
