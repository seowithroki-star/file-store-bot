import os
import asyncio
import time
import logging
from pyrogram import Client, filters
from aiohttp import web

print("🚀 Starting Bot with PORT 10000...")

# Time sync fix
time.sleep(20)

# Configuration
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
PORT = 10000  # Render uses 10000

print(f"🔧 Using PORT: {PORT}")

# Pyrogram client
app = Client("file_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Health check server
async def health_handler(request):
    return web.Response(text="🤖 Bot is running on PORT 10000!")

async def start_web_server():
    """Start web server for Render health checks"""
    web_app = web.Application()
    web_app.router.add_get('/', health_handler)
    web_app.router.add_get('/health', health_handler)
    web_app.router.add_get('/ping', health_handler)
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    
    # Use PORT 10000
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"🌐 Health server running on port {PORT}")
    return runner

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply(
        "✅ **Bot is Working!**\n\n"
        "🚀 PORT: 10000\n"
        "📁 File Store Bot\n\n"
        "**Commands:**\n"
        "/start - Start bot\n"
        "/help - Help guide\n"
        "/ping - Test response"
    )

@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    await message.reply("📖 This bot can store files and share them!")

@app.on_message(filters.command("ping"))
async def ping(client, message):
    await message.reply("🏓 Pong! Bot is active!")

@app.on_message(filters.text & filters.private)
async def echo(client, message):
    if not message.text.startswith('/'):
        await message.reply(f"💬 You said: {message.text}")

async def main():
    try:
        # Start web server first
        web_runner = await start_web_server()
        
        # Then start Pyrogram
        await app.start()
        print("✅ Bot Started Successfully on PORT 10000!")
        
        # Keep running
        while True:
            await asyncio.sleep(3600)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
