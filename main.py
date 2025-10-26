from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from pymongo import MongoClient
from flask import Flask
import os
from datetime import datetime
import threading

# ==============================
# الإعدادات العامة
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # توكن البوت من Render
MONGO_URL = os.getenv("MONGO_URL")  # رابط قاعدة البيانات من MongoDB Atlas

if not BOT_TOKEN or not MONGO_URL:
    raise ValueError("⚠️ يجب ضبط المتغيرات BOT_TOKEN و MONGO_URL في إعدادات Render")

# الاتصال بقاعدة البيانات
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["telegram_bot"]
users = db["users"]

# ==============================
# إعداد Flask حتى يبقى البوت شغال دائمًا على Render
# ==============================
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "🤖 البوت يعمل بنجاح!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=10000)

# ==============================
# أوامر البوت
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يُشغّل عند كتابة /start"""
    user = update.message.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name

    # تحقق هل المستخدم موجود أم لا
    existing_user = users.find_one({"user_id": user_id})
    if not existing_user:
        users.insert_one({
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "balance": 0.0,
            "joined_at": datetime.utcnow()
        })
        print(f"✅ مستخدم جديد: {first_name} ({user_id})")

    keyboard = [["💰 رصيدي"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"أهلاً {first_name}! 👋\nاختر من القائمة:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يتعامل مع الرسائل والزر"""
    text = update.message.text
    user_id = update.message.from_user.id

    user = users.find_one({"user_id": user_id})
    if not user:
        await update.message.reply_text("⚠️ الرجاء إرسال /start أولاً.")
        return

    if text == "💰 رصيدي":
        balance = user.get("balance", 0.0)
        await update.message.reply_text(f"💰 رصيدك الحالي هو: {balance:.2f}💵")
    else:
        await update.message.reply_text("🤖 لم أفهم رسالتك، استخدم الأزرار أدناه.")

# ==============================
# تشغيل البوت
# ==============================
def run_bot():
    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    telegram_app.run_polling()

# ==============================
# تشغيل Flask + Bot في نفس الوقت
# ==============================
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
