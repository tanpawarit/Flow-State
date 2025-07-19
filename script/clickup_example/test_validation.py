#!/usr/bin/env python3
"""
Test validation fixes for ClickUp models
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.integrations.clickup_client import ClickUpClient
from src.utils.config import get_clickup_config


async def test_validation():
    """Test that validation errors are fixed"""
    config = get_clickup_config()
    api_key = config.get("api_key")
    if not api_key:
        print("❌ Please set clickup.api_key in config.yaml")
        return

    async with ClickUpClient(api_key) as client:
        print("🔧 Testing validation fixes...")

        # Test teams
        try:
            teams = await client.get_teams()
            print(f"✅ Teams: {len(teams)}")
        except Exception as e:
            print(f"❌ Teams: {e}")

        # Test a simple list with tasks
        teams = await client.get_teams()
        if teams:
            spaces = await client.get_spaces(teams[0].id)
            if spaces:
                folders = await client.get_folders(spaces[0].id)
                if folders:
                    lists = await client.get_lists(folders[0].id)
                    if lists:
                        try:
                            tasks = await client.get_tasks(lists[0].id, limit=1)
                            print(f"✅ Tasks: {len(tasks)}")
                            if tasks:
                                task = tasks[0]
                                print(f"✅ Task name: {task.name}")
                                print(
                                    f"✅ Task orderindex: {task.orderindex} (type: {type(task.orderindex)})"
                                )
                        except Exception as e:
                            print(f"❌ Tasks: {e}")


if __name__ == "__main__":
    asyncio.run(test_validation())
