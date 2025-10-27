from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask
import sqlite3
import os
import threading
import asyncio
from datetime import datetime

# ==============================
# الإعدادات العامة
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("⚠️ يجب ضبط المتغير BOT_TOKEN في إعدادات Render")

DB_FILE = "database.db"

# ==============================
# إعداد قاعدة بيانات SQLite
# ==============================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # جدول المستخدمين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 0,
            joined_at TEXT
        )
    """)

    # جدول طلبات المستخدمين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            link TEXT,
            order_type TEXT,
            quantity INTEGER,
            created_at TEXT,
            completed INTEGER DEFAULT 0
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
        VALUES (?, ?, ?, 0, ?)
    """, (user_id, username, first_name, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def add_request(user_id, link, order_type, quantity):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO requests (user_id, link, order_type, quantity, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, link, order_type, quantity, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_requests():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, link, order_type, quantity FROM requests WHERE completed = 0 LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result

def mark_request_done(request_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE requests SET completed = 1 WHERE id = ?", (request_id,))
    conn.commit()
    conn.close()

# ==============================
# إعداد Flask لإبقاء الخدمة نشطة
# ==============================
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "🤖 بوت تبادل المتابعين يعمل بنجاح!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=10000)

# ==============================
# Telegram Bot Commands
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id, username, first_name = user.id, user.username, user.first_name
    add_user(user_id, username, first_name)

    keyboard = [["💰 رصيدي", "📢 جمع النقاط"], ["➕ إنشاء طلب متابعين"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"👋 أهلاً {first_name}! اختر من القائمة:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.message.from_user
    user_id = user.id

    # --- عرض الرصيد ---
    if text == "💰 رصيدي":
        balance = get_balance(user_id)
        await update.message.reply_text(f"💰 رصيدك الحالي: {balance} نقطة")

    # --- جمع النقاط ---
    elif text == "📢 جمع النقاط":
        request = get_requests()
        if not request:
            await update.message.reply_text("📭 لا توجد طلبات حالياً. ارجع لاحقاً.")
            return

        req_id, req_user_id, link, order_type, quantity = request
        if req_user_id == user_id:
            await update.message.reply_text("⚠️ لا يمكنك تنفيذ طلبك الخاص.")
            return

        await update.message.reply_text(
            f"🔗 رابط الطلب: {link}\n📌 نوع الطلب: {order_type}\n📈 الكمية: {quantity}\n\n"
            f"✅ بعد إتمام المتابعة، أرسل كلمة (تم) للحصول على نقاطك."
        )
        context.user_data["current_request"] = req_id

    # --- تأكيد المتابعة ---
    elif text.lower() == "تم":
        if "current_request" not in context.user_data:
            await update.message.reply_text("⚠️ لا يوجد طلب مرتبط بك حالياً.")
            return

        req_id = context.user_data["current_request"]
        mark_request_done(req_id)
        update_balance(user_id, 5)
        del context.user_data["current_request"]
        await update.message.reply_text("🎉 تم تأكيد المتابعة! حصلت على +5 نقاط.")

    # --- إنشاء طلب ---
    elif text == "➕ إنشاء طلب متابعين":
        context.user_data["creating_order"] = True
        keyboard = [["50", "100", "200"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("📸 اختر الكمية المطلوبة:", reply_markup=reply_markup)

    elif "creating_order" in context.user_data and text.isdigit():
        context.user_data["quantity"] = int(text)
        await update.message.reply_text("🔗 أرسل الآن رابط حسابك في إنستغرام:")
        context.user_data["awaiting_link"] = True
        del context.user_data["creating_order"]

    elif "awaiting_link" in context.user_data:
        link = text
        quantity = context.user_data.get("quantity", 0)
        cost = quantity // 10 * 5  # كل 10 متابعين = 5 نقاط

        balance = get_balance(user_id)
        if balance < cost:
            await update.message.reply_text("❌ رصيدك غير كافٍ لإنشاء هذا الطلب.")
            context.user_data.clear()
            return

        add_request(user_id, link, "انستغرام", quantity)
        update_balance(user_id, -cost)
        await update.message.reply_text(f"✅ تم إنشاء طلبك بنجاح!\n🔗 {link}\n📈 الكمية: {quantity}\n💸 تم خصم {cost} نقطة.")
        context.user_data.clear()

    else:
        await update.message.reply_text("🤖 استخدم الأزرار أدناه للتفاعل مع البوت.")

# ==============================
# تشغيل Telegram Bot
# ==============================
def run_bot():
    init_db()

    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.run_polling())

# ==============================
# تشغيل Flask + Bot
# ==============================
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
