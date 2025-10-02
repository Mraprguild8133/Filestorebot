import os
import logging

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

# Admin IDs (comma separated)
ADMIN_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", str(OWNER_ID)).split(",") if x.strip()]

# Simple logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - %(message)s",
    datefmt='%H:%M:%S'
)

LOGGER = logging.getLogger(__name__)
