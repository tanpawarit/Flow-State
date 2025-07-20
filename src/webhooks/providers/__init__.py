"""
Webhook Providers Module

This module contains webhook implementations for different platforms and services.
Each provider is organized in its own subdirectory with specific handlers and models.
"""

from typing import Dict, Type

from src.webhooks.shared.base_models import BaseWebhookProvider

# Provider registry - automatically populated when providers are imported
_PROVIDERS: Dict[str, Type[BaseWebhookProvider]] = {}


def register_provider(name: str, provider_class: Type[BaseWebhookProvider]) -> None:
    """Register a webhook provider."""
    _PROVIDERS[name] = provider_class


def get_provider(name: str) -> Type[BaseWebhookProvider]:
    """Get a registered webhook provider by name."""
    if name not in _PROVIDERS:
        raise ValueError(f"Unknown webhook provider: {name}")
    return _PROVIDERS[name]


def get_all_providers() -> Dict[str, Type[BaseWebhookProvider]]:
    """Get all registered webhook providers."""
    return _PROVIDERS.copy()


def list_provider_names() -> list[str]:
    """Get list of all registered provider names."""
    return list(_PROVIDERS.keys())
