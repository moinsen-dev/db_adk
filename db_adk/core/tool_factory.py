"""
Factory for loading tools from database records.
"""

import json
import importlib
from ..db.models import Tool, AgentTool
from ..utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

def load_tools_for_agent(agent_id, db_session):
    """Load all tools associated with an agent.
    
    Args:
        agent_id (int): The ID of the agent.
        db_session: The database session.
        
    Returns:
        list: A list of ADK tool instances.
    """
    # Query for tool mappings
    mappings = db_session.query(AgentTool).filter(AgentTool.agent_id == agent_id).all()
    
    logger.info(f"Loading tools for agent ID: {agent_id} (found {len(mappings)} mappings)")
    
    tools = []
    for mapping in mappings:
        # Fetch tool record
        tool_record = db_session.query(Tool).filter(Tool.id == mapping.tool_id).first()
        if tool_record:
            try:
                # Create the tool
                tool = create_tool_from_record(tool_record)
                tools.append(tool)
            except Exception as e:
                logger.error(f"Failed to create tool {tool_record.name}: {str(e)}")
    
    logger.info(f"Successfully loaded {len(tools)} tools for agent ID: {agent_id}")
    
    return tools

def create_tool_from_record(tool_record):
    """Create an ADK tool from a tool record.
    
    Args:
        tool_record (Tool): The tool record.
        
    Returns:
        google.adk.Tool: The created tool instance.
        
    Raises:
        ImportError: If the module cannot be imported.
        AttributeError: If the function does not exist in the module.
    """
    try:
        # Import Google ADK
        from google.adk import Tool as AdkTool
        
        logger.info(f"Creating tool from record: {tool_record.name} (ID: {tool_record.id})")
        
        # Dynamically import the module containing the tool
        module = importlib.import_module(tool_record.module_path)
        
        # Get the function
        tool_func = getattr(module, tool_record.function_name)
        
        # Parse parameters schema
        parameters_schema = {}
        if tool_record.parameters_schema:
            if isinstance(tool_record.parameters_schema, str):
                parameters_schema = json.loads(tool_record.parameters_schema)
            else:
                parameters_schema = tool_record.parameters_schema
        
        # Create ADK tool wrapper
        tool = AdkTool(
            func=tool_func,
            name=tool_record.name,
            description=tool_record.description,
            parameters_schema=parameters_schema
        )
        
        logger.info(f"Successfully created tool: {tool_record.name}")
        
        return tool
    except ImportError as e:
        logger.error(f"Failed to import module {tool_record.module_path}: {str(e)}")
        raise
    except AttributeError as e:
        logger.error(f"Function {tool_record.function_name} not found in module {tool_record.module_path}: {str(e)}")
        raise
