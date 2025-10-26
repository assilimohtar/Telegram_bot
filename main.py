from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# دالة start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("• بدء التعليقات •", callback_data="start_comments")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "مرحباً بك يا عزيزي في روبوت الأسئلة 👋\n"
        "- يمكنك طرح سؤالك للجمهور في أي وقت.\n"
        "- فقط اضغط على الزر أدناه لبدء التعليقات 💬",
        reply_markup=reply_markup
    )

# دالة معالجة الضغط على الزر
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # لتفادي الرسالة "loading..."
    
    if query.data == "start_comments":
        await query.message.reply_text("تم بدء التعليقات ✅ يمكنك الآن إرسال سؤالك.")

# إعداد التطبيق
app = ApplicationBuilder().token("ضع_توكن_البوت_هنا").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_callback))

print("🤖 Bot is running...")
app.run_polling()
