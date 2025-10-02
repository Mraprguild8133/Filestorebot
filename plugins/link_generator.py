from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import Bot
from helper_func import admin, encode, get_message_id

@Bot.on_message(filters.command("genlink") & filters.private & admin)
async def genlink(client: Bot, message: Message):
    if message.reply_to_message:
        msg_id = await get_message_id(client, message.reply_to_message)
        if msg_id:
            base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
            link = f"https://t.me/{client.username}?start={base64_string}"
            
            await message.reply(
                f"**🔗 File Link:**\n{link}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Share", url=f'https://telegram.me/share/url?url={link}')]
                ])
            )
        else:
            await message.reply("❌ Invalid message")
    else:
        await message.reply("❌ Reply to a message")

@Bot.on_message(filters.command("batch") & filters.private & admin)
async def batch(client: Bot, message: Message):
    if message.reply_to_message:
        first_id = await get_message_id(client, message.reply_to_message)
        if not first_id:
            await message.reply("❌ Invalid first message")
            return
            
        # Ask for second message
        await message.reply("📤 Now forward the last message")
        
        try:
            second_msg = await client.listen(message.chat.id, filters=filters.forwarded, timeout=60)
            second_id = await get_message_id(client, second_msg)
            
            if second_id:
                string = f"get-{first_id * abs(client.db_channel.id)}-{second_id * abs(client.db_channel.id)}"
                base64_string = await encode(string)
                link = f"https://t.me/{client.username}?start={base64_string}"
                
                await message.reply(
                    f"**🔗 Batch Link:**\n{link}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Share", url=f'https://telegram.me/share/url?url={link}')]
                    ])
                )
            else:
                await message.reply("❌ Invalid second message")
                
        except:
            await message.reply("❌ Timeout")
    else:
        await message.reply("❌ Reply to first message")
