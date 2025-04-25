"""
Example implementation of a multi-agent network using DB-ADK.

This example creates a travel planning system with a coordinator agent
and specialized agents for weather information and itinerary planning.
"""

import json
import os
import sys

from sqlalchemy import create_engine

# Add parent directory to path for standalone execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from DB-ADK package
from db_adk.core.network_manager import run_agent_network
from db_adk.db.connection import get_db_session
from db_adk.db.models import Agent, AgentRelationship, AgentTool, Base, Tool
from db_adk.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Example tool function implementations
# These would normally be in separate modules
def get_weather(location: str):
    """Get weather information for a location.

    Args:
        location (str): The location to get weather for (city, country).

    Returns:
        dict: Weather information.
    """
    # This is a mock implementation
    weather_data = {
        "location": location,
        "temperature": 25,
        "conditions": "Sunny",
        "forecast": [
            {"day": "Today", "temp": 25, "conditions": "Sunny"},
            {"day": "Tomorrow", "temp": 23, "conditions": "Partly Cloudy"},
            {"day": "Day after", "temp": 22, "conditions": "Cloudy"}
        ]
    }

    return weather_data

def plan_travel(destination: str, days: int):
    """Plan a travel itinerary.

    Args:
        destination (str): Travel destination.
        days (int): Number of days for the trip.

    Returns:
        dict: Travel itinerary.
    """
    # This is a mock implementation
    itinerary = {
        "destination": destination,
        "days": days,
        "plan": []
    }

    # Generate a simple itinerary
    for day in range(1, days + 1):
        itinerary["plan"].append({
            "day": day,
            "activities": [
                "Morning: Visit local attractions",
                "Afternoon: Enjoy local cuisine",
                "Evening: Cultural experience"
            ]
        })

    return itinerary

def setup_database():
    """Set up the database with example data.

    Returns:
        int: The ID of the coordinator agent.
    """
    # Create engine and tables
    engine = create_engine("postgresql://postgres:password@localhost:5432/db_adk")
    Base.metadata.create_all(engine)

    logger.info("Setting up database with example data")

    with get_db_session() as session:
        # Create weather tool
        weather_tool = Tool(
            name="get_weather",
            description="Get weather information for a location",
            tool_type="python_function",
            module_path="db_adk.examples.multi_agent_network",
            function_name="get_weather",
            parameters_schema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location to get weather for (city, country)"
                    }
                },
                "required": ["location"]
            }
        )
        session.add(weather_tool)

        # Create travel planning tool
        travel_tool = Tool(
            name="plan_travel",
            description="Plan a travel itinerary",
            tool_type="python_function",
            module_path="db_adk.examples.multi_agent_network",
            function_name="plan_travel",
            parameters_schema={
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "Travel destination"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days for the trip"
                    }
                },
                "required": ["destination", "days"]
            }
        )
        session.add(travel_tool)

        # Create coordinator agent
        coordinator = Agent(
            name="travel_coordinator",
            description="Coordinates travel planning with weather information",
            agent_type="Coordinator",
            prompt_template=(
                "You are a travel coordinator that helps plan trips taking weather into account.\n"
                "You coordinate between a weather assistant and a travel planner to create\n"
                "comprehensive travel plans that consider weather conditions."
            ),
            model_name="gemini-1.5-pro"
        )
        session.add(coordinator)

        # Create weather agent
        weather_agent = Agent(
            name="weather_assistant",
            description="Provides weather information",
            agent_type="LLM",
            prompt_template=(
                "You are a weather assistant that provides weather information for travel planning.\n"
                "When asked about weather, use the get_weather tool to retrieve information and\n"
                "provide helpful insights about how the weather might affect travel plans."
            ),
            model_name="gemini-1.5-pro"
        )
        session.add(weather_agent)

        # Create travel planner agent
        travel_agent = Agent(
            name="travel_planner",
            description="Plans travel itineraries",
            agent_type="LLM",
            prompt_template=(
                "You are a travel planner that creates detailed itineraries.\n"
                "When asked to plan a trip, use the plan_travel tool to create an itinerary and\n"
                "provide additional recommendations for activities, dining, and attractions."
            ),
            model_name="gemini-1.5-pro"
        )
        session.add(travel_agent)

        # Commit to get IDs
        session.commit()

        # Assign tools to agents
        session.add(AgentTool(
            agent_id=weather_agent.id,
            tool_id=weather_tool.id
        ))

        session.add(AgentTool(
            agent_id=travel_agent.id,
            tool_id=travel_tool.id
        ))

        # Set up agent relationships
        session.add(AgentRelationship(
            parent_agent_id=coordinator.id,
            child_agent_id=weather_agent.id,
            relationship_type="sequential",
            execution_order=1
        ))

        session.add(AgentRelationship(
            parent_agent_id=coordinator.id,
            child_agent_id=travel_agent.id,
            relationship_type="sequential",
            execution_order=2
        ))

        session.commit()

        logger.info(f"Database setup complete. Coordinator agent ID: {coordinator.id}")

        return coordinator.id

def run_example():
    """Run the example agent network."""
    try:
        # Set up database
        coordinator_id = setup_database()

        # Create and run the agent network
        with get_db_session() as session:
            # Prepare input data
            input_data = {
                "query": "Plan a 3-day trip to Barcelona in June"
            }

            logger.info(f"Running agent network with input: {input_data}")

            # Run the network
            result = run_agent_network(coordinator_id, input_data, session)

            # Print the result
            print("\nAgent Network Result:")
            print("====================")
            print(json.dumps(result, indent=2))

            logger.info("Example execution completed")

    except Exception as e:
        logger.error(f"Error running example: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_example()
