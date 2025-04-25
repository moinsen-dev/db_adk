"""
FastAPI REST interface for DB-ADK.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ..db.connection import get_db_session
from ..db.models import Agent, AgentRelationship, AgentTool, Tool
from ..import_export import ImportOptions, export_agent, export_all_agents, import_agent
from ..utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DB-ADK API", description="Database-driven Agent Development Kit API"
)


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
    description: Optional[str] = None
    agent_type: str
    prompt_template: Optional[str] = None
    model_name: Optional[str] = None
    configuration: Dict[str, Any] = {}

    class Config:
        from_attributes = True


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
    description: Optional[str] = None
    tool_type: str
    module_path: str
    function_name: str
    parameters_schema: Dict[str, Any] = {}

    class Config:
        from_attributes = True


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


class ImportOptionsModel(BaseModel):
    """Model for import options."""

    use_existing_tools: bool = True
    overwrite_existing_agent: bool = False
    ignore_missing_relationships: bool = True
    defer_relationships: bool = True


class ExportOptionsModel(BaseModel):
    """Model for export options."""

    format: str = "json"
    include_tools: bool = True
    include_relationships: bool = True


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
            # Always use the v0.3.0 compatible runner
            from ..core.runner_v030 import run_agent_with_runner

            logger.info(f"Running agent {agent_id} with v0.3.0 compatible runner")
            result = run_agent_with_runner(agent_id, input_data, session)

            logger.info("Agent execution completed")
            return {"result": result}
    except Exception as e:
        logger.error(f"Error running agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_id}/export")
def export_agent_endpoint(agent_id: int, options: ExportOptionsModel):
    """
    Export an agent to a file.

    Returns the exported agent data directly in the response.
    """
    try:
        # Create a temporary file to store the export
        with tempfile.NamedTemporaryFile(
            suffix=f".{options.format}", delete=False
        ) as temp_file:
            temp_path = temp_file.name

        # Export the agent
        export_agent(
            agent_id=agent_id,
            output_file=temp_path,
            format_name=options.format,
            include_tools=options.include_tools,
            include_relationships=options.include_relationships,
        )

        # Read the exported file and return as response
        with open(temp_path, "r") as f:
            content = f.read()

        # Clean up temporary file
        os.unlink(temp_path)

        # Determine content type
        content_type = (
            "application/json" if options.format == "json" else "application/yaml"
        )

        # Return the exported content
        return {
            "format": options.format,
            "content": content,
            "agent_id": agent_id,
            "content_type": content_type,
        }
    except Exception as e:
        logger.error(f"Error exporting agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/export-all")
def export_all_agents_endpoint(
    options: ExportOptionsModel, background_tasks: BackgroundTasks
):
    """
    Export all agents to files in a temporary directory and provide download links.
    """
    try:
        # Create a temporary directory to store exports
        temp_dir = tempfile.mkdtemp()

        # Export all agents
        export_files = export_all_agents(
            output_dir=temp_dir,
            format_name=options.format,
            include_tools=options.include_tools,
            include_relationships=options.include_relationships,
        )

        # Extract file names and create download information
        downloads = []
        for file_path in export_files:
            path = Path(file_path)
            agent_name = path.stem
            downloads.append(
                {
                    "agent_name": agent_name,
                    "file_name": path.name,
                    "format": options.format,
                }
            )

        # Schedule cleanup after some time (e.g., 1 hour)
        def cleanup_temp_dir():
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

        background_tasks.add_task(cleanup_temp_dir)

        return {
            "export_dir": temp_dir,
            "exports": downloads,
            "format": options.format,
            "count": len(downloads),
        }
    except Exception as e:
        logger.error(f"Error exporting all agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/import")
async def import_agent_endpoint(
    file: UploadFile = File(...), options_json: str = Form(...)
):
    """
    Import an agent from an uploaded file.
    """
    try:
        import json

        # Parse import options
        options_data = json.loads(options_json)
        import_options = ImportOptions(
            use_existing_tools=options_data.get("use_existing_tools", True),
            overwrite_existing_agent=options_data.get(
                "overwrite_existing_agent", False
            ),
            ignore_missing_relationships=options_data.get(
                "ignore_missing_relationships", True
            ),
        )

        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            content = await file.read()
            temp_file.write(content)

        # Import the agent
        agent_id = import_agent(file_path=temp_path, options=import_options)

        # Clean up temporary file
        os.unlink(temp_path)

        # Return the imported agent ID
        return {"message": "Agent imported successfully", "agent_id": agent_id}
    except Exception as e:
        logger.error(f"Error importing agent: {str(e)}")
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
            existing = (
                session.query(AgentTool)
                .filter(
                    AgentTool.agent_id == mapping.agent_id,
                    AgentTool.tool_id == mapping.tool_id,
                )
                .first()
            )

            if existing:
                return {"message": "Mapping already exists"}

            # Create new mapping
            db_mapping = AgentTool(**mapping.dict())
            session.add(db_mapping)
            session.commit()
            logger.info(
                f"Created agent-tool mapping: Agent ID {mapping.agent_id} - Tool ID {mapping.tool_id}"
            )

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
            existing = (
                session.query(AgentRelationship)
                .filter(
                    AgentRelationship.parent_agent_id == relationship.parent_agent_id,
                    AgentRelationship.child_agent_id == relationship.child_agent_id,
                )
                .first()
            )

            if existing:
                return {"message": "Relationship already exists"}

            # Create new relationship
            db_relationship = AgentRelationship(**relationship.dict())
            session.add(db_relationship)
            session.commit()
            logger.info(
                f"Created agent relationship: Parent ID {relationship.parent_agent_id} - "
                f"Child ID {relationship.child_agent_id} - Type {relationship.relationship_type}"
            )

            return {
                "message": "Relationship created successfully",
                "id": db_relationship.id,
            }
    except Exception as e:
        logger.error(f"Error creating agent relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Routes for Agent Networks
@app.post("/networks/{coordinator_id}/run")
def run_network_endpoint(coordinator_id: int, input_data: Dict[str, Any]):
    """Run an agent network with given input."""
    try:
        with get_db_session() as session:
            # Always use the v0.3.0 compatible runner
            from ..core.runner_v030 import run_network_with_runner

            logger.info(
                f"Running network with coordinator {coordinator_id} using v0.3.0 compatible runner"
            )
            result = run_network_with_runner(coordinator_id, input_data, session)

            logger.info("Network execution completed")
            return {"result": result}
    except Exception as e:
        logger.error(
            f"Error running network with coordinator {coordinator_id}: {str(e)}"
        )
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
