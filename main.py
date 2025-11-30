import os
import asyncio
import time
from pyrogram import Client, filters

print("🟢 Starting Bot...")

# Time sync fix - wait before starting
time.sleep(10)

# Environment variables
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

# Pyrogram client
app = Client(
    "file_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start(client, message):
    print(f"🎯 Start from: {message.from_user.id}")
    await message.reply("✅ **বট কাজ করছে!**\n\nআমি সক্রিয় আছি! 🚀")

@app.on_message(filters.command("test"))
async def test(client, message):
    await message.reply("🔧 **টেস্ট সফল!** বট সম্পূর্ণ সক্রিয়।")

@app.on_message(filters.text & filters.private)
async def echo(client, message):
    if not message.text.startswith('/'):
        await message.reply(f"📝 আপনি বলেছেন: {message.text}")

async def main():
    try:
        await app.start()
        bot_info = await app.get_me()
        print(f"🤖 Bot Started: @{bot_info.username}")
        print("✅ বট প্রস্তুত এবং রেসপন্স দিচ্ছে!")
        
        # Keep running
        while True:
            await asyncio.sleep(3600)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("বট বন্ধ করা হয়েছে")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
