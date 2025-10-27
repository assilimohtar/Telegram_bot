import os
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ========= إعداد بوت التلغرام =========
BOT_TOKEN = os.getenv("BOT_TOKEN")

# دالة بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["💰 رصيدي"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("أهلاً بك! اختر من القائمة:", reply_markup=reply_markup)

# دالة التعامل مع الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "💰 رصيدي":
        await update.message.reply_text("رصيدك الحالي هو: 0.00💵")
    else:
        await update.message.reply_text("لم أفهم رسالتك 🤔")

# إنشاء التطبيق
app_tg = ApplicationBuilder().token(BOT_TOKEN).build()
app_tg.add_handler(CommandHandler("start", start))
app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ========= خادم Flask لإبقاء Render نشط =========
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "🤖 Telegram bot is running on Render!"

# ========= تشغيل البوت و Flask معًا =========
def run_telegram():
    print("🚀 Bot is running...")
    app_tg.run_polling()

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Web server running on port {port}")
    web_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # تشغيل البوت في Thread والخادم في Thread آخر
    threading.Thread(target=run_telegram).start()
    run_flask()
