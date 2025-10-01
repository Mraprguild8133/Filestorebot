import motor.motor_asyncio
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from config import DB_URI, DB_NAME, get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """Complete database manager with all required methods."""
    
    def __init__(self, db_uri: str, db_name: str):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                db_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            self.db = self.client[db_name]
            self._setup_collections()
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise

    def _setup_collections(self):
        """Initialize all collections."""
        self.user_data = self.db['users']
        self.admins_data = self.db['admins']
        self.banned_user_data = self.db['banned_users']
        self.channel_data = self.db['channels']
        self.fsub_data = self.db['fsub']
        self.del_timer_data = self.db['del_timer']
        self.rqst_fsub_Channel_data = self.db['request_forcesub_channel']

    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False

    # ==================== USER MANAGEMENT ====================
    async def present_user(self, user_id: int) -> bool:
        """Check if user exists in database."""
        try:
            found = await self.user_data.find_one({'_id': user_id})
            return bool(found)
        except Exception as e:
            logger.error(f"Error checking user {user_id}: {e}")
            return False

    async def add_user(self, user_id: int) -> bool:
        """Add user to database."""
        try:
            await self.user_data.update_one(
                {'_id': user_id},
                {'$set': {'joined_at': datetime.now()}},
                upsert=True
            )
            logger.info(f"✅ User added: {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add user {user_id}: {e}")
            return False

    async def del_user(self, user_id: int) -> bool:
        """Remove user from database."""
        try:
            result = await self.user_data.delete_one({'_id': user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to delete user {user_id}: {e}")
            return False

    async def full_userbase(self) -> List[int]:
        """Get all user IDs."""
        try:
            user_docs = await self.user_data.find().to_list(length=None)
            user_ids = [doc['_id'] for doc in user_docs]
            return user_ids
        except Exception as e:
            logger.error(f"❌ Failed to get userbase: {e}")
            return []

    async def get_user_count(self) -> int:
        """Get total user count."""
        try:
            return await self.user_data.count_documents({})
        except Exception as e:
            logger.error(f"❌ Failed to get user count: {e}")
            return 0

    # ==================== ADMIN MANAGEMENT ====================
    async def admin_exist(self, admin_id: int) -> bool:
        """Check if admin exists."""
        try:
            found = await self.admins_data.find_one({'_id': admin_id})
            return bool(found)
        except Exception as e:
            logger.error(f"Error checking admin {admin_id}: {e}")
            return False

    async def add_admin(self, admin_id: int) -> bool:
        """Add admin user."""
        try:
            if not await self.admin_exist(admin_id):
                await self.admins_data.insert_one({
                    '_id': admin_id,
                    'added_at': datetime.now()
                })
                logger.info(f"✅ Admin added: {admin_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add admin {admin_id}: {e}")
            return False

    async def del_admin(self, admin_id: int) -> bool:
        """Remove admin user."""
        try:
            result = await self.admins_data.delete_one({'_id': admin_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to delete admin {admin_id}: {e}")
            return False

    async def get_all_admins(self) -> List[int]:
        """Get all admin IDs."""
        try:
            admin_docs = await self.admins_data.find().to_list(length=None)
            admin_ids = [doc['_id'] for doc in admin_docs]
            return admin_ids
        except Exception as e:
            logger.error(f"❌ Failed to get admins: {e}")
            return []

    # ==================== BAN MANAGEMENT ====================
    async def ban_user_exist(self, user_id: int) -> bool:
        """Check if user is banned."""
        try:
            found = await self.banned_user_data.find_one({'_id': user_id})
            return bool(found)
        except Exception as e:
            logger.error(f"Error checking banned user {user_id}: {e}")
            return False

    async def add_ban_user(self, user_id: int) -> bool:
        """Ban a user."""
        try:
            if not await self.ban_user_exist(user_id):
                await self.banned_user_data.insert_one({
                    '_id': user_id,
                    'banned_at': datetime.now()
                })
                logger.info(f"✅ User banned: {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to ban user {user_id}: {e}")
            return False

    async def del_ban_user(self, user_id: int) -> bool:
        """Unban a user."""
        try:
            result = await self.banned_user_data.delete_one({'_id': user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to unban user {user_id}: {e}")
            return False

    async def get_ban_users(self) -> List[int]:
        """Get all banned user IDs."""
        try:
            ban_docs = await self.banned_user_data.find().to_list(length=None)
            ban_ids = [doc['_id'] for doc in ban_docs]
            return ban_ids
        except Exception as e:
            logger.error(f"❌ Failed to get banned users: {e}")
            return []

    # ==================== CHANNEL MANAGEMENT ====================
    async def channel_exist(self, channel_id: int) -> bool:
        """Check if channel exists."""
        try:
            found = await self.fsub_data.find_one({'_id': channel_id})
            return bool(found)
        except Exception as e:
            logger.error(f"Error checking channel {channel_id}: {e}")
            return False

    async def add_channel(self, channel_id: int, title: str = "") -> bool:
        """Add force-sub channel."""
        try:
            if not await self.channel_exist(channel_id):
                await self.fsub_data.insert_one({
                    '_id': channel_id,
                    'title': title,
                    'mode': 'off',
                    'added_at': datetime.now()
                })
                logger.info(f"✅ Channel added: {channel_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add channel {channel_id}: {e}")
            return False

    async def rem_channel(self, channel_id: int) -> bool:
        """Remove force-sub channel."""
        try:
            result = await self.fsub_data.delete_one({'_id': channel_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to remove channel {channel_id}: {e}")
            return False

    async def show_channels(self) -> List[int]:
        """Get all channel IDs."""
        try:
            channel_docs = await self.fsub_data.find().to_list(length=None)
            channel_ids = [doc['_id'] for doc in channel_docs]
            return channel_ids
        except Exception as e:
            logger.error(f"❌ Failed to get channels: {e}")
            return []

    async def get_channel_mode(self, channel_id: int) -> str:
        """Get channel force-sub mode."""
        try:
            channel = await self.fsub_data.find_one({'_id': channel_id})
            return channel.get('mode', 'off') if channel else 'off'
        except Exception as e:
            logger.error(f"❌ Failed to get channel mode for {channel_id}: {e}")
            return 'off'

    async def set_channel_mode(self, channel_id: int, mode: str) -> bool:
        """Set channel force-sub mode."""
        try:
            await self.fsub_data.update_one(
                {'_id': channel_id},
                {'$set': {'mode': mode}},
                upsert=True
            )
            logger.info(f"✅ Channel {channel_id} mode set to: {mode}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to set channel mode for {channel_id}: {e}")
            return False

    # ==================== AUTO DELETE TIMER ====================
    async def set_del_timer(self, seconds: int) -> bool:
        """Set auto-delete timer."""
        try:
            await self.del_timer_data.update_one(
                {'key': 'delete_timer'},
                {'$set': {'value': seconds}},
                upsert=True
            )
            logger.info(f"✅ Delete timer set to: {seconds} seconds")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to set delete timer: {e}")
            return False

    async def get_del_timer(self) -> int:
        """Get auto-delete timer value."""
        try:
            setting = await self.del_timer_data.find_one({'key': 'delete_timer'})
            return setting.get('value', 600) if setting else 600  # Default 10 minutes
        except Exception as e:
            logger.error(f"❌ Failed to get delete timer: {e}")
            return 600

    # ==================== FORCE SUB REQUEST MANAGEMENT ====================
    async def req_user(self, channel_id: int, user_id: int) -> bool:
        """Add user to join request list."""
        try:
            await self.rqst_fsub_Channel_data.update_one(
                {'_id': channel_id},
                {'$addToSet': {'user_ids': user_id}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add join request: {e}")
            return False

    async def del_req_user(self, channel_id: int, user_id: int) -> bool:
        """Remove user from join request list."""
        try:
            await self.rqst_fsub_Channel_data.update_one(
                {'_id': channel_id},
                {'$pull': {'user_ids': user_id}}
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to remove join request: {e}")
            return False

    async def req_user_exist(self, channel_id: int, user_id: int) -> bool:
        """Check if user has pending join request."""
        try:
            found = await self.rqst_fsub_Channel_data.find_one({
                '_id': channel_id,
                'user_ids': user_id
            })
            return bool(found)
        except Exception as e:
            logger.error(f"❌ Failed to check join request: {e}")
            return False

    async def reqChannel_exist(self, channel_id: int) -> bool:
        """Check if channel exists in force-sub list."""
        try:
            channel_ids = await self.show_channels()
            return channel_id in channel_ids
        except Exception as e:
            logger.error(f"❌ Failed to check channel existence: {e}")
            return False

    async def has_pending_request(self, channel_id: int, user_id: int) -> bool:
        """Alias for req_user_exist for compatibility."""
        return await self.req_user_exist(channel_id, user_id)

    async def get_all_channels(self) -> List[int]:
        """Alias for show_channels for compatibility."""
        return await self.show_channels()

    async def is_admin(self, user_id: int) -> bool:
        """Alias for admin_exist for compatibility."""
        return await self.admin_exist(user_id)

    # ==================== MAINTENANCE METHODS ====================
    async def cleanup_old_data(self, days: int = 30):
        """Cleanup old data (optional maintenance)."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            # Example: Remove users who haven't been active
            # Implement based on your needs
            logger.info("🔄 Database cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            return {
                'total_users': await self.get_user_count(),
                'total_admins': len(await self.get_all_admins()),
                'total_banned': len(await self.get_ban_users()),
                'total_channels': len(await self.show_channels()),
                'delete_timer': await self.get_del_timer()
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {}

# Global database instance
db = DatabaseManager(DB_URI, DB_NAME)
