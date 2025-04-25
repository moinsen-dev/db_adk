"""
Manager for creating and running agent networks.
"""

from ..db.models import AgentRelationship
from .agent_factory import create_agent_from_record
from ..utils.logging import get_logger

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
    if not hasattr(coordinator, 'add_agent') and not hasattr(coordinator, 'add_sequential_agent'):
        raise ValueError(f"Agent {coordinator.name} is not a valid coordinator type")
    
    # Find all child agent relationships
    relationships = db_session.query(AgentRelationship).filter(
        AgentRelationship.parent_agent_id == coordinator_agent_id
    ).order_by(AgentRelationship.execution_order).all()
    
    logger.info(f"Found {len(relationships)} child agent relationships")
    
    # Create and add child agents
    for rel in relationships:
        try:
            child_agent = create_agent_from_record(rel.child_agent_id, db_session)
            
            # Add child to coordinator based on relationship type
            if rel.relationship_type == "sequential":
                if hasattr(coordinator, 'add_sequential_agent'):
                    coordinator.add_sequential_agent(child_agent)
                    logger.info(f"Added sequential agent {child_agent.name} (order: {rel.execution_order})")
                else:
                    coordinator.add_agent(child_agent)
                    logger.info(f"Added agent {child_agent.name} (no sequential support)")
            elif rel.relationship_type == "parallel":
                if hasattr(coordinator, 'add_parallel_agent'):
                    coordinator.add_parallel_agent(child_agent)
                    logger.info(f"Added parallel agent {child_agent.name}")
                else:
                    coordinator.add_agent(child_agent)
                    logger.info(f"Added agent {child_agent.name} (no parallel support)")
            else:
                # Default to generic add_agent method
                coordinator.add_agent(child_agent)
                logger.info(f"Added agent {child_agent.name} with relationship type: {rel.relationship_type}")
        except Exception as e:
            logger.error(f"Failed to add child agent ID {rel.child_agent_id}: {str(e)}")
    
    logger.info(f"Successfully created agent network with coordinator: {coordinator.name}")
    
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
    
    # Run the network
    logger.info(f"Running agent network with coordinator: {network.name}")
    result = network.run(input_data)
    logger.info(f"Agent network execution completed")
    
    return result
