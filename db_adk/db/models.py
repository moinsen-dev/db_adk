"""
SQLAlchemy models for DB-ADK.
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Agent(Base):
    """Agent model representing an ADK agent configuration."""

    __tablename__ = "agents"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    agent_type = Column(
        String(50), nullable=False
    )  # Valid types: LLM, Coordinator (uses LlmAgent), Sequential, Parallel
    prompt_template = Column(Text)
    model_name = Column(String(100))
    configuration = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tools = relationship("Tool", secondary="agent_tools", back_populates="agents")
    child_agents = relationship(
        "Agent",
        secondary="agent_relationships",
        primaryjoin="Agent.id==AgentRelationship.parent_agent_id",
        secondaryjoin="Agent.id==AgentRelationship.child_agent_id",
        backref="parent_agents",
    )


class Tool(Base):
    """Tool model representing a tool that can be used by agents."""

    __tablename__ = "tools"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    tool_type = Column(String(50), nullable=False)  # Python function, API, etc.
    module_path = Column(String(255), nullable=False)
    function_name = Column(String(100), nullable=False)
    parameters_schema = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agents = relationship("Agent", secondary="agent_tools", back_populates="tools")


class AgentTool(Base):
    """Association table for agent-tool relationships."""

    __tablename__ = "agent_tools"

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentRelationship(Base):
    """Association table for agent-agent relationships."""

    __tablename__ = "agent_relationships"

    id = Column(Integer, primary_key=True)
    parent_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    child_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    relationship_type = Column(
        String(50), nullable=False
    )  # sequential, orchestrator, etc.
    execution_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
