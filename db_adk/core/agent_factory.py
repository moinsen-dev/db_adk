"""
Factory for creating ADK agents from database records.

In the Agent Development Kit (ADK), an 'Agent' is a self-contained execution unit
designed to act autonomously to achieve specific goals. Agents can perform tasks,
interact with users, utilize external tools, and coordinate with other agents.

Core Agent Categories:
1. LLM Agents (LlmAgent, Agent): These agents utilize Large Language Models as their
   core engine to understand natural language, reason, plan, generate responses, and
   dynamically decide how to proceed or which tools to use.

2. Workflow Agents (SequentialAgent, ParallelAgent, LoopAgent): These specialized
   agents control the execution flow of other agents in predefined, deterministic
   patterns without using an LLM for the flow control itself.

3. Custom Agents: Created by extending BaseAgent directly, these agents allow you
   to implement unique operational logic, specific control flows, or specialized
   integrations not covered by the standard types.

The true power often comes from combining them in multi-agent systems where LLM agents
handle intelligent tasks, workflow agents manage process flow, and custom agents provide
specialized capabilities.
"""

import json

from ..db.models import Agent
from ..utils.logging import get_logger
from .tool_factory import load_tools_for_agent

# Initialize logger
logger = get_logger(__name__)


def get_agent_class(agent_type):
    """Get the ADK agent class based on agent type.

    Args:
        agent_type (str): The type of agent to create. Supported types:
            - 'LlmAgent': Language model agent that utilizes LLMs to understand natural language,
              reason, plan, and dynamically decide how to proceed or which tools to use.
            - 'Agent': Alternative LLM agent class with similar capabilities.
            - 'SequentialAgent': Workflow agent that executes sub-agents in a predefined sequence.
            - 'ParallelAgent': Workflow agent that executes multiple sub-agents concurrently.
            - 'LoopAgent': Workflow agent that repeatedly executes a sub-agent based on a condition.
            - 'BaseAgent': Base class for creating custom agents with unique operational logic.

    Returns:
        class: The agent class.

    Raises:
        ValueError: If the agent type is not supported.
    """
    try:
        # Import the Google ADK package
        import google.adk.agents as adk_agents

        # Map agent types to ADK agent classes
        agent_classes = {
            "LlmAgent": adk_agents.LlmAgent,  # Using LlmAgent instead of non-existent CoordinatorAgent
            "SequentialAgent": adk_agents.SequentialAgent,
            "ParallelAgent": adk_agents.ParallelAgent,
            "LoopAgent": adk_agents.LoopAgent,
            "Agent": adk_agents.Agent,
            "BaseAgent": adk_agents.BaseAgent,
        }

        if agent_type not in agent_classes:
            raise ValueError(f"Unsupported agent type: {agent_type}")

        return agent_classes[agent_type]
    except ImportError:
        logger.error("Failed to import Google ADK. Make sure it is installed.")
        raise


def create_agent_from_record(agent_id, db_session):
    """Create an ADK agent instance from a database record.

    Args:
        agent_id (int): The ID of the agent record.
        db_session: The database session.

    Returns:
        google.adk.agents.BaseAgent: The created agent instance.

    Raises:
        ValueError: If the agent record is not found.
    """
    # Fetch agent record
    agent_record = db_session.query(Agent).filter(Agent.id == agent_id).first()
    if not agent_record:
        raise ValueError(f"Agent with ID {agent_id} not found")

    logger.info(f"Creating agent from record: {agent_record.name} (ID: {agent_id})")

    # Determine agent class based on agent_type
    agent_class = get_agent_class(agent_record.agent_type)

    # Load tools for this agent
    tools = load_tools_for_agent(agent_id, db_session)

    # Parse configuration from JSON
    agent_kwargs = {}
    if agent_record.configuration:
        if isinstance(agent_record.configuration, str):
            agent_kwargs = json.loads(agent_record.configuration)
        else:
            agent_kwargs = agent_record.configuration

    # Set model if provided (maps from model_name to model for ADK v0.3.0)
    if agent_record.model_name:
        agent_kwargs["model"] = agent_record.model_name

    # Special handling for Coordinator agents
    # For Coordinator type, we load child agents and set them as sub_agents
    sub_agents = []
    if agent_record.agent_type == "Coordinator":
        for child_agent_record in agent_record.child_agents:
            # Avoid infinite recursion by checking if child is not the same as parent
            if child_agent_record.id != agent_id:
                child_agent = create_agent_from_record(
                    child_agent_record.id, db_session
                )
                sub_agents.append(child_agent)

        # Add sub_agents parameter for the LlmAgent being used as a coordinator
        if sub_agents:
            agent_kwargs["sub_agents"] = sub_agents
            logger.info(
                f"Added {len(sub_agents)} sub-agents to coordinator agent {agent_record.name}"
            )

    # Create agent instance with mapping prompt_template to instruction for ADK v0.3.0
    agent = agent_class(
        name=agent_record.name,
        description=agent_record.description,
        instruction=agent_record.prompt_template,
        tools=tools,
        **agent_kwargs,
    )

    logger.info(f"Successfully created agent: {agent_record.name}")

    return agent
