# ADK Import/Export Examples

This directory contains examples of agent configurations in JSON format that can be imported into the ADK system.

## Agent Type Examples

The `agent_types` directory contains examples for each of the agent types supported by the ADK:

1. **LlmAgent** - Language model agent that uses LLMs to understand natural language, reason, plan, and dynamically decide how to proceed or which tools to use.
2. **Agent** - Alternative LLM agent class with similar capabilities.
3. **SequentialAgent** - Workflow agent that executes sub-agents in a predefined sequence.
4. **ParallelAgent** - Workflow agent that executes multiple sub-agents concurrently.
5. **LoopAgent** - Workflow agent that repeatedly executes a sub-agent based on a condition.
6. **BaseAgent** - Base class for creating custom agents with unique operational logic.

These examples demonstrate the JSON structure required for each agent type and can be used as templates for creating your own agents.

## Domain-Specific Examples

In addition to the agent type examples, this directory contains domain-specific multi-agent system examples:

- `fitness_training/` - A set of coordinated agents for fitness planning and health assessment
- `travel_guidelines/` - A system of agents for travel planning and assistance

## Usage

To use these examples:

1. Import the JSON configuration into your ADK application
2. Create agent instances from the imported configuration
3. Customize the configurations as needed for your specific use case

See the `adk_v030_runner.py` script in the parent directory for an example of how to load and run agents from these configurations.