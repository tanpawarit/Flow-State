"""
Separate ngrok server to expose webhook endpoints.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import Config
from src.utils.ngrok_manager import NgrokManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NgrokServer:
    """Standalone ngrok server for webhook tunneling."""

    def __init__(self):
        self.config = Config.get()
        self.ngrok_manager: Optional[NgrokManager] = None
        self.running = False

    async def start(self):
        """Start the ngrok tunnel server."""
        logger.info("Starting Flow-State Ngrok Tunnel Server...")

        try:
            self.running = True

            # Get webhook configuration
            webhooks_config = self.config.get("webhooks", {})
            
            if not webhooks_config.get("enabled", True):
                logger.error("Webhooks are disabled in configuration")
                return

            # Get ngrok configuration
            ngrok_config = webhooks_config.get("ngrok", {})
            if not ngrok_config.get("enabled", False):
                logger.error("Ngrok is disabled in configuration")
                return

            # Initialize ngrok manager
            self.ngrok_manager = NgrokManager(webhooks_config)
            
            # Get webhook port
            webhook_port = webhooks_config.get("port", 8000)
            
            # Start tunnel
            public_url = await self.ngrok_manager.start_tunnel(webhook_port)
            
            if public_url:
                logger.info("=" * 60)
                logger.info("🎉 NGROK TUNNEL READY!")
                logger.info("=" * 60)
                logger.info(f"🌐 Public URL: {public_url}")
                logger.info(f"🔗 ClickUp Webhook: {public_url}/webhooks/clickup")
                logger.info(f"📊 Ngrok Dashboard: http://localhost:4040")
                logger.info(f"🎯 Local Port: {webhook_port}")
                logger.info("=" * 60)
                logger.info("ℹ️  Configure ClickUp webhook with the URL above")
                logger.info("ℹ️  Keep this process running to maintain the tunnel")
                logger.info("ℹ️  Press Ctrl+C to stop the tunnel")
                logger.info("=" * 60)
                
                # Keep running
                try:
                    while self.running:
                        await asyncio.sleep(1)
                        
                        # Check if tunnel is still active
                        if not self.ngrok_manager.is_active():
                            logger.warning("Ngrok tunnel lost connection, attempting to reconnect...")
                            public_url = await self.ngrok_manager.start_tunnel(webhook_port)
                            if public_url:
                                logger.info(f"🔄 Tunnel reconnected: {public_url}")
                            else:
                                logger.error("Failed to reconnect tunnel")
                                break
                        
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal, shutting down...")
            else:
                logger.error("Failed to establish ngrok tunnel")

        except Exception as e:
            logger.error(f"Ngrok server error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Gracefully shutdown the ngrok tunnel."""
        logger.info("Shutting down ngrok tunnel...")
        
        self.running = False
        
        if self.ngrok_manager:
            await self.ngrok_manager.stop_tunnel()
            
        logger.info("Ngrok server shutdown complete")

    def get_tunnel_info(self):
        """Get current tunnel information."""
        if self.ngrok_manager:
            return self.ngrok_manager.get_tunnel_info()
        return {"status": "not_initialized"}


def main():
    """Main entry point for standalone ngrok server."""
    try:
        server = NgrokServer()
        
        # Setup signal handlers
        import signal
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(server.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run the server
        asyncio.run(server.start())
        
    except KeyboardInterrupt:
        logger.info("Ngrok server interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()