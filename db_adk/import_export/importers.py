"""
Import functionality for DB-ADK agents and tools.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jsonschema import ValidationError, validate
from sqlalchemy.orm import Session

from ..db.connection import get_db_session
from ..db.models import Agent, AgentRelationship, AgentTool, Tool
from .serializers import detect_format, get_serializer

# Set up logger
logger = logging.getLogger(__name__)


# Schema for validation
AGENT_SCHEMA = {
    "type": "object",
    "required": ["schema_version", "agent"],
    "properties": {
        "schema_version": {"type": "string"},
        "export_date": {"type": "string"},
        "agent": {
            "type": "object",
            "required": ["name", "agent_type"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": ["string", "null"]},
                "agent_type": {"type": "string"},
                "prompt_template": {"type": ["string", "null"]},
                "model_name": {"type": ["string", "null"]},
                "configuration": {"type": "object"},
            },
        },
        "tools": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "tool_type", "module_path", "function_name"],
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": ["string", "null"]},
                    "tool_type": {"type": "string"},
                    "module_path": {"type": "string"},
                    "function_name": {"type": "string"},
                    "parameters_schema": {"type": "object"},
                },
            },
        },
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["child_agent_name", "relationship_type"],
                "properties": {
                    "child_agent_name": {"type": "string"},
                    "relationship_type": {"type": "string"},
                    "execution_order": {"type": "integer"},
                },
            },
        },
    },
}


class ImportOptions:
    """Options for controlling agent import behavior."""

    def __init__(
        self,
        use_existing_tools: bool = True,
        overwrite_existing_agent: bool = False,
        ignore_missing_relationships: bool = True,
        defer_relationships: bool = True,
    ):
        """
        Initialize import options.

        Args:
            use_existing_tools: Whether to use existing tools with the same name
            overwrite_existing_agent: Whether to overwrite existing agent with the same name
            ignore_missing_relationships: Whether to ignore relationships to non-existent agents
            defer_relationships: Whether to create relationships after all agents are imported
        """
        self.use_existing_tools = use_existing_tools
        self.overwrite_existing_agent = overwrite_existing_agent
        self.ignore_missing_relationships = ignore_missing_relationships
        self.defer_relationships = defer_relationships


def validate_import_data(data: Dict[str, Any]) -> bool:
    """
    Validate import data against schema.

    Args:
        data: Agent data dictionary

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    try:
        validate(instance=data, schema=AGENT_SCHEMA)
        return True
    except ValidationError as e:
        logger.error(f"Schema validation error: {str(e)}")
        raise


def import_agent(
    file_path: Union[str, Path], options: Optional[ImportOptions] = None
) -> int:
    """
    Import agent from file.

    Args:
        file_path: Path to input file
        options: Import options

    Returns:
        ID of the imported agent

    Raises:
        ValueError: If agent data is invalid or import fails
    """
    if options is None:
        options = ImportOptions()

    file_path = Path(file_path)
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")

    try:
        # Detect format and deserialize
        with open(file_path, "r") as f:
            content = f.read()

        serializer_class = detect_format(content)
        data = serializer_class.deserialize(content)

        # Validate against schema
        validate_import_data(data)

        # Import agent to database
        with get_db_session() as session:
            agent_id = create_agent_from_data(data, session, options)
            return agent_id

    except Exception as e:
        logger.error(f"Error importing agent: {str(e)}")
        raise ValueError(f"Failed to import agent: {str(e)}")


def create_agent_from_data(
    data: Dict[str, Any], session: Session, options: ImportOptions
) -> int:
    """
    Create agent from import data.

    Args:
        data: Agent data dictionary
        session: Database session
        options: Import options

    Returns:
        ID of the created/updated agent
    """
    agent_data = data["agent"]

    # Check if agent exists
    existing_agent = (
        session.query(Agent).filter(Agent.name == agent_data["name"]).first()
    )

    if existing_agent and not options.overwrite_existing_agent:
        raise ValueError(
            f"Agent with name '{agent_data['name']}' already exists. Use overwrite option to replace it."
        )

    if existing_agent:
        # Update existing agent
        existing_agent.description = agent_data.get("description")
        existing_agent.agent_type = agent_data["agent_type"]
        existing_agent.prompt_template = agent_data.get("prompt_template")
        existing_agent.model_name = agent_data.get("model_name")
        existing_agent.configuration = agent_data.get("configuration", {})
        agent = existing_agent
    else:
        # Create new agent
        agent = Agent(
            name=agent_data["name"],
            description=agent_data.get("description"),
            agent_type=agent_data["agent_type"],
            prompt_template=agent_data.get("prompt_template"),
            model_name=agent_data.get("model_name"),
            configuration=agent_data.get("configuration", {}),
        )
        session.add(agent)

    # Flush to get agent ID
    session.flush()
    agent_id = int(agent.id)  # Explicitly cast to int to handle Column[int] type

    # Import tools if included
    if "tools" in data and data["tools"]:
        import_tools(agent_id, data["tools"], session, options)

    # Import relationships if included and not deferred
    if (
        "relationships" in data
        and data["relationships"]
        and not options.defer_relationships
    ):
        import_relationships(agent_id, data["relationships"], session, options)

    # Commit changes
    session.commit()

    return agent_id


def import_tools(
    agent_id: int,
    tools_data: List[Dict[str, Any]],
    session: Session,
    options: ImportOptions,
) -> None:
    """
    Import tools and associate them with agent.

    Args:
        agent_id: ID of the agent
        tools_data: List of tool data dictionaries
        session: Database session
        options: Import options
    """
    # Get existing agent-tool mappings
    existing_mappings = (
        session.query(AgentTool).filter(AgentTool.agent_id == agent_id).all()
    )
    existing_tool_ids = {mapping.tool_id for mapping in existing_mappings}

    # Process each tool
    for tool_data in tools_data:
        # Check if tool exists
        existing_tool = (
            session.query(Tool).filter(Tool.name == tool_data["name"]).first()
        )

        if existing_tool and options.use_existing_tools:
            # Use existing tool
            tool = existing_tool
        else:
            # Create new tool
            tool = Tool(
                name=tool_data["name"],
                description=tool_data.get("description"),
                tool_type=tool_data["tool_type"],
                module_path=tool_data["module_path"],
                function_name=tool_data["function_name"],
                parameters_schema=tool_data.get("parameters_schema", {}),
            )
            session.add(tool)
            session.flush()

        # Create agent-tool mapping if not exists
        if tool.id not in existing_tool_ids:
            mapping = AgentTool(agent_id=agent_id, tool_id=tool.id)
            session.add(mapping)
            existing_tool_ids.add(tool.id)


def import_relationships(
    parent_agent_id: int,
    relationships_data: List[Dict[str, Any]],
    session: Session,
    options: ImportOptions,
) -> None:
    """
    Import agent relationships.

    Args:
        parent_agent_id: ID of the parent agent
        relationships_data: List of relationship data dictionaries
        session: Database session
        options: Import options
    """
    # Process each relationship
    for rel_data in relationships_data:
        child_agent_name = rel_data["child_agent_name"]

        # Find child agent by name
        child_agent = (
            session.query(Agent).filter(Agent.name == child_agent_name).first()
        )

        if not child_agent:
            if options.ignore_missing_relationships:
                logger.warning(
                    f"Child agent '{child_agent_name}' not found, skipping relationship"
                )
                continue
            else:
                raise ValueError(f"Child agent '{child_agent_name}' not found")

        # Check if relationship already exists
        existing_rel = (
            session.query(AgentRelationship)
            .filter(
                AgentRelationship.parent_agent_id == parent_agent_id,
                AgentRelationship.child_agent_id == child_agent.id,
            )
            .first()
        )

        if not existing_rel:
            # Create new relationship
            rel = AgentRelationship(
                parent_agent_id=parent_agent_id,
                child_agent_id=child_agent.id,
                relationship_type=rel_data["relationship_type"],
                execution_order=rel_data.get("execution_order", 0),
            )
            session.add(rel)


def import_agents_from_directory(
    directory_path: Union[str, Path], options: Optional[ImportOptions] = None
) -> List[int]:
    """
    Import all agent files from directory.

    Args:
        directory_path: Path to directory containing agent files
        options: Import options

    Returns:
        List of imported agent IDs
    """
    if options is None:
        options = ImportOptions(defer_relationships=True)

    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"Directory not found: {directory}")

    # First pass: import all agents without relationships
    agent_ids = []
    relationship_data = {}  # Store relationship data for second pass

    for file_path in (
        directory.glob("*.json") or directory.glob("*.yaml") or directory.glob("*.yml")
    ):
        try:
            # Read and deserialize file
            serializer_class = get_serializer(file_path=file_path)
            data = serializer_class.deserialize_from_file(file_path)

            # Validate data
            validate_import_data(data)

            # Store relationships for later if defer_relationships is True
            if options.defer_relationships and "relationships" in data:
                relationships = data.pop("relationships", None)
                if relationships:
                    relationship_data[data["agent"]["name"]] = relationships

            # Import agent
            with get_db_session() as session:
                agent_id = create_agent_from_data(data, session, options)
                agent_ids.append(agent_id)

        except Exception as e:
            logger.error(f"Error importing {file_path}: {str(e)}")
            if not options.ignore_missing_relationships:
                raise

    # Second pass: create relationships if deferred
    if options.defer_relationships and relationship_data:
        with get_db_session() as session:
            for agent_name, relationships in relationship_data.items():
                # Get agent ID from name
                agent = session.query(Agent).filter(Agent.name == agent_name).first()
                if agent:
                    try:
                        import_relationships(
                            int(agent.id), relationships, session, options
                        )
                    except Exception as e:
                        logger.error(
                            f"Error importing relationships for {agent_name}: {str(e)}"
                        )
                        if not options.ignore_missing_relationships:
                            raise

            # Commit all relationship changes
            session.commit()

    return agent_ids
