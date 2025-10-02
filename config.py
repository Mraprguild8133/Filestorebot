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

# Database Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DATABASE_NAME", "PrivateFileStore")

# Server Configuration
PORT = int(os.environ.get("PORT", 8000))

# Bot Settings
PROTECT_CONTENT = os.environ.get('PROTECT_CONTENT', "True").lower() == "true"
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", "False").lower() == "true"
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", "<b>• Shared via Private Bot</b>")

# Auto-delete timer (in seconds)
AUTO_DELETE_TIME = int(os.environ.get("AUTO_DELETE_TIME", "600"))  # 10 minutes default

# Text Messages
START_MSG = """
<b>👋 Hello {mention}!</b>

This is a private file store bot for authorized admins only.

<b>🔒 Admin Features:</b>
• Secure file storage
• Shareable links
• Auto-delete files
• Admin management

<b>📁 Commands:</b>
• /start - Start bot
• /help - Show commands
• /genlink - Generate file link
• /batch - Batch file links
• /admins - Admin list
"""

HELP_TXT = """
<b>🔧 Admin Commands:</b>

• /start - Start the bot
• /help - Show this help
• /genlink - Generate file link
• /batch - Generate batch links
• /broadcast - Broadcast to admins
• /stats - Bot statistics
• /admins - List all admins
• /add_admin - Add new admin
• /del_admin - Remove admin

<b>📝 Usage:</b>
1. Send file to store in channel
2. Get shareable link
3. Share with authorized users
"""

ABOUT_TXT = """
<b>🤖 Private File Store Bot</b>

<b>🔒 Features:</b>
• Admin-only access
• MongoDB storage
• Secure file sharing
• Auto file deletion

<b>⚡ Version:</b> 2.0 (Motor)
<b>💾 Database:</b> MongoDB
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
logging.getLogger("motor").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

LOGGER = get_logger(__name__)

# Backward compatibility
DB_URI = DATABASE_URL
