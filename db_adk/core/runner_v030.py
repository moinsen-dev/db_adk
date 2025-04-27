"""
ADK v0.3.0 Compatible Runner

This module provides compatibility with Google ADK v0.3.0 by implementing
runner functionality that matches the new API requirements.
"""

import json
import os
from typing import Any, Dict, List, Union

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from ..utils.logging import get_logger
from .agent_factory import create_agent_from_record

# Initialize logger
logger = get_logger(__name__)


def setup_api_credentials():
    """Setup Google AI API credentials from environment variables or dotenv."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        # Try loading from .env file if python-dotenv is available
        try:
            from dotenv import load_dotenv

            load_dotenv()
            api_key = os.environ.get("GOOGLE_API_KEY")
        except ImportError:
            logger.warning("python-dotenv not installed, cannot load from .env file")

    if not api_key:
        logger.warning("GOOGLE_API_KEY environment variable not set")
        return False

    # No need to call configure - the Client will use API_KEY from env
    logger.info("Google AI API credentials found in environment")
    return True


def setup_runner(
    agent, user_id="user123", session_id="session123", app_name="db_adk_app"
):
    """Set up a v0.3.0 compatible Runner with an InMemorySessionService.

    Args:
        agent: The ADK agent instance
        user_id: User identifier (default: 'user123')
        session_id: Session identifier (default: 'session123')
        app_name: Application name (default: 'db_adk_app')

    Returns:
        tuple: (runner, session_service) containing the configured Runner and SessionService
    """
    # Setup API credentials first - ensure API_KEY exists
    setup_api_credentials()

    # Create session service and initialize session
    session_service = InMemorySessionService()
    session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )

    # Create runner
    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)

    return runner, session_service


def create_content_message(input_data: Union[str, Dict[str, Any]]) -> types.Content:
    """Convert input data to a v0.3.0 compatible Content message.

    Args:
        input_data: Either a string query or a dictionary of data

    Returns:
        types.Content: Formatted content message for ADK v0.3.0
    """
    # Convert input_data to a string if it's a dictionary
    if isinstance(input_data, dict):
        if "text" in input_data:
            query_text = input_data["text"]
        else:
            query_text = json.dumps(input_data)
    else:
        query_text = input_data

    # Create content message with user role
    return types.Content(role="user", parts=[types.Part(text=query_text)])


def extract_response_from_events(events) -> List[str]:
    """Extract text responses from runner events.

    Args:
        events: Iterator of events from runner.run()

    Returns:
        List[str]: List of text responses extracted from events
    """
    responses = []
    for event in events:
        if event.is_final_response() and event.content is not None:
            if hasattr(event.content, "parts") and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        responses.append(part.text)

    return responses


def run_agent_with_runner(
    agent_id: int,
    input_data: Union[str, Dict[str, Any]],
    db_session,
    user_id: str = "user123",
    session_id: str = "session123",
    verbose: bool = True,
):
    """Run an agent using the v0.3.0 Runner API.

    Args:
        agent_id: ID of the agent to run
        input_data: Input data (string or dictionary)
        db_session: Database session
        user_id: User identifier (default: 'user123')
        session_id: Session identifier (default: 'session123')
        verbose: Whether to log detailed progress information (default: True)

    Returns:
        str: Agent response
    """
    # Setup API credentials first
    credential_setup = setup_api_credentials()
    if not credential_setup:
        return (
            "Error: Google API credentials not configured. "
            "Please set GOOGLE_API_KEY environment variable."
        )

    # Create agent from database record
    agent = create_agent_from_record(agent_id, db_session)

    # Check if this is a coordinator agent with sub-agents
    is_coordinator = hasattr(agent, "sub_agents") and agent.sub_agents
    sub_agent_names = []
    if is_coordinator and verbose:
        sub_agent_names = [sub_agent.name for sub_agent in agent.sub_agents]
        logger.info(
            f"Coordinator agent {agent.name} has {len(agent.sub_agents)} sub-agents: {', '.join(sub_agent_names)}"
        )

    # Set up runner
    runner, _ = setup_runner(agent, user_id, session_id)

    # Create message
    content = create_content_message(input_data)

    logger.info(f"Running agent {agent.name} with v0.3.0 runner")

    # For tracking sub-agent activities
    active_agents = set()
    last_agent = None

    # Run the agent using the runner
    events = runner.run(user_id=user_id, session_id=session_id, new_message=content)

    # Process events to extract responses and track sub-agent activities
    responses = []

    # Check if the iterator is actually returning events
    if hasattr(events, "__iter__"):
        for event in events:
            # Extract agent activity information if available
            if hasattr(event, "agent_name") and event.agent_name:
                if event.agent_name != last_agent:
                    if verbose:
                        logger.info(f"Sub-agent active: {event.agent_name}")
                    active_agents.add(event.agent_name)
                    last_agent = event.agent_name

            # Process final responses
            if (
                hasattr(event, "is_final_response")
                and event.is_final_response()
                and event.content is not None
            ):
                if hasattr(event.content, "parts") and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            responses.append(part.text)

    # Log which sub-agents were involved
    if is_coordinator and verbose:
        if active_agents:
            logger.info(
                f"Sub-agents involved in processing: {', '.join(active_agents)}"
            )
            # Check if any sub-agents were not used
            unused_agents = set(sub_agent_names) - active_agents
            if unused_agents:
                logger.warning(
                    f"Sub-agents not involved in processing: {', '.join(unused_agents)}"
                )
        else:
            logger.warning(
                f"No sub-agent activity detected from coordinator {agent.name}"
            )

    logger.info("Agent execution completed")

    return responses[0] if responses else "No response from agent"


def run_network_with_runner(
    coordinator_agent_id: int,
    input_data: Union[str, Dict[str, Any]],
    db_session,
    user_id: str = "user123",
    session_id: str = "session123",
    verbose: bool = True,
):
    """Run an agent network using the v0.3.0 Runner API.

    Args:
        coordinator_agent_id: ID of the coordinator agent
        input_data: Input data (string or dictionary)
        db_session: Database session
        user_id: User identifier (default: 'user123')
        session_id: Session identifier (default: 'session123')
        verbose: Whether to log detailed progress information (default: True)

    Returns:
        str: Network response
    """
    # This function is identical to run_agent_with_runner
    # since the v0.3.0 API handles sub-agents automatically through the Runner
    return run_agent_with_runner(
        agent_id=coordinator_agent_id,
        input_data=input_data,
        db_session=db_session,
        user_id=user_id,
        session_id=session_id,
        verbose=verbose,
    )
