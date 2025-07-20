"""
Base models and abstract classes for webhook providers.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WebhookEventType(str, Enum):
    """Common webhook event types across providers."""

    # Task/Issue events
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_ASSIGNED = "task_assigned"
    TASK_UNASSIGNED = "task_unassigned"

    # Comment events
    COMMENT_CREATED = "comment_created"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"

    # Project/List events
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"

    # User events
    USER_ADDED = "user_added"
    USER_REMOVED = "user_removed"

    # Generic events
    OTHER = "other"


class ProcessingStatus(str, Enum):
    """Status of webhook event processing."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"


class BaseWebhookEvent(BaseModel, ABC):
    """
    Abstract base class for all webhook events.

    Each provider should extend this class with their specific event structure.
    """

    # Common fields across all webhook events
    provider: str = Field(
        ..., description="Name of the webhook provider (e.g., 'clickup', 'discord')"
    )
    event_type: WebhookEventType = Field(..., description="Normalized event type")
    event_id: str = Field(..., description="Unique identifier for this event")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the event occurred"
    )

    # Provider-specific data
    raw_data: Dict[str, Any] = Field(
        default_factory=dict, description="Original webhook payload"
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"
        use_enum_values = True

    @abstractmethod
    def get_affected_entity_id(self) -> Optional[str]:
        """Get the ID of the main entity affected by this event (task, project, etc.)."""
        pass

    @abstractmethod
    def get_affected_entity_type(self) -> str:
        """Get the type of entity affected (task, project, comment, etc.)."""
        pass

    def get_normalized_data(self) -> Dict[str, Any]:
        """Get normalized event data for consistent processing."""
        return {
            "provider": self.provider,
            "event_type": self.event_type,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "entity_id": self.get_affected_entity_id(),
            "entity_type": self.get_affected_entity_type(),
        }


class WebhookProcessingResult(BaseModel):
    """Result of processing a webhook event."""

    status: ProcessingStatus = Field(..., description="Processing status")
    message: str = Field(..., description="Human-readable processing message")
    error_details: Optional[str] = Field(
        None, description="Error details if processing failed"
    )
    entities_updated: List[str] = Field(
        default_factory=list, description="IDs of entities updated in the graph"
    )
    processing_time_ms: Optional[int] = Field(
        None, description="Processing time in milliseconds"
    )

    # Metadata for debugging and monitoring
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class BaseWebhookProvider(ABC):
    """
    Abstract base class for webhook providers.

    Each provider (ClickUp, Discord, GitHub, etc.) should implement this interface.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the provider with configuration."""
        self.config = config
        self.provider_name = self.get_provider_name()

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider (e.g., 'clickup', 'discord')."""
        pass

    @abstractmethod
    def parse_webhook_event(self, raw_payload: Dict[str, Any]) -> BaseWebhookEvent:
        """Parse raw webhook payload into a normalized event object."""
        pass

    @abstractmethod
    def validate_signature(self, payload: bytes, headers: Dict[str, str]) -> bool:
        """Validate webhook signature for security."""
        pass

    @abstractmethod
    async def process_event(self, event: BaseWebhookEvent) -> WebhookProcessingResult:
        """Process a webhook event and update the graph database."""
        pass

    @abstractmethod
    def get_supported_events(self) -> List[str]:
        """Get list of event types supported by this provider."""
        pass

    def is_enabled(self) -> bool:
        """Check if this provider is enabled in configuration."""
        return self.config.get("enabled", True)

    def get_webhook_secret(self) -> Optional[str]:
        """Get webhook secret for signature validation."""
        return self.config.get("webhook_secret")

    def get_endpoint_path(self) -> str:
        """Get the webhook endpoint path for this provider."""
        return f"/webhooks/{self.provider_name}"

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics for this provider.

        Returns:
            Dict containing provider statistics (e.g., events processed, errors, etc.)
        """
        return {
            "provider": self.get_provider_name(),
            "enabled": self.is_enabled(),
            "supported_events": self.get_supported_events(),
        }
