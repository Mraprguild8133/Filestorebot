import asyncio
import signal
import sys
from aiohttp import web
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import (
    ApiIdInvalid, AccessTokenInvalid, FloodWait, 
    ChannelInvalid, ChannelPrivate
)
import pytz
from datetime import datetime

from config import *
from plugins import web_server

class FileStoreBot(Client):
    def __init__(self):
        super().__init__(
            name="FileStoreBot",
            api_id=APP_ID,
            api_hash=API_HASH,
            bot_token=TG_BOT_TOKEN,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            sleep_threshold=60,
            parse_mode=ParseMode.HTML
        )
        self.logger = LOGGER
        self.uptime = None
        self.db_channel = None
        self.username = None

    async def validate_config(self):
        """Validate all configuration values."""
        errors = []
        
        if not TG_BOT_TOKEN or TG_BOT_TOKEN == "8154426339":
            errors.append("TG_BOT_TOKEN is not set or is default")
        
        if not APP_ID or APP_ID == 0:
            errors.append("APP_ID is not set or invalid")
            
        if not API_HASH:
            errors.append("API_HASH is not set")
            
        if not CHANNEL_ID or CHANNEL_ID == 0:
            errors.append("CHANNEL_ID is not set or invalid")
            
        if not OWNER_ID or OWNER_ID == 0:
            errors.append("OWNER_ID is not set or invalid")
            
        if not DB_URI:
            errors.append("DATABASE_URL is not set")
        
        if errors:
            self.logger.error("Configuration errors found:")
            for error in errors:
                self.logger.error(f"  - {error}")
            return False
            
        return True

    async def setup_db_channel(self):
        """Setup and validate database channel."""
        try:
            self.db_channel = await self.get_chat(CHANNEL_ID)
            
            # Test channel access
            test_msg = await self.send_message(
                chat_id=CHANNEL_ID, 
                text="🔧 Bot startup test message"
            )
            await test_msg.delete()
            
            self.logger.info(f"Database channel configured: {self.db_channel.title}")
            return True
            
        except (ChannelInvalid, ChannelPrivate) as e:
            self.logger.error(f"Database channel error: {e}")
            self.logger.error("Please ensure:")
            self.logger.error("1. Bot is admin in the channel")
            self.logger.error("2. CHANNEL_ID is correct")
            self.logger.error("3. Channel is not private/deleted")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error setting up DB channel: {e}")
            return False

    async def start(self):
        """Start the bot."""
        self.logger.info("🚀 Starting File Store Bot...")
        
        # Validate configuration
        if not await self.validate_config():
            self.logger.error("❌ Invalid configuration. Bot stopped.")
            sys.exit(1)
        
        try:
            await super().start()
        except (ApiIdInvalid, AccessTokenInvalid) as e:
            self.logger.error(f"❌ Authentication failed: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"❌ Failed to start bot: {e}")
            sys.exit(1)
        
        # Get bot info
        bot_me = await self.get_me()
        self.username = bot_me.username
        self.uptime = datetime.now(pytz.timezone("Asia/Kolkata"))
        
        self.logger.info(f"✅ Bot started: @{bot_me.username} (ID: {bot_me.id})")
        
        # Setup database channel
        if not await self.setup_db_channel():
            self.logger.error("❌ Failed to setup database channel. Bot stopped.")
            sys.exit(1)
        
        # Start web server
        try:
            app = web.AppRunner(await web_server())
            await app.setup()
            await web.TCPSite(app, "0.0.0.0", PORT).start()
            self.logger.info(f"🌐 Web server started on port {PORT}")
        except Exception as e:
            self.logger.warning(f"Web server failed: {e}")
        
        # Notify owner
        try:
            await self.send_message(
                OWNER_ID,
                f"🤖 <b>Bot Started Successfully</b>\n\n"
                f"• Bot: @{self.username}\n"
                f"• Time: {self.uptime.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                f"• Version: 2.0"
            )
        except Exception as e:
            self.logger.warning(f"Failed to notify owner: {e}")
        
        self.logger.info("🎉 Bot is now ready and running!")

    async def stop(self, *args):
        """Stop the bot gracefully."""
        self.logger.info("🛑 Stopping bot...")
        try:
            await self.send_message(
                OWNER_ID,
                f"🔴 <b>Bot Stopped</b>\n\n"
                f"• Bot: @{self.username}\n"
                f"• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except:
            pass
            
        await super().stop()
        self.logger.info("✅ Bot stopped successfully.")

    def run(self):
        """Run the bot with graceful shutdown handling."""
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        loop = asyncio.get_event_loop()
        
        try:
            loop.run_until_complete(self.start())
            self.logger.info("Bot is running. Press Ctrl+C to stop.")
            loop.run_forever()
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal...")
        finally:
            loop.run_until_complete(self.stop())
            loop.close()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop())

# For backward compatibility
Bot = FileStoreBot
