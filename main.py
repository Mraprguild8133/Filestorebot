#!/usr/bin/env python3
"""
File Store Bot - Main Entry Point
A powerful Telegram bot for file storage and sharing
"""

import pyrogram.utils
from bot import FileStoreBot

# Set minimum channel ID for Pyrogram
pyrogram.utils.MIN_CHANNEL_ID = -1002973965279

if __name__ == "__main__":
    # Initialize and run the bot
    bot = FileStoreBot()
    bot.run()
