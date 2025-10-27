from telegram import (
    Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, filters
)
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
            balance REAL DEFAULT 0.0,
            joined_at TEXT
        )
    """)

    # جدول الطلبات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_number INTEGER,
            order_type TEXT,
            quantity TEXT,
            link TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


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


def add_order(user_id, order_number, order_type, quantity, link):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_orders (user_id, order_number, order_type, quantity, link, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, order_number, order_type, quantity, link, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_orders(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT order_type, link FROM user_orders WHERE user_id = ?", (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders

# ==============================
# Flask لإبقاء Render شغال
# ==============================
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "🤖 البوت يعمل بنجاح باستخدام SQLite!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=10000)

# ==============================
# محادثة إنشاء الطلب
# ==============================
ORDER_TYPE, QUANTITY, LINK, CONFIRM = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    add_user(user.id, user.username, user.first_name)

    keyboard = [["💰 رصيدي", "🎯 جمع النقاط"], ["📦 إنشاء طلب"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"أهلاً {user.first_name}! 👋\nاختر من القائمة:",
        reply_markup=reply_markup
    )


async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    orders = get_orders(user_id)

    if not orders:
        await update.message.reply_text("📭 لا توجد طلبات بعد.")
        return

    msg = "📋 طلباتك السابقة:\n\n"
    for order_type, link in orders:
        msg += f"🏷️ النوع: {order_type}\n🔗 الرابط: {link}\n\n"

    await update.message.reply_text(msg)


async def create_order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["طلب انستقرام"]]
    await update.message.reply_text(
        "📦 اختر نوع الطلب:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ORDER_TYPE


async def set_order_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_type"] = update.message.text
    keyboard = [["50", "100", "متابع"]]
    await update.message.reply_text(
        "🔢 اختر الكمية:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return QUANTITY


async def set_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quantity"] = update.message.text
    await update.message.reply_text("📎 أرسل رابط الحساب أو المنشور:", reply_markup=ReplyKeyboardRemove())
    return LINK


async def set_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["link"] = update.message.text
    order_type = context.user_data["order_type"]
    quantity = context.user_data["quantity"]
    link = context.user_data["link"]

    msg = f"🧾 تأكيد الطلب:\n\n🏷️ النوع: {order_type}\n🔢 الكمية: {quantity}\n🔗 الرابط: {link}\n\nهل تؤكد؟"
    keyboard = [["✅ تأكيد", "❌ إلغاء"]]
    await update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRM


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user

    if text == "✅ تأكيد":
        order_number = int(datetime.utcnow().timestamp())
        add_order(
            user.id,
            order_number,
            context.user_data["order_type"],
            context.user_data["quantity"],
            context.user_data["link"]
        )
        await update.message.reply_text("✅ تم إنشاء الطلب بنجاح!", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("❌ تم إلغاء العملية.", reply_markup=ReplyKeyboardRemove())

    await start(update, context)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية.", reply_markup=ReplyKeyboardRemove())
    await start(update, context)
    return ConversationHandler.END

# ==============================
# التعامل مع الرسائل العامة
# ==============================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "💰 رصيدي":
        balance = get_balance(user_id)
        await update.message.reply_text(f"💰 رصيدك الحالي هو: {balance:.2f}💵")
    elif text == "🎯 جمع النقاط":
        await show_orders(update, context)
    elif text == "📦 إنشاء طلب":
        await create_order_start(update, context)
    else:
        await update.message.reply_text("🤖 استخدم الأزرار أدناه.")


# ==============================
# تشغيل البوت
# ==============================
def run_bot():
    init_db()  # تأكد من وجود القاعدة والجداول

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📦 إنشاء طلب$"), create_order_start)],
        states={
            ORDER_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_order_type)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_quantity)],
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_link)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_order)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running with SQLite...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(app.run_polling())

# ==============================
# تشغيل Flask + Bot
# ==============================
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
