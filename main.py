import os
import asyncio
from pyrogram import Client, filters, idle
from aiohttp import web
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("🚀 Starting Bot...")

# Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
PORT = int(os.environ.get("PORT", 8080))

if not all([BOT_TOKEN, API_ID, API_HASH]):
    print("❌ Check environment variables")
    exit(1)

# Create client
app = Client(
    "mybot", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN,
    workers=3
)

# Message handlers - SIMPLE AND DIRECT
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    print(f"📨 Received /start from {message.from_user.id}")
    await message.reply_text(
        "🎉 **Bot is Working!**\n\n"
        "✅ **All systems operational**\n\n"
        "**Commands:**\n"
        "/start - Start bot\n"
        "/help - Help guide\n"
        "/test - Test bot\n\n"
        "📁 **Send any file to test!**"
    )

@app.on_message(filters.command("help") & filters.private)
async def help_handler(client, message):
    print(f"📨 Received /help from {message.from_user.id}")
    await message.reply_text(
        "🤖 **Help Guide**\n\n"
        "**Available Commands:**\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/test - Test the bot\n\n"
        "**How to use:**\n"
        "Just send me any file or use the commands above!"
    )

@app.on_message(filters.command("test") & filters.private)
async def test_handler(client, message):
    print(f"📨 Received /test from {message.from_user.id}")
    await message.reply_text("✅ **Test Successful!** Bot is responding.")

@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def file_handler(client, message):
    print(f"📁 Received file from {message.from_user.id}")
    file_type = "File"
    if message.document:
        file_type = "Document"
    elif message.video:
        file_type = "Video"
    elif message.audio:
        file_type = "Audio"
    elif message.photo:
        file_type = "Photo"
    
    await message.reply_text(f"📁 **{file_type} Received!**\n\n✅ Bot is working perfectly!")

@app.on_message(filters.private & filters.text)
async def text_handler(client, message):
    if not message.text.startswith('/'):
        print(f"📝 Received text from {message.from_user.id}: {message.text}")
        await message.reply_text(
            "🤖 **Send me files or use commands!**\n\n"
            "Use /help to see available commands."
        )

async def health_check(request):
    return web.Response(text="🤖 Bot is running!")

async def start_web_server():
    """Start HTTP server for health checks"""
    web_app = web.Application()
    web_app.router.add_get('/', health_check)
    web_app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    print(f"🌐 Health check server running on port {PORT}")
    return runner

async def main():
    # Start health check server
    runner = await start_web_server()
    
    try:
        # Start Telegram bot
        print("🔗 Connecting to Telegram...")
        await app.start()
        
        bot_info = await app.get_me()
        print(f"✅ Bot started: @{bot_info.username}")
        print("📝 Bot is now listening for messages...")
        print("💡 Test with: /start, /test, or send any file")
        
        # Use idle to keep bot running and listening
        await idle()
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        print("🛑 Shutting down...")
        await app.stop()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
