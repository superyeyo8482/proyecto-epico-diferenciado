import requests
import os
import asyncio
import csv
import json
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.error import NetworkError, TimedOut
import torch
import clip
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pymupdf as fitz

TELEGRAM_TOKEN = "8924820055:AAE73Jub2MhK1L-5JM_aHSsT2YlX68eX3kc"
DEEPSEEK_API_KEY = "sk-6036f527b5ff4906ae18bbfebabeb1f1"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def consultar_deepseek(mensaje):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": mensaje}]}
    response = requests.post(DEEPSEEK_URL, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hola, soy Lux Vinculum.")

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    respuesta = consultar_deepseek(update.message.text)
    await update.message.reply_text(respuesta)

async def manejar_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import base64
    if update.message.voice:
        file = await update.message.voice.get_file()
        ext = ".ogg"
    elif update.message.audio:
        file = await update.message.audio.get_file()
        ext = ".mp3"
    else:
        await update.message.reply_text("Envía un mensaje de voz.")
        return
    path = f"audio_{update.message.message_id}{ext}"
    await file.download_to_drive(path)
    await update.message.reply_text("🔄 Procesando audio...")
    try:
        with open(path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": f"Transcribe este audio a texto (Base64): {audio_b64}"}]}
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload)
        if response.status_code == 200:
            texto = response.json()["choices"][0]["message"]["content"]
            os.makedirs("transcripciones", exist_ok=True)
            with open(f"transcripciones/audio_{update.message.message_id}.txt", "w", encoding="utf-8") as f:
                f.write(texto)
            await update.message.reply_text(f"✅ Transcripción:\n\n{texto[:500]}...")
        else:
            await update.message.reply_text(f"❌ Error: {response.status_code}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        if os.path.exists(path):
            os.remove(path)

async def semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("agendas/2026/semana_actual.txt", "r", encoding="utf-8") as f:
            await update.message.reply_text(f.read())
    except FileNotFoundError:
        await update.message.reply_text("⚠️ No se encontró la agenda.")

async def ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Función de ticket en desarrollo.")

async def guardar_imagen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Imagen recibida. Procesando...")

app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, manejar_audio))
app.add_handler(CommandHandler("semana", semana))
app.add_handler(CommandHandler("ticket", ticket))
app.add_handler(MessageHandler(filters.PHOTO, guardar_imagen))

print("🧡 ANSLV1 iniciado.")
app.run_polling()


