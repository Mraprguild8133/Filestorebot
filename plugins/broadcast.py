import asyncio
import logging
from typing import List
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import Bot
from database.database import db
from helper_func import admin_filter

logger = logging.getLogger(__name__)

class BroadcastManager:
    """Enhanced broadcast system with better performance."""
    
    @staticmethod
    async def send_broadcast_chunk(client, users_chunk: List[int], message, broadcast_type: str, **kwargs):
        """Send broadcast to a chunk of users."""
        success = 0
        blocked = 0
        deleted = 0
        failed = 0
        
        for user_id in users_chunk:
            try:
                if broadcast_type == "normal":
                    await message.copy(user_id)
                elif broadcast_type == "pin":
                    sent_msg = await message.copy(user_id)
                    await client.pin_chat_message(user_id, sent_msg.id, both_sides=True)
                elif broadcast_type == "auto_delete":
                    sent_msg = await message.copy(user_id)
                    duration = kwargs.get('duration', 60)
                    await asyncio.sleep(duration)
                    await sent_msg.delete()
                
                success += 1
                await asyncio.sleep(0.1)  # Rate limiting
                
            except UserIsBlocked:
                await db.del_user(user_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(user_id)
                deleted += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                # Retry after flood wait
                try:
                    if broadcast_type == "normal":
                        await message.copy(user_id)
                    elif broadcast_type == "pin":
                        sent_msg = await message.copy(user_id)
                        await client.pin_chat_message(user_id, sent_msg.id, both_sides=True)
                    success += 1
                except:
                    failed += 1
            except Exception as e:
                logger.error(f"Broadcast failed for {user_id}: {e}")
                failed += 1
        
        return success, blocked, deleted, failed

@Bot.on_message(filters.private & filters.command('broadcast') & admin_filter)
async def broadcast_message(client: Bot, message: Message):
    """Broadcast message to all users."""
    if not message.reply_to_message:
        msg = await message.reply(
            "**📢 Broadcast**\n\n"
            "Please reply to a message to broadcast it to all users."
        )
        await asyncio.sleep(5)
        await msg.delete()
        return
    
    processing_msg = await message.reply("🔄 **Starting broadcast...**")
    
    try:
        users = await db.full_userbase()
        total_users = len(users)
        
        if total_users == 0:
            return await processing_msg.edit("❌ **No users to broadcast to.**")
        
        # Split users into chunks for better performance
        chunk_size = 100
        user_chunks = [users[i:i + chunk_size] for i in range(0, total_users, chunk_size)]
        
        total_success = 0
        total_blocked = 0
        total_deleted = 0
        total_failed = 0
        
        # Update progress
        await processing_msg.edit(f"🔄 **Broadcasting...**\n\n0/{total_users} users")
        
        for i, chunk in enumerate(user_chunks):
            success, blocked, deleted, failed = await BroadcastManager.send_broadcast_chunk(
                client, chunk, message.reply_to_message, "normal"
            )
            
            total_success += success
            total_blocked += blocked
            total_deleted += deleted
            total_failed += failed
            
            # Update progress
            progress = min((i + 1) * chunk_size, total_users)
            await processing_msg.edit(
                f"🔄 **Broadcasting...**\n\n"
                f"**Progress:** {progress}/{total_users} users\n"
                f"**Success:** {total_success}\n"
                f"**Blocked:** {total_blocked}\n"
                f"**Deleted:** {total_deleted}"
            )
        
        # Final report
        report = (
            f"**📢 Broadcast Complete**\n\n"
            f"**Total Users:** {total_users}\n"
            f"**✅ Successful:** {total_success}\n"
            f"**🚫 Blocked:** {total_blocked}\n"
            f"**🗑️ Deleted Accounts:** {total_deleted}\n"
            f"**❌ Failed:** {total_failed}\n"
            f"**📊 Success Rate:** {(total_success/total_users)*100:.1f}%"
        )
        
        await processing_msg.edit(
            report,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        await processing_msg.edit(f"❌ **Broadcast failed:** `{e}`")

@Bot.on_message(filters.private & filters.command('pbroadcast') & admin_filter)
async def pin_broadcast(client: Bot, message: Message):
    """Broadcast and pin message."""
    if not message.reply_to_message:
        msg = await message.reply(
            "**📌 Pin Broadcast**\n\n"
            "Please reply to a message to broadcast and pin it."
        )
        await asyncio.sleep(5)
        await msg.delete()
        return
    
    processing_msg = await message.reply("🔄 **Starting pin broadcast...**")
    
    try:
        users = await db.full_userbase()
        total_users = len(users)
        
        if total_users == 0:
            return await processing_msg.edit("❌ **No users to broadcast to.**")
        
        chunk_size = 50  # Smaller chunks for pin operations
        user_chunks = [users[i:i + chunk_size] for i in range(0, total_users, chunk_size)]
        
        total_success = 0
        total_blocked = 0
        total_deleted = 0
        total_failed = 0
        
        await processing_msg.edit(f"🔄 **Pin Broadcasting...**\n\n0/{total_users} users")
        
        for i, chunk in enumerate(user_chunks):
            success, blocked, deleted, failed = await BroadcastManager.send_broadcast_chunk(
                client, chunk, message.reply_to_message, "pin"
            )
            
            total_success += success
            total_blocked += blocked
            total_deleted += deleted
            total_failed += failed
            
            progress = min((i + 1) * chunk_size, total_users)
            await processing_msg.edit(
                f"🔄 **Pin Broadcasting...**\n\n"
                f"**Progress:** {progress}/{total_users} users\n"
                f"**Success:** {total_success}\n"
                f"**Blocked:** {total_blocked}"
            )
        
        report = (
            f"**📌 Pin Broadcast Complete**\n\n"
            f"**Total Users:** {total_users}\n"
            f"**✅ Successful:** {total_success}\n"
            f"**🚫 Blocked:** {total_blocked}\n"
            f"**🗑️ Deleted:** {total_deleted}\n"
            f"**❌ Failed:** {total_failed}"
        )
        
        await processing_msg.edit(
            report,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Pin broadcast error: {e}")
        await processing_msg.edit(f"❌ **Pin broadcast failed:** `{e}`")

@Bot.on_message(filters.private & filters.command('dbroadcast') & admin_filter)
async def delete_broadcast(client: Bot, message: Message):
    """Broadcast with auto-delete feature."""
    if not message.reply_to_message:
        msg = await message.reply(
            "**⏰ Auto-Delete Broadcast**\n\n"
            "Please reply to a message to broadcast with auto-delete."
        )
        await asyncio.sleep(5)
        await msg.delete()
        return
    
    try:
        duration = int(message.command[1])
        if duration < 10 or duration > 86400:  # 10 seconds to 24 hours
            return await message.reply("❌ **Duration must be between 10 seconds and 24 hours.**")
    except (IndexError, ValueError):
        return await message.reply(
            "**⏰ Auto-Delete Broadcast**\n\n"
            "**Usage:**\n"
            "`/dbroadcast duration_in_seconds`\n\n"
            "**Example:**\n"
            "`/dbroadcast 300` (5 minutes)"
        )
    
    processing_msg = await message.reply(f"🔄 **Starting auto-delete broadcast ({duration}s)...**")
    
    try:
        users = await db.full_userbase()
        total_users = len(users)
        
        if total_users == 0:
            return await processing_msg.edit("❌ **No users to broadcast to.**")
        
        chunk_size = 50
        user_chunks = [users[i:i + chunk_size] for i in range(0, total_users, chunk_size)]
        
        total_success = 0
        total_blocked = 0
        total_deleted = 0
        total_failed = 0
        
        await processing_msg.edit(f"🔄 **Auto-Delete Broadcasting...**\n\n0/{total_users} users")
        
        for i, chunk in enumerate(user_chunks):
            success, blocked, deleted, failed = await BroadcastManager.send_broadcast_chunk(
                client, chunk, message.reply_to_message, "auto_delete", duration=duration
            )
            
            total_success += success
            total_blocked += blocked
            total_deleted += deleted
            total_failed += failed
            
            progress = min((i + 1) * chunk_size, total_users)
            await processing_msg.edit(
                f"🔄 **Auto-Delete Broadcasting...**\n\n"
                f"**Progress:** {progress}/{total_users} users\n"
                f"**Success:** {total_success}\n"
                f"**Delete After:** {duration}s"
            )
        
        report = (
            f"**⏰ Auto-Delete Broadcast Complete**\n\n"
            f"**Total Users:** {total_users}\n"
            f"**✅ Successful:** {total_success}\n"
            f"**🚫 Blocked:** {total_blocked}\n"
            f"**🗑️ Deleted Accounts:** {total_deleted}\n"
            f"**❌ Failed:** {total_failed}\n"
            f"**⏰ Auto-Delete Time:** {duration} seconds"
        )
        
        await processing_msg.edit(
            report,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Auto-delete broadcast error: {e}")
        await processing_msg.edit(f"❌ **Auto-delete broadcast failed:** `{e}`")
