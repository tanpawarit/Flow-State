"""
ClickUp-specific event handlers for processing webhook events and updating the graph database.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.graph.neo4j_client import Neo4jClient
from src.integrations.clickup_client import ClickUpClient
from src.webhooks.providers.clickup.models import ClickUpWebhookEvent

logger = logging.getLogger(__name__)


class ClickUpEventHandler:
    """
    Handles ClickUp webhook events and updates the Neo4j graph database.
    """

    def __init__(self, neo4j_client: Neo4jClient, clickup_client: ClickUpClient):
        self.neo4j_client = neo4j_client
        self.clickup_client = clickup_client

    async def handle_event(self, event: ClickUpWebhookEvent) -> List[str]:
        """
        Main event handler that routes ClickUp webhook events to appropriate processors.

        Args:
            event: ClickUp webhook event to process

        Returns:
            List of entity IDs that were updated in the graph
        """
        logger.info(f"Processing ClickUp {event.event} event for task {event.task_id}")

        # Route event to appropriate handler
        handler_map = {
            "taskCreated": self._handle_task_created,
            "taskUpdated": self._handle_task_updated,
            "taskDeleted": self._handle_task_deleted,
            "taskStatusUpdated": self._handle_task_status_updated,
            "taskAssigneeUpdated": self._handle_task_assignee_updated,
            "taskDueDateUpdated": self._handle_task_due_date_updated,
            "taskPriorityUpdated": self._handle_task_priority_updated,
            "taskMoved": self._handle_task_moved,
            "taskCommentPosted": self._handle_task_comment_posted,
            "subtaskCreated": self._handle_subtask_created,
            "subtaskUpdated": self._handle_subtask_updated,
            "subtaskDeleted": self._handle_subtask_deleted,
        }

        handler = handler_map.get(event.event)
        if handler:
            return await handler(event)
        else:
            logger.warning(f"No handler found for ClickUp event type: {event.event}")
            return []

    async def _handle_task_created(self, event: ClickUpWebhookEvent) -> List[str]:
        """Handle task creation event."""
        # Fetch full task details from ClickUp API
        async with self.clickup_client as client:
            task = await client.get_task(event.task_id)

        # Create task node in graph
        await self._create_or_update_task_node(task)

        # Create relationships (assignees, status, priority, list)
        await self._create_task_relationships(task)

        return [event.task_id]

    async def _handle_task_updated(self, event: ClickUpWebhookEvent) -> List[str]:
        """Handle task update event."""
        # Fetch updated task details
        async with self.clickup_client as client:
            task = await client.get_task(event.task_id)

        # Update task node
        await self._create_or_update_task_node(task)

        # Update relationships
        await self._update_task_relationships(task, event)

        return [event.task_id]

    async def _handle_task_deleted(self, event: ClickUpWebhookEvent) -> List[str]:
        """Handle task deletion event."""
        query = """
        MATCH (t:Task {id: $task_id})
        DETACH DELETE t
        """

        self.neo4j_client.execute_write(query, {"task_id": event.task_id})
        logger.info(f"Deleted task {event.task_id} from graph")

        return [event.task_id]

    async def _handle_task_status_updated(
        self, event: ClickUpWebhookEvent
    ) -> List[str]:
        """Handle task status change event."""
        # Get new status from history items
        new_status = self._extract_new_value_from_history(event, "status")

        if new_status:
            query = """
            MATCH (t:Task {id: $task_id})
            SET t.status = $status,
                t.updated_at = datetime()
            
            // Update status relationship
            OPTIONAL MATCH (t)-[r:HAS_STATUS]->(:Status)
            DELETE r
            
            WITH t
            MATCH (s:Status {status: $status})
            MERGE (t)-[:HAS_STATUS]->(s)
            """

            self.neo4j_client.execute_write(
                query, {"task_id": event.task_id, "status": new_status}
            )

        return [event.task_id]

    async def _handle_task_assignee_updated(
        self, event: ClickUpWebhookEvent
    ) -> List[str]:
        """Handle task assignee change event."""
        # Fetch updated task to get current assignees
        async with self.clickup_client as client:
            task = await client.get_task(event.task_id)

        # Remove old assignee relationships
        query_remove = """
        MATCH (t:Task {id: $task_id})-[r:ASSIGNED_TO]->(u:User)
        DELETE r
        """
        self.neo4j_client.execute_write(query_remove, {"task_id": event.task_id})

        # Add new assignee relationships
        updated_entities = [event.task_id]
        for assignee in task.assignees:
            await self._create_assignee_relationship(event.task_id, assignee)
            updated_entities.append(assignee.get("id", ""))

        return updated_entities

    async def _handle_task_due_date_updated(
        self, event: ClickUpWebhookEvent
    ) -> List[str]:
        """Handle task due date change event."""
        new_due_date = self._extract_new_value_from_history(event, "due_date")

        query = """
        MATCH (t:Task {id: $task_id})
        SET t.due_date = $due_date,
            t.updated_at = datetime()
        """

        # Convert timestamp to datetime if present
        due_date_param = None
        if new_due_date:
            try:
                due_date_param = datetime.fromtimestamp(int(new_due_date) / 1000)
            except (ValueError, TypeError):
                logger.warning(f"Invalid due date format: {new_due_date}")

        self.neo4j_client.execute_write(
            query, {"task_id": event.task_id, "due_date": due_date_param}
        )

        return [event.task_id]

    async def _handle_task_priority_updated(
        self, event: ClickUpWebhookEvent
    ) -> List[str]:
        """Handle task priority change event."""
        new_priority = self._extract_new_value_from_history(event, "priority")

        if new_priority:
            query = """
            MATCH (t:Task {id: $task_id})
            SET t.priority = $priority,
                t.updated_at = datetime()
            
            // Update priority relationship
            OPTIONAL MATCH (t)-[r:HAS_PRIORITY]->(:Priority)
            DELETE r
            
            WITH t
            MATCH (p:Priority {priority: $priority})
            MERGE (t)-[:HAS_PRIORITY]->(p)
            """

            self.neo4j_client.execute_write(
                query, {"task_id": event.task_id, "priority": new_priority}
            )

        return [event.task_id]

    async def _handle_task_moved(self, event: ClickUpWebhookEvent) -> List[str]:
        """Handle task move between lists event."""
        new_list_id = self._extract_new_value_from_history(event, "list_id")

        if new_list_id:
            query = """
            MATCH (t:Task {id: $task_id})
            
            // Remove old list relationship
            OPTIONAL MATCH (t)-[r:BELONGS_TO]->(:List)
            DELETE r
            
            // Create new list relationship
            WITH t
            MATCH (l:List {id: $list_id})
            MERGE (t)-[:BELONGS_TO]->(l)
            
            SET t.updated_at = datetime()
            """

            self.neo4j_client.execute_write(
                query, {"task_id": event.task_id, "list_id": new_list_id}
            )

            return [event.task_id, new_list_id]

        return [event.task_id]

    async def _handle_task_comment_posted(
        self, event: ClickUpWebhookEvent
    ) -> List[str]:
        """Handle new comment on task event."""
        # For now, just log the comment event
        # Could be extended to store comments in graph if needed
        logger.info(f"Comment posted on task {event.task_id}")
        return []

    async def _handle_subtask_created(self, event: ClickUpWebhookEvent) -> List[str]:
        """Handle subtask creation event."""
        # Fetch full subtask details
        async with self.clickup_client as client:
            subtask = await client.get_task(event.task_id)

        # Create subtask node
        await self._create_or_update_task_node(subtask)

        # Create parent relationship if parent exists
        if subtask.parent:
            query = """
            MATCH (subtask:Task {id: $subtask_id})
            MATCH (parent:Task {id: $parent_id})
            MERGE (subtask)-[:SUBTASK_OF]->(parent)
            """

            self.neo4j_client.execute_write(
                query, {"subtask_id": event.task_id, "parent_id": subtask.parent}
            )

            return [event.task_id, subtask.parent]

        return [event.task_id]

    async def _handle_subtask_updated(self, event: ClickUpWebhookEvent) -> List[str]:
        """Handle subtask update event."""
        return await self._handle_task_updated(
            event
        )  # Same logic as regular task update

    async def _handle_subtask_deleted(self, event: ClickUpWebhookEvent) -> List[str]:
        """Handle subtask deletion event."""
        return await self._handle_task_deleted(
            event
        )  # Same logic as regular task deletion

    async def _create_or_update_task_node(self, task: Any) -> None:
        """Create or update a task node in the graph."""
        query = """
        MERGE (t:Task {id: $id})
        SET t.name = $name,
            t.description = $description,
            t.status = $status,
            t.priority = $priority,
            t.points = $points,
            t.due_date = $due_date,
            t.start_date = $start_date,
            t.updated_at = datetime(),
            t.url = $url,
            t.custom_id = $custom_id,
            t.time_estimate = $time_estimate,
            t.archived = $archived
        """

        # Parse dates
        due_date = None
        start_date = None

        if task.due_date:
            try:
                due_date = datetime.fromtimestamp(int(task.due_date) / 1000)
            except (ValueError, TypeError):
                pass

        if task.start_date:
            try:
                start_date = datetime.fromtimestamp(int(task.start_date) / 1000)
            except (ValueError, TypeError):
                pass

        # Extract status and priority strings
        status = task.status
        priority = task.priority

        if isinstance(status, dict):
            status = status.get("status", "")
        if isinstance(priority, dict):
            priority = priority.get("priority", "")

        parameters = {
            "id": task.id,
            "name": task.name,
            "description": task.description or "",
            "status": status or "",
            "priority": priority or "",
            "points": getattr(task, "points", 0),
            "due_date": due_date,
            "start_date": start_date,
            "url": task.url,
            "custom_id": getattr(task, "custom_id", ""),
            "time_estimate": getattr(task, "time_estimate", 0),
            "archived": getattr(task, "archived", False),
        }

        self.neo4j_client.execute_write(query, parameters)

    async def _create_task_relationships(self, task: Any) -> None:
        """Create all relationships for a task."""
        # Create assignee relationships
        for assignee in task.assignees:
            await self._create_assignee_relationship(task.id, assignee)

        # Create list relationship
        if task.list_id:
            query = """
            MATCH (t:Task {id: $task_id})
            MATCH (l:List {id: $list_id})
            MERGE (t)-[:BELONGS_TO]->(l)
            """
            self.neo4j_client.execute_write(
                query, {"task_id": task.id, "list_id": task.list_id}
            )

        # Create status relationship
        if task.status:
            status = task.status
            if isinstance(status, dict):
                status = status.get("status", "")

            if status:
                query = """
                MATCH (t:Task {id: $task_id})
                MATCH (s:Status {status: $status})
                MERGE (t)-[:HAS_STATUS]->(s)
                """
                self.neo4j_client.execute_write(
                    query, {"task_id": task.id, "status": status}
                )

        # Create priority relationship
        if task.priority:
            priority = task.priority
            if isinstance(priority, dict):
                priority = priority.get("priority", "")

            if priority:
                query = """
                MATCH (t:Task {id: $task_id})
                MATCH (p:Priority {priority: $priority})
                MERGE (t)-[:HAS_PRIORITY]->(p)
                """
                self.neo4j_client.execute_write(
                    query, {"task_id": task.id, "priority": priority}
                )

    async def _update_task_relationships(
        self, task: Any, event: ClickUpWebhookEvent
    ) -> None:
        """Update task relationships based on what changed."""
        # For now, recreate all relationships
        # Could be optimized to only update changed relationships
        await self._create_task_relationships(task)

    async def _create_assignee_relationship(
        self, task_id: str, assignee: Dict[str, Any]
    ) -> None:
        """Create assignee relationship."""
        # First ensure user exists
        query_user = """
        MERGE (u:User {id: $user_id})
        SET u.username = $username,
            u.email = $email,
            u.color = $color,
            u.initials = $initials
        """

        self.neo4j_client.execute_write(
            query_user,
            {
                "user_id": assignee.get("id", ""),
                "username": assignee.get("username", ""),
                "email": assignee.get("email", ""),
                "color": assignee.get("color", ""),
                "initials": assignee.get("initials", ""),
            },
        )

        # Create assignment relationship
        query_assign = """
        MATCH (u:User {id: $user_id})
        MATCH (t:Task {id: $task_id})
        MERGE (u)-[:ASSIGNED_TO {assigned_at: datetime()}]->(t)
        """

        self.neo4j_client.execute_write(
            query_assign, {"user_id": assignee.get("id", ""), "task_id": task_id}
        )

    def _extract_new_value_from_history(
        self, event: ClickUpWebhookEvent, field: str
    ) -> Optional[str]:
        """Extract new value for a field from webhook history items."""
        for item in event.history_items:
            if item.get("field") == field:
                return item.get("after", {}).get("value")
        return None
