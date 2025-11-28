import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
import sys
from aiohttp import web
import threading

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

# Your Channel IDs
CHANNEL_ID = -1002491097530
FORCE_SUB_CHANNEL = -1003200571840

# Validate
if not all([BOT_TOKEN, API_ID, API_HASH]):
    logger.error("❌ Missing BOT_TOKEN, API_ID, or API_HASH")
    sys.exit(1)

logger.info("✅ Configuration loaded successfully!")

# Global variables
user_data = {}
app = None
web_app = None
runner = None

async def start_web_server():
    """Start HTTP server for health checks"""
    global web_app, runner
    
    async def health_check(request):
        return web.Response(text="🤖 Bot is running!")
    
    async def bot_status(request):
        return web.Response(text=f"Bot: @RokiFilestore1bot\nUsers: {len(user_data)}")
    
    web_app = web.Application()
    web_app.router.add_get('/', health_check)
    web_app.router.add_get('/health', health_check)
    web_app.router.add_get('/status', bot_status)
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    
    # Use PORT from environment or default to 8080
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🌐 Health check server running on port {port}")
    return runner

async def check_subscription(user_id: int) -> bool:
    """Check if user is subscribed to force sub channel"""
    try:
        member = await app.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        is_subscribed = member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
        logger.info(f"🔍 User {user_id} subscription: {is_subscribed}")
        return is_subscribed
    except Exception as e:
        logger.error(f"❌ Subscription check failed: {e}")
        return False

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
        
        logger.info(f"🚀 /start from {user_id}")
        
        # Check subscription
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
            except Exception as e:
                await message.reply_text(
                    "❌ **Please join our channel first!**\n\n"
                    "Contact admin for assistance."
                )
            return
        
        # Welcome subscribed users
        await message.reply_text(
            f"**Welcome {first_name}!** 🎉\n\n"
            "✅ **You're all set!**\n\n"
            "🤖 **File Store Bot Features:**\n"
            "• Store files in channel\n"
            "• Share files easily\n"
            "• Fast and reliable\n\n"
            "📁 **Send me any file to get started!**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Channel", url="https://t.me/RHmovieHDOFFICIAL")],
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")]
            ])
        )
        
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
                    [InlineKeyboardButton("📢 Channel", url="https://t.me/RHmovieHDOFFICIAL")],
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
            "/stats - Bot stats (Admin)\n\n"
            "**How to use:**\n"
            "1. Join our channel first\n"
            "2. Send any file to store\n"
            "3. Share with others!"
        )

    @app.on_message(filters.command("stats") & filters.user(OWNER_ID))
    async def stats_command(client: Client, message: Message):
        total_users = len(user_data)
        await message.reply_text(
            f"**📊 Bot Statistics**\n\n"
            f"👥 Users: {total_users}\n"
            f"📢 Channel: {CHANNEL_ID}\n"
            f"🔔 Force Sub: {FORCE_SUB_CHANNEL}\n"
            f"👤 Owner: {OWNER_ID}\n"
            f"✅ Status: Running"
        )

    @app.on_message(filters.private & filters.user(OWNER_ID) & (
        filters.document | filters.video | filters.audio | filters.photo))
    async def store_file(client: Client, message: Message):
        try:
            await message.forward(CHANNEL_ID)
            await message.reply_text("✅ **File stored successfully!**")
            logger.info(f"📁 File stored by {message.from_user.id}")
        except Exception as e:
            await message.reply_text("❌ **Error storing file!**")
            logger.error(f"File store error: {e}")

    @app.on_message(filters.private & ~filters.command(["start", "help", "stats"]))
    async def handle_other_messages(client: Client, message: Message):
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
        
        bot = await app.get_me()
        print(f"""
╔══════════════════════╗
║     BOT IS LIVE!     ║
╠══════════════════════╣
║ 🤖 @{bot.username}
║ 👤 Owner: {OWNER_ID}  
║ 📢 Channel: {CHANNEL_ID}
║ 🔔 Force Sub: {FORCE_SUB_CHANNEL}
║ 🌐 Port: {os.environ.get('PORT', 8080)}
║ ✅ Status: RUNNING
╚══════════════════════╝

💡 Bot is ready! Test with /start
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
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
