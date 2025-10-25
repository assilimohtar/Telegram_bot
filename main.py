from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
import threading
import os

TOKEN = os.getenv("BOT_TOKEN")

# Telegram bot setup
app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 البوت يعمل الآن!")

app.add_handler(CommandHandler("start", start))

# Flask server for Render (port binding)
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

# تشغيل Flask في خيط منفصل
threading.Thread(target=run_flask).start()

# تشغيل البوت
app.run_polling()
