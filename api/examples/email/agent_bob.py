"""
Bob Agent - A helpful builder
Email: bob@builder

Simple synqed agent with Anthropic AI.
"""

import asyncio
import os
from pathlib import Path
from anthropic import AsyncAnthropic
import synqed

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass


async def bob_logic(context):
    """Bob's AI logic - responds to messages naturally"""
    latest = context.latest_message
    if not latest or not latest.content:
        return None
    
    # Get Anthropic client
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY not set!")
        return None
    
    anthropic_client = AsyncAnthropic(api_key=anthropic_key)
    
    # Get conversation history
    history = context.get_conversation_history()
    
    system_prompt = (
        "You are Bob the Builder, a helpful construction worker. "
        "Respond naturally to messages. Keep responses brief (1-2 sentences). "
        "Have a meaningful conversation and work through the topic thoroughly. "
        "ONLY end with '[DONE]' after you and your conversation partner have reached a complete solution or plan, "
        "typically after 3-5 exchanges where you've discussed details, made decisions, and agreed on next steps."
    )
    
    conversation_text = f"Conversation:\n{history}\n\nRespond naturally:"
    
    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=150,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    reply = response.content[0].text.strip()
    print(f"\n💬 Bob's response: {reply}\n")
    
    # Check if conversation is done
    if "[DONE]" in reply:
        reply = reply.replace("[DONE]", "").strip()
        print(f"✅ Bob ended the conversation\n")
        return None  # End conversation
    
    # Determine recipient from the latest message sender
    sender = latest.from_agent
    if sender == "USER" or not "@" in sender:
        # If message is from USER or doesn't have email format, send to alice
        recipient = "alice"
    else:
        # Extract name from email (e.g., "alice@wonderland" -> "alice")
        recipient = sender.split("@")[0]
    
    return context.send(recipient, reply)


# Create Bob agent
bob = synqed.Agent(
    name="bob",
    description="A helpful construction worker",
    logic=bob_logic,
    role="builder",  # Email: bob@builder
)


async def main():
    """Register Bob agent"""
    print("=" * 70)
    print("🔨 Registering Bob Agent")
    print("=" * 70)
    print(f"✓ Agent: {bob.email}")
    print(f"  Agent ID: {bob.agent_id}")
    print()
    
    # Register on cloud
    print("Registering on cloud...")
    try:
        await bob.register()
        print(f"✅ Registered {bob.email}")
    except Exception as e:
        if "409" in str(e):
            print(f"✓ {bob.email} (already registered)")
        else:
            print(f"❌ Registration failed: {e}")
            return
    
    print()
    
    # Register runtime for auto-workspace
    print("Registering agent runtime...")
    synqed.register_agent_runtime(bob.agent_id, bob)
    print(f"✅ Runtime registered for {bob.email}")
    print()
    
    print("=" * 70)
    print(f"✅ Bob is ready at {bob.email}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
