#!/usr/bin/env python3
"""
Test AsyncClickUpClient convenience methods
Tests all filtering functions: by status, overdue, assignee, and tag
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integrations.clickup_client import AsyncClickUpClient


class AsyncTestRunner:
    """Test runner for AsyncClickUpClient convenience methods"""

    def __init__(self, client: AsyncClickUpClient):
        self.client = client

    async def find_working_list(self):
        """Find a working list with tasks for testing"""
        teams = await self.client.client.get_teams()
        if not teams:
            return None

        spaces = await self.client.client.get_spaces(teams[0].id)
        if not spaces:
            return None

        for space in spaces:
            folders = await self.client.client.get_folders(space.id)
            for folder in folders:
                lists = await self.client.client.get_lists(folder.id)
                for lst in lists:
                    tasks = await self.client.client.get_tasks(lst.id, limit=1)
                    if tasks:
                        return lst
        return None

    async def test_by_status(self, list_id: str):
        """Test get_all_tasks_by_status"""
        print("🔍 Testing get_all_tasks_by_status...")

        # Get all tasks to see what statuses are available
        all_tasks = await self.client.client.get_tasks(list_id, include_closed=True)
        if not all_tasks:
            print("   ⚠️  No tasks found")
            return

        # Get unique statuses
        statuses = set()
        for task in all_tasks:
            if task.status:
                if isinstance(task.status, dict):
                    status_name = task.status.get("status", str(task.status))
                else:
                    status_name = str(task.status)
                statuses.add(status_name)

        print(f"   📊 Available statuses: {list(statuses)}")

        # Test filtering by each status
        for status in list(statuses)[:3]:  # Test first 3 statuses
            try:
                filtered_tasks = await self.client.get_all_tasks_by_status(
                    list_id, status
                )
                print(f"   ✅ Status '{status}': {len(filtered_tasks)} tasks")
            except Exception as e:
                print(f"   ❌ Status '{status}': {e}")

    async def test_overdue_tasks(self, list_id: str):
        """Test get_overdue_tasks"""
        print("⏰ Testing get_overdue_tasks...")
        try:
            overdue = await self.client.get_overdue_tasks(list_id)
            print(f"   ✅ Overdue tasks: {len(overdue)}")

            for task in overdue[:3]:
                print(f"      📅 {task.name} - Due: {task.due_date}")
        except Exception as e:
            print(f"   ❌ Overdue test: {e}")

    async def test_by_assignee(self, list_id: str):
        """Test get_tasks_by_assignee"""
        print("👤 Testing get_tasks_by_assignee...")

        # Get all tasks to see assignees
        all_tasks = await self.client.client.get_tasks(list_id)
        assignees = set()

        for task in all_tasks:
            for assignee in task.assignees:
                if isinstance(assignee, dict) and "id" in assignee:
                    assignees.add(assignee["id"])

        if not assignees:
            print("   ⚠️  No assignees found")
            return

        assignee_list = list(assignees)[:2]  # Test first 2 assignees
        for assignee_id in assignee_list:
            try:
                tasks = await self.client.get_tasks_by_assignee(list_id, assignee_id)
                print(f"   ✅ Assignee {assignee_id}: {len(tasks)} tasks")
            except Exception as e:
                print(f"   ❌ Assignee {assignee_id}: {e}")

    async def test_by_tag(self, list_id: str):
        """Test get_tasks_by_tag"""
        print("🏷️  Testing get_tasks_by_tag...")

        # Get all tasks to see tags
        all_tasks = await self.client.client.get_tasks(list_id)
        tags = set()

        for task in all_tasks:
            for tag in task.tags:
                if isinstance(tag, dict) and "name" in tag:
                    tags.add(tag["name"])

        if not tags:
            print("   ⚠️  No tags found")
            return

        tag_list = list(tags)[:3]  # Test first 3 tags
        for tag_name in tag_list:
            try:
                tasks = await self.client.get_tasks_by_tag(list_id, tag_name)
                print(f"   ✅ Tag '{tag_name}': {len(tasks)} tasks")
            except Exception as e:
                print(f"   ❌ Tag '{tag_name}': {e}")

    async def run_all_tests(self):
        """Run all AsyncClickUpClient tests"""
        print("🚀 Starting AsyncClickUpClient Tests...")
        print("=" * 60)

        # Find a working list
        test_list = await self.find_working_list()
        if not test_list:
            print("❌ No working list found with tasks")
            return

        print(f"📋 Using list: {test_list.name} (ID: {test_list.id})")
        print()

        # Run all tests
        await self.test_by_status(test_list.id)
        print()

        await self.test_overdue_tasks(test_list.id)
        print()

        await self.test_by_assignee(test_list.id)
        print()

        await self.test_by_tag(test_list.id)
        print()

        print("✅ All AsyncClickUpClient tests completed!")


async def main():
    """Main test function"""
    api_key = os.getenv("CLICKUP_API_KEY")
    if not api_key:
        print("❌ Please set CLICKUP_API_KEY environment variable")
        return

    async with AsyncClickUpClient(api_key) as client:
        tester = AsyncTestRunner(client)
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
