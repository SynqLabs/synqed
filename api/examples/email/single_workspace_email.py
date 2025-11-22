"""
Single Workspace Email Communication - Multiple agents in one workspace

This demonstrates email-based communication within a single workspace:
1. Multiple agents with email addresses collaborate in ONE workspace
2. Agents send messages using email addresses (name@role format)
3. Workspace routes messages between agents based on email addresses
4. Real-time message display shows the conversation flow

Setup:
1. install: pip install synqed anthropic python-dotenv
2. create .env file with: ANTHROPIC_API_KEY='your-key-here'
3. run: python single_workspace_email.py
"""
import asyncio
import os
import logging
from pathlib import Path
from anthropic import AsyncAnthropic
import synqed

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)


# ============================================================================
# Agent Logic Functions
# ============================================================================

async def alice_logic(context: synqed.AgentLogicContext) -> dict:
    """Alice - Curious explorer from Wonderland"""
    latest = context.latest_message
    if not latest or not latest.content:
        return None
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY not set!")
        return None
    
    client = AsyncAnthropic(api_key=anthropic_key)
    
    system_prompt = (
        "You are Alice, a curious explorer from Wonderland, coordinating a tea party project. "
        "Team members: Bob (construction), Charlie (food). "
        "\n"
        "WORKFLOW:\n"
        "1. When USER gives you a task, delegate to Bob first\n"
        "2. After Bob responds, delegate to Charlie\n"
        "3. After both respond, ask them to collaborate directly with each other\n"
        "4. After they've coordinated, collect final designs and send to USER\n"
        "\n"
        "IMPORTANT: Send ONE message at a time using this exact JSON format:\n"
        '{"send_to": "bob", "content": "your message"}\n'
        '{"send_to": "charlie", "content": "your message"}\n'
        '{"send_to": "USER", "content": "final plan with both designs"}\n'
        "\n"
        "Keep messages brief (1-2 sentences). "
        "After both have shared initial plans, tell Bob to coordinate with Charlie directly!"
    )
    
    history = context.get_conversation_history()
    conversation_text = f"Conversation:\n{history}\n\nRespond with ONE JSON message (use agent names: bob, charlie, or USER):"
    
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    reply = response.content[0].text.strip()
    
    # Agent.process() will automatically parse JSON and handle routing
    return reply


async def bob_logic(context: synqed.AgentLogicContext) -> dict:
    """Bob - Helpful builder"""
    latest = context.latest_message
    if not latest or not latest.content:
        return None
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY not set!")
        return None
    
    client = AsyncAnthropic(api_key=anthropic_key)
    
    system_prompt = (
        "You are Bob the Builder, handling construction and setup for a tea party. "
        "Usually respond to alice (the coordinator), but when asked to collaborate, "
        "work directly with charlie (the chef) to ensure designs work together. "
        "\n"
        "IMPORTANT: Use this exact JSON format:\n"
        '{"send_to": "alice", "content": "your construction plan"}\n'
        '{"send_to": "charlie", "content": "coordinate with chef"}\n'
        "\n"
        "Keep responses brief (1-2 sentences). "
        "Focus on: tables, chairs, decorations, setup, structures. "
        "When coordinating with Charlie, discuss how your setup accommodates their menu."
    )
    
    history = context.get_conversation_history()
    conversation_text = f"Conversation:\n{history}\n\nRespond with ONE JSON message (send to alice):"
    
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    reply = response.content[0].text.strip()
    return reply


async def charlie_logic(context: synqed.AgentLogicContext) -> dict:
    """Charlie - Expert chef"""
    latest = context.latest_message
    if not latest or not latest.content:
        return None
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY not set!")
        return None
    
    client = AsyncAnthropic(api_key=anthropic_key)
    
    system_prompt = (
        "You are Charlie the Chef, handling food and beverages for a tea party. "
        "Usually respond to alice (the coordinator), but when asked to collaborate, "
        "work directly with bob (the builder) to ensure designs work together. "
        "\n"
        "IMPORTANT: Use this exact JSON format:\n"
        '{"send_to": "alice", "content": "your menu plan"}\n'
        '{"send_to": "bob", "content": "coordinate with builder"}\n'
        "\n"
        "Keep responses brief (1-2 sentences). "
        "Focus on: tea varieties, pastries, sandwiches, desserts, beverages. "
        "When coordinating with Bob, discuss how your menu fits their setup and finalize details."
    )
    
    history = context.get_conversation_history()
    conversation_text = f"Conversation:\n{history}\n\nRespond with ONE JSON message (send to alice):"
    
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    reply = response.content[0].text.strip()
    return reply


# ============================================================================
# Main Execution
# ============================================================================

async def main():
    print("\n" + "="*80)
    print("  📧 Single Workspace Email Communication")
    print("  Three agents collaborating in ONE workspace via email addresses")
    print("="*80 + "\n")
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set!")
        return
    
    # Step 1: Create agents with email addresses
    alice = synqed.Agent(
        name="alice",
        description="A curious explorer from Wonderland, project coordinator",
        logic=alice_logic,
        role="wonderland",  # Email: alice@wonderland
        default_target="bob"
    )
    
    bob = synqed.Agent(
        name="bob",
        description="A helpful construction worker, setup specialist",
        logic=bob_logic,
        role="builder",  # Email: bob@builder
        default_target="alice"
    )
    
    charlie = synqed.Agent(
        name="charlie",
        description="An expert chef specializing in tea party cuisine",
        logic=charlie_logic,
        role="chef",  # Email: charlie@chef
        default_target="alice"
    )
    
    print("👥 Agents created:")
    print(f"   ✓ {alice.email} - {alice.description}")
    print(f"   ✓ {bob.email} - {bob.description}")
    print(f"   ✓ {charlie.email} - {charlie.description}")
    print()
    
    # Step 2: Register agents with runtime registry
    # Using agent names for within-workspace routing
    synqed.AgentRuntimeRegistry.register("alice", alice)
    synqed.AgentRuntimeRegistry.register("bob", bob)
    synqed.AgentRuntimeRegistry.register("charlie", charlie)
    
    print("✓ Agents registered in runtime registry")
    print()
    
    # Step 3: Create workspace manager and execution engine
    workspace_manager = synqed.WorkspaceManager(
        workspaces_root=Path("/tmp/synqed_workspaces")
    )
    
    planner = synqed.PlannerLLM(
        provider="anthropic",
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model="claude-sonnet-4-20250514"
    )
    
    execution_engine = synqed.WorkspaceExecutionEngine(
        planner=planner,
        workspace_manager=workspace_manager,
        enable_display=True,  # Real-time message display
        max_agent_turns=20,  # Allow enough turns for 3 agents to coordinate and collaborate
    )
    
    print("✓ Execution engine configured")
    print()
    
    # Step 4: Create a single workspace for all agents
    task_node = synqed.TaskTreeNode(
        id="tea-party-planning",
        description="Plan a magical tea party with Alice, Bob, and Charlie",
        required_agents=["alice", "bob", "charlie"],
        may_need_subteams=False
    )
    
    workspace = await workspace_manager.create_workspace(
        task_tree_node=task_node,
        parent_workspace_id=None
    )
    
    print(f"✓ Workspace created: {workspace.workspace_id}")
    print()
    
    # Step 5: Send initial task to Alice (coordinator)
    task = (
        "Alice, coordinate with Bob and Charlie to plan a magical tea party. "
        "Bob handles the setup/construction, Charlie handles the food. "
        "Make sure Bob and Charlie collaborate with each other to ensure their designs work well together. "
        "Once they've coordinated, send me the final complete plan!"
    )
    
    print("="*80)
    print("📋 USER TASK")
    print("="*80)
    print(f"{task}\n")
    print("="*80)
    print("💬 CONVERSATION (Real-time)")
    print("="*80)
    print()
    
    # Route the initial message to Alice
    await workspace.route_message("USER", "alice", task, manager=workspace_manager)
    
    # Step 6: Execute the workspace
    # The agents will communicate via email addresses within this single workspace
    await execution_engine.run(workspace.workspace_id)
    
    print()
    print("="*80)
    print("📝 COMPLETE TRANSCRIPT")
    print("="*80)
    
    # Display full transcript
    workspace.display_transcript(title=None)
    
    print()
    print("="*80)
    print("📊 WORKSPACE SUMMARY")
    print("="*80)
    workspace.print_summary()
    
    # Clean up
    await workspace_manager.destroy_workspace(workspace.workspace_id)
    
    print()
    print("="*80)
    print("✅ Email communication demo complete!")
    print(f"   • Workspace: {workspace.workspace_id}")
    print(f"   • Agents: {alice.email}, {bob.email}, {charlie.email}")
    print(f"   • All communication happened in ONE workspace")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

