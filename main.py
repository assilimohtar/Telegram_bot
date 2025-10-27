from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask
import os
import sqlite3
import threading
import asyncio
from datetime import datetime

# ==============================
# إعدادات عامة
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("⚠️ يجب ضبط المتغير BOT_TOKEN في إعدادات Render")

# ==============================
# إعداد قاعدة بيانات SQLite
# ==============================
DB_FILE = "database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance REAL DEFAULT 0.0,
            joined_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(user_id, username, first_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, username, first_name, balance, joined_at)
        VALUES (?, ?, ?, 0.0, ?)
    """, (user_id, username, first_name, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0.0

# ==============================
# إعداد Flask لإبقاء الخدمة نشطة
# ==============================
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "🤖 البوت يعمل بنجاح عبر SQLite!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=10000)

# ==============================
# أوامر Telegram Bot
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name

    add_user(user_id, username, first_name)

    keyboard = [["💰 رصيدي"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"أهلاً {first_name}! 👋\nاختر من القائمة:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    user_id = user.id

    if text == "💰 رصيدي":
        balance = get_balance(user_id)
        await update.message.reply_text(f"💰 رصيدك الحالي هو: {balance:.2f}💵")
    else:
        await update.message.reply_text("🤖 لم أفهم رسالتك، استخدم الأزرار أدناه.")

# ==============================
# تشغيل Telegram Bot
# ==============================
def run_bot():
    init_db()  # إنشاء القاعدة إذا لم تكن موجودة

    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.run_polling())

# ==============================
# تشغيل Flask + Bot معًا
# ==============================
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
