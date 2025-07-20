"""
ClickUp webhook event models.

Based on ClickUp webhook documentation:
https://clickup.com/api/clickupreference/operation/Webhooks/
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.webhooks.shared.base_models import BaseWebhookEvent, WebhookEventType


class ClickUpUser(BaseModel):
    """ClickUp user representation in webhook events."""

    id: str
    username: str
    email: Optional[str] = None
    color: Optional[str] = None
    profilePicture: Optional[str] = None
    initials: Optional[str] = None


class ClickUpStatus(BaseModel):
    """ClickUp status representation."""

    id: str
    status: str
    color: str
    type: str
    orderindex: int


class ClickUpPriority(BaseModel):
    """ClickUp priority representation."""

    id: str
    priority: str
    color: str
    orderindex: int


class ClickUpList(BaseModel):
    """ClickUp list representation."""

    id: str
    name: str
    color: Optional[str] = None
    avatar: Optional[str] = None


class ClickUpSpace(BaseModel):
    """ClickUp space representation."""

    id: str
    name: str
    color: Optional[str] = None
    private: bool = False
    avatar: Optional[str] = None


class ClickUpTask(BaseModel):
    """ClickUp task representation in webhook events."""

    id: str
    name: str
    text_content: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ClickUpStatus] = None
    priority: Optional[ClickUpPriority] = None
    assignees: List[ClickUpUser] = Field(default_factory=list)
    watchers: List[ClickUpUser] = Field(default_factory=list)
    creator: Optional[ClickUpUser] = None
    list: Optional[ClickUpList] = None
    space: Optional[ClickUpSpace] = None
    list_id: Optional[str] = None  # List ID for relationships
    points: Optional[int] = None
    time_estimate: Optional[int] = None
    time_spent: Optional[int] = None
    custom_id: Optional[str] = None
    due_date: Optional[str] = None  # ClickUp sends as string timestamp
    start_date: Optional[str] = None  # ClickUp sends as string timestamp
    date_created: Optional[str] = None
    date_updated: Optional[str] = None
    date_closed: Optional[str] = None
    archived: bool = False
    parent: Optional[str] = None  # Parent task ID for subtasks
    url: Optional[str] = None


class ClickUpWebhookEvent(BaseWebhookEvent):
    """
    ClickUp webhook event model extending BaseWebhookEvent.

    Handles all types of ClickUp webhook events:
    - taskCreated, taskUpdated, taskDeleted
    - taskStatusUpdated, taskAssigneeUpdated
    - taskDueDateUpdated, taskPriorityUpdated
    - taskMoved, subtaskCreated, etc.
    """

    # ClickUp-specific fields
    event: str = Field(
        ..., description="ClickUp event type (e.g., 'taskCreated', 'taskUpdated')"
    )
    task_id: str = Field(..., description="ClickUp task ID")
    webhook_id: str = Field(..., description="ClickUp webhook ID")
    history_items: List[Dict[str, Any]] = Field(
        default_factory=list, description="Change history items"
    )
    task: Optional[ClickUpTask] = Field(None, description="Task details if available")

    # Additional context fields that might be present
    before: Optional[Dict[str, Any]] = Field(
        None, description="Before state for updates"
    )
    after: Optional[Dict[str, Any]] = Field(None, description="After state for updates")

    def __init__(self, **data):
        # Set provider and normalize event type
        data["provider"] = "clickup"
        data["event_id"] = (
            f"clickup_{data.get('webhook_id', '')}_{data.get('task_id', '')}"
        )
        data["event_type"] = self._normalize_clickup_event_type(data.get("event", ""))

        # Store original ClickUp event data
        data["raw_data"] = {
            "event": data.get("event"),
            "task_id": data.get("task_id"),
            "webhook_id": data.get("webhook_id"),
            "history_items": data.get("history_items", []),
        }

        super().__init__(**data)

    @staticmethod
    def _normalize_clickup_event_type(clickup_event: str) -> WebhookEventType:
        """Normalize ClickUp event types to common webhook event types."""
        event_mapping = {
            "taskCreated": WebhookEventType.TASK_CREATED,
            "taskUpdated": WebhookEventType.TASK_UPDATED,
            "taskDeleted": WebhookEventType.TASK_DELETED,
            "taskStatusUpdated": WebhookEventType.TASK_STATUS_CHANGED,
            "taskAssigneeUpdated": WebhookEventType.TASK_ASSIGNED,
            "taskDueDateUpdated": WebhookEventType.TASK_UPDATED,
            "taskPriorityUpdated": WebhookEventType.TASK_UPDATED,
            "taskMoved": WebhookEventType.TASK_UPDATED,
            "taskCommentPosted": WebhookEventType.COMMENT_CREATED,
            "subtaskCreated": WebhookEventType.TASK_CREATED,
            "subtaskUpdated": WebhookEventType.TASK_UPDATED,
            "subtaskDeleted": WebhookEventType.TASK_DELETED,
        }

        return event_mapping.get(clickup_event, WebhookEventType.OTHER)

    def get_affected_entity_id(self) -> Optional[str]:
        """Get the task ID that was affected by this event."""
        return self.task_id

    def get_affected_entity_type(self) -> str:
        """Get the type of entity affected (always 'task' for ClickUp)."""
        return "task"

    def is_subtask_event(self) -> bool:
        """Check if this is a subtask-related event."""
        return self.event.startswith("subtask")

    def get_change_details(self) -> Dict[str, Any]:
        """Extract change details from history items."""
        changes = {}

        for item in self.history_items:
            field = item.get("field")
            if field:
                changes[field] = {
                    "before": item.get("before", {}).get("value"),
                    "after": item.get("after", {}).get("value"),
                }

        return changes


class WebhookVerification(BaseModel):
    """Model for ClickUp webhook verification."""

    webhook_id: str
    secret: str
    signature: str
    timestamp: str
    body: str
