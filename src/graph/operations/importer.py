"""Graph data import operations."""

import sys
from pathlib import Path

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, TransientError
from pydantic import BaseModel

from src.integrations.clickup.client import (
    ClickUpClient,
    ClickUpList,
    ClickUpSpace,
    ClickUpTask,
)

logger = logging.getLogger(__name__)


class SyncStats(BaseModel):
    """Statistics for sync operation"""

    teams_synced: int = 0
    spaces_synced: int = 0
    lists_synced: int = 0
    tasks_synced: int = 0
    users_synced: int = 0
    relationships_created: int = 0
    subtask_relationships_created: int = 0
    errors: List[str] = []
    start_time: datetime = datetime.now()
    end_time: Optional[datetime] = None

    def duration(self) -> float:
        """Get sync duration in seconds"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


class InvesticDataImporter:
    """Import Investic Tech space data to Neo4j"""

    TARGET_LISTS = {"901602625750": "Get Shit Done", "901606939084": "PADTAI"}

    def __init__(
        self,
        clickup_api_key: str,
        neo4j_uri: str,
        neo4j_username: str,
        neo4j_password: str,
    ):
        self.clickup_api_key = clickup_api_key
        self.driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_username, neo4j_password),
            max_connection_lifetime=30 * 60,  # 30 minutes
            max_connection_pool_size=50,
            connection_acquisition_timeout=60,  # 60 seconds
        )
        self.stats = SyncStats()

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()

    def test_connection(self) -> bool:
        """Test Neo4j connection"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                return record is not None and record["test"] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    async def __aenter__(self):
        # Test connection on entry
        if not self.test_connection():
            raise ConnectionError("Failed to connect to Neo4j database")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def escape_cypher_string(self, value: str) -> str:
        """Escape string for Cypher queries"""
        if not value:
            return ""
        return value.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')

    def format_datetime_for_cypher(self, timestamp: Optional[str]) -> Optional[str]:
        """Convert ClickUp timestamp to Neo4j datetime"""
        if not timestamp:
            return None
        try:
            timestamp_ms = int(timestamp)
            dt = datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc)
            return dt.isoformat()
        except Exception:
            return None

    def execute_cypher(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> List[Dict[str, Any]]:
        """Execute Cypher query with retry logic"""
        last_exception = None

        for attempt in range(max_retries):
            try:
                with self.driver.session() as session:
                    result = session.run(query, parameters or {})  # type: ignore[arg-type]
                    return [record.data() for record in result]

            except (ServiceUnavailable, TransientError) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"Connection error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Failed after {max_retries} attempts: {e}")

            except Exception as e:
                error_msg = f"Cypher execution failed: {e}"
                logger.error(error_msg)
                self.stats.errors.append(error_msg)
                raise

        # If we get here, all retries failed
        if last_exception:
            error_msg = (
                f"Cypher execution failed after {max_retries} retries: {last_exception}"
            )
            logger.error(error_msg)
            self.stats.errors.append(error_msg)
            raise last_exception
        else:
            error_msg = f"Cypher execution failed after {max_retries} retries"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)
            raise RuntimeError(error_msg)

    def clear_investic_data(self):
        """Clear existing Investic data from Neo4j using batched approach"""
        logger.info("🧹 Clearing existing Investic data...")

        # Batch size for deletion to avoid memory issues
        batch_size = 1000

        # Clear in specific order to avoid constraint violations
        clear_operations = [
            # 1. Delete task assignments and relationships in batches
            """
            MATCH (u:User)-[r:ASSIGNED_TO]->(t:Task)
            WHERE t.space_id = '90161158278'
            WITH r LIMIT $batch_size
            DELETE r
            RETURN count(r) as deleted
            """,
            # 2. Delete tasks in batches
            """
            MATCH (t:Task)
            WHERE t.space_id = '90161158278'
            WITH t LIMIT $batch_size
            DETACH DELETE t
            RETURN count(t) as deleted
            """,
            # 3. Delete list relationships and lists
            """
            MATCH (l:List)
            WHERE l.space_id = '90161158278'
            WITH l LIMIT $batch_size
            DETACH DELETE l
            RETURN count(l) as deleted
            """,
            # 4. Delete space and team
            """
            MATCH (s:Space {id: '90161158278'})
            OPTIONAL MATCH (t:Team {id: 'investic_team'})
            DETACH DELETE s, t
            RETURN count(s) + count(t) as deleted
            """,
            # 5. Cleanup any orphaned users (optional)
            """
            MATCH (u:User)
            WHERE NOT (u)-[:ASSIGNED_TO]->()
            WITH u LIMIT $batch_size
            DELETE u
            RETURN count(u) as deleted
            """,
        ]

        for i, query in enumerate(clear_operations):
            try:
                total_deleted = 0
                while True:
                    result = self.execute_cypher(query, {"batch_size": batch_size})
                    deleted = result[0]["deleted"] if result else 0
                    total_deleted += deleted

                    if deleted == 0:
                        break

                    # Log progress for large deletions
                    if total_deleted > 0 and total_deleted % 5000 == 0:
                        logger.info(
                            f"   Cleared {total_deleted} items in operation {i + 1}"
                        )

                if total_deleted > 0:
                    logger.info(f"✅ Operation {i + 1}: cleared {total_deleted} items")

            except Exception as e:
                logger.warning(f"Clear operation {i + 1} warning: {e}")
                # Continue with next operation even if one fails

    def create_team_and_space(self, space: ClickUpSpace):
        """Create team and space nodes"""
        logger.info("📋 Creating team and space nodes...")

        query = """
        MERGE (team:Team {id: 'investic_team'})
        SET team.name = 'Investic',
            team.color = '#0066cc',
            team.created_at = datetime()
        
        MERGE (space:Space {id: $space_id})
        SET space.name = $space_name,
            space.private = $space_private,
            space.multiple_assignees = $space_multiple_assignees,
            space.archived = $space_archived,
            space.updated_at = datetime()
        
        MERGE (team)-[:HAS_SPACE]->(space)
        
        RETURN team, space
        """

        params = {
            "space_id": space.id,
            "space_name": space.name,
            "space_private": space.private,
            "space_multiple_assignees": space.multiple_assignees,
            "space_archived": space.archived,
        }

        result = self.execute_cypher(query, params)
        self.stats.teams_synced = 1
        self.stats.spaces_synced = 1

        logger.info(f"✅ Created team and space: {len(result)} nodes")

    def create_lists(self, lists: List[ClickUpList]):
        """Create list nodes for target lists"""
        logger.info("📝 Creating list nodes...")

        for lst in lists:
            if lst.id not in self.TARGET_LISTS:
                continue

            query = """
            MATCH (space:Space {id: $space_id})
            MERGE (list:List {id: $list_id})
            SET list.name = $list_name,
                list.task_count = $task_count,
                list.orderindex = $orderindex,
                list.status = $status,
                list.space_id = $space_id,
                list.updated_at = datetime()
            
            MERGE (space)-[:CONTAINS_LIST]->(list)
            
            RETURN list
            """

            params = {
                "space_id": "90161158278",  # Tech space ID
                "list_id": lst.id,
                "list_name": lst.name,
                "task_count": lst.task_count,
                "orderindex": lst.orderindex or 0,
                "status": lst.status or "active",
            }

            self.execute_cypher(query, params)
            self.stats.lists_synced += 1

        logger.info(f"✅ Created {self.stats.lists_synced} lists")

    def create_users_from_tasks(self, tasks_by_list: Dict[str, List[ClickUpTask]]):
        """Create user nodes from task assignees"""
        logger.info("👥 Creating user nodes...")

        users = {}
        for list_id, tasks in tasks_by_list.items():
            if list_id not in self.TARGET_LISTS:
                continue

            for task in tasks:
                for assignee in task.assignees:
                    user_id = str(assignee.get("id", ""))
                    if user_id and user_id not in users:
                        users[user_id] = assignee

        for user_id, user_data in users.items():
            query = """
            MERGE (user:User {id: $user_id})
            SET user.username = $username,
                user.email = $email,
                user.color = $color,
                user.initials = $initials,
                user.profile_picture = $profile_picture,
                user.updated_at = datetime()
            
            RETURN user
            """

            params = {
                "user_id": user_id,
                "username": user_data.get("username", ""),
                "email": user_data.get("email", ""),
                "color": user_data.get("color", ""),
                "initials": user_data.get("initials", ""),
                "profile_picture": user_data.get("profilePicture", ""),
            }

            self.execute_cypher(query, params)
            self.stats.users_synced += 1

        logger.info(f"✅ Created {self.stats.users_synced} users")

    def create_tasks(self, tasks_by_list: Dict[str, List[ClickUpTask]]):
        """Create task nodes and relationships"""
        logger.info("📋 Creating task nodes...")

        for list_id, tasks in tasks_by_list.items():
            if list_id not in self.TARGET_LISTS:
                continue

            logger.info(
                f"   Processing {len(tasks)} tasks from {self.TARGET_LISTS[list_id]}"
            )

            for task in tasks:
                # Create task node
                query = """
                MATCH (list:List {id: $list_id})
                MERGE (task:Task {id: $task_id})
                SET task.name = $name,
                    task.description = $description,
                    task.text_content = $text_content,
                    task.status = $status,
                    task.priority = $priority,
                    task.due_date = CASE WHEN $due_date IS NOT NULL THEN datetime($due_date) ELSE NULL END,
                    task.start_date = CASE WHEN $start_date IS NOT NULL THEN datetime($start_date) ELSE NULL END,
                    task.date_created = CASE WHEN $date_created IS NOT NULL THEN datetime($date_created) ELSE NULL END,
                    task.date_updated = CASE WHEN $date_updated IS NOT NULL THEN datetime($date_updated) ELSE NULL END,
                    task.date_closed = CASE WHEN $date_closed IS NOT NULL THEN datetime($date_closed) ELSE NULL END,
                    task.orderindex = $orderindex,
                    task.url = $url,
                    task.time_estimate = $time_estimate,
                    task.time_spent = $time_spent,
                    task.archived = false,
                    task.list_id = $list_id,
                    task.space_id = '90161158278',
                    task.updated_at = datetime()
                
                MERGE (list)-[:CONTAINS_TASK]->(task)
                
                RETURN task
                """

                # Extract status and priority
                status_str = ""
                if isinstance(task.status, dict):
                    status_str = task.status.get("status", "")
                elif task.status:
                    status_str = str(task.status)

                priority_str = ""
                if isinstance(task.priority, dict):
                    priority_str = task.priority.get("priority", "")
                elif task.priority:
                    priority_str = str(task.priority)

                params = {
                    "list_id": list_id,
                    "task_id": task.id,
                    "name": task.name,
                    "description": task.description or "",
                    "text_content": task.text_content or "",
                    "status": status_str,
                    "priority": priority_str,
                    "due_date": self.format_datetime_for_cypher(task.due_date),
                    "start_date": self.format_datetime_for_cypher(task.start_date),
                    "date_created": self.format_datetime_for_cypher(task.date_created),
                    "date_updated": self.format_datetime_for_cypher(task.date_updated),
                    "date_closed": self.format_datetime_for_cypher(task.date_closed),
                    "orderindex": task.orderindex or 0,
                    "url": task.url,
                    "time_estimate": task.time_estimate or 0,
                    "time_spent": task.time_spent or 0,
                }

                self.execute_cypher(query, params)
                self.stats.tasks_synced += 1

                # Create user assignments
                for assignee in task.assignees:
                    user_id = str(assignee.get("id", ""))
                    if user_id:
                        assign_query = """
                        MATCH (user:User {id: $user_id})
                        MATCH (task:Task {id: $task_id})
                        MERGE (user)-[r:ASSIGNED_TO]->(task)
                        SET r.assigned_at = datetime()
                        RETURN r
                        """

                        assign_params = {"user_id": user_id, "task_id": task.id}

                        self.execute_cypher(assign_query, assign_params)
                        self.stats.relationships_created += 1

        # Create subtask relationships after all tasks are created
        self.create_subtask_relationships(tasks_by_list)

        logger.info(
            f"✅ Created {self.stats.tasks_synced} tasks with {self.stats.relationships_created} assignments and {self.stats.subtask_relationships_created} subtask relationships"
        )

    def create_subtask_relationships(self, tasks_by_list: Dict[str, List[ClickUpTask]]):
        """Create SUBTASK_OF relationships between parent and child tasks"""
        logger.info("🔗 Creating subtask relationships...")

        for list_id, tasks in tasks_by_list.items():
            if list_id not in self.TARGET_LISTS:
                continue

            logger.info(
                f"   Processing subtask relationships for {self.TARGET_LISTS[list_id]}"
            )

            for task in tasks:
                # Check if this task has a parent (making it a subtask)
                if task.parent:
                    try:
                        query = """
                        MATCH (parent:Task {id: $parent_id})
                        MATCH (subtask:Task {id: $subtask_id})
                        MERGE (subtask)-[r:SUBTASK_OF]->(parent)
                        SET r.created_at = datetime()
                        RETURN r
                        """

                        params = {"parent_id": task.parent, "subtask_id": task.id}

                        result = self.execute_cypher(query, params)
                        if result:  # Relationship was created successfully
                            self.stats.subtask_relationships_created += 1
                            logger.debug(
                                f"Created SUBTASK_OF relationship: {task.name} -> {task.parent}"
                            )

                    except Exception as e:
                        error_msg = f"Failed to create subtask relationship for task {task.id} -> {task.parent}: {e}"
                        logger.warning(error_msg)
                        self.stats.errors.append(error_msg)
                        # Continue processing other relationships even if one fails

        logger.info(
            f"✅ Created {self.stats.subtask_relationships_created} subtask relationships"
        )

    async def sync_investic_data(self, full_sync: bool = True):
        """Main sync function"""
        logger.info("🚀 Starting Investic Tech space sync...")

        async with ClickUpClient(self.clickup_api_key) as client:
            try:
                # Get Investic team and Tech space
                teams = await client.get_teams()
                investic_team = next((t for t in teams if t.name == "Investic"), None)
                if not investic_team:
                    raise ValueError("Investic team not found")

                spaces = await client.get_spaces(investic_team.id)
                tech_space = next((s for s in spaces if s.name == "Tech"), None)
                if not tech_space:
                    raise ValueError("Tech space not found")

                # Get target lists
                try:
                    lists = await client.get_space_lists(tech_space.id)
                except Exception:
                    folders = await client.get_folders(tech_space.id)
                    lists = []
                    for folder in folders:
                        folder_lists = await client.get_lists(folder.id)
                        lists.extend(folder_lists)

                target_lists = [lst for lst in lists if lst.id in self.TARGET_LISTS]
                logger.info(f"📝 Found {len(target_lists)} target lists")

                # Get tasks
                tasks_by_list = {}
                for lst in target_lists:
                    logger.info(f"📋 Fetching tasks from {lst.name}...")
                    tasks = await client.get_tasks(
                        lst.id, include_closed=True, limit=200
                    )
                    tasks_by_list[lst.id] = tasks
                    logger.info(f"   Found {len(tasks)} tasks")

                # Clear existing data if full sync
                if full_sync:
                    self.clear_investic_data()

                # Import data
                self.create_team_and_space(tech_space)
                self.create_lists(target_lists)
                self.create_users_from_tasks(tasks_by_list)
                self.create_tasks(tasks_by_list)

                self.stats.end_time = datetime.now()

                logger.info("✅ Sync completed successfully!")
                logger.info(
                    f"📊 Stats: {self.stats.tasks_synced} tasks, {self.stats.users_synced} users, {self.stats.relationships_created} assignments, {self.stats.subtask_relationships_created} subtask relationships"
                )
                logger.info(f"⏱️  Duration: {self.stats.duration():.1f} seconds")

                return self.stats

            except Exception as e:
                error_msg = f"Sync failed: {e}"
                logger.error(error_msg)
                self.stats.errors.append(error_msg)
                self.stats.end_time = datetime.now()
                raise


if __name__ == "__main__":
    import asyncio

    from src.utils.config import get_config

    async def main():
        config = get_config()
        importer = InvesticDataImporter(
            clickup_api_key=config["clickup"]["api_key"],
            neo4j_uri=config["neo4j"]["uri"],
            neo4j_username=config["neo4j"]["username"],
            neo4j_password=config["neo4j"]["password"],
        )
        await importer.sync_investic_data()

    asyncio.run(main())
