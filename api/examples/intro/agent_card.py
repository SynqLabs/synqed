"""
Agent Card Example - View an agent's capabilities and metadata

This example shows how to fetch and display an agent's card, which contains:
- Agent name and description
- Available skills/capabilities
- Supported features (streaming, authentication, etc.)

The agent card is available at the /.well-known/agent-card endpoint.

To run:
1. First, start the agent: python agent.py
2. Then run this script: python agent_card.py
"""
import synqed
import asyncio
import aiohttp

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/.well-known/agent-card.json") as resp:
            card = await resp.json()
            
            print("Agent Card:")
            print("=" * 60)
            
            import json
            print(json.dumps(card, indent=2))
            
            print("\n" + "=" * 60)
            print(f"Agent Name: {card['name']}")
            print(f"Skills: {[s['id'] for s in card['skills']]}")
            print(f"Streaming: {card['capabilities']['streaming']}")

if __name__ == "__main__":
    asyncio.run(main())
