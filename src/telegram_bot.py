import os
import urllib3
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

from src.whoop_client import WhoopClient
from src.gemini_brain import GeminiBrain
from src.report_generator import generate_and_save_html_report

# Desactivar advertencias de SSL locales
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

whoop = WhoopClient()
brain = GeminiBrain()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not whoop.refresh_token:
        url = whoop.get_auth_url()
        msg = (
            "¡Hola Mauricio! Soy tu asistente de salud.\n\n"
            "Parece que no tengo acceso a tu cuenta de Whoop. Por favor:\n"
            f"1. Entra a este enlace: {url}\n"
            "2. Autoriza la app.\n"
            "3. Cuando llegues a la página blanca, copia el ENLACE COMPLETO o el 'code=XXXX' de la barra de direcciones y pégalo aquí."
        )
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("¡Hola Mauricio! Estoy conectado a Whoop y listo. Usa /report para ver tu resumen de hoy o simplemente háblame.")

async def send_long_message(update: Update, text: str):
    MAX_LEN = 4000
    for i in range(0, len(text), MAX_LEN):
        await update.message.reply_text(text[i:i+MAX_LEN])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # Manejar el código de autorización si no hay token
    if not whoop.refresh_token:
        if 'code=' in text:
            # Extraer el código
            code = text.split('code=')[1].split('&')[0]
            success = whoop.exchange_code(code)
            if success:
                await update.message.reply_text("¡Excelente! Autenticación con Whoop exitosa. Ya puedo leer tus datos.")
            else:
                await update.message.reply_text("Hubo un error al procesar el código. Inténtalo de nuevo.")
        else:
            await update.message.reply_text("Sigo esperando el código de Whoop. Envíame la URL a la que fuiste redirigido.")
        return

    # Si ya tenemos acceso a Whoop, es un mensaje de chat normal para Gemini
    whoop_data = {}
    try:
        whoop_data['recovery'] = whoop.get_latest_recovery()
        whoop_data['sleep'] = whoop.get_latest_sleep()
        whoop_data['cycle'] = whoop.get_latest_cycle()
    except Exception as e:
        print(f"Error fetching live whoop data for chat: {e}")

    reply = brain.chat_and_update_memory(text, chat_history=[], whoop_data=whoop_data)
    await send_long_message(update, reply)

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Comando /report recibido de {update.message.chat_id}")
    if not whoop.refresh_token:
        await update.message.reply_text("Primero necesito que autorices a Whoop. Usa /start")
        return
        
    user_notes = " ".join(context.args) if context.args else ""
    await update.message.reply_text("Generando tu reporte ejecutivo... 🔄 (Extrayendo datos de Whoop)")
    try:
        recovery = whoop.get_latest_recovery()
        sleep = whoop.get_latest_sleep()
        cycle = whoop.get_latest_cycle()
        
        workouts = []
        if cycle:
            workouts = whoop.get_workouts_for_cycle(cycle.get('start'), cycle.get('end'))
        
        await update.message.reply_text("Analizando con Gemini y calculando calorías... 🧠")
        json_report = brain.generate_daily_report(cycle, recovery, sleep, workouts, user_notes=user_notes)
        
        # Generar HTML y guardar
        base_dir = os.path.dirname(os.path.dirname(__file__))
        html_filepath = generate_and_save_html_report(json_report, base_dir)
        
        # Enviar documento HTML a Telegram
        with open(html_filepath, 'rb') as f:
            await update.message.reply_document(
                document=f, 
                filename=os.path.basename(html_filepath),
                caption="📊 Aquí tienes tu Reporte Ejecutivo McKinsey Style."
            )
        
    except Exception as e:
        await send_long_message(update, f"Error generando reporte: {str(e)}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not whoop.refresh_token:
        await update.message.reply_text("Primero necesito que autorices a Whoop. Usa /start")
        return

    photo_file = await update.message.photo[-1].get_file()
    
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, "temp_inbody.jpg")
    await photo_file.download_to_drive(temp_path)
    
    user_message = update.message.caption or "Aquí está mi nuevo InBody."
    await update.message.reply_text("Analizando tu InBody con Gemini Vision... 👁️🧠")
    
    try:
        reply = brain.analyze_image_and_update_memory(temp_path, user_message)
        await send_long_message(update, reply)
    except Exception as e:
        await update.message.reply_text(f"Error analizando la imagen: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

import asyncio
from aiohttp import web

async def main():
    if not TELEGRAM_TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el .env", flush=True)
        return
        
    print("Configurando Bot de Telegram en Modo Webhook...", flush=True)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    processed_updates = set()

    async def telegram_webhook(request: web.Request) -> web.Response:
        data = await request.json()
        update_id = data.get("update_id")
        
        # Ignorar retries duplicados de Telegram durante el cold-start
        if update_id in processed_updates:
            print(f"Ignorando update duplicado: {update_id}", flush=True)
            return web.Response()
            
        processed_updates.add(update_id)
        if len(processed_updates) > 500:
            processed_updates.clear() # Limpiar memoria periódicamente
            
        await app.update_queue.put(
            Update.de_json(data=data, bot=app.bot)
        )
        return web.Response()
        
    async def health_check(request: web.Request) -> web.Response:
        print("Health check recibido", flush=True)
        return web.Response(text="Bot is running!")

    web_app = web.Application()
    web_app.router.add_post(f"/{TELEGRAM_TOKEN}", telegram_webhook)
    web_app.router.add_get("/", health_check)
    web_app.router.add_get("/healthz", health_check)
    
    port = int(os.environ.get("PORT", 8080))
    url = "https://whoop-analyzer.onrender.com"
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    print(f"Iniciando aiohttp y webhook en puerto {port}...", flush=True)
    async with app:
        await app.bot.set_webhook(url=f"{url}/{TELEGRAM_TOKEN}")
        await app.start()
        await site.start()
        print("¡Servidor Webhook iniciado y escuchando!", flush=True)
        
        await asyncio.Event().wait()
        await site.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
