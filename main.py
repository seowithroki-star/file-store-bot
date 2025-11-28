import os
import asyncio
from pyrogram import Client, filters
from aiohttp import web

print("🤖 Starting Bot - Guaranteed Working...")

# Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
PORT = int(os.environ.get("PORT", 8080))

if not all([BOT_TOKEN, API_ID, API_HASH]):
    print("❌ Missing environment variables")
    exit(1)

# Create Pyrogram client
app = Client(
    "file_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=3
)

# Message Handlers
@app.on_message(filters.command("start"))
async def start_command(client, message):
    print(f"✅ Received /start from {message.from_user.id}")
    await message.reply_text(
        "🎉 **Bot is Working!**\n\n"
        "✅ **Message received and processed**\n\n"
        "**Test Commands:**\n"
        "/start - This message\n"
        "/test - Test response\n"
        "/help - Help guide\n\n"
        "📁 **Send any file to test file handling**"
    )

@app.on_message(filters.command("test"))
async def test_command(client, message):
    print(f"✅ Received /test from {message.from_user.id}")
    await message.reply_text("✅ **Test Successful!** Bot is responding to commands.")

@app.on_message(filters.command("help"))
async def help_command(client, message):
    print(f"✅ Received /help from {message.from_user.id}")
    await message.reply_text(
        "🤖 **Help Guide**\n\n"
        "**Commands:**\n"
        "/start - Start bot\n"
        "/test - Test bot\n"
        "/help - This message\n\n"
        "**Just send me a file or use commands!**"
    )

@app.on_message(filters.document | filters.video | filters.audio | filters.photo)
async def file_handler(client, message):
    print(f"✅ Received file from {message.from_user.id}")
    file_type = "File"
    if message.document:
        file_type = "Document"
    elif message.video:
        file_type = "Video"
    elif message.audio:
        file_type = "Audio"
    elif message.photo:
        file_type = "Photo"
    
    await message.reply_text(f"📁 **{file_type} Received!**\n\n✅ File handling is working!")

@app.on_message(filters.text)
async def text_handler(client, message):
    if not message.text.startswith('/'):
        print(f"✅ Received text from {message.from_user.id}")
        await message.reply_text(
            "🤖 **Send me commands or files!**\n\n"
            "Use:\n"
            "/start - Start bot\n"
            "/test - Test bot\n"
            "/help - Help guide\n\n"
            "Or send any file to test."
        )

# Health check server
async def health_check(request):
    return web.Response(text="🤖 Bot is running and ready!")

async def start_web_server():
    web_app = web.Application()
    web_app.router.add_get('/', health_check)
    web_app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    print(f"🌐 Health server running on port {PORT}")
    return runner

async def main():
    # Start web server
    runner = await start_web_server()
    
    try:
        # Start bot
        print("🔗 Connecting to Telegram...")
        await app.start()
        
        bot = await app.get_me()
        print(f"✅ Bot started: @{bot.username}")
        print("📡 Listening for messages...")
        print("💡 Test with: /start, /test, or send any file")
        
        # Keep running
        await asyncio.Future()  # Run forever
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await app.stop()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
