"""
Webhook provider registry for managing multiple webhook providers.
"""

import logging
from typing import Any, Dict, List, Type

from src.webhooks.shared.base_models import BaseWebhookProvider
from src.webhooks.shared.exceptions import ProviderNotFoundError

logger = logging.getLogger(__name__)


class WebhookProviderRegistry:
    """Registry for managing webhook providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._providers: Dict[str, BaseWebhookProvider] = {}
        self._provider_classes: Dict[str, Type[BaseWebhookProvider]] = {}

    def register_provider_class(
        self, name: str, provider_class: Type[BaseWebhookProvider]
    ) -> None:
        """
        Register a webhook provider class.

        Args:
            name: Provider name (e.g., 'clickup', 'discord')
            provider_class: Provider class implementing BaseWebhookProvider
        """
        self._provider_classes[name] = provider_class
        logger.info(f"Registered webhook provider class: {name}")

    def initialize_provider(self, name: str) -> BaseWebhookProvider:
        """
        Initialize a webhook provider instance.

        Args:
            name: Provider name

        Returns:
            Initialized provider instance

        Raises:
            ProviderNotFoundError: If provider class is not registered
        """
        if name not in self._provider_classes:
            raise ProviderNotFoundError(f"Provider '{name}' is not registered")

        # Get provider-specific configuration
        webhooks_config = self.config.get("webhooks", {})
        providers_config = webhooks_config.get("providers", {})
        provider_config = providers_config.get(name, {})

        if not provider_config:
            # Fallback to legacy configuration for ClickUp
            if name == "clickup":
                clickup_config = self.config.get("clickup", {})
                provider_config = {
                    "enabled": webhooks_config.get("enabled", True),
                    "webhook_secret": clickup_config.get("webhook_secret"),
                }

        provider_class = self._provider_classes[name]
        provider_instance = provider_class(provider_config)

        self._providers[name] = provider_instance
        logger.info(f"Initialized webhook provider: {name}")

        return provider_instance

    def get_provider(self, name: str) -> BaseWebhookProvider:
        """
        Get a provider instance, initializing it if necessary.

        Args:
            name: Provider name

        Returns:
            Provider instance

        Raises:
            ProviderNotFoundError: If provider is not registered
        """
        if name not in self._providers:
            return self.initialize_provider(name)

        return self._providers[name]

    def get_enabled_providers(self) -> Dict[str, BaseWebhookProvider]:
        """Get all enabled providers."""
        enabled_providers = {}

        for name, provider_class in self._provider_classes.items():
            try:
                provider = self.get_provider(name)
                if provider.is_enabled():
                    enabled_providers[name] = provider
            except Exception as e:
                logger.warning(f"Failed to initialize provider '{name}': {e}")

        return enabled_providers

    def list_registered_providers(self) -> List[str]:
        """Get list of all registered provider names."""
        return list(self._provider_classes.keys())

    def list_enabled_provider_names(self) -> List[str]:
        """Get list of enabled provider names."""
        return list(self.get_enabled_providers().keys())

    def auto_discover_providers(self) -> None:
        """
        Auto-discover and register available webhook providers.

        This method dynamically imports provider modules and registers them.
        """
        try:
            # Import ClickUp provider
            from src.webhooks.providers.clickup import ClickUpWebhookProcessor

            self.register_provider_class("clickup", ClickUpWebhookProcessor)
        except ImportError as e:
            logger.warning(f"Failed to import ClickUp provider: {e}")

        # TODO: Add other providers as they are implemented
        # try:
        #     from src.webhooks.providers.discord import DiscordWebhookProcessor
        #     self.register_provider_class("discord", DiscordWebhookProcessor)
        # except ImportError as e:
        #     logger.warning(f"Failed to import Discord provider: {e}")

        logger.info(f"Auto-discovered {len(self._provider_classes)} webhook providers")

    def get_provider_stats(self) -> Dict[str, Dict]:
        """Get statistics for all enabled providers."""
        stats = {}

        for name, provider in self.get_enabled_providers().items():
            try:
                if hasattr(provider, "get_processing_stats"):
                    stats[name] = provider.get_processing_stats()
                else:
                    stats[name] = {
                        "provider": name,
                        "enabled": provider.is_enabled(),
                        "supported_events": provider.get_supported_events(),
                    }
            except Exception as e:
                stats[name] = {
                    "provider": name,
                    "error": str(e),
                }

        return stats
