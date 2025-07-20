#!/usr/bin/env python3
"""
Simple usage example for AsyncClickUpClient
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.integrations.clickup_client import AsyncClickUpClient, ClickUpList
from src.utils.config import get_clickup_config


async def main():
    """Simple usage example"""
    config = get_clickup_config()
    api_key = config.get("api_key")
    if not api_key:
        print("❌ Please set clickup.api_key in config.yaml")
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

        # Find the "tech" space
        tech_space = None
        for space in spaces:
            print(f"🌌 Space: {space.name}")
            if space.name.lower() == "tech":
                tech_space = space
                break

        if not tech_space:
            print("❌ No 'tech' space found")
            return

        space = tech_space
        print(f"✅ Found tech space: {space.name}")

        # Get folders
        folders = await client.client.get_folders(space.id)

        if folders:
            print(f"📁 Found {len(folders)} folders")
            folder = folders[0]
            print(f"📁 Using folder: {folder.name}")

            # Get lists from folder
            lists = await client.client.get_lists(folder.id)
        else:
            print("⚠️  No folders found, checking for lists directly in space...")
            # Try getting lists directly from space (some spaces have lists without folders)
            try:
                # ClickUp API allows getting lists from space directly
                space_lists_url = f"/space/{space.id}/list"
                data = await client.client._make_request("GET", space_lists_url)
                lists = [ClickUpList(**lst) for lst in data.get("lists", [])]
            except Exception as e:
                print(f"❌ Error getting space lists: {e}")
                lists = []

        if not lists:
            print("❌ No lists found")
            return

        print(f"📝 Found {len(lists)} lists in Tech space:")
        for i, lst in enumerate(lists, 1):
            print(f"   {i}. {lst.name} (ID: {lst.id})")

        # Use first list for testing
        test_list = lists[1]
        print(f"\n🔍 Testing with list: {test_list.name}")
        print()

        # Now test the AsyncClickUpClient methods
        print("🔍 Testing AsyncClickUpClient methods:")

        # 1. Filter by status
        dev_tasks = await client.get_all_tasks_by_status(test_list.id, "dev")
        print(f"   📋 dev tasks: {len(dev_tasks)}")

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
