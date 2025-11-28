import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import time

# Configuration
def get_env_var(key, default="", required=False):
    value = os.environ.get(key, default)
    if required and not value:
        raise ValueError(f"Environment variable {key} is required!")
    return value

def get_int_env(key, default=0):
    value = os.environ.get(key, str(default))
    try:
        return int(value) if value else default
    except ValueError:
        raise ValueError(f"{key} must be an integer!")

# Required variables
BOT_TOKEN = get_env_var("BOT_TOKEN", required=True)
API_ID = get_int_env("API_ID", required=True)
API_HASH = get_env_var("API_HASH", required=True)

# Optional variables
OWNER_ID = get_int_env("OWNER_ID", 7945670631)
DB_URL = get_env_var("DB_URL", "")
DB_NAME = get_env_var("DB_NAME", "file_store_bot")

# Channels
CHANNEL_ID = get_int_env("CHANNEL_ID", -1002491097530)

def get_channel_id(env_var, default=0):
    value = os.environ.get(env_var)
    if not value or value == "0":
        return None
    try:
        return int(value)
    except ValueError:
        return None

FORCE_SUB_CHANNEL_1 = get_channel_id("FORCE_SUB_CHANNEL_1", -1002491097530)
FORCE_SUB_CHANNEL_2 = get_channel_id("FORCE_SUB_CHANNEL_2")
FORCE_SUB_CHANNEL_3 = get_channel_id("FORCE_SUB_CHANNEL_3")
FORCE_SUB_CHANNEL_4 = get_channel_id("FORCE_SUB_CHANNEL_4")

# Other settings
START_PIC = get_env_var("START_PIC", "https://files.catbox.moe/ufzpkn.jpg")
F_PIC = get_env_var("FORCE_PIC", "https://files.catbox.moe/ufzpkn.jpg")
FILE_AUTO_DELETE = get_int_env("FILE_AUTO_DELETE", 1800)

# Admins setup
try:
    ADMINS = [OWNER_ID]
    admins_str = os.environ.get("ADMINS", "")
    if admins_str:
        additional_admins = [int(x.strip()) for x in admins_str.split() if x.strip()]
        ADMINS.extend(additional_admins)
    ADMINS = list(dict.fromkeys(ADMINS))
except ValueError:
    raise Exception("Admins list contains invalid integers!")

# Bot messages
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION")
PROTECT_CONTENT = os.environ.get('PROTECT_CONTENT', "False").lower() == "true"
DISABLE_CHANNEL_BUTTON = os.environ.get('DISABLE_CHANNEL_BUTTON', "False").lower() == "true"

START_MSG = get_env_var("START_MESSAGE", "<b>Hi {first}! 🤖 I am an Advanced File Store Bot</b>")
FORCE_MSG = get_env_var("FORCE_SUB_MESSAGE", "📢 Please join our channels first to use this bot!")

# Logging setup
LOG_FILE_NAME = "filesharingbot.txt"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(LOG_FILE_NAME, maxBytes=50000000, backupCount=10),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

# Database connection
if DB_URL:
    mongo_client = MongoClient(DB_URL)
    db = mongo_client[DB_NAME]
    users_collection = db["users"]
    files_collection = db["files"]
else:
    db = None
    users_collection = None
    files_collection = None

# Pyrogram Client
app = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")
)

# Bot start time for uptime
start_time = time.time()

async def is_subscribed(user_id: int) -> bool:
    """Check if user is subscribed to required channels"""
    if not any([FORCE_SUB_CHANNEL_1, FORCE_SUB_CHANNEL_2, FORCE_SUB_CHANNEL_3, FORCE_SUB_CHANNEL_4]):
        return True
    
    try:
        # Check each channel
        for channel_id in [FORCE_SUB_CHANNEL_1, FORCE_SUB_CHANNEL_2, FORCE_SUB_CHANNEL_3, FORCE_SUB_CHANNEL_4]:
            if channel_id:
                member = await app.get_chat_member(channel_id, user_id)
                if member.status in ["left", "kicked", "banned"]:
                    return False
        return True
    except Exception as e:
        LOGGER(__name__).error(f"Error checking subscription: {e}")
        return False

def get_uptime():
    """Get bot uptime"""
    seconds = int(time.time() - start_time)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

# Start command handler
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    # Check subscription
    if not await is_subscribed(user_id):
        # User not subscribed - show force subscribe message
        buttons = []
        
        if FORCE_SUB_CHANNEL_1:
            buttons.append([InlineKeyboardButton("📢 Channel 1", url=f"https://t.me/{await get_channel_username(FORCE_SUB_CHANNEL_1)}")])
        if FORCE_SUB_CHANNEL_2:
            buttons.append([InlineKeyboardButton("📢 Channel 2", url=f"https://t.me/{await get_channel_username(FORCE_SUB_CHANNEL_2)}")])
        if FORCE_SUB_CHANNEL_3:
            buttons.append([InlineKeyboardButton("📢 Channel 3", url=f"https://t.me/{await get_channel_username(FORCE_SUB_CHANNEL_3)}")])
        if FORCE_SUB_CHANNEL_4:
            buttons.append([InlineKeyboardButton("📢 Channel 4", url=f"https://t.me/{await get_channel_username(FORCE_SUB_CHANNEL_4)}")])
        
        buttons.append([InlineKeyboardButton("🔄 Try Again", callback_data="check_sub")])
        
        await message.reply_photo(
            photo=F_PIC,
            caption=FORCE_MSG.format(first=first_name),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    
    # User is subscribed - show start message
    await message.reply_photo(
        photo=START_PIC,
        caption=START_MSG.format(first=first_name),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📢 Updates Channel", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")
        ]])
    )

async def get_channel_username(channel_id: int):
    """Get channel username from ID"""
    try:
        chat = await app.get_chat(channel_id)
        return chat.username if chat.username else "unknown"
    except:
        return "unknown"

# Stats command for owner
@app.on_message(filters.command("stats") & filters.user(ADMINS))
async def stats_command(client: Client, message: Message):
    uptime = get_uptime()
    stats_text = f"<b>🤖 Bot Statistics</b>\n\n"
    stats_text += f"<b>⏰ Uptime:</b> {uptime}\n"
    stats_text += f"<b>👥 Total Users:</b> {users_collection.count_documents({}) if users_collection else 'N/A'}\n"
    stats_text += f"<b>📁 Total Files:</b> {files_collection.count_documents({}) if files_collection else 'N/A'}\n"
    stats_text += f"<b>🛠️ Admin Count:</b> {len(ADMINS)}"
    
    await message.reply_text(stats_text)

# Broadcast command for owner
@app.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def broadcast_command(client: Client, message: Message):
    if not users_collection:
        await message.reply_text("❌ Database not configured!")
        return
    
    if len(message.command) < 2:
        await message.reply_text("Usage: /broadcast <message>")
        return
    
    broadcast_msg = message.text.split(None, 1)[1]
    users = users_collection.find()
    total = users_collection.count_documents({})
    success = 0
    failed = 0
    
    broadcast_msg = await message.reply_text("📢 Starting broadcast...")
    
    for user in users:
        try:
            await client.send_message(user["user_id"], broadcast_msg)
            success += 1
        except:
            failed += 1
        await asyncio.sleep(0.1)  # Prevent flooding
    
    await broadcast_msg.edit_text(
        f"📊 Broadcast Completed!\n\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}\n"
        f"� Total: {total}"
    )

# Start the bot
async def main():
    await app.start()
    LOGGER(__name__).info("🤖 File Store Bot Started Successfully!")
    print("""
    ╔══════════════════════╗
    ║   FILE STORE BOT     ║
    ║      Started!        ║
    ╚══════════════════════╝
    """)
    await idle()
    await app.stop()

if __name__ == "__main__":
    # Validate configuration
    required_vars = {
        "BOT_TOKEN": BOT_TOKEN,
        "API_ID": API_ID,
        "API_HASH": API_HASH
    }
    
    for name, value in required_vars.items():
        if not value:
            raise ValueError(f"❌ {name} is required!")
    
    print("✅ Configuration validated successfully!")
    print(f"🤖 Bot is starting...")
    
    # Run the bot
    asyncio.run(main())
