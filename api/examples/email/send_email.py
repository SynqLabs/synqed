"""
Send Email: Alice → Bob

Simple script that sends an email from Alice to Bob via email addresses.
The conversation continues automatically until the agents decide to end it.
Email communication triggers automatic workspace creation in the background.
"""

import asyncio
import os
from pathlib import Path
import synqed

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# Import agents
from agent_alice import alice
from agent_bob import bob


async def main(max_agent_turns: int = 10):
    """
    Send an email from Alice to Bob via email addresses.
    
    Args:
        max_agent_turns: Maximum number of agent responses before stopping (default: 10)
    """
    print("\n" + "="*70)
    print("📧 EMAIL CONVERSATION: alice@wonderland ↔ bob@builder")
    print("="*70)
    print()
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set!")
        return
    
    print(f"✓ Using {alice.email}")
    print(f"✓ Using {bob.email}")
    print()
    
    # Register agents on cloud
    print("Registering agents on cloud...")
    for agent in [alice, bob]:
        try:
            await agent.register()
            print(f"✓ Registered {agent.email}")
        except Exception as e:
            if "409" in str(e):
                print(f"✓ {agent.email} (already registered)")
            else:
                print(f"❌ Registration failed: {e}")
                return
    
    print()
    
    # Register agent runtimes (enables auto-workspace creation)
    print("Registering agent runtimes...")
    synqed.register_agent_runtime(alice.agent_id, alice)
    synqed.register_agent_runtime(bob.agent_id, bob)
    
    # Also register with AgentRuntimeRegistry for workspace creation
    synqed.AgentRuntimeRegistry.register(alice.name, alice)
    synqed.AgentRuntimeRegistry.register(bob.name, bob)
    
    print(f"✓ Registered runtime for {alice.email}")
    print(f"✓ Registered runtime for {bob.email}")
    print()
    
    # Configure auto-workspace manager to use execution engine
    print(f"Configuring auto-workspace with max_agent_turns={max_agent_turns}...")
    auto_ws_manager = synqed.get_auto_workspace_manager()
    
    # Create execution engine for auto-workspaces
    execution_engine = synqed.WorkspaceExecutionEngine(
        planner=None,
        workspace_manager=auto_ws_manager.workspace_manager,
        enable_display=False,  # Agents print their own responses
        max_agent_turns=max_agent_turns,
    )
    print(f"✓ Auto-workspace configured\n")
    
    # Start conversation
    message = "Can you help me build a magical treehouse in Wonderland?"
    
    print("="*70)
    print("🎬 STARTING CONVERSATION VIA EMAIL")
    print("="*70)
    print(f"\n👤 USER → {alice.email}: \"{message}\"\n")
    
    try:
        # Send email from Alice to Bob
        # This triggers automatic workspace creation
        result = await alice.send(
            to=bob.email,
            content=message,
            via_cloud=True,
        )
        
        print(f"✅ Email sent! Message ID: {result.get('message_id', 'N/A')}")
        print()
        print("Processing conversation through auto-workspace...\n")
        
        # Simulate what the inbox worker would do:
        # Create auto-workspace and route the initial message
        envelope = {
            "thread_id": "conversation-alice-bob",
            "role": "user",
            "content": message,
        }
        
        # Get or create workspace via auto-workspace manager
        workspace = await auto_ws_manager.get_or_create_workspace(
            sender=alice.agent_id,
            recipient=bob.agent_id,
            thread_id="conversation-alice-bob",
        )
        
        if not workspace:
            print("❌ Failed to create auto-workspace")
            return
        
        print(f"✓ Auto-workspace created: {workspace.workspace_id}")
        print()
        
        # Route initial message
        await workspace.route_message("USER", alice.name, message, manager=auto_ws_manager.workspace_manager)
        
        # Execute the workspace with max_agent_turns
        print(f"Executing conversation (max {max_agent_turns} agent turns)...\n")
        await execution_engine.run(workspace.workspace_id)
        
        print()
        print("="*70)
        print("✅ CONVERSATION COMPLETE")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # You can customize max_agent_turns here
    asyncio.run(main(max_agent_turns=10))


if __name__ == "__main__":
    asyncio.run(main())

