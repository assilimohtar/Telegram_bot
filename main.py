import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os

# ============== إعداد قاعدة البيانات ==============
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# حفظ مستخدم جديد إن لم يكن موجودًا
def register_user(user_id, username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
                  (user_id, username, 0))
        conn.commit()
    conn.close()

# جلب رصيد المستخدم
def get_balance(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

# ============== أوامر البوت ==============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username)
    keyboard = [["💰 رصيدي"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"أهلاً {user.first_name}! 👋\nاختر من القائمة:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if text == "💰 رصيدي":
        balance = get_balance(user.id)
        await update.message.reply_text(f"رصيدك الحالي هو: {balance:.2f} 💵")
    else:
        await update.message.reply_text("لم أفهم رسالتك 🤔")

# ============== تشغيل البوت ==============
def main():
    init_db()
    BOT_TOKEN = os.getenv("BOT_TOKEN")  # توكن البوت من Render
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running with SQLite database...")
    app.run_polling()

if __name__ == "__main__":
    main()
