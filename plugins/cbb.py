from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot

@Bot.on_callback_query()
async def callback_handler(client: Bot, query: CallbackQuery):
    if query.data == "help":
        await query.message.edit(
            "📖 **Commands:**\n\n"
            "• /start - Start bot\n"
            "• /help - Show help\n"
            "• /genlink - Generate file link\n"
            "• /batch - Generate batch links",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Back", callback_data="start")]
            ])
        )
    elif query.data == "start":
        await query.message.edit(
            "🤖 **Private File Bot**\n\n"
            "Only admins can use this bot.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Help", callback_data="help")]
            ])
        )
    elif query.data == "close":
        await query.message.delete()
