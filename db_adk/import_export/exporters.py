"""
Export functionality for DB-ADK agents and tools.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from ..db.connection import get_db_session
from ..db.models import Agent, AgentRelationship
from .serializers import SerializerFormat, get_serializer


def prepare_agent_export(
    agent_id: int,
    session: Session,
    include_tools: bool = True,
    include_relationships: bool = True,
) -> Dict[str, Any]:
    """
    Prepare agent data for export.

    Args:
        agent_id: ID of the agent to export
        session: Database session
        include_tools: Whether to include tool definitions
        include_relationships: Whether to include agent relationships

    Returns:
        Dictionary with agent data

    Raises:
        ValueError: If agent not found
    """
    # Get agent
    agent = session.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise ValueError(f"Agent with ID {agent_id} not found")

    # Basic agent data
    agent_data = {
        "schema_version": "1.0",
        "export_date": datetime.utcnow().isoformat(),
        "agent": {
            "name": agent.name,
            "description": agent.description,
            "agent_type": agent.agent_type,
            "prompt_template": agent.prompt_template,
            "model_name": agent.model_name,
            "configuration": agent.configuration,
        },
    }

    # Include tools if requested
    if include_tools and agent.tools:
        tools_data = []
        for tool in agent.tools:
            tool_data = {
                "name": tool.name,
                "description": tool.description,
                "tool_type": tool.tool_type,
                "module_path": tool.module_path,
                "function_name": tool.function_name,
                "parameters_schema": tool.parameters_schema,
            }
            tools_data.append(tool_data)

        agent_data["tools"] = tools_data

    # Include relationships if requested
    if include_relationships:
        # Get relationships where this agent is the parent
        parent_relationships = (
            session.query(AgentRelationship)
            .filter(AgentRelationship.parent_agent_id == agent_id)
            .all()
        )

        if parent_relationships:
            relationships_data = []
            for rel in parent_relationships:
                child_agent = (
                    session.query(Agent).filter(Agent.id == rel.child_agent_id).first()
                )
                if child_agent:
                    rel_data = {
                        "child_agent_name": child_agent.name,
                        "relationship_type": rel.relationship_type,
                        "execution_order": rel.execution_order,
                    }
                    relationships_data.append(rel_data)

            if relationships_data:
                agent_data["relationships"] = relationships_data

    return agent_data


def export_agent(
    agent_id: int,
    output_file: Union[str, Path],
    format_name: Optional[str] = None,
    include_tools: bool = True,
    include_relationships: bool = True,
) -> str:
    """
    Export agent to file.

    Args:
        agent_id: ID of the agent to export
        output_file: Output file path
        format_name: Format to use (json or yaml), if None, determined from file extension
        include_tools: Whether to include tool definitions
        include_relationships: Whether to include agent relationships

    Returns:
        Path to the output file

    Raises:
        ValueError: If agent not found or format is unsupported
    """
    # Get serializer based on format or file extension
    serializer_class = get_serializer(format_name, output_file)

    with get_db_session() as session:
        # Prepare agent data
        agent_data = prepare_agent_export(
            agent_id, session, include_tools, include_relationships
        )

        # Serialize and write to file
        serializer_class.serialize_to_file(agent_data, output_file)

    return str(output_file)


def export_all_agents(
    output_dir: Union[str, Path],
    format_name: Optional[str] = None,
    include_tools: bool = True,
    include_relationships: bool = True,
) -> List[str]:
    """
    Export all agents to directory.

    Args:
        output_dir: Output directory path
        format_name: Format to use (json or yaml)
        include_tools: Whether to include tool definitions
        include_relationships: Whether to include agent relationships

    Returns:
        List of output file paths

    Raises:
        ValueError: If format is unsupported
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Determine file extension based on format
    if not format_name:
        format_name = SerializerFormat.JSON

    extension = ".json" if format_name.lower() == SerializerFormat.JSON else ".yaml"

    # Get serializer
    serializer_class = get_serializer(format_name)

    exported_files = []

    with get_db_session() as session:
        # Get all agents
        agents = session.query(Agent).all()

        for agent in agents:
            # Prepare agent data
            agent_data = prepare_agent_export(
                agent.id, session, include_tools, include_relationships
            )

            # Generate output file path
            file_name = f"{agent.name.lower().replace(' ', '_')}{extension}"
            file_path = output_path / file_name

            # Serialize and write to file
            serializer_class.serialize_to_file(agent_data, file_path)
            exported_files.append(str(file_path))

    return exported_files
