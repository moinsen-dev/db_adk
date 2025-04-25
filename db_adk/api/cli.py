"""
Command-line interface for DB-ADK.
"""

import click
import json
import os
import sys
from ..db.models import Agent, Tool, AgentTool, AgentRelationship
from ..db.connection import get_db_session, init_db
from ..core.agent_factory import create_agent_from_record
from ..core.network_manager import create_agent_network, run_agent_network
from ..utils.logging import get_logger
from .rest import start_server

# Initialize logger
logger = get_logger(__name__)

@click.group()
def cli():
    """Database-driven Agent Development Kit CLI."""
    pass

# Database commands
@cli.group()
def db():
    """Manage database."""
    pass

@db.command("init")
def init_database():
    """Initialize the database by creating all tables."""
    try:
        init_db()
        click.echo("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        click.echo(f"Error initializing database: {str(e)}", err=True)
        sys.exit(1)

# Agent commands
@cli.group()
def agents():
    """Manage agents."""
    pass

@agents.command("list")
def list_agents():
    """List all agents."""
    try:
        with get_db_session() as session:
            agents = session.query(Agent).all()
            if not agents:
                click.echo("No agents found")
                return
            
            click.echo("ID | Name | Type | Description")
            click.echo("-" * 50)
            for agent in agents:
                click.echo(f"{agent.id} | {agent.name} | {agent.agent_type} | {agent.description}")
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        click.echo(f"Error listing agents: {str(e)}", err=True)
        sys.exit(1)

@agents.command("create")
@click.option("--name", required=True, help="Agent name")
@click.option("--description", help="Agent description")
@click.option("--type", "agent_type", required=True, help="Agent type")
@click.option("--prompt", "prompt_template", help="Prompt template")
@click.option("--model", "model_name", help="Model name")
@click.option("--config", "config_file", type=click.Path(exists=True), help="Configuration JSON file")
def create_agent(name, description, agent_type, prompt_template, model_name, config_file):
    """Create a new agent."""
    try:
        configuration = {}
        if config_file:
            with open(config_file, "r") as f:
                configuration = json.load(f)
        
        with get_db_session() as session:
            agent = Agent(
                name=name,
                description=description,
                agent_type=agent_type,
                prompt_template=prompt_template,
                model_name=model_name,
                configuration=configuration
            )
            session.add(agent)
            session.commit()
            click.echo(f"Created agent with ID: {agent.id}")
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        click.echo(f"Error creating agent: {str(e)}", err=True)
        sys.exit(1)

@agents.command("run")
@click.argument("agent_id", type=int)
@click.option("--input", "input_file", type=click.Path(exists=True), required=True, help="Input JSON file")
def run_agent_cmd(agent_id, input_file):
    """Run an agent with given input."""
    try:
        with open(input_file, "r") as f:
            input_data = json.load(f)
        
        with get_db_session() as session:
            agent = create_agent_from_record(agent_id, session)
            result = agent.run(input_data)
            click.echo(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}")
        click.echo(f"Error running agent: {str(e)}", err=True)
        sys.exit(1)

# Tool commands
@cli.group()
def tools():
    """Manage tools."""
    pass

@tools.command("list")
def list_tools():
    """List all tools."""
    try:
        with get_db_session() as session:
            tools = session.query(Tool).all()
            if not tools:
                click.echo("No tools found")
                return
            
            click.echo("ID | Name | Type | Module | Function")
            click.echo("-" * 60)
            for tool in tools:
                click.echo(f"{tool.id} | {tool.name} | {tool.tool_type} | {tool.module_path} | {tool.function_name}")
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        click.echo(f"Error listing tools: {str(e)}", err=True)
        sys.exit(1)

@tools.command("create")
@click.option("--name", required=True, help="Tool name")
@click.option("--description", help="Tool description")
@click.option("--type", "tool_type", required=True, help="Tool type")
@click.option("--module", "module_path", required=True, help="Module path")
@click.option("--function", "function_name", required=True, help="Function name")
@click.option("--schema", "schema_file", type=click.Path(exists=True), help="Parameters schema JSON file")
def create_tool(name, description, tool_type, module_path, function_name, schema_file):
    """Create a new tool."""
    try:
        parameters_schema = {}
        if schema_file:
            with open(schema_file, "r") as f:
                parameters_schema = json.load(f)
        
        with get_db_session() as session:
            tool = Tool(
                name=name,
                description=description,
                tool_type=tool_type,
                module_path=module_path,
                function_name=function_name,
                parameters_schema=parameters_schema
            )
            session.add(tool)
            session.commit()
            click.echo(f"Created tool with ID: {tool.id}")
    except Exception as e:
        logger.error(f"Error creating tool: {str(e)}")
        click.echo(f"Error creating tool: {str(e)}", err=True)
        sys.exit(1)

# Agent-Tool mapping commands
@cli.group(name="agent-tools")
def agent_tools():
    """Manage agent-tool mappings."""
    pass

@agent_tools.command("assign")
@click.option("--agent-id", required=True, type=int, help="Agent ID")
@click.option("--tool-id", required=True, type=int, help="Tool ID")
def assign_tool(agent_id, tool_id):
    """Assign a tool to an agent."""
    try:
        with get_db_session() as session:
            # Check if mapping already exists
            existing = session.query(AgentTool).filter(
                AgentTool.agent_id == agent_id,
                AgentTool.tool_id == tool_id
            ).first()
            
            if existing:
                click.echo("Tool is already assigned to this agent")
                return
            
            # Create mapping
            mapping = AgentTool(agent_id=agent_id, tool_id=tool_id)
            session.add(mapping)
            session.commit()
            click.echo(f"Assigned tool {tool_id} to agent {agent_id}")
    except Exception as e:
        logger.error(f"Error assigning tool: {str(e)}")
        click.echo(f"Error assigning tool: {str(e)}", err=True)
        sys.exit(1)

@agent_tools.command("list")
@click.option("--agent-id", type=int, help="Filter by agent ID")
def list_agent_tools(agent_id):
    """List agent-tool mappings."""
    try:
        with get_db_session() as session:
            query = session.query(AgentTool, Agent, Tool).join(
                Agent, AgentTool.agent_id == Agent.id
            ).join(
                Tool, AgentTool.tool_id == Tool.id
            )
            
            if agent_id:
                query = query.filter(AgentTool.agent_id == agent_id)
            
            mappings = query.all()
            
            if not mappings:
                click.echo("No mappings found")
                return
            
            click.echo("Agent ID | Agent Name | Tool ID | Tool Name")
            click.echo("-" * 60)
            for mapping, agent, tool in mappings:
                click.echo(f"{agent.id} | {agent.name} | {tool.id} | {tool.name}")
    except Exception as e:
        logger.error(f"Error listing agent-tool mappings: {str(e)}")
        click.echo(f"Error listing agent-tool mappings: {str(e)}", err=True)
        sys.exit(1)

# Agent relationship commands
@cli.group(name="relationships")
def relationships():
    """Manage agent relationships."""
    pass

@relationships.command("create")
@click.option("--parent-id", required=True, type=int, help="Parent agent ID")
@click.option("--child-id", required=True, type=int, help="Child agent ID")
@click.option("--type", "rel_type", required=True, help="Relationship type")
@click.option("--order", type=int, default=0, help="Execution order")
def create_relationship(parent_id, child_id, rel_type, order):
    """Create a relationship between agents."""
    try:
        with get_db_session() as session:
            # Check if relationship already exists
            existing = session.query(AgentRelationship).filter(
                AgentRelationship.parent_agent_id == parent_id,
                AgentRelationship.child_agent_id == child_id
            ).first()
            
            if existing:
                click.echo("Relationship already exists")
                return
            
            # Create relationship
            relationship = AgentRelationship(
                parent_agent_id=parent_id,
                child_agent_id=child_id,
                relationship_type=rel_type,
                execution_order=order
            )
            session.add(relationship)
            session.commit()
            click.echo(f"Created relationship: Parent {parent_id} -> Child {child_id} (Type: {rel_type}, Order: {order})")
    except Exception as e:
        logger.error(f"Error creating relationship: {str(e)}")
        click.echo(f"Error creating relationship: {str(e)}", err=True)
        sys.exit(1)

# Network commands
@cli.group()
def networks():
    """Manage agent networks."""
    pass

@networks.command("run")
@click.argument("coordinator_id", type=int)
@click.option("--input", "input_file", type=click.Path(exists=True), required=True, help="Input JSON file")
def run_network_cmd(coordinator_id, input_file):
    """Run an agent network with a coordinator."""
    try:
        with open(input_file, "r") as f:
            input_data = json.load(f)
        
        with get_db_session() as session:
            result = run_agent_network(coordinator_id, input_data, session)
            click.echo(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Error running network: {str(e)}")
        click.echo(f"Error running network: {str(e)}", err=True)
        sys.exit(1)

# Server command
@cli.command("serve")
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=8000, type=int, help="Port to bind")
def serve(host, port):
    """Start the REST API server."""
    try:
        start_server(host, port)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        click.echo(f"Error starting server: {str(e)}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    cli()
