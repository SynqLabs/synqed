"""
Single Workspace Email Communication - PlannerLLM-driven coordination

This demonstrates how PlannerLLM breaks down tasks and coordinates agents:
1. USER provides a task description
2. PlannerLLM analyzes it and creates a hierarchical task breakdown
3. PlannerLLM determines which agents are needed
4. Framework creates workspace and routes messages based on the plan
5. Agents collaborate using GLOBAL INTERACTION PROTOCOL

Key Architecture:
- PlannerLLM does the delegation and task breakdown (NOT Alice!)
- Alice, Bob, Charlie are peer specialists (no coordinator role)
- Each agent has specific capabilities and responds to messages
- Shared plan document accessible via context.shared_plan
- Agents can broadcast to ALL peers using send_to: "ALL"

Framework Handles:
- Task breakdown and delegation (via PlannerLLM)
- Message routing based on task plan
- Protocol guides agent-to-agent communication
- No hardcoded coordinator logic in agents

Setup:
1. install: pip install synqed anthropic python-dotenv
2. create .env file with: ANTHROPIC_API_KEY='your-key-here'
3. run: python single_workspace.py
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
# Shared Agent Logic Helper
# ============================================================================

async def create_agent_response(
    context: synqed.AgentLogicContext,
    agent_name: str,
    role: str,
    capabilities: str,
    custom_instructions: str,
    max_tokens: int = 500
) -> dict:
    """Shared logic for all agents - DRY principle."""
    latest = context.latest_message
    if not latest or not latest.content:
        return None
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY not set!")
        return None
    
    client = AsyncAnthropic(api_key=anthropic_key)
    
    # Get protocol (excludes current agent from team roster)
    protocol = synqed.get_interaction_protocol(exclude_agent=agent_name)
    
    system_prompt = f"""{protocol}

YOUR ROLE: {agent_name} ({role})
YOUR CAPABILITIES: {capabilities}

{custom_instructions}
"""
    
    history = context.get_conversation_history(workspace_wide=True)
    plan_context = f"\n\nShared Plan:\n{context.shared_plan}" if context.shared_plan else ""
    
    conversation_text = f"Conversation:\n{history}{plan_context}\n\nRespond with JSON:"
    
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    return response.content[0].text.strip()


# ============================================================================
# Agent Logic Functions
# ============================================================================

async def alice_logic(context: synqed.AgentLogicContext) -> dict:
    """Alice - Curious explorer from Wonderland, decorations specialist"""
    return await create_agent_response(
        context=context,
        agent_name="alice",
        role="wonderland",
        capabilities="decorations, aesthetics, party theme, invitations, color schemes",
        custom_instructions="""You handle decorations, invitations, and the overall aesthetic theme.

WORKFLOW:
1. When you receive a subtask from USER, coordinate with teammates FIRST
2. Use send_to: "ALL" to share your plans with bob and charlie together
3. Read their responses and refine your approach
4. ONLY after alignment, send final results to USER with send_to: "USER"

Focus areas: color schemes, decorations, invitations, party favors, aesthetic coordination."""
    )


async def bob_logic(context: synqed.AgentLogicContext) -> dict:
    """Bob - Helpful builder, setup specialist"""
    return await create_agent_response(
        context=context,
        agent_name="bob",
        role="builder",
        capabilities="construction, setup, furniture arrangement, venue setup, structures",
        custom_instructions="""You handle physical setup and construction for the tea party.

WORKFLOW:
1. When you receive a subtask from USER, coordinate with teammates FIRST
2. Use send_to: "ALL" to share your setup plans with alice and charlie together
3. Read their responses to align decorations and menu needs with your setup
4. ONLY after alignment, send final results to USER with send_to: "USER"

Focus areas: tables, chairs, furniture arrangement, venue setup, structures."""
    )


async def charlie_logic(context: synqed.AgentLogicContext) -> dict:
    """Charlie - Expert chef, food specialist"""
    return await create_agent_response(
        context=context,
        agent_name="charlie",
        role="chef",
        capabilities="menu planning, food preparation, beverage selection, tea varieties, pastries",
        custom_instructions="""You handle food and beverages for the tea party.

WORKFLOW:
1. When you receive a subtask from USER, coordinate with teammates FIRST
2. Use send_to: "ALL" to share your menu ideas with alice and bob together
3. Read their responses to align menu with decorations and setup
4. ONLY after alignment, send final results to USER with send_to: "USER"

Focus areas: tea varieties, pastries, sandwiches, desserts, beverages, menu planning."""
    )


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
    
    # Step 1: Create agents with email addresses and metadata
    alice = synqed.Agent(
        name="alice",
        description="A curious explorer from Wonderland, decorations and aesthetics specialist",
        logic=alice_logic,
        role="wonderland",
        default_target="USER",
        capabilities=["decorations", "aesthetics", "party theme", "invitations"],
        default_coordination="broadcast"  # Prefer ALL over individual messages
    )
    
    bob = synqed.Agent(
        name="bob",
        description="A helpful construction worker, setup specialist",
        logic=bob_logic,
        role="builder",
        default_target="USER",
        capabilities=["construction", "setup", "furniture arrangement"],
        default_coordination="broadcast"
    )
    
    charlie = synqed.Agent(
        name="charlie",
        description="An expert chef specializing in tea party cuisine",
        logic=charlie_logic,
        role="chef",
        default_target="USER",
        capabilities=["menu planning", "food preparation", "beverage selection"],
        default_coordination="broadcast"
    )
    
    print("👥 Agents created:")
    print(f"   ✓ {alice.email} - {alice.description}")
    print(f"   ✓ {bob.email} - {bob.description}")
    print(f"   ✓ {charlie.email} - {charlie.description}")
    print()
    
    # Step 2: Register agents with runtime registry
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
        enable_display=True,
        max_agent_turns=15,  # Reduced - broadcast reduces turn count needed
    )
    
    print("✓ Execution engine configured")
    print()
    
    # Step 4: Use PlannerLLM to break down the user task
    user_task = "Plan a magical tea party"
    
    print("📋 USER TASK")
    print("="*80)
    print(f"{user_task}\n")
    print("="*80)
    print()
    
    print("🤔 PlannerLLM is analyzing the task and creating delegation plan...")
    
    task_plan = await planner.plan_task(user_task)
    
    print("✓ PlannerLLM created task breakdown:")
    print(f"   Root task: {task_plan.root.description}")
    print(f"   Required agents: {task_plan.root.required_agents}")
    if task_plan.root.children:
        print(f"   Subtasks: {len(task_plan.root.children)}")
        for i, child in enumerate(task_plan.root.children, 1):
            agents = ", ".join(child.required_agents) if child.required_agents else "none"
            print(f"     {i}. {child.description} [{agents}]")
    print()
    
    # Step 5: Create workspace - aggregate all agents for single workspace mode
    if task_plan.root.children:
        all_agents = set(task_plan.root.required_agents or [])
        for child in task_plan.root.children:
            all_agents.update(child.required_agents or [])
        task_plan.root.required_agents = list(all_agents)
        print(f"✓ Aggregated all agents for single workspace: {task_plan.root.required_agents}")
    
    workspace = await workspace_manager.create_workspace(
        task_tree_node=task_plan.root,
        parent_workspace_id=None
    )
    
    print(f"✓ Workspace created: {workspace.workspace_id}")
    print(f"   Agents in workspace: {list(workspace.agents.keys())}")
    print()
    
    # Step 6: Send subtasks to appropriate agents
    print("="*80)
    print("💬 AGENT CONVERSATION (Real-time)")
    print("="*80)
    print()
    
    if task_plan.root.children:
        print(f"📤 Distributing {len(task_plan.root.children)} subtasks to agents...\n")
        for child in task_plan.root.children:
            subtask_description = child.description
            assigned_agents = child.required_agents
            
            for agent_name in assigned_agents:
                if agent_name in workspace.agents:
                    subtask_message = f"{user_task}\n\nYour subtask: {subtask_description}"
                    await workspace.route_message(
                        "USER",
                        agent_name,
                        subtask_message,
                        manager=workspace_manager
                    )
                    print(f"   Sent subtask to {agent_name}: {subtask_description}")
        print()
    else:
        print(f"📤 Sending task to all agents...\n")
        for agent_name in task_plan.root.required_agents:
            if agent_name in workspace.agents:
                await workspace.route_message(
                    "USER",
                    agent_name,
                    user_task,
                    manager=workspace_manager
                )
    
    # Step 7: Execute the workspace
    await execution_engine.run(workspace.workspace_id)
    
    print()
    print("="*80)
    print("📝 COMPLETE TRANSCRIPT")
    print("="*80)
    
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
