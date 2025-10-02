import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode, ChatAction

from bot import Bot
from config import START_MSG, HELP_TXT, ABOUT_TXT, START_PIC, CUSTOM_CAPTION, PROTECT_CONTENT
from database.database import db
from helper_func import admin_filter, encode, decode, get_messages, get_message_id, get_readable_time, schedule_auto_delete

logger = logging.getLogger(__name__)

@Bot.on_message(filters.command('start') & filters.private & admin_filter)
async def start_command(client: Bot, message: Message):
    """Start command for admins only."""
    user_id = message.from_user.id
    
    # Check if user is admin
    if not client.is_admin(user_id):
        return await message.reply_text(
            "❌ **Access Denied**\n\n"
            "This bot is for authorized admins only.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Contact Owner", url=f"tg://user?id={client.OWNER_ID}")]
            ])
        )
    
    # Handle file links
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except IndexError:
            return await show_main_menu(client, message)

        try:
            string = await decode(base64_string)
            argument = string.split("-")

            ids = []
            if len(argument) == 3:
                try:
                    start = int(int(argument[1]) / abs(client.db_channel.id))
                    end = int(int(argument[2]) / abs(client.db_channel.id))
                    ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
                except Exception as e:
                    logger.error(f"Error decoding batch IDs: {e}")
                    return

            elif len(argument) == 2:
                try:
                    ids = [int(int(argument[1]) / abs(client.db_channel.id))]
                except Exception as e:
                    logger.error(f"Error decoding single ID: {e}")
                    return

            temp_msg = await message.reply("<b>📥 Downloading files...</b>")
            try:
                messages = await get_messages(client, ids)
            except Exception as e:
                await message.reply_text("❌ Failed to get files!")
                logger.error(f"Error getting messages: {e}")
                return
            finally:
                await temp_msg.delete()

            # Send files to user
            sent_messages = []
            for msg in messages:
                caption = (CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, 
                                             filename=msg.document.file_name) if bool(CUSTOM_CAPTION) and bool(msg.document)
                       else ("" if not msg.caption else msg.caption.html))
                
                try:
                    copied_msg = await msg.copy(
                        chat_id=message.from_user.id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        protect_content=PROTECT_CONTENT
                    )
                    await asyncio.sleep(0.1)
                    sent_messages.append(copied_msg)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")

            # Schedule auto-delete
            auto_delete_time = await db.get_auto_delete_time()
            if auto_delete_time > 0:
                notification_msg = await message.reply(
                    f"⏰ **These files will be deleted in {get_readable_time(auto_delete_time)}.**\n"
                    f"Please save or forward them before they're deleted."
                )
                
                reload_url = f"https://t.me/{client.username}?start={message.command[1]}"
                asyncio.create_task(
                    schedule_auto_delete(client, sent_messages, notification_msg, auto_delete_time)
                )
                
        except Exception as e:
            logger.error(f"Start command error: {e}")
            await message.reply("❌ An error occurred while processing your request.")
    
    else:
        await show_main_menu(client, message)

async def show_main_menu(client: Bot, message: Message):
    """Show main menu to admin users."""
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Help", callback_data="help"),
         InlineKeyboardButton("ℹ️ About", callback_data="about")],
        [InlineKeyboardButton("👥 Admins", callback_data="admins"),
         InlineKeyboardButton("📊 Stats", callback_data="stats")]
    ])
    
    await message.reply_photo(
        photo=START_PIC,
        caption=START_MSG.format(
            mention=message.from_user.mention,
            first=message.from_user.first_name,
            last=message.from_user.last_name or "",
            username=f"@{message.from_user.username}" if message.from_user.username else "No Username",
            id=message.from_user.id
        ),
        reply_markup=reply_markup
    )

@Bot.on_message(filters.command('help') & filters.private & admin_filter)
async def help_command(client: Client, message: Message):
    """Show help message."""
    await message.reply_text(
        HELP_TXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="start"),
             InlineKeyboardButton("❌ Close", callback_data="close")]
        ])
    )

@Bot.on_message(filters.command('stats') & filters.private & admin_filter)
async def stats_command(client: Bot, message: Message):
    """Show bot statistics."""
    try:
        admin_count = await db.get_admin_count()
        auto_delete_time = await db.get_auto_delete_time()
        uptime = client.get_uptime() if hasattr(client, 'get_uptime') else "Unknown"
        
        stats_text = (
            f"**🤖 Bot Statistics**\n\n"
            f"**👥 Admins:** {admin_count}\n"
            f"**⏰ Uptime:** {uptime}\n"
            f"**🗑️ Auto-delete:** {auto_delete_time}s\n"
            f"**🔗 Username:** @{client.username}\n"
            f"**💾 Database:** MongoDB"
        )
        
        await message.reply_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
                 InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Stats command error: {e}")
        await message.reply("❌ Failed to get statistics.")
