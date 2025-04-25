# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-04-25

### Added
- Initial release of DB-ADK
- Database-driven agent configuration using SQLite
- Dynamic loading of tools from Python modules
- Agent network management with relationship types
- REST API for agent and tool management
- CLI interface for database operations and agent execution
- Multi-agent system support with coordinator, sequential, and parallel agents
- SQLAlchemy models for agent, tool, and relationship storage
- Configuration management with environment variables
- Example implementation of a travel planning agent network
- Agent-to-agent communication framework
- Tool discovery and integration system
- JSON schema validation for tool parameters
- Import/export functionality for agents in both JSON and YAML formats
- Auto-detection of file formats during import
- Batch import/export for agent directories

### Tech Stack
- Python 3.9+
- SQLite database (via SQLAlchemy)
- Google ADK integration
- FastAPI for REST endpoints
- Click for CLI commands
- SQLAlchemy ORM for database models
- Python-dotenv for configuration management
- PyYAML for YAML import/export support