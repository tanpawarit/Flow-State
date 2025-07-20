"""
ClickUp REST API Client
Comprehensive client for interacting with ClickUp's REST API
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import aiohttp
from pydantic import BaseModel, Field

from src.utils.config import get_clickup_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic Models
class ClickUpUser(BaseModel):
    """ClickUp user model"""

    id: str
    username: str
    email: str
    color: str = ""
    initials: str = ""
    profile_picture: Optional[str] = None


class ClickUpStatus(BaseModel):
    """ClickUp status model"""

    id: str
    status: str
    color: str
    orderindex: int
    type: str


class ClickUpTask(BaseModel):
    """ClickUp task model"""

    id: str
    name: str
    text_content: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Union[str, Dict[str, Any]]] = ""
    orderindex: Union[int, float, str] = 0
    date_created: Optional[str] = None
    date_updated: Optional[str] = None
    date_closed: Optional[str] = None
    date_done: Optional[str] = None
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    priority: Optional[Union[str, Dict[str, Any]]] = None
    assignees: List[Dict[str, Any]] = Field(default_factory=list)
    parent: Optional[str] = None
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[Dict[str, Any]] = Field(default_factory=list)
    custom_fields: List[Dict[str, Any]] = Field(default_factory=list)
    list_id: str = ""
    folder_id: str = ""
    space_id: str = ""
    url: str = ""
    team_id: Optional[str] = None
    creator: Optional[Dict[str, Any]] = None
    watchers: List[Dict[str, Any]] = Field(default_factory=list)
    time_estimate: Optional[int] = None
    time_spent: Optional[int] = None


class ClickUpList(BaseModel):
    """ClickUp list model"""

    id: str
    name: str
    task_count: int = 0
    orderindex: Union[int, float, str] = 0
    content: Optional[str] = ""
    status: Optional[str] = ""
    priority: Optional[str] = ""
    assignee: Optional[str] = ""
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    folder_id: str = ""
    space_id: str = ""


class ClickUpFolder(BaseModel):
    """ClickUp folder model"""

    id: str
    name: str
    orderindex: Union[int, float, str] = 0
    override_statuses: bool = False
    hidden: bool = False
    space_id: str = ""
    task_count: int = 0


class ClickUpSpace(BaseModel):
    """ClickUp space model"""

    id: str
    name: str
    private: bool = False
    status_boards: List[Dict[str, Any]] = Field(default_factory=list)
    features: Dict[str, Any] = Field(default_factory=dict)
    archived: bool = False
    multiple_assignees: bool = True
    permissions: Dict[str, Any] = Field(default_factory=dict)


class ClickUpTeam(BaseModel):
    """ClickUp team model"""

    id: str
    name: str
    color: str = ""
    avatar: Optional[str] = None
    members: List[Dict[str, Any]] = Field(default_factory=list)


class ClickUpComment(BaseModel):
    """ClickUp comment model"""

    id: str
    comment_text: str
    comment_text_array: List[Dict[str, Any]] = Field(default_factory=list)
    user: ClickUpUser
    resolved: bool = False
    assignee: Optional[ClickUpUser] = None
    date: str = ""


class ClickUpAPIError(Exception):
    """Custom exception for ClickUp API errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ClickUpRateLimiter:
    """Rate limiter for API requests"""

    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    async def wait_if_needed(self):
        """Wait if rate limit exceeded"""
        now = time.time()
        self.requests = [
            req_time for req_time in self.requests if now - req_time < self.time_window
        ]

        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.1f} seconds")
                await asyncio.sleep(sleep_time)

        self.requests.append(now)


class ClickUpClient:
    """Main ClickUp REST API Client"""

    BASE_URL = "https://api.clickup.com/api/v2"

    def __init__(self, api_key: Optional[str] = None, rate_limit: bool = True):
        self.api_key = api_key
        if not self.api_key:
            # Try to get from config if not provided
            config = get_clickup_config()
            self.api_key = config.get("api_key")

        if not self.api_key:
            raise ValueError(
                "API key must be provided or set in clickup.api_key in config.yaml"
            )

        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = ClickUpRateLimiter() if rate_limit else None
        self._session_lock = asyncio.Lock()

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _ensure_session(self):
        """Ensure we have an active session"""
        async with self._session_lock:
            if self.session is None or self.session.closed:
                headers = {
                    "Authorization": self.api_key,
                    "Content-Type": "application/json",
                }
                self.session = aiohttp.ClientSession(
                    headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                )

    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to ClickUp API"""
        await self._ensure_session()

        if self.rate_limiter:
            await self.rate_limiter.wait_if_needed()

        # Ensure endpoint starts with / to prevent urljoin issues
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        url = f"{self.BASE_URL}{endpoint}"

        if not self.session:
            raise RuntimeError("Client not initialized")

        async with self.session.request(
            method, url, params=params, json=json_data
        ) as response:
            response_data = await response.json()

            if response.status >= 400:
                error_msg = response_data.get("err", f"HTTP {response.status}")
                raise ClickUpAPIError(
                    error_msg, status_code=response.status, response=response_data
                )

            return response_data

    # Team Operations
    async def get_teams(self) -> List[ClickUpTeam]:
        """Get all teams"""
        data = await self._make_request("GET", "/team")
        return [ClickUpTeam(**team) for team in data.get("teams", [])]

    # Space Operations
    async def get_spaces(
        self, team_id: str, archived: bool = False
    ) -> List[ClickUpSpace]:
        """Get spaces for a team"""
        params = {"archived": str(archived).lower()}
        data = await self._make_request("GET", f"/team/{team_id}/space", params=params)
        return [ClickUpSpace(**space) for space in data.get("spaces", [])]

    # Folder Operations
    async def get_folders(
        self, space_id: str, archived: bool = False
    ) -> List[ClickUpFolder]:
        """Get folders for a space"""
        params = {"archived": str(archived).lower()}
        data = await self._make_request(
            "GET", f"/space/{space_id}/folder", params=params
        )
        return [ClickUpFolder(**folder) for folder in data.get("folders", [])]

    # List Operations
    async def get_lists(
        self, folder_id: str, archived: bool = False
    ) -> List[ClickUpList]:
        """Get lists for a folder"""
        params = {"archived": str(archived).lower()}
        data = await self._make_request(
            "GET", f"/folder/{folder_id}/list", params=params
        )
        return [ClickUpList(**lst) for lst in data.get("lists", [])]

    async def get_space_lists(
        self, space_id: str, archived: bool = False
    ) -> List[ClickUpList]:
        """Get lists for a space (lists without folders)"""
        params = {"archived": str(archived).lower()}
        data = await self._make_request("GET", f"/space/{space_id}/list", params=params)
        return [ClickUpList(**lst) for lst in data.get("lists", [])]

    async def get_list(self, list_id: str) -> ClickUpList:
        """Get a specific list"""
        data = await self._make_request("GET", f"/list/{list_id}")
        return ClickUpList(**data)

    # Task Operations
    async def get_tasks(
        self,
        list_id: str,
        include_closed: bool = False,
        assignees: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[ClickUpTask]:
        """Get tasks for a list"""
        params: Dict[str, Union[str, List[str]]] = {
            "archived": "false",
            "page": "0",
            "subtasks": "true",
            "include_closed": str(include_closed).lower(),
        }

        if assignees:
            params["assignees[]"] = assignees
        if statuses:
            params["statuses[]"] = statuses
        if tags:
            params["tags[]"] = tags
        if limit:
            params["limit"] = str(limit)

        data = await self._make_request("GET", f"/list/{list_id}/task", params=params)
        return [ClickUpTask(**task) for task in data.get("tasks", [])]

    async def get_task(self, task_id: str) -> ClickUpTask:
        """Get a specific task"""
        data = await self._make_request("GET", f"/task/{task_id}")
        return ClickUpTask(**data)

    async def create_task(
        self,
        list_id: str,
        name: str,
        description: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        due_date: Optional[int] = None,
        start_date: Optional[int] = None,
        parent: Optional[str] = None,
        custom_fields: Optional[List[Dict]] = None,
    ) -> ClickUpTask:
        """Create a new task"""
        task_data: Dict[str, Any] = {"name": name}

        if description:
            task_data["description"] = description
        if assignees:
            task_data["assignees"] = assignees
        if tags:
            task_data["tags"] = tags
        if status:
            task_data["status"] = status
        if priority is not None:
            task_data["priority"] = priority
        if due_date is not None:
            task_data["due_date"] = due_date
        if start_date is not None:
            task_data["start_date"] = start_date
        if parent:
            task_data["parent"] = parent
        if custom_fields:
            task_data["custom_fields"] = custom_fields

        data = await self._make_request(
            "POST", f"/list/{list_id}/task", json_data=task_data
        )
        return ClickUpTask(**data)

    async def update_task(self, task_id: str, **kwargs) -> ClickUpTask:
        """Update a task"""
        data = await self._make_request("PUT", f"/task/{task_id}", json_data=kwargs)
        return ClickUpTask(**data)

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        await self._make_request("DELETE", f"/task/{task_id}")
        return True

    # Comments
    async def get_task_comments(self, task_id: str) -> List[ClickUpComment]:
        """Get comments for a task"""
        data = await self._make_request("GET", f"/task/{task_id}/comment")
        return [ClickUpComment(**comment) for comment in data.get("comments", [])]

    async def create_task_comment(
        self, task_id: str, comment_text: str
    ) -> ClickUpComment:
        """Create a comment on a task"""
        data = await self._make_request(
            "POST", f"/task/{task_id}/comment", json_data={"comment_text": comment_text}
        )
        return ClickUpComment(**data)

    # Utility Methods
    async def get_hierarchy(self, team_id: str) -> Dict[str, Any]:
        """Get complete team hierarchy"""
        team_data = {
            "team": await self.get_teams(),
            "spaces": await self.get_spaces(team_id),
            "folders": {},
            "lists": {},
            "tasks": {},
        }

        for space in team_data["spaces"]:
            space_id = space.id
            team_data["folders"][space_id] = await self.get_folders(space_id)

            for folder in team_data["folders"][space_id]:
                folder_id = folder.id
                team_data["lists"][folder_id] = await self.get_lists(folder_id)

                for lst in team_data["lists"][folder_id]:
                    list_id = lst.id
                    team_data["tasks"][list_id] = await self.get_tasks(list_id)

        return team_data

    async def search_tasks(
        self,
        query: str,
        team_id: Optional[str] = None,
        space_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ClickUpTask]:
        """Search for tasks"""
        params = {"query": query, "limit": str(limit)}

        if team_id:
            endpoint = f"/team/{team_id}/task"
        elif space_id:
            endpoint = f"/space/{space_id}/task"
        else:
            endpoint = "/task"

        data = await self._make_request("GET", endpoint, params=params)
        return [ClickUpTask(**task) for task in data.get("tasks", [])]


class AsyncClickUpClient:
    """High-level async client with convenience methods"""

    async def get_teams(self) -> List[ClickUpTeam]:
        """Return teams accessible with API key."""
        return await self.client.get_teams()

    async def get_spaces(
        self, team_id: str, archived: bool = False
    ) -> List[ClickUpSpace]:
        """Get spaces for a team.

        Args:
            team_id: ID of the team
            archived: Whether to include archived spaces

        Returns:
            List of ClickUpSpace objects
        """
        return await self.client.get_spaces(team_id, archived=archived)

    async def get_lists(
        self, folder_id: str, archived: bool = False
    ) -> List[ClickUpList]:
        """Get lists in a folder.

        Args:
            folder_id: ID of the folder
            archived: Whether to include archived lists

        Returns:
            List of ClickUpList objects
        """
        return await self.client.get_lists(folder_id, archived=archived)

    async def get_space_lists(
        self, space_id: str, archived: bool = False
    ) -> List[ClickUpList]:
        """Get lists directly from a space.

        Args:
            space_id: ID of the space
            archived: Whether to include archived lists

        Returns:
            List of ClickUpList objects
        """
        return await self.client.get_space_lists(space_id, archived=archived)

    async def get_folders(
        self, space_id: str, archived: bool = False
    ) -> List[ClickUpFolder]:
        """Get folders in a space.

        Args:
            space_id: ID of the space
            archived: Whether to include archived folders

        Returns:
            List of ClickUpFolder objects
        """
        return await self.client.get_folders(space_id, archived=archived)

    """High-level async client with convenience methods"""

    def __init__(self, api_key: Optional[str] = None):
        self.client = ClickUpClient(api_key)

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def get_all_tasks_by_status(
        self, list_id: str, status: str
    ) -> List[ClickUpTask]:
        """Get all tasks with specific status"""
        all_tasks = await self.client.get_tasks(list_id, include_closed=True)
        return [
            task
            for task in all_tasks
            if task.status
            and (
                task.status.get("status", "").lower() == status.lower()
                if isinstance(task.status, dict)
                else str(task.status).lower() == status.lower()
            )
        ]

    async def get_overdue_tasks(self, list_id: str) -> List[ClickUpTask]:
        """Get all overdue tasks"""
        all_tasks = await self.client.get_tasks(list_id)
        overdue_tasks = []
        now = datetime.now(timezone.utc)

        for task in all_tasks:
            if task.due_date:
                try:
                    # Convert to timestamp in seconds (from milliseconds)
                    try:
                        # First try to convert to int in case it's a string timestamp
                        timestamp_ms = int(task.due_date)
                        due_date = datetime.fromtimestamp(
                            timestamp_ms / 1000, timezone.utc
                        )
                    except (ValueError, TypeError):
                        # If conversion to int fails, try parsing as ISO format string
                        try:
                            due_date_str = str(task.due_date)
                            if due_date_str.endswith("Z"):
                                due_date_str = due_date_str[:-1] + "+00:00"
                            due_date = datetime.fromisoformat(due_date_str)
                            if due_date.tzinfo is None:
                                due_date = due_date.replace(tzinfo=timezone.utc)
                        except Exception:
                            continue

                    if due_date < now:
                        overdue_tasks.append(task)

                except Exception:
                    continue

        return overdue_tasks

    async def get_tasks_by_assignee(
        self, list_id: str, assignee_id: str
    ) -> List[ClickUpTask]:
        """Get tasks assigned to specific user"""
        all_tasks = await self.client.get_tasks(list_id)
        return [
            task
            for task in all_tasks
            if assignee_id in [a.get("id") for a in task.assignees]
        ]

    async def get_tasks_by_tag(self, list_id: str, tag: str) -> List[ClickUpTask]:
        """Get tasks with specific tag"""
        tasks_data = await self.client.get_tasks(list_id, tags=[tag])
        return tasks_data

    async def get_tasks(
        self,
        list_id: str,
        include_closed: bool = False,
        assignees: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[ClickUpTask]:
        """Get tasks from a list.

        Args:
            list_id: ID of the list
            include_closed: Whether to include closed tasks
            assignees: List of assignee IDs to filter by
            statuses: List of statuses to filter by
            tags: List of tags to filter by
            limit: Maximum number of tasks to return

        Returns:
            List of ClickUpTask objects
        """
        tasks_data = await self.client.get_tasks(
            list_id=list_id,
            include_closed=include_closed,
            assignees=assignees,
            statuses=statuses,
            tags=tags,
            limit=limit,
        )
        return tasks_data
