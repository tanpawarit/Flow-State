#!/usr/bin/env python3
"""
Simple Neo4j test runner to verify the Neo4j client is working correctly.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from graph.neo4j_client import Neo4jClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_connection():
    """Test basic Neo4j connection."""
    print("🔄 Testing Neo4j connection...")
    
    try:
        client = Neo4jClient()
        print("✅ Neo4j client initialized successfully")
        return client
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return None
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


def test_basic_queries(client):
    """Test basic read and write queries."""
    if not client:
        return False

    print("\n🔄 Testing basic queries...")
    
    # Test write query
    write_query = """
    CREATE (test:TestNode {name: $name, timestamp: $timestamp})
    RETURN id(test) as node_id
    """
    
    try:
        write_result = client.execute_write(
            write_query,
            {"name": "test_connection", "timestamp": "2024-01-01"}
        )
        
        if write_result:
            print("✅ Write query successful")
        else:
            print("❌ Write query failed")
            return False
            
    except Exception as e:
        print(f"❌ Write query error: {e}")
        return False

    # Test read query
    read_query = """
    MATCH (test:TestNode {name: $name})
    RETURN test.name as name, test.timestamp as timestamp
    LIMIT 5
    """
    
    try:
        results = client.execute_read(read_query, {"name": "test_connection"})
        
        if results:
            print(f"✅ Read query successful - found {len(results)} records")
            for record in results:
                print(f"   📄 Found: {record}")
        else:
            print("⚠️  Read query returned no results")
            
        return True
        
    except Exception as e:
        print(f"❌ Read query error: {e}")
        return False


def cleanup_test_data(client):
    """Clean up test data."""
    if not client:
        return
        
    print("\n🧹 Cleaning up test data...")
    
    cleanup_query = """
    MATCH (test:TestNode {name: $name})
    DELETE test
    """
    
    try:
        result = client.execute_write(cleanup_query, {"name": "test_connection"})
        if result:
            print("✅ Test data cleaned up")
        else:
            print("⚠️  No test data to clean up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")


def show_database_info(client):
    """Show basic database information."""
    if not client:
        return
        
    print("\n📊 Database Information:")
    
    try:
        # Get node count
        node_count = client.execute_read("MATCH (n) RETURN count(n) as count")
        if node_count:
            print(f"   📈 Total nodes: {node_count[0]['count']}")
            
        # Get relationship count
        rel_count = client.execute_read("MATCH ()-[r]-() RETURN count(r) as count")
        if rel_count:
            print(f"   🔗 Total relationships: {rel_count[0]['count']}")
            
        # Get labels
        labels = client.execute_read("CALL db.labels() YIELD label RETURN label LIMIT 10")
        if labels:
            print(f"   🏷️  Labels: {[l['label'] for l in labels]}")
            
    except Exception as e:
        print(f"⚠️  Could not fetch database info: {e}")


def main():
    """Main test runner."""
    print("🚀 Neo4j Client Test Runner")
    print("=" * 40)
    
    # Test connection
    client = test_connection()
    if not client:
        print("\n❌ Aborting tests due to connection failure")
        return 1
    
    try:
        # Show database info
        show_database_info(client)
        
        # Test queries
        success = test_basic_queries(client)
        
        if success:
            print("\n✅ All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
            
    finally:
        # Always cleanup and close
        cleanup_test_data(client)
        client.close()
        print("\n🔌 Connection closed")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)