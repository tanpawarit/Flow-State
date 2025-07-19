#!/usr/bin/env python3
"""
ClickUp REST API Client Example
Demonstrates all available functions with detailed usage
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

from src.integrations.clickup_client import ClickUpClient


class ColorPrinter:
    """Color printing utilities"""

    COLORS = {
        "HEADER": "\033[95m",
        "OKBLUE": "\033[94m",
        "OKGREEN": "\033[92m",
        "WARNING": "\033[93m",
        "FAIL": "\033[91m",
        "BOLD": "\033[1m",
        "UNDERLINE": "\033[4m",
        "ENDC": "\033[0m",
    }

    @classmethod
    def print_header(cls, text):
        print(
            f"\n{cls.COLORS['HEADER']}{cls.COLORS['BOLD']}{'=' * 60}{cls.COLORS['ENDC']}"
        )
        print(
            f"{cls.COLORS['HEADER']}{cls.COLORS['BOLD']}{text.center(60)}{cls.COLORS['ENDC']}"
        )
        print(
            f"{cls.COLORS['HEADER']}{cls.COLORS['BOLD']}{'=' * 60}{cls.COLORS['ENDC']}"
        )

    @classmethod
    def print_success(cls, text):
        print(f"{cls.COLORS['OKGREEN']}✅ {text}{cls.COLORS['ENDC']}")

    @classmethod
    def print_info(cls, text):
        print(f"{cls.COLORS['OKBLUE']}ℹ️  {text}{cls.COLORS['ENDC']}")

    @classmethod
    def print_warning(cls, text):
        print(f"{cls.COLORS['WARNING']}⚠️  {text}{cls.COLORS['ENDC']}")


class ClickUpExample:
    """Comprehensive example class demonstrating all ClickUp client functions"""

    def __init__(self, client: ClickUpClient):
        self.client = client
        self.printer = ColorPrinter()

    async def demonstrate_all_functions(self):
        """Demonstrate all available functions"""

        self.printer.print_header("CLICKUP REST API CLIENT - ALL FUNCTIONS DEMO")

        # 1. Connection and Basic Info
        await self.demo_connection()

        # 2. Team Operations
        await self.demo_teams()

        # 3. Space Operations
        await self.demo_spaces()

        # 4. Folder Operations
        await self.demo_folders()

        # 5. List Operations
        await self.demo_lists()

        # 6. Task Operations
        await self.demo_tasks()

        # 7. Comment Operations
        await self.demo_comments()

        # 8. Utility Functions
        await self.demo_utilities()

    async def demo_connection(self):
        """Demonstrate connection and basic info"""
        self.printer.print_header("1. CONNECTION TEST")

        try:
            teams = await self.client.get_teams()
            self.printer.print_success(f"Connected! Found {len(teams)} teams")

            for team in teams:
                self.printer.print_info(f"Team: {team.name} (ID: {team.id})")

            return teams
        except Exception as e:
            self.printer.print_warning(f"Connection failed: {e}")
            return []

    async def demo_teams(self):
        """Demonstrate team operations"""
        self.printer.print_header("2. TEAM OPERATIONS")

        teams = await self.client.get_teams()

        if teams:
            team = teams[0]
            self.printer.print_success(f"Working with team: {team.name}")

            # Display team details
            print(f"  Name: {team.name}")
            print(f"  ID: {team.id}")
            print(f"  Color: {team.color}")
            if team.avatar:
                print(f"  Avatar: {team.avatar}")
            print(f"  Members: {len(team.members)}")

        return teams

    async def demo_spaces(self):
        """Demonstrate space operations"""
        self.printer.print_header("3. SPACE OPERATIONS")

        teams = await self.client.get_teams()
        if not teams:
            return []

        team = teams[0]
        spaces = await self.client.get_spaces(team.id)

        self.printer.print_success(f"Found {len(spaces)} spaces in {team.name}")

        for space in spaces[:3]:  # Show first 3
            print(f"\n  📍 {space.name}")
            print(f"    ID: {space.id}")
            print(f"    Private: {space.private}")
            print(f"    Archived: {space.archived}")

        return spaces

    async def demo_folders(self):
        """Demonstrate folder operations"""
        self.printer.print_header("4. FOLDER OPERATIONS")

        teams = await self.client.get_teams()
        if not teams:
            return []

        # Get first space with folders
        spaces = await self.client.get_spaces(teams[0].id)
        if not spaces:
            return []

        space = spaces[0]
        folders = await self.client.get_folders(space.id)

        self.printer.print_success(f"Found {len(folders)} folders in {space.name}")

        for folder in folders[:3]:  # Show first 3
            print(f"\n  📁 {folder.name}")
            print(f"    ID: {folder.id}")
            print(f"    Task Count: {folder.task_count}")

        return folders

    async def demo_lists(self):
        """Demonstrate list operations"""
        self.printer.print_header("5. LIST OPERATIONS")

        # Get first available list
        teams = await self.client.get_teams()
        if not teams:
            return []

        spaces = await self.client.get_spaces(teams[0].id)
        if not spaces:
            return []

        folders = await self.client.get_folders(spaces[0].id)
        if not folders:
            return []

        lists = await self.client.get_lists(folders[0].id)

        self.printer.print_success(f"Found {len(lists)} lists")

        for lst in lists[:3]:  # Show first 3
            print(f"\n  📋 {lst.name}")
            print(f"    ID: {lst.id}")
            print(f"    Task Count: {lst.task_count}")
            print(f"    Status: {lst.status}")
            print(f"    Priority: {lst.priority}")

        return lists

    async def demo_tasks(self):
        """Demonstrate task operations"""
        self.printer.print_header("6. TASK OPERATIONS")

        # Get first available list with tasks
        teams = await self.client.get_teams()
        if not teams:
            return []

        spaces = await self.client.get_spaces(teams[0].id)
        if not spaces:
            return []

        folders = await self.client.get_folders(spaces[0].id)
        if not folders:
            return []

        lists = await self.client.get_lists(folders[0].id)
        if not lists:
            return []

        test_list = lists[0]

        # Get tasks
        tasks = await self.client.get_tasks(test_list.id, limit=5)
        self.printer.print_success(f"Found {len(tasks)} tasks in {test_list.name}")

        # Display tasks
        for task in tasks:
            print(f"\n  📝 {task.name}")
            print(f"    ID: {task.id}")
            print(f"    Status: {task.status}")
            print(f"    Priority: {task.priority}")
            print(f"    Due Date: {task.due_date}")
            print(f"    Assignees: {len(task.assignees)}")
            print(f"    Tags: {[tag.get('name') for tag in task.tags]}")

        # Create sample task
        if lists:
            try:
                new_task = await self.client.create_task(
                    list_id=test_list.id,
                    name=f"Demo Task - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    description="This is a demo task created by the example",
                    priority=3,
                )
                self.printer.print_success(f"Created task: {new_task.name}")

                # Update task
                updated_task = await self.client.update_task(
                    new_task.id,
                    name=f"Updated Demo Task - {datetime.now().strftime('%H:%M')}",
                )
                self.printer.print_success(f"Updated task: {updated_task.name}")

                # Get detailed task
                detailed_task = await self.client.get_task(new_task.id)
                print(f"    Detailed: {detailed_task.name} ({detailed_task.status})")

                # Clean up
                await self.client.delete_task(new_task.id)
                self.printer.print_success("Deleted demo task")

            except Exception as e:
                self.printer.print_warning(f"Task demo failed: {e}")

        return tasks

    async def demo_comments(self):
        """Demonstrate comment operations"""
        self.printer.print_header("7. COMMENT OPERATIONS")

        # Get first available task
        teams = await self.client.get_teams()
        if not teams:
            return []

        spaces = await self.client.get_spaces(teams[0].id)
        if not spaces:
            return []

        folders = await self.client.get_folders(spaces[0].id)
        if not folders:
            return []

        lists = await self.client.get_lists(folders[0].id)
        if not lists:
            return []

        tasks = await self.client.get_tasks(lists[0].id, limit=1)
        if not tasks:
            return []

        task = tasks[0]

        # Get comments
        comments = await self.client.get_task_comments(task.id)
        self.printer.print_success(f"Found {len(comments)} comments for {task.name}")

        for comment in comments[:2]:  # Show first 2
            print(f"  💬 {comment.comment_text[:100]}...")

        return comments

    async def demo_utilities(self):
        """Demonstrate utility functions"""
        self.printer.print_header("8. UTILITY FUNCTIONS")

        teams = await self.client.get_teams()
        if not teams:
            return

        # Search tasks
        try:
            search_results = await self.client.search_tasks("test", team_id=teams[0].id)
            self.printer.print_success(f"Search found {len(search_results)} tasks")
        except Exception as e:
            self.printer.print_warning(f"Search failed: {e}")

        # Get hierarchy
        try:
            hierarchy = await self.client.get_hierarchy(teams[0].id)
            self.printer.print_success("Retrieved complete team hierarchy")

            print(f"  Team: {len(hierarchy['team'])} teams")
            print(f"  Spaces: {len(hierarchy['spaces'])} spaces")
            print(
                f"  Folders: {sum(len(f) for f in hierarchy['folders'].values())} folders"
            )
            print(f"  Lists: {sum(len(l) for l in hierarchy['lists'].values())} lists")
            print(f"  Tasks: {sum(len(t) for t in hierarchy['tasks'].values())} tasks")
        except Exception as e:
            self.printer.print_warning(f"Hierarchy failed: {e}")


def print_all_functions():
    """Print all available functions"""
    print("\n" + "=" * 80)
    print("CLICKUP REST API CLIENT - ALL AVAILABLE FUNCTIONS")
    print("=" * 80)

    functions = [
        # Team Operations
        ("ClickUpClient.get_teams()", "Get all teams"),
        # Space Operations
        ("ClickUpClient.get_spaces(team_id)", "Get spaces for a team"),
        # Folder Operations
        ("ClickUpClient.get_folders(space_id)", "Get folders for a space"),
        # List Operations
        ("ClickUpClient.get_lists(folder_id)", "Get lists for a folder"),
        ("ClickUpClient.get_list(list_id)", "Get specific list"),
        # Task Operations
        ("ClickUpClient.get_tasks(list_id)", "Get tasks for a list"),
        ("ClickUpClient.get_task(task_id)", "Get specific task"),
        ("ClickUpClient.create_task(list_id, name, ...)", "Create new task"),
        ("ClickUpClient.update_task(task_id, ...)", "Update existing task"),
        ("ClickUpClient.delete_task(task_id)", "Delete task"),
        # Comment Operations
        ("ClickUpClient.get_task_comments(task_id)", "Get task comments"),
        ("ClickUpClient.create_task_comment(task_id, text)", "Add task comment"),
        # Search & Utilities
        ("ClickUpClient.search_tasks(query)", "Search for tasks"),
        ("ClickUpClient.get_hierarchy(team_id)", "Get complete team structure"),
        # Async Client Convenience
        (
            "AsyncClickUpClient.get_all_tasks_by_status(list_id, status)",
            "Filter tasks by status",
        ),
        ("AsyncClickUpClient.get_overdue_tasks(list_id)", "Get overdue tasks"),
        (
            "AsyncClickUpClient.get_tasks_by_assignee(list_id, assignee_id)",
            "Filter by assignee",
        ),
        ("AsyncClickUpClient.get_tasks_by_tag(list_id, tag)", "Filter by tag"),
    ]

    for func, description in functions:
        print(f"\n📋 {func}")
        print(f"   {description}")

    print("\n" + "=" * 80)
    print("USAGE EXAMPLES:")
    print("=" * 80)

    examples = [
        "# Basic usage:",
        "async with ClickUpClient() as client:",
        "    teams = await client.get_teams()",
        "    ",
        "# Create task:",
        "task = await client.create_task(",
        "    list_id='123456789',",
        "    name='My New Task',",
        "    description='Task description',",
        "    priority=3",
        ")",
        "",
        "# Get all tasks:",
        "tasks = await client.get_tasks('123456789')",
        "",
        "# Search tasks:",
        "results = await client.search_tasks('important', team_id='987654321')",
    ]

    for example in examples:
        print(example)


async def main():
    """Main function to run all demonstrations"""
    api_key = os.getenv("CLICKUP_API_KEY")
    if not api_key:
        print("❌ Please set CLICKUP_API_KEY environment variable")
        print("   export CLICKUP_API_KEY=your_api_key_here")
        return

    print_all_functions()

    async with ClickUpClient(api_key) as client:
        example = ClickUpExample(client)
        await example.demonstrate_all_functions()


if __name__ == "__main__":
    asyncio.run(main())
