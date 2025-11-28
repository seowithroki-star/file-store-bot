import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ChatType
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

# Global variables - WILL BE CREATED AUTOMATICALLY
user_data = {}
app = None
runner = None
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

async def create_channels():
    """Automatically create channels if they don't exist"""
    global CHANNEL_ID, FORCE_SUB_CHANNEL
    
    bot = await app.get_me()
    
    # Create main file storage channel
    try:
        main_chat = await app.create_supergroup(
            title="📁 File Storage",
            description=f"Files stored by @{bot.username}"
        )
        CHANNEL_ID = main_chat.id
        logger.info(f"✅ Created main channel: {CHANNEL_ID}")
        
        # Try to set username
        try:
            await app.set_chat_username(CHANNEL_ID, f"files_{bot.username}")
            logger.info(f"✅ Set main channel username")
        except:
            logger.warning("⚠️ Could not set main channel username")
            
    except Exception as e:
        logger.error(f"❌ Failed to create main channel: {e}")
        return False
    
    # Create force subscription channel  
    try:
        force_chat = await app.create_supergroup(
            title="🔔 Join Our Channel",
            description="Join to use the file storage bot"
        )
        FORCE_SUB_CHANNEL = force_chat.id
        logger.info(f"✅ Created force sub channel: {FORCE_SUB_CHANNEL}")
        
        # Try to set username
        try:
            await app.set_chat_username(FORCE_SUB_CHANNEL, f"join_{bot.username}")
            logger.info(f"✅ Set force sub channel username")
        except:
            logger.warning("⚠️ Could not set force sub channel username")
            
    except Exception as e:
        logger.error(f"❌ Failed to create force sub channel: {e}")
        # Continue with just main channel
    
    return True

async def check_subscription(user_id: int) -> bool:
    """Check if user is subscribed to force sub channel"""
    if not FORCE_SUB_CHANNEL:
        return True
    
    try:
        member = await app.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        return member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
    except Exception as e:
        logger.error(f"❌ Subscription check failed: {e}")
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
        
        # Store user
        user_data[user_id] = {
            "name": first_name, 
            "username": message.from_user.username,
            "joined": "now"
        }
        
        # Create channels if not exists
        if not CHANNEL_ID:
            await message.reply_text("🔄 Creating channels... Please wait!")
            success = await create_channels()
            if not success:
                await message.reply_text(
                    "❌ Failed to create channels!\n\n"
                    "Please try again or contact support."
                )
                return
        
        # Check force subscription
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
                        "2. Then click 'I've Joined'\n"
                        "3. Start storing files!",
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                    return
                except Exception as e:
                    logger.error(f"❌ Force sub error: {e}")
                    # Continue without force sub
        
        # Welcome message
        await message.reply_text(
            f"**Welcome {first_name}!** 🎉\n\n"
            "✅ **File Store Bot is Ready!**\n\n"
            "🤖 **Features:**\n"
            "• Store files in our channel\n"
            "• Easy file sharing\n"
            "• Direct file links\n\n"
            "📁 **Send me any file to get started!**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL")],
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")]
            ])
        )

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
            await query.answer("❌ Please join the channel first!", show_alert=True)

    @app.on_message(filters.command("setup") & filters.user(OWNER_ID))
    async def setup_command(client: Client, message: Message):
        """Recreate channels"""
        await message.reply_text("🔄 Recreating channels...")
        
        global CHANNEL_ID, FORCE_SUB_CHANNEL
        CHANNEL_ID = None
        FORCE_SUB_CHANNEL = None
        
        success = await create_channels()
        if success:
            await message.reply_text("✅ Channels created successfully!")
        else:
            await message.reply_text("❌ Failed to create channels!")

    @app.on_message(filters.private & filters.user(OWNER_ID) & (
        filters.document | filters.video | filters.audio | filters.photo))
    async def store_file(client: Client, message: Message):
        """Store files in channel"""
        if not CHANNEL_ID:
            await message.reply_text(
                "❌ **Channels not created yet!**\n\n"
                "Please use /start first to create channels automatically."
            )
            return
        
        try:
            # Forward file to channel
            forwarded_msg = await message.forward(CHANNEL_ID)
            
            # Get channel info for link
            chat = await app.get_chat(CHANNEL_ID)
            file_link = None
            if chat.username:
                file_link = f"https://t.me/{chat.username}/{forwarded_msg.id}"
            
            # Success message
            success_text = (
                "✅ **File stored successfully!**\n\n"
                f"📁 **Channel:** {chat.title}\n"
                f"🆔 **Message ID:** `{forwarded_msg.id}`\n"
            )
            
            if file_link:
                success_text += f"🔗 **Direct Link:** {file_link}"
            
            buttons = []
            if file_link:
                buttons.append([InlineKeyboardButton("📂 View in Channel", url=file_link)])
            
            await message.reply_text(
                success_text,
                reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
                disable_web_page_preview=True
            )
            
            logger.info(f"📁 File stored by {message.from_user.id} in channel {CHANNEL_ID}")
            
        except Exception as e:
            await message.reply_text(f"❌ **Error storing file!**\n\nError: {str(e)}")
            logger.error(f"File store error: {e}")

    @app.on_message(filters.command("channels"))
    async def channels_command(client: Client, message: Message):
        """Show channel information"""
        if not CHANNEL_ID:
            await message.reply_text("❌ No channels created yet. Use /start first.")
            return
        
        try:
            main_chat = await app.get_chat(CHANNEL_ID)
            response = "**📢 Channel Information**\n\n"
            response += f"**Main Channel:**\n"
            response += f"📢 {main_chat.title}\n"
            response += f"🆔 `{main_chat.id}`\n"
            
            if main_chat.username:
                response += f"👤 @{main_chat.username}\n"
                response += f"🔗 https://t.me/{main_chat.username}\n"
            
            if FORCE_SUB_CHANNEL:
                try:
                    force_chat = await app.get_chat(FORCE_SUB_CHANNEL)
                    response += f"\n**Force Sub Channel:**\n"
                    response += f"📢 {force_chat.title}\n"
                    response += f"🆔 `{force_chat.id}`\n"
                    
                    if force_chat.username:
                        response += f"👤 @{force_chat.username}\n"
                        response += f"🔗 https://t.me/{force_chat.username}\n"
                        
                except Exception as e:
                    response += f"\n**Force Sub:** ❌ {e}\n"
            
            await message.reply_text(response)
            
        except Exception as e:
            await message.reply_text(f"❌ Error getting channel info: {e}")

    @app.on_message(filters.command("help"))
    async def help_command(client: Client, message: Message):
        help_text = (
            "**Help Guide** 🤖\n\n"
            "**Commands:**\n"
            "/start - Start bot & create channels\n"
            "/help - Show this help\n"
            "/channels - Show channel info\n"
            "/setup - Recreate channels (Owner)\n\n"
            "**How to use:**\n"
            "1. Use /start to create channels\n"
            "2. Join the force sub channel\n"
            "3. Send any file to store it!"
        )
        await message.reply_text(help_text)

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
║ 🤖 Bot: @{bot.username}
║ 👤 Owner: {OWNER_ID}  
║ 📢 Main: {'✅ READY' if CHANNEL_ID else '❌ NOT CREATED'}
║ 🔔 Force Sub: {'✅ READY' if FORCE_SUB_CHANNEL else '❌ NOT CREATED'}
║ 👥 Users: {len(user_data)}
║ ✅ Status: RUNNING
╚══════════════════════╝

💡 Instructions:
1. Send /start to create channels
2. Join the force sub channel  
3. Start storing files!

📋 Commands:
/start - Create channels & start
/channels - Show channel info
/help - Help guide
        """)
        
        # Keep running
        await idle()
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
    finally:
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
