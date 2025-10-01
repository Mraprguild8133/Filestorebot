import asyncio
import signal
import sys
import logging
from aiohttp import web
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import (
    ApiIdInvalid, AccessTokenInvalid, FloodWait, 
    ChannelInvalid, ChannelPrivate, UserNotParticipant
)
import pytz
from datetime import datetime

from config import *
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
            workers=TG_BOT_WORKERS or 20,
            sleep_threshold=60,
            parse_mode=ParseMode.HTML
        )
        self.logger = logger
        self.uptime = None
        self.db_channel = None
        self.username = None
        self._is_running = False

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
            self.logger.error("❌ Configuration errors found:")
            for error in errors:
                self.logger.error(f"  - {error}")
            self.logger.error("Please check your environment variables.")
            return False
            
        self.logger.info("✅ Configuration validation passed")
        return True

    async def setup_db_channel(self):
        """Setup and validate database channel."""
        try:
            self.db_channel = await self.get_chat(CHANNEL_ID)
            self.logger.info(f"✅ Database channel: {self.db_channel.title} (ID: {self.db_channel.id})")
            
            # Test channel access with a simple operation
            try:
                test_msg = await self.send_message(
                    chat_id=CHANNEL_ID, 
                    text="🤖 Bot startup test - this will be deleted"
                )
                await test_msg.delete()
                self.logger.info("✅ Database channel access test passed")
            except Exception as e:
                self.logger.warning(f"⚠️ Channel test message failed (might not be critical): {e}")
            
            return True
            
        except (ChannelInvalid, ChannelPrivate) as e:
            self.logger.error(f"❌ Database channel error: {e}")
            self.logger.error("Please ensure:")
            self.logger.error("1. Bot is admin in the channel")
            self.logger.error("2. CHANNEL_ID is correct")
            self.logger.error("3. Channel is not private/deleted")
            return False
        except Exception as e:
            self.logger.error(f"❌ Unexpected error setting up DB channel: {e}")
            return False

    async def start(self):
        """Start the bot."""
        self.logger.info("🚀 Starting File Store Bot...")
        
        # Validate configuration first
        if not await self.validate_config():
            self.logger.error("❌ Invalid configuration. Bot stopped.")
            return False
        
        try:
            # Initialize Pyrogram client
            await super().start()
            self._is_running = True
        except (ApiIdInvalid, AccessTokenInvalid) as e:
            self.logger.error(f"❌ Authentication failed: {e}")
            self.logger.error("Please check your API_ID, API_HASH, and BOT_TOKEN")
            return False
        except Exception as e:
            self.logger.error(f"❌ Failed to start bot: {e}")
            return False
        
        # Get bot info
        try:
            bot_me = await self.get_me()
            self.username = bot_me.username
            self.uptime = datetime.now(pytz.timezone("Asia/Kolkata"))
            
            self.logger.info(f"✅ Bot started: @{bot_me.username} (ID: {bot_me.id})")
            self.logger.info(f"✅ Bot first name: {bot_me.first_name}")
        except Exception as e:
            self.logger.error(f"❌ Failed to get bot info: {e}")
            return False
        
        # Setup database channel
        if not await self.setup_db_channel():
            self.logger.error("❌ Failed to setup database channel.")
            return False
        
        # Start web server
        web_success = await self.start_web_server()
        if not web_success:
            self.logger.warning("⚠️ Web server startup failed, but continuing...")
        
        # Notify owner
        await self.notify_owner("startup")
        
        self.logger.info("🎉 Bot is now ready and running!")
        return True

    async def start_web_server(self):
        """Start the web server."""
        try:
            app = web.AppRunner(await web_server())
            await app.setup()
            site = web.TCPSite(app, "0.0.0.0", PORT)
            await site.start()
            
            self.logger.info(f"🌐 Web server started on port {PORT}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Web server failed to start: {e}")
            return False

    async def notify_owner(self, event_type: str):
        """Notify owner about bot events."""
        try:
            if event_type == "startup":
                message = (
                    f"🤖 <b>Bot Started Successfully</b>\n\n"
                    f"• Bot: @{self.username}\n"
                    f"• Time: {self.uptime.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                    f"• ID: {(await self.get_me()).id}\n"
                    f"• Version: 2.0"
                )
            elif event_type == "shutdown":
                message = (
                    f"🔴 <b>Bot Stopped</b>\n\n"
                    f"• Bot: @{self.username}\n"
                    f"• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"• Uptime: {self.get_uptime()}"
                )
            else:
                return
                
            await self.send_message(OWNER_ID, message)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to notify owner: {e}")

    async def stop(self, *args):
        """Stop the bot gracefully."""
        if not self._is_running:
            return
            
        self.logger.info("🛑 Stopping bot...")
        self._is_running = False
        
        try:
            await self.notify_owner("shutdown")
        except:
            pass
            
        try:
            await super().stop()
            self.logger.info("✅ Bot stopped successfully.")
        except Exception as e:
            self.logger.error(f"❌ Error during bot stop: {e}")

    def get_uptime(self):
        """Get bot uptime as string."""
        if not self.uptime:
            return "Not started"
        
        delta = datetime.now(pytz.timezone("Asia/Kolkata")) - self.uptime
        return self.get_readable_time(delta.total_seconds())

    @staticmethod
    def get_readable_time(seconds: int) -> str:
        """Convert seconds to human readable time."""
        periods = [
            ('day', 86400),
            ('hour', 3600),
            ('minute', 60),
            ('second', 1)
        ]
        
        result = []
        for period_name, period_seconds in periods:
            if seconds >= period_seconds:
                period_value, seconds = divmod(seconds, period_seconds)
                if period_value > 0:
                    result.append(f"{int(period_value)} {period_name}{'s' if period_value > 1 else ''}")
                    
        return ", ".join(result) if result else "0 seconds"

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        asyncio.create_task(self.stop())

    def run(self):
        """Run the bot with graceful shutdown handling."""
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Create and configure event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Set up exception handler
        def exception_handler(loop, context):
            self.logger.error(f"🔴 Event loop error: {context.get('exception', 'Unknown error')}")
        
        loop.set_exception_handler(exception_handler)
        
        success = False
        try:
            # Start the bot
            self.logger.info("🟡 Attempting to start bot...")
            success = loop.run_until_complete(self.start())
            
            if success:
                self.logger.info("✅ Bot started successfully. Press Ctrl+C to stop.")
                
                # Keep the bot running
                try:
                    loop.run_forever()
                except KeyboardInterrupt:
                    self.logger.info("🛑 Received KeyboardInterrupt, shutting down...")
                except Exception as e:
                    self.logger.error(f"🔴 Unexpected error in main loop: {e}")
            else:
                self.logger.error("❌ Bot failed to start properly.")
                sys.exit(1)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Received interrupt before startup completed.")
        except Exception as e:
            self.logger.error(f"🔴 Fatal error during bot execution: {e}")
            sys.exit(1)
        finally:
            # Cleanup
            self.logger.info("🧹 Cleaning up...")
            try:
                # Stop the bot
                loop.run_until_complete(self.stop())
                
                # Cancel all running tasks
                tasks = asyncio.all_tasks(loop)
                for task in tasks:
                    task.cancel()
                
                # Wait for tasks to complete
                if tasks:
                    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                
                # Close the loop
                loop.close()
                self.logger.info("✅ Cleanup completed.")
                
            except Exception as e:
                self.logger.error(f"❌ Error during cleanup: {e}")
            
            if not success:
                sys.exit(1)

# For backward compatibility
Bot = FileStoreBot
