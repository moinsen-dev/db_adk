# ADK Examples

This directory contains examples and reference implementations for the Agent Development Kit (ADK).

## Contents

- `adk_v030_runner.py` - A script that demonstrates how to properly create and run agents with Google ADK v0.3.0. It shows how to set up API credentials, create various agent types, and execute queries.

- `import_export/` - Directory containing example agent configurations in JSON format:
  - `agent_types/` - Example implementations for each ADK agent type
  - `fitness_training/` - Domain-specific multi-agent system for fitness planning
  - `travel_guidelines/` - Domain-specific multi-agent system for travel planning

## ADK Agent Types

The Agent Development Kit supports several agent types, each designed for different use cases:

1. **LlmAgent** - Language model agent that uses LLMs to understand natural language, reason, plan, and dynamically decide how to proceed or which tools to use.

2. **Agent** - Alternative LLM agent class with similar capabilities to LlmAgent.

3. **SequentialAgent** - Workflow agent that executes sub-agents in a predefined sequence.

4. **ParallelAgent** - Workflow agent that executes multiple sub-agents concurrently.

5. **LoopAgent** - Workflow agent that repeatedly executes a sub-agent based on a condition.

6. **BaseAgent** - Base class for creating custom agents with unique operational logic.

## Running the Examples

To run the `adk_v030_runner.py` example:

```bash
# Set your Google API key
export GOOGLE_API_KEY="your_api_key_here"

# Run with a basic query
python adk_v030_runner.py --query "What's a good workout routine for beginners?"

# Try different agent types
python adk_v030_runner.py --type llm --query "Explain the benefits of strength training"
python adk_v030_runner.py --type sequential --query "Create a weekly workout plan"

# Load from an example file
python adk_v030_runner.py --example import_export/agent_types/llm_agent_example.json --query "What are the health benefits of regular exercise?"
```

## Using the Examples as Templates

These examples can be used as templates for creating your own agents by:

1. Understanding the structure of agent configurations
2. Copying and modifying the JSON examples to fit your use case
3. Using the `create_agent_from_record` function in `db_adk/core/agent_factory.py` to create agents from your configurations

Refer to each example's documentation for specific details on how to adapt it for your needs.