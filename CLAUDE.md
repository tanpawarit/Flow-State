# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Flow-State** is a GraphRAG Discord Bot that combines ClickUp task management with Neo4j graph database and AI analytics for intelligent project management. The bot provides real-time project insights, bottleneck detection, and team workload optimization for development teams.

## Technology Stack

- **Language**: Python 3.12+
- **Package Manager**: uv (modern Python package manager)
- **Database**: Neo4j AuraDB (graph database)
- **Bot Framework**: Discord.py
- **API Integration**: ClickUp REST API, aiohttp/httpx
- **Configuration**: YAML-based config management
- **Data Validation**: Pydantic models
- **Testing**: pytest with markers (unit, integration, slow)

## Development Commands

```bash
# Package management
uv install              # Install dependencies
uv add <package>        # Add new dependency

# Testing
pytest                  # Run all tests
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests

# Run application
python main.py          # Start the Discord bot
```

## Configuration

- **Primary config**: `config.yaml` (gitignored, contains API keys)
- **Template**: `example-config.yaml` (safe to commit)
- **Required credentials**: ClickUp API key, Neo4j AuraDB connection, Discord bot token

Example config structure:
```yaml
clickup:
  api_key: "pk_xxx"
  team_id: "xxx"
neo4j:
  uri: "neo4j+s://xxx.databases.neo4j.io"
  username: "neo4j"
  password: "xxx"
discord:
  token: "xxx"
```

## Architecture

### Core Components

1. **`src/bot/`** - Discord bot implementation with 25+ commands
2. **`src/graph/`** - Neo4j operations and graph schema management
3. **`src/integrations/`** - ClickUp API client and data processing
4. **`src/ai/`** - LLM integration for analysis and recommendations
5. **`src/utils/`** - Configuration and logging utilities

### Graph Schema

The Neo4j database models project management entities:

- **Nodes**: Task, User, Space, Folder, List, Status, Priority, Tag, Sprint
- **Relationships**: ASSIGNED_TO, DEPENDS_ON, BELONGS_TO, BLOCKS, HAS_STATUS, etc.

Schema definitions are in `src/graph/schema/` with sample queries and structure examples.

### Discord Bot Commands

Commands are organized in categories:
- **Status**: `/project-status`, `/milestone-status`, `/daily-report`
- **Team**: `/team-workload`, `/my-tasks`, `/team-member`
- **Analysis**: `/bottleneck`, `/impact-analysis`, `/critical-path`
- **AI Suggestions**: `/suggest-priority`, `/resource-suggestions`
- **Data Management**: `/sync-data`, `/graph-stats`

## Development Workflow

1. **Async Architecture**: All operations use async/await for scalability
2. **Type Safety**: Pydantic models throughout for data validation
3. **Error Handling**: Comprehensive exception management with graceful fallbacks
4. **Rate Limiting**: Built-in API rate limiting for external services
5. **Security**: API keys in gitignored config, no hardcoded credentials

## Key Integration Points

- **ClickUp API**: Full CRUD operations for teams, spaces, tasks with rate limiting
- **Neo4j**: Graph operations for relationship analysis and dependency mapping
- **Discord**: Command processing and rich response formatting with embeds
- **AI/LLM**: Context-aware analysis using graph data for recommendations

## Testing Structure

Tests are categorized with pytest markers:
- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests with external services
- `@pytest.mark.slow` - Long-running tests (can be skipped during development)

## Data Flow

1. **Input**: Discord commands or ClickUp webhooks
2. **Processing**: Graph queries + AI analysis
3. **Output**: Formatted Discord responses with actionable insights

The system maintains real-time sync between ClickUp tasks and the Neo4j knowledge graph for up-to-date project analytics.