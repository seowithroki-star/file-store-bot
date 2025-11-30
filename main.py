import os
import time
import asyncio
from pyrogram import Client, filters

print("🚀 Starting Bot with Ultimate Time Fix...")
time.sleep(20)  # Wait 20 seconds for time sync

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"] 
BOT_TOKEN = os.environ["BOT_TOKEN"]

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🎉 **BOT IS WORKING!** Time sync fixed! ✅")

async def main():
    await app.start()
    print("🤖 Bot Started Successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
