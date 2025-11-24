"""
Single Agent Using MCP (Zoom) - Dynamic Agent Creation
=======================================================

This script demonstrates a single AI agent dynamically created with access to
Zoom tools via the Global MCP Server.

The agent is created by PlannerLLM based on the user task, and MCP tools are
available through context rather than hardcoded in the system prompt.

Key Features:
- PlannerLLM analyzes task and creates appropriate agent
- MCP tools attached via middleware (not in system prompt)
- Agent discovers available tools through context
- Follows synqed best practices for agent creation

Requirements:
    pip install anthropic httpx synqed

Setup:
    1. Deploy the Global MCP Server (synq-mcp-server) to Fly.io
    2. Configure Zoom credentials on the MCP server
    3. Set environment variables:
       export ANTHROPIC_API_KEY="your-key"
       export SYNQ_GLOBAL_MCP_ENDPOINT="https://your-mcp-server.fly.dev"

Usage:
    python examples/mcp/single_agent_zoom_mcp.py
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
    Main demonstration function using PlannerLLM to create agent dynamically.
    
    Args:
        user_task: The user's task description
        max_agent_turns: Maximum agent responses before stopping
    """
    print("\n" + "="*80)
    print("🤖 SINGLE AGENT WITH ZOOM MCP - DYNAMIC CREATION")
    print("="*80)
    print()
    print("This demo shows PlannerLLM creating an agent based on the task.")
    print("MCP tools are available through context, not hardcoded.")
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
    print("   • Determining required agent capabilities")
    print("   • Creating agent specification")
    print()
    
    task_plan, agent_specs = await planner.plan_task_and_create_agent_specs(
        user_task=user_task,
        agent_provider="anthropic",
        agent_api_key=api_key,
        agent_model="claude-sonnet-4-20250514"
    )
    
    print(f"✅ Created {len(agent_specs)} agent specification(s):")
    for spec in agent_specs:
        print(f"   • {spec['name']} - {spec['description']}")
        print(f"     Capabilities: {', '.join(spec['capabilities'])}")
    print()
    
    # Step 4: Create actual Agent instance
    print("👥 Creating Agent from specification...")
    agents = synqed.create_agents_from_specs(agent_specs)
    agent = agents[0]  # Use first agent
    print(f"✓ Agent created: {agent.email}")
    print()
    
    # Step 5: Attach MCP middleware
    print("🔧 Attaching Global MCP Server access...")
    
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
    
    # Attach to agent with logging
    mcp_middleware.attach(agent)
    
    # Wrap agent logic to log MCP calls
    if hasattr(agent, 'logic'):
        original_logic = agent.logic
        agent_name = agent.name
        
        async def logged_logic(context):
            # Wrap MCP client with logger
            if hasattr(context, 'mcp'):
                original_mcp = context.mcp
                
                class MCPLogger:
                    async def call_tool(self, tool_name: str, arguments: dict):
                        result = await original_mcp.call_tool(tool_name, arguments)
                        log_mcp_call(agent_name, tool_name, arguments, result)
                        return result
                    
                    def __getattr__(self, name):
                        return getattr(original_mcp, name)
                
                context.mcp = MCPLogger()
            
            return await original_logic(context)
        
        agent.logic = logged_logic
    
    print(f"✅ MCP access enabled for {agent.name}")
    print("   Agent can now discover and use Zoom tools via context.mcp")
    print()
    
    # Step 6: Setup workspace and execute
    print("🏗️  Setting up workspace...")
    workspace_manager = synqed.WorkspaceManager(
        workspaces_root=Path("/tmp/synqed_single_agent_zoom_demo")
    )
    
    # Register agent
    synqed.AgentRuntimeRegistry.register(agent.name, agent)
    
    # Create workspace
    workspace = await workspace_manager.create_workspace(
        task_tree_node=task_plan.root,
        parent_workspace_id=None
    )
    
    print(f"✓ Workspace created: {workspace.workspace_id}")
    print()
    
    # Step 7: Send task to agent
    print("="*80)
    print("⚡ EXECUTING TASK")
    print("="*80)
    print()
    
    await workspace.route_message(
        "USER",
        agent.name,
        user_task,
        manager=workspace_manager
    )
    
    # Execute agent turns
    execution_engine = synqed.WorkspaceExecutionEngine(
        planner=planner,
        workspace_manager=workspace_manager,
        enable_display=True,
        max_agent_turns=max_agent_turns,
    )
    
    execution_engine.schedule_workspace(workspace.workspace_id)
    await execution_engine.run_global_scheduler()
    
    print()
    print("="*80)
    print("📊 EXECUTION SUMMARY")
    print("="*80)
    print()
    
    # Show transcript
    transcript = workspace.router.get_transcript()
    print(f"Total messages: {len(transcript)}")
    print()
    
    # Show final message to USER
    for msg in reversed(transcript):
        if msg.get("to") == "USER":
            content = msg.get("content", "")
            if content and content != "[startup]":
                print(f"Final response:")
                print(f"{content}")
                break
    print()
    
    # Show MCP calls
    if MCP_CALLS:
        print(f"MCP Calls Made: {len(MCP_CALLS)}")
        for call in MCP_CALLS:
            status_icon = "✅" if call["status"] == "success" else "❌"
            print(f"  {status_icon} {call['tool']}")
            if call["status"] != "success":
                print(f"     Error: {call['result'].get('error', 'unknown')}")
        print()
    
    print("="*80)
    print("✅ DEMO COMPLETE!")
    print("="*80)
    print()
    print("What happened:")
    print("  1. ✅ PlannerLLM analyzed task and created agent specification")
    print("  2. ✅ Agent created dynamically from specification")
    print("  3. ✅ MCP middleware attached (tools available via context)")
    print("  4. ✅ Agent executed task using Zoom MCP tools")
    print("  5. ✅ Tools discovered at runtime, not hardcoded")
    print()
    print("Key Features:")
    print("  • Dynamic agent creation based on task")
    print("  • MCP tools via context, not system prompt")
    print("  • Follows synqed best practices")
    print("  • Scalable pattern for complex systems")
    print()
    
    # Cleanup
    await workspace_manager.destroy_workspace(workspace.workspace_id)


if __name__ == "__main__":
    # Example task - PlannerLLM will create appropriate agent
    user_task = """I need help managing Zoom meetings. Please:
1. Create a team standup meeting for tomorrow at 10am (30 minutes)
2. Show me my upcoming meetings
3. Provide a summary of scheduled meetings"""
    
    asyncio.run(main(user_task, max_agent_turns=10))

