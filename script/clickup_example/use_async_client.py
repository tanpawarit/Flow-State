#!/usr/bin/env python3
"""
Simple usage example for AsyncClickUpClient
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.integrations.clickup_client import AsyncClickUpClient


async def main():
    """Simple usage example"""
    api_key = os.getenv("CLICKUP_API_KEY")
    if not api_key:
        print("❌ Please set CLICKUP_API_KEY environment variable")
        return

    async with AsyncClickUpClient(api_key) as client:
        print("🚀 AsyncClickUpClient Usage Examples")
        print("=" * 50)

        # Get teams
        teams = await client.client.get_teams()
        team = teams[0]
        print(f"📋 Team: {team.name}")

        # Get spaces
        spaces = await client.client.get_spaces(team.id)
        for space in spaces:
            print(f"🌌 Space: {space.name}")
        space = spaces[0]  # First space
        print(f"🌌 Space: {space.name}")

        # Get folders
        folders = await client.client.get_folders(space.id)
        if not folders:
            print("❌ No folders found")
            return

        folder = folders[0]
        print(f"📁 Folder: {folder.name}")

        # Get lists
        lists = await client.client.get_lists(folder.id)
        if not lists:
            print("❌ No lists found")
            return

        test_list = lists[0]
        print(f"📝 List: {test_list.name} (ID: {test_list.id})")
        print()

        # Now test the AsyncClickUpClient methods
        print("🔍 Testing AsyncClickUpClient methods:")

        # 1. Filter by status
        todo_tasks = await client.get_all_tasks_by_status(test_list.id, "todo")
        print(f"   📋 TODO tasks: {len(todo_tasks)}")

        # 2. Get overdue tasks
        overdue = await client.get_overdue_tasks(test_list.id)
        print(f"   ⏰ Overdue tasks: {len(overdue)}")

        # 3. Get tasks by assignee (using first available assignee)
        all_tasks = await client.client.get_tasks(test_list.id)
        if all_tasks:
            first_task = all_tasks[0]
            if first_task.assignees:
                assignee_id = first_task.assignees[0].get("id")
                if assignee_id:
                    assignee_tasks = await client.get_tasks_by_assignee(
                        test_list.id, assignee_id
                    )
                    print(f"   👤 Tasks by assignee: {len(assignee_tasks)}")

        # 4. Get tasks by tag
        tag_tasks = await client.get_tasks_by_tag(test_list.id, "backtesting")
        print(f"   🏷️  Tasks with 'backtesting' tag: {len(tag_tasks)}")

        print("\n✅ All AsyncClickUpClient methods tested successfully!")


if __name__ == "__main__":
    asyncio.run(main())
