import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
import time
from datetime import datetime
import sys

# ==================== CONFIGURATION FIRST ====================
def get_env_var(key, default=""):
    return os.environ.get(key, default)

def get_int_env(key, default=0):
    value = os.environ.get(key, str(default))
    try:
        return int(value) if value else default
    except ValueError:
        return default

# REQUIRED VARIABLES - DEFINE THEM AT THE TOP
BOT_TOKEN = get_env_var("BOT_TOKEN", "default_token_placeholder")
API_ID = get_int_env("API_ID", 1234567)  # Define here
API_HASH = get_env_var("API_HASH", "default_hash_placeholder")

# Check if using default values
if BOT_TOKEN == "default_token_placeholder" or API_ID == 1234567 or API_HASH == "default_hash_placeholder":
    print("❌ ERROR: Please set Environment Variables in Koyeb!")
    print("Required: API_ID, API_HASH, BOT_TOKEN")
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
admins_str = os.environ.get("ADMINS", "")
if admins_str:
    try:
        additional_admins = [int(x.strip()) for x in admins_str.split() if x.strip()]
        ADMINS.extend(additional_admins)
        ADMINS = list(dict.fromkeys(ADMINS))
    except ValueError:
        pass

# Messages
START_MSG = get_env_var("START_MESSAGE", "<b>Hi {first}! 🤖 I am an Advanced File Store Bot</b>")
FORCE_MSG = get_env_var("FORCE_SUB_MESSAGE", "📢 Please join our channels first to use this bot!")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# ==================== NOW CREATE CLIENT ====================
# NOW API_ID, API_HASH, BOT_TOKEN are defined
app = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=60,
    workers=3
)

# ==================== EMERGENCY DEBUGGING ====================
@app.on_message(filters.command("test") & filters.private)
async def test_command(client, message):
    """Emergency test command"""
    logger.info(f"🎯 TEST COMMAND RECEIVED FROM: {message.from_user.id}")
    await message.reply_text("🚨 BOT IS WORKING! Test successful!")

@app.on_message(filters.text & filters.private)
async def echo_all_messages(client, message):
    """Echo all text messages for testing"""
    user_id = message.from_user.id
    text = message.text
    logger.info(f"📩 Message from {user_id}: {text}")
    
    if text not in ['/start', '/test', '/stats']:
        await message.reply_text(f"Echo: {text}")

# ==================== REST OF YOUR CODE ====================
# Bot start time
start_time = time.time()

async def is_subscribed(user_id: int) -> bool:
    """Check if user is subscribed to required channels"""
    if not FORCE_SUB_CHANNEL_1:
        return True
    
    try:
        member = await app.get_chat_member(FORCE_SUB_CHANNEL_1, user_id)
        if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
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
async def start_command(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    logger.info(f"🚀 /start from {user_id} ({first_name})")
    
    # Check subscription
    if not await is_subscribed(user_id):
        buttons = []
        
        if FORCE_SUB_CHANNEL_1:
            channel_username = await get_channel_username(FORCE_SUB_CHANNEL_1)
            buttons.append([InlineKeyboardButton("📢 Join Our Channel", url=f"https://t.me/{channel_username}")])
        
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
async def check_sub_callback(client, query):
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
        await query.answer("❌ Please join our channel first!", show_alert=True)

@app.on_callback_query(filters.regex("about"))
async def about_callback(client, query):
    about_text = """
<b>🤖 About This Bot</b>

<b>📝 Language:</b> Python 3
<b>📚 Framework:</b> Pyrogram
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
async def back_to_start(client, query):
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
async def stats_command(client, message):
    uptime = get_uptime()
    
    stats_text = f"""
<b>🤖 Bot Statistics</b>

<b>⏰ Uptime:</b> {uptime}
<b>🛠️ Admin Count:</b> {len(ADMINS)}
<b>📢 Main Channel:</b> {CHANNEL_ID}
<b>🔔 Force Sub:</b> {FORCE_SUB_CHANNEL_1}
<b>🌐 Port:</b> {PORT}
"""
    
    await message.reply_text(stats_text)

# File store functionality
@app.on_message(filters.private & filters.user(ADMINS) & (filters.document | filters.video | filters.audio | filters.photo))
async def store_file(client, message):
    """Store files sent by admins"""
    if not CHANNEL_ID:
        await message.reply_text("❌ CHANNEL_ID not configured!")
        return
    
    try:
        # Forward file to channel
        forwarded_msg = await message.forward(CHANNEL_ID)
        
        file_link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{forwarded_msg.id}"
        
        await message.reply_text(
            f"✅ File stored successfully!\n\n"
            f"📁 File ID: `{forwarded_msg.id}`\n"
            f"🔗 Direct Link: {file_link}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📂 View in Channel", url=file_link)
            ]])
        )
        
    except Exception as e:
        await message.reply_text(f"❌ Error storing file: {e}")
        logger.error(f"File storage error: {e}")

# Simple HTTP server for health checks
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
    
    # Test print to verify environment variables
    logger.info(f"🔑 API_ID: {API_ID}")
    logger.info(f"🔑 BOT_TOKEN first 10 chars: {BOT_TOKEN[:10]}...")
    
    logger.info(f"📢 Main Channel: {CHANNEL_ID}")
    logger.info(f"🔔 Force Sub: {FORCE_SUB_CHANNEL_1}")
    
    # Start web server for health checks
    web_runner = await start_web_server()
    
    try:
        await app.start()
        bot_info = await app.get_me()
        logger.info(f"🤖 Bot Started Successfully! @{bot_info.username}")
        
        # Force print to verify bot is running
        print("🎉 BOT IS ACTUALLY RUNNING NOW!")
        print(f"🔗 Bot: https://t.me/{bot_info.username}")
        
        print(f"""
╔══════════════════════╗
║   FILE STORE BOT     ║
║      Started!        ║
╠══════════════════════╣
║ 🤖 Bot: @{bot_info.username}
║ 👤 Owner: {OWNER_ID}
║ 👥 Admins: {len(ADMINS)}
║ 📢 Main: {CHANNEL_ID}
║ 🔔 Force Sub: {FORCE_SUB_CHANNEL_1}
║ 🌐 Port: {PORT}
║ 🚀 Host: Koyeb
╚══════════════════════╝
        """)
        
        # Keep the bot running
        await idle()
        
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
        print(f"💥 CRITICAL ERROR: {e}")
    finally:
        # Cleanup
        if web_runner:
            await web_runner.cleanup()
        await app.stop()
        logger.info("👋 Bot stopped")

if __name__ == "__main__":
    print("🟢 Script started executing...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
