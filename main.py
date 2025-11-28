import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

print("🚀 Starting Bot with python-telegram-bot...")

# Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🎉 **Welcome {user.first_name}!**\n\n"
        "🤖 **Bot is Working Perfectly!**\n\n"
        "**Commands:**\n"
        "/start - Start bot\n"
        "/test - Test bot\n"
        "/help - Help guide\n\n"
        "📁 **Send any file to test!**"
    )
    logger.info(f"✅ Responded to /start from {user.id}")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ **Test Successful!** Bot is responding.")
    logger.info(f"✅ Responded to /test from {update.effective_user.id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Help Guide**\n\n"
        "**Commands:**\n"
        "/start - Start bot\n"
        "/test - Test bot\n"
        "/help - This message\n\n"
        "**Just send me files or use commands!**"
    )

async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document or update.message.video or update.message.audio or update.message.photo
    file_type = "File"
    
    if update.message.document:
        file_type = "Document"
    elif update.message.video:
        file_type = "Video"
    elif update.message.audio:
        file_type = "Audio"
    elif update.message.photo:
        file_type = "Photo"
    
    await update.message.reply_text(f"📁 **{file_type} Received!**\n\n✅ File handling working!")
    logger.info(f"✅ Processed {file_type} from {update.effective_user.id}")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Send me files or use /help for commands")
    logger.info(f"✅ Responded to text from {update.effective_user.id}")

def main():
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO | filters.AUDIO | filters.PHOTO, file_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Start bot
    print("✅ Bot starting with python-telegram-bot...")
    application.run_polling()

if __name__ == '__main__':
    main()
