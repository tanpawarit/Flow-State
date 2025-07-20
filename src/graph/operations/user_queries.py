"""
User-focused graph query operations for retrieving tasks and todos.

Example usage:
    from src.graph.operations.user_queries import get_user_tasks, get_user_by_username

    # Find user by username
    user = get_user_by_username("john_doe")
    if user:
        # Get all tasks for the user
        tasks = get_user_tasks(user["user_id"])

        # Get task summary
        summary = get_user_task_summary(user["user_id"])

        # Get overdue tasks for user
        overdue = get_overdue_tasks(user["user_id"])
"""

import logging
from typing import Any, Dict, List, Optional

from src.integrations.neo4j.client import Neo4jClient

logger = logging.getLogger(__name__)


def get_user_tasks(
    user_id: str, list_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Get all tasks assigned to a specific user.

    Args:
        user_id: The ClickUp user ID
        list_ids: Optional list of specific list IDs to filter by

    Returns:
        List of task dictionaries with task details

    Example:
        tasks = get_user_tasks("12345")
        for task in tasks:
            print(f"Task: {task['task_name']} - Status: {task['status']}")
    """
    client = Neo4jClient()

    # Default to the main project lists if none specified
    if list_ids is None:
        list_ids = ["901602625750", "901606939084"]  # Get Shit Done, PADTAI

    query = """
    MATCH (u:User {id: $user_id})-[:ASSIGNED_TO]->(t:Task)
    WHERE t.list_id IN $list_ids
    RETURN t.id as task_id,
           t.name as task_name,
           t.status as status,
           t.priority as priority,
           t.list_id as list_id,
           t.due_date as due_date,
           t.description as description,
           t.url as url
    ORDER BY CASE 
        WHEN t.due_date IS NOT NULL THEN t.due_date 
        ELSE '9999-12-31T23:59:59Z' 
    END ASC, t.priority DESC
    """

    try:
        result = client.execute_read(query, {"user_id": user_id, "list_ids": list_ids})
        return result
    except Exception as e:
        logger.error(f"Failed to get user tasks for user {user_id}: {e}")
        return []


def get_user_task_summary(user_id: str) -> Dict[str, Any]:
    """
    Get a summary of tasks for a user including counts by status and priority.

    Args:
        user_id: The ClickUp user ID

    Returns:
        Dictionary with task summary statistics

    Example:
        summary = get_user_task_summary("12345")
        print(f"Total tasks: {summary['total_tasks']}")
        print(f"Statuses: {summary['statuses']}")
    """
    client = Neo4jClient()

    query = """
    MATCH (u:User {id: $user_id})-[:ASSIGNED_TO]->(t:Task)
    WHERE t.list_id IN ['901602625750', '901606939084']
    WITH t
    RETURN 
        count(t) as total_tasks,
        collect(DISTINCT t.status) as statuses,
        collect(DISTINCT t.priority) as priorities
    """

    try:
        result = client.execute_read(query, {"user_id": user_id})
        if result:
            return result[0]
        return {
            "total_tasks": 0,
            "statuses": [],
            "priorities": [],
        }
    except Exception as e:
        logger.error(f"Failed to get user task summary for user {user_id}: {e}")
        return {
            "total_tasks": 0,
            "statuses": [],
            "priorities": [],
        }


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Get user information by username.

    Args:
        username: The username to search for

    Returns:
        User dictionary or None if not found

    Example:
        user = get_user_by_username("john_doe")
        if user:
            print(f"Found user: {user['username']} (ID: {user['user_id']})")
    """
    client = Neo4jClient()

    query = """
    MATCH (u:User)
    WHERE toLower(u.username) = toLower($username)
    RETURN u.id as user_id,
           u.username as username,
           u.email as email,
           u.initials as initials
    LIMIT 1
    """

    try:
        result = client.execute_read(query, {"username": username})
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Failed to get user by username {username}: {e}")
        return None


def get_overdue_tasks(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all overdue tasks, optionally filtered by user.

    Args:
        user_id: Optional user ID to filter by

    Returns:
        List of overdue task dictionaries

    Example:
        # Get all overdue tasks
        overdue = get_overdue_tasks()

        # Get overdue tasks for specific user
        user_overdue = get_overdue_tasks("12345")
        for task in user_overdue:
            print(f"Overdue: {task['task_name']} - Due: {task['due_date']}")
    """
    client = Neo4jClient()

    base_query = """
    MATCH (t:Task)
    WHERE t.due_date IS NOT NULL 
      AND datetime(t.due_date) < datetime()
      AND NOT t.status IN ['complete', 'closed']
    """

    if user_id:
        query = (
            base_query
            + """
        AND EXISTS((t)<-[:ASSIGNED_TO]-(:User {id: $user_id}))
        """
        )
    else:
        query = base_query

    query += """
    OPTIONAL MATCH (u:User)-[:ASSIGNED_TO]->(t)
    RETURN t.id as task_id,
           t.name as task_name,
           t.status as status,
           t.priority as priority,
           t.due_date as due_date,
           t.list_id as list_id,
           collect(u.username) as assigned_users
    ORDER BY datetime(t.due_date) ASC
    """

    try:
        params = {"user_id": user_id} if user_id else {}
        result = client.execute_read(query, params)
        return result
    except Exception as e:
        logger.error(f"Failed to get overdue tasks: {e}")
        return []
