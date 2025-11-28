import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode, ChatMemberStatus
from pymongo import MongoClient
import time
from datetime import datetime
import sys

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Configuration with debug
def get_env_var(key, default="", required=False):
    value = os.environ.get(key, default)
    logger.info(f"🔧 Loading {key}: {value if not 'TOKEN' in key and not 'HASH' in key else '***'}")
    if required and not value:
        raise ValueError(f"❌ {key} is required!")
    return value

def get_int_env(key, default=0):
    value = os.environ.get(key, str(default))
    try:
        return int(value) if value else default
    except ValueError:
        raise ValueError(f"❌ {key} must be an integer!")

# Required variables
try:
    BOT_TOKEN = get_env_var("BOT_TOKEN", required=True)
    API_ID = get_int_env("API_ID")
    API_HASH = get_env_var("API_HASH", required=True)
    
    if not API_ID:
        raise ValueError("❌ API_ID is required!")
        
    logger.info("✅ Required environment variables loaded successfully!")
except Exception as e:
    logger.error(f"❌ Failed to load required variables: {e}")
    sys.exit(1)

# Optional variables
PORT = int(os.environ.get("PORT", "8080"))
OWNER_ID = get_int_env("OWNER_ID", 7945670631)
DB_URL = get_env_var("DB_URL", "")
DB_NAME = get_env_var("DB_NAME", "file_store_bot")

# Your Channel IDs
CHANNEL_ID = get_int_env("CHANNEL_ID", -1002491097530)  # Main channel
FORCE_SUB_CHANNEL_1 = get_int_env("FORCE_SUB_CHANNEL_1", -1003200571840)  # Force sub channel
FORCE_SUB_CHANNEL_2 = get_int_env("FORCE_SUB_CHANNEL_2", 0)
FORCE_SUB_CHANNEL_3 = get_int_env("FORCE_SUB_CHANNEL_3", 0)
FORCE_SUB_CHANNEL_4 = get_int_env("FORCE_SUB_CHANNEL_4", 0)

# Other settings
START_PIC = get_env_var("START_PIC", "https://files.catbox.moe/ufzpkn.jpg")
F_PIC = get_env_var("FORCE_PIC", "https://files.catbox.moe/ufzpkn.jpg")

# Admins
try:
    ADMINS = [OWNER_ID]
    admins_str = os.environ.get("ADMINS", "")
    if admins_str:
        additional_admins = [int(x.strip()) for x in admins_str.split() if x.strip()]
        ADMINS.extend(additional_admins)
    ADMINS = list(dict.fromkeys(ADMINS))
    logger.info(f"👥 Admins loaded: {ADMINS}")
except ValueError as e:
    logger.error(f"❌ Error loading admins: {e}")
    ADMINS = [OWNER_ID]

# Bot messages
START_MSG = get_env_var("START_MESSAGE", "🤖 <b>Hello {first}!</b>\n\nI am a File Store Bot. Send me any file and I'll store it in the channel!")
FORCE_MSG = get_env_var("FORCE_SUB_MESSAGE", "❌ <b>Access Denied</b>\n\nYou must join our channel to use this bot!")

# Database
if DB_URL and DB_URL.strip():
    try:
        mongo_client = MongoClient(DB_URL)
        db = mongo_client[DB_NAME]
        users_collection = db["users"]
        files_collection = db["files"]
        logger.info("✅ MongoDB connected successfully!")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        db = None
        users_collection = None
        files_collection = None
else:
    logger.warning("⚠️ No MongoDB URL provided, running without database")
    db = None
    users_collection = None
    files_collection = None

# Pyrogram Client with better error handling
try:
    app = Client(
        "file_store_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        sleep_threshold=60,
        workers=3
    )
    logger.info("✅ Pyrogram client created successfully!")
except Exception as e:
    logger.error(f"❌ Failed to create Pyrogram client: {e}")
    sys.exit(1)

start_time = time.time()

def get_uptime():
    seconds = int(time.time() - start_time)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

async def is_subscribed(user_id: int):
    """Check if user is subscribed to force sub channels"""
    force_channels = [FORCE_SUB_CHANNEL_1, FORCE_SUB_CHANNEL_2, FORCE_SUB_CHANNEL_3, FORCE_SUB_CHANNEL_4]
    active_channels = [channel for channel in force_channels if channel]
    
    if not active_channels:
        logger.info(f"✅ No force sub channels, allowing user {user_id}")
        return True
    
    logger.info(f"🔍 Checking subscription for user {user_id} in channels: {active_channels}")
    
    for channel_id in active_channels:
        try:
            member = await app.get_chat_member(channel_id, user_id)
            logger.info(f"📋 User {user_id} status in channel {channel_id}: {member.status}")
            
            if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
                logger.info(f"❌ User {user_id} not subscribed to channel {channel_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking user {user_id} in channel {channel_id}: {e}")
            return False
    
    logger.info(f"✅ User {user_id} is subscribed to all channels")
    return True

# Start command handler
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    logger.info(f"🚀 /start command from user {user_id} ({first_name})")
    
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
            logger.info(f"💾 User {user_id} saved to database")
        except Exception as e:
            logger.error(f"❌ Error saving user {user_id} to database: {e}")
    
    # Check subscription
    is_sub = await is_subscribed(user_id)
    logger.info(f"📊 Subscription check for {user_id}: {is_sub}")
    
    if not is_sub:
        # Force subscribe message
        buttons = []
        if FORCE_SUB_CHANNEL_1:
            try:
                chat = await app.get_chat(FORCE_SUB_CHANNEL_1)
                username = chat.username
                invite_link = f"https://t.me/{username}" if username else None
                
                if invite_link:
                    buttons.append([InlineKeyboardButton("📢 Join Channel", url=invite_link)])
                else:
                    logger.warning("⚠️ Force sub channel has no username or invite link")
            except Exception as e:
                logger.error(f"❌ Error getting channel info: {e}")
        
        buttons.append([InlineKeyboardButton("🔄 Try Again", callback_data="check_sub")])
        
        try:
            await message.reply_photo(
                photo=F_PIC,
                caption=FORCE_MSG.format(first=first_name),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            logger.info(f"📨 Sent force sub message to user {user_id}")
        except Exception as e:
            logger.error(f"❌ Error sending force sub message: {e}")
            await message.reply_text(FORCE_MSG.format(first=first_name))
        return
    
    # User is subscribed
    try:
        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(first=first_name),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")
            ], [
                InlineKeyboardButton("📊 Stats", callback_data="stats"),
                InlineKeyboardButton("ℹ️ About", callback_data="about")
            ]])
        )
        logger.info(f"✅ Sent welcome message to user {user_id}")
    except Exception as e:
        logger.error(f"❌ Error sending welcome message: {e}")
        await message.reply_text(START_MSG.format(first=first_name))

# Callback handlers
@app.on_callback_query(filters.regex("check_sub"))
async def check_sub_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    logger.info(f"🔄 Check sub callback from user {user_id}")
    
    if await is_subscribed(user_id):
        await query.message.edit_caption(
            caption=START_MSG.format(first=query.from_user.first_name),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")
            ], [
                InlineKeyboardButton("📊 Stats", callback_data="stats"),
                InlineKeyboardButton("ℹ️ About", callback_data="about")
            ]])
        )
    else:
        await query.answer("❌ Please join the channel first!", show_alert=True)

@app.on_callback_query(filters.regex("stats"))
async def stats_callback(client: Client, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Admin access required!", show_alert=True)
        return
    
    uptime = get_uptime()
    total_users = users_collection.count_documents({}) if users_collection else "N/A"
    total_files = files_collection.count_documents({}) if files_collection else "N/A"
    
    stats_text = f"""
<b>📊 Bot Statistics</b>

⏰ Uptime: <code>{uptime}</code>
👥 Total Users: <code>{total_users}</code>
📁 Total Files: <code>{total_files}</code>
🛠️ Admins: <code>{len(ADMINS)}</code>
📢 Force Sub: <code>{FORCE_SUB_CHANNEL_1}</code>
"""
    await query.message.edit_caption(
        caption=stats_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="back_to_start")
        ]])
    )

@app.on_callback_query(filters.regex("about"))
async def about_callback(client: Client, query: CallbackQuery):
    about_text = """
<b>🤖 About File Store Bot</b>

A powerful Telegram bot to store and share files through channels.

<b>Features:</b>
• File storage in channels
• Force subscribe system
• User management
• Broadcast messages

<b>Developer:</b> @Rakibul51624
"""
    await query.message.edit_caption(
        caption=about_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="back_to_start")
        ]])
    )

@app.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client: Client, query: CallbackQuery):
    await query.message.edit_caption(
        caption=START_MSG.format(first=query.from_user.first_name),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")
        ], [
            InlineKeyboardButton("📊 Stats", callback_data="stats"),
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ]])
    )

# Admin commands
@app.on_message(filters.command("stats") & filters.private & filters.user(ADMINS))
async def stats_command(client: Client, message: Message):
    uptime = get_uptime()
    total_users = users_collection.count_documents({}) if users_collection else "N/A"
    
    stats_text = f"""
<b>🤖 Bot Stats</b>

⏰ Uptime: {uptime}
👥 Users: {total_users}
🛠️ Admins: {len(ADMINS)}
"""
    await message.reply_text(stats_text)

@app.on_message(filters.command("broadcast") & filters.private & filters.user(ADMINS))
async def broadcast_command(client: Client, message: Message):
    if not users_collection:
        await message.reply_text("❌ Database not connected!")
        return
    
    if len(message.command) < 2:
        await message.reply_text("Usage: /broadcast <message>")
        return
    
    broadcast_msg = message.text.split(None, 1)[1]
    total_users = users_collection.count_documents({})
    
    if total_users == 0:
        await message.reply_text("❌ No users found!")
        return
    
    progress = await message.reply_text(f"📢 Broadcasting to {total_users} users...")
    
    success = 0
    failed = 0
    
    for user in users_collection.find():
        try:
            await client.send_message(user["user_id"], broadcast_msg)
            success += 1
        except:
            failed += 1
        await asyncio.sleep(0.1)
    
    await progress.edit_text(
        f"✅ Broadcast Complete!\n\n"
        f"✓ Success: {success}\n"
        f"✗ Failed: {failed}\n"
        f"📊 Total: {total_users}"
    )

# File handler for admins
@app.on_message(filters.private & filters.user(ADMINS) & (filters.document | filters.video | filters.audio | filters.photo))
async def store_file(client: Client, message: Message):
    logger.info(f"📁 File received from admin {message.from_user.id}")
    
    if not CHANNEL_ID:
        await message.reply_text("❌ CHANNEL_ID not set!")
        return
    
    try:
        # Forward to channel
        forwarded = await message.forward(CHANNEL_ID)
        logger.info(f"✅ File forwarded to channel {CHANNEL_ID}, message ID: {forwarded.id}")
        
        # Save to database
        if files_collection:
            files_collection.insert_one({
                "file_id": forwarded.id,
                "admin_id": message.from_user.id,
                "date": datetime.now()
            })
        
        await message.reply_text("✅ File stored successfully in channel!")
        
    except Exception as e:
        logger.error(f"❌ Error storing file: {e}")
        await message.reply_text(f"❌ Error: {e}")

# Health check server
async def start_web_server():
    try:
        from aiohttp import web
        
        async def health_check(request):
            return web.Response(text="🤖 Bot is running!")
        
        app_web = web.Application()
        app_web.router.add_get('/', health_check)
        app_web.router.add_get('/health', health_check)
        
        runner = web.AppRunner(app_web)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        logger.info(f"🌐 Health server started on port {PORT}")
        return runner
    except Exception as e:
        logger.warning(f"⚠️ Web server not started: {e}")
        return None

# Main function
async def main():
    logger.info("🚀 Starting File Store Bot...")
    
    # Validate config
    logger.info("🔍 Configuration Summary:")
    logger.info(f"   Bot Token: {'✓' if BOT_TOKEN else '✗'}")
    logger.info(f"   API ID: {'✓' if API_ID else '✗'}")
    logger.info(f"   API Hash: {'✓' if API_HASH else '✗'}")
    logger.info(f"   Main Channel: {CHANNEL_ID}")
    logger.info(f"   Force Sub: {FORCE_SUB_CHANNEL_1}")
    logger.info(f"   Owner: {OWNER_ID}")
    
    # Start web server
    web_runner = await start_web_server()
    
    try:
        await app.start()
        bot = await app.get_me()
        logger.info(f"✅ Bot @{bot.username} started successfully!")
        
        print(f"""
╔══════════════════════╗
║     BOT IS LIVE!     ║
╠══════════════════════╣
║ 🤖 @{bot.username}
║ 👤 Owner: {OWNER_ID}
║ 📢 Main: {CHANNEL_ID}
║ 🔔 Force: {FORCE_SUB_CHANNEL_1}
║ 🌐 Port: {PORT}
╚══════════════════════╝
        """)
        
        await idle()
        
    except Exception as e:
        logger.error(f"❌ Bot startup failed: {e}")
    finally:
        if web_runner:
            await web_runner.cleanup()
        await app.stop()
        logger.info("👋 Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())
