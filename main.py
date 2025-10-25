from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# دالتك عند بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["💰 رصيدي"]]  # هنا نضع الأزرار (زر واحد الآن)
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("أهلاً بك! اختر من القائمة:", reply_markup=reply_markup)

# دالة التعامل مع زر "رصيدي"
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "💰 رصيدي":
        await update.message.reply_text("رصيدك الحالي هو: 0.00💵")
    else:
        await update.message.reply_text("لم أفهم رسالتك 🤔")

# إنشاء التطبيق
app = ApplicationBuilder().token("ضع_توكن_البوت_هنا").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Bot is running...")
app.run_polling()
