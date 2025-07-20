"""
Multi-Provider Webhooks Module

This module handles incoming webhooks from multiple providers (ClickUp, Discord, etc.)
to keep the Neo4j graph database in sync with real-time changes.

The module is organized into:
- providers/: Provider-specific implementations (clickup, discord, etc.)
- shared/: Common utilities and base classes
- core/: Main server and routing logic
"""

# Import main components
from src.webhooks.core.webhook_server import WebhookServer
from src.webhooks.core.registry import WebhookProviderRegistry
from src.webhooks.shared.base_models import BaseWebhookEvent, BaseWebhookProvider

# Import ClickUp provider for backward compatibility
from src.webhooks.providers.clickup.models import ClickUpWebhookEvent
from src.webhooks.providers.clickup.processor import ClickUpWebhookProcessor

__all__ = [
    # Core components
    "WebhookServer",
    "WebhookProviderRegistry",
    "BaseWebhookEvent",
    "BaseWebhookProvider",
    # ClickUp provider (backward compatibility)
    "ClickUpWebhookEvent",
    "ClickUpWebhookProcessor",
]
