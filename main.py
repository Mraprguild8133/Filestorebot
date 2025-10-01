#!/usr/bin/env python3
"""
File Store Bot - Main Entry Point
"""

import pyrogram.utils
from bot import FileStoreBot

# Set minimum channel ID for Pyrogram
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

def main():
    """Main entry point."""
    try:
        # Initialize and run the bot
        bot = FileStoreBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"🔴 Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
