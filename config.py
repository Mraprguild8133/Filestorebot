import os
import logging
from logging.handlers import RotatingFileHandler

# Bot Configuration
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
APP_ID = int(os.environ.get("APP_ID", 0))
API_HASH = os.environ.get("API_HASH", "")

# Channel Configuration
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0))
OWNER_ID = int(os.environ.get("OWNER_ID", 0))

# Admin Configuration (Comma separated user IDs)
ADMIN_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]

# Server Configuration
PORT = int(os.environ.get("PORT", 8000))

# Bot Settings
PROTECT_CONTENT = os.environ.get('PROTECT_CONTENT', "True").lower() == "true"
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", "False").lower() == "true"
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", "<b>• Shared via File Store Bot</b>")

# Auto-delete timer (in seconds)
AUTO_DELETE_TIME = int(os.environ.get("AUTO_DELETE_TIME", "600"))  # 10 minutes default

# Text Messages
START_MSG = """
<b>👋 Hello {mention}!</b>

This is a private file store bot for authorized users only.

<b>🔒 Private Bot:</b>
• Only admins can use this bot
• Files are stored securely
• Auto-delete after download

<b>📁 Features:</b>
• Secure file storage
• Shareable links
• Auto file deletion
• Private access only
"""

HELP_TXT = """
<b>🔧 Admin Commands:</b>

• /start - Start the bot
• /help - Show this help
• /broadcast - Broadcast message to users
• /stats - Bot statistics
• /genlink - Generate file link
• /batch - Generate batch file links

<b>📝 Usage:</b>
1. Send any file to store it
2. Get a shareable link
3. Share with authorized users
"""

ABOUT_TXT = """
<b>🤖 Private File Store Bot</b>

<b>🔒 Features:</b>
• Private access only
• Secure file storage
• Auto file deletion
• Admin-only operations

<b>⚡ Version:</b> 2.0
<b>🔐 Access:</b> Admin Only
"""

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            "bot.log",
            maxBytes=5_000_000,  # 5MB
            backupCount=3
        ),
        logging.StreamHandler()
    ]
)

# Reduce noise from other libraries
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

LOGGER = get_logger(__name__)
