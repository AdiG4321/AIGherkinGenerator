import os
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
load_dotenv()

# Initialize the agents
qa_agent = Agent(
    model=OpenAIChat(id="gpt-4o", api_key=os.environ.get("OPENAI_API_KEY")),
    markdown=True,
) 