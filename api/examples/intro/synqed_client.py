"""
Client Example - Two ways to talk to an AI agent

There are 2 ways to get responses:

1. ask() - Wait for the complete answer
   Example: response = await client.ask("What's 2+2?")
   Use when: You need the full answer at once

2. stream() - Get the answer piece by piece (like ChatGPT typing)
   Example: async for chunk in client.stream("Tell a story"):
   Use when: You want to show text appearing in real-time

Why use end="" and flush=True?
- end="" makes chunks print on the same line (not separate lines)
- flush=True makes text appear immediately (creates typing effect)

To run:
1. First, start the agent: python agent_creation_and_card.py
2. Then run this client: python client.py
"""
import synqed
import asyncio

async def main():
    # Connect to the AI agent
    async with synqed.Client("http://localhost:8000") as client:
        
        # Method 1: Get the complete answer at once
        response = await client.ask("What are 3 best practices for customer support?")
        print(f"Complete response:\n{response}\n")
        
        # Method 2: Get the answer piece by piece, in real-time
        print("Streaming response:")
        async for chunk in client.stream("Tell me a short story about a helpful robot"):
            print(chunk, end="", flush=True)  # Creates typing effect
        print()

if __name__ == "__main__":
    asyncio.run(main())