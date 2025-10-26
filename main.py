import os
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ⚙️ إنشاء تطبيق Flask بسيط ليبقى السيرفر مستيقظًا (مطلوب لـ Render)
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "🤖 Telegram Bot is running on Render!"

# 🤖 دالة عند بدء المحادثة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["💰 رصيدي"]]  # الأزرار التي ستظهر للمستخدم
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "أهلاً بك! 👋\nاختر من القائمة أدناه:",
        reply_markup=reply_markup
    )

# 💬 دالة لمعالجة الرسائل النصية
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "💰 رصيدي":
        await update.message.reply_text("رصيدك الحالي هو: 0.00 💵")
    else:
        await update.message.reply_text("لم أفهم رسالتك 🤔")

# 🚀 نقطة الدخول الرئيسية للبوت
def main():
    bot_token = os.getenv("BOT_TOKEN")  # قراءة التوكن من بيئة Render

    if not bot_token:
        raise ValueError("❌ لم يتم العثور على متغير BOT_TOKEN في إعدادات Render!")

    app = ApplicationBuilder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    from threading import Thread

    # تشغيل Flask في Thread جانبي
    Thread(target=lambda: app_flask.run(host="0.0.0.0", port=10000)).start()

    # تشغيل البوت
    main()
