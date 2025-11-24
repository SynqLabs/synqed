"""
Multi-Agent MCP Demo - Action-Focused Architecture
===================================================

🔧 UPDATED ARCHITECTURE (Anti-Chatter System):

This script demonstrates Synqed's improved multi-agent system that PREVENTS
agent proliferation and verbose coordination, forcing concrete ACTION instead.

KEY IMPROVEMENTS:
1. ✅ Max 3 agents per task (enforced in PlannerLLM)
2. ✅ Structured messages only (no essay-style coordination)
3. ✅ Action reminder at turn 5 (forces MCP tool usage)
4. ✅ Strict routing (rejects nonexistent agent names)
5. ✅ Brief communication (max 2 sentences per message)

WHAT THIS FIXES:
- ❌ NO MORE: 10+ agents created for simple tasks
- ❌ NO MORE: Endless "let me coordinate with..." essays
- ❌ NO MORE: Agents planning for 30+ turns without action
- ❌ NO MORE: Silent fallback to USER for typos

ARCHITECTURE:
- PlannerLLM creates 2-3 agents based on task complexity
- Agents communicate using structured JSON messages
- System enforces action by turn 5 (MCP reminder injected)
- Routing validation prevents hallucinated agent names
- MCP tools available via context for immediate use

Requirements:
    pip install anthropic httpx synqed

Setup:
    1. Deploy the Global MCP Server (synq-mcp-server) to Fly.io
    2. Configure Zoom credentials on the MCP server
    3. Set environment variables:
       export ANTHROPIC_API_KEY="your-key"
       export SYNQ_GLOBAL_MCP_ENDPOINT="https://your-mcp-server.fly.dev"

Usage:
    python examples/mcp/two_agents_zoom_mcp.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add synqed to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "synqed-python" / "src"))

import synqed

# Try to import MCP components
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "synqed-python"))
    from synqed_mcp.client import RemoteMCPClient
    from synqed_mcp.integrate.injector import create_mcp_middleware
    HAS_MCP = True
except ImportError as e:
    print(f"⚠️  MCP not available: {e}")
    HAS_MCP = False

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass


# Track MCP calls
MCP_CALLS = []

def log_mcp_call(agent_name: str, tool: str, arguments: dict, result: dict):
    """Track MCP calls for summary."""
    MCP_CALLS.append({
        "agent": agent_name,
        "tool": tool,
        "arguments": arguments,
        "result": result,
        "status": result.get("status", "unknown")
    })
    status_icon = "✅" if result.get("status") == "success" else "❌"
    print(f"   [MCP] {status_icon} {agent_name} → {tool}")


async def main(user_task: str, max_agent_turns: int = 10):
    """
    Main demonstration function using PlannerLLM to create agents dynamically.
    
    🔧 UPDATED ARCHITECTURE:
    - Maximum 3 agents created (enforced)
    - Brief, structured communication (no essays)
    - Forced action by turn 5 (MCP usage reminder)
    - Routing errors for nonexistent agents
    
    Args:
        user_task: The user's task description
        max_agent_turns: Maximum agent responses before stopping (default: 10)
    """
    print("\n" + "="*80)
    print("🤝 MULTI-AGENT MCP DEMO - ACTION-FOCUSED ARCHITECTURE")
    print("="*80)
    print()
    print("🔧 NEW FEATURES:")
    print("   • Max 3 agents (enforced)")
    print("   • Structured communication only")
    print("   • Action required by turn 5")
    print("   • No hallucinated agent names")
    print("="*80)
    print()
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set!")
        return
    
    # Check MCP
    if not HAS_MCP:
        print("❌ MCP support not available!")
        return
    
    mcp_endpoint = os.getenv("SYNQ_GLOBAL_MCP_ENDPOINT")
    if not mcp_endpoint:
        print("❌ SYNQ_GLOBAL_MCP_ENDPOINT not set!")
        print("Please deploy synq-mcp-server and set the endpoint.")
        return
    
    print("✅ Configuration:")
    print(f"   • API Key: {api_key[:20]}...")
    print(f"   • MCP Endpoint: {mcp_endpoint}")
    print()
    
    # Step 1: Display user task
    print("="*80)
    print("📋 USER TASK")
    print("="*80)
    print(f"{user_task}")
    print("="*80)
    print()
    
    # Step 2: Initialize PlannerLLM
    print("🧠 Initializing PlannerLLM...")
    planner = synqed.PlannerLLM(
        provider="anthropic",
        api_key=api_key,
        model="claude-sonnet-4-20250514"
    )
    print("✓ PlannerLLM initialized")
    print()
    
    # Step 3: PlannerLLM creates agent specifications based on task
    print("🔍 PlannerLLM analyzing task...")
    print("   • Breaking down task requirements")
    print("   • Determining required agent roles")
    print("   • Creating agent specifications")
    print()
    
    task_plan, agent_specs = await planner.plan_task_and_create_agent_specs(
        user_task=user_task,
        agent_provider="anthropic",
        agent_api_key=api_key,
        agent_model="claude-sonnet-4-20250514"
    )
    
    print("✅ Task breakdown created:")
    print(f"   Root: {task_plan.root.description}")
    print(f"   Subtasks: {len(task_plan.root.children)}")
    print()
    
    for i, child in enumerate(task_plan.root.children, 1):
        print(f"   {i}. {child.description}")
        print(f"      Agents: {', '.join(child.required_agents)}")
    print()
    
    print(f"✅ Created {len(agent_specs)} agent specification(s):")
    for spec in agent_specs:
        print(f"   • {spec['name']} - {spec['description']}")
        print(f"     Capabilities: {', '.join(spec['capabilities'])}")
    print()
    
    # Step 4: Create actual Agent instances
    print("👥 Creating Agents from specifications...")
    agents = synqed.create_agents_from_specs(agent_specs)
    
    for agent in agents:
        print(f"   ✓ {agent.email} - {agent.description}")
    print(f"\n✓ Total agents created: {len(agents)}")
    print()
    
    # Step 5: Attach Global MCP Server to all agents
    print("🔧 Attaching Global MCP Server access to all agents...")
    
    # Test MCP connectivity first
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            health_response = await client.get(f"{mcp_endpoint}/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✅ Connected to MCP Server!")
                print(f"   • Status: {health_data.get('status', 'unknown')}")
                
                # List tools
                tools_response = await client.get(f"{mcp_endpoint}/mcp/tools")
                if tools_response.status_code == 200:
                    tools_data = tools_response.json()
                    zoom_tools = [t for t in tools_data.get('tools', []) if t['name'].startswith('zoom.')]
                    print(f"   • Zoom tools available: {len(zoom_tools)}")
                    for tool in zoom_tools:
                        print(f"     - {tool['name']}")
                print()
    except Exception as e:
        print(f"⚠️  Could not connect to MCP Server: {e}")
        print()
    
    # Create MCP middleware
    mcp_middleware = create_mcp_middleware(
        router=None,
        a2a_client=None,
        mode="cloud",
        endpoint=f"{mcp_endpoint}/mcp"
    )
    
    print()
    print(f"✅ MCP middleware created!")
    print("   Will be auto-attached to agents in workspaces")
    print()
    
    # Step 6: Register agents (prototypes, don't attach MCP yet)
    print("📝 Registering agents...")
    for agent in agents:
        synqed.AgentRuntimeRegistry.register(agent.name, agent)
        print(f"  ✓ {agent.name}")
    print()
    
    print("🏗️  Setting up workspace...")
    workspace_manager = synqed.WorkspaceManager(
        workspaces_root=Path("/tmp/synqed_two_agents_zoom_demo")
    )
    
    # 🔧 FIX: Pass MCP middleware to execution engine
    # It will automatically attach to all agents after workspace creation
    execution_engine = synqed.WorkspaceExecutionEngine(
        planner=planner,
        workspace_manager=workspace_manager,
        enable_display=True,
        max_agent_turns=max_agent_turns,
        mcp_middleware=mcp_middleware,
    )
    
    print("✓ Infrastructure configured")
    print()
    
    # Step 7: Execute task plan
    print("="*80)
    print("⚡ EXECUTING TASK PLAN")
    print("="*80)
    print()
    print("Agents will now collaborate to complete the task.")
    print("Watch as they discuss and decide who uses MCP tools!")
    print()
    
    root_workspace, child_workspaces = await execution_engine.execute_task_plan(
        task_plan=task_plan,
        user_task=user_task
    )
    
    print()
    print("="*80)
    print("📊 EXECUTION SUMMARY")
    print("="*80)
    print()
    
    # Show results
    all_workspaces = [root_workspace] + child_workspaces
    for i, workspace in enumerate(all_workspaces, 1):
        transcript = workspace.router.get_transcript()
        print(f"Workspace {i}: {workspace.workspace_id}")
        print(f"  Messages exchanged: {len(transcript)}")
        
        # Show final message to USER
        for msg in reversed(transcript):
            if msg.get("to") == "USER":
                content = msg.get("content", "")
                if content and content != "[startup]":
                    print(f"  Final message: {content[:100]}...")
                    break
        print()
    
    # Show MCP calls
    if MCP_CALLS:
        print(f"Total MCP Calls: {len(MCP_CALLS)}")
        print()
        
        # Group by agent
        by_agent = {}
        for call in MCP_CALLS:
            agent = call['agent']
            if agent not in by_agent:
                by_agent[agent] = []
            by_agent[agent].append(call)
        
        for agent_name, calls in by_agent.items():
            print(f"{agent_name}: {len(calls)} call(s)")
            for call in calls:
                status_icon = "✅" if call["status"] == "success" else "❌"
                print(f"  {status_icon} {call['tool']}: {call['arguments'].get('topic', 'N/A')}")
            print()
    else:
        print("No MCP calls were made during execution.")
        print()
    
    print("="*80)
    print("✅ DEMO COMPLETE!")
    print("="*80)
    print()
    print("🔧 NEW ARCHITECTURE IN ACTION:")
    print(f"  1. ✅ PlannerLLM created {len(agents)} agent(s) (max 3 enforced)")
    print("  2. ✅ Agents used STRUCTURED messages (no essays)")
    print("  3. ✅ MCP tools accessed via context")
    print("  4. ✅ Action reminder at turn 5 if needed")
    print("  5. ✅ Invalid agent names rejected (not silently converted)")
    print()
    print("Key Improvements:")
    print("  • 🚫 No agent proliferation (max 3)")
    print("  • 🚫 No verbose coordination essays")
    print("  • ✅ Early action enforcement (turn 5)")
    print("  • ✅ Strict routing validation")
    print("  • ✅ Brief, structured communication")
    print()
    
    # Cleanup
    print("🧹 Cleaning up workspaces...")
    for workspace in child_workspaces:
        await workspace_manager.destroy_workspace(workspace.workspace_id)
    await workspace_manager.destroy_workspace(root_workspace.workspace_id)
    print("✓ Workspaces cleaned up")
    print()


if __name__ == "__main__":
    # 🔧 UPDATED: Simpler, more action-focused task
    # The new system limits to 3 agents max and forces early action
    user_task = """Create Zoom meetings for our product launch:
1. Team planning meeting - internal discussion (60 minutes)
2. Client presentation - product demo (45 minutes)

Use Zoom MCP tools to create these meetings NOW and provide the meeting details."""
    
    # Alternative task examples (all simplified for action):
    
    # Example 2: Quick meeting setup
    # user_task = """Create these Zoom meetings immediately:
    # 1. Executive sync (Monday 2pm, 90 minutes)
    # 2. Client demo (Friday 3pm, 60 minutes)
    # Provide the meeting links and IDs."""
    
    # Example 3: Event sessions
    # user_task = """Set up 3 Zoom meetings for our virtual conference:
    # - Keynote session (2 hours)
    # - Workshop A (90 minutes)
    # - Workshop B (90 minutes)
    # Create them now and give me the details."""
    
    asyncio.run(main(user_task, max_agent_turns=10))
