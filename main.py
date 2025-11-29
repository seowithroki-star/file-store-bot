import os
import asyncio
from pyrogram import Client, filters

# Hardcode credentials for testing (Koyeb এ Environment Variables সেট করতে ভুলবেন না!)
API_ID = 1234567  # YOUR_ACTUAL_API_ID
API_HASH = "your_api_hash_here"  # YOUR_ACTUAL_API_HASH  
BOT_TOKEN = "your_bot_token_here"  # YOUR_ACTUAL_BOT_TOKEN

app = Client("test_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    print("🎯 START COMMAND RECEIVED!")
    await message.reply_text("🔥 BOT IS WORKING! Test successful!")

@app.on_message(filters.text & filters.private)
async def echo(client, message):
    print(f"📩 Received: {message.text}")
    await message.reply_text(f"You said: {message.text}")

async def main():
    await app.start()
    print("🤖 Bot is running...")
    
    # Get bot info
    bot_info = await app.get_me()
    print(f"🔗 Bot: https://t.me/{bot_info.username}")
    
    # Keep running
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
