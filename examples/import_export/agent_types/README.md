# Agent Type Examples

This directory contains JSON examples for the different agent types supported by the ADK (Agent Development Kit). These examples demonstrate the structure and configuration for each type of agent.

## Available Agent Types

1. **LlmAgent** (`llm_agent_example.json`)
   - An intelligent agent that uses Large Language Models to understand natural language, reason, plan, and dynamically decide actions.
   - Example: Research assistant that helps find, summarize, and analyze information.

2. **Agent** (`agent_example.json`)
   - Alternative LLM agent class with similar capabilities to LlmAgent.
   - Example: Customer support agent that handles product inquiries and troubleshooting.

3. **SequentialAgent** (`sequential_agent_example.json`)
   - Workflow agent that executes sub-agents in a predefined sequence.
   - Example: Content production pipeline that manages the flow from research to publishing.

4. **ParallelAgent** (`parallel_agent_example.json`)
   - Workflow agent that executes multiple sub-agents concurrently.
   - Example: Data analytics system that performs multiple analysis tasks in parallel.

5. **LoopAgent** (`loop_agent_example.json`)
   - Workflow agent that repeatedly executes a sub-agent based on a condition.
   - Example: Iterative code optimizer that improves code until quality standards are met.

6. **BaseAgent** (`base_agent_example.json`)
   - Base class for creating custom agents with unique operational logic.
   - Example: Custom database agent with specialized database connection capabilities.

## JSON Structure

Each example follows this general structure:

```json
{
  "schema_version": "1.0",
  "export_date": "YYYY-MM-DDT00:00:00Z",
  "agent": {
    "name": "agent_name",
    "description": "Agent description",
    "agent_type": "AgentType",
    "prompt_template": "Agent instructions",
    "model_name": "model_name",
    "configuration": {}
  },
  "tools": [],             // For LLM-based agents
  "relationships": [],     // For workflow agents
  "sub_agents": []         // For workflow agents
}
```

## Usage

These examples can be used as templates for creating your own agents by modifying the configurations to suit your specific use cases. Import them into your ADK application using the appropriate import functions.