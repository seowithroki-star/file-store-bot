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

# Get environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
OWNER_ID = int(os.environ.get("OWNER_ID", 7945670631))

# Channel IDs from your configuration
CHANNEL_ID = -1002491097530  # Your main channel
FORCE_SUB_CHANNEL = -1003200571840  # Your force sub channel

# Validate required variables
if not all([BOT_TOKEN, API_ID, API_HASH]):
    logger.error("❌ Missing required environment variables!")
    sys.exit(1)

# Create Pyrogram client
app = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=3
)

# Store for user data (temporary, without MongoDB)
user_data = {}

async def check_subscription(user_id: int) -> bool:
    """Check if user is subscribed to the force sub channel"""
    try:
        member = await app.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        return member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    logger.info(f"📨 /start from {user_id} ({first_name})")
    
    # Check subscription
    is_subscribed = await check_subscription(user_id)
    
    if not is_subscribed:
        # User not subscribed
        try:
            chat = await app.get_chat(FORCE_SUB_CHANNEL)
            channel_username = chat.username
            invite_link = f"https://t.me/{channel_username}" if channel_username else None
            
            buttons = []
            if invite_link:
                buttons.append([InlineKeyboardButton("📢 Join Channel", url=invite_link)])
            buttons.append([InlineKeyboardButton("🔄 Try Again", callback_data="check_sub")])
            
            await message.reply_text(
                f"**Hello {first_name}!**\n\n"
                "❌ You must join our channel to use this bot.\n"
                "Please join the channel and try again!",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception as e:
            await message.reply_text(
                f"**Hello {first_name}!**\n\n"
                "❌ You must join our channel to use this bot.\n"
                "Please contact the admin for access."
            )
        return
    
    # User is subscribed
    await message.reply_text(
        f"**Welcome {first_name}!** 🎉\n\n"
        "🤖 I am a File Store Bot\n\n"
        "**Features:**\n"
        "• Store files in channel\n"
        "• Share files with users\n"
        "• Force subscription system\n\n"
        "Send me any file and I'll store it!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL")],
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")]
        ])
    )
    
    # Store user data
    user_data[user_id] = {
        "first_name": first_name,
        "username": message.from_user.username,
        "last_active": "now"
    }

@app.on_callback_query(filters.regex("check_sub"))
async def check_sub_callback(client: Client, query):
    user_id = query.from_user.id
    
    if await check_subscription(user_id):
        await query.message.edit_text(
            f"**Welcome {query.from_user.first_name}!** 🎉\n\n"
            "✅ Now you can use the bot!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Updates", url="https://t.me/RHmovieHDOFFICIAL")],
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")]
            ])
        )
    else:
        await query.answer("❌ Please join the channel first!", show_alert=True)

@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    await message.reply_text(
        "**Help Guide** 🤖\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/stats - Bot statistics (Admin only)\n\n"
        "**For Admins:**\n"
        "Send any file to store in channel"
    )

@app.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id != OWNER_ID:
        await message.reply_text("❌ Admin access required!")
        return
    
    total_users = len(user_data)
    
    await message.reply_text(
        f"**Bot Statistics** 📊\n\n"
        f"👥 Total Users: {total_users}\n"
        f"📢 Main Channel: {CHANNEL_ID}\n"
        f"🔔 Force Sub: {FORCE_SUB_CHANNEL}\n"
        f"👤 Owner: {OWNER_ID}"
    )

@app.on_message(filters.private & filters.user(OWNER_ID) & (
    filters.document | filters.video | filters.audio | filters.photo))
async def store_file(client: Client, message: Message):
    try:
        # Forward file to main channel
        forwarded_msg = await message.forward(CHANNEL_ID)
        logger.info(f"📁 File stored in channel: {forwarded_msg.id}")
        
        await message.reply_text("✅ File successfully stored in channel!")
    except Exception as e:
        logger.error(f"Error storing file: {e}")
        await message.reply_text("❌ Error storing file!")

@app.on_message(filters.private & ~filters.command(["start", "help", "stats"]))
async def handle_other_messages(client: Client, message: Message):
    # For any other messages, check subscription first
    is_subscribed = await check_subscription(message.from_user.id)
    
    if not is_subscribed:
        await message.reply_text(
            "❌ Please use /start first and join our channel!"
        )
        return
    
    await message.reply_text(
        "🤖 Send me files to store in the channel!\n"
        "Use /help for more information."
    )

async def main():
    await app.start()
    bot = await app.get_me()
    logger.info(f"✅ Bot started: @{bot.username}")
    
    print(f"""
╔══════════════════════╗
║     BOT IS READY     ║
╠══════════════════════╣
║ 🤖 @{bot.username}
║ 👤 Owner: {OWNER_ID}
║ 📢 Channel: {CHANNEL_ID}
║ 🔔 Force Sub: {FORCE_SUB_CHANNEL}
╚══════════════════════╝
    """)
    
    # Keep bot running
    await idle()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
