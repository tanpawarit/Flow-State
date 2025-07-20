"""
Integration modules for external services.

This package provides clients for integrating with external services like ClickUp and Neo4j.
"""

from src.integrations.clickup.client import ClickUpClient
from src.integrations.neo4j.client import Neo4jClient

__all__ = ["ClickUpClient", "Neo4jClient"]