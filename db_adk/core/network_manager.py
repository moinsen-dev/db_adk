"""
Manager for creating and running agent networks.
"""

import asyncio
import json

from ..db.models import AgentRelationship
from ..utils.logging import get_logger
from .agent_factory import create_agent_from_record

# Initialize logger
logger = get_logger(__name__)


def create_agent_network(coordinator_agent_id, db_session):
    """Create a network of agents with a coordinator.

    Args:
        coordinator_agent_id (int): The ID of the coordinator agent.
        db_session: The database session.

    Returns:
        google.adk.agents.BaseAgent: The coordinator agent with child agents attached.

    Raises:
        ValueError: If the coordinator agent is not found or not a valid coordinator type.
    """
    # Create the coordinator agent
    coordinator = create_agent_from_record(coordinator_agent_id, db_session)

    logger.info(f"Creating agent network with coordinator: {coordinator.name}")

    # Check if the coordinator has appropriate methods for adding child agents
    if not hasattr(coordinator, "add_agent") and not hasattr(
        coordinator, "add_sequential_agent"
    ):
        raise ValueError(f"Agent {coordinator.name} is not a valid coordinator type")

    # Find all child agent relationships
    relationships = (
        db_session.query(AgentRelationship)
        .filter(AgentRelationship.parent_agent_id == coordinator_agent_id)
        .order_by(AgentRelationship.execution_order)
        .all()
    )

    logger.info(f"Found {len(relationships)} child agent relationships")

    # The coordinator was already created with sub_agents in agent_factory.py
    # No need to manually add child agents here

    return coordinator


def run_agent_network(coordinator_agent_id, input_data, db_session):
    """Create and run an agent network.

    Args:
        coordinator_agent_id (int): The ID of the coordinator agent.
        input_data (dict): The input data for the network.
        db_session: The database session.

    Returns:
        dict: The result of running the agent network.
    """
    # Create the agent network
    network = create_agent_network(coordinator_agent_id, db_session)

    # Run the network using run_async for ADK v0.3.0 compatibility
    logger.info(f"Running agent network with coordinator: {network.name}")

    # For ADK v0.3.0, convert input_data to a simple string if it's a dict
    if isinstance(input_data, dict):
        if "text" in input_data:
            query_text = input_data["text"]
        else:
            query_text = json.dumps(input_data)
    else:
        query_text = input_data

    # Handle the async generator returned by run_async
    async def collect_results():
        result = []
        async for resp in network.run_async(query_text):
            if resp:
                result.append(resp)
        return result[-1] if result else "No response from agent"

    # Run the async generator and collect the results
    result = asyncio.run(collect_results())

    logger.info("Agent network execution completed")

    return result
