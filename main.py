import os
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------- TIME FIX (Render Fix) ----------
real_time = time.time
time.time = lambda: real_time() + 5

print("🤖 Starting File Store Bot...")
time.sleep(2)

# Configuration
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ.get("OWNER_ID", 7945670631))

MAIN_CHANNEL = -1003279353938
FORCE_SUB_CHANNEL = -1003483616299

app = Client("filestore_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------- Check Subscription ----------
async def check_subscription(user_id):
    try:
        user = await app.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        return user.status not in ["left", "kicked"]
    except:
        return False

# ---------- /start ----------
@app.on_message(filters.command("start"))
async def start_command(client, message):
    user = message.from_user
    user_id = user.id
    first_name = user.first_name

    if not await check_subscription(user_id):
        buttons = [
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/RHmovieHDOFFICIAL")],
            [InlineKeyboardButton("🔄 Try Again", callback_data="check_sub")]
        ]
        return await message.reply(
            f"**Hello {first_name}!** 👋\n\n"
            "**⚠️ Please join our channel to use this bot.**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

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
        "🤖 **File Store Bot Ready!**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------- /help ----------
@app.on_message(filters.command("help"))
async def help_command(client, message):
    await message.reply(
        "**📖 Help Guide**\n\n"
        "• Join channel\n"
        "• Use /start\n"
        "• Admin can upload files\n"
    )

# ---------- Store Files ----------
@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def store_file(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ **Admin access required!**")

    try:
        forwarded_msg = await message.forward(MAIN_CHANNEL)
        file_link = f"https://t.me/c/{str(MAIN_CHANNEL)[4:]}/{forwarded_msg.id}"

        await message.reply(
            "**✅ File Stored Successfully!**\n\n"
            f"**🔗 Link:** {file_link}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📂 Open", url=file_link)]])
        )

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

# ---------- /stats ----------
@app.on_message(filters.command("stats"))
async def stats_command(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ **Admin only!**")

    await message.reply(
        "**📊 Bot Statistics**\n\n"
        "Status: ✅ Online\n"
        f"Channel: {MAIN_CHANNEL}\n"
        f"ForceSub: {FORCE_SUB_CHANNEL}\n"
    )

# ---------- Callbacks ----------
@app.on_callback_query(filters.regex("check_sub"))
async def check_sub_callback(client, query):
    if await check_subscription(query.from_user.id):
        await query.message.edit(
            "**✅ Access Granted!**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Start", callback_data="start_using")]
            ])
        )
    else:
        await query.answer("❌ Please join channel!", show_alert=True)

@app.on_callback_query(filters.regex("start_using"))
async def start_using_callback(client, query):
    await query.message.edit("**🎉 You now have full access!**")

@app.on_callback_query(filters.regex("about"))
async def about_callback(client, query):
    await query.message.edit(
        "**ℹ️ About Bot**\n\n🤖 File Store Bot\nPython + Pyrogram\nHost: Render",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
    )

@app.on_callback_query(filters.regex("help"))
async def help_callback(client, query):
    await query.message.edit(
        "**📖 Help**\n\nUse /start and upload files (Admin only)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
    )

@app.on_callback_query(filters.regex("back"))
async def back_callback(client, query):
    await query.message.edit("**🤖 File Store Bot Ready!**")

# ---------- Run Bot ----------
print("✅ Bot Running...")
app.run()
