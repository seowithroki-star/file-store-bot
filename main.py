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

# ==================== ALL COMMANDS ====================

# Start command
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
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
            InlineKeyboardButton("📖 Help", callback_data="help")
        ]])
    )

# Help command
@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    help_text = """
<b>📖 Help Guide</b>

<b>Available Commands:</b>
/start - Start the bot
/help - Show this help message  
/stats - Bot statistics (Admins only)
/id - Get your user ID
/broadcast - Broadcast message (Admins only)

<b>For Users:</b>
• Join our channel to access the bot
• Search files using inline mode

<b>For Admins:</b>
• Send any file to store it in channel
• Use /broadcast to send messages
• Use /stats to check bot status
"""
    
    await message.reply_text(help_text)

# ID command - Get user ID
@app.on_message(filters.command("id") & filters.private)
async def id_command(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    await message.reply_text(
        f"<b>👤 Your Information</b>\n\n"
        f"<b>First Name:</b> {first_name}\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n"
        f"<b>Username:</b> @{message.from_user.username if message.from_user.username else 'N/A'}"
    )

# Stats command for admin
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
<b>🚀 Host:</b> Koyeb
"""
    
    await message.reply_text(stats_text)

# Broadcast command for admin
@app.on_message(filters.command("broadcast") & filters.private & filters.user(ADMINS))
async def broadcast_command(client, message):
    if len(message.command) < 2:
        await message.reply_text(
            "📢 <b>Broadcast Usage:</b>\n\n"
            "<code>/broadcast your message here</code>\n\n"
            "Example:\n"
            "<code>/broadcast Hello everyone! New update available.</code>"
        )
        return
    
    broadcast_text = message.text.split(' ', 1)[1]
    confirm_text = f"""
<b>📢 Broadcast Preview:</b>

{broadcast_text}

<b>Total Admins:</b> {len(ADMINS)}

<b>Confirm broadcast?</b>
"""
    
    await message.reply_text(
        confirm_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Yes, Send", callback_data=f"broadcast_confirm_{message.id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")
        ]])
    )

# Ping command - Check bot response time
@app.on_message(filters.command("ping") & filters.private)
async def ping_command(client, message):
    start_time = time.time()
    msg = await message.reply_text("🏓 Pong!")
    end_time = time.time()
    
    ping_time = round((end_time - start_time) * 1000, 2)
    
    await msg.edit_text(f"🏓 <b>Pong!</b>\n\n⏱️ <b>Response Time:</b> {ping_time}ms")

# Test command - Emergency testing
@app.on_message(filters.command("test") & filters.private)
async def test_command(client, message):
    """Emergency test command"""
    logger.info(f"🎯 TEST COMMAND RECEIVED FROM: {message.from_user.id}")
    await message.reply_text("✅ <b>Bot is working perfectly!</b>\n\nAll systems operational! 🚀")

# Echo all messages for testing
@app.on_message(filters.text & filters.private)
async def echo_all_messages(client, message):
    """Echo all text messages for testing"""
    user_id = message.from_user.id
    text = message.text
    
    # Ignore commands
    if text.startswith('/'):
        return
        
    logger.info(f"📩 Message from {user_id}: {text}")
    await message.reply_text(f"🔁 <b>Echo:</b> {text}")

# ==================== CALLBACK HANDLERS ====================

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
                InlineKeyboardButton("ℹ️ About", callback_data="about"),
                InlineKeyboardButton("📖 Help", callback_data="help")
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

<b>🌟 Features:</b>
• File Storage System
• Force Subscription
• Broadcast Messages
• Multi Admin Support

This bot can store files and forward them to users."""
    
    await query.message.edit_caption(
        caption=about_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="back_to_start"),
            InlineKeyboardButton("📖 Help", callback_data="help")
        ]])
    )

@app.on_callback_query(filters.regex("help"))
async def help_callback(client, query):
    help_text = """
<b>📖 Help Guide</b>

<b>Available Commands:</b>
/start - Start the bot
/help - Show this help message  
/stats - Bot statistics (Admins only)
/id - Get your user ID
/ping - Check bot response time
/broadcast - Broadcast message (Admins only)

<b>For Users:</b>
• Join our channel to access the bot
• Use /id to get your user ID

<b>For Admins:</b>
• Send any file to store it in channel
• Use /broadcast to send messages
• Use /stats to check bot status
"""
    
    await query.message.edit_caption(
        caption=help_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="back_to_start"),
            InlineKeyboardButton("ℹ️ About", callback_data="about")
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
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
            InlineKeyboardButton("📖 Help", callback_data="help")
        ]])
    )

# Broadcast confirmation handler
@app.on_callback_query(filters.regex("broadcast_confirm_"))
async def broadcast_confirm(client, query):
    message_id = int(query.data.split("_")[2])
    original_message = await app.get_messages(query.message.chat.id, message_id)
    broadcast_text = original_message.text.split(' ', 1)[1]
    
    await query.message.edit_text("📢 Sending broadcast to admins...")
    
    success = 0
    failed = 0
    
    for admin_id in ADMINS:
        try:
            await app.send_message(admin_id, f"📢 <b>Broadcast Message:</b>\n\n{broadcast_text}")
            success += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {admin_id}: {e}")
            failed += 1
    
    await query.message.edit_text(
        f"📊 <b>Broadcast Completed!</b>\n\n"
        f"✅ <b>Success:</b> {success}\n"
        f"❌ <b>Failed:</b> {failed}\n"
        f"👥 <b>Total Admins:</b> {len(ADMINS)}"
    )

@app.on_callback_query(filters.regex("broadcast_cancel"))
async def broadcast_cancel(client, query):
    await query.message.edit_text("❌ Broadcast cancelled.")

# ==================== FILE STORE FUNCTIONALITY ====================

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
            f"✅ <b>File stored successfully!</b>\n\n"
            f"📁 <b>File ID:</b> <code>{forwarded_msg.id}</code>\n"
            f"🔗 <b>Direct Link:</b> {file_link}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📂 View in Channel", url=file_link)
            ]])
        )
        
    except Exception as e:
        await message.reply_text(f"❌ Error storing file: {e}")
        logger.error(f"File storage error: {e}")

# ==================== UTILITY FUNCTIONS ====================

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

# ==================== WEB SERVER FOR HEALTH CHECKS ====================

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

# ==================== START THE BOT ====================

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
