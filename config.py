# Copyright (C) 2025 by Codeflix-Bots@Github
# All rights reserved.

import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Initialize logging before anything else
LOG_FILE_NAME = "filesharingbot.log"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def get_env_var(name, default=None, required=False):
    """Helper function to get environment variables"""
    value = os.environ.get(name, default)
    if required and value is None:
        logging.error(f"Missing required environment variable: {name}")
        raise ValueError(f"Missing required environment variable: {name}")
    return value

# ============================ REQUIRED CONFIG ==============================
try:
    #Bot token @Botfather
TG_BOT_TOKEN = int(os.environ.get("TG_BOT_TOKEN", ""))

#Your API ID from my.telegram.org
APP_ID = int(os.environ.get("APP_ID", ""))

#Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "")
    # Channel and owner info
    CHANNEL_ID = int(get_env_var("CHANNEL_ID", "-1002170811388"))
    OWNER = get_env_var("OWNER", "sewxiy")
    OWNER_ID = int(get_env_var("OWNER_ID", "7328629001"))
    
    # Database configuration
    DB_URI = get_env_var("DATABASE_URL", required=True)
    DB_NAME = get_env_var("DATABASE_NAME", "Cluooo")
    
except Exception as e:
    logging.critical(f"Configuration error: {str(e)}")
    raise

# ============================ OPTIONAL CONFIG ==============================
# Server configuration
PORT = int(get_env_var("PORT", "8001"))

# Feature toggles
PROTECT_CONTENT = get_env_var('PROTECT_CONTENT', "False").lower() == "true"
DISABLE_CHANNEL_BUTTON = get_env_var("DISABLE_CHANNEL_BUTTON", "False").lower() == "true"
FSUB_LINK_EXPIRY = int(get_env_var("FSUB_LINK_EXPIRY", "10"))  # In seconds

# URLs and resources
BAN_SUPPORT = get_env_var("BAN_SUPPORT", "https://t.me/CodeflixSupport")
START_PIC = get_env_var("START_PIC", "https://telegra.ph/file/ec17880d61180d3312d6a.jpg")
FORCE_PIC = get_env_var("FORCE_PIC", "https://telegra.ph/file/e292b12890b8b4b9dcbd1.jpg")
CUSTOM_CAPTION = get_env_var("CUSTOM_CAPTION", "<b>• ʙʏ @nova_flix</b>")

# Performance settings
TG_BOT_WORKERS = int(get_env_var("TG_BOT_WORKERS", "200"))

# Message templates
START_MSG = get_env_var(
    "START_MESSAGE",
    "<b>ʜᴇʟʟᴏ {mention}\n\n<blockquote>ɪ ᴀᴍ ғɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ, ɪ ᴄᴀɴ sᴛᴏʀᴇ ᴘʀɪᴠᴀᴛᴇ ғɪʟᴇs ɪɴ sᴘᴇᴄɪғɪᴇᴅ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴏᴛʜᴇʀ �sᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss ɪᴛ ғʀᴏᴍ sᴘᴇᴄɪᴀʟ ʟɪɴᴋ.</blockquote></b>"
)

FORCE_MSG = get_env_var(
    "FORCE_SUB_MESSAGE",
    "ʜᴇʟʟᴏ {mention}\n\n<b><blockquote>ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʀᴇʟᴏᴀᴅ button ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛᴇᴅ ꜰɪʟᴇ.</b></blockquote>"
)

HELP_TXT = get_env_var(
    "HELP_TEXT",
    """<b><blockquote>ᴛʜɪs ɪs ᴀɴ ғɪʟᴇ ᴛᴏ ʟɪɴᴋ ʙᴏᴛ ᴡᴏʀᴋ ғᴏʀ @Nova_Flix

❏ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs
├/start : sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ
├/about : ᴏᴜʀ Iɴғᴏʀᴍᴀᴛɪᴏɴ
└/help : ʜᴇʟᴘ ʀᴇʟᴀᴛᴇᴅ ʙᴏᴛ

sɪᴍᴘʟʏ ᴄʟɪᴄᴋ ᴏɴ ʟɪɴᴋ ᴀɴᴅ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ᴊᴏɪɴ ʙᴏᴛʜ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴛʜᴀᴛs ɪᴛ.....!

ᴅᴇᴠᴇʟᴏᴘᴇᴅ ʙʏ <a href=https://t.me/cosmic_freak>sᴜʙᴀʀᴜ</a></blockquote></b>"""
)

ABOUT_TXT = get_env_var(
    "ABOUT_TEXT",
    """<b><blockquote>◈ ᴄʀᴇᴀᴛᴏʀ: <a href=https://t.me/cosmic_freak>Yato</a>
◈ ꜰᴏᴜɴᴅᴇʀ ᴏꜰ : <a href=https://t.me/otakuflix_network>ᴏᴛᴀᴋᴜғʟɪx ɴᴇᴛᴡᴏʀᴋ</a>
◈ ᴀɴɪᴍᴇ ᴄʜᴀɴɴᴇʟ : <a href=https://t.me/anime_cruise_netflix>ᴀɴɪᴍᴇ ᴄʀᴜɪsᴇ</a>
◈ sᴇʀɪᴇs ᴄʜᴀɴɴᴇʟ : <a href=https://t.me/webseries_flix>ᴡᴇʙsᴇʀɪᴇs ғʟɪx</a>
◈ ᴀᴅᴜʟᴛ ᴍᴀɴʜᴡᴀ : <a href=https://t.me/pornhwa_flix>ᴘᴏʀɴʜᴡᴀs</a>
◈ ᴅᴇᴠᴇʟᴏᴘᴇʀ : <a href=https://t.me/cosmic_freak>subaru</a></blockquote></b>"""
)

CMD_TXT = """<blockquote><b>» ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs:</b></blockquote>

<b>›› /dlt_time :</b> sᴇᴛ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ
<b>›› /check_dlt_time :</b> ᴄʜᴇᴄᴋ ᴄᴜʀʀᴇɴᴛ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ
<b>›› /dbroadcast :</b> ʙʀᴏᴀᴅᴄᴀsᴛ ᴅᴏᴄᴜᴍᴇɴᴛ / ᴠɪᴅᴇᴏ
<b>›› /ban :</b> ʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /unban :</b> ᴜɴʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /banlist :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ʙᴀɴɴᴇᴅ ᴜꜱᴇʀs
<b>›› /addchnl :</b> ᴀᴅᴅ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /delchnl :</b> ʀᴇᴍᴏᴠᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /listchnl :</b> �ᴠɪᴇᴡ ᴀᴅᴅᴇᴅ ᴄʜᴀɴɴᴇʟs
<b>›› /fsub_mode :</b> ᴛᴏɢɢʟᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴍᴏᴅᴇ
<b>›› /pbroadcast :</b> sᴇɴᴅ ᴘʜᴏᴛᴏ ᴛᴏ ᴀʟʟ �sᴇʀs
<b>›› /add_admin :</b> ᴀᴅᴅ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /deladmin :</b> ʀᴇᴍᴏᴠᴇ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /admins :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ᴀᴅᴍɪɴs
<b>›› /delreq :</b> Rᴇᴍᴏᴠᴇᴅ ʟᴇғᴛᴏᴠᴇʀ ɴᴏɴ-ʀᴇǫᴜᴇsᴛ ᴜsᴇʀs
"""

BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "ʙᴀᴋᴋᴀ ! ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍʏ ꜱᴇɴᴘᴀɪ!!"

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

# Validate critical configuration
if not all([TG_BOT_TOKEN, APP_ID, API_HASH, DB_URI]):
    logging.critical("Missing one or more required configuration parameters!")
    raise ValueError("Missing required configuration parameters")

logging.info("Configuration loaded successfully")
