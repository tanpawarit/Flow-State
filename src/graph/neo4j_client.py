# # test_connection.py
# from neo4j import GraphDatabase

# # Connection details from AuraDB
# URI = "neo4j+s://xxxxx.databases.neo4j.io"
# USERNAME = "neo4j"
# PASSWORD = "your_generated_password"


# def test_connection():
#     driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

#     try:
#         # Test query
#         with driver.session() as session:
#             result = session.run("RETURN 'Hello Neo4j!' as message")
#             record = result.single()
#             print(f"Connected: {record['message']}")

#         # Check database info
#         with driver.session() as session:
#             result = session.run("CALL dbms.components() YIELD name, versions")
#             for record in result:
#                 print(f"Component: {record['name']}, Version: {record['versions']}")

#     except Exception as e:
#         print(f"Connection failed: {e}")
#     finally:
#         driver.close()


# if __name__ == "__main__":
#     test_connection()


# # app/neo4j_client.py
# import logging
# import os
# from typing import Any, Dict, List


# class Neo4jClient:
#     def __init__(self):
#         self.uri = os.getenv("NEO4J_URI")
#         self.username = os.getenv("NEO4J_USERNAME", "neo4j")
#         self.password = os.getenv("NEO4J_PASSWORD")

#         if not all([self.uri, self.password]):
#             raise ValueError("Missing Neo4j credentials")

#         self.driver = GraphDatabase.driver(
#             self.uri,
#             auth=(self.username, self.password),
#             max_connection_lifetime=30 * 60,  # 30 minutes
#             max_connection_pool_size=50,
#             connection_acquisition_timeout=2 * 60,  # 2 minutes
#         )

#     def close(self):
#         if self.driver:
#             self.driver.close()

#     def execute_read(self, query: str, parameters: Dict = None) -> List[Dict[str, Any]]:
#         """Execute read query"""
#         with self.driver.session() as session:
#             try:
#                 result = session.run(query, parameters or {})
#                 return [record.data() for record in result]
#             except Exception as e:
#                 logging.error(f"Read query failed: {e}")
#                 return []

#     def execute_write(self, query: str, parameters: Dict = None) -> bool:
#         """Execute write query"""
#         with self.driver.session() as session:
#             try:
#                 session.run(query, parameters or {})
#                 return True
#             except Exception as e:
#                 logging.error(f"Write query failed: {e}")
#                 return False


# # Global client instance
# neo4j_client = Neo4jClient()

# # Cleanup on exit
# import atexit

# atexit.register(lambda: neo4j_client.close())
