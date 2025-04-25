"""
Command-line interface for DB-ADK.
"""

import json
import sys

import click
from rich.console import Console
from rich.table import Table

from ..core.agent_factory import create_agent_from_record
from ..core.network_manager import run_agent_network
from ..db.connection import clear_db, get_db_session, init_db
from ..db.models import Agent, AgentRelationship, AgentTool, Tool
from ..import_export import (
    ImportOptions,
    export_agent,
    export_all_agents,
    import_agent,
    import_agents_from_directory,
)
from ..utils.logging import get_logger
from .rest import start_server

# Initialize logger
logger = get_logger(__name__)
console = Console()


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


@db.command("clear")
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
def clear_database(force):
    """Clear all data from the database by dropping and recreating all tables."""
    if not force:
        if not click.confirm(
            "This will delete ALL data from the database. Are you sure?"
        ):
            click.echo("Operation cancelled")
            return

    try:
        clear_db()
        click.echo("Database cleared successfully")
    except Exception as e:
        logger.error(f"Error clearing database: {str(e)}")
        click.echo(f"Error clearing database: {str(e)}", err=True)
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
                console.print("No agents found", style="yellow")
                return

            table = Table(title="Available Agents")
            table.add_column("ID", style="cyan", justify="right")
            table.add_column("Name", style="green")
            table.add_column("Type", style="magenta")
            table.add_column("Model", style="blue")
            table.add_column("Description", style="yellow")

            for agent in agents:
                # At runtime, these are actual values, not Column objects
                # The type checker is confused by SQLAlchemy's typing
                model_name = "None" if agent.model_name is None else agent.model_name
                description = "" if agent.description is None else agent.description

                table.add_row(
                    str(agent.id),
                    agent.name,  # type: ignore
                    agent.agent_type,  # type: ignore
                    model_name,  # type: ignore
                    description,  # type: ignore
                )

            console.print(table)
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        console.print(f"Error listing agents: {str(e)}", style="bold red")
        sys.exit(1)


@agents.command("create")
@click.option("--name", required=True, help="Agent name")
@click.option("--description", help="Agent description")
@click.option("--type", "agent_type", required=True, help="Agent type")
@click.option("--prompt", "prompt_template", help="Prompt template")
@click.option("--model", "model_name", help="Model name")
@click.option(
    "--config",
    "config_file",
    type=click.Path(exists=True),
    help="Configuration JSON file",
)
def create_agent(
    name, description, agent_type, prompt_template, model_name, config_file
):
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
                configuration=configuration,
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
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True),
    required=False,
    help="Input JSON file",
)
@click.option(
    "--query",
    "-q",
    type=str,
    required=False,
    help="Direct query text (alternative to input file)",
)
@click.option(
    "--use-v030",
    is_flag=True,
    default=False,
    help="Force using v0.3.0 compatible runner",
)
def run_agent_cmd(agent_id, input_file, query, use_v030):
    """Run an agent with given input, either from a file or direct query text."""
    # Check that we have either an input file or a direct query
    if not input_file and not query:
        logger.error("Error: Either --input or --query is required")
        click.echo("Error: Either --input or --query is required", err=True)
        sys.exit(1)

    # Prepare input data
    if input_file:
        try:
            with open(input_file, "r") as f:
                input_data = json.load(f)
        except Exception as e:
            logger.error(f"Error reading input file: {str(e)}")
            click.echo(f"Error reading input file: {str(e)}", err=True)
            sys.exit(1)
    else:
        # For direct queries, use the query text directly
        input_data = query

    with get_db_session() as session:
        try:
            # Detect if we should use the v0.3.0 compatible runner
            adk_version = None
            try:
                import google.adk

                adk_version = getattr(google.adk, "__version__", None)
            except (ImportError, AttributeError):
                pass

            # Use v0.3.0 runner if explicitly requested or if ADK version is 0.3.0 or higher
            use_v030_runner = use_v030 or (
                adk_version is not None
                and isinstance(adk_version, str)
                and adk_version >= "0.3.0"
            )

            if use_v030_runner:
                # Import here to avoid circular imports
                from ..core.runner_v030 import run_agent_with_runner

                console.print(
                    f"Using v0.3.0 compatible runner for ADK version: {adk_version or 'unknown'}",
                    style="yellow",
                )

                # Get agent name to display
                agent_record = session.query(Agent).filter(Agent.id == agent_id).first()
                agent_name = agent_record.name if agent_record else f"Agent {agent_id}"

                console.print(
                    f"Running agent [bold cyan]{agent_name}[/] with query...",
                    style="green",
                )

                # Run using v0.3.0 runner
                result = run_agent_with_runner(agent_id, input_data, session)
            else:
                # Create the agent using the traditional method
                agent = create_agent_from_record(agent_id, session)

                console.print(
                    f"Running agent [bold cyan]{agent.name}[/] with query...",
                    style="green",
                )

                # Use run_async with a simple string input for ADK compatibility
                import asyncio

                async def collect_results():
                    result = []
                    async for resp in agent.run_async(input_data):
                        if resp:
                            result.append(resp)
                    return result[-1] if result else "No response from agent"

                # Run the async generator and collect the results
                result = asyncio.run(collect_results())

            # Format the output nicely with Rich
            if isinstance(result, dict):
                console.print_json(json.dumps(result))
            else:
                console.print(result)

        except ImportError as e:
            console.print("Google ADK dependency error:", style="bold red")
            console.print(f"  {str(e)}", style="red")
            console.print(
                "\nThis is likely due to version incompatibility with the Google ADK library.",
                style="yellow",
            )
            console.print(
                "Please make sure you have the correct version installed or update the agent types in your database.",
                style="yellow",
            )
            sys.exit(1)
        except AttributeError as e:
            if "has no attribute" in str(e) and "Agent" in str(e):
                console.print("Google ADK agent type error:", style="bold red")
                console.print(f"  {str(e)}", style="red")
                console.print(
                    "\nThe agent type defined in the database is not available in your installed Google ADK version.",
                    style="yellow",
                )
                console.print(
                    "Please check the available agent types in your Google ADK version and update your agent records accordingly.",
                    style="yellow",
                )
                sys.exit(1)
            else:
                raise


@agents.command("export")
@click.argument("agent_id", type=int)
@click.option("--output", "-o", required=True, help="Output file path")
@click.option(
    "--format",
    "-f",
    "format_name",
    type=click.Choice(["json", "yaml"]),
    help="Export format (default: determined from file extension)",
)
@click.option(
    "--include-tools/--exclude-tools",
    default=True,
    help="Include tool definitions in export",
)
@click.option(
    "--include-relationships/--exclude-relationships",
    default=True,
    help="Include agent relationships in export",
)
def export_agent_cmd(
    agent_id, output, format_name, include_tools, include_relationships
):
    """Export an agent to a file."""
    try:
        output_file = export_agent(
            agent_id,
            output_file=output,
            format_name=format_name,
            include_tools=include_tools,
            include_relationships=include_relationships,
        )
        click.echo(f"Agent exported to {output_file}")
    except Exception as e:
        logger.error(f"Error exporting agent: {str(e)}")
        click.echo(f"Error exporting agent: {str(e)}", err=True)
        sys.exit(1)


@agents.command("export-all")
@click.option("--output-dir", "-o", required=True, help="Output directory path")
@click.option(
    "--format",
    "-f",
    "format_name",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Export format (default: json)",
)
@click.option(
    "--include-tools/--exclude-tools",
    default=True,
    help="Include tool definitions in export",
)
@click.option(
    "--include-relationships/--exclude-relationships",
    default=True,
    help="Include agent relationships in export",
)
def export_all_agents_cmd(
    output_dir, format_name, include_tools, include_relationships
):
    """Export all agents to files in a directory."""
    try:
        output_files = export_all_agents(
            output_dir=output_dir,
            format_name=format_name,
            include_tools=include_tools,
            include_relationships=include_relationships,
        )
        click.echo(f"Exported {len(output_files)} agents to {output_dir}")
    except Exception as e:
        logger.error(f"Error exporting agents: {str(e)}")
        click.echo(f"Error exporting agents: {str(e)}", err=True)
        sys.exit(1)


@agents.command("import")
@click.option(
    "--file", "-f", required=True, type=click.Path(exists=True), help="Input file path"
)
@click.option(
    "--use-existing-tools/--create-new-tools",
    default=True,
    help="Use existing tools with same name if found",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    help="Overwrite existing agent with same name",
)
@click.option(
    "--ignore-missing-relationships/--strict-relationships",
    default=True,
    help="Ignore relationships to missing agents",
)
def import_agent_cmd(file, use_existing_tools, overwrite, ignore_missing_relationships):
    """Import an agent from a file."""
    try:
        options = ImportOptions(
            use_existing_tools=use_existing_tools,
            overwrite_existing_agent=overwrite,
            ignore_missing_relationships=ignore_missing_relationships,
        )

        agent_id = import_agent(file_path=file, options=options)
        click.echo(f"Agent imported with ID: {agent_id}")
    except Exception as e:
        logger.error(f"Error importing agent: {str(e)}")
        click.echo(f"Error importing agent: {str(e)}", err=True)
        sys.exit(1)


@agents.command("import-dir")
@click.option(
    "--directory",
    "-d",
    required=True,
    type=click.Path(exists=True),
    help="Directory containing agent files",
)
@click.option(
    "--use-existing-tools/--create-new-tools",
    default=True,
    help="Use existing tools with same name if found",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    help="Overwrite existing agents with same name",
)
@click.option(
    "--ignore-missing-relationships/--strict-relationships",
    default=True,
    help="Ignore relationships to missing agents",
)
def import_agents_from_directory_cmd(
    directory, use_existing_tools, overwrite, ignore_missing_relationships
):
    """Import agents from files in a directory."""
    try:
        options = ImportOptions(
            use_existing_tools=use_existing_tools,
            overwrite_existing_agent=overwrite,
            ignore_missing_relationships=ignore_missing_relationships,
            defer_relationships=True,
        )

        agent_ids = import_agents_from_directory(
            directory_path=directory, options=options
        )
        click.echo(f"Imported {len(agent_ids)} agents")
    except Exception as e:
        logger.error(f"Error importing agents: {str(e)}")
        click.echo(f"Error importing agents: {str(e)}", err=True)
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
                console.print("No tools found", style="yellow")
                return

            table = Table(title="Available Tools")
            table.add_column("ID", style="cyan", justify="right")
            table.add_column("Name", style="green")
            table.add_column("Type", style="magenta")
            table.add_column("Module", style="blue")
            table.add_column("Function", style="yellow")

            for tool in tools:
                # At runtime, these are actual values, not Column objects
                table.add_row(
                    str(tool.id),
                    tool.name,  # type: ignore
                    tool.tool_type,  # type: ignore
                    tool.module_path,  # type: ignore
                    tool.function_name,  # type: ignore
                )

            console.print(table)
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        console.print(f"Error listing tools: {str(e)}", style="bold red")
        sys.exit(1)


@tools.command("create")
@click.option("--name", required=True, help="Tool name")
@click.option("--description", help="Tool description")
@click.option("--type", "tool_type", required=True, help="Tool type")
@click.option("--module", "module_path", required=True, help="Module path")
@click.option("--function", "function_name", required=True, help="Function name")
@click.option(
    "--schema",
    "schema_file",
    type=click.Path(exists=True),
    help="Parameters schema JSON file",
)
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
                parameters_schema=parameters_schema,
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
            existing = (
                session.query(AgentTool)
                .filter(AgentTool.agent_id == agent_id, AgentTool.tool_id == tool_id)
                .first()
            )

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
            query = (
                session.query(AgentTool, Agent, Tool)
                .join(Agent, AgentTool.agent_id == Agent.id)
                .join(Tool, AgentTool.tool_id == Tool.id)
            )

            if agent_id:
                query = query.filter(AgentTool.agent_id == agent_id)

            mappings = query.all()

            if not mappings:
                console.print("No mappings found", style="yellow")
                return

            table = Table(title="Agent-Tool Mappings")
            table.add_column("Agent ID", style="cyan", justify="right")
            table.add_column("Agent Name", style="green")
            table.add_column("Tool ID", style="cyan", justify="right")
            table.add_column("Tool Name", style="yellow")

            for mapping, agent, tool in mappings:
                table.add_row(
                    str(agent.id),
                    agent.name,  # type: ignore
                    str(tool.id),
                    tool.name,  # type: ignore
                )

            console.print(table)
    except Exception as e:
        logger.error(f"Error listing agent-tool mappings: {str(e)}")
        console.print(f"Error listing agent-tool mappings: {str(e)}", style="bold red")
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
            existing = (
                session.query(AgentRelationship)
                .filter(
                    AgentRelationship.parent_agent_id == parent_id,
                    AgentRelationship.child_agent_id == child_id,
                )
                .first()
            )

            if existing:
                click.echo("Relationship already exists")
                return

            # Create relationship
            relationship = AgentRelationship(
                parent_agent_id=parent_id,
                child_agent_id=child_id,
                relationship_type=rel_type,
                execution_order=order,
            )
            session.add(relationship)
            session.commit()
            click.echo(
                f"Created relationship: Parent {parent_id} -> Child {child_id} (Type: {rel_type}, Order: {order})"
            )
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
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True),
    required=False,
    help="Input JSON file",
)
@click.option(
    "--query",
    "-q",
    type=str,
    required=False,
    help="Direct query text (alternative to input file)",
)
@click.option(
    "--use-v030",
    is_flag=True,
    default=False,
    help="Force using v0.3.0 compatible runner",
)
def run_network_cmd(coordinator_id, input_file, query, use_v030):
    """Run an agent network with a coordinator, either from a file or direct query text."""
    try:
        if not input_file and not query:
            console.print(
                "Error: Either --input or --query must be provided", style="bold red"
            )
            sys.exit(1)

        if input_file and query:
            console.print(
                "Warning: Both input file and query provided. Using input file.",
                style="yellow",
            )

        if input_file:
            with open(input_file, "r") as f:
                input_data = json.load(f)
        else:
            # For v0.3.0 compatibility, use the query text directly
            # rather than wrapping in a dictionary
            input_data = query

        with get_db_session() as session:
            try:
                # Detect if we should use the v0.3.0 compatible runner
                adk_version = None
                try:
                    import google.adk

                    adk_version = getattr(google.adk, "__version__", None)
                except (ImportError, AttributeError):
                    pass

                # Use v0.3.0 runner if explicitly requested or if ADK version is 0.3.0 or higher
                use_v030_runner = use_v030 or (
                    adk_version is not None
                    and isinstance(adk_version, str)
                    and adk_version >= "0.3.0"
                )

                # Get agent name to display
                agent_record = (
                    session.query(Agent).filter(Agent.id == coordinator_id).first()
                )
                agent_name = (
                    agent_record.name
                    if agent_record
                    else f"Network Coordinator {coordinator_id}"
                )

                console.print(
                    f"Running agent network with coordinator [bold cyan]{agent_name}[/]...",
                    style="green",
                )

                if use_v030_runner:
                    # Import here to avoid circular imports
                    from ..core.runner_v030 import run_network_with_runner

                    console.print(
                        f"Using v0.3.0 compatible runner for ADK version: {adk_version or 'unknown'}",
                        style="yellow",
                    )

                    # Run using v0.3.0 runner
                    result = run_network_with_runner(
                        coordinator_id, input_data, session
                    )
                else:
                    # Use the traditional runner
                    result = run_agent_network(coordinator_id, input_data, session)

                # Format the output nicely with Rich
                if isinstance(result, dict):
                    console.print_json(json.dumps(result))
                else:
                    console.print(result)
            except ImportError as e:
                console.print("Google ADK dependency error:", style="bold red")
                console.print(f"  {str(e)}", style="red")
                console.print(
                    "\nThis is likely due to version incompatibility with the Google ADK library.",
                    style="yellow",
                )
                console.print(
                    "Please make sure you have the correct version installed or update the agent types in your database.",
                    style="yellow",
                )
                sys.exit(1)
            except AttributeError as e:
                if "has no attribute" in str(e) and "Agent" in str(e):
                    console.print("Google ADK agent type error:", style="bold red")
                    console.print(f"  {str(e)}", style="red")
                    console.print(
                        "\nThe agent type defined in the database is not available in your installed Google ADK version.",
                        style="yellow",
                    )
                    console.print(
                        "Please check the available agent types in your Google ADK version and update your agent records accordingly.",
                        style="yellow",
                    )
                    sys.exit(1)
                else:
                    raise
    except Exception as e:
        logger.error(f"Error running network: {str(e)}")
        console.print(f"Error running network: {str(e)}", style="bold red")
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
