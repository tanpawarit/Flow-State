"""Discord bot implementation."""

import discord
from discord.ext import commands

from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DiscordBot(commands.Bot):
    """Main Discord bot class."""

    def __init__(self):
        """Initialize the Discord bot."""
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="/",
            intents=intents,
            description="Flow-State GraphRAG Discord Bot",
        )

    async def setup_hook(self) -> None:
        """Called when the bot is starting up."""
        logger.info("Bot is starting up...")
        # Add cog loading here when cogs are implemented

    async def on_ready(self) -> None:
        """Called when the bot has finished connecting."""
        logger.info(f"Bot is ready! Logged in as {self.user}")

    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Called when an error occurs."""
        logger.error(f"Error in event {event}: {args}, {kwargs}")

    def run_bot(self) -> None:
        """Run the Discord bot."""
        config = Config.get()
        token = config.get("discord", {}).get("token")

        if not token:
            raise ValueError("Discord token not found in configuration")

        self.run(token)
