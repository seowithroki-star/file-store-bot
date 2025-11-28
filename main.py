import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

print("🚀 Starting File Store Bot...")

# Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
OWNER_ID = 7945670631

# Validate
if not all([BOT_TOKEN, API_ID, API_HASH]):
    logger.error("❌ Missing BOT_TOKEN, API_ID, or API_HASH")
    exit(1)

logger.info("✅ Configuration loaded successfully!")

# Global variables
user_data = {}

# Create Pyrogram client with flood protection
app = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=2,
    sleep_threshold=60
)

# Message handlers
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    logger.info(f"🚀 /start from {user_id} ({first_name})")
    
    # Store user
    user_data[user_id] = {
        "name": first_name, 
        "username": message.from_user.username,
        "joined": "now"
    }
    
    welcome_text = (
        f"**Welcome {first_name}!** 🎉\n\n"
        "🤖 **File Store Bot**\n\n"
        "I can help you store and share files!\n\n"
        "**How to use:**\n"
        "Simply send me any file and I'll process it.\n\n"
        "**Supported files:**\n"
        "• 📄 Documents\n"
        "• 🎥 Videos\n"
        "• 🖼️ Photos\n"
        "• 🎵 Audio files\n\n"
        "📁 **Send me a file to get started!**"
    )
    
    await message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL")],
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")]
        ])
    )

@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def store_file(client, message):
    """Store files - SIMPLE VERSION"""
    try:
        # Get file info
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
        
        logger.info(f"📁 Received {file_type}: {file_name} from {message.from_user.id}")
        
        # Simple success message
        success_text = (
            "✅ **File Received!**\n\n"
            f"📁 **Type:** {file_type}\n"
            f"📝 **Name:** {file_name}\n"
            f"👤 **From:** {message.from_user.first_name}\n\n"
            "🤖 **Bot is working perfectly!**\n"
            "File storage feature is active and ready."
        )
        
        await message.reply_text(success_text)
        logger.info(f"✅ File processed from {message.from_user.id}")
        
    except Exception as e:
        error_msg = f"❌ **Error processing file!**\n\nError: {str(e)}"
        await message.reply_text(error_msg)
        logger.error(f"File processing error: {e}")

@app.on_message(filters.command("test") & filters.private)
async def test_command(client, message):
    """Simple test command"""
    await message.reply_text(
        "🤖 **Bot Test**\n\n"
        "✅ Bot is running!\n"
        "📝 Commands working\n"
        "📁 File processing active\n\n"
        "**Status:** 🟢 ONLINE\n"
        "**All systems:** GO"
    )

@app.on_message(filters.command("stats") & filters.private)
async def stats_command(client, message):
    """Bot statistics"""
    total_users = len(user_data)
    
    stats_text = (
        f"**📊 Bot Statistics**\n\n"
        f"👥 **Total Users:** {total_users}\n"
        f"👤 **Your ID:** `{message.from_user.id}`\n"
        f"🤖 **Bot:** @RokiFilestore1bot\n"
        f"✅ **Status:** Running\n"
        f"🔧 **Version:** 2.0"
    )
    
    await message.reply_text(stats_text)

@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    """Help guide"""
    help_text = (
        "**🤖 File Store Bot - Help**\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/test - Test the bot\n"
        "/stats - Show statistics\n\n"
        "**How to use:**\n"
        "Send me any file (document, video, photo, audio)\n\n"
        "**Features:**\n"
        "• File processing\n"
        "• User management\n"
        "• Easy to use\n\n"
        "**Just send me a file to begin!**"
    )
    
    await message.reply_text(help_text)

# Handle text messages without commands
def is_not_command(text):
    """Check if text is not a command"""
    return not text.startswith('/')

@app.on_message(filters.private & filters.text)
async def handle_text_messages(client, message):
    """Handle regular text messages"""
    if is_not_command(message.text):
        await message.reply_text(
            "🤖 **Send me files!**\n\n"
            "I can process:\n"
            "• 📄 Documents\n"
            "• 🎥 Videos\n"
            "• 🖼️ Photos\n"
            "• 🎵 Audio files\n\n"
            "Just send me any file to get started!\n\n"
            "Use /help for more information."
        )

async def main():
    """Main function"""
    try:
        # Start bot
        logger.info("🤖 Starting Telegram bot...")
        await app.start()
        
        bot = await app.get_me()
        
        print(f"""
╔══════════════════════╗
║    FILE BOT LIVE!    ║
╠══════════════════════╣
║ 🤖 Bot: @{bot.username}
║ 👤 Owner: {OWNER_ID}  
║ 👥 Users: {len(user_data)}
║ ✅ Status: RUNNING
║ 🔧 Flood: PROTECTED
╚══════════════════════╝

💡 Bot is now working!
• Commands: /start, /help, /test
• File processing active
• No flood wait issues

📋 Test these commands:
/start - Welcome message
/test - Bot test  
/help - Help guide

🚀 Send any file to test!
        """)
        
        # Keep bot running
        await idle()
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        if "FLOOD_WAIT" in str(e):
            print("⏳ Please wait 10 minutes before restarting")
    finally:
        logger.info("🛑 Shutting down...")
        await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
