# DB-ADK: Database-Driven Agent Development Kit

DB-ADK is a Python package that extends Google's Agent Development Kit (ADK) to create a fully database-driven approach for building and managing agent networks. This approach minimizes explicit Python coding by storing agent configurations, prompts, and tool definitions in a PostgreSQL database.

## Key Features

- **Database-Driven**: Store all agent and tool configurations in PostgreSQL
- **Minimal Python Coding**: Define new agents and tools through the database or API without writing new code
- **Dynamic Loading**: Automatically load tools and create agents from database records
- **Agent Networks**: Build complex multi-agent systems with different relationship types
- **API Interfaces**: REST API and CLI for managing agents, tools, and networks
- **Extensible**: Easily add new tools and agent types

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/db-adk.git
cd db-adk

# Install the package
pip install -e .
```

## Requirements

- Python 3.9+
- PostgreSQL database
- Google ADK (`google-adk`)

## Quick Start

### 1. Set up environment variables

Create a `.env` file with your database and ADK configuration:

```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=db_adk
ADK_API_KEY=your_api_key
DEFAULT_MODEL=gemini-1.5-pro
```

### 2. Initialize the database

```bash
# Initialize the database
db-adk db init
```

### 3. Create agents and tools

You can create agents and tools using the CLI, REST API, or by directly inserting records into the database.

Using the CLI:

```bash
# Create a tool
db-adk tools create \
  --name "get_weather" \
  --description "Get weather information for a location" \
  --type "python_function" \
  --module "my_tools.weather" \
  --function "get_weather" \
  --schema weather_schema.json

# Create an agent
db-adk agents create \
  --name "weather_assistant" \
  --description "Provides weather information" \
  --type "LLM" \
  --prompt "You are a weather assistant that provides weather information." \
  --model "gemini-1.5-pro"

# Assign tool to agent
db-adk agent-tools assign --agent-id 1 --tool-id 1
```

### 4. Run an agent

```bash
# Create input.json with the query
echo '{"query": "What is the weather in New York?"}' > input.json

# Run the agent
db-adk agents run 1 --input input.json
```

### 5. Run the REST API server

```bash
# Start the server
db-adk serve
```

## Architecture

DB-ADK consists of the following components:

1. **Database Layer**: SQLAlchemy models and repositories for database interactions
2. **Core Layer**: Dynamic agent and tool factories
3. **API Layer**: REST API and CLI interfaces
4. **Utils**: Logging and schema validation utilities

### Database Schema

The database schema includes the following tables:

- `agents`: Agent definitions (configurations, prompts, descriptions)
- `tools`: Tool definitions (functions, parameters, descriptions)
- `agent_tools`: Mapping between agents and tools
- `agent_relationships`: Relationships between agents (for multi-agent systems)

## Examples

### Multi-Agent Network Example

The package includes an example of a travel planning system with a coordinator agent and specialized agents for weather information and itinerary planning:

```bash
# Run the multi-agent network example
python -m db_adk.examples.multi_agent_network
```

This example demonstrates:
- Creating a coordinator agent
- Creating specialized agents
- Assigning tools to agents
- Setting up relationships between agents
- Running a multi-agent network

## API Reference

### REST API Endpoints

- `/agents/`: CRUD operations for agents
- `/tools/`: CRUD operations for tools
- `/agent-tools/`: Manage agent-tool mappings
- `/agent-relationships/`: Manage agent relationships
- `/agents/{agent_id}/run`: Run an agent
- `/networks/{coordinator_id}/run`: Run an agent network

### CLI Commands

- `db-adk db init`: Initialize the database
- `db-adk agents list`: List all agents
- `db-adk agents create`: Create a new agent
- `db-adk agents run`: Run an agent
- `db-adk tools list`: List all tools
- `db-adk tools create`: Create a new tool
- `db-adk agent-tools assign`: Assign a tool to an agent
- `db-adk agent-tools list`: List agent-tool mappings
- `db-adk relationships create`: Create a relationship between agents
- `db-adk networks run`: Run an agent network
- `db-adk serve`: Start the REST API server

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
