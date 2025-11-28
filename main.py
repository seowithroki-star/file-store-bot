import os
import time
import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import logging

from config import *

# Initialize MongoDB
mongo_client = MongoClient(DB_URL)
db = mongo_client[DB_NAME]
files_collection = db["files"]
users_collection = db["users"]

# Initialize Bot
app = Client(
    "file_store_bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

# Helper functions
async def is_subscribed(user_id):
    """Check if user is subscribed to required channels"""
    try:
        if FORCE_SUB_CHANNEL_1 != 0:
            member = await app.get_chat_member(FORCE_SUB_CHANNEL_1, user_id)
            if member.status in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]:
                return False, 1
        
        if FORCE_SUB_CHANNEL_2 != 0:
            member = await app.get_chat_member(FORCE_SUB_CHANNEL_2, user_id)
            if member.status in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]:
                return False, 2
        
        if FORCE_SUB_CHANNEL_3 != 0:
            member = await app.get_chat_member(FORCE_SUB_CHANNEL_3, user_id)
            if member.status in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]:
                return False, 3
        
        if FORCE_SUB_CHANNEL_4 != 0:
            member = await app.get_chat_member(FORCE_SUB_CHANNEL_4, user_id)
            if member.status in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]:
                return False, 4
        
        return True, None
    except Exception as e:
        logging.error(f"Error checking subscription: {e}")
        return False, None

def get_force_sub_buttons():
    """Generate force subscribe buttons"""
    buttons = []
    
    if FORCE_SUB_CHANNEL_1 != 0:
        buttons.append([InlineKeyboardButton("📢 Channel 1", url=f"https://t.me/{await get_channel_username(FORCE_SUB_CHANNEL_1)}")])
    
    if FORCE_SUB_CHANNEL_2 != 0:
        buttons.append([InlineKeyboardButton("📢 Channel 2", url=f"https://t.me/{await get_channel_username(FORCE_SUB_CHANNEL_2)}")])
    
    if FORCE_SUB_CHANNEL_3 != 0:
        buttons.append([InlineKeyboardButton("📢 Channel 3", url=f"https://t.me/{await get_channel_username(FORCE_SUB_CHANNEL_3)}")])
    
    if FORCE_SUB_CHANNEL_4 != 0:
        buttons.append([InlineKeyboardButton("📢 Channel 4", url=f"https://t.me/{await get_channel_username(FORCE_SUB_CHANNEL_4)}")])
    
    buttons.append([InlineKeyboardButton("🔄 Try Again", callback_data="checksub")])
    return InlineKeyboardMarkup(buttons)

async def get_channel_username(channel_id):
    """Get channel username from ID"""
    try:
        chat = await app.get_chat(channel_id)
        return chat.username
    except:
        return ""

def save_file(file_data):
    """Save file info to database"""
    files_collection.insert_one(file_data)

def get_user_files(user_id):
    """Get all files uploaded by user"""
    return list(files_collection.find({"user_id": user_id}))

def delete_old_files():
    """Delete files older than FILE_AUTO_DELETE seconds"""
    cutoff_time = datetime.now() - timedelta(seconds=FILE_AUTO_DELETE)
    files_collection.delete_many({"timestamp": {"$lt": cutoff_time}})

# Start command
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check subscription
    subscribed, channel = await is_subscribed(user_id)
    if not subscribed:
        await message.reply_photo(
            photo=F_PIC,
            caption=FORCE_MSG.format(first=message.from_user.first_name),
            reply_markup=get_force_sub_buttons()
        )
        return
    
    # Save user to database
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {
            "first_name": message.from_user.first_name,
            "username": message.from_user.username,
            "last_activity": datetime.now()
        }},
        upsert=True
    )
    
    await message.reply_photo(
        photo=START_PIC,
        caption=START_MSG.format(first=message.from_user.first_name),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📁 Upload File", callback_data="upload_help")],
            [InlineKeyboardButton("📂 My Files", callback_data="my_files")],
            [InlineKeyboardButton("ℹ️ About", callback_data="about"),
             InlineKeyboardButton("🔧 Help", callback_data="help")]
        ])
    )

# Handle files
@app.on_message(filters.media & filters.private)
async def handle_files(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check subscription
    subscribed, channel = await is_subscribed(user_id)
    if not subscribed:
        await message.reply_photo(
            photo=F_PIC,
            caption=FORCE_MSG.format(first=message.from_user.first_name),
            reply_markup=get_force_sub_buttons()
        )
        return
    
    file_info = None
    file_type = None
    
    if message.document:
        file_info = message.document
        file_type = "document"
    elif message.video:
        file_info = message.video
        file_type = "video"
    elif message.audio:
        file_info = message.audio
        file_type = "audio"
    elif message.photo:
        file_info = message.photo
        file_type = "photo"
    
    if file_info:
        # Prepare file data
        file_data = {
            "file_id": file_info.file_id,
            "file_name": getattr(file_info, 'file_name', f'{file_type}_{file_info.file_id}'),
            "file_type": file_type,
            "file_size": getattr(file_info, 'file_size', 0),
            "user_id": user_id,
            "timestamp": datetime.now(),
            "message_id": message.id
        }
        
        # Save to database
        save_file(file_data)
        
        # Generate file link
        file_link = f"https://t.me/{client.me.username}?start=file_{file_info.file_id}"
        
        caption = CUSTOM_CAPTION or f"**📁 File Name:** `{file_data['file_name']}`\n**📦 File Size:** `{file_data['file_size']} bytes`"
        
        await message.reply_text(
            f"✅ File stored successfully!\n\n{caption}\n\n**🔗 Permanent Link:** {file_link}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📁 Share File", url=file_link)]
            ])
        )

# Callback query handler
@app.on_callback_query()
async def handle_callbacks(client: Client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if data == "checksub":
        subscribed, channel = await is_subscribed(user_id)
        if subscribed:
            await callback_query.message.edit_text(
                START_MSG.format(first=callback_query.from_user.first_name),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📁 Upload File", callback_data="upload_help")],
                    [InlineKeyboardButton("📂 My Files", callback_data="my_files")],
                    [InlineKeyboardButton("ℹ️ About", callback_data="about"),
                     InlineKeyboardButton("🔧 Help", callback_data="help")]
                ])
            )
        else:
            await callback_query.answer("Please join all required channels!", show_alert=True)
    
    elif data == "my_files":
        files = get_user_files(user_id)
        if not files:
            await callback_query.answer("You haven't stored any files yet!", show_alert=True)
            return
        
        text = "**📂 Your Stored Files:**\n\n"
        for i, file in enumerate(files, 1):
            file_link = f"https://t.me/{client.me.username}?start=file_{file['file_id']}"
            text += f"{i}. `{file['file_name']}`\n🔗: `{file_link}`\n\n"
        
        await callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_start")]
            ])
        )
    
    elif data == "about":
        await callback_query.message.edit_text(
            Txt.about,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_start")]
            ])
        )
    
    elif data == "upload_help":
        help_text = """
**📁 How to Upload Files:**

1. **Send any file** (document, video, audio, photo) to this bot
2. The bot will automatically store it
3. You'll receive a **permanent link** to share
4. Files are automatically deleted after **30 minutes** (configurable)

**Supported Formats:**
- 📄 Documents (PDF, ZIP, etc.)
- 🎥 Videos (MP4, MKV, etc.)
- 🎵 Audio (MP3, etc.)
- 🖼️ Photos (JPEG, PNG, etc.)
"""
        await callback_query.message.edit_text(
            help_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_start")]
            ])
        )
    
    elif data == "back_start":
        await callback_query.message.edit_text(
            START_MSG.format(first=callback_query.from_user.first_name),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📁 Upload File", callback_data="upload_help")],
                [InlineKeyboardButton("📂 My Files", callback_data="my_files")],
                [InlineKeyboardButton("ℹ️ About", callback_data="about"),
                 InlineKeyboardButton("🔧 Help", callback_data="help")]
            ])
        )

# Start file via link
@app.on_message(filters.command("start") & filters.private)
async def start_with_file(client: Client, message: Message):
    if len(message.command) > 1:
        param = message.command[1]
        if param.startswith("file_"):
            file_id = param.split("_")[1]
            file_data = files_collection.find_one({"file_id": file_id})
            
            if file_data:
                # Send the file
                if file_data["file_type"] == "document":
                    await message.reply_document(
                        file_data["file_id"],
                        caption=CUSTOM_CAPTION or f"**📁 File Name:** `{file_data['file_name']}`"
                    )
                elif file_data["file_type"] == "video":
                    await message.reply_video(
                        file_data["file_id"],
                        caption=CUSTOM_CAPTION or f"**📁 File Name:** `{file_data['file_name']}`"
                    )
                elif file_data["file_type"] == "audio":
                    await message.reply_audio(
                        file_data["file_id"],
                        caption=CUSTOM_CAPTION or f"**📁 File Name:** `{file_data['file_name']}`"
                    )
                elif file_data["file_type"] == "photo":
                    await message.reply_photo(
                        file_data["file_id"],
                        caption=CUSTOM_CAPTION or f"**📁 File Name:** `{file_data['file_name']}`"
                    )
            else:
                await message.reply_text("❌ File not found or expired!")

# Auto delete old files
async def auto_delete_old_files():
    while True:
        delete_old_files()
        await asyncio.sleep(3600)  # Check every hour

if __name__ == "__main__":
    # Start auto delete task
    asyncio.create_task(auto_delete_old_files())
    
    print("Bot started!")
    app.run()
