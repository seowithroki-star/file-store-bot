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

# Global variables
user_data = {}
app = None
runner = None

# YOUR CHANNEL IDs - REPLACE WITH ACTUAL IDs
CHANNEL_ID = -1002491097530      # Main channel for storing files
FORCE_SUB_CHANNEL = -1003200571840  # Channel users must join

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

async def verify_channel_access(channel_id, channel_name):
    """Verify if bot can access and post in channel"""
    try:
        # Get channel info
        chat = await app.get_chat(channel_id)
        logger.info(f"✅ {channel_name} found: {chat.title}")
        
        # Check if bot is admin
        bot_me = await app.get_me()
        try:
            member = await app.get_chat_member(channel_id, bot_me.id)
            if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                logger.info(f"✅ Bot is admin in {channel_name}")
                
                # Check if bot can post messages
                if member.privileges and member.privileges.can_post_messages:
                    logger.info(f"✅ Bot can post messages in {channel_name}")
                    return True, chat, "Can post messages"
                else:
                    logger.warning(f"⚠️ Bot cannot post messages in {channel_name}")
                    return False, chat, "No post permission"
            else:
                logger.error(f"❌ Bot is NOT admin in {channel_name}")
                return False, chat, "Not admin"
                
        except Exception as e:
            logger.error(f"❌ Admin check failed for {channel_name}: {e}")
            return False, chat, f"Admin check failed: {e}"
            
    except Exception as e:
        logger.error(f"❌ Cannot access {channel_name}: {e}")
        return False, None, f"Access failed: {e}"

async def check_subscription(user_id: int) -> bool:
    """Check if user is subscribed to force sub channel"""
    if not FORCE_SUB_CHANNEL:
        return True
    
    try:
        member = await app.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        is_subscribed = member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
        return is_subscribed
    except Exception as e:
        logger.error(f"❌ Subscription check failed: {e}")
        return True  # Allow access if check fails

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
        
        # Check force subscription
        if FORCE_SUB_CHANNEL:
            is_subscribed = await check_subscription(user_id)
            
            if not is_subscribed:
                try:
                    chat = await app.get_chat(FORCE_SUB_CHANNEL)
                    username = chat.username
                    
                    buttons = []
                    if username:
                        buttons.append([InlineKeyboardButton("📢 Join Our Channel", url=f"https://t.me/{username}")])
                    
                    buttons.append([InlineKeyboardButton("🔄 I've Joined", callback_data="check_sub")])
                    
                    await message.reply_text(
                        f"**Hello {first_name}!** 👋\n\n"
                        "📢 **Please join our channel to use this bot**\n\n"
                        "1. Click the button below to join\n"
                        "2. Then click 'I've Joined'\n"
                        "3. Start using the bot!",
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                    return
                except Exception as e:
                    logger.error(f"❌ Force sub error: {e}")
        
        # Welcome message
        welcome_text = f"**Welcome {first_name}!** 🎉\n\n"
        
        # Check main channel access
        main_accessible, main_chat, main_status = await verify_channel_access(CHANNEL_ID, "Main Channel")
        
        if main_accessible:
            welcome_text += (
                "✅ **File Store Bot is Ready!**\n\n"
                "🤖 **Features:**\n"
                "• Store files in channel\n"
                "• Easy file sharing\n"
                "• Direct file links\n\n"
                "📁 **Send me any file to get started!**"
            )
        else:
            welcome_text += (
                "🤖 **File Store Bot**\n\n"
                "⚠️ **File storage temporarily unavailable**\n"
                "Channel configuration in progress.\n"
                "You can still test other features!"
            )
        
        buttons = [
            [InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL")],
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")]
        ]
        
        if main_accessible and main_chat and main_chat.username:
            buttons.append([InlineKeyboardButton("📂 Files Channel", url=f"https://t.me/{main_chat.username}")])
        
        await message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(buttons)
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

    @app.on_message(filters.command("test") & filters.user(OWNER_ID))
    async def test_command(client: Client, message: Message):
        """Test channel access"""
        await message.reply_text("🔍 Testing channel access...")
        
        # Test main channel
        main_accessible, main_chat, main_status = await verify_channel_access(CHANNEL_ID, "Main Channel")
        
        response = "**📢 Channel Test Results**\n\n"
        response += f"**Main Channel:** {main_status}\n"
        
        if main_accessible:
            # Try to send a test message
            try:
                test_msg = await client.send_message(CHANNEL_ID, "🤖 Bot test message")
                response += f"✅ Test message sent! ID: {test_msg.id}\n"
                
                if main_chat.username:
                    link = f"https://t.me/{main_chat.username}/{test_msg.id}"
                    response += f"🔗 Link: {link}\n"
            except Exception as e:
                response += f"❌ Cannot send message: {e}\n"
        
        await message.reply_text(response)

    @app.on_message(filters.private & filters.user(OWNER_ID) & (
        filters.document | filters.video | filters.audio | filters.photo))
    async def store_file(client: Client, message: Message):
        """Store files in channel"""
        # Verify channel access first
        main_accessible, main_chat, main_status = await verify_channel_access(CHANNEL_ID, "Main Channel")
        
        if not main_accessible:
            await message.reply_text(
                f"❌ **Cannot access main channel!**\n\n"
                f"Error: {main_status}\n\n"
                "Please check:\n"
                "1. Bot is admin in channel\n"
                "2. Bot has 'Post Messages' permission\n"
                "3. Channel ID is correct"
            )
            return
        
        try:
            logger.info(f"📁 Attempting to store file from {message.from_user.id}")
            
            # Forward file to channel
            forwarded_msg = await message.forward(CHANNEL_ID)
            logger.info(f"✅ File forwarded to channel, message ID: {forwarded_msg.id}")
            
            # Create file link
            file_link = None
            if main_chat and main_chat.username:
                file_link = f"https://t.me/{main_chat.username}/{forwarded_msg.id}"
            
            # Send success message
            success_text = (
                "✅ **File stored successfully!**\n\n"
                f"📁 **Channel:** {main_chat.title if main_chat else 'Unknown'}\n"
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
            
            logger.info(f"📁 File stored successfully by {message.from_user.id}")
            
        except Exception as e:
            error_msg = f"❌ **Error storing file!**\n\nError: {str(e)}"
            await message.reply_text(error_msg)
            logger.error(f"File store error: {e}")

    @app.on_message(filters.command("help"))
    async def help_command(client: Client, message: Message):
        help_text = (
            "**Help Guide** 🤖\n\n"
            "**Commands:**\n"
            "/start - Start the bot\n"
            "/help - Show this help\n"
            "/stats - Bot statistics\n"
            "/test - Test channel (Admin)\n\n"
        )
        
        main_accessible, _, _ = await verify_channel_access(CHANNEL_ID, "Main Channel")
        if main_accessible:
            help_text += "**To store files:**\nJust send me any file (document, video, photo, audio)"
        else:
            help_text += "⚠️ **File storage:** Currently being configured"
        
        await message.reply_text(help_text)

    @app.on_message(filters.command("stats"))
    async def stats_command(client: Client, message: Message):
        total_users = len(user_data)
        
        main_accessible, _, main_status = await verify_channel_access(CHANNEL_ID, "Main Channel")
        force_accessible, _, force_status = await verify_channel_access(FORCE_SUB_CHANNEL, "Force Sub")
        
        main_status_display = "✅ Accessible" if main_accessible else f"❌ {main_status}"
        force_status_display = "✅ Accessible" if force_accessible else f"❌ {force_status}"
        
        stats_text = (
            f"**📊 Bot Statistics**\n\n"
            f"👥 Total Users: {total_users}\n"
            f"📢 Main Channel: {main_status_display}\n"
            f"🔔 Force Sub: {force_status_display}\n"
            f"👤 Your ID: `{message.from_user.id}`\n"
            f"✅ Status: Running"
        )
        
        await message.reply_text(stats_text)

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
        
        # Verify channels on startup
        logger.info("🔍 Verifying channel access...")
        main_accessible, main_chat, main_status = await verify_channel_access(CHANNEL_ID, "Main Channel")
        force_accessible, force_chat, force_status = await verify_channel_access(FORCE_SUB_CHANNEL, "Force Sub")
        
        bot = await app.get_me()
        
        # Display startup message
        print(f"""
╔══════════════════════╗
║     BOT IS LIVE!     ║
╠══════════════════════╣
║ 🤖 Bot: @{bot.username}
║ 👤 Owner: {OWNER_ID}  
║ 📢 Main: {CHANNEL_ID}
║ 🔔 Force Sub: {FORCE_SUB_CHANNEL}
║ 👥 Users: {len(user_data)}
║ ✅ Status: RUNNING
╚══════════════════════╝

📢 Channel Status:
   Main: {'✅ ACCESSIBLE' if main_accessible else '❌ INACCESSIBLE'}
   Force Sub: {'✅ ACCESSIBLE' if force_accessible else '❌ INACCESSIBLE'}

💡 Commands:
/start - Start bot
/test - Test channels (Admin)  
/stats - View statistics
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
