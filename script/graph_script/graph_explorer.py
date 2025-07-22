#!/usr/bin/env python3
"""
Graph Explorer - Interactive text-based exploration of the Neo4j graph
Shows detailed relationships and allows querying specific parts of the graph
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from neo4j import GraphDatabase  # noqa: E402

from src.utils.config import get_neo4j_config  # noqa: E402


class GraphExplorer:
    """Interactive exploration of Neo4j graph"""

    def __init__(self):
        # Neo4j connection
        neo4j_config = get_neo4j_config()
        uri = neo4j_config.get("uri")
        username = neo4j_config.get("username", "neo4j")
        password = neo4j_config.get("password")

        if not all([uri, password]):
            raise ValueError("Neo4j configuration missing")

        # Type assertion since we've verified values are not None
        assert uri is not None and password is not None
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()

    def show_complete_structure(self):
        """Show the complete graph structure with all relationships"""
        print("🔍 Complete Graph Structure")
        print("=" * 60)

        with self.driver.session() as session:
            # Get hierarchical structure
            self._show_hierarchy(session)

            # Show user assignments
            self._show_user_assignments(session)

            # Show task relationships
            self._show_task_relationships(session)

    def _show_hierarchy(self, session):
        """Show organizational hierarchy"""
        print("\n🏗️  Organizational Hierarchy:")
        print("-" * 40)

        # Start from team
        team_query = """
        MATCH (t:Team {id: 'investic_team'})
        RETURN t.name as name
        """
        result = session.run(team_query)
        team_record = result.single()

        if team_record:
            print(f"🏢 {team_record['name']}")

            # Get spaces
            space_query = """
            MATCH (t:Team {id: 'investic_team'})-[:HAS_SPACE]->(s:Space)
            RETURN s.id as id, s.name as name
            """
            space_result = session.run(space_query)

            for space_record in space_result:
                space_id = space_record["id"]
                space_name = space_record["name"]
                print(f"├─ 🌌 {space_name} (ID: {space_id})")

                # Get lists in space
                list_query = """
                MATCH (s:Space {id: $space_id})-[:CONTAINS_LIST]->(l:List)
                RETURN l.id as id, l.name as name, l.task_count as task_count
                ORDER BY l.name
                """
                list_result = session.run(list_query, space_id=space_id)

                lists = list(list_result)
                for i, list_record in enumerate(lists):
                    list_id = list_record["id"]
                    list_name = list_record["name"]
                    task_count = list_record["task_count"]

                    # Check if it's the last list
                    prefix = "└─" if i == len(lists) - 1 else "├─"
                    print(f"│  {prefix} 📝 {list_name} (ID: {list_id})")
                    print(
                        f"│  {'   ' if i == len(lists) - 1 else '│  '}    └─ Stated tasks: {task_count}"
                    )

                    # Get actual task count
                    actual_count_query = """
                    MATCH (l:List {id: $list_id})-[:CONTAINS_TASK]->(t:Task)
                    RETURN count(t) as actual_count
                    """
                    actual_result = session.run(actual_count_query, list_id=list_id)
                    actual_record = actual_result.single()
                    assert actual_record is not None, (
                        f"No actual count found for list {list_id}"
                    )
                    actual_count = actual_record["actual_count"]
                    print(
                        f"│  {'   ' if i == len(lists) - 1 else '│  '}    └─ Actual tasks: {actual_count}"
                    )

    def _show_user_assignments(self, session):
        """Show user assignments with detailed breakdown"""
        print("\n👥 User Assignments:")
        print("-" * 40)

        # Get all users and their assignments
        user_query = """
        MATCH (u:User)
        RETURN u.id as id, u.username as username, u.initials as initials
        ORDER BY u.username
        """

        user_result = session.run(user_query)

        for user_record in user_result:
            user_id = user_record["id"]
            username = user_record["username"]
            initials = user_record["initials"]

            print(f"\n👤 {username} ({initials}) - ID: {user_id}")

            # Get assignments by list
            assignment_query = """
            MATCH (u:User {id: $user_id})-[:ASSIGNED_TO]->(t:Task)
            WHERE t.list_id IN ['901602625750', '901606939084']
            RETURN t.list_id as list_id, 
                   collect(t.name)[0..3] as sample_tasks,
                   count(t) as task_count
            ORDER BY list_id
            """

            assignment_result = session.run(assignment_query, user_id=user_id)

            total_tasks = 0
            for assign_record in assignment_result:
                list_id = assign_record["list_id"]
                task_count = assign_record["task_count"]
                sample_tasks = assign_record["sample_tasks"]
                total_tasks += task_count

                list_name = "Get Shit Done" if list_id == "901602625750" else "PADTAI"
                print(f"   ├─ 📝 {list_name}: {task_count} tasks")

                # Show sample tasks
                for i, task_name in enumerate(sample_tasks):
                    truncated_name = (
                        task_name[:50] + "..." if len(task_name) > 50 else task_name
                    )
                    print(f"   │  └─ {truncated_name}")

                if task_count > 3:
                    print(f"   │  └─ ... and {task_count - 3} more tasks")

            if total_tasks == 0:
                print("   └─ ⚠️  No tasks assigned")
            else:
                print(f"   └─ 📊 Total: {total_tasks} tasks")

    def _show_task_relationships(self, session):
        """Show task relationships like subtasks and dependencies"""
        print("\n🔗 Task Relationships:")
        print("-" * 40)

        # Check for subtask relationships
        subtask_query = """
        MATCH (parent:Task)<-[:SUBTASK_OF]-(child:Task)
        WHERE parent.list_id IN ['901602625750', '901606939084']
        RETURN parent.name as parent_name, 
               parent.list_id as parent_list,
               collect(child.name) as subtasks,
               count(child) as subtask_count
        ORDER BY subtask_count DESC
        LIMIT 10
        """

        subtask_result = session.run(subtask_query)
        subtask_records = list(subtask_result)

        if subtask_records:
            print("\n📋 Tasks with Subtasks:")
            for record in subtask_records:
                parent_name = record["parent_name"]
                parent_list = record["parent_list"]
                subtasks = record["subtasks"]
                subtask_count = record["subtask_count"]

                list_name = (
                    "Get Shit Done" if parent_list == "901602625750" else "PADTAI"
                )
                truncated_parent = (
                    parent_name[:40] + "..." if len(parent_name) > 40 else parent_name
                )

                print(f"\n   📝 {truncated_parent} ({list_name})")
                print(f"      └─ Has {subtask_count} subtasks:")

                for subtask in subtasks[:3]:  # Show first 3
                    truncated_subtask = (
                        subtask[:50] + "..." if len(subtask) > 50 else subtask
                    )
                    print(f"         ├─ {truncated_subtask}")

                if len(subtasks) > 3:
                    print(f"         └─ ... and {len(subtasks) - 3} more")
        else:
            print("\n   ℹ️  No subtask relationships found")

        # Check for other relationships
        other_rel_query = """
        MATCH (t1:Task)-[r]->(t2:Task)
        WHERE t1.list_id IN ['901602625750', '901606939084'] 
        AND t2.list_id IN ['901602625750', '901606939084']
        AND type(r) <> 'SUBTASK_OF'
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY count DESC
        """

        other_rel_result = session.run(other_rel_query)
        other_rels = list(other_rel_result)

        if other_rels:
            print("\n🔄 Other Task Relationships:")
            for record in other_rels:
                rel_type = record["rel_type"]
                count = record["count"]
                print(f"   {rel_type}: {count} relationships")
        else:
            print("\n   ℹ️  No other task relationships found")

    def show_list_details(self, list_name: str):
        """Show detailed information about a specific list"""
        list_id = (
            "901602625750" if list_name.lower() == "get shit done" else "901606939084"
        )

        print(f"\n🔍 Detailed Analysis: {list_name}")
        print("=" * 60)

        with self.driver.session() as session:
            # Basic list info
            list_query = """
            MATCH (l:List {id: $list_id})
            RETURN l.name as name, l.task_count as stated_count
            """

            list_result = session.run(list_query, list_id=list_id)
            list_record = list_result.single()

            if list_record:
                print(f"📝 List: {list_record['name']}")
                print(f"   Stated task count: {list_record['stated_count']}")

                # Get actual task count and breakdown
                task_breakdown_query = """
                MATCH (l:List {id: $list_id})-[:CONTAINS_TASK]->(t:Task)
                RETURN count(t) as actual_count,
                       count(CASE WHEN t.status = 'complete' THEN 1 END) as completed,
                       count(CASE WHEN t.status = 'dev' OR t.status CONTAINS 'dev' THEN 1 END) as in_dev,
                       count(CASE WHEN t.status = 'review' THEN 1 END) as in_review,
                       count(CASE WHEN t.status = 'backlog' THEN 1 END) as backlog
                """

                breakdown_result = session.run(task_breakdown_query, list_id=list_id)
                breakdown = breakdown_result.single()
                assert breakdown is not None, (
                    f"No breakdown data found for list {list_id}"
                )

                print(f"   Actual task count: {breakdown['actual_count']}")
                print(f"   Completed: {breakdown['completed']}")
                print(f"   In Development: {breakdown['in_dev']}")
                print(f"   In Review: {breakdown['in_review']}")
                print(f"   Backlog: {breakdown['backlog']}")

                # User distribution
                user_dist_query = """
                MATCH (u:User)-[:ASSIGNED_TO]->(t:Task)
                WHERE t.list_id = $list_id
                RETURN u.username as username, count(t) as task_count
                ORDER BY task_count DESC
                """

                user_dist_result = session.run(user_dist_query, list_id=list_id)

                print("\n👥 User Distribution:")
                for user_record in user_dist_result:
                    username = user_record["username"]
                    task_count = user_record["task_count"]
                    print(f"   {username}: {task_count} tasks")

    def show_user_details(self, username: str):
        """Show detailed information about a specific user"""
        print(f"\n🔍 Detailed Analysis: {username}")
        print("=" * 60)

        with self.driver.session() as session:
            # Find user
            user_query = """
            MATCH (u:User)
            WHERE u.username CONTAINS $username
            RETURN u.id as id, u.username as username, u.email as email, u.initials as initials
            """

            user_result = session.run(user_query, username=username)
            user_record = user_result.single()

            if not user_record:
                print(f"❌ User '{username}' not found")
                return

            user_id = user_record["id"]
            full_username = user_record["username"]
            email = user_record["email"]
            initials = user_record["initials"]

            print(f"👤 User: {full_username} ({initials})")
            print(f"   Email: {email}")
            print(f"   ID: {user_id}")

            # Get all tasks assigned to user
            task_query = """
            MATCH (u:User {id: $user_id})-[:ASSIGNED_TO]->(t:Task)
            WHERE t.list_id IN ['901602625750', '901606939084']
            RETURN t.name as task_name, 
                   t.status as status,
                   t.priority as priority,
                   t.list_id as list_id,
                   t.due_date as due_date
            ORDER BY t.due_date DESC, t.status
            """

            task_result = session.run(task_query, user_id=user_id)

            get_shit_done_tasks = []
            padtai_tasks = []

            for task_record in task_result:
                task_data = {
                    "name": task_record["task_name"],
                    "status": task_record["status"] or "No Status",
                    "priority": task_record["priority"] or "No Priority",
                    "due_date": task_record["due_date"],
                }

                if task_record["list_id"] == "901602625750":
                    get_shit_done_tasks.append(task_data)
                else:
                    padtai_tasks.append(task_data)

            # Show tasks by list
            if get_shit_done_tasks:
                print(f"\n📝 Get Shit Done Tasks ({len(get_shit_done_tasks)}):")
                for i, task in enumerate(get_shit_done_tasks[:10]):  # Show first 10
                    truncated_name = (
                        task["name"][:60] + "..."
                        if len(task["name"]) > 60
                        else task["name"]
                    )
                    print(f"   {i + 1:2d}. {truncated_name}")
                    print(
                        f"       Status: {task['status']} | Priority: {task['priority']}"
                    )

                if len(get_shit_done_tasks) > 10:
                    print(f"       ... and {len(get_shit_done_tasks) - 10} more tasks")

            if padtai_tasks:
                print(f"\n📝 PADTAI Tasks ({len(padtai_tasks)}):")
                for i, task in enumerate(padtai_tasks[:10]):  # Show first 10
                    truncated_name = (
                        task["name"][:60] + "..."
                        if len(task["name"]) > 60
                        else task["name"]
                    )
                    print(f"   {i + 1:2d}. {truncated_name}")
                    print(
                        f"       Status: {task['status']} | Priority: {task['priority']}"
                    )

                if len(padtai_tasks) > 10:
                    print(f"       ... and {len(padtai_tasks) - 10} more tasks")

            if not get_shit_done_tasks and not padtai_tasks:
                print("\n   ⚠️  No tasks assigned to this user")


def main():
    """Main function with interactive menu"""
    explorer = GraphExplorer()

    try:
        print("🔍 Graph Explorer - Investic Tech Space")
        print("=" * 60)

        while True:
            print("\nChoose an option:")
            print("1. Show complete graph structure")
            print("2. Show Get Shit Done list details")
            print("3. Show PADTAI list details")
            print("4. Show user details (enter username)")
            print("5. Exit")

            choice = input("\nEnter your choice (1-5): ").strip()

            if choice == "1":
                explorer.show_complete_structure()

            elif choice == "2":
                explorer.show_list_details("Get Shit Done")

            elif choice == "3":
                explorer.show_list_details("PADTAI")

            elif choice == "4":
                username = input("Enter username (or part of username): ").strip()
                if username:
                    explorer.show_user_details(username)
                else:
                    print("❌ Please enter a username")

            elif choice == "5":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please enter 1-5")

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        explorer.close()


if __name__ == "__main__":
    main()
