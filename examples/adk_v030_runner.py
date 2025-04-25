#!/usr/bin/env python3
"""
ADK v0.3.0 Agent Runner Example

This script demonstrates how to properly create and run agents with Google ADK v0.3.0.
It serves as a reference for updating the db_adk package to work with this ADK version.
"""

import argparse
import os
from typing import List, Optional

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import configure, types


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
    model: str = "gemini-1.5-pro",
    sub_agents: Optional[List] = None,
):
    """Create an agent with the given parameters."""
    agent_kwargs = {
        "name": name,
        "instruction": instruction,
        "model": model,
    }

    if sub_agents:
        agent_kwargs["sub_agents"] = sub_agents

    return Agent(**agent_kwargs)


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
        choices=["single", "coordinator"],
        help="Type of agent to create (single or coordinator with sub-agents)",
    )

    args = parser.parse_args()

    # Setup API credentials
    setup_api_credentials()

    print(
        f"Creating {'coordinator' if args.type == 'coordinator' else 'single'} agent..."
    )

    if args.type == "coordinator":
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
    else:
        # Create a single agent
        agent = create_agent(
            name="fitness_assistant",
            instruction="You are a fitness assistant. Help users with fitness planning based on their age, flexibility, and other attributes.",
        )

    # Set up session service
    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name="fitness_app", user_id="user123", session_id="sess123"
    )

    # Create runner
    runner = Runner(
        agent=agent, app_name="fitness_app", session_service=session_service
    )

    print(f"Running agent with query: {args.query}")
    response = call_agent(runner, args.query)

    # Print the response
    print("\nAgent response:")
    print(response)


if __name__ == "__main__":
    main()
