import asyncio
import logging
from pyrogram import Client
from config import TG_BOT_TOKEN, APP_ID, API_HASH, get_logger

logger = get_logger(__name__)

class FileStoreBot(Client):
    def __init__(self):
        super().__init__(
            "FileStoreBot",
            api_id=APP_ID,
            api_hash=API_HASH,
            bot_token=TG_BOT_TOKEN,
            plugins={"root": "plugins"}
        )
    
    async def start(self):
        await super().start()
        bot_me = await self.get_me()
        logger.info(f"Bot started: @{bot_me.username}")
        return True
    
    async def stop(self):
        await super().stop()
        logger.info("Bot stopped")

def main():
    bot = FileStoreBot()
    
    try:
        # Start the bot
        loop = asyncio.get_event_loop()
        loop.run_until_complete(bot.start())
        
        # Keep running
        logger.info("Bot is running. Press Ctrl+C to stop.")
        loop.run_forever()
        
    except KeyboardInterrupt:
        logger.info("Stopping bot...")
        loop.run_until_complete(bot.stop())
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()

Bot = FileStoreBot
