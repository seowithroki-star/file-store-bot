import os
import asyncio
import logging
from pyrogram import Client, filters

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")

# Validate
if not all([BOT_TOKEN, API_ID, API_HASH]):
    logger.error("❌ Missing environment variables")
    exit(1)

# Create client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text("🎉 **Welcome!**\n\nSend me any file to get started!")

@app.on_message(filters.command("help"))
async def help_handler(client, message):
    await message.reply_text("🤖 **Help**\n\nCommands:\n/start - Start bot\n/help - This message\n/test - Test bot")

@app.on_message(filters.command("test"))
async def test_handler(client, message):
    await message.reply_text("✅ **Bot is working!**")

@app.on_message(filters.document | filters.video | filters.audio | filters.photo)
async def file_handler(client, message):
    await message.reply_text("📁 **File received!**\n\n✅ Bot is working perfectly!")

@app.on_message(filters.text)
async def text_handler(client, message):
    if not message.text.startswith('/'):
        await message.reply_text("🤖 Send me files or use /help for commands")

async def main():
    await app.start()
    bot = await app.get_me()
    print(f"✅ Bot started: @{bot.username}")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
