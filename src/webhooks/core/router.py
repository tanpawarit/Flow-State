"""
Dynamic webhook routing for multiple providers.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse

from src.webhooks.core.registry import WebhookProviderRegistry
from src.webhooks.shared.exceptions import (
    ProviderNotFoundError,
    WebhookError,
    WebhookSignatureError,
    WebhookValidationError,
)
from src.webhooks.shared.validators import WebhookEventValidator

logger = logging.getLogger(__name__)


class WebhookRouter:
    """Dynamic webhook router that handles multiple providers."""

    def __init__(self, provider_registry: WebhookProviderRegistry):
        self.provider_registry = provider_registry
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup dynamic routes for all enabled providers."""

        @self.router.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "multi-provider-webhooks"}

        @self.router.get("/providers")
        async def list_providers():
            """List all available webhook providers."""
            enabled_providers = self.provider_registry.list_enabled_provider_names()
            all_providers = self.provider_registry.list_registered_providers()

            return {
                "all_providers": all_providers,
                "enabled_providers": enabled_providers,
                "count": len(enabled_providers),
            }

        @self.router.get("/stats")
        async def webhook_stats():
            """Get webhook processing statistics for all providers."""
            try:
                stats = self.provider_registry.get_provider_stats()
                return {
                    "status": "operational",
                    "providers": stats,
                }
            except Exception as e:
                logger.error(f"Failed to get webhook stats: {e}")
                raise HTTPException(
                    status_code=500, detail="Failed to retrieve statistics"
                )

        @self.router.post("/webhooks/{provider_name}")
        async def handle_webhook(
            provider_name: str,
            request: Request,
            background_tasks: BackgroundTasks,
        ):
            """
            Dynamic webhook endpoint that routes to appropriate provider.

            Args:
                provider_name: Name of the webhook provider (e.g., 'clickup', 'discord')
                request: FastAPI request object
                background_tasks: FastAPI background tasks
            """
            try:
                # Validate payload size
                body = await request.body()
                WebhookEventValidator.validate_payload_size(body, max_size_mb=10)

                # Get the appropriate provider
                try:
                    provider = self.provider_registry.get_provider(provider_name)
                except ProviderNotFoundError:
                    logger.warning(f"Unknown webhook provider: {provider_name}")
                    raise HTTPException(
                        status_code=404,
                        detail=f"Unknown webhook provider: {provider_name}",
                    )

                # Check if provider is enabled
                if not provider.is_enabled():
                    logger.warning(f"Webhook provider '{provider_name}' is disabled")
                    raise HTTPException(
                        status_code=403,
                        detail=f"Webhook provider '{provider_name}' is disabled",
                    )

                # Verify webhook signature
                headers = dict(request.headers)
                if not provider.validate_signature(body, headers):
                    logger.warning(
                        f"Invalid webhook signature for provider: {provider_name}"
                    )
                    raise HTTPException(
                        status_code=401, detail="Invalid webhook signature"
                    )

                # Parse JSON payload
                try:
                    payload_data = await request.json()
                except Exception as e:
                    logger.error(f"Failed to parse JSON payload: {e}")
                    raise HTTPException(status_code=400, detail="Invalid JSON payload")

                # Parse webhook event using provider
                try:
                    webhook_event = provider.parse_webhook_event(payload_data)
                except WebhookValidationError as e:
                    logger.error(f"Webhook validation failed for {provider_name}: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

                # Process event in background
                background_tasks.add_task(
                    self._process_webhook_event_background,
                    provider,
                    webhook_event,
                )

                logger.info(
                    f"Webhook event received from {provider_name}: "
                    f"{webhook_event.event_type} for entity {webhook_event.get_affected_entity_id()}"
                )

                return JSONResponse(
                    {
                        "status": "success",
                        "message": "Webhook received and queued for processing",
                        "provider": provider_name,
                        "event_type": webhook_event.event_type,
                        "event_id": webhook_event.event_id,
                    }
                )

            except HTTPException:
                raise
            except WebhookSignatureError as e:
                logger.warning(f"Webhook signature error: {e}")
                raise HTTPException(status_code=401, detail=str(e))
            except WebhookValidationError as e:
                logger.error(f"Webhook validation error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
            except WebhookError as e:
                logger.error(f"Webhook processing error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error in webhook handler: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

    async def _process_webhook_event_background(
        self,
        provider,
        webhook_event,
    ) -> None:
        """
        Process webhook event in background task.

        Args:
            provider: Webhook provider instance
            webhook_event: Parsed webhook event
        """
        try:
            result = await provider.process_event(webhook_event)

            if result.status.value == "success":
                logger.info(
                    f"Successfully processed {webhook_event.event_type} event "
                    f"from {provider.provider_name}: {result.message}"
                )
            else:
                logger.error(
                    f"Failed to process {webhook_event.event_type} event "
                    f"from {provider.provider_name}: {result.message}"
                )
                if result.error_details:
                    logger.error(f"Error details: {result.error_details}")

        except Exception as e:
            logger.error(
                f"Unexpected error processing {webhook_event.event_type} event "
                f"from {provider.provider_name}: {e}"
            )

    def get_router(self) -> APIRouter:
        """Get the FastAPI router instance."""
        return self.router
