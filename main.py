"""
Flow-State: GraphRAG Discord Bot with ClickUp Integration

Main entry point that starts both the Discord bot and webhook server.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from src.utils.config import Config
from src.webhooks.core.webhook_server import WebhookServer
from src.bot.discord_bot import DiscordBot

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FlowStateApp:
    """Main application class that manages both Discord bot and webhook server."""

    def __init__(self):
        self.config = Config.get()
        self.webhook_server: Optional[WebhookServer] = None
        self.discord_bot: Optional[DiscordBot] = None
        self.running = False

    async def start(self):
        """Start the application with both webhook server and Discord bot."""
        logger.info("Starting Flow-State GraphRAG Discord Bot...")

        try:
            self.running = True

            # Initialize components
            tasks = []

            # Start webhook server if enabled
            webhooks_config = self.config.get("webhooks", {})
            if webhooks_config.get("enabled", True):
                self.webhook_server = WebhookServer(self.config)
                webhook_host = webhooks_config.get("host", "0.0.0.0")
                webhook_port = webhooks_config.get("port", 8000)

                logger.info(f"Starting webhook server on {webhook_host}:{webhook_port}")
                tasks.append(
                    asyncio.create_task(
                        self.webhook_server.start_server(webhook_host, webhook_port),
                        name="webhook_server",
                    )
                )
            else:
                logger.info("Webhook server disabled in configuration")

            # Start Discord bot if token is configured
            discord_config = self.config.get("discord", {})
            discord_token = discord_config.get("token")
            if discord_token and discord_token != "your_discord_bot_token_here":
                logger.info("Starting Discord bot...")
                self.discord_bot = DiscordBot()
                tasks.append(
                    asyncio.create_task(
                        self.discord_bot.start(discord_token), name="discord_bot"
                    )
                )
            else:
                logger.warning("Discord bot token not configured, skipping Discord bot")

            if not tasks:
                logger.error(
                    "No services configured to start. Please check your config.yaml"
                )
                return

            # Wait for all tasks to complete (or fail)
            logger.info("All services started successfully")
            await asyncio.gather(*tasks, return_exceptions=True)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Gracefully shutdown all services."""
        logger.info("Shutting down Flow-State application...")

        self.running = False

        # Close webhook server
        if self.webhook_server:
            logger.info("Stopping webhook server...")
            # WebhookServer shutdown is handled by uvicorn

        # Close Discord bot
        if self.discord_bot:
            logger.info("Stopping Discord bot...")
            await self.discord_bot.close()

        logger.info("Application shutdown complete")

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main entry point."""
    try:
        app = FlowStateApp()
        app.setup_signal_handlers()

        # Run the async application
        asyncio.run(app.start())

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
