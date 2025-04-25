"""
Factory for creating ADK agents from database records.
"""

import json
import importlib
from ..db.models import Agent
from ..utils.logging import get_logger
from .tool_factory import load_tools_for_agent

# Initialize logger
logger = get_logger(__name__)

def get_agent_class(agent_type):
    """Get the ADK agent class based on agent type.
    
    Args:
        agent_type (str): The type of agent (e.g., 'LLM', 'Coordinator', 'Sequential').
        
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
            'LLM': adk_agents.LlmAgent,
            'Coordinator': adk_agents.CoordinatorAgent,
            'Sequential': adk_agents.SequentialAgent,
            'Parallel': adk_agents.ParallelAgent,
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
    
    # Set model_name if provided
    if agent_record.model_name:
        agent_kwargs['model_name'] = agent_record.model_name
    
    # Create agent instance
    agent = agent_class(
        name=agent_record.name,
        description=agent_record.description,
        prompt_template=agent_record.prompt_template,
        tools=tools,
        **agent_kwargs
    )
    
    logger.info(f"Successfully created agent: {agent_record.name}")
    
    return agent
