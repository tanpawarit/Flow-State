#!/usr/bin/env python3
"""
Script to create ClickUp webhook using their API.
Based on: https://developer.clickup.com/reference/createwebhook
"""

import asyncio
import json
import logging
from typing import List, Optional

import aiohttp

from src.utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ClickUpWebhookSetup:
    """Setup ClickUp webhooks via API."""

    def __init__(self, config: dict):
        self.config = config
        self.api_key = config.get("clickup", {}).get("api_key")
        self.team_id = config.get("clickup", {}).get("team_id")
        self.webhook_url = None
        
        # Get webhook URL from config or ngrok
        webhooks_config = config.get("webhooks", {})
        if webhooks_config.get("ngrok", {}).get("enabled"):
            # Will be set dynamically when ngrok is running
            self.webhook_url = None
        else:
            self.webhook_url = webhooks_config.get("public_url")

    async def get_current_webhooks(self) -> List[dict]:
        """Get existing webhooks for the team."""
        if not self.api_key or not self.team_id:
            logger.error("Missing ClickUp API key or team ID in config")
            return []

        url = f"https://api.clickup.com/api/v2/team/{self.team_id}/webhook"
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        webhooks = data.get("webhooks", [])
                        logger.info(f"Found {len(webhooks)} existing webhooks")
                        return webhooks
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get webhooks: {response.status} - {error_text}")
                        return []
        except Exception as e:
            logger.error(f"Error getting webhooks: {e}")
            return []

    async def create_webhook(self, webhook_url: str, events: Optional[List[str]] = None) -> bool:
        """Create a new ClickUp webhook."""
        if not self.api_key or not self.team_id:
            logger.error("Missing ClickUp API key or team ID in config")
            return False

        # Default events to subscribe to (using ClickUp's exact event names)
        if events is None:
            events = [
                "taskCreated",
                "taskUpdated", 
                "taskDeleted",
                "taskStatusUpdated",
                "taskAssigneeUpdated",
                "taskDueDateUpdated",
                "taskPriorityUpdated",
                "taskMoved"
            ]

        url = f"https://api.clickup.com/api/v2/team/{self.team_id}/webhook"
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "endpoint": f"{webhook_url}/webhooks/clickup",
            "events": events
        }

        logger.info(f"Creating webhook with endpoint: {payload['endpoint']}")
        logger.info(f"Events: {', '.join(events)}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        webhook = data.get("webhook", {})
                        logger.info("✅ Webhook created successfully!")
                        logger.info(f"   Webhook ID: {webhook.get('id')}")
                        logger.info(f"   Endpoint: {webhook.get('endpoint')}")
                        logger.info(f"   Events: {len(webhook.get('events', []))} events")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to create webhook: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"❌ Error creating webhook: {e}")
            return False

    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a ClickUp webhook."""
        if not self.api_key:
            logger.error("Missing ClickUp API key in config")
            return False

        url = f"https://api.clickup.com/api/v2/webhook/{webhook_id}"
        headers = {
            "Authorization": self.api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"✅ Webhook {webhook_id} deleted successfully")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to delete webhook: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"❌ Error deleting webhook: {e}")
            return False

    def get_ngrok_url(self) -> Optional[str]:
        """Try to get ngrok URL from the running tunnel."""
        try:
            import requests
            response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get("tunnels", [])
                for tunnel in tunnels:
                    if tunnel.get("proto") == "https":
                        return tunnel.get("public_url")
        except Exception as e:
            logger.debug(f"Could not get ngrok URL: {e}")
        return None

    async def setup_webhook_interactive(self):
        """Interactive webhook setup."""
        logger.info("=== ClickUp Webhook Setup ===")
        
        # Check existing webhooks
        existing_webhooks = await self.get_current_webhooks()
        
        if existing_webhooks:
            logger.info("\n📋 Existing webhooks:")
            for webhook in existing_webhooks:
                logger.info(f"   ID: {webhook.get('id')}")
                logger.info(f"   Endpoint: {webhook.get('endpoint')}")
                logger.info(f"   Events: {len(webhook.get('events', []))}")
                logger.info("")

        # Determine webhook URL
        webhook_url = self.get_ngrok_url()
        if not webhook_url:
            webhook_url = self.webhook_url

        if not webhook_url:
            logger.error("❌ No webhook URL available. Make sure ngrok is running or set public_url in config")
            return

        logger.info(f"🌐 Using webhook URL: {webhook_url}")
        
        # Create webhook
        success = await self.create_webhook(webhook_url)
        
        if success:
            logger.info("\n🎉 Webhook setup complete!")
            logger.info(f"✅ ClickUp will send events to: {webhook_url}/webhooks/clickup")
            logger.info("✅ You can now test by updating tasks in ClickUp")
        else:
            logger.error("❌ Webhook setup failed")


async def main():
    """Main setup function."""
    try:
        # Load configuration
        config = Config.get()
        
        # Initialize webhook setup
        webhook_setup = ClickUpWebhookSetup(config)
        
        # Run interactive setup
        await webhook_setup.setup_webhook_interactive()
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())