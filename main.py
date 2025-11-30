import os
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

print("🤖 Starting File Store Bot...")
time.sleep(30)

# Configuration
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ.get("OWNER_ID", 7945670631))

# Your channels
MAIN_CHANNEL = -1003279353938
FORCE_SUB_CHANNEL = -1003483616299

app = Client("file_store_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Check if user joined channel
async def check_subscription(user_id):
    try:
        user = await app.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        return user.status not in ["left", "kicked"]
    except:
        return False

# Start command
@app.on_message(filters.command("start"))
async def start_command(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    # Check if user joined channel
    if not await check_subscription(user_id):
        buttons = [
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/RHmovieHDOFFICIAL")],
            [InlineKeyboardButton("🔄 Try Again", callback_data="check_sub")]
        ]
        await message.reply(
            f"**Hello {first_name}!** 👋\n\n"
            "**⚠️ Access Required**\n"
            "Please join our channel to use this bot.\n\n"
            "Join the channel and click **Try Again**!",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    
    # User has joined channel
    buttons = [
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👤 Developer", url="https://t.me/Rakibul51624")
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
            InlineKeyboardButton("📖 Help", callback_data="help")
        ]
    ]
    
    await message.reply(
        f"**Welcome {first_name}!** 🎉\n\n"
        "**🤖 File Store Bot**\n\n"
        "I can store files and share them with users!\n\n"
        "**✨ Features:**\n"
        "• 📁 File Storage\n"
        "• 🔗 Direct Links\n"
        "• ⚡ Fast Access\n"
        "• 🛡️ Secure\n\n"
        "Use buttons below to navigate!",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Help command
@app.on_message(filters.command("help"))
async def help_command(client, message):
    await message.reply(
        "**📖 Help Guide**\n\n"
        "**For Users:**\n"
        "• Join our channel for access\n"
        "• Use /start to begin\n"
        "• Access stored files from channel\n\n"
        "**For Admins:**\n"
        "• Send any file to store it\n"
        "• Files auto-save to channel\n"
        "• Get direct file links\n\n"
        "**Support:** @Rakibul51624"
    )

# Store files (Admin only)
@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def store_file(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ **Admin access required!**")
        return
    
    try:
        # Forward file to channel
        forwarded_msg = await message.forward(MAIN_CHANNEL)
        
        # Generate file link
        file_link = f"https://t.me/c/{str(MAIN_CHANNEL)[4:]}/{forwarded_msg.id}"
        
        await message.reply(
            "**✅ File Stored Successfully!**\n\n"
            f"**📁 File ID:** `{forwarded_msg.id}`\n"
            f"**🔗 Direct Link:** {file_link}\n\n"
            "File is now available in the channel!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📂 View in Channel", url=file_link)
            ]])
        )
    except Exception as e:
        await message.reply(f"❌ **Error:** {str(e)}")

# Stats command (Admin only)
@app.on_message(filters.command("stats"))
async def stats_command(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ **Admin access required!**")
        return
    
    await message.reply(
        "**📊 Bot Statistics**\n\n"
        "**🤖 Status:** ✅ Online\n"
        "**👤 Owner:** 7945670631\n"
        "**📢 Channel:** -1003279353938\n"
        "**🔔 Force Sub:** -1003483616299\n"
        "**🚀 Host:** Render\n\n"
        "**All systems operational!** 🟢"
    )

# Callback queries
@app.on_callback_query(filters.regex("check_sub"))
async def check_sub_callback(client, query):
    user_id = query.from_user.id
    
    if await check_subscription(user_id):
        await query.message.edit(
            "**✅ Access Granted!**\n\n"
            "You can now use all bot features!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 Start Using", callback_data="start_using")
            ]])
        )
    else:
        await query.answer("❌ Please join the channel first!", show_alert=True)

@app.on_callback_query(filters.regex("start_using"))
async def start_using_callback(client, query):
    buttons = [
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👤 Developer", url="https://t.me/Rakibul51624")
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
            InlineKeyboardButton("📖 Help", callback_data="help")
        ]
    ]
    
    await query.message.edit(
        "**🎉 Welcome!**\n\n"
        "You now have full access to all features!\n\n"
        "**What you can do:**\n"
        "• Access stored files\n"
        "• Get direct download links\n"
        "• Fast and secure access\n\n"
        "Use buttons to navigate!",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query(filters.regex("about"))
async def about_callback(client, query):
    await query.message.edit(
        "**ℹ️ About This Bot**\n\n"
        "**🤖 Name:** File Store Bot\n"
        "**⚙️ Framework:** Pyrogram\n"
        "**💻 Language:** Python\n"
        "**🚀 Host:** Render\n\n"
        "**👨‍💻 Developer:** @Rakibul51624\n"
        "**📢 Channel:** @RHmovieHDOFFICIAL\n\n"
        "A secure file storage and sharing solution.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="back_to_start")
        ]])
    )

@app.on_callback_query(filters.regex("help"))
async def help_callback(client, query):
    await query.message.edit(
        "**📖 Help & Guide**\n\n"
        "**Commands:**\n"
        "• /start - Start bot\n"
        "• /help - This message\n"
        "• /stats - Bot stats (Admin)\n\n"
        "**Features:**\n"
        "• File storage system\n"
        "• Force subscription\n"
        "• Admin file management\n"
        "• Fast file access\n\n"
        "**Support:** @Rakibul51624",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="back_to_start")
        ]])
    )

@app.on_callback_query(filters.regex("back_to_start"))
async def back_to_start_callback(client, query):
    buttons = [
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👤 Developer", url="https://t.me/Rakibul51624")
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
            InlineKeyboardButton("📖 Help", callback_data="help")
        ]
    ]
    
    await query.message.edit(
        "**🤖 File Store Bot**\n\n"
        "I can store files and share them with users!\n\n"
        "**✨ Features:**\n"
        "• 📁 File Storage\n"
        "• 🔗 Direct Links\n"
        "• ⚡ Fast Access\n"
        "• 🛡️ Secure\n\n"
        "Use buttons below to navigate!",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Start the bot
print("✅ Bot is starting...")
app.run()
