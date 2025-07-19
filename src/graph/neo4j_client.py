import logging
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase

from src.utils.config import get_neo4j_config


class Neo4jClient:
    def __init__(self):
        """Initialize Neo4j client.

        Parameters
        ----------
        uri : str, optional
            Neo4j URI. If not provided, loads from config.yaml
        username : str, optional
            Neo4j username. If not provided, loads from config.yaml
        password : str, optional
            Neo4j password. If not provided, loads from config.yaml
        """
        config = get_neo4j_config()

        uri = config.get("uri")
        username = config.get("username")
        password = config.get("password")

        if not all([uri, username, password]):
            raise ValueError(
                "Missing Neo4j credentials. Please check your config.yaml file."
            )

        # Safe assignment after validation
        self.uri = str(uri)
        self.username = str(username)
        self.password = str(password)

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
            max_connection_lifetime=30 * 60,  # 30 minutes
            max_connection_pool_size=50,
            connection_acquisition_timeout=2 * 60,  # 2 minutes
        )

    def close(self):
        if self.driver:
            self.driver.close()

    def execute_read(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute read query"""
        with self.driver.session() as session:
            try:
                result = session.run(query, parameters or {})  # type: ignore[arg-type]
                return [record.data() for record in result]
            except Exception as e:
                logging.error(f"Read query failed: {e}")
                return []

    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> bool:
        """Execute write query"""
        with self.driver.session() as session:
            try:
                session.run(query, parameters or {})  # type: ignore[arg-type]
                return True
            except Exception as e:
                logging.error(f"Write query failed: {e}")
                return False
