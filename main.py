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

# Global variables - MANUALLY SET YOUR CHANNEL IDs HERE
user_data = {}
app = None
runner = None

# MANUAL CHANNEL SETUP - Replace these with your actual channel IDs
CHANNEL_ID = -1002491097530  # Replace with your MAIN channel ID
FORCE_SUB_CHANNEL = -1003200571840  # Replace with your FORCE SUB channel ID

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

async def verify_channels():
    """Verify if channels are accessible"""
    global CHANNEL_ID, FORCE_SUB_CHANNEL
    
    channels_to_check = []
    
    if CHANNEL_ID:
        channels_to_check.append(("Main Channel", CHANNEL_ID))
    if FORCE_SUB_CHANNEL:
        channels_to_check.append(("Force Sub Channel", FORCE_SUB_CHANNEL))
    
    accessible_channels = []
    
    for name, channel_id in channels_to_check:
        try:
            chat = await app.get_chat(channel_id)
            accessible_channels.append((name, channel_id, chat.title, True))
            logger.info(f"✅ {name}: {chat.title} (ID: {channel_id})")
            
            # Check bot admin status
            try:
                bot_me = await app.get_me()
                member = await app.get_chat_member(channel_id, bot_me.id)
                logger.info(f"👑 Bot admin status in {name}: {member.status}")
            except Exception as e:
                logger.warning(f"⚠️ Bot may not be admin in {name}: {e}")
                
        except Exception as e:
            accessible_channels.append((name, channel_id, str(e), False))
            logger.error(f"❌ {name} (ID: {channel_id}): {e}")
    
    return accessible_channels

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
        # Allow access if we can't check
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
        
        # Check force subscription if configured
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
                        "1. Click the button below to join our channel\n"
                        "2. Then click 'I've Joined' to verify\n"
                        "3. Start using the bot!",
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                    return
                except Exception as e:
                    logger.error(f"❌ Force sub channel error: {e}")
                    # Continue without force sub
        
        # Welcome message
        welcome_text = f"**Welcome {first_name}!** 🎉\n\n"
        
        if CHANNEL_ID:
            welcome_text += (
                "✅ **File Store Bot is Ready!**\n\n"
                "🤖 **Features:**\n"
                "• Store files in our channel\n"
                "• Easy file sharing\n"
                "• Fast and reliable\n\n"
                "📁 **Send me any file to get started!**"
            )
        else:
            welcome_text += (
                "🤖 **File Store Bot**\n\n"
                "⚠️ **Note:** File storage will be available soon.\n"
                "You can still use other features!"
            )
        
        buttons = [
            [InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL")],
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")]
        ]
        
        if CHANNEL_ID:
            try:
                chat = await app.get_chat(CHANNEL_ID)
                if chat.username:
                    buttons.append([InlineKeyboardButton("📂 View Files Channel", url=f"https://t.me/{chat.username}")])
            except:
                pass
        
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
                "✅ **Thank you for joining our channel!**\n\n"
                "You can now use all bot features.\n"
                "Send me any file to store in our channel!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL")],
                    [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")]
                ])
            )
        else:
            await query.answer("❌ You haven't joined the channel yet! Please join first.", show_alert=True)

    @app.on_message(filters.command("help"))
    async def help_command(client: Client, message: Message):
        help_text = (
            "**Help Guide** 🤖\n\n"
            "**Commands:**\n"
            "/start - Start the bot\n"
            "/help - Show this help\n"
            "/stats - Bot statistics\n"
            "/channels - Channel status\n\n"
        )
        
        if CHANNEL_ID:
            help_text += "**How to store files:**\nJust send me any file (document, video, photo, audio) and I'll store it in our channel!"
        else:
            help_text += "⚠️ **File storage is currently being configured.**"
        
        await message.reply_text(help_text)

    @app.on_message(filters.command("stats"))
    async def stats_command(client: Client, message: Message):
        total_users = len(user_data)
        
        # Channel status
        main_channel_status = "✅ Configured" if CHANNEL_ID else "❌ Not configured"
        force_sub_status = "✅ Configured" if FORCE_SUB_CHANNEL else "❌ Not configured"
        
        stats_text = (
            f"**📊 Bot Statistics**\n\n"
            f"👥 Total Users: {total_users}\n"
            f"📢 Main Channel: {main_channel_status}\n"
            f"🔔 Force Sub: {force_sub_status}\n"
            f"👤 Your ID: `{message.from_user.id}`\n"
            f"✅ Bot Status: Running"
        )
        
        await message.reply_text(stats_text)

    @app.on_message(filters.command("channels") & filters.user(OWNER_ID))
    async def channels_command(client: Client, message: Message):
        """Detailed channel information for admin"""
        accessible_channels = await verify_channels()
        
        response = "**📢 Channel Status Report**\n\n"
        
        for name, channel_id, info, is_accessible in accessible_channels:
            if is_accessible:
                response += f"✅ **{name}**\n"
                response += f"   📢 Title: {info}\n"
                response += f"   🆔 ID: `{channel_id}`\n"
            else:
                response += f"❌ **{name}**\n"
                response += f"   🆔 ID: `{channel_id}`\n"
                response += f"   📛 Error: {info}\n"
        
        if not accessible_channels:
            response += "❌ No channels configured"
        
        await message.reply_text(response)

    @app.on_message(filters.private & filters.user(OWNER_ID) & (
        filters.document | filters.video | filters.audio | filters.photo))
    async def store_file(client: Client, message: Message):
        if not CHANNEL_ID:
            await message.reply_text(
                "❌ **Main channel not configured!**\n\n"
                "Please configure the main channel ID first."
            )
            return
        
        try:
            # Forward file to main channel
            forwarded_msg = await message.forward(CHANNEL_ID)
            
            # Get file link
            chat = await app.get_chat(CHANNEL_ID)
            if chat.username:
                file_link = f"https://t.me/{chat.username}/{forwarded_msg.id}"
            else:
                file_link = f"Message ID: {forwarded_msg.id}"
            
            await message.reply_text(
                "✅ **File stored successfully!**\n\n"
                f"📁 File saved in: {chat.title}\n"
                f"🔗 Access: {file_link}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📂 View in Channel", url=file_link)
                ]]) if chat.username else None
            )
            
            logger.info(f"📁 File stored by {message.from_user.id} in channel {CHANNEL_ID}")
            
        except Exception as e:
            error_msg = f"❌ **Error storing file!**\n\n{str(e)}"
            await message.reply_text(error_msg)
            logger.error(f"File store error: {e}")

    @app.on_message(filters.private & ~filters.command(["start", "help", "stats", "channels"]))
    async def handle_other_messages(client: Client, message: Message):
        # Check force subscription for non-command messages
        if FORCE_SUB_CHANNEL:
            is_subscribed = await check_subscription(message.from_user.id)
            if not is_subscribed:
                await message.reply_text(
                    "❌ **Please join our channel first!**\n\n"
                    "Use /start to begin."
                )
                return
        
        if message.text:
            await message.reply_text(
                "🤖 **Send me files to store!**\n\n"
                "I can store:\n"
                "• 📄 Documents\n" 
                "• 🎥 Videos\n"
                "• 🖼️ Photos\n"
                "• 🎵 Audio files\n\n"
                "Use /help for more information."
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
        
        # Verify channels
        logger.info("🔍 Verifying channels...")
        accessible_channels = await verify_channels()
        
        bot = await app.get_me()
        
        # Display startup message
        print(f"""
╔══════════════════════╗
║     BOT IS LIVE!     ║
╠══════════════════════╣
║ 🤖 Bot: @{bot.username}
║ 👤 Owner: {OWNER_ID}  
║ 📢 Main: {CHANNEL_ID or 'Not set'}
║ 🔔 Force Sub: {FORCE_SUB_CHANNEL or 'Not set'}
║ 👥 Users: {len(user_data)}
║ 🌐 Port: {os.environ.get('PORT', 8080)}
║ ✅ Status: RUNNING
╚══════════════════════╝

💡 Available Commands:
/start - Start bot
/stats - View statistics  
/channels - Channel info (Admin)
/help - Help guide
        """)
        
        # Show channel status
        print("📢 Channel Status:")
        for name, channel_id, info, is_accessible in accessible_channels:
            status = "✅ ACCESSIBLE" if is_accessible else "❌ INACCESSIBLE"
            print(f"   {name}: {status}")
        
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
