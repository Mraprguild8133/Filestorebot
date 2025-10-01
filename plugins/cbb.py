import logging
from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot import Bot
from config import HELP_TXT, ABOUT_TXT, START_MSG
from database.database import db

logger = logging.getLogger(__name__)

@Bot.on_callback_query()
async def callback_handler(client: Bot, query: CallbackQuery):
    """Handle all callback queries."""
    try:
        data = query.data
        
        if data == "help":
            await query.message.edit_text(
                text=HELP_TXT,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('🏠 Home', callback_data='start'),
                     InlineKeyboardButton("❌ Close", callback_data='close')]
                ])
            )

        elif data == "about":
            await query.message.edit_text(
                text=ABOUT_TXT,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('🏠 Home', callback_data='start'),
                     InlineKeyboardButton('❌ Close', callback_data='close')]
                ])
            )

        elif data == "start":
            await query.message.edit_text(
                text=START_MSG.format(
                    mention=query.from_user.mention,
                    first=query.from_user.first_name,
                    last=query.from_user.last_name or "",
                    username=f"@{query.from_user.username}" if query.from_user.username else "No Username",
                    id=query.from_user.id
                ),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📚 Help", callback_data='help'),
                     InlineKeyboardButton("ℹ️ About", callback_data='about')],
                    [InlineKeyboardButton("🔗 More Channels", url="https://t.me/Nova_Flix/50")]
                ])
            )

        elif data == "close":
            await query.message.delete()
            try:
                await query.message.reply_to_message.delete()
            except:
                pass

        elif data == "refresh_admins":
            await query.answer("🔄 Refreshing admin list...")
            # Implementation for refreshing admin list
            pass

        elif data == "refresh_banlist":
            await query.answer("🔄 Refreshing ban list...")
            # Implementation for refreshing ban list
            pass

        elif data.startswith("rfs_ch_"):
            channel_id = int(data.split("_")[2])
            await handle_channel_toggle(client, query, channel_id)

        elif data.startswith("rfs_toggle_"):
            parts = data.split("_")
            channel_id = int(parts[2])
            action = parts[3]
            await toggle_channel_mode(client, query, channel_id, action)

        elif data == "fsub_back":
            await show_force_sub_channels(client, query)

        else:
            await query.answer("❌ Unknown button action", show_alert=True)
            
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await query.answer("❌ An error occurred", show_alert=True)

async def handle_channel_toggle(client: Bot, query: CallbackQuery, channel_id: int):
    """Handle channel force-sub mode toggle view."""
    try:
        chat = await client.get_chat(channel_id)
        mode = await db.get_channel_mode(channel_id)
        
        status = "🟢 ON" if mode == "on" else "🔴 OFF"
        new_mode = "off" if mode == "on" else "on"
        
        buttons = [
            [InlineKeyboardButton(f"🔄 Toggle {'OFF' if mode == 'on' else 'ON'}", 
                               callback_data=f"rfs_toggle_{channel_id}_{new_mode}")],
            [InlineKeyboardButton("🔙 Back", callback_data="fsub_back")]
        ]
        
        await query.message.edit_text(
            f"**Channel:** {chat.title}\n"
            f"**Force-Sub Mode:** {status}\n\n"
            f"Toggle the force-subscription mode for this channel.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    except Exception as e:
        logger.error(f"Channel toggle error: {e}")
        await query.answer("❌ Failed to fetch channel info", show_alert=True)

async def toggle_channel_mode(client: Bot, query: CallbackQuery, channel_id: int, mode: str):
    """Toggle channel force-sub mode."""
    try:
        await db.set_channel_mode(channel_id, mode)
        await query.answer(f"✅ Force-Sub set to {'ON' if mode == 'on' else 'OFF'}")
        
        # Refresh the view
        chat = await client.get_chat(channel_id)
        status = "🟢 ON" if mode == "on" else "🔴 OFF"
        new_mode = "off" if mode == "on" else "on"
        
        buttons = [
            [InlineKeyboardButton(f"🔄 Toggle {'OFF' if mode == 'on' else 'ON'}", 
                               callback_data=f"rfs_toggle_{channel_id}_{new_mode}")],
            [InlineKeyboardButton("🔙 Back", callback_data="fsub_back")]
        ]
        
        await query.message.edit_text(
            f"**Channel:** {chat.title}\n"
            f"**Force-Sub Mode:** {status}\n\n"
            f"Toggle the force-subscription mode for this channel.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    except Exception as e:
        logger.error(f"Toggle channel mode error: {e}")
        await query.answer("❌ Failed to update channel mode", show_alert=True)

async def show_force_sub_channels(client: Bot, query: CallbackQuery):
    """Show all force-sub channels for management."""
    try:
        channels = await db.show_channels()
        buttons = []
        
        for channel_id in channels:
            try:
                chat = await client.get_chat(channel_id)
                mode = await db.get_channel_mode(channel_id)
                status = "🟢" if mode == "on" else "🔴"
                buttons.append([
                    InlineKeyboardButton(
                        f"{status} {chat.title}", 
                        callback_data=f"rfs_ch_{channel_id}"
                    )
                ])
            except Exception as e:
                logger.error(f"Error fetching channel {channel_id}: {e}")
                buttons.append([
                    InlineKeyboardButton(
                        f"⚠️ {channel_id} (Unavailable)", 
                        callback_data=f"rfs_ch_{channel_id}"
                    )
                ])
        
        buttons.append([InlineKeyboardButton("❌ Close", callback_data="close")])
        
        await query.message.edit_text(
            "**🔧 Force-Sub Channel Management**\n\n"
            "Select a channel to toggle its force-subscription mode:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    except Exception as e:
        logger.error(f"Show force-sub channels error: {e}")
        await query.answer("❌ Failed to load channels", show_alert=True)
