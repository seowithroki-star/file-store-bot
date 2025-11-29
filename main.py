import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
import time
from datetime import datetime
import sys

# Configuration - Keep your existing config code...
# [আপনার existing configuration code এখানে রাখুন]

# Pyrogram Client - FIXED
app = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=60,
    workers=3
)

# Bot start time for uptime
start_time = time.time()

async def is_subscribed(user_id: int) -> bool:
    """Check if user is subscribed to required channels"""
    if not FORCE_SUB_CHANNEL_1:
        return True
    
    try:
        member = await app.get_chat_member(FORCE_SUB_CHANNEL_1, user_id)
        if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
            return False
        return True
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False

def get_uptime():
    """Get bot uptime"""
    seconds = int(time.time() - start_time)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

async def get_channel_username(channel_id: int):
    """Get channel username from ID"""
    try:
        chat = await app.get_chat(channel_id)
        return chat.username if chat.username else "unknown"
    except Exception as e:
        logger.error(f"Error getting channel username: {e}")
        return "unknown"

# FIXED: Remove type annotations from handler parameters
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    logger.info(f"🚀 /start from {user_id} ({first_name})")
    
    # Check subscription
    if not await is_subscribed(user_id):
        buttons = []
        
        if FORCE_SUB_CHANNEL_1:
            channel_username = await get_channel_username(FORCE_SUB_CHANNEL_1)
            buttons.append([InlineKeyboardButton("📢 Join Our Channel", url=f"https://t.me/{channel_username}")])
        
        buttons.append([InlineKeyboardButton("🔄 Try Again", callback_data="check_sub")])
        
        await message.reply_photo(
            photo=F_PIC,
            caption=FORCE_MSG.format(first=first_name),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    
    # User is subscribed - show start message
    await message.reply_photo(
        photo=START_PIC,
        caption=START_MSG.format(first=first_name),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📢 Updates Channel", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")
        ], [
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ]])
    )

# FIXED: Callback handlers
@app.on_callback_query(filters.regex("check_sub"))
async def check_sub_callback(client, query):
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    
    if await is_subscribed(user_id):
        await query.message.edit_caption(
            caption=START_MSG.format(first=first_name),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Updates Channel", url="https://t.me/RHmovieHDOFFICIAL"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")
            ], [
                InlineKeyboardButton("ℹ️ About", callback_data="about")
            ]])
        )
    else:
        await query.answer("❌ Please join our channel first!", show_alert=True)

@app.on_callback_query(filters.regex("about"))
async def about_callback(client, query):
    about_text = """
<b>🤖 About This Bot</b>

<b>📝 Language:</b> Python 3
<b>📚 Framework:</b> Pyrogram
<b>🚀 Host:</b> Koyeb

<b>👨‍💻 Developer:</b> @Rakibul51624
<b>📢 Channel:</b> @RHmovieHDOFFICIAL

This bot can store files and forward them to users."""
    
    await query.message.edit_caption(
        caption=about_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="back_to_start")
        ]])
    )

@app.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query):
    first_name = query.from_user.first_name
    await query.message.edit_caption(
        caption=START_MSG.format(first=first_name),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📢 Updates Channel", url="https://t.me/RHmovieHDOFFICIAL"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Rakibul51624")
        ], [
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ]])
    )

# FIXED: Stats command
@app.on_message(filters.command("stats") & filters.private & filters.user(ADMINS))
async def stats_command(client, message):
    uptime = get_uptime()
    
    stats_text = f"""
<b>🤖 Bot Statistics</b>

<b>⏰ Uptime:</b> {uptime}
<b>🛠️ Admin Count:</b> {len(ADMINS)}
<b>📢 Main Channel:</b> {CHANNEL_ID}
<b>🔔 Force Sub:</b> {FORCE_SUB_CHANNEL_1}
<b>🌐 Port:</b> {PORT}
"""
    
    await message.reply_text(stats_text)

# FIXED: File store functionality
@app.on_message(filters.private & filters.user(ADMINS) & (filters.document | filters.video | filters.audio | filters.photo))
async def store_file(client, message):
    """Store files sent by admins"""
    if not CHANNEL_ID:
        await message.reply_text("❌ CHANNEL_ID not configured!")
        return
    
    try:
        # Forward file to channel
        forwarded_msg = await message.forward(CHANNEL_ID)
        
        file_link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{forwarded_msg.id}"
        
        await message.reply_text(
            f"✅ File stored successfully!\n\n"
            f"📁 File ID: `{forwarded_msg.id}`\n"
            f"🔗 Direct Link: {file_link}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📂 View in Channel", url=file_link)
            ]])
        )
        
    except Exception as e:
        await message.reply_text(f"❌ Error storing file: {e}")
        logger.error(f"File storage error: {e}")

# Keep your existing web server and main function...
# [আপনার existing web server and main function code এখানে রাখুন]

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
