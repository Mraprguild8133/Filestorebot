from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

from bot import Bot
from helper_func import admin, encode, decode, get_messages, get_message_id

@Bot.on_message(filters.command("start") & filters.private & admin)
async def start(client: Bot, message: Message):
    if len(message.text) > 7:
        try:
            base64_string = message.text.split(" ", 1)[1]
            string = await decode(base64_string)
            argument = string.split("-")
            
            if len(argument) == 2:  # Single file
                msg_id = int(int(argument[1]) / abs(client.db_channel.id))
                messages = await get_messages(client, [msg_id])
                
                for msg in messages:
                    await msg.copy(message.chat.id)
                    
            elif len(argument) == 3:  # Batch files
                start_id = int(int(argument[1]) / abs(client.db_channel.id))
                end_id = int(int(argument[2]) / abs(client.db_channel.id))
                msg_ids = range(start_id, end_id + 1)
                messages = await get_messages(client, msg_ids)
                
                for msg in messages:
                    await msg.copy(message.chat.id)
                    
        except Exception as e:
            await message.reply("❌ Error processing link")
    
    else:
        await message.reply(
            "🤖 **Private File Bot**\n\n"
            "Only admins can use this bot.\n"
            "Send files to store them in the channel.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Help", callback_data="help")]
            ])
        )

@Bot.on_message(filters.command("help") & filters.private & admin)
async def help_cmd(client: Bot, message: Message):
    await message.reply(
        "📖 **Commands:**\n\n"
        "• /start - Start bot\n"
        "• /help - Show this help\n"
        "• /genlink - Generate file link\n"
        "• /batch - Generate batch links"
    )
