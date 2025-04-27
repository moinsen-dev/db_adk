#!/usr/bin/env python3
"""
ADK v0.3.0 Agent Runner Example

This script demonstrates how to properly create and run agents with Google ADK v0.3.0.
It serves as a reference for updating the db_adk package to work with this ADK version.

The import_export/agent_types/ directory contains examples of JSON configurations for
different agent types (LlmAgent, Agent, SequentialAgent, ParallelAgent, LoopAgent, BaseAgent).
"""

import argparse
import json
import os
from typing import Any, Dict, List, Optional, Union, cast

# Ignore library stubs missing errors - these are external packages
from google.adk.agents import (  # type: ignore
    Agent,
    BaseAgent,
    LlmAgent,
    LoopAgent,
    ParallelAgent,
    SequentialAgent,
)
from google.adk.runners import Runner  # type: ignore
from google.adk.sessions import InMemorySessionService  # type: ignore
from google.genai import types  # type: ignore

# Direct import for configure to avoid linter error
try:
    from google.genai import configure  # type: ignore
except (ImportError, AttributeError):
    # Define fallback configure function in case it's not available
    def configure(api_key: str) -> None:
        """Fallback configure function."""
        print(f"Using API key: {api_key[:4]}...")


def setup_api_credentials():
    """Setup Google AI API credentials."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Please set it to your Google AI API key."
        )
    configure(api_key=api_key)
    print("API credentials configured")


def create_agent(
    name: str,
    instruction: str,
    model: Optional[str] = "gemini-1.5-pro",
    agent_type: str = "Agent",
    sub_agents: Optional[List[Union[Agent, LlmAgent, BaseAgent]]] = None,
    configuration: Optional[Dict[str, Any]] = None,
):
    """Create an agent with the given parameters.

    Args:
        name: Name of the agent
        instruction: Prompt template/instruction for the agent
        model: Model name to use (for LLM-based agents)
        agent_type: Type of agent to create (Agent, LlmAgent, SequentialAgent, etc.)
        sub_agents: List of sub-agents for workflow agents
        configuration: Additional configuration parameters

    Returns:
        An instance of the specified agent type
    """
    agent_kwargs: Dict[str, Any] = {
        "name": name,
        "instruction": instruction,
    }

    if model and agent_type in ["Agent", "LlmAgent", "BaseAgent"]:
        agent_kwargs["model"] = model

    if sub_agents and agent_type in ["SequentialAgent", "ParallelAgent", "LoopAgent"]:
        agent_kwargs["sub_agents"] = sub_agents

    if configuration:
        agent_kwargs.update(configuration)

    # Get the appropriate agent class based on type
    agent_classes = {
        "Agent": Agent,
        "LlmAgent": LlmAgent,
        "SequentialAgent": SequentialAgent,
        "ParallelAgent": ParallelAgent,
        "LoopAgent": LoopAgent,
        "BaseAgent": BaseAgent,
    }

    agent_class = agent_classes.get(agent_type, Agent)
    return agent_class(**agent_kwargs)


def call_agent(runner, query: str):
    """Run an agent with the given query text."""
    content = types.Content(role="user", parts=[types.Part(text=query)])

    print("Running agent, waiting for response...")

    events = runner.run(user_id="user123", session_id="sess123", new_message=content)

    responses = []
    for event in events:
        if event.is_final_response():
            response = event.content.parts[0].text
            responses.append(response)
            print("Response received!")

    return responses[0] if responses else "No response from agent"


def load_agent_from_example(example_file: str) -> Dict[str, Any]:
    """Load agent configuration from an example JSON file.

    Args:
        example_file: Path to the agent example JSON file

    Returns:
        Dictionary containing agent configuration
    """
    with open(example_file, "r") as f:
        example_data = json.load(f)

    agent_config = example_data.get("agent", {})
    return cast(Dict[str, Any], agent_config)


def main():
    parser = argparse.ArgumentParser(description="Run an agent using ADK v0.3.0")
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        required=True,
        help="The query text to send to the agent",
    )
    parser.add_argument(
        "--type",
        "-t",
        type=str,
        default="single",
        choices=[
            "single",
            "coordinator",
            "llm",
            "sequential",
            "parallel",
            "loop",
            "base",
        ],
        help="Type of agent to create (single, coordinator, llm, sequential, parallel, loop, base)",
    )
    parser.add_argument(
        "--example",
        "-e",
        type=str,
        help="Path to an example agent JSON file to load",
    )

    args = parser.parse_args()

    # Setup API credentials
    setup_api_credentials()

    # Handle loading from example file if provided
    if args.example:
        example_path = args.example
        print(f"Loading agent from example: {example_path}")
        agent_config = load_agent_from_example(example_path)

        # Use default type if not specified or None
        agent_type = agent_config.get("agent_type", "Agent")
        if agent_type is None:
            agent_type = "Agent"

        agent = create_agent(
            name=agent_config.get("name", "example_agent"),
            instruction=agent_config.get("prompt_template", ""),
            model=agent_config.get("model_name"),
            agent_type=agent_type,
            configuration=agent_config.get("configuration", {}),
        )

        print(f"Created {agent_type} agent: {agent_config.get('name')}")

    # Handle predefined agent types
    elif args.type == "coordinator":
        # Create sub-agents
        intake_agent = create_agent(
            name="intake_interviewer",
            instruction="You are an intake interviewer. Ask the user about their fitness goals, current activity level, schedule, preferences, and any limitations or injuries. Summarize the responses.",
        )

        medical_agent = create_agent(
            name="medical_assessor",
            instruction="You are a medical assessor for a fitness program. Review the user's medical history, current health status, age, injuries, and limitations to provide safe training recommendations and identify potential risks.",
        )

        # Create coordinator agent with sub-agents
        agent = create_agent(
            name="fitness_coordinator",
            instruction="You are a fitness coordinator agent. You orchestrate a network of agents: an intake interviewer, medical assessor, mental health specialist, workout planner, and nutrition planner. Collect user goals, assess health constraints, support mental wellbeing, and produce a comprehensive fitness plan.",
            sub_agents=[intake_agent, medical_agent],
        )

        print("Created coordinator agent with sub-agents")

    elif args.type == "llm":
        agent = create_agent(
            name="research_assistant",
            instruction="You are a research assistant specialized in finding, analyzing, and summarizing information. When asked about a topic, provide thorough and accurate information.",
            agent_type="LlmAgent",
        )

        print("Created LlmAgent")

    elif args.type == "sequential":
        # Create a simplified sequential agent for demo purposes
        sub_agent = create_agent(
            name="helper_agent",
            instruction="You are a helper agent for the sequential workflow.",
        )

        agent = create_agent(
            name="sequential_workflow",
            instruction="You are a sequential workflow agent that processes tasks in order.",
            agent_type="SequentialAgent",
            model=None,
            sub_agents=[sub_agent],
        )

        print("Created SequentialAgent with a sub-agent")

    elif args.type == "parallel":
        # Create a simplified parallel agent for demo purposes
        sub_agent1 = create_agent(
            name="helper_agent_1",
            instruction="You are the first helper agent for the parallel workflow.",
        )

        sub_agent2 = create_agent(
            name="helper_agent_2",
            instruction="You are the second helper agent for the parallel workflow.",
        )

        agent = create_agent(
            name="parallel_workflow",
            instruction="You are a parallel workflow agent that processes tasks concurrently.",
            agent_type="ParallelAgent",
            model=None,
            sub_agents=[sub_agent1, sub_agent2],
        )

        print("Created ParallelAgent with two sub-agents")

    elif args.type == "loop":
        # Create a simplified loop agent for demo purposes
        sub_agent = create_agent(
            name="repeating_agent",
            instruction="You are a repeating agent in a loop workflow.",
        )

        agent = create_agent(
            name="loop_workflow",
            instruction="You are a loop workflow agent that repeatedly processes a task.",
            agent_type="LoopAgent",
            model=None,
            sub_agents=[sub_agent],
            configuration={"max_iterations": 3},
        )

        print("Created LoopAgent with a repeating sub-agent")

    elif args.type == "base":
        # Create a basic agent using BaseAgent
        agent = create_agent(
            name="custom_agent",
            instruction="You are a custom agent built with BaseAgent.",
            agent_type="BaseAgent",
        )

        print("Created BaseAgent")

    else:  # default to single
        # Create a single agent
        agent = create_agent(
            name="fitness_assistant",
            instruction="You are a fitness assistant. Help users with fitness planning based on their age, flexibility, and other attributes.",
        )

        print("Created single Agent")

    # Set up session service
    session_service = InMemorySessionService()
    session_service.create_session(
        app_name="example_app", user_id="user123", session_id="sess123"
    )

    # Create runner
    runner = Runner(
        agent=agent, app_name="example_app", session_service=session_service
    )

    print(f"Running agent with query: {args.query}")
    response = call_agent(runner, args.query)

    # Print the response
    print("\nAgent response:")
    print(response)


if __name__ == "__main__":
    main()
