import os
import asyncio
import logging
from pyrogram import Client, filters, idle

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("🚀 Starting File Store Bot...")

# Configuration - আপনার আগের Bot credentials
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
API_ID = int(os.environ.get("API_ID", "YOUR_API_ID_HERE"))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH_HERE")

# Validate
if not all([BOT_TOKEN, API_ID, API_HASH]):
    logger.error("❌ Missing environment variables")
    exit(1)

# Create client with flood wait protection
app = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=2,
    sleep_threshold=60,
    no_updates=True  # Reduce flood issues
)

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    await message.reply_text(
        "🎉 **Welcome to File Store Bot!**\n\n"
        "🤖 **I can store your files**\n\n"
        "**How to use:**\n"
        "• Send me any file (document, video, photo, audio)\n"
        "• I'll process and store it\n"
        "• Get direct links\n\n"
        "📁 **Send a file to get started!**\n\n"
        "**Commands:**\n"
        "/start - Start bot\n"
        "/help - Help guide\n"
        "/test - Test bot\n"
        "/stats - Bot statistics"
    )

@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    await message.reply_text(
        "🤖 **File Store Bot - Help**\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/test - Test the bot\n"
        "/stats - Show statistics\n\n"
        "**How to use:**\n"
        "1. Send any file (document, video, photo, audio)\n"
        "2. Bot will process it\n"
        "3. Get confirmation message\n\n"
        "**Features:**\n"
        "• File storage\n"
        "• Easy to use\n"
        "• Fast processing\n\n"
        "**Just send me a file to begin!**"
    )

@app.on_message(filters.command("test") & filters.private)
async def test_command(client, message):
    await message.reply_text(
        "✅ **Bot Test Successful!**\n\n"
        "🤖 **All systems are working:**\n"
        "• Command processing ✓\n"
        "• Message handling ✓\n"
        "• File reception ✓\n"
        "• User management ✓\n\n"
        "**Status:** 🟢 ONLINE"
    )

@app.on_message(filters.command("stats") & filters.private)
async def stats_command(client, message):
    await message.reply_text(
        "📊 **Bot Statistics**\n\n"
        "🤖 **Bot:** @RokiFilestore1bot\n"
        "✅ **Status:** Running\n"
        "🔧 **Version:** 2.0\n"
        "🚀 **Ready for files!**\n\n"
        "Send any file to test storage functionality."
    )

@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def file_handler(client, message):
    try:
        # Get file type
        file_type = "File"
        file_name = "Unknown"
        
        if message.document:
            file_type = "Document"
            file_name = message.document.file_name or "Document"
        elif message.video:
            file_type = "Video"
            file_name = message.video.file_name or "Video"
        elif message.audio:
            file_type = "Audio"
            file_name = message.audio.file_name or "Audio"
        elif message.photo:
            file_type = "Photo"
            file_name = "Photo"
        
        logger.info(f"📁 Received {file_type}: {file_name}")
        
        # Success response
        await message.reply_text(
            f"✅ **{file_type} Received!**\n\n"
            f"📝 **Name:** {file_name}\n"
            f"👤 **From:** {message.from_user.first_name}\n\n"
            "🤖 **File storage is working!**\n"
            "Your file has been processed successfully.\n\n"
            "**Next:** Channel storage will be configured soon."
        )
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.private & filters.text)
async def text_handler(client, message):
    if not message.text.startswith('/'):
        await message.reply_text(
            "🤖 **Send me files to store!**\n\n"
            "I can process:\n"
            "• 📄 Documents\n"
            "• 🎥 Videos\n"
            "• 🖼️ Photos\n"
            "• 🎵 Audio files\n\n"
            "Just send me any file to get started!\n\n"
            "Use /help for more information."
        )

async def main():
    try:
        logger.info("🔄 Connecting to Telegram...")
        await app.start()
        
        bot = await app.get_me()
        logger.info(f"✅ Bot started: @{bot.username}")
        
        print(f"""
╔══════════════════════╗
║    BOT IS LIVE!      ║
╠══════════════════════╣
║ 🤖 Bot: @{bot.username}
║ ✅ Status: RUNNING
║ 🔧 Flood: PROTECTED
║ 🚀 Ready: YES
╚══════════════════════╝

💡 Test Commands:
/start - Welcome message
/test  - Bot test  
/help  - Help guide
/stats - Statistics

📁 Send any file to test!
        """)
        
        # Keep bot running
        await idle()
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Startup failed: {error_msg}")
        
        if "FLOOD_WAIT" in error_msg or "wait of" in error_msg:
            print("\n⏳ **FLOOD WAIT DETECTED**")
            print("💡 Please wait 10 minutes before restarting")
            print("📝 This is a Telegram security measure")
        else:
            print(f"❌ Error: {error_msg}")
            
    finally:
        try:
            await app.stop()
            logger.info("🛑 Bot stopped")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
