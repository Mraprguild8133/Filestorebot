import logging
from typing import List
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatAction

from bot import Bot
from config import OWNER_ID, LOGGER
from database.database import db
from helper_func import admin_filter

logger = logging.getLogger(__name__)

class BanManager:
    """Enhanced ban management system."""
    
    @staticmethod
    async def validate_ban_actions(user_ids: List[str]) -> tuple[List[int], List[str]]:
        """Validate users for ban actions."""
        valid_ids = []
        invalid_ids = []
        
        for user_id in user_ids:
            try:
                uid = int(user_id)
                if uid > 0:
                    valid_ids.append(uid)
                else:
                    invalid_ids.append(f"Invalid ID: {user_id}")
            except (ValueError, TypeError):
                invalid_ids.append(f"Invalid format: {user_id}")
                
        return valid_ids, invalid_ids

@Bot.on_message(filters.private & filters.command('ban') & admin_filter)
async def ban_user(client: Client, message: Message):
    """Ban users from using the bot."""
    try:
        if len(message.command) < 2:
            return await message.reply(
                "**🚫 Ban User**\n\n"
                "**Usage:**\n"
                "`/ban user_id1 user_id2 ...`\n\n"
                "**Example:**\n"
                "`/ban 123456789 987654321`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        
        processing_msg = await message.reply("🔄 **Processing ban request...**")
        
        # Get and validate user IDs
        input_ids = message.command[1:]
        valid_ids, invalid_ids = await BanManager.validate_ban_actions(input_ids)
        
        if not valid_ids:
            return await processing_msg.edit(
                "❌ **No valid user IDs provided.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        
        # Check existing bans and admins
        existing_bans = await db.get_ban_users()
        existing_admins = await db.get_all_admins()
        
        banned_ids = []
        skipped_ids = []
        
        for user_id in valid_ids:
            # Prevent banning admins and owner
            if user_id == OWNER_ID or user_id in existing_admins:
                skipped_ids.append(f"⛔ Admin/Owner: `{user_id}`")
                continue
            
            if user_id in existing_bans:
                skipped_ids.append(f"ℹ️ Already banned: `{user_id}`")
                continue
            
            if await db.add_ban_user(user_id):
                banned_ids.append(f"✅ Banned: `{user_id}`")
            else:
                skipped_ids.append(f"❌ Failed: `{user_id}`")
        
        # Prepare response
        response = ["**🚫 Ban Results**\n"]
        
        if banned_ids:
            response.append("\n**✅ Banned:**")
            response.extend(banned_ids)
        
        if skipped_ids:
            response.append("\n**⚠️ Skipped:**")
            response.extend(skipped_ids)
        
        if invalid_ids:
            response.append("\n**❌ Invalid:**")
            response.extend(invalid_ids)
        
        await processing_msg.edit(
            "\n".join(response),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Ban user error: {e}")
        await message.reply(f"❌ **Error:** `{e}`")

@Bot.on_message(filters.private & filters.command('unban') & admin_filter)
async def unban_user(client: Client, message: Message):
    """Unban users from the bot."""
    try:
        if len(message.command) < 2:
            return await message.reply(
                "**🔓 Unban User**\n\n"
                "**Usage:**\n"
                "`/unban user_id` - Unban specific user\n"
                "`/unban all` - Unban all users\n\n"
                "**Example:**\n"
                "`/unban 123456789`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        
        processing_msg = await message.reply("🔄 **Processing unban request...**")
        existing_bans = await db.get_ban_users()
        
        # Unban all users
        if message.command[1].lower() == "all":
            if not existing_bans:
                return await processing_msg.edit("✅ **No banned users found.**")
            
            unbanned_count = 0
            for banned_id in existing_bans:
                if await db.del_ban_user(banned_id):
                    unbanned_count += 1
            
            await processing_msg.edit(
                f"✅ **Unbanned {unbanned_count} users.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
            return
        
        # Unban specific user
        try:
            target_id = int(message.command[1])
        except ValueError:
            return await processing_msg.edit(
                "❌ **Invalid user ID.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        
        if target_id not in existing_bans:
            return await processing_msg.edit(
                f"ℹ️ **User `{target_id}` is not banned.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        
        if await db.del_ban_user(target_id):
            await processing_msg.edit(
                f"✅ **Unbanned user:** `{target_id}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        else:
            await processing_msg.edit(
                f"❌ **Failed to unban:** `{target_id}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
            
    except Exception as e:
        logger.error(f"Unban user error: {e}")
        await message.reply(f"❌ **Error:** `{e}`")

@Bot.on_message(filters.private & filters.command('banlist') & admin_filter)
async def ban_list(client: Client, message: Message):
    """Show list of banned users."""
    try:
        processing_msg = await message.reply("🔄 **Fetching ban list...**")
        await message.reply_chat_action(ChatAction.TYPING)
        
        banned_users = await db.get_ban_users()
        
        if not banned_users:
            return await processing_msg.edit(
                "✅ **No banned users.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        
        response = ["**🚫 Banned Users**\n"]
        
        for i, user_id in enumerate(banned_users, 1):
            try:
                user_info = await client.get_users(user_id)
                user_name = user_info.first_name or "Unknown"
                response.append(f"{i}. **{user_name}** - `{user_id}`")
            except:
                response.append(f"{i}. `{user_id}` - *Unable to fetch*")
        
        response.append(f"\n**Total:** {len(banned_users)} users")
        
        await processing_msg.edit(
            "\n".join(response),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_banlist"),
                 InlineKeyboardButton("❌ Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Ban list error: {e}")
        await message.reply(f"❌ **Error:** `{e}`")
