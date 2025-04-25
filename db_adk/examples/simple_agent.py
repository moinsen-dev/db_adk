"""
Simple example demonstrating how to create and run a single agent using DB-ADK.

This example shows how to:
1. Set up the database
2. Create a tool
3. Create an agent
4. Assign the tool to the agent
5. Run the agent with a query
"""

import json
import os
import sys

from sqlalchemy import create_engine

# Add parent directory to path for standalone execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from DB-ADK package
from db_adk.core.agent_factory import create_agent_from_record
from db_adk.db.connection import get_db_session
from db_adk.db.models import Agent, AgentTool, Base, Tool
from db_adk.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Example tool function implementation
def search_wiki(query: str) -> dict:
    """Search for information (mock implementation).

    Args:
        query (str): The search query.

    Returns:
        dict: Search results.
    """
    # This is a mock implementation
    return {
        "query": query,
        "results": [
            {
                "title": f"Result for {query}",
                "snippet": f"This is a mock search result for the query: {query}.",
                "url": f"https://example.com/search?q={query}"
            }
        ]
    }

def setup_database():
    """Set up the database with a simple agent and tool.

    Returns:
        int: The ID of the created agent.
    """
    # Create engine and tables
    engine = create_engine("postgresql://postgres:password@localhost:5432/db_adk")
    Base.metadata.create_all(engine)

    logger.info("Setting up database with simple agent example")

    with get_db_session() as session:
        # Create search tool
        search_tool = Tool(
            name="search_wiki",
            description="Search for information in a knowledge base",
            tool_type="python_function",
            module_path="db_adk.examples.simple_agent",
            function_name="search_wiki",
            parameters_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        )
        session.add(search_tool)
        session.commit()

        # Create a simple LLM agent
        agent = Agent(
            name="research_assistant",
            description="A research assistant that can search for information",
            agent_type="LLM",
            prompt_template=(
                "You are a helpful research assistant. When asked a question, you can search for "
                "information using the search_wiki tool. Provide clear, concise answers based on "
                "the search results. If the search doesn't yield relevant information, acknowledge "
                "that and provide your best guess based on your knowledge."
            ),
            model_name="gemini-1.5-pro",
            configuration={
                "temperature": 0.7,
                "top_p": 0.95
            }
        )
        session.add(agent)
        session.commit()

        # Assign tool to agent
        session.add(AgentTool(
            agent_id=agent.id,
            tool_id=search_tool.id
        ))
        session.commit()

        logger.info(f"Database setup complete. Agent ID: {agent.id}")

        return agent.id

def run_example():
    """Run the simple agent example."""
    try:
        # Set up database
        agent_id = setup_database()

        # Create and run the agent
        with get_db_session() as session:
            # Create agent from record
            agent = create_agent_from_record(agent_id, session)

            # Prepare query
            query = {
                "query": "What is the capital of France?"
            }

            logger.info(f"Running agent with query: {query}")

            # Run the agent
            result = agent.run(query)

            # Print the result
            print("\nAgent Result:")
            print("=============")
            print(json.dumps(result, indent=2))

            logger.info("Example execution completed")

    except Exception as e:
        logger.error(f"Error running example: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_example()
