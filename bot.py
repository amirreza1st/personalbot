import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import logging
import asyncio

# تنظیم لاگ برای دیباگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# خواندن توکن و ID از متغیرهای محیطی
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# دکمه‌ها برای /start
def start_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("About Me", callback_data='about'),
            InlineKeyboardButton("Hidden Chat", callback_data='hidden')
        ],
        [
            InlineKeyboardButton("’A N O R A ‚", url="https://t.me/yourchannel"),  # لینک کانالت رو جایگزین کن
            InlineKeyboardButton("Gift", callback_data='gift')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# تابع /start
async def start(update, context):
    await update.message.reply_text(
        "به ربات من خوش آمدید! 🌟\n"
        "اینجا می‌تونید از امکانات جذاب استفاده کنید! 😎",
        reply_markup=start_keyboard()
    )

# تابع About Me
async def about(update, context):
    query = update.callback_query
    await query.answer()
    about_text = (
        "سلام! من امیررضا هستم، یک توسعه‌دهنده خلاق و عاشق تکنولوژی! 🌌\n"
        "اینجا هستم تا با شما ایده‌ها و پروژه‌هام رو به اشتراک بذارم. همراهم باشید! 🚀\n"
        "برای دنبال کردنم، روی دکمه زیر کلیک کنید!"
    )
    keyboard = [[InlineKeyboardButton("Instagram", url="https://instagram.com/yourusername")]]  # لینک اینستاگرامت رو جایگزین کن
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(about_text, reply_markup=reply_markup)

# تابع Hidden Chat
async def hidden(update, context):
    query = update.callback_query
    await query.answer()
    hidden_text = "از الان هر پیامی که بفرستید، به صورت ناشناس برای امیررضا ارسال می‌شود! 🤫\nبرای بازگشت به منوی اصلی، روی دکمه زیر کلیک کنید."
    keyboard = [[InlineKeyboardButton("بازگشت", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(hidden_text, reply_markup=reply_markup)
    user_id = query.from_user.id
    context.user_data[user_id] = {'mode': 'hidden'}

# مدیریت پیام‌های ناشناس
async def handle_hidden_message(update, context):
    user_id = update.message.from_user.id
    if context.user_data.get(user_id, {}).get('mode') == 'hidden':
        username = update.message.from_user.username or "بدون نام کاربری"
        full_name = update.message.from_user.full_name
        message_text = update.message.text
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"پیام ناشناس از {full_name} (@{username}) - ID: {user_id}:\n{message_text}\n\n"
                 f"گزینه‌ها: /reply_{user_id} برای پاسخ | /ignore برای نادیده گرفتن | /block_{user_id} برای بلاک"
        )
        await update.message.reply_text("پیام شما با موفقیت ارسال شد! منتظر پاسخ باشید...")

# پاسخ به ادمین
async def handle_admin_commands(update, context):
    message = update.message.text
    if message.startswith('/reply_'):
        user_id = int(message.split('_')[1])
        if user_id != int(ADMIN_ID):
            reply_text = message.replace(f'/reply_{user_id} ', '')
            await context.bot.send_message(chat_id=user_id, text=f"پاسخ از امیررضا: {reply_text}")
            await update.message.reply_text("پاسخ شما ارسال شد!")
    elif message == '/ignore':
        await update.message.reply_text("پیام نادیده گرفته شد.")
    elif message.startswith('/block_'):
        user_id = int(message.split('_')[1])
        await context.bot.ban_chat_member(chat_id=ADMIN_ID, user_id=user_id)
        await update.message.reply_text(f"کاربر با ID {user_id} بلاک شد.")

# تابع Gift
async def gift(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("لطفاً به من یک گیفت تلگرامی یا استارز هدیه بده! 🎁\nبرای ارسال گیفت، روی آیکون هدیه در چت کلیک کن.")

# بازگشت به منوی اصلی
async def back(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if context.user_data.get(user_id, {}).get('mode') == 'hidden':
        del context.user_data[user_id]['mode']
    await query.edit_message_text(
        "به منوی اصلی بازگشتید! 🌟",
        reply_markup=start_keyboard()
    )

# تابع اصلی با مدیریت خطاها
def main():
    if not TOKEN or not ADMIN_ID:
        raise ValueError("لطفاً BOT_TOKEN و ADMIN_ID را در متغیرهای محیطی تنظیم کنید!")
    application = Application.builder().token(TOKEN).build()

    # افزودن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(about, pattern='^about$'))
    application.add_handler(CallbackQueryHandler(hidden, pattern='^hidden$'))
    application.add_handler(CallbackQueryHandler(gift, pattern='^gift$'))
    application.add_handler(CallbackQueryHandler(back, pattern='^back$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hidden_message))
    application.add_handler(MessageHandler(filters.Regex('^/(reply_|block_|ignore)$'), handle_admin_commands))

    # اجرای ربات با مدیریت خطاها
    try:
        application.run_polling(allowed_updates=Application.ALL_UPDATE_TYPES)
    except Exception as e:
        logger.error(f"خطا در اجرای ربات: {e}")

if __name__ == "__main__":
    main()
