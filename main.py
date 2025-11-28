import os
import asyncio
from pyrogram import Client, filters
from aiohttp import web
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🚀 Starting Bot with Health Checks...")

# Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
PORT = int(os.environ.get("PORT", 8080))

if not all([BOT_TOKEN, API_ID, API_HASH]):
    print("❌ Check environment variables")
    exit(1)

# Create client
app = Client("mybot", API_ID, API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🎉 **Bot is Working!**\n\nSend me any file or use /help")

@app.on_message(filters.command("help"))
async def help(client, message):
    await message.reply("🤖 **Commands:**\n/start - Start\n/help - Help\n/test - Test\n\n📁 Send any file to test")

@app.on_message(filters.command("test"))
async def test(client, message):
    await message.reply("✅ **Bot Test Successful!**")

@app.on_message(filters.document | filters.video | filters.audio | filters.photo)
async def files(client, message):
    await message.reply("📁 **File Received!**\n\n✅ Bot is working perfectly!")

@app.on_message(filters.text)
async def text(client, message):
    if not message.text.startswith('/'):
        await message.reply("🤖 Send me files or use /help")

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
    # Start health check server first
    runner = await start_web_server()
    
    try:
        # Start Telegram bot
        await app.start()
        me = await app.get_me()
        print(f"✅ @{me.username} is running!")
        
        # Keep both servers running
        await asyncio.Future()  # Run forever
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await app.stop()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
