import base64
import re
import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserNotParticipant, ChatAdminRequired

from config import OWNER_ID, LOGGER
from database.database import db

logger = logging.getLogger(__name__)

class HelperFunctions:
    """Enhanced helper functions with comprehensive error handling and utilities."""
    
    @staticmethod
    async def check_admin(client, message: Message) -> bool:
        """
        Check if user is admin or owner.
        
        Args:
            client: Bot client
            message: Message object
            
        Returns:
            bool: True if user is admin/owner, False otherwise
        """
        try:
            user_id = message.from_user.id
            is_owner = user_id == OWNER_ID
            is_admin = await db.admin_exist(user_id)
            
            logger.debug(f"Admin check for user {user_id}: owner={is_owner}, admin={is_admin}")
            return is_owner or is_admin
            
        except Exception as e:
            logger.error(f"Admin check failed for user {getattr(message.from_user, 'id', 'Unknown')}: {e}")
            return False

    @staticmethod
    async def is_subscribed(client, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if user is subscribed to all force-sub channels.
        
        Args:
            client: Bot client
            user_id: User ID to check
            
        Returns:
            Tuple[bool, Optional[str]]: (is_subscribed, missing_channel_info)
        """
        try:
            channels = await db.show_channels()
            
            if not channels:
                logger.debug(f"No force-sub channels for user {user_id}")
                return True, None
                
            if user_id == OWNER_ID:
                logger.debug(f"User {user_id} is owner, bypassing subscription check")
                return True, None
                
            # Check if user is admin (admins bypass force-sub)
            if await db.admin_exist(user_id):
                logger.debug(f"User {user_id} is admin, bypassing subscription check")
                return True, None
                
            for channel_id in channels:
                is_sub, channel_info = await HelperFunctions.is_sub(client, user_id, channel_id)
                if not is_sub:
                    logger.info(f"User {user_id} not subscribed to {channel_info}")
                    return False, channel_info
                    
            logger.debug(f"User {user_id} is subscribed to all channels")
            return True, None
            
        except Exception as e:
            logger.error(f"Subscription check failed for user {user_id}: {e}")
            return False, "Error checking subscription"

    @staticmethod
    async def is_sub(client, user_id: int, channel_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check subscription for a specific channel.
        
        Args:
            client: Bot client
            user_id: User ID to check
            channel_id: Channel ID to check
            
        Returns:
            Tuple[bool, Optional[str]]: (is_subscribed, channel_info)
        """
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
                    logger.debug(f"User {user_id} is member of {channel.title}")
                    return True, None
                    
            except UserNotParticipant:
                if channel_mode == "on":
                    # Check if user has pending join request
                    has_request = await db.req_user_exist(channel_id, user_id)
                    logger.debug(f"User {user_id} join request for {channel.title}: {has_request}")
                    return has_request, f"{channel.title} (Join Request Pending)"
                
                logger.debug(f"User {user_id} not participant in {channel.title}")
                return False, channel.title
                
            except ChatAdminRequired:
                logger.warning(f"Bot needs admin rights in {channel.title} to check membership")
                return False, f"{channel.title} (Bot needs admin)"
                
            logger.debug(f"User {user_id} not member of {channel.title}")
            return False, channel.title
            
        except Exception as e:
            logger.error(f"Channel subscription check failed for {channel_id}: {e}")
            return False, "Unknown Channel"

    @staticmethod
    async def encode_string(string: str) -> str:
        """
        Encode string to base64 URL-safe.
        
        Args:
            string: String to encode
            
        Returns:
            str: Base64 encoded string
        """
        try:
            string_bytes = string.encode("ascii")
            base64_bytes = base64.urlsafe_b64encode(string_bytes)
            base64_string = (base64_bytes.decode("ascii")).strip("=")
            logger.debug(f"Encoded string: {string} -> {base64_string}")
            return base64_string
        except Exception as e:
            logger.error(f"Encoding failed for string: {e}")
            raise

    @staticmethod
    async def decode_string(base64_string: str) -> str:
        """
        Decode base64 URL-safe string.
        
        Args:
            base64_string: Base64 string to decode
            
        Returns:
            str: Decoded string
        """
        try:
            base64_string = base64_string.strip("=")
            base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
            string_bytes = base64.urlsafe_b64decode(base64_bytes)
            string = string_bytes.decode("ascii")
            logger.debug(f"Decoded string: {base64_string} -> {string}")
            return string
        except Exception as e:
            logger.error(f"Decoding failed for base64 string: {e}")
            raise

    @staticmethod
    async def get_messages_batch(client, message_ids: List[int]) -> List[Message]:
        """
        Get messages in batches to avoid FloodWait.
        
        Args:
            client: Bot client
            message_ids: List of message IDs
            
        Returns:
            List[Message]: List of message objects
        """
        messages = []
        batch_size = 100  # Telegram limit
        
        if not message_ids:
            logger.warning("No message IDs provided")
            return messages
        
        logger.info(f"Fetching {len(message_ids)} messages in batches of {batch_size}")
        
        for i in range(0, len(message_ids), batch_size):
            batch_ids = message_ids[i:i + batch_size]
            
            try:
                batch_messages = await client.get_messages(
                    chat_id=client.db_channel.id,
                    message_ids=batch_ids
                )
                
                # Handle single message or list
                if isinstance(batch_messages, list):
                    messages.extend(batch_messages)
                else:
                    messages.append(batch_messages)
                
                logger.debug(f"Fetched batch {i//batch_size + 1}: {len(batch_ids)} messages")
                
            except FloodWait as e:
                logger.warning(f"FloodWait: Sleeping for {e.value}s")
                await asyncio.sleep(e.value)
                
                # Retry after flood wait
                try:
                    batch_messages = await client.get_messages(
                        chat_id=client.db_channel.id,
                        message_ids=batch_ids
                    )
                    
                    if isinstance(batch_messages, list):
                        messages.extend(batch_messages)
                    else:
                        messages.append(batch_messages)
                        
                except Exception as retry_error:
                    logger.error(f"Failed to retry batch {i//batch_size + 1}: {retry_error}")
                    
            except Exception as e:
                logger.error(f"Failed to get messages batch {i//batch_size + 1}: {e}")
                continue
                
        logger.info(f"Successfully fetched {len(messages)}/{len(message_ids)} messages")
        return messages

    @staticmethod
    async def extract_message_id(client, message: Message) -> Optional[int]:
        """
        Extract message ID from forwarded message or link.
        
        Args:
            client: Bot client
            message: Message object
            
        Returns:
            Optional[int]: Message ID or None
        """
        try:
            # From forwarded message
            if (message.forward_from_chat and 
                message.forward_from_chat.id == client.db_channel.id):
                msg_id = message.forward_from_message_id
                logger.debug(f"Extracted message ID from forward: {msg_id}")
                return msg_id
            
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
                            logger.debug(f"Extracted message ID from numeric link: {msg_id}")
                            return msg_id
                    else:
                        if channel_ref == client.db_channel.username:
                            logger.debug(f"Extracted message ID from username link: {msg_id}")
                            return msg_id
                            
            logger.debug("No valid message ID found in message")
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract message ID: {e}")
            return None

    @staticmethod
    def get_readable_time(seconds: int) -> str:
        """
        Convert seconds to human readable time.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            str: Human readable time string
        """
        if seconds <= 0:
            return "0 seconds"
            
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
        """
        Get expiry time in friendly format.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            str: Formatted expiry time
        """
        return HelperFunctions.get_readable_time(seconds)

    @staticmethod
    def validate_user_ids(user_ids: List[str]) -> tuple[List[int], List[str]]:
        """
        Validate and convert user IDs from string to integer.
        
        Args:
            user_ids: List of user ID strings
            
        Returns:
            tuple[List[int], List[str]]: (valid_ids, invalid_ids)
        """
        valid_ids = []
        invalid_ids = []
        
        for user_id in user_ids:
            try:
                # Check if it's a valid integer and positive
                uid = int(user_id)
                if uid > 0:
                    valid_ids.append(uid)
                else:
                    invalid_ids.append(f"Invalid ID (negative): {user_id}")
            except (ValueError, TypeError):
                invalid_ids.append(f"Invalid format: {user_id}")
        
        return valid_ids, invalid_ids

    @staticmethod
    async def schedule_auto_delete(client, messages: List[Message], notification_msg: Message, 
                                 delete_after: int, reload_url: str = None):
        """
        Schedule automatic deletion of messages.
        
        Args:
            client: Bot client
            messages: List of messages to delete
            notification_msg: Notification message
            delete_after: Delete after seconds
            reload_url: URL for reload button
        """
        try:
            logger.info(f"Scheduling auto-delete for {len(messages)} messages after {delete_after}s")
            await asyncio.sleep(delete_after)
            
            # Delete all messages
            deleted_count = 0
            for msg in messages:
                if msg:
                    try:
                        await msg.delete()
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Failed to delete message {msg.id}: {e}")
            
            # Update notification
            try:
                keyboard = None
                if reload_url:
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Get File Again", url=reload_url)]
                    ])

                await notification_msg.edit(
                    f"**🗑️ Auto-Deletion Complete**\n\n"
                    f"• Deleted {deleted_count} files\n"
                    f"• Reload to get files again",
                    reply_markup=keyboard
                )
                
                logger.info(f"Auto-deletion completed: {deleted_count}/{len(messages)} messages deleted")
                
            except Exception as e:
                logger.error(f"Failed to update notification: {e}")
                
        except Exception as e:
            logger.error(f"Auto-delete scheduling failed: {e}")

    @staticmethod
    async def create_file_link(client, message_id: int, batch: bool = False, 
                             start_id: int = None, end_id: int = None) -> str:
        """
        Create file sharing link.
        
        Args:
            client: Bot client
            message_id: Message ID
            batch: Whether it's a batch link
            start_id: Start ID for batch
            end_id: End ID for batch
            
        Returns:
            str: File sharing link
        """
        try:
            if batch and start_id is not None and end_id is not None:
                string = f"get-{start_id}-{end_id}"
            else:
                string = f"get-{message_id}"
            
            base64_string = await HelperFunctions.encode_string(string)
            link = f"https://t.me/{client.username}?start={base64_string}"
            
            logger.debug(f"Created {'batch ' if batch else ''}link: {link}")
            return link
            
        except Exception as e:
            logger.error(f"Failed to create file link: {e}")
            raise

# ==================== BACKWARD COMPATIBILITY FUNCTIONS ====================

async def check_admin(filter, client, update):
    """
    Backward compatibility function for admin filter.
    Used by Pyrogram's filters.create()
    """
    return await HelperFunctions.check_admin(client, update)

async def is_subscribed(client, user_id: int) -> bool:
    """
    Backward compatibility function for subscription check.
    Returns only boolean for filter compatibility.
    """
    try:
        result, _ = await HelperFunctions.is_subscribed(client, user_id)
        return result
    except Exception as e:
        logger.error(f"Subscription check failed: {e}")
        return False

async def is_sub(client, user_id: int, channel_id: int) -> bool:
    """
    Backward compatibility function for single channel subscription check.
    """
    try:
        result, _ = await HelperFunctions.is_sub(client, user_id, channel_id)
        return result
    except Exception as e:
        logger.error(f"Single channel subscription check failed: {e}")
        return False

async def encode(string: str) -> str:
    """Backward compatibility for encoding."""
    return await HelperFunctions.encode_string(string)

async def decode(base64_string: str) -> str:
    """Backward compatibility for decoding."""
    return await HelperFunctions.decode_string(base64_string)

async def get_messages(client, message_ids: List[int]) -> List[Message]:
    """Backward compatibility for getting messages."""
    return await HelperFunctions.get_messages_batch(client, message_ids)

async def get_message_id(client, message: Message) -> Optional[int]:
    """Backward compatibility for extracting message ID."""
    return await HelperFunctions.extract_message_id(client, message)

def get_readable_time(seconds: int) -> str:
    """Backward compatibility for readable time."""
    return HelperFunctions.get_readable_time(seconds)

def get_exp_time(seconds: int) -> str:
    """Backward compatibility for expiry time."""
    return HelperFunctions.get_expiry_time(seconds)

def validate_user_ids(user_ids: List[str]) -> tuple[List[int], List[str]]:
    """Backward compatibility for user ID validation."""
    return HelperFunctions.validate_user_ids(user_ids)

async def schedule_auto_delete(client, messages: List[Message], notification_msg: Message, 
                             file_auto_delete: int, reload_url: str = None):
    """Backward compatibility for auto-delete scheduling."""
    return await HelperFunctions.schedule_auto_delete(
        client, messages, notification_msg, file_auto_delete, reload_url
    )

# ==================== FILTER CREATION ====================

# Create Pyrogram filters
admin_filter = filters.create(check_admin)
subscribed = filters.create(is_subscribed)

# For backward compatibility with existing code
admin = admin_filter

# ==================== ADDITIONAL UTILITY FUNCTIONS ====================

async def not_joined(client: Client, message: Message):
    """
    Handle users who haven't joined required channels.
    This function should be implemented in start.py
    """
    from plugins.start import not_joined as actual_not_joined
    return await actual_not_joined(client, message)

async def get_messages_safe(client, message_ids: List[int]) -> List[Message]:
    """
    Safe wrapper for get_messages with enhanced error handling.
    
    Args:
        client: Bot client
        message_ids: List of message IDs
        
    Returns:
        List[Message]: List of successfully fetched messages
    """
    try:
        messages = await get_messages(client, message_ids)
        successful_messages = [msg for msg in messages if msg is not None]
        
        if len(successful_messages) != len(message_ids):
            logger.warning(f"Fetched {len(successful_messages)}/{len(message_ids)} messages successfully")
            
        return successful_messages
        
    except Exception as e:
        logger.error(f"Safe message fetch failed: {e}")
        return []

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
        return f"{size_bytes:.2f} {size_names[i]}"

def create_share_button(link: str) -> InlineKeyboardMarkup:
    """
    Create share button for file links.
    
    Args:
        link: File sharing link
        
    Returns:
        InlineKeyboardMarkup: Share button markup
    """
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔗 Share URL", url=f'https://telegram.me/share/url?url={link}')
    ]])
    # Export the helper class for external use
Helper = HelperFunctions

logger.info("✅ Helper functions loaded successfully")
