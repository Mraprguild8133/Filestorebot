import motor.motor_asyncio
from typing import List, Optional, Dict, Any
import logging
from config import DB_URI, DB_NAME, get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """Enhanced database manager with better error handling and performance."""
    
    def __init__(self, db_uri: str, db_name: str):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                db_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            self.db = self.client[db_name]
            self._setup_collections()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _setup_collections(self):
        """Initialize all collections."""
        self.users = self.db['users']
        self.admins = self.db['admins']
        self.banned_users = self.db['banned_users']
        self.channels = self.db['channels']
        self.settings = self.db['settings']
        self.join_requests = self.db['join_requests']

    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    # User Management
    async def add_user(self, user_id: int) -> bool:
        """Add user to database."""
        try:
            await self.users.update_one(
                {'_id': user_id},
                {'$set': {'joined_at': datetime.now()}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add user {user_id}: {e}")
            return False

    async def get_user_count(self) -> int:
        """Get total user count."""
        try:
            return await self.users.count_documents({})
        except Exception as e:
            logger.error(f"Failed to get user count: {e}")
            return 0

    # Admin Management
    async def add_admin(self, user_id: int) -> bool:
        """Add admin user."""
        try:
            await self.admins.update_one(
                {'_id': user_id},
                {'$set': {'added_at': datetime.now()}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add admin {user_id}: {e}")
            return False

    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        try:
            admin = await self.admins.find_one({'_id': user_id})
            return bool(admin)
        except Exception as e:
            logger.error(f"Failed to check admin status for {user_id}: {e}")
            return False

    # Channel Management
    async def add_channel(self, channel_id: int, title: str = "") -> bool:
        """Add force-sub channel."""
        try:
            await self.channels.update_one(
                {'_id': channel_id},
                {
                    '$set': {
                        'title': title,
                        'mode': 'off',
                        'added_at': datetime.now()
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add channel {channel_id}: {e}")
            return False

    async def get_channel_mode(self, channel_id: int) -> str:
        """Get channel force-sub mode."""
        try:
            channel = await self.channels.find_one({'_id': channel_id})
            return channel.get('mode', 'off') if channel else 'off'
        except Exception as e:
            logger.error(f"Failed to get channel mode for {channel_id}: {e}")
            return 'off'

    # Settings Management
    async def set_delete_timer(self, seconds: int) -> bool:
        """Set auto-delete timer."""
        try:
            await self.settings.update_one(
                {'key': 'delete_timer'},
                {'$set': {'value': seconds}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set delete timer: {e}")
            return False

    async def get_delete_timer(self) -> int:
        """Get auto-delete timer value."""
        try:
            setting = await self.settings.find_one({'key': 'delete_timer'})
            return setting.get('value', 600) if setting else 600  # Default 10 minutes
        except Exception as e:
            logger.error(f"Failed to get delete timer: {e}")
            return 600

    # Join Request Management
    async def add_join_request(self, channel_id: int, user_id: int) -> bool:
        """Add user to join request list."""
        try:
            await self.join_requests.update_one(
                {'_id': channel_id},
                {'$addToSet': {'pending_users': user_id}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add join request: {e}")
            return False

    async def remove_join_request(self, channel_id: int, user_id: int) -> bool:
        """Remove user from join request list."""
        try:
            await self.join_requests.update_one(
                {'_id': channel_id},
                {'$pull': {'pending_users': user_id}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to remove join request: {e}")
            return False

    async def cleanup_old_data(self, days: int = 30):
        """Cleanup old data (optional maintenance)."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            # Example: Remove old join requests
            # Implement based on your needs
            pass
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Global database instance
db = DatabaseManager(DB_URI, DB_NAME)
