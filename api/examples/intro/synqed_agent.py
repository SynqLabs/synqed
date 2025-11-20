"""
Agent Creation Example - Build and run your own AI agent

This shows how to create an agent in 3 steps:

1. Define agent_logic() - What your agent does, what LLM it is
   - Gets the user's message from context
   - Calls an LLM (ex. OpenAI) to generate a response

2. Create an Agent - Give it a name, description, and skills
   - name: What to call your agent
   - description: What it does
   - skills: What capabilities it has
   - executor: The function that handles requests (agent_logic)
   - capabilities: Optional dict to configure:
     * streaming: Enable real-time response streaming (default: True)
     * push_notifications: Enable webhook notifications for long tasks (default: False)
     * state_transition_history: Enable state change tracking (default: False)

3. Create a Server - Host your agent so clients can connect
   - The agent runs at http://localhost:8000
   - Clients can connect and send messages to it

Setup:
1. Install dependencies: pip install openai python-dotenv
2. Create a .env file with: OPENAI_API_KEY='your-key-here'
3. Run: python agent.py
4. Test: python client.py (in another terminal)
"""
import synqed
import asyncio

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in the script directory, parent directories, or current working directory
load_dotenv()  # Checks current directory and parents
load_dotenv(dotenv_path=Path(__file__).parent / '.env')  # Check script directory

async def agent_logic(context):
    """Agent logic for a gpt-4o agent."""
    user_message = context.get_user_input()
    
    # Define the agent's capabilities and what LLM it is
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful customer support assistant."},
            {"role": "user", "content": user_message}
        ]
    )
        
    return response.choices[0].message.content

async def main():
    # Step 1: Create your agent
    agent = synqed.Agent(
        name="Customer Support Assistant",
        description="Automated support agent that handles customer inquiries and service requests efficiently",
        skills=["customer_support", "ticket_routing", "inquiry_handling"],
        executor=agent_logic,  # The function that processes messages
        
        # Optional: Configure agent capabilities
        capabilities={
            "streaming": True,              # Enable real-time streaming responses
            "push_notifications": False,    # Disable webhook notifications for long tasks
            "state_transition_history": False  # Disable state history tracking
        }
    )
    
    # Step 2: Create a server to host your agent
    server = synqed.AgentServer(agent, port=8000)
    
    # Step 3: Start the server
    print(f"Agent running at {agent.url}")
    print("Ready to receive messages! Run client.py to test it.")
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
