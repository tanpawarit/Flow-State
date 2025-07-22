"""
Ngrok tunnel manager for exposing webhook server to the internet.
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from pyngrok import ngrok, conf
from pyngrok.exception import PyngrokNgrokError

logger = logging.getLogger(__name__)


class NgrokManager:
    """
    Manages ngrok tunnel for webhook server with configuration support.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("ngrok", {})
        self.tunnel: Optional[ngrok.NgrokTunnel] = None
        self.public_url: Optional[str] = None
        self.enabled = self.config.get("enabled", False)

    async def start_tunnel(self, port: int) -> Optional[str]:
        """
        Start ngrok tunnel for the specified port.
        
        Args:
            port: Local port to tunnel
            
        Returns:
            Public URL if successful, None if disabled or failed
        """
        if not self.enabled:
            logger.info("Ngrok tunnel disabled in configuration")
            return None

        try:
            # Configure ngrok
            authtoken = self.config.get("authtoken")
            if authtoken:
                conf.get_default().auth_token = authtoken
                logger.info("Ngrok authtoken configured")

            # Set region if specified
            region = self.config.get("region", "us")
            conf.get_default().region = region

            # Configure logging
            log_level = self.config.get("log_level", "info")
            conf.get_default().log_level = log_level

            # Disable ngrok monitor if specified
            if not self.config.get("inspect", True):
                conf.get_default().monitor_thread = False

            # Start tunnel
            logger.info(f"Starting ngrok tunnel for port {port}")
            
            # Run ngrok.connect in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            self.tunnel = await loop.run_in_executor(
                None, 
                lambda: ngrok.connect(port, "http")
            )
            
            self.public_url = self.tunnel.public_url
            
            logger.info(f"✅ Ngrok tunnel established: {self.public_url}")
            logger.info(f"🌐 Webhook endpoint: {self.public_url}/webhooks/clickup")
            
            if self.config.get("inspect", True):
                logger.info("🔍 Ngrok web interface: http://localhost:4040")
            
            return self.public_url

        except PyngrokNgrokError as e:
            logger.error(f"❌ Failed to start ngrok tunnel: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error starting ngrok: {e}")
            return None

    async def stop_tunnel(self):
        """Stop the ngrok tunnel."""
        if self.tunnel:
            try:
                logger.info("Stopping ngrok tunnel...")
                
                # Run ngrok.disconnect in a thread
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, 
                    lambda: ngrok.disconnect(self.tunnel.public_url)
                )
                
                self.tunnel = None
                self.public_url = None
                logger.info("✅ Ngrok tunnel stopped")
                
            except Exception as e:
                logger.error(f"❌ Error stopping ngrok tunnel: {e}")

    def get_public_url(self) -> Optional[str]:
        """Get the current public URL."""
        return self.public_url

    def get_webhook_url(self, provider: str = "clickup") -> Optional[str]:
        """
        Get the full webhook URL for a provider.
        
        Args:
            provider: Webhook provider name (default: clickup)
            
        Returns:
            Full webhook URL or None if tunnel not active
        """
        if self.public_url:
            return f"{self.public_url}/webhooks/{provider}"
        return None

    def is_active(self) -> bool:
        """Check if tunnel is active."""
        return self.tunnel is not None and self.public_url is not None

    def get_tunnel_info(self) -> Dict[str, Any]:
        """Get tunnel information for logging/monitoring."""
        if not self.is_active():
            return {
                "status": "inactive",
                "enabled": self.enabled
            }
            
        return {
            "status": "active",
            "enabled": self.enabled,
            "public_url": self.public_url,
            "webhook_url": self.get_webhook_url(),
            "inspect_url": "http://localhost:4040" if self.config.get("inspect", True) else None,
            "region": self.config.get("region", "us"),
            "tunnel_name": self.tunnel.name if self.tunnel else None
        }

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_tunnel()