import asyncio
import signal
import sys
import logging
from aiohttp import web
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import (
    ApiIdInvalid, AccessTokenInvalid, FloodWait, 
    ChannelInvalid, ChannelPrivate
)
import pytz
from datetime import datetime

from config import (
    APP_ID, API_HASH, TG_BOT_TOKEN, CHANNEL_ID, 
    OWNER_ID, PORT, ADMIN_IDS, LOGGER, get_logger
)
from plugins import web_server

logger = get_logger(__name__)

class FileStoreBot(Client):
    def __init__(self):
        super().__init__(
            name="FileStoreBot",
            api_id=APP_ID,
            api_hash=API_HASH,
            bot_token=TG_BOT_TOKEN,
            plugins={"root": "plugins"},
            workers=10,
            sleep_threshold=60,
            parse_mode=ParseMode.HTML
        )
        self.logger = logger
        self.uptime = None
        self.db_channel = None
        self.username = None
        self._is_running = False
        self.admin_ids = set(ADMIN_IDS) | {OWNER_ID}  # Combine admins and owner

    async def validate_config(self):
        """Validate all configuration values."""
        errors = []
        
        if not TG_BOT_TOKEN:
            errors.append("TG_BOT_TOKEN is not set")
        
        if not APP_ID or APP_ID == 0:
            errors.append("APP_ID is not set or invalid")
            
        if not API_HASH:
            errors.append("API_HASH is not set")
            
        if not CHANNEL_ID or CHANNEL_ID == 0:
            errors.append("CHANNEL_ID is not set or invalid")
            
        if not OWNER_ID or OWNER_ID == 0:
            errors.append("OWNER_ID is not set or invalid")
        
        if errors:
            self.logger.error("❌ Configuration errors found:")
            for error in errors:
                self.logger.error(f"  - {error}")
            return False
            
        self.logger.info("✅ Configuration validation passed")
        return True

    async def setup_db_channel(self):
        """Setup and validate database channel."""
        try:
            self.db_channel = await self.get_chat(CHANNEL_ID)
            self.logger.info(f"✅ Database channel: {self.db_channel.title} (ID: {self.db_channel.id})")
            
            # Test channel access
            try:
                test_msg = await self.send_message(
                    chat_id=CHANNEL_ID, 
                    text="🤖 Bot startup test"
                )
                await test_msg.delete()
            except Exception as e:
                self.logger.warning(f"⚠️ Channel test failed: {e}")
            
            return True
            
        except (ChannelInvalid, ChannelPrivate) as e:
            self.logger.error(f"❌ Database channel error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Unexpected error setting up DB channel: {e}")
            return False

    async def start(self):
        """Start the bot."""
        self.logger.info("🚀 Starting Private File Store Bot...")
        
        # Validate configuration
        if not await self.validate_config():
            self.logger.error("❌ Invalid configuration. Bot stopped.")
            return False
        
        try:
            await super().start()
            self._is_running = True
        except (ApiIdInvalid, AccessTokenInvalid) as e:
            self.logger.error(f"❌ Authentication failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Failed to start bot: {e}")
            return False
        
        # Get bot info
        try:
            bot_me = await self.get_me()
            self.username = bot_me.username
            self.uptime = datetime.now(pytz.timezone("Asia/Kolkata"))
            
            self.logger.info(f"✅ Bot started: @{bot_me.username}")
            self.logger.info(f"✅ Admin users: {len(self.admin_ids)}")
        except Exception as e:
            self.logger.error(f"❌ Failed to get bot info: {e}")
            return False
        
        # Setup database channel
        if not await self.setup_db_channel():
            self.logger.error("❌ Failed to setup database channel.")
            return False
        
        # Start web server
        try:
            app = web.AppRunner(await web_server())
            await app.setup()
            await web.TCPSite(app, "0.0.0.0", PORT).start()
            self.logger.info(f"🌐 Web server started on port {PORT}")
        except Exception as e:
            self.logger.warning(f"⚠️ Web server failed: {e}")
        
        # Notify owner
        await self.notify_owner()
        
        self.logger.info("🎉 Private bot is now ready! (Admin only)")
        return True

    async def notify_owner(self):
        """Notify owner about bot startup."""
        try:
            await self.send_message(
                OWNER_ID,
                f"🤖 <b>Private Bot Started</b>\n\n"
                f"• Bot: @{self.username}\n"
                f"• Time: {self.uptime.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"• Admins: {len(self.admin_ids)} users\n"
                f"• Mode: Private (Admin Only)"
            )
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to notify owner: {e}")

    async def stop(self):
        """Stop the bot gracefully."""
        if not self._is_running:
            return
            
        self.logger.info("🛑 Stopping bot...")
        self._is_running = False
        
        try:
            await super().stop()
            self.logger.info("✅ Bot stopped successfully.")
        except Exception as e:
            self.logger.error(f"❌ Error during bot stop: {e}")

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id in self.admin_ids

    def run(self):
        """Run the bot."""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        success = False
        try:
            # Start the bot
            success = loop.run_until_complete(self.start())
            
            if success:
                self.logger.info("✅ Bot running. Press Ctrl+C to stop.")
                loop.run_forever()
            else:
                self.logger.error("❌ Bot failed to start.")
                sys.exit(1)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Received interrupt, shutting down...")
        except Exception as e:
            self.logger.error(f"🔴 Fatal error: {e}")
            sys.exit(1)
        finally:
            # Cleanup
            if success:
                loop.run_until_complete(self.stop())
            loop.close()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"🛑 Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop())

# For backward compatibility
Bot = FileStoreBot
