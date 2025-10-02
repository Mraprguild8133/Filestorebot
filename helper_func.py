import base64
import re
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserNotParticipant, ChatAdminRequired

from config import OWNER_ID, LOGGER
from database.database import db

logger = logging.getLogger(__name__)

class HelperFunctions:
    """Helper functions for private bot with Motor."""
    
    @staticmethod
    async def check_admin(client: Client, message: Message) -> bool:
        """Check if user is admin."""
        try:
            user_id = message.from_user.id
            is_admin = await db.is_admin(user_id)
            
            if not is_admin:
                logger.warning(f"Non-admin access attempt by {user_id}")
                
            return is_admin
            
        except Exception as e:
            logger.error(f"Admin check failed: {e}")
            return False

    @staticmethod
    async def check_admin_filter(filter, client: Client, message: Message) -> bool:
        """Check if user is admin for Pyrogram filter."""
        return await HelperFunctions.check_admin(client, message)

    @staticmethod
    async def encode_string(string: str) -> str:
        """Encode string to base64 URL-safe."""
        try:
            string_bytes = string.encode("ascii")
            base64_bytes = base64.urlsafe_b64encode(string_bytes)
            return (base64_bytes.decode("ascii")).strip("=")
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            raise

    @staticmethod
    async def decode_string(base64_string: str) -> str:
        """Decode base64 URL-safe string."""
        try:
            base64_string = base64_string.strip("=")
            base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
            string_bytes = base64.urlsafe_b64decode(base64_bytes)
            return string_bytes.decode("ascii")
        except Exception as e:
            logger.error(f"Decoding failed: {e}")
            raise

    @staticmethod
    async def get_messages(client: Client, message_ids: List[int]) -> List[Message]:
        """Get messages from database channel."""
        messages = []
        
        for msg_id in message_ids:
            try:
                msg = await client.get_messages(
                    chat_id=client.db_channel.id,
                    message_ids=msg_id
                )
                if msg:
                    messages.append(msg)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                msg = await client.get_messages(
                    chat_id=client.db_channel.id,
                    message_ids=msg_id
                )
                if msg:
                    messages.append(msg)
            except Exception as e:
                logger.error(f"Failed to get message {msg_id}: {e}")
        
        return messages

    @staticmethod
    async def get_message_id(client: Client, message: Message) -> Optional[int]:
        """Extract message ID from forwarded message or link."""
        try:
            # From forwarded message
            if (message.forward_from_chat and 
                message.forward_from_chat.id == client.db_channel.id):
                return message.forward_from_message_id
            
            # From text link
            if message.text:
                pattern = r"https://t.me/(?:c/)?(.*)/(\d+)"
                matches = re.match(pattern, message.text)
                if matches:
                    channel_ref = matches.group(1)
                    msg_id = int(matches.group(2))
                    
                    if channel_ref.isdigit():
                        if f"-100{channel_ref}" == str(client.db_channel.id):
                            return msg_id
                    else:
                        if channel_ref == client.db_channel.username:
                            return msg_id
                            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract message ID: {e}")
            return None

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

    @staticmethod
    async def schedule_auto_delete(client: Client, messages: List[Message], 
                                 notification_msg: Message, delete_after: int):
        """Schedule automatic deletion of messages."""
        try:
            await asyncio.sleep(delete_after)
            
            # Delete all messages
            for msg in messages:
                if msg:
                    try:
                        await msg.delete()
                    except Exception as e:
                        logger.error(f"Failed to delete message: {e}")

            # Update notification
            try:
                await notification_msg.edit("🗑️ Files have been automatically deleted.")
            except Exception as e:
                logger.error(f"Failed to update notification: {e}")
                
        except Exception as e:
            logger.error(f"Auto-delete scheduling failed: {e}")

    @staticmethod
    async def get_auto_delete_time() -> int:
        """Get auto-delete time from database."""
        return await db.get_auto_delete_time()

# Backward compatibility functions
async def check_admin(filter, client, message):
    return await HelperFunctions.check_admin_filter(filter, client, message)

async def encode(string):
    return await HelperFunctions.encode_string(string)

async def decode(base64_string):
    return await HelperFunctions.decode_string(base64_string)

async def get_messages(client, message_ids):
    return await HelperFunctions.get_messages(client, message_ids)

async def get_message_id(client, message):
    return await HelperFunctions.get_message_id(client, message)

def get_readable_time(seconds):
    return HelperFunctions.get_readable_time(seconds)

# Create filters
admin_filter = filters.create(check_admin)
admin = admin_filter  # Alias for backward compatibility

logger.info("✅ Helper functions loaded successfully")
