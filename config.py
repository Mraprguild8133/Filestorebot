import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

# Bot Configuration
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
APP_ID = int(os.environ.get("APP_ID", 0))
API_HASH = os.environ.get("API_HASH", "")

# Channel Configuration
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0))
OWNER_ID = int(os.environ.get("OWNER_ID", 0))

# Server Configuration
PORT = int(os.environ.get("PORT", 8000))

# Database Configuration
DB_URI = os.environ.get("DATABASE_URL", "")
DB_NAME = os.environ.get("DATABASE_NAME", "FileStoreBot")

# Feature Configuration
FSUB_LINK_EXPIRY = int(os.getenv("FSUB_LINK_EXPIRY", "3600"))  # 1 hour default
BAN_SUPPORT = os.environ.get("BAN_SUPPORT", "https://t.me/CodeflixSupport")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "20"))

# Media URLs
START_PIC = os.environ.get("START_PIC", "https://telegra.ph/file/ec17880d61180d3312d6a.jpg")
FORCE_PIC = os.environ.get("FORCE_PIC", "https://telegra.ph/file/e292b12890b8b4b9dcbd1.jpg")

# Text Messages
HELP_TXT = """
<b>📚 Bot Commands Guide</b>

<b>User Commands:</b>
• /start - Start the bot
• /help - Show this help message
• /about - Bot information

<b>Admin Commands:</b>
• /stats - Bot statistics
• /users - User count
• /broadcast - Broadcast message
• /pbroadcast - Broadcast with pin
• /dbroadcast - Auto-delete broadcast
• /ban - Ban user
• /unban - Unban user
• /banlist - Banned users list
• /add_admin - Add admin
• /deladmin - Remove admin
• /admins - Admin list
• /dlt_time - Set auto-delete timer
• /check_dlt_time - Check delete timer
• /addchnl - Add force-sub channel
• /delchnl - Remove force-sub channel
• /listchnl - Channel list
• /fsub_mode - Toggle force-sub mode
• /delreq - Cleanup request users

<b>Features:</b>
• File storage with secure links
• Force subscription system
• Auto-delete files
• Broadcast messages
• User management
"""

ABOUT_TXT = """
<b>🤖 About This Bot</b>

<b>Creator:</b> <a href="https://t.me/rohit_1888">Rohit</a>
<b>Channel:</b> <a href="https://t.me/Codeflix_Bots">CodeFlix Bots</a>
<b>Support:</b> <a href="https://t.me/CodeflixSupport">CodeFlix Support</a>

<b>🔧 Features:</b>
• Secure file storage
• Auto link generation
• Force subscription
• User management
• Broadcast system
"""

START_MSG = """
<b>👋 Hello {mention}!</b>

I'm a powerful file store bot that can store your private files in a specified channel and generate shareable links.

<b>🛠️ How to use:</b>
1. Send me any file/media
2. I'll store it securely
3. Get a shareable link
4. Share with others

<b>📚 Commands:</b>
• /help - Show all commands
• /about - Bot information
"""

FORCE_MSG = """
<b>🔒 Subscription Required</b>

Hello {mention}, to access this bot you need to join our channels first.

Please join all the channels below and then click the reload button.
"""

# Bot Settings
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", "<b>• Shared via @Codeflix_Bots</b>")
PROTECT_CONTENT = os.environ.get('PROTECT_CONTENT', "False").lower() == "true"
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", "False").lower() == "true"

BOT_STATS_TEXT = "<b>🤖 Bot Statistics</b>\n\n⏰ Uptime: {uptime}\n👥 Users: {users}\n📊 Version: 2.0"
USER_REPLY_TEXT = "❌ Please use the bot commands instead of replying to messages."

# Logging Configuration
LOG_FILE_NAME = "bot.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=10_000_000,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

# Reduce noise from other libraries
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("motor").setLevel(logging.WARNING)

# Create logger function
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

# Create main logger
LOGGER = get_logger(__name__)
