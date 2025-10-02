import base64
import re
import asyncio
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

from bot import Bot

async def check_admin(_, client, message):
    return Bot.is_admin(message.from_user.id)

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    return (base64_bytes.decode("ascii")).strip("=")

async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    return string_bytes.decode("ascii")

async def get_messages(client, message_ids):
    messages = []
    for msg_id in message_ids:
        try:
            msg = await client.get_messages(client.db_channel.id, message_ids=msg_id)
            if msg:
                messages.append(msg)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            msg = await client.get_messages(client.db_channel.id, message_ids=msg_id)
            if msg:
                messages.append(msg)
        except:
            pass
    return messages

async def get_message_id(client, message):
    if message.forward_from_chat and message.forward_from_chat.id == client.db_channel.id:
        return message.forward_from_message_id
    
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

# Create admin filter
admin = filters.create(check_admin)
