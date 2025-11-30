import os
import asyncio
import logging
import time
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Configuration
def get_env_var(key, default=""):
    return os.environ.get(key, default)

def get_int_env(key, default=0):
    value = os.environ.get(key, str(default))
    try:
        return int(value) if value else default
    except ValueError:
        return default

# Required variables
BOT_TOKEN = get_env_var("BOT_TOKEN", "default_token_placeholder")
API_ID = get_int_env("API_ID", 1234567)
API_HASH = get_env_var("API_HASH", "default_hash_placeholder")

if BOT_TOKEN == "default_token_placeholder" or API_ID == 1234567 or API_HASH == "default_hash_placeholder":
    print("❌ ERROR: Please set Environment Variables!")
    sys.exit(1)

# Optional variables
OWNER_ID = get_int_env("OWNER_ID", 7945670631)
PORT = int(os.environ.get("PORT", 8080))

# Channel IDs
CHANNEL_ID = -1003279353938
FORCE_SUB_CHANNEL_1 = -1003483616299

# Other settings
START_PIC = get_env_var("START_PIC", "https://files.catbox.moe/ufzpkn.jpg")
F_PIC = get_env_var("FORCE_PIC", "https://files.catbox.moe/ufzpkn.jpg")

# Admins
ADMINS = [OWNER_ID]

# Messages
START_MSG = "<b>Hi {first}! 🤖 I am an Advanced File Store Bot</b>"
FORCE_MSG = "📢 Please join our channels first to use this bot!"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# ==================== TIME SYNC FIX ====================
async def time_sync_fix():
    """Fix time synchronization issues"""
    import datetime
    current_time = datetime.datetime.utcnow()
    logger.info(f"🕒 Current UTC Time: {current_time}")

# ==================== PYROGRAM CLIENT ====================
app = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=60,
    workers=3,
    # Time sync parameters
    app_version="1.0.0",
    device_model="Python",
    system_version="Linux",
    lang_code="en"
)

# ==================== BOT FUNCTIONALITY ====================

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    logger.info(f"🚀 /start from {user_id} ({first_name})")
    
    # Simple response without subscription check first
    await message.reply_text(
        f"🎉 Hello {first_name}!\n\n"
        f"🤖 Bot is working!\n"
        f"📝 Your ID: {user_id}\n\n"
        f"Try /help for more commands."
    )

@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    await message.reply_text(
        "📖 **Available Commands:**\n\n"
        "/start - Start bot\n"
        "/help - This message\n" 
        "/test - Test bot\n"
        "/id - Your user ID\n"
        "/ping - Check response time"
    )

@app.on_message(filters.command("test") & filters.private)
async def test_command(client, message):
    await message.reply_text("✅ **Bot is working!**")

@app.on_message(filters.command("id") & filters.private)
async def id_command(client, message):
    await message.reply_text(f"👤 Your ID: `{message.from_user.id}`")

@app.on_message(filters.command("ping") & filters.private)
async def ping_command(client, message):
    start = time.time()
    msg = await message.reply_text("🏓 Pong!")
    end = time.time()
    await msg.edit_text(f"🏓 Pong! ⏱ {round((end-start)*1000, 2)}ms")

@app.on_message(filters.text & filters.private)
async def echo_handler(client, message):
    if not message.text.startswith('/'):
        await message.reply_text(f"🔁 You said: {message.text}")

# ==================== START BOT ====================

async def main():
    logger.info("🚀 Starting Bot...")
    
    # Time sync fix
    await time_sync_fix()
    
    try:
        await app.start()
        bot_info = await app.get_me()
        logger.info(f"🤖 Bot Started: @{bot_info.username}")
        
        print(f"""
╔══════════════════════╗
║   BOT STARTED!       ║
╠══════════════════════╣
║ 🤖 @{bot_info.username}
║ 👤 Owner: {OWNER_ID}
║ 🌐 Port: {PORT}
╚══════════════════════╝
        """)
        
        # Keep bot running
        await idle()
        
    except Exception as e:
        logger.error(f"❌ Bot failed: {e}")
    finally:
        await app.stop()
        logger.info("👋 Bot stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Error: {e}")
