from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

# 1. Define the agent
root_agent = Agent(
    name="search_assistant",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant. Answer user questions using Google Search when needed.",
    description="An assistant that can search the web.",
    tools=[google_search],
)

# 2. Set up session service
session_service = InMemorySessionService()
session = session_service.create_session(
    app_name="search_app", user_id="user123", session_id="sess123"
)

# 3. Create runner
runner = Runner(
    agent=root_agent, app_name="search_app", session_service=session_service
)


# 4. Programmatic interaction
def call_agent(query: str):
    content = types.Content(role="user", parts=[types.Part(text=query)])
    events = runner.run(user_id="user123", session_id="sess123", new_message=content)
    for event in events:
        if event.is_final_response():
            print("Agent Response:", event.content.parts[0].text)


# Example call
call_agent("What's the weather forecast for Berlin today?")
