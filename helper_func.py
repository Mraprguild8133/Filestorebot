import base64
import re
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserNotParticipant

from config import *
from database.database import db

class HelperFunctions:
    """Enhanced helper functions with better error handling."""
    
    @staticmethod
    async def check_admin(client, message: Message) -> bool:
        """Check if user is admin or owner."""
        try:
            user_id = message.from_user.id
            return user_id == OWNER_ID or await db.is_admin(user_id)
        except Exception as e:
            logger.error(f"Admin check failed: {e}")
            return False

    @staticmethod
    async def is_subscribed(client, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if user is subscribed to all channels.
        Returns (is_subscribed, missing_channel_info)
        """
        try:
            channels = await db.get_all_channels()
            
            if not channels:
                return True, None
                
            if user_id == OWNER_ID:
                return True, None
                
            for channel_id in channels:
                is_sub, channel_info = await HelperFunctions.is_sub(client, user_id, channel_id)
                if not is_sub:
                    return False, channel_info
                    
            return True, None
            
        except Exception as e:
            logger.error(f"Subscription check failed: {e}")
            return False, "Error checking subscription"

    @staticmethod
    async def is_sub(client, user_id: int, channel_id: int) -> Tuple[bool, Optional[str]]:
        """Check subscription for a specific channel."""
        try:
            # Get channel info
            channel = await client.get_chat(channel_id)
            channel_mode = await db.get_channel_mode(channel_id)
            
            try:
                member = await client.get_chat_member(channel_id, user_id)
                if member.status in {
                    ChatMemberStatus.OWNER,
                    ChatMemberStatus.ADMINISTRATOR,
                    ChatMemberStatus.MEMBER
                }:
                    return True, None
                    
            except UserNotParticipant:
                if channel_mode == "on":
                    # Check if user has pending join request
                    has_request = await db.has_pending_request(channel_id, user_id)
                    return has_request, f"{channel.title} (Join Request Pending)"
                return False, channel.title
                
            return False, channel.title
            
        except Exception as e:
            logger.error(f"Channel subscription check failed for {channel_id}: {e}")
            return False, "Unknown Channel"

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
    async def get_messages_batch(client, message_ids: List[int]) -> List[Message]:
        """Get messages in batches to avoid FloodWait."""
        messages = []
        batch_size = 100  # Telegram limit
        
        for i in range(0, len(message_ids), batch_size):
            batch_ids = message_ids[i:i + batch_size]
            
            try:
                batch_messages = await client.get_messages(
                    chat_id=client.db_channel.id,
                    message_ids=batch_ids
                )
                messages.extend(batch_messages)
                
            except FloodWait as e:
                logger.warning(f"FloodWait: Sleeping for {e.value}s")
                await asyncio.sleep(e.value)
                batch_messages = await client.get_messages(
                    chat_id=client.db_channel.id,
                    message_ids=batch_ids
                )
                messages.extend(batch_messages)
                
            except Exception as e:
                logger.error(f"Failed to get messages batch: {e}")
                continue
                
        return messages

    @staticmethod
    def get_readable_time(seconds: int) -> str:
        """Convert seconds to human readable time."""
        periods = [
            ('year', 31536000),
            ('month', 2592000),
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
                    result.append(f"{period_value} {period_name}{'s' if period_value > 1 else ''}")
                    
        return ", ".join(result) if result else "0 seconds"

    @staticmethod
    def get_expiry_time(seconds: int) -> str:
        """Get expiry time in friendly format."""
        return HelperFunctions.get_readable_time(seconds)

    @staticmethod
    async def extract_message_id(client, message: Message) -> Optional[int]:
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
                    
                    # Validate channel
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

# Create filters
admin_filter = filters.create(HelperFunctions.check_admin)

# Backward compatibility functions
async def check_admin(filter, client, update):
    return await HelperFunctions.check_admin(client, update)

async def is_subscribed(client, user_id):
    result, _ = await HelperFunctions.is_subscribed(client, user_id)
    return result

async def encode(string):
    return await HelperFunctions.encode_string(string)

async def decode(base64_string):
    return await HelperFunctions.decode_string(base64_string)

async def get_messages(client, message_ids):
    return await HelperFunctions.get_messages_batch(client, message_ids)

async def get_message_id(client, message):
    return await HelperFunctions.extract_message_id(client, message)

def get_readable_time(seconds):
    return HelperFunctions.get_readable_time(seconds)

def get_exp_time(seconds):
    return HelperFunctions.get_expiry_time(seconds)

# Filters
subscribed = filters.create(is_subscribed)
admin = filters.create(check_admin)
