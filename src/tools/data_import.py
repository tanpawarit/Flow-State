#!/usr/bin/env python3
"""
Import and sync Investic Tech space data from ClickUp to Neo4j
Focuses on Get Shit Done and PADTAI lists only
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.graph.operations.importer import InvesticDataImporter  # noqa: E402
from src.utils.config import get_clickup_config, get_neo4j_config  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main function"""
    # Get configuration
    clickup_config = get_clickup_config()
    neo4j_config = get_neo4j_config()

    api_key = clickup_config.get("api_key")
    if not api_key:
        print("❌ Please set clickup.api_key in config.yaml")
        return

    neo4j_uri = neo4j_config.get("uri")
    neo4j_username = neo4j_config.get("username", "neo4j")
    neo4j_password = neo4j_config.get("password")

    if not all([neo4j_uri, neo4j_password]):
        print("❌ Please set neo4j configuration in config.yaml")
        return

    # Type assertion since we've verified values are not None
    assert neo4j_uri is not None and neo4j_password is not None
    # Run sync
    async with InvesticDataImporter(
        api_key, neo4j_uri, neo4j_username, neo4j_password
    ) as importer:
        try:
            stats = await importer.sync_investic_data(full_sync=True)
            print(f"✅ Sync completed: {stats.tasks_synced} tasks imported")
        except Exception as e:
            print(f"❌ Sync failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
