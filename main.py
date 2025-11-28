import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType
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

# Global variables - YOUR MAIN CHANNEL ID
user_data = {}
app = None
runner = None
CHANNEL_ID = -1003200571840  # Your main channel ID

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

async def verify_channel_access():
    """Verify if bot can access the channel"""
    try:
        chat = await app.get_chat(CHANNEL_ID)
        logger.info(f"✅ Channel accessible: {chat.title}")
        
        # Check if bot is admin
        bot_me = await app.get_me()
        try:
            member = await app.get_chat_member(CHANNEL_ID, bot_me.id)
            logger.info(f"👑 Bot role: {member.status}")
            return True, chat, "Accessible"
        except Exception as e:
            logger.error(f"❌ Bot admin check failed: {e}")
            return False, chat, "Not admin"
            
    except Exception as e:
        logger.error(f"❌ Cannot access channel: {e}")
        return False, None, f"Cannot access: {e}"

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
        
        # Verify channel access
        accessible, chat, status = await verify_channel_access()
        
        if not accessible:
            if user_id == OWNER_ID:
                await message.reply_text(
                    f"**Hello {first_name}!** 👋\n\n"
                    "❌ **Channel Access Problem**\n\n"
                    f"Error: {status}\n\n"
                    "**Please ensure:**\n"
                    "1. Bot is admin in the channel\n"
                    "2. Channel ID is correct\n"
                    "3. Bot has 'Post Messages' permission\n\n"
                    "Channel ID: `-1003200571840`"
                )
            else:
                await message.reply_text(
                    f"**Hello {first_name}!** 👋\n\n"
                    "🤖 **File Store Bot**\n\n"
                    "⚠️ **Bot is being configured...**\n\n"
                    "Please check back later!\n"
                    "Admin is setting up file storage.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL")],
                        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")]
                    ])
                )
            return
        
        # Welcome message - Channel is accessible
        welcome_text = (
            f"**Welcome {first_name}!** 🎉\n\n"
            "✅ **File Store Bot is Ready!**\n\n"
            "🤖 **I can store your files in our channel**\n\n"
            "**Supported files:**\n"
            "• 📄 Documents (PDF, Word, Excel, etc.)\n"
            "• 🎥 Videos (MP4, MKV, etc.)\n"
            "• 🖼️ Photos (JPG, PNG, etc.)\n"
            "• 🎵 Audio files (MP3, etc.)\n\n"
            "**How to use:**\n"
            "Simply send me any file and I'll store it!\n\n"
            "📁 **Send me a file to get started!**"
        )
        
        # Create buttons
        buttons = [
            [InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL")],
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")]
        ]
        
        if chat and chat.username:
            buttons.append([InlineKeyboardButton("📂 View Files Channel", url=f"https://t.me/{chat.username}")])
        
        await message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    @app.on_message(filters.private & (
        filters.document | filters.video | filters.audio | filters.photo))
    async def store_file(client: Client, message: Message):
        """Store files in channel - ALL USERS CAN USE"""
        # Verify channel access first
        accessible, chat, status = await verify_channel_access()
        
        if not accessible:
            await message.reply_text(
                f"❌ **Cannot access storage channel!**\n\n"
                f"Error: {status}\n\n"
                "Please contact the admin to fix this issue."
            )
            return
        
        try:
            # Get file info
            file_type = "File"
            file_name = "Unknown"
            file_size = "Unknown"
            
            if message.document:
                file_type = "Document"
                file_name = message.document.file_name or "Document"
                file_size = f"{message.document.file_size / 1024 / 1024:.2f} MB" if message.document.file_size else "Unknown"
            elif message.video:
                file_type = "Video"
                file_name = message.video.file_name or "Video"
                file_size = f"{message.video.file_size / 1024 / 1024:.2f} MB" if message.video.file_size else "Unknown"
            elif message.audio:
                file_type = "Audio" 
                file_name = message.audio.file_name or "Audio"
                file_size = f"{message.audio.file_size / 1024 / 1024:.2f} MB" if message.audio.file_size else "Unknown"
            elif message.photo:
                file_type = "Photo"
                file_name = "Photo"
                file_size = "Unknown"
            
            logger.info(f"📁 Storing {file_type}: {file_name} from user {message.from_user.id}")
            
            # Forward file to channel
            forwarded_msg = await message.forward(CHANNEL_ID)
            
            # Create file link
            file_link = None
            if chat and chat.username:
                file_link = f"https://t.me/{chat.username}/{forwarded_msg.id}"
            
            # Success message
            success_text = (
                "✅ **File stored successfully!**\n\n"
                f"📁 **Type:** {file_type}\n"
                f"📝 **Name:** {file_name}\n"
                f"💾 **Size:** {file_size}\n"
                f"📢 **Channel:** {chat.title if chat else 'File Storage'}\n"
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
            
            logger.info(f"✅ File stored by {message.from_user.id} in channel {CHANNEL_ID}")
            
        except Exception as e:
            error_msg = f"❌ **Error storing file!**\n\nError: {str(e)}"
            await message.reply_text(error_msg)
            logger.error(f"File store error: {e}")

    @app.on_message(filters.command("channel"))
    async def channel_command(client: Client, message: Message):
        """Show channel information"""
        accessible, chat, status = await verify_channel_access()
        
        if not accessible:
            await message.reply_text(f"❌ Channel not accessible: {status}")
            return
        
        response = (
            "**📢 File Storage Channel**\n\n"
            f"📢 **Title:** {chat.title}\n"
            f"🆔 **ID:** `{chat.id}`\n"
        )
        
        if chat.username:
            response += f"👤 **Username:** @{chat.username}\n"
            response += f"🔗 **Link:** https://t.me/{chat.username}\n"
        else:
            response += "👤 **Username:** Not set (private channel)\n"
        
        response += f"🔧 **Status:** {status}\n\n"
        response += "**All files are stored in this channel!**"
        
        buttons = []
        if chat.username:
            buttons.append([InlineKeyboardButton("📂 Open Channel", url=f"https://t.me/{chat.username}")])
        
        await message.reply_text(
            response,
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
        )

    @app.on_message(filters.command("test") & filters.user(OWNER_ID))
    async def test_command(client: Client, message: Message):
        """Test channel access for admin"""
        await message.reply_text("🔍 Testing channel access...")
        
        accessible, chat, status = await verify_channel_access()
        
        response = "**🧪 Channel Test Results**\n\n"
        response += f"**Channel ID:** `{CHANNEL_ID}`\n"
        response += f"**Status:** {status}\n"
        
        if accessible and chat:
            response += f"**Title:** {chat.title}\n"
            if chat.username:
                response += f"**Username:** @{chat.username}\n"
            
            # Try to send a test message
            try:
                test_msg = await client.send_message(CHANNEL_ID, "🤖 Bot test message")
                response += f"✅ **Test message sent!** ID: {test_msg.id}\n"
                
                if chat.username:
                    link = f"https://t.me/{chat.username}/{test_msg.id}"
                    response += f"🔗 **Link:** {link}\n"
            except Exception as e:
                response += f"❌ **Cannot send message:** {e}\n"
        
        await message.reply_text(response)

    @app.on_message(filters.command("stats"))
    async def stats_command(client: Client, message: Message):
        """Bot statistics"""
        total_users = len(user_data)
        accessible, chat, status = await verify_channel_access()
        
        stats_text = (
            f"**📊 Bot Statistics**\n\n"
            f"👥 **Total Users:** {total_users}\n"
            f"📢 **Channel:** {'✅ Accessible' if accessible else '❌ Not accessible'}\n"
            f"🔔 **Force Subscribe:** ❌ Disabled\n"
            f"👤 **Your ID:** `{message.from_user.id}`\n"
            f"✅ **Status:** Running"
        )
        
        if accessible and chat:
            stats_text += f"\n\n**Channel Info:**\n📢 {chat.title}\n🆔 `{chat.id}`"
            if chat.username:
                stats_text += f"\n👤 @{chat.username}"
        
        await message.reply_text(stats_text)

    @app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
    async def broadcast_command(client: Client, message: Message):
        """Broadcast message to all users"""
        if len(message.command) < 2:
            await message.reply_text("Usage: /broadcast <message>")
            return
        
        if not user_data:
            await message.reply_text("❌ No users found!")
            return
        
        broadcast_msg = message.text.split(None, 1)[1]
        total_users = len(user_data)
        
        progress_msg = await message.reply_text(f"📢 Broadcasting to {total_users} users...")
        
        success = 0
        failed = 0
        
        for user_id in user_data.keys():
            try:
                await client.send_message(user_id, broadcast_msg)
                success += 1
            except:
                failed += 1
            await asyncio.sleep(0.1)
        
        await progress_msg.edit_text(
            f"📊 **Broadcast Complete!**\n\n"
            f"✅ **Success:** {success}\n"
            f"❌ **Failed:** {failed}\n"
            f"📋 **Total:** {total_users}"
        )

    @app.on_message(filters.command("help"))
    async def help_command(client: Client, message: Message):
        """Help guide"""
        help_text = (
            "**🤖 File Store Bot - Help Guide**\n\n"
            "**Commands:**\n"
            "/start - Start the bot\n"
            "/help - Show this help\n"
            "/channel - Show channel info\n"
            "/stats - Bot statistics\n"
            "/test - Test channel (Admin)\n\n"
            "**How to use:**\n"
            "Simply send me any file and I'll store it in our channel!\n\n"
            "**Supported files:**\n"
            "• Documents (PDF, Word, Excel)\n"
            "• Videos (MP4, MKV)\n"
            "• Photos (JPG, PNG)\n"
            "• Audio files (MP3)\n\n"
            "**No subscription required!**\n"
            "Everyone can use this bot freely."
        )
        
        await message.reply_text(help_text)

    @app.on_message(filters.private & filters.text & ~filters.command())
    async def handle_text_messages(client: Client, message: Message):
        """Handle regular text messages"""
        await message.reply_text(
            "🤖 **Send me files to store!**\n\n"
            "I can store:\n"
            "• 📄 Documents\n"
            "• 🎥 Videos\n"
            "• 🖼️ Photos\n"
            "• 🎵 Audio files\n\n"
            "Just send me any file and I'll store it in our channel!\n\n"
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
        
        # Verify channel on startup
        accessible, chat, status = await verify_channel_access()
        
        bot = await app.get_me()
        
        print(f"""
╔══════════════════════╗
║    FILE STORE BOT    ║
╠══════════════════════╣
║ 🤖 Bot: @{bot.username}
║ 👤 Owner: {OWNER_ID}  
║ 📢 Channel: -1003200571840
║ 🔔 Force Sub: ❌ DISABLED
║ 🔧 Status: {'✅ ACCESSIBLE' if accessible else '❌ INACCESSIBLE'}
║ 👥 Users: {len(user_data)}
║ ✅ Bot: RUNNING
╚══════════════════════╝

💡 Features:
• No force subscription
• Easy file storage  
• Direct file links
• All users welcome

📋 Commands:
/start - Start bot
/help - Help guide
/channel - Channel info

🚀 Send any file to begin!
        """)
        
        if not accessible:
            print(f"❌ CHANNEL ISSUE: {status}")
            print("💡 Please ensure bot is admin in the channel!")
        
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
