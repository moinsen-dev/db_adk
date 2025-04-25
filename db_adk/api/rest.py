"""
FastAPI REST interface for DB-ADK.
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ..db.connection import get_db_session
from ..db.models import Agent, Tool, AgentTool, AgentRelationship
from ..core.agent_factory import create_agent_from_record
from ..core.network_manager import create_agent_network, run_agent_network
from ..utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(title="DB-ADK API", description="Database-driven Agent Development Kit API")

# Pydantic models for request/response
class AgentCreate(BaseModel):
    """Model for creating an agent."""
    name: str
    description: str
    agent_type: str
    prompt_template: Optional[str] = None
    model_name: Optional[str] = None
    configuration: Dict[str, Any] = {}

class AgentResponse(BaseModel):
    """Model for agent response."""
    id: int
    name: str
    description: str
    agent_type: str
    prompt_template: Optional[str]
    model_name: Optional[str]
    configuration: Dict[str, Any]
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True

class ToolCreate(BaseModel):
    """Model for creating a tool."""
    name: str
    description: str
    tool_type: str
    module_path: str
    function_name: str
    parameters_schema: Dict[str, Any] = {}

class ToolResponse(BaseModel):
    """Model for tool response."""
    id: int
    name: str
    description: str
    tool_type: str
    module_path: str
    function_name: str
    parameters_schema: Dict[str, Any]
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True

class AgentToolCreate(BaseModel):
    """Model for creating an agent-tool mapping."""
    agent_id: int
    tool_id: int

class RelationshipCreate(BaseModel):
    """Model for creating an agent relationship."""
    parent_agent_id: int
    child_agent_id: int
    relationship_type: str
    execution_order: int = 0

# Routes for Agents
@app.post("/agents/", response_model=AgentResponse)
def create_agent(agent: AgentCreate):
    """Create a new agent."""
    try:
        with get_db_session() as session:
            db_agent = Agent(**agent.dict())
            session.add(db_agent)
            session.commit()
            session.refresh(db_agent)
            logger.info(f"Created agent: {db_agent.name} (ID: {db_agent.id})")
            return db_agent
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/", response_model=List[AgentResponse])
def read_agents():
    """Get all agents."""
    try:
        with get_db_session() as session:
            agents = session.query(Agent).all()
            return agents
    except Exception as e:
        logger.error(f"Error retrieving agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/{agent_id}", response_model=AgentResponse)
def read_agent(agent_id: int):
    """Get an agent by ID."""
    try:
        with get_db_session() as session:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            if agent is None:
                raise HTTPException(status_code=404, detail="Agent not found")
            return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/agents/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: int, agent: AgentCreate):
    """Update an agent."""
    try:
        with get_db_session() as session:
            db_agent = session.query(Agent).filter(Agent.id == agent_id).first()
            if db_agent is None:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            # Update fields
            for key, value in agent.dict().items():
                setattr(db_agent, key, value)
            
            session.commit()
            session.refresh(db_agent)
            logger.info(f"Updated agent: {db_agent.name} (ID: {db_agent.id})")
            return db_agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/agents/{agent_id}")
def delete_agent(agent_id: int):
    """Delete an agent."""
    try:
        with get_db_session() as session:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            if agent is None:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            session.delete(agent)
            session.commit()
            logger.info(f"Deleted agent ID: {agent_id}")
            return {"message": f"Agent {agent_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/{agent_id}/run")
def run_agent(agent_id: int, input_data: Dict[str, Any]):
    """Run an agent with given input."""
    try:
        with get_db_session() as session:
            # Create agent from database record
            agent = create_agent_from_record(agent_id, session)
            
            # Run the agent
            logger.info(f"Running agent: {agent.name} (ID: {agent_id})")
            result = agent.run(input_data)
            logger.info(f"Agent execution completed")
            
            return {"result": result}
    except Exception as e:
        logger.error(f"Error running agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Routes for Tools
@app.post("/tools/", response_model=ToolResponse)
def create_tool(tool: ToolCreate):
    """Create a new tool."""
    try:
        with get_db_session() as session:
            db_tool = Tool(**tool.dict())
            session.add(db_tool)
            session.commit()
            session.refresh(db_tool)
            logger.info(f"Created tool: {db_tool.name} (ID: {db_tool.id})")
            return db_tool
    except Exception as e:
        logger.error(f"Error creating tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/", response_model=List[ToolResponse])
def read_tools():
    """Get all tools."""
    try:
        with get_db_session() as session:
            tools = session.query(Tool).all()
            return tools
    except Exception as e:
        logger.error(f"Error retrieving tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Routes for Agent-Tool mappings
@app.post("/agent-tools/")
def create_agent_tool_mapping(mapping: AgentToolCreate):
    """Create an agent-tool mapping."""
    try:
        with get_db_session() as session:
            # Check if mapping already exists
            existing = session.query(AgentTool).filter(
                AgentTool.agent_id == mapping.agent_id,
                AgentTool.tool_id == mapping.tool_id
            ).first()
            
            if existing:
                return {"message": "Mapping already exists"}
            
            # Create new mapping
            db_mapping = AgentTool(**mapping.dict())
            session.add(db_mapping)
            session.commit()
            logger.info(f"Created agent-tool mapping: Agent ID {mapping.agent_id} - Tool ID {mapping.tool_id}")
            
            return {"message": "Mapping created successfully", "id": db_mapping.id}
    except Exception as e:
        logger.error(f"Error creating agent-tool mapping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Routes for Agent Relationships
@app.post("/agent-relationships/")
def create_agent_relationship(relationship: RelationshipCreate):
    """Create an agent relationship."""
    try:
        with get_db_session() as session:
            # Check if relationship already exists
            existing = session.query(AgentRelationship).filter(
                AgentRelationship.parent_agent_id == relationship.parent_agent_id,
                AgentRelationship.child_agent_id == relationship.child_agent_id
            ).first()
            
            if existing:
                return {"message": "Relationship already exists"}
            
            # Create new relationship
            db_relationship = AgentRelationship(**relationship.dict())
            session.add(db_relationship)
            session.commit()
            logger.info(f"Created agent relationship: Parent ID {relationship.parent_agent_id} - "
                       f"Child ID {relationship.child_agent_id} - Type {relationship.relationship_type}")
            
            return {"message": "Relationship created successfully", "id": db_relationship.id}
    except Exception as e:
        logger.error(f"Error creating agent relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Routes for Agent Networks
@app.post("/networks/{coordinator_id}/run")
def run_network_endpoint(coordinator_id: int, input_data: Dict[str, Any]):
    """Run an agent network with given input."""
    try:
        with get_db_session() as session:
            # Run the network
            result = run_agent_network(coordinator_id, input_data, session)
            
            return {"result": result}
    except Exception as e:
        logger.error(f"Error running agent network with coordinator {coordinator_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def start_server(host="0.0.0.0", port=8000):
    """Start the FastAPI server.
    
    Args:
        host (str): The host to bind to.
        port (int): The port to bind to.
    """
    logger.info(f"Starting DB-ADK API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
