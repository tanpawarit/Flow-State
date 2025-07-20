from __future__ import annotations

import os
from typing import Any, Dict, Optional

import yaml

from src.utils.logger import get_logger

"""Thin wrapper around **YAML** to keep call-sites minimal and testable."""

logger = get_logger(__name__)

DEFAULT_CONFIG_PATH: str = os.path.join(os.getcwd(), "config.yaml")

# Global config cache
_config_cache: Optional[Dict[str, Any]] = None


def get_config(config_path: str | None = None) -> Dict[str, Any]:
    """Load and return configuration from a YAML file.

    Parameters
    ----------
    config_path: str | None, optional
        Path to the YAML configuration file.
        When None, defaults to "config.yaml" in the current working directory.

    Returns
    -------
    Dict[str, Any]
        Configuration values from the YAML file.

    Raises
    ------
    FileNotFoundError
        If the configuration file doesn't exist.
    yaml.YAMLError
        If the YAML file has invalid syntax.
    """
    global _config_cache

    # Return cached config if available and no custom path provided
    if _config_cache is not None and config_path is None:
        return _config_cache

    # Use provided path or default
    cfg_path: str = config_path or DEFAULT_CONFIG_PATH

    # Check if file exists
    if not os.path.isfile(cfg_path):
        raise FileNotFoundError(f"Configuration file not found: {cfg_path}")

    logger.info(f"Loading configuration from {cfg_path}")

    # Load and return config
    with open(cfg_path, "r", encoding="utf-8") as fp:
        try:
            config: Dict[str, Any] = yaml.safe_load(fp) or {}
            if config_path is None:  # Only cache default config
                _config_cache = config
            return config
        except yaml.YAMLError as exc:
            logger.error(f"Failed to parse YAML configuration: {exc}")
            raise


def get_clickup_config() -> Dict[str, Any]:
    """Get ClickUp configuration.

    Returns
    -------
    Dict[str, Any]
        ClickUp configuration containing api_key and team_id
    """
    config = get_config()
    return config.get("clickup", {})


def get_neo4j_config() -> Dict[str, Any]:
    """Get Neo4j configuration.

    Returns
    -------
    Dict[str, Any]
        Neo4j configuration containing uri, username, and password
    """
    config = get_config()
    return config.get("neo4j", {})


def reload_config() -> None:
    """Force reload configuration from file."""
    global _config_cache
    _config_cache = None
    logger.info("Configuration cache cleared")


class Config:
    """Configuration class for accessing YAML configuration values."""

    @staticmethod
    def get(config_path: str | None = None) -> Dict[str, Any]:
        """Load and return configuration from a YAML file."""
        return get_config(config_path)

    @staticmethod
    def get_clickup() -> Dict[str, Any]:
        """Get ClickUp configuration."""
        return get_clickup_config()

    @staticmethod
    def get_neo4j() -> Dict[str, Any]:
        """Get Neo4j configuration."""
        return get_neo4j_config()

    @staticmethod
    def reload() -> None:
        """Force reload configuration from file."""
        reload_config()
