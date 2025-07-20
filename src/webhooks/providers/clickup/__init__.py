"""
ClickUp Webhook Provider

Handles webhook events from ClickUp for real-time synchronization with the graph database.
"""

from src.webhooks.providers.clickup.models import ClickUpWebhookEvent
from src.webhooks.providers.clickup.processor import ClickUpWebhookProcessor

# Register ClickUp provider
from src.webhooks.providers import register_provider

register_provider("clickup", ClickUpWebhookProcessor)

__all__ = ["ClickUpWebhookEvent", "ClickUpWebhookProcessor"]
