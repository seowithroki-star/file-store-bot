import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode, ChatMemberStatus
from pymongo import MongoClient
import time
from datetime import datetime
import sys

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

# Koyeb uses PORT environment variable
PORT = int(os.environ.get("PORT", 8080))

# Optional variables
OWNER_ID = get_int_env("OWNER_ID", 7945670631)
DB_URL = get_env_var("DB_URL", "")
DB_NAME = get_env_var("DB_NAME", "file_store_bot")

# Channels
CHANNEL_ID = get_int_env("CHANNEL_ID", -1003094784222)

def get_channel_id(env_var, default=0):
    value = os.environ.get(env_var)
    if not value or value == "0":
        return None
    try:
        return int(value)
    except ValueError:
        return None

FORCE_SUB_CHANNEL_1 = get_channel_id("FORCE_SUB_CHANNEL_1", -1003056865925)
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
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Database connection
if DB_URL and DB_URL.strip():
    try:
        mongo_client = MongoClient(DB_URL)
        db = mongo_client[DB_NAME]
        users_collection = db["users"]
        files_collection = db["files"]
        logger.info("✅ Connected to MongoDB")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        db = None
        users_collection = None
        files_collection = None
else:
    logger.info("ℹ️ No MongoDB URL provided, running without database")
    db = None
    users_collection = None
    files_collection = None

# Pyrogram Client
app = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=60,
    workers=3
)

# Bot start time for uptime
start_time = time.time()

async def is_subscribed(user_id: int) -> bool:
    """Check if user is subscribed to required channels"""
    if not any([FORCE_SUB_CHANNEL_1, FORCE_SUB_CHANNEL_2, FORCE_SUB_CHANNEL_3, FORCE_SUB_CHANNEL_4]):
        return True
    
    try:
        for channel_id in [FORCE_SUB_CHANNEL_1, FORCE_SUB_CHANNEL_2, FORCE_SUB_CHANNEL_3, FORCE_SUB_CHANNEL_4]:
            if channel_id:
                try:
                    member = await app.get_chat_member(channel_id, user_id)
                    if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
                        return False
                except Exception as e:
                    logger.error(f"Error checking channel {channel_id}: {e}")
                    return False
        return True
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
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

async def get_channel_username(channel_id: int):
    """Get channel username from ID"""
    try:
        chat = await app.get_chat(channel_id)
        return chat.username if chat.username else "unknown"
    except Exception as e:
        logger.error(f"Error getting channel username: {e}")
        return "unknown"

# Start command handler
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    # Save user to database
    if users_collection:
        try:
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "first_name": first_name,
                    "username": message.from_user.username,
                    "last_used": datetime.now()
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error saving user to database: {e}")
    
    # Check subscription
    if not await is_subscribed(user_id):
        buttons = []
        
        if FORCE_SUB_CHANNEL_1:
            channel_username = await get_channel_username(FORCE_SUB_CHANNEL_1)
            buttons.append([InlineKeyboardButton("📢 Channel 1", url=f"https://t.me/{channel_username}")])
        if FORCE_SUB_CHANNEL_2:
            channel_username = await get_channel_username(FORCE_SUB_CHANNEL_2)
            buttons.append([InlineKeyboardButton("📢 Channel 2", url=f"https://t.me/{channel_username}")])
        
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
        ], [
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ]])
    )

# Callback query handlers
@app.on_callback_query(filters.regex("check_sub"))
async def check_sub_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    
    if await is_subscribed(user_id):
        await query.message.edit_caption(
            caption=START_MSG.format(first=first_name),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Updates Channel", url="https://t.me/RHmovieHDOFFICIAL"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")
            ], [
                InlineKeyboardButton("ℹ️ About", callback_data="about")
            ]])
        )
    else:
        await query.answer("❌ Please join all channels first!", show_alert=True)

@app.on_callback_query(filters.regex("about"))
async def about_callback(client: Client, query: CallbackQuery):
    about_text = """
<b>🤖 About This Bot</b>

<b>📝 Language:</b> Python 3
<b>📚 Framework:</b> Pyrogram
<b>🗄️ Database:</b> MongoDB
<b>🚀 Host:</b> Koyeb

<b>👨‍💻 Developer:</b> @Rakibul51624
<b>📢 Channel:</b> @RHmovieHDOFFICIAL

This bot can store files and forward them to users."""
    
    await query.message.edit_caption(
        caption=about_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="back_to_start")
        ]])
    )

@app.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client: Client, query: CallbackQuery):
    first_name = query.from_user.first_name
    await query.message.edit_caption(
        caption=START_MSG.format(first=first_name),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📢 Updates Channel", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")
        ], [
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ]])
    )

# Stats command for owner
@app.on_message(filters.command("stats") & filters.private & filters.user(ADMINS))
async def stats_command(client: Client, message: Message):
    uptime = get_uptime()
    total_users = users_collection.count_documents({}) if users_collection else "N/A"
    total_files = files_collection.count_documents({}) if files_collection else "N/A"
    
    stats_text = f"""
<b>🤖 Bot Statistics</b>

<b>⏰ Uptime:</b> {uptime}
<b>👥 Total Users:</b> {total_users}
<b>📁 Total Files:</b> {total_files}
<b>🛠️ Admin Count:</b> {len(ADMINS)}
<b>🌐 Port:</b> {PORT}
"""
    
    await message.reply_text(stats_text)

# Simple HTTP server for health checks
async def start_web_server():
    try:
        from aiohttp import web
        app_web = web.Application()
        
        async def health_check(request):
            return web.Response(text="🤖 Bot is running!")
        
        app_web.router.add_get('/', health_check)
        app_web.router.add_get('/health', health_check)
        
        runner = web.AppRunner(app_web)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        logger.info(f"🌐 Health check server running on port {PORT}")
        return runner
    except ImportError:
        logger.warning("aiohttp not installed, health checks disabled")
        return None
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
        return None

# Start the bot
async def main():
    logger.info("🚀 Starting File Store Bot...")
    
    # Validate configuration
    required_vars = {
        "BOT_TOKEN": BOT_TOKEN,
        "API_ID": API_ID,
        "API_HASH": API_HASH
    }
    
    for name, value in required_vars.items():
        if not value:
            logger.error(f"❌ {name} is required!")
            sys.exit(1)
    
    logger.info("✅ Configuration validated successfully!")
    
    # Start web server for health checks
    web_runner = await start_web_server()
    
    try:
        await app.start()
        bot_info = await app.get_me()
        logger.info(f"🤖 Bot Started Successfully! @{bot_info.username}")
        
        print(f"""
╔══════════════════════╗
║   FILE STORE BOT     ║
║      Started!        ║
╠══════════════════════╣
║ 🤖 Bot: @{bot_info.username}
║ 👤 Owner: {OWNER_ID}
║ 👥 Admins: {len(ADMINS)}
║ 🌐 Port: {PORT}
║ 🚀 Host: Koyeb
╚══════════════════════╝
        """)
        
        # Keep the bot running
        await idle()
        
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
    finally:
        # Cleanup
        if web_runner:
            await web_runner.cleanup()
        await app.stop()
        logger.info("👋 Bot stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
