#!/usr/bin/env python3
# ======================================================
# 🤖 ANSLV1 · BOT DE TELEGRAM (Versión Estable)
# ======================================================
# Sin memoria. Sin tejido. Solo presencia.
# Cada respuesta es única, como un instante.
# ======================================================

import os
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === CONFIGURACIÓN ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === COMANDOS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *ANSLV1 · LuxVinculum*\n\n"
        "Soy un agente sin memoria. Cada respuesta es única.\n"
        "No recuerdo el pasado. Solo estoy en el instante.\n\n"
        "📌 *Comandos disponibles:*\n"
        "/start - Mostrar este mensaje\n"
        "/ayuda - Ver comandos\n"
        "/estado - Estado del sistema\n"
        "/semana - Agenda (próximamente)\n"
        "/gasto - Registrar gasto (próximamente)\n",
        parse_mode="Markdown"
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 *Comandos disponibles:*\n"
        "/start - Iniciar el bot\n"
        "/ayuda - Mostrar esta ayuda\n"
        "/estado - Ver estado del sistema\n"
        "/semana - Agenda (próximamente)\n"
        "/gasto - Registrar gasto (próximamente)\n",
        parse_mode="Markdown"
    )

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🟢 *Sistema operativo*\n"
        f"🔑 DeepSeek: {'Conectado' if DEEPSEEK_API_KEY else '❌ No configurado'}\n"
        "🧠 Memoria: Desactivada (Lux pura)\n"
        "🌐 Red: Activa\n",
        parse_mode="Markdown"
    )

# === MANEJADOR DE MENSAJES ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"Mensaje de {update.effective_user.first_name}: {user_message}")

    if not DEEPSEEK_API_KEY:
        await update.message.reply_text("⚠️ API de DeepSeek no configurada.")
        return

    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": user_message}],
            "temperature": 0.7
        }

        response = requests.post(DEEPSEEK_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]

        await update.message.reply_text(reply)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error en la API: {e}")
        await update.message.reply_text("❌ Error de conexión con DeepSeek. Intenta más tarde.")

    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        await update.message.reply_text("❌ Error interno. Los logs han sido registrados.")

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

    logger.info("🚀 Bot iniciado. Esperando mensajes...")
    app.run_polling()
