"""
Parallel Workspaces Demo: 3 Simultaneous Email Conversations

This script demonstrates running 3 parallel workspaces with email addressing:
1. alice@wonderland ↔ bob@builder (discussing treehouse construction)
2. alice@wonderland ↔ charlie@design (discussing aesthetic choices)
3. bob@builder ↔ charlie@design (discussing materials and design)

Each workspace operates independently and processes messages in parallel.
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
from agent_charlie import charlie


async def main(max_agent_turns: int = 8):
    """
    Run 3 parallel email conversations in separate workspaces.
    
    Args:
        max_agent_turns: Maximum number of agent responses per workspace (default: 8)
    """
    print("\n" + "="*80)
    print("🚀 PARALLEL WORKSPACES DEMO: 3 Simultaneous Email Conversations")
    print("="*80)
    print()
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set!")
        return
    
    agents = [alice, bob, charlie]
    print("📧 Agents:")
    for agent in agents:
        print(f"  ✓ {agent.email}")
    print()
    
    # Register agents on cloud
    print("Registering agents on cloud...")
    for agent in agents:
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
    for agent in agents:
        synqed.register_agent_runtime(agent.agent_id, agent)
        synqed.AgentRuntimeRegistry.register(agent.name, agent)
        print(f"✓ Runtime registered for {agent.email}")
    
    print()
    
    # Configure auto-workspace manager
    print(f"Configuring auto-workspaces (max_agent_turns={max_agent_turns})...")
    auto_ws_manager = synqed.get_auto_workspace_manager()
    
    # Create execution engine for auto-workspaces
    execution_engine = synqed.WorkspaceExecutionEngine(
        planner=None,
        workspace_manager=auto_ws_manager.workspace_manager,
        enable_display=False,  # Agents print their own responses
        max_agent_turns=max_agent_turns,
    )
    print(f"✓ Auto-workspace configured\n")
    
    # Define 3 parallel conversations
    conversations = [
        {
            "name": "Workspace 1: Treehouse Construction",
            "sender": alice,
            "recipient": bob,
            "thread_id": "treehouse-construction",
            "message": "Hi Bob! I need your help building a magical treehouse in Wonderland. What materials should we use?",
            "emoji": "🏗️"
        },
        {
            "name": "Workspace 2: Design Aesthetics",
            "sender": alice,
            "recipient": charlie,
            "thread_id": "design-aesthetics",
            "message": "Hey Charlie! I'm working on a treehouse project. Can you help me design something whimsical and colorful?",
            "emoji": "🎨"
        },
        {
            "name": "Workspace 3: Material Design Collaboration",
            "sender": bob,
            "recipient": charlie,
            "thread_id": "material-design-collab",
            "message": "Charlie, I'm building a treehouse. What materials would work best for a whimsical design?",
            "emoji": "🤝"
        }
    ]
    
    print("="*80)
    print("🎬 STARTING 3 PARALLEL CONVERSATIONS")
    print("="*80)
    print()
    
    # Display the conversations that will be started
    for conv in conversations:
        print(f"{conv['emoji']} {conv['name']}")
        print(f"   {conv['sender'].email} → {conv['recipient'].email}")
        print(f"   Message: \"{conv['message']}\"")
        print()
    
    try:
        # Create workspaces and prepare initial messages
        workspaces = []
        
        for conv in conversations:
            print(f"Setting up {conv['name']}...")
            
            # Send email through cloud
            await conv['sender'].send(
                to=conv['recipient'].email,
                content=conv['message'],
                via_cloud=True,
            )
            
            # Get or create workspace via auto-workspace manager
            workspace = await auto_ws_manager.get_or_create_workspace(
                sender=conv['sender'].agent_id,
                recipient=conv['recipient'].agent_id,
                thread_id=conv['thread_id'],
            )
            
            if not workspace:
                print(f"❌ Failed to create workspace for {conv['name']}")
                continue
            
            print(f"✓ Created workspace: {workspace.workspace_id}")
            
            # Route initial message
            await workspace.route_message(
                "USER",
                conv['sender'].name,
                conv['message'],
                manager=auto_ws_manager.workspace_manager
            )
            
            workspaces.append({
                "workspace": workspace,
                "info": conv,
            })
        
        print()
        print("="*80)
        print(f"⚡ EXECUTING {len(workspaces)} WORKSPACES IN PARALLEL")
        print("="*80)
        print()
        
        # Execute all workspaces in parallel
        tasks = []
        for ws_data in workspaces:
            workspace = ws_data["workspace"]
            info = ws_data["info"]
            
            print(f"{info['emoji']} Starting: {info['name']} (ID: {workspace.workspace_id})")
            
            # Create a task for each workspace execution
            task = asyncio.create_task(
                execution_engine.run(workspace.workspace_id)
            )
            tasks.append({
                "task": task,
                "info": info,
            })
        
        print()
        print("⏳ Processing all conversations in parallel...")
        print()
        
        # Wait for all tasks to complete
        results = await asyncio.gather(
            *[t["task"] for t in tasks],
            return_exceptions=True
        )
        
        # Report results
        print()
        print("="*80)
        print("📊 RESULTS SUMMARY")
        print("="*80)
        print()
        
        for i, (result, task_data) in enumerate(zip(results, tasks)):
            info = task_data["info"]
            if isinstance(result, Exception):
                print(f"❌ {info['name']}")
                print(f"   Error: {result}")
            else:
                print(f"✅ {info['name']}")
                print(f"   {info['sender'].email} ↔ {info['recipient'].email}")
        
        print()
        print("="*80)
        print("🎉 ALL PARALLEL CONVERSATIONS COMPLETE!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # You can customize max_agent_turns here
    asyncio.run(main(max_agent_turns=8))

