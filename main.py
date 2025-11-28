import os
import asyncio
from pyrogram import Client

async def check_channel_access():
    BOT_TOKEN = "8191375017:AAEPlv-JH2h5zceFVzFPquilo7GVKulci8k" 
    API_ID = "24808756"            
    API_HASH = "28d4f50e0d2a2fc3ba2df10930dd0b00"         
    
    client = Client("checker", int(API_ID), API_HASH, bot_token=BOT_TOKEN)
    
    await client.start()
    bot = await client.get_me()
    print(f"🤖 Bot: @{bot.username}")
    
    # আপনার channel IDs
    channels = [
        (-1002491097530, "Main Channel"),
        (-1003200571840, "Force Sub Channel")
    ]
    
    for channel_id, channel_name in channels:
        try:
            print(f"\n🔍 Checking {channel_name}...")
            
            # Channel info
            chat = await client.get_chat(channel_id)
            print(f"✅ Channel Found: {chat.title}")
            print(f"   🆔 ID: {chat.id}")
            print(f"   👤 Username: @{chat.username}")
            
            # Check bot admin status
            try:
                member = await client.get_chat_member(channel_id, bot.id)
                print(f"   👑 Bot Role: {member.status}")
                
                if member.status in ["administrator", "creator"]:
                    print("   ✅ Bot has admin rights!")
                else:
                    print("   ❌ Bot is NOT admin!")
                    
            except Exception as e:
                print(f"   ❌ Bot admin check failed: {e}")
                
            # Try to send a test message
            try:
                test_msg = await client.send_message(channel_id, "🤖 Bot test message")
                print(f"   💬 Can send messages: YES (Message ID: {test_msg.id})")
                
                # Try to get message link
                if chat.username:
                    link = f"https://t.me/{chat.username}/{test_msg.id}"
                    print(f"   🔗 Message link: {link}")
                else:
                    print("   🔗 Message link: Cannot create (no username)")
                    
            except Exception as e:
                print(f"   💬 Can send messages: NO - {e}")
                
        except Exception as e:
            print(f"❌ {channel_name} error: {e}")
    
    await client.stop()

# Run the check
asyncio.run(check_channel_access())
