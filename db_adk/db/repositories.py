"""
Repository classes for database operations.
"""

from .models import Agent, Tool, AgentTool, AgentRelationship
from .connection import get_db_session

class AgentRepository:
    """Repository for Agent operations."""
    
    @staticmethod
    def get_by_id(agent_id):
        """Get an agent by ID.
        
        Args:
            agent_id (int): The ID of the agent.
            
        Returns:
            Agent: The agent with the given ID, or None if not found.
        """
        with get_db_session() as session:
            return session.query(Agent).filter(Agent.id == agent_id).first()
    
    @staticmethod
    def get_all():
        """Get all agents.
        
        Returns:
            list[Agent]: A list of all agents.
        """
        with get_db_session() as session:
            return session.query(Agent).all()
    
    @staticmethod
    def create(agent_data):
        """Create a new agent.
        
        Args:
            agent_data (dict): The agent data.
            
        Returns:
            Agent: The created agent.
        """
        with get_db_session() as session:
            agent = Agent(**agent_data)
            session.add(agent)
            session.commit()
            session.refresh(agent)
            return agent
    
    @staticmethod
    def update(agent_id, agent_data):
        """Update an agent.
        
        Args:
            agent_id (int): The ID of the agent to update.
            agent_data (dict): The updated agent data.
            
        Returns:
            Agent: The updated agent, or None if not found.
        """
        with get_db_session() as session:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                for key, value in agent_data.items():
                    setattr(agent, key, value)
                session.commit()
                session.refresh(agent)
            return agent
    
    @staticmethod
    def delete(agent_id):
        """Delete an agent.
        
        Args:
            agent_id (int): The ID of the agent to delete.
            
        Returns:
            bool: True if the agent was deleted, False if not found.
        """
        with get_db_session() as session:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                session.delete(agent)
                session.commit()
                return True
            return False


class ToolRepository:
    """Repository for Tool operations."""
    
    @staticmethod
    def get_by_id(tool_id):
        """Get a tool by ID."""
        with get_db_session() as session:
            return session.query(Tool).filter(Tool.id == tool_id).first()
    
    @staticmethod
    def get_all():
        """Get all tools."""
        with get_db_session() as session:
            return session.query(Tool).all()
    
    @staticmethod
    def create(tool_data):
        """Create a new tool."""
        with get_db_session() as session:
            tool = Tool(**tool_data)
            session.add(tool)
            session.commit()
            session.refresh(tool)
            return tool
    
    @staticmethod
    def update(tool_id, tool_data):
        """Update a tool."""
        with get_db_session() as session:
            tool = session.query(Tool).filter(Tool.id == tool_id).first()
            if tool:
                for key, value in tool_data.items():
                    setattr(tool, key, value)
                session.commit()
                session.refresh(tool)
            return tool
    
    @staticmethod
    def delete(tool_id):
        """Delete a tool."""
        with get_db_session() as session:
            tool = session.query(Tool).filter(Tool.id == tool_id).first()
            if tool:
                session.delete(tool)
                session.commit()
                return True
            return False


class AgentToolRepository:
    """Repository for AgentTool operations."""
    
    @staticmethod
    def get_tools_for_agent(agent_id):
        """Get all tools for an agent."""
        with get_db_session() as session:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                return agent.tools
            return []
    
    @staticmethod
    def get_agents_for_tool(tool_id):
        """Get all agents for a tool."""
        with get_db_session() as session:
            tool = session.query(Tool).filter(Tool.id == tool_id).first()
            if tool:
                return tool.agents
            return []
    
    @staticmethod
    def assign_tool_to_agent(agent_id, tool_id):
        """Assign a tool to an agent."""
        with get_db_session() as session:
            existing = session.query(AgentTool).filter(
                AgentTool.agent_id == agent_id,
                AgentTool.tool_id == tool_id
            ).first()
            
            if not existing:
                mapping = AgentTool(agent_id=agent_id, tool_id=tool_id)
                session.add(mapping)
                session.commit()
                return True
            return False
    
    @staticmethod
    def unassign_tool_from_agent(agent_id, tool_id):
        """Unassign a tool from an agent."""
        with get_db_session() as session:
            mapping = session.query(AgentTool).filter(
                AgentTool.agent_id == agent_id,
                AgentTool.tool_id == tool_id
            ).first()
            
            if mapping:
                session.delete(mapping)
                session.commit()
                return True
            return False


class AgentRelationshipRepository:
    """Repository for AgentRelationship operations."""
    
    @staticmethod
    def get_child_agents(parent_agent_id):
        """Get all child agents for a parent agent."""
        with get_db_session() as session:
            parent = session.query(Agent).filter(Agent.id == parent_agent_id).first()
            if parent:
                return parent.child_agents
            return []
    
    @staticmethod
    def get_parent_agents(child_agent_id):
        """Get all parent agents for a child agent."""
        with get_db_session() as session:
            child = session.query(Agent).filter(Agent.id == child_agent_id).first()
            if child:
                return child.parent_agents
            return []
    
    @staticmethod
    def create_relationship(parent_id, child_id, relationship_type, execution_order=0):
        """Create a relationship between two agents."""
        with get_db_session() as session:
            existing = session.query(AgentRelationship).filter(
                AgentRelationship.parent_agent_id == parent_id,
                AgentRelationship.child_agent_id == child_id
            ).first()
            
            if not existing:
                relationship = AgentRelationship(
                    parent_agent_id=parent_id,
                    child_agent_id=child_id,
                    relationship_type=relationship_type,
                    execution_order=execution_order
                )
                session.add(relationship)
                session.commit()
                return True
            return False
    
    @staticmethod
    def delete_relationship(parent_id, child_id):
        """Delete a relationship between two agents."""
        with get_db_session() as session:
            relationship = session.query(AgentRelationship).filter(
                AgentRelationship.parent_agent_id == parent_id,
                AgentRelationship.child_agent_id == child_id
            ).first()
            
            if relationship:
                session.delete(relationship)
                session.commit()
                return True
            return False
