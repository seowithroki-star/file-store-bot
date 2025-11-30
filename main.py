import os
import asyncio
from pyrogram import Client, filters

print("🟢 Starting Bot...")

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

app = Client("test_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    print(f"🎯 Start from: {message.from_user.id}")
    await message.reply("🔥 **Bot is Working!** ✅")

@app.on_message(filters.text)
async def echo(client, message):
    if not message.text.startswith('/'):
        print(f"📩 Message: {message.text}")
        await message.reply(f"📢 You said: {message.text}")

async def main():
    await app.start()
    print("🤖 Bot Started Successfully!")
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
