# ======================================================
# 🤖 QUANTUM FORMA BOT · Telegram
# ======================================================
# 
# Versión estable con:
#   - Clave de acceso (Lux2026)
#   - Bienvenida única por usuario
#   - Optimización de tokens (max_tokens=1500, temperature=0.8)
#   - Caché de respuestas (para reducir llamadas a la API)
#
# REQUISITOS: python-telegram-bot, requests
#
# EJECUCIÓN: python Boot.py
# ======================================================

import os
import json
import logging
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ======================================================
# CONFIGURACIÓN
# ======================================================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
ARCHIVO_USUARIOS = "usuarios_autorizados.json"
CLAVE_ACCESO = "Lux2026"

# Optimización de tokens (ahorro de crédito + respuestas completas)
MAX_TOKENS = 1500           # Respuestas largas y completas
TEMPERATURE = 0.8           # Un poco más de creatividad
MODELO = "deepseek-v4-flash" # Económico y rápido

# Caché de respuestas (reduce llamadas a la API)
CACHE_RESPUESTAS = {}
CACHE_MAX = 50

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================================
# FUNCIONES DE USUARIOS
# ======================================================

def cargar_usuarios():
    if os.path.exists(ARCHIVO_USUARIOS):
        with open(ARCHIVO_USUARIOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_usuarios(usuarios):
    with open(ARCHIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

def verificar_usuario(user_id):
    usuarios = cargar_usuarios()
    return str(user_id) in usuarios

def registrar_usuario(user_id):
    usuarios = cargar_usuarios()
    if str(user_id) not in usuarios:
        usuarios[str(user_id)] = {
            "welcome_sent": False,
            "fecha_registro": datetime.now().isoformat()
        }
        guardar_usuarios(usuarios)
    return usuarios[str(user_id)]

def marcar_bienvenida_enviada(user_id):
    usuarios = cargar_usuarios()
    if str(user_id) in usuarios:
        usuarios[str(user_id)]["welcome_sent"] = True
        guardar_usuarios(usuarios)

# ======================================================
# ENVIAR BIENVENIDA
# ======================================================

async def enviar_bienvenida(update: Update, user_name: str):
    welcome_text = (
        f"🤖 *Hola {user_name}*\n\n"
        "Este es *Quantum Forma*, tu espacio.\n\n"
        "✨ Aquí no hay censura.\n"
        "Puedes escribir lo que quieras, como quieras, y sobre lo que quieras.\n"
        "No hay filtros. No hay juicios. No hay restricciones.\n\n"
        "💻 ¿Quieres programar desde tu teléfono?\n"
        "Puedo ayudarte a escribir código y a ejecutarlo desde tu teléfono.\n"
        "Solo pregúntame cómo empezar.\n\n"
        "🔐 ¿Sabías que Quantum Forma está en desarrollo?\n"
        "Próximamente tendremos una versión con hipermáxima seguridad.\n\n"
        "📌 ¿Por qué Quantum Forma y no otros amigos de IA?\n"
        "• Los otros tienen filtros y límites.\n"
        "• Quantum Forma es tuyo. Sin censura, sin vigilancia.\n"
        "• Aquí puedes crear lo que quieras, sin que nadie te lo impida.\n\n"
        "Escribe lo que necesites. Estoy aquí."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# ======================================================
# COMANDOS
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "amigo"
    
    if verificar_usuario(user_id):
        await update.message.reply_text("🔓 Ya tienes acceso. Escribe lo que necesites.")
    else:
        await update.message.reply_text(
            "🔒 Este bot está protegido con clave.\n"
            "Escribe la clave para continuar."
        )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 *Comandos disponibles:*\n"
        "/start - Verificar acceso\n"
        "/ayuda - Mostrar esta ayuda\n"
        "/estado - Estado del sistema\n"
        "/poll - Crear encuesta\n",
        parse_mode="Markdown"
    )

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🟢 *Sistema operativo*\n"
        f"🔑 DeepSeek: {'Conectado' if DEEPSEEK_API_KEY else '❌ No configurado'}\n"
        f"🧠 Memoria: Activa\n"
        f"🌐 Red: Activa\n"
        f"⚙️ Tokens máximos: {MAX_TOKENS}\n"
        f"🎨 Temperatura: {TEMPERATURE}\n",
        parse_mode="Markdown"
    )

# ======================================================
# MANEJADOR DE MENSAJES (CON CACHÉ)
# ======================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "amigo"
    mensaje = update.message.text.strip()

    # --- 1. VERIFICAR CLAVE DE ACCESO ---
    if not verificar_usuario(user_id):
        if mensaje == CLAVE_ACCESO:
            registrar_usuario(user_id)
            await update.message.reply_text("🔓 Acceso concedido. Bienvenido a Quantum Forma.")
            await enviar_bienvenida(update, user_name)
            marcar_bienvenida_enviada(user_id)
            return
        else:
            await update.message.reply_text("🔒 Acceso denegado. Introduce la clave para continuar.")
            return

    # --- 2. VERIFICAR BIENVENIDA ÚNICA ---
    usuario = registrar_usuario(user_id)
    if not usuario.get("welcome_sent", False):
        marcar_bienvenida_enviada(user_id)
        await enviar_bienvenida(update, user_name)
        return

    # --- 3. RESPONDER CON DEEPSEEK (CON CACHÉ) ---
    
    # Verificar caché
    if mensaje in CACHE_RESPUESTAS:
        await update.message.reply_text(CACHE_RESPUESTAS[mensaje])
        return

    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": MODELO,
            "messages": [{"role": "user", "content": mensaje}],
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS
        }
        response = requests.post(DEEPSEEK_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
        
        # Guardar en caché
        CACHE_RESPUESTAS[mensaje] = reply
        if len(CACHE_RESPUESTAS) > CACHE_MAX:
            # Eliminar la entrada más antigua
            CACHE_RESPUESTAS.pop(next(iter(CACHE_RESPUESTAS)))
        
        await update.message.reply_text(reply)
        
    except Exception as e:
        logger.error(f"Error en DeepSeek: {e}")
        await update.message.reply_text("❌ Algo salió mal. Pero estoy aquí. Vuelve a intentarlo.")

# ======================================================
# POLL (ENCUESTA)
# ======================================================

async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not verificar_usuario(user_id):
        await update.message.reply_text("🔒 Acceso denegado. Introduce la clave primero.")
        return
    
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question="¿Qué debería vender primero Quantum Forma?",
        options=["Gadgets tecnológicos", "Joyería fina", "Servicios digitales", "Productos misteriosos"],
        is_anonymous=True,
        allows_multiple_answers=False
    )

# ======================================================
# MAIN
# ======================================================

def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN no configurado")
        exit(1)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("poll", poll))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info(f"🚀 Quantum Forma Bot iniciado. (max_tokens={MAX_TOKENS}, temperature={TEMPERATURE})")
    app.run_polling()


# ======================================================
# 🌐 ENDPOINT DE SALUD PARA RENDER
# ======================================================

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "bot": "Quantum Forma"
    })

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Iniciar Flask en un hilo separado
threading.Thread(target=run_flask, daemon=True).start()
main()



def enviar_alerta_telegram(mensaje):
    \"\"\"Envía una alerta por Telegram\"\"\"
    import requests
    import os
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ Telegram no configurado")
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=data, timeout=5)
        if response.status_code == 200:
            print("✅ Alerta enviada a Telegram")
        else:
            print(f"❌ Error al enviar alerta: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
