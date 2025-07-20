"""
Multi-provider webhook server using FastAPI.
"""

import logging
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI

from src.webhooks.core.registry import WebhookProviderRegistry
from src.webhooks.core.router import WebhookRouter

logger = logging.getLogger(__name__)


class WebhookServer:
    """
    Multi-provider FastAPI-based webhook server.

    Supports multiple webhook providers (ClickUp, Discord, GitHub, etc.)
    with dynamic routing and provider management.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # Initialize FastAPI app
        self.app = FastAPI(
            title="Flow-State Multi-Provider Webhook Server",
            description="Receives and processes webhook events from multiple providers for graph updates",
            version="2.0.0",
        )

        # Initialize provider registry
        self.provider_registry = WebhookProviderRegistry(config)

        # Auto-discover and register providers
        self.provider_registry.auto_discover_providers()

        # Initialize router
        self.webhook_router = WebhookRouter(self.provider_registry)

        # Setup routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""

        # Include webhook router
        self.app.include_router(self.webhook_router.get_router(), tags=["webhooks"])

        @self.app.get("/")
        async def root():
            """Root endpoint with server information."""
            enabled_providers = self.provider_registry.list_enabled_provider_names()

            return {
                "service": "Flow-State Multi-Provider Webhook Server",
                "version": "2.0.0",
                "enabled_providers": enabled_providers,
                "endpoints": {
                    "health": "/health",
                    "providers": "/providers",
                    "stats": "/stats",
                    "webhooks": "/webhooks/{provider_name}",
                },
            }

    async def start_server(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """
        Start the webhook server.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        enabled_providers = self.provider_registry.list_enabled_provider_names()

        logger.info(f"Starting multi-provider webhook server on {host}:{port}")
        logger.info(f"Enabled providers: {', '.join(enabled_providers) or 'None'}")

        if not enabled_providers:
            logger.warning(
                "No webhook providers are enabled! Server will start but won't process webhooks."
            )

        # Log available endpoints
        for provider in enabled_providers:
            logger.info(f"Webhook endpoint: POST /webhooks/{provider}")

        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
        )

        server = uvicorn.Server(config)
        await server.serve()

    def get_app(self) -> FastAPI:
        """Get the FastAPI app instance for testing or manual serving."""
        return self.app

    def get_provider_registry(self) -> WebhookProviderRegistry:
        """Get the provider registry instance."""
        return self.provider_registry

    def add_custom_provider(self, name: str, provider_class) -> None:
        """
        Add a custom webhook provider.

        Args:
            name: Provider name
            provider_class: Provider class implementing BaseWebhookProvider
        """
        self.provider_registry.register_provider_class(name, provider_class)
        logger.info(f"Added custom webhook provider: {name}")
