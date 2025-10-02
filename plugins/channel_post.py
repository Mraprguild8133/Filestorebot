from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from bot import Bot
from helper_func import admin, encode

@Bot.on_message(filters.private & admin & ~filters.command(['start', 'help']))
async def channel_post(client: Bot, message: Message):
    try:
        # Forward message to channel
        post_message = await message.copy(client.db_channel.id)
        
        # Generate link
        converted_id = post_message.id * abs(client.db_channel.id)
        string = f"get-{converted_id}"
        base64_string = await encode(string)
        link = f"https://t.me/{client.username}?start={base64_string}"

        await message.reply(
            f"**✅ File Stored**\n\n**Link:** {link}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Share", url=f'https://telegram.me/share/url?url={link}')]
            ])
        )
        
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await channel_post(client, message)
    except Exception as e:
        await message.reply("❌ Error storing file")
