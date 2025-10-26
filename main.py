from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# دالة /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # لوحة الأزرار السفلية (reply keyboard)
    keyboard = [["💰 رصيدي"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    # زر مضمّن أسفل الرسالة (inline button)
    inline_keyboard = [
        [InlineKeyboardButton("• بدء التعليقات •", callback_data="start_comments")]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)

    # إرسال الرسالة مع الزرين
    await update.message.reply_text(
        "أهلاً بك! 👋\n"
        "اختر من القائمة أدناه أو اضغط على الزر لبدء التعليقات:",
        reply_markup=reply_markup
    )

    await update.message.reply_text(
        "⬇️ اضغط هنا:",
        reply_markup=inline_markup
    )

# دالة التعامل مع زر "💰 رصيدي"
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "💰 رصيدي":
        await update.message.reply_text("رصيدك الحالي هو: 0.00💵")
    else:
        await update.message.reply_text("لم أفهم رسالتك 🤔")

# دالة الضغط على زر "بدء التعليقات"
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # لتجنب رسالة "Loading..."
    if query.data == "start_comments":
        await query.message.reply_text("✅ تم بدء التعليقات! يمكنك الآن إرسال سؤالك.")

# إنشاء التطبيق
app = ApplicationBuilder().token("ضع_توكن_البوت_هنا").build()

# إضافة المعالجات
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button_callback))

print("🤖 Bot is running...")
app.run_polling()
