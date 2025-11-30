import os
import time
import asyncio
from pyrogram import Client, filters

print("🚀 SUPER SIMPLE BOT - Starting...")
time.sleep(30)  # Wait 30 seconds

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

app = Client("simple_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🎉 **SUCCESS!** Bot is working with time sync fix! ✅")

async def main():
    await app.start()
    print("✅ BOT IS RUNNING!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
