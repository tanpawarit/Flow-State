"""
ClickUp webhook processor for handling ClickUp-specific webhook events.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.graph.neo4j_client import Neo4jClient
from src.integrations.clickup_client import ClickUpClient
from src.webhooks.providers.clickup.handlers import ClickUpEventHandler
from src.webhooks.providers.clickup.models import ClickUpWebhookEvent
from src.webhooks.shared.base_models import (
    BaseWebhookEvent,
    BaseWebhookProvider,
    ProcessingStatus,
    WebhookProcessingResult,
)
from src.webhooks.shared.exceptions import WebhookProcessingError
from src.webhooks.shared.security import WebhookSignatureValidator

logger = logging.getLogger(__name__)


class ClickUpWebhookProcessor(BaseWebhookProvider):
    """
    ClickUp webhook processor implementing BaseWebhookProvider interface.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.neo4j_client = Neo4jClient()
        self.clickup_client = ClickUpClient()
        self.event_handler = ClickUpEventHandler(self.neo4j_client, self.clickup_client)

        # Processing statistics
        self.events_processed = 0
        self.events_failed = 0
        self.last_processed: Optional[datetime] = None

    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return "clickup"

    def parse_webhook_event(self, raw_payload: Dict[str, Any]) -> BaseWebhookEvent:
        """Parse ClickUp webhook payload into normalized event."""
        try:
            return ClickUpWebhookEvent(**raw_payload)
        except Exception as e:
            raise WebhookProcessingError(
                f"Failed to parse ClickUp webhook event: {e}", provider="clickup"
            )

    def validate_signature(self, payload: bytes, headers: Dict[str, str]) -> bool:
        """Validate ClickUp webhook signature."""
        webhook_secret = self.get_webhook_secret()

        if not webhook_secret:
            logger.warning(
                "No ClickUp webhook secret configured - skipping signature verification"
            )
            return True

        return WebhookSignatureValidator.validate_clickup_signature(
            payload=payload, headers=headers, secret=webhook_secret
        )

    async def process_event(self, event: BaseWebhookEvent) -> WebhookProcessingResult:
        """Process ClickUp webhook event and update the graph database."""
        start_time = datetime.now()

        if not isinstance(event, ClickUpWebhookEvent):
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return WebhookProcessingResult(
                status=ProcessingStatus.FAILED,
                message="Invalid event type for ClickUp processor",
                error_details=f"Expected ClickUpWebhookEvent, got {type(event).__name__}",
                processing_time_ms=processing_time,
            )

        try:
            # Update processing timestamp
            self.last_processed = start_time

            # Process the event based on its type
            entities_updated = await self.event_handler.handle_event(event)

            # Update success statistics
            self.events_processed += 1
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.info(
                f"Successfully processed ClickUp {event.event} event for task {event.task_id}"
            )

            return WebhookProcessingResult(
                status=ProcessingStatus.SUCCESS,
                message=f"Successfully processed {event.event} event",
                error_details=None,
                entities_updated=entities_updated,
                processing_time_ms=processing_time,
                metadata={
                    "event_type": event.event,
                    "task_id": event.task_id,
                    "webhook_id": event.webhook_id,
                },
            )

        except Exception as e:
            # Update failure statistics
            self.events_failed += 1
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.error(f"Failed to process ClickUp {event.event} event: {e}")

            return WebhookProcessingResult(
                status=ProcessingStatus.FAILED,
                message=f"Failed to process {event.event} event",
                error_details=str(e),
                processing_time_ms=processing_time,
                metadata={
                    "event_type": event.event,
                    "task_id": event.task_id,
                    "webhook_id": event.webhook_id,
                    "error_type": type(e).__name__,
                },
            )

    def get_supported_events(self) -> List[str]:
        """Get list of ClickUp event types supported by this processor."""
        return [
            "taskCreated",
            "taskUpdated",
            "taskDeleted",
            "taskStatusUpdated",
            "taskAssigneeUpdated",
            "taskDueDateUpdated",
            "taskPriorityUpdated",
            "taskMoved",
            "taskCommentPosted",
            "subtaskCreated",
            "subtaskUpdated",
            "subtaskDeleted",
        ]

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics for monitoring."""
        return {
            "provider": self.provider_name,
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "last_processed": self.last_processed.isoformat()
            if self.last_processed
            else None,
            "success_rate": (
                self.events_processed / (self.events_processed + self.events_failed)
                if (self.events_processed + self.events_failed) > 0
                else 0
            ),
            "supported_events": self.get_supported_events(),
            "enabled": self.is_enabled(),
        }
