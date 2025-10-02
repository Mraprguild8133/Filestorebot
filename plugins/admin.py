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
        
        # Add admins
        added_ids = []
        failed_ids = []
        
        for user_id in valid_ids:
            try:
                # Get user info for username
                try:
                    user_info = await client.get_users(user_id)
                    username = user_info.username or user_info.first_name
                except:
                    username = "Unknown"
                
                if await db.add_admin(user_id, username):
                    added_ids.append(f"✅ Added: `{user_id}` ({username})")
                else:
                    failed_ids.append(f"❌ Failed: `{user_id}`")
                    
            except Exception as e:
                failed_ids.append(f"❌ Error: `{user_id}` - {e}")
        
        # Reload admin cache
        await client.reload_admins()
        
        # Prepare response
        response = ["**👥 Admin Addition Results**\n"]
        
        if added_ids:
            response.append("\n**✅ Added:**")
            response.extend(added_ids)
        
        if failed_ids:
            response.append("\n**❌ Failed:**")
            response.extend(failed_ids)
        
        if invalid_ids:
            response.append("\n**⚠️ Invalid:**")
            response.extend(invalid_ids)
        
        await processing_msg.edit(
            "\n".join(response),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh Admins", callback_data="refresh_admins"),
                 InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Add admin error: {e}")
        await message.reply(f"❌ **Error:** `{e}`")

@Bot.on_message(filters.command('del_admin') & filters.private & filters.user(OWNER_ID))
async def delete_admin(client: Client, message: Message):
    """Remove admin privileges."""
    try:
        if len(message.command) < 2:
            return await message.reply(
                "**🗑️ Remove Admin**\n\n"
                "**Usage:**\n"
                "`/del_admin user_id` - Remove specific admin\n\n"
                "**Example:**\n"
                "`/del_admin 123456789`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
        
        processing_msg = await message.reply("🔄 **Processing...**")
        
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
        
        if await db.remove_admin(target_id):
            # Reload admin cache
            await client.reload_admins()
            
            await processing_msg.edit(
                f"✅ **Removed admin:** `{target_id}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh Admins", callback_data="refresh_admins"),
                     InlineKeyboardButton("❌ Close", callback_data="close")]
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
        
        response = ["**👥 Admin List**\n"]
        
        for admin in admins:
            is_owner = admin.get('is_owner', False)
            username = admin.get('username', 'Unknown')
            user_id = admin['_id']
            
            if is_owner:
                response.append(f"👑 **Owner:** `{user_id}` - {username}")
            else:
                response.append(f"🛠️ **Admin:** `{user_id}` - {username}")
        
        response.append(f"\n**Total:** {len(admins)} admins")
        
        await processing_msg.edit(
            "\n".join(response),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_admins"),
                 InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )
        
    except Exception as e:
        logger.error(f"List admins error: {e}")
        await message.reply(f"❌ **Error:** `{e}`")

@Bot.on_message(filters.command('admin_stats') & filters.private & admin_filter)
async def admin_stats(client: Client, message: Message):
    """Show admin statistics."""
    try:
        processing_msg = await message.reply("🔄 **Fetching statistics...**")
        
        stats = await db.get_stats()
        admin_count = await db.get_admin_count()
        auto_delete_time = await db.get_auto_delete_time()
        
        response = [
            "**📊 Bot Statistics**\n",
            f"**👥 Total Admins:** {admin_count}",
            f"**⏰ Auto-delete Time:** {auto_delete_time} seconds",
            f"**💾 Database:** {stats.get('database', 'Unknown')}",
            f"**📁 Collections:** {', '.join(stats.get('collections', []))}"
        ]
        
        await processing_msg.edit(
            "\n".join(response),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Admin stats error: {e}")
        await message.reply(f"❌ **Error:** `{e}`")
