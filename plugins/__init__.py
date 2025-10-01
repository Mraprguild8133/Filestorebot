from aiohttp import web
from .route import routes
import logging

logger = logging.getLogger(__name__)

async def web_server():
    """Initialize and configure the aiohttp web server."""
    server_config = {
        'client_max_size': 50 * 1024 * 1024,  # 50MB
        'access_log': logging.getLogger('aiohttp.access'),
    }
    
    web_app = web.Application(**server_config)
    web_app.add_routes(routes)
    
    # Add startup and cleanup handlers
    async def on_startup(app):
        logger.info("🌐 Web server starting up...")
    
    async def on_cleanup(app):
        logger.info("🧹 Web server cleaning up...")
    
    web_app.on_startup.append(on_startup)
    web_app.on_cleanup.append(on_cleanup)
    
    return web_app
