import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

print("🤖 Starting File Store Bot...")
time.sleep(25)

# Configuration - FIXED SYNTAX
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ.get("OWNER_ID", 7945670631))

# Your channels
MAIN_CHANNEL = -1003279353938
FORCE_SUB_CHANNEL = -1003483616299

app = Client("file_store", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Check subscription
async def check_sub(user_id):
    try:
        user = await app.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        return user.status not in ["left", "kicked"]
    except:
        return False

# Start command
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    
    if not await check_sub(user_id):
        btn = [
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/RHmovieHDOFFICIAL")],
            [InlineKeyboardButton("🔄 Try Again", callback_data="checksub")]
        ]
        await message.reply(
            "**⚠️ Access Denied!**\n\n"
            "You must join our channel to use this bot.\n"
            "Join the channel and click Try Again!",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return
    
    btn = [
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👤 Developer", url="https://t.me/Rakibul51624")
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
            InlineKeyboardButton("🔧 Help", callback_data="help")
        ]
    ]
    
    await message.reply(
        "**🤖 Welcome to File Store Bot!**\n\n"
        "I can store files and share them with users.\n\n"
        "**Features:**\n"
        "• File Storage\n"
        "• Fast Access\n"
        "• 24/7 Online\n\n"
        "Use buttons below to navigate!",
        reply_markup=InlineKeyboardMarkup(btn)
    )

# Help command
@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    await message.reply(
        "**📖 Help Guide**\n\n"
        "**For Users:**\n"
        "• Join our channel for access\n"
        "• Use /start to begin\n\n"
        "**For Admins:**\n"
        "• Send any file to store\n"
        "• Files auto-forward to channel\n\n"
        "**Support:** @Rakibul51624"
    )

# Store files (Admin only)
@app.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def store_file(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Admin access required!")
    
    try:
        # Forward to channel
        msg = await message.forward(MAIN_CHANNEL)
        file_link = f"https://t.me/c/{str(MAIN_CHANNEL)[4:]}/{msg.id}"
        
        await message.reply(
            f"**✅ File Stored Successfully!**\n\n"
            f"**📁 File ID:** `{msg.id}`\n"
            f"**🔗 Direct Link:** {file_link}\n\n"
            f"File is now available in channel!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📂 View File", url=file_link)
            ]])
        )
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

# Stats command
@app.on_message(filters.command("stats"))
async def stats(client, message):
    if message.from_user.id != OWNER_ID:
        return
    
    await message.reply(
        "**📊 Bot Statistics**\n\n"
        "**🤖 Bot Status:** ✅ Online\n"
        "**👤 Owner ID:** 7945670631\n"
        "**📢 Main Channel:** -1003279353938\n"
        "**🔔 Force Sub:** -1003483616299\n"
        "**🚀 Host:** Render\n\n"
        "All systems operational! 🟢"
    )

# Callback queries
@app.on_callback_query(filters.regex("checksub"))
async def checksub(client, query):
    user_id = query.from_user.id
    
    if await check_sub(user_id):
        await query.message.edit(
            "**✅ Access Granted!**\n\n"
            "You can now use all bot features!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 Start Using", callback_data="startusing")
            ]])
        )
    else:
        await query.answer("❌ Please join the channel first!", show_alert=True)

@app.on_callback_query(filters.regex("startusing"))
async def startusing(client, query):
    btn = [
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👤 Developer", url="https://t.me/Rakibul51624")
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
            InlineKeyboardButton("🔧 Help", callback_data="help")
        ]
    ]
    
    await query.message.edit(
        "**🤖 Welcome to File Store Bot!**\n\n"
        "You now have full access to all features!\n\n"
        "**What you can do:**\n"
        "• Access stored files\n"
        "• Get file links\n"
        "• Fast downloads\n\n"
        "Use buttons to navigate!",
        reply_markup=InlineKeyboardMarkup(btn)
    )

@app.on_callback_query(filters.regex("about"))
async def about(client, query):
    await query.message.edit(
        "**ℹ️ About This Bot**\n\n"
        "**🤖 Bot Name:** File Store Bot\n"
        "**⚙️ Framework:** Pyrogram\n"
        "**💻 Language:** Python\n"
        "**🚀 Host:** Render\n\n"
        "**👨‍💻 Developer:** @Rakibul51624\n"
        "**📢 Channel:** @RHmovieHDOFFICIAL\n\n"
        "This bot can store files and share them with users securely.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="back")
        ]])
    )

@app.on_callback_query(filters.regex("help"))
async def help_callback(client, query):
    await query.message.edit(
        "**🔧 Help & Guide**\n\n"
        "**Available Commands:**\n"
        "• /start - Start the bot\n"
        "• /help - Show this message\n"
        "• /stats - Bot statistics (Admin)\n\n"
        "**Features:**\n"
        "• File storage system\n"
        "• Force subscription\n"
        "• Admin file management\n"
        "• Fast file access\n\n"
        "**Support:** @Rakibul51624",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="back")
        ]])
    )

@app.on_callback_query(filters.regex("back"))
async def back(client, query):
    btn = [
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👤 Developer", url="https://t.me/Rakibul51624")
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
            InlineKeyboardButton("🔧 Help", callback_data="help")
        ]
    ]
    
    await query.message.edit(
        "**🤖 Welcome to File Store Bot!**\n\n"
        "I can store files and share them with users.\n\n"
        "**Features:**\n"
        "• File Storage\n"
        "• Fast Access\n"
        "• 24/7 Online\n\n"
        "Use buttons below to navigate!",
        reply_markup=InlineKeyboardMarkup(btn)
    )

# Start bot
print("✅ Starting bot...")
app.run()
