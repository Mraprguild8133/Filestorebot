import motor.motor_asyncio
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from config import DATABASE_URL, DB_NAME, get_logger, OWNER_ID

logger = get_logger(__name__)

class DatabaseManager:
    """Motor-based database manager for admin management."""
    
    def __init__(self, db_uri: str, db_name: str):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                db_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            self.db = self.client[db_name]
            self._setup_collections()
            logger.info("✅ MongoDB connection established with Motor")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise

    def _setup_collections(self):
        """Initialize collections."""
        self.admins = self.db['admins']
        self.settings = self.db['settings']

    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False

    # ==================== ADMIN MANAGEMENT ====================
    async def add_admin(self, user_id: int, username: str = "") -> bool:
        """Add admin user."""
        try:
            # Don't add if already exists
            if await self.is_admin(user_id):
                return True
                
            await self.admins.update_one(
                {'_id': user_id},
                {
                    '$set': {
                        'username': username,
                        'added_at': datetime.now(),
                        'added_by': 'system'
                    }
                },
                upsert=True
            )
            logger.info(f"✅ Admin added: {user_id} ({username})")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add admin {user_id}: {e}")
            return False

    async def remove_admin(self, user_id: int) -> bool:
        """Remove admin user (cannot remove owner)."""
        try:
            if user_id == OWNER_ID:
                logger.warning(f"⚠️ Cannot remove owner: {user_id}")
                return False
                
            result = await self.admins.delete_one({'_id': user_id})
            success = result.deleted_count > 0
            
            if success:
                logger.info(f"✅ Admin removed: {user_id}")
            else:
                logger.warning(f"⚠️ Admin not found: {user_id}")
                
            return success
        except Exception as e:
            logger.error(f"❌ Failed to remove admin {user_id}: {e}")
            return False

    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        try:
            # Owner is always admin
            if user_id == OWNER_ID:
                return True
                
            admin = await self.admins.find_one({'_id': user_id})
            return bool(admin)
        except Exception as e:
            logger.error(f"❌ Failed to check admin status for {user_id}: {e}")
            return False

    async def get_all_admins(self) -> List[Dict[str, Any]]:
        """Get all admins with details."""
        try:
            admins = []
            
            # Add owner first
            admins.append({
                '_id': OWNER_ID,
                'username': 'owner',
                'added_at': datetime.now(),
                'is_owner': True
            })
            
            # Add other admins
            async for admin in self.admins.find():
                admin['is_owner'] = False
                admins.append(admin)
                
            return admins
        except Exception as e:
            logger.error(f"❌ Failed to get admins: {e}")
            return []

    async def get_admin_ids(self) -> List[int]:
        """Get all admin IDs."""
        try:
            admin_ids = [OWNER_ID]  # Owner is always admin
            
            async for admin in self.admins.find():
                admin_ids.append(admin['_id'])
                
            return admin_ids
        except Exception as e:
            logger.error(f"❌ Failed to get admin IDs: {e}")
            return [OWNER_ID]

    async def get_admin_count(self) -> int:
        """Get total admin count."""
        try:
            count = await self.admins.count_documents({})
            return count + 1  # +1 for owner
        except Exception as e:
            logger.error(f"❌ Failed to get admin count: {e}")
            return 1

    # ==================== SETTINGS MANAGEMENT ====================
    async def set_setting(self, key: str, value: Any) -> bool:
        """Store bot settings."""
        try:
            await self.settings.update_one(
                {'key': key},
                {'$set': {'value': value, 'updated_at': datetime.now()}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to set setting {key}: {e}")
            return False

    async def get_setting(self, key: str, default: Any = None) -> Any:
        """Get bot setting."""
        try:
            setting = await self.settings.find_one({'key': key})
            return setting.get('value', default) if setting else default
        except Exception as e:
            logger.error(f"❌ Failed to get setting {key}: {e}")
            return default

    async def set_auto_delete_time(self, seconds: int) -> bool:
        """Set auto-delete timer."""
        return await self.set_setting('auto_delete_time', seconds)

    async def get_auto_delete_time(self) -> int:
        """Get auto-delete timer."""
        return await self.get_setting('auto_delete_time', 600)  # Default 10 minutes

    # ==================== STATISTICS ====================
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            return {
                'total_admins': await self.get_admin_count(),
                'auto_delete_time': await self.get_auto_delete_time(),
                'database': self.db.name,
                'collections': await self.db.list_collection_names()
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {}

    # ==================== INITIALIZATION ====================
    async def initialize_defaults(self):
        """Initialize default settings and add owner as admin."""
        try:
            # Add owner as admin if not exists
            await self.add_admin(OWNER_ID, "owner")
            
            # Set default auto-delete time
            current_time = await self.get_auto_delete_time()
            if not current_time:
                await self.set_auto_delete_time(600)  # 10 minutes
                
            logger.info("✅ Database defaults initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize defaults: {e}")

# Global database instance
db = DatabaseManager(DATABASE_URL, DB_NAME)
