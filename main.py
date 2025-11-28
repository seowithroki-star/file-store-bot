import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# HARDCODED - Your specific channel IDs
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
OWNER_ID = 7945670631

# YOUR CHANNEL IDs - HARDCODED
CHANNEL_ID = -1002491097530
FORCE_SUB_CHANNEL = -1003200571840

# Validate
if not all([BOT_TOKEN, API_ID, API_HASH]):
    logger.error("❌ Missing BOT_TOKEN, API_ID, or API_HASH")
    sys.exit(1)

logger.info(f"✅ Config loaded - Force Sub: {FORCE_SUB_CHANNEL}")

# Create client
app = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user_data = {}

async def check_subscription(user_id: int) -> bool:
    """Check if user is subscribed"""
    try:
        member = await app.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        is_subscribed = member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
        logger.info(f"🔍 User {user_id} subscription: {is_subscribed}")
        return is_subscribed
    except Exception as e:
        logger.error(f"❌ Subscription check failed: {e}")
        return False

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    logger.info(f"🚀 /start from {user_id}")
    
    # Check subscription
    is_subscribed = await check_subscription(user_id)
    
    if not is_subscribed:
        # Force subscribe
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
                "2. Then click 'I've Joined'",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception as e:
            logger.error(f"❌ Channel error: {e}")
            await message.reply_text(
                "❌ **Channel configuration error**\n\n"
                "Please contact the admin."
            )
        return
    
    # Welcome message for subscribed users
    await message.reply_text(
        f"**Welcome {first_name}!** 🎉\n\n"
        "✅ **You're all set!**\n\n"
        "🤖 **I'm a File Store Bot**\n"
        "• Store files in our channel\n"
        "• Share files with users\n"
        "• Easy file management\n\n"
        "📁 **Just send me any file to get started!**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Channel", url="https://t.me/RHmovieHDOFFICIAL")],
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")]
        ])
    )
    
    # Store user
    user_data[user_id] = {
        "name": first_name,
        "joined": "now"
    }

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
        f"🤖 Bot: @RokiFilestore1bot"
    )

@app.on_message(filters.private & filters.user(OWNER_ID) & (
    filters.document | filters.video | filters.audio | filters.photo))
async def store_file(client: Client, message: Message):
    try:
        # Forward to channel
        await message.forward(CHANNEL_ID)
        await message.reply_text("✅ **File stored successfully!**")
        logger.info(f"📁 File stored by {message.from_user.id}")
    except Exception as e:
        await message.reply_text("❌ **Error storing file!**")
        logger.error(f"File store error: {e}")

@app.on_message(filters.private)
async def handle_other_messages(client: Client, message: Message):
    if message.text and not message.text.startswith('/'):
        # Check subscription for non-command messages
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
║ ✅ Status: RUNNING
╚══════════════════════╝

💡 Test the bot: /start
    """)
    
    await idle()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Bot failed: {e}")
