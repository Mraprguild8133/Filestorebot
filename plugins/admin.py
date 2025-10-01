import logging
from typing import List
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import Bot
from config import OWNER_ID, LOGGER
from database.database import db
from helper_func import admin_filter

logger = logging.getLogger(__name__)

class AdminManager:
    """Enhanced admin management system."""
    
    @staticmethod
    async def validate_user_ids(user_ids: List[str]) -> tuple[List[int], List[str]]:
        """Validate and convert user IDs."""
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

@Bot.on_message(filters.command('add_admin') & filters.private & filters.user(OWNER_ID))
async def add_admin(client: Client, message: Message):
    """Add one or more users as admins."""
    try:
        if len(message.command) < 2:
            return await message.reply(
                "**👥 Add Admin**\n\n"
                "**Usage:**\n"
                "`/add_admin user_id1 user_id2 ...`\n\n"
                "**Example:**\n"
                "`/add_admin 123456789 987654321`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        
        processing_msg = await message.reply("🔄 **Processing...**")
        
        # Get and validate user IDs
        input_ids = message.command[1:]
        valid_ids, invalid_ids = await AdminManager.validate_user_ids(input_ids)
        
        if not valid_ids:
            return await processing_msg.edit(
                "❌ **No valid user IDs provided.**\n\n"
                f"**Invalid IDs:**\n" + "\n".join(invalid_ids),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        
        # Check existing admins
        existing_admins = await db.get_all_admins()
        added_ids = []
        skipped_ids = []
        
        for user_id in valid_ids:
            if user_id in existing_admins:
                skipped_ids.append(f"🔄 Already admin: `{user_id}`")
                continue
            
            if await db.add_admin(user_id):
                added_ids.append(f"✅ Added: `{user_id}`")
            else:
                skipped_ids.append(f"❌ Failed: `{user_id}`")
        
        # Prepare response
        response = ["**👥 Admin Addition Results**\n"]
        
        if added_ids:
            response.append("\n**✅ Added:**")
            response.extend(added_ids)
        
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
        logger.error(f"Add admin error: {e}")
        await message.reply(f"❌ **Error:** `{e}`")

@Bot.on_message(filters.command('deladmin') & filters.private & filters.user(OWNER_ID))
async def delete_admin(client: Client, message: Message):
    """Remove admin privileges."""
    try:
        if len(message.command) < 2:
            return await message.reply(
                "**🗑️ Remove Admin**\n\n"
                "**Usage:**\n"
                "`/deladmin user_id` - Remove specific admin\n"
                "`/deladmin all` - Remove all admins\n\n"
                "**Example:**\n"
                "`/deladmin 123456789`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        
        processing_msg = await message.reply("🔄 **Processing...**")
        existing_admins = await db.get_all_admins()
        
        # Remove all admins
        if message.command[1].lower() == "all":
            if not existing_admins:
                return await processing_msg.edit("✅ **No admins to remove.**")
            
            removed_count = 0
            for admin_id in existing_admins:
                if admin_id != OWNER_ID:  # Don't remove owner
                    if await db.del_admin(admin_id):
                        removed_count += 1
            
            await processing_msg.edit(
                f"✅ **Removed {removed_count} admins.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
            return
        
        # Remove specific admin
        try:
            target_id = int(message.command[1])
        except ValueError:
            return await processing_msg.edit(
                "❌ **Invalid user ID.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        
        if target_id == OWNER_ID:
            return await processing_msg.edit(
                "❌ **Cannot remove owner.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        
        if target_id not in existing_admins:
            return await processing_msg.edit(
                f"❌ **User `{target_id}` is not an admin.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        
        if await db.del_admin(target_id):
            await processing_msg.edit(
                f"✅ **Removed admin:** `{target_id}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        else:
            await processing_msg.edit(
                f"❌ **Failed to remove admin:** `{target_id}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
            
    except Exception as e:
        logger.error(f"Delete admin error: {e}")
        await message.reply(f"❌ **Error:** `{e}`")

@Bot.on_message(filters.command('admins') & filters.private & admin_filter)
async def list_admins(client: Client, message: Message):
    """List all admins."""
    try:
        processing_msg = await message.reply("🔄 **Fetching admin list...**")
        
        admins = await db.get_all_admins()
        owner_info = await client.get_users(OWNER_ID)
        
        response = [
            "**👥 Admin List**\n",
            f"**👑 Owner:** {owner_info.mention} (`{OWNER_ID}`)\n"
        ]
        
        if admins:
            response.append("\n**🛠️ Admins:**")
            for i, admin_id in enumerate(admins, 1):
                try:
                    user_info = await client.get_users(admin_id)
                    response.append(f"{i}. {user_info.mention} (`{admin_id}`)")
                except:
                    response.append(f"{i}. `{admin_id}` (Unable to fetch)")
        else:
            response.append("\n**ℹ️ No additional admins.**")
        
        await processing_msg.edit(
            "\n".join(response),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_admins"),
                 InlineKeyboardButton("❌ Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"List admins error: {e}")
        await message.reply(f"❌ **Error:** `{e}`")
