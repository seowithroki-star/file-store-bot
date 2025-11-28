import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
import sys
from aiohttp import web

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
OWNER_ID = 7945670631

# Validate
if not all([BOT_TOKEN, API_ID, API_HASH]):
    logger.error("❌ Missing BOT_TOKEN, API_ID, or API_HASH")
    sys.exit(1)

logger.info("✅ Configuration loaded successfully!")

# Global variables
user_data = {}
app = None
runner = None

# Channel IDs - Will be detected automatically
CHANNEL_ID = None
FORCE_SUB_CHANNEL = None

async def start_web_server():
    """Start HTTP server for health checks"""
    global runner
    
    async def health_check(request):
        return web.Response(text="🤖 Bot is running!")
    
    web_app = web.Application()
    web_app.router.add_get('/', health_check)
    web_app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🌐 Health check server running on port {port}")
    return runner

async def detect_channels():
    """Detect and verify channels"""
    global CHANNEL_ID, FORCE_SUB_CHANNEL
    
    # Try to detect channels from common sources
    test_channels = [
        -1002491097530,  # Your main channel
        -1003200571840,  # Your force sub channel
    ]
    
    valid_channels = []
    
    for channel_id in test_channels:
        try:
            chat = await app.get_chat(channel_id)
            valid_channels.append((channel_id, chat.title))
            logger.info(f"✅ Found channel: {chat.title} ({channel_id})")
        except Exception as e:
            logger.warning(f"⚠️ Cannot access channel {channel_id}: {e}")
    
    # Set channels if found
    if len(valid_channels) >= 2:
        CHANNEL_ID = valid_channels[0][0]
        FORCE_SUB_CHANNEL = valid_channels[1][0]
        logger.info(f"📢 Main channel set to: {CHANNEL_ID}")
        logger.info(f"🔔 Force sub set to: {FORCE_SUB_CHANNEL}")
    elif len(valid_channels) >= 1:
        CHANNEL_ID = valid_channels[0][0]
        logger.info(f"📢 Main channel set to: {CHANNEL_ID}")
        logger.warning("⚠️ Only one channel found, force sub disabled")
    else:
        logger.error("❌ No valid channels found!")
        return False
    
    return True

async def check_subscription(user_id: int) -> bool:
    """Check if user is subscribed"""
    if not FORCE_SUB_CHANNEL:
        logger.info("ℹ️ No force sub channel configured")
        return True
    
    try:
        member = await app.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        is_subscribed = member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
        logger.info(f"🔍 User {user_id} subscription: {is_subscribed}")
        return is_subscribed
    except Exception as e:
        logger.error(f"❌ Subscription check failed: {e}")
        # If we can't check, allow access temporarily
        return True

async def setup_bot():
    """Setup bot handlers"""
    global app
    
    app = Client(
        "file_store_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        workers=3
    )

    @app.on_message(filters.command("start") & filters.private)
    async def start_command(client: Client, message: Message):
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        
        logger.info(f"🚀 /start from {user_id} ({first_name})")
        
        # Check subscription if force sub is configured
        if FORCE_SUB_CHANNEL:
            is_subscribed = await check_subscription(user_id)
            
            if not is_subscribed:
                try:
                    chat = await app.get_chat(FORCE_SUB_CHANNEL)
                    username = chat.username
                    buttons = []
                    
                    if username:
                        buttons.append([InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{username}")])
                    
                    buttons.append([InlineKeyboardButton("🔄 I've Joined", callback_data="check_sub")])
                    
                    await message.reply_text(
                        f"**Hello {first_name}!** 👋\n\n"
                        "📢 **Please join our channel to use this bot**\n\n"
                        "1. Click the button below to join\n"
                        "2. Then click 'I've Joined'",
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                    return
                except Exception as e:
                    logger.error(f"❌ Channel access error: {e}")
                    # Continue without force sub if channel not accessible
        
        # Welcome message (with or without force sub)
        if CHANNEL_ID:
            welcome_text = (
                f"**Welcome {first_name}!** 🎉\n\n"
                "✅ **You're all set!**\n\n"
                "🤖 **File Store Bot**\n"
                "• Store files in our channel\n"
                "• Share files easily\n"
                "• Fast and reliable\n\n"
                "📁 **Send me any file to get started!**"
            )
        else:
            welcome_text = (
                f"**Welcome {first_name}!** 🎉\n\n"
                "🤖 **File Store Bot**\n\n"
                "⚠️ **Note:** Channel configuration needed.\n"
                "Please contact admin to setup file storage."
            )
        
        await message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL")],
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")]
            ])
        )
        
        # Store user
        user_data[user_id] = {"name": first_name, "joined": "now"}

    @app.on_callback_query(filters.regex("check_sub"))
    async def check_sub_callback(client: Client, query):
        user_id = query.from_user.id
        
        if await check_subscription(user_id):
            await query.message.edit_text(
                f"**Welcome {query.from_user.first_name}!** 🎉\n\n"
                "✅ **Thank you for joining!**\n\n"
                "You can now use all bot features.\n"
                "Send me any file to store in our channel!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL")],
                    [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")]
                ])
            )
        else:
            await query.answer("❌ You haven't joined the channel yet!", show_alert=True)

    @app.on_message(filters.command("help"))
    async def help_command(client: Client, message: Message):
        await message.reply_text(
            "**Help Guide** 🤖\n\n"
            "**Commands:**\n"
            "/start - Start the bot\n"
            "/help - This message\n"
            "/stats - Bot stats (Admin)\n"
            "/channels - Channel info\n\n"
            "**How to use:**\n"
            "Send any file to store in our channel!"
        )

    @app.on_message(filters.command("stats") & filters.user(OWNER_ID))
    async def stats_command(client: Client, message: Message):
        total_users = len(user_data)
        channel_status = "✅ Configured" if CHANNEL_ID else "❌ Not configured"
        force_sub_status = "✅ Configured" if FORCE_SUB_CHANNEL else "❌ Not configured"
        
        await message.reply_text(
            f"**📊 Bot Statistics**\n\n"
            f"👥 Users: {total_users}\n"
            f"📢 Main Channel: {channel_status}\n"
            f"🔔 Force Sub: {force_sub_status}\n"
            f"👤 Owner: {OWNER_ID}\n"
            f"✅ Status: Running"
        )

    @app.on_message(filters.command("channels") & filters.user(OWNER_ID))
    async def channels_command(client: Client, message: Message):
        """Check channel status"""
        try:
            channel_info = []
            
            if CHANNEL_ID:
                try:
                    chat = await app.get_chat(CHANNEL_ID)
                    channel_info.append(f"✅ **Main Channel:** {chat.title} (ID: {CHANNEL_ID})")
                except Exception as e:
                    channel_info.append(f"❌ **Main Channel:** Cannot access (ID: {CHANNEL_ID}) - {e}")
            else:
                channel_info.append("❌ **Main Channel:** Not configured")
            
            if FORCE_SUB_CHANNEL:
                try:
                    chat = await app.get_chat(FORCE_SUB_CHANNEL)
                    channel_info.append(f"✅ **Force Sub:** {chat.title} (ID: {FORCE_SUB_CHANNEL})")
                except Exception as e:
                    channel_info.append(f"❌ **Force Sub:** Cannot access (ID: {FORCE_SUB_CHANNEL}) - {e}")
            else:
                channel_info.append("❌ **Force Sub:** Not configured")
            
            await message.reply_text("\n".join(channel_info))
        except Exception as e:
            await message.reply_text(f"❌ Error checking channels: {e}")

    @app.on_message(filters.private & filters.user(OWNER_ID) & (
        filters.document | filters.video | filters.audio | filters.photo))
    async def store_file(client: Client, message: Message):
        if not CHANNEL_ID:
            await message.reply_text("❌ **Main channel not configured!**\nUse /channels to check status.")
            return
        
        try:
            await message.forward(CHANNEL_ID)
            await message.reply_text("✅ **File stored successfully!**")
            logger.info(f"📁 File stored by {message.from_user.id}")
        except Exception as e:
            await message.reply_text(f"❌ **Error storing file!**\n{str(e)}")
            logger.error(f"File store error: {e}")

    @app.on_message(filters.private & ~filters.command(["start", "help", "stats", "channels"]))
    async def handle_other_messages(client: Client, message: Message):
        if FORCE_SUB_CHANNEL:
            is_subscribed = await check_subscription(message.from_user.id)
            if not is_subscribed:
                await message.reply_text(
                    "❌ **Please join our channel first!**\n\n"
                    "Use /start to begin."
                )
                return
        
        await message.reply_text(
            "🤖 **Send me files to store!**\n\n"
            "I can store:\n"
            "• Documents\n" 
            "• Videos\n"
            "• Photos\n"
            "• Audio files\n\n"
            "Use /help for more info."
        )

async def main():
    """Main function"""
    global app, runner
    
    try:
        # Start web server first
        logger.info("🚀 Starting health check server...")
        runner = await start_web_server()
        
        # Start bot
        logger.info("🤖 Starting Telegram bot...")
        await setup_bot()
        await app.start()
        
        # Detect channels
        logger.info("🔍 Detecting channels...")
        channels_ok = await detect_channels()
        
        bot = await app.get_me()
        print(f"""
╔══════════════════════╗
║     BOT IS LIVE!     ║
╠══════════════════════╣
║ 🤖 @{bot.username}
║ 👤 Owner: {OWNER_ID}  
║ 📢 Main: {CHANNEL_ID or 'Not set'}
║ 🔔 Force Sub: {FORCE_SUB_CHANNEL or 'Not set'}
║ 🌐 Port: {os.environ.get('PORT', 8080)}
║ ✅ Status: RUNNING
╚══════════════════════╝

💡 Commands:
/start - Start bot
/channels - Check channels (Admin)
/stats - Bot statistics
        """)
        
        # Keep running
        await idle()
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
    finally:
        # Cleanup
        logger.info("🛑 Shutting down...")
        try:
            await app.stop()
        except:
            pass
        try:
            await runner.cleanup()
        except:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
