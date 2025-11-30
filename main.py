import os
import asyncio
import time
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

print("🟢 Starting Simple File Store Bot...")

# Time sync fix
time.sleep(10)

# Configuration
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ.get("OWNER_ID", 7945670631))

# Your channels
CHANNEL_ID = -1003279353938
FORCE_SUB_CHANNEL = -1003483616299

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Client("file_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Check if user joined channel
async def check_subscription(user_id):
    try:
        member = await app.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        return member.status not in ["left", "kicked"]
    except:
        return False

# Start command
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    
    # Check subscription
    if not await check_subscription(user_id):
        buttons = [
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/RHmovieHDOFFICIAL")],
            [InlineKeyboardButton("🔄 Try Again", callback_data="check_sub")]
        ]
        await message.reply(
            "📢 **Please join our channel first!**\n\n"
            "Join the channel below and then try again.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    
    # User has joined channel
    buttons = [
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
            InlineKeyboardButton("📖 Help", callback_data="help")
        ]
    ]
    
    await message.reply(
        "🤖 **Welcome to File Store Bot!**\n\n"
        "I can store files and share them with users.\n\n"
        "**Commands:**\n"
        "/start - Start bot\n"
        "/help - Help guide\n"
        "/store - Store files (Admin)\n"
        "/stats - Bot stats (Admin)",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Help command
@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    await message.reply(
        "📖 **Help Guide**\n\n"
        "**For Users:**\n"
        "• Join our channel for access\n"
        "• Use /start to begin\n\n"
        "**For Admins:**\n"
        "• Send files to store them\n"
        "• Use /stats for bot status\n\n"
        "**Support:** @Rakibul51624"
    )

# Store files (Admin only)
@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def store_file(client, message):
    if message.from_user.id != OWNER_ID:
        return
    
    try:
        # Forward to channel
        forwarded = await message.forward(CHANNEL_ID)
        file_link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{forwarded.id}"
        
        await message.reply(
            f"✅ **File Stored Successfully!**\n\n"
            f"📁 **File ID:** `{forwarded.id}`\n"
            f"🔗 **Link:** {file_link}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📂 View File", url=file_link)
            ]])
        )
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# Stats command (Admin only)
@app.on_message(filters.command("stats"))
async def stats(client, message):
    if message.from_user.id != OWNER_ID:
        return
    
    await message.reply(
        "📊 **Bot Statistics**\n\n"
        "🤖 **Bot:** File Store Bot\n"
        "👤 **Owner:** 7945670631\n"
        "📢 **Channel:** -1003279353938\n"
        "🚀 **Host:** Render\n"
        "✅ **Status:** Running"
    )

# Callback queries
@app.on_callback_query(filters.regex("check_sub"))
async def check_sub_callback(client, query):
    user_id = query.from_user.id
    
    if await check_subscription(user_id):
        await query.message.edit(
            "✅ **Access Granted!**\n\n"
            "You can now use the bot.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 Start Using", callback_data="start_using")
            ]])
        )
    else:
        await query.answer("❌ Please join the channel first!", show_alert=True)

@app.on_callback_query(filters.regex("start_using"))
async def start_using(client, query):
    await query.message.edit(
        "🤖 **Welcome to File Store Bot!**\n\n"
        "You can now store and share files.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📢 Channel", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")
        ]])
    )

@app.on_callback_query(filters.regex("about"))
async def about(client, query):
    await query.message.edit(
        "ℹ️ **About This Bot**\n\n"
        "🤖 **File Store Bot**\n"
        "📝 **Language:** Python\n"
        "⚙️ **Framework:** Pyrogram\n"
        "🚀 **Host:** Render\n\n"
        "👨‍💻 **Developer:** @Rakibul51624\n"
        "📢 **Channel:** @RHmovieHDOFFICIAL",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="back_start")
        ]])
    )

@app.on_callback_query(filters.regex("help"))
async def help_callback(client, query):
    await query.message.edit(
        "📖 **Help Guide**\n\n"
        "**Available Commands:**\n"
        "/start - Start bot\n"
        "/help - This message\n"
        "/stats - Bot stats (Admin)\n\n"
        "**Features:**\n"
        "• File storage\n"
        "• Channel integration\n"
        "• User management",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="back_start")
        ]])
    )

@app.on_callback_query(filters.regex("back_start"))
async def back_start(client, query):
    await query.message.edit(
        "🤖 **Welcome to File Store Bot!**\n\n"
        "I can store files and share them with users.\n\n"
        "**Commands:**\n"
        "/start - Start bot\n"
        "/help - Help guide\n"
        "/store - Store files (Admin)\n"
        "/stats - Bot stats (Admin)",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📢 Channel", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")
        ], [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
            InlineKeyboardButton("📖 Help", callback_data="help")
        ]])
    )

# Keep bot running
async def main():
    await app.start()
    print("✅ Bot Started Successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
