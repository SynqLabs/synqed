"""
Universal Substrate Demo - Mixing Local and Remote A2A Agents

HIERARCHY DIAGRAM:
┌────────────────────────────────────────────────────────────────┐
│ SYNQED WORKSPACE (Single workspace with mixed agents)          │
│                                                                │
│  ┌────────────────┐                                            │
│  │  Coordinator   │  ◄─── Local Synqed Agent (in-memory)       │
│  │  (Local)       │                                            │
│  └───┬────────────┘                                            │
│      │ delegates                                               │
│      ├──────────┬─────────────────┐                            │
│      │          │                 │                            │
│      ▼          ▼                 ▼                            │
│  ┌────────┐  ┌────────┐  ┌──────────────────┐                  │
│  │ Local  │  │ Local  │  │ RemoteCodeAgent  │                  │
│  │ Writer │  │ (soon) │  │ (Remote A2A)     │                  │
│  │        │  │        │  │                  │                  │
│  └────────┘  └────────┘  └────────┬─────────┘                  │
│     ▲                              │                           │
│     │                              │ HTTP call                 │
│  Local                             │ (A2A protocol)            │
│  Synqed                            │                           │
│  Agent                             │                           │
└────────────────────────────────────┼───────────────────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────────┐
                    │ A2A Agent Server                   │
                    │ (http://localhost:8001)            │
                    │                                    │
                    │ Built with: a2a-python SDK         │
                    │ NOT Synqed - completely separate!  │
                    │                                    │
                    │ Endpoints:                         │
                    │ • /.well-known/agent-card.json     │
                    │ • POST / (JSON-RPC)                │
                    └────────────────────────────────────┘

MESSAGE FLOW:
1. USER → Coordinator (in-memory, local Synqed agent)
2. Coordinator → LocalWriter (in-memory, local Synqed agent)
3. LocalWriter → Coordinator (in-memory)
4. Coordinator → RemoteCodeAgent (HTTP POST to localhost:8001 via A2A)
5. RemoteCodeAgent → Coordinator (HTTP response via A2A)
6. Coordinator → USER (final result)

KEY INSIGHT: Local and Remote agents coexist in the SAME workspace!
Synqed routes transparently - agents don't know if peers are local or remote.

This example demonstrates Synqed as a UNIVERSAL SUBSTRATE for AI agents.

Key Concept:
- Synqed doesn't wrap agents from different ecosystems
- Synqed provides the ROUTING INFRASTRUCTURE that any A2A agent can plug into
- As long as an agent speaks A2A protocol, it can join a Synqed workspace

In this demo:
- Local agents: Built directly with Synqed (in-memory routing)
- Remote A2A agents: Built with a2a-python SDK, running as separate server

The remote agent:
- Built using a2a-python SDK (NOT Synqed)
- Runs as a separate HTTP server
- Exposes A2A protocol endpoints
- Synqed routes to it via RemoteA2AAgent

Setup:
1. pip install synqed anthropic aiohttp python-dotenv a2a-sdk
2. Create .env with: ANTHROPIC_API_KEY='your-key-here'
3. Run: python universal_substrate_demo.py
"""

import asyncio
import os
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv
import synqed

# Load environment
load_dotenv()

# ============================================================================
# Part 1: Local Agents (built with Synqed)
# ============================================================================

async def coordinator_logic(context: synqed.AgentLogicContext) -> dict:
    """
    Local coordinator agent - routes work to local and remote agents.
    """
    import anthropic
    
    latest = context.latest_message
    if not latest:
        return context.build_response("USER", "Coordinator ready!")
    
    # Get conversation history
    history = context.get_conversation_history()
    
    # Check if we've received work from agents
    if latest.from_agent == "LocalWriter":
        # We got a story from LocalWriter, send it to RemoteCodeAgent for review
        return context.build_response(
            "RemoteCodeAgent",
            f"Please review this story for code quality concepts and best practices:\n\n{latest.content}"
        )
    elif latest.from_agent == "RemoteCodeAgent":
        # We got review from RemoteCodeAgent, synthesize and send to USER
        return context.build_response(
            "USER",
            f"Here's the final result:\n\nStory: [created by LocalWriter]\n\nReview: {latest.content}"
        )
    
    # Initial request from USER - delegate to LocalWriter
    # Use LLM to understand the request
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    prompt = f"""You are a Coordinator agent. The user wants you to write a story and then have it reviewed.

User request: {latest.content}

Delegate to LocalWriter to create the story. Be specific about what you want.

Return JSON: {{"send_to": "LocalWriter", "content": "Your delegation message"}}"""
    
    response = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text.strip()


async def local_writer_logic(context: synqed.AgentLogicContext) -> dict:
    """
    Local writer agent - creates written content.
    """
    import anthropic
    
    latest = context.latest_message
    if not latest:
        return context.build_response("Coordinator", "LocalWriter ready!")
    
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    prompt = f"""You are a creative writer agent.

Task: {latest.content}

Write a short, creative response (2-3 paragraphs). When done, send it back to the Coordinator.

Return JSON: {{"send_to": "Coordinator", "content": "Your written content"}}"""
    
    response = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text.strip()


# ============================================================================
# Part 2: Start Real A2A Agent (built with a2a-python SDK)
# ============================================================================

def start_a2a_agent_server():
    """
    Start the Code Review A2A Agent as a background process.
    
    This agent is built with a2a-python SDK (NOT Synqed).
    It's a completely separate server that happens to speak A2A protocol.
    
    Returns:
        subprocess.Popen: The running server process
    """
    print("🌍 Starting Code Review A2A Agent (built with a2a-python SDK)...")
    print("   This is a REAL A2A agent, not a Synqed agent!")
    print("   Built with: a2a-python SDK")
    print("   Running at: http://localhost:8001")
    print("")
    
    # Get the path to the A2A agent file
    agent_file = Path(__file__).parent / "code_review_a2a_agent.py"
    
    # Start the A2A agent as a background process
    process = subprocess.Popen(
        ["python", str(agent_file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    print("   Waiting for A2A agent to start...")
    time.sleep(3)
    
    print("✅ A2A agent started at http://localhost:8001\n")
    return process


# ============================================================================
# Main Demo
# ============================================================================

async def main():
    print("\n" + "="*80)
    print("  🌐 UNIVERSAL SUBSTRATE DEMO")
    print("  Synqed routes to ANY agent that speaks A2A protocol")
    print("="*80 + "\n")
    
    # Step 0: Start the real A2A agent server
    a2a_server_process = None
    try:
        a2a_server_process = start_a2a_agent_server()
        
        # Step 1: Create local agents (built with Synqed)
        print("📍 Step 1: Creating LOCAL agents (built with Synqed)...")
        
        coordinator = synqed.Agent(
            name="Coordinator",
            description="Coordinates between local and remote agents",
            logic=coordinator_logic,
            default_target="USER"
        )
        
        local_writer = synqed.Agent(
            name="LocalWriter",
            description="Local writer agent",
            logic=local_writer_logic,
            default_target="Coordinator"
        )
        
        print("✅ Created 2 local agents: Coordinator, LocalWriter\n")
        
        # Step 2: Register remote A2A agent with Synqed
        print("🌍 Step 2: Registering REMOTE A2A agent with Synqed...")
        print("   Agent URL: http://localhost:8001")
        print("   Built with: a2a-python SDK (NOT Synqed)")
        print("   Transport: JSON-RPC")
        print("")
        
        # Register local agents
        synqed.AgentRuntimeRegistry.register("Coordinator", coordinator)
        synqed.AgentRuntimeRegistry.register("LocalWriter", local_writer)
        
        # Register the REAL remote A2A agent
        synqed.AgentRuntimeRegistry.register_remote(
            role="RemoteCodeAgent",
            url="http://localhost:8001",
            name="Code Review Agent",
            transport="JSONRPC",
            description="Remote code review agent built with A2A SDK"
        )
        
        print("✅ Registered remote A2A agent: RemoteCodeAgent\n")
        print("   Synqed will route messages to http://localhost:8001 using A2A protocol\n")
    
        # Step 3: Create workspace with mixed agents
        print("🏗️  Step 3: Creating workspace with MIXED agents...")
        
        workspace_manager = synqed.WorkspaceManager(
            workspaces_root=Path("/tmp/synqed_universal_demo")
        )
        
        planner = synqed.PlannerLLM(
            provider="anthropic",
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model="claude-sonnet-4-5"
        )
        
        # Create task node
        class TaskNode:
            id = "root"
            required_agents = ["Coordinator", "LocalWriter", "RemoteCodeAgent"]
            description = "Mixed local and remote agent collaboration"
        
        root_workspace = await workspace_manager.create_workspace(
            task_tree_node=TaskNode(),
            parent_workspace_id=None
        )
        
        print(f"✅ Created workspace with {len(root_workspace.agents)} agents:")
        print(f"   - Coordinator (local Synqed agent)")
        print(f"   - LocalWriter (local Synqed agent)")
        print(f"   - RemoteCodeAgent (remote A2A agent at http://localhost:8001)\n")
    
        # Step 4: Execute task with mixed agents
        print("🚀 Step 4: Running task with mixed agents...\n")
        print("-"*80)
        
        execution_engine = synqed.WorkspaceExecutionEngine(
            planner=planner,
            workspace_manager=workspace_manager,
            enable_display=True,
            max_cycles=10,
            max_agent_turns=8
        )
        
        # Send initial task
        await root_workspace.route_message(
            sender="USER",
            recipient="Coordinator",
            content="Please write a short story about a startup building AI agents. Include technical concepts.",
            manager=workspace_manager
        )
        
        # Run workspace
        await execution_engine.run_workspace(root_workspace.workspace_id)
        
        print("-"*80)
        print("\n✨ Task complete!\n")
        
        # Show full conversation
        print("="*80)
        print("  📜 FULL CONVERSATION LOG")
        print("="*80)
        print()
        
        for agent_name, agent in root_workspace.agents.items():
            messages = agent.memory.get_messages()
            if messages:
                print(f"📍 {agent_name} - Message History ({len(messages)} messages):")
                print("-"*80)
                for i, msg in enumerate(messages, 1):
                    print(f"\n[{i}] From: {msg.from_agent}")
                    content_preview = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                    print(f"    Content: {content_preview}")
                print("\n" + "="*80 + "\n")
        
        # Step 5: Show the power of universal substrate
        print("="*80)
        print("  💡 KEY INSIGHT: Universal Substrate")
        print("="*80)
        print()
        print("What just happened:")
        print("1. Coordinator (Synqed agent) coordinated the task")
        print("2. LocalWriter (Synqed agent) wrote a story")
        print("3. RemoteCodeAgent (A2A agent) reviewed it via HTTP call")
        print()
        print("The RemoteCodeAgent:")
        print("  ✅ Built with a2a-python SDK (NOT Synqed)")
        print("  ✅ Running as separate server (http://localhost:8001)")
        print("  ✅ Synqed routed to it using A2A protocol")
        print("  ✅ No wrapping, no adaptation - just routing!")
        print()
        print("This proves Synqed is a UNIVERSAL SUBSTRATE.")
        print("ANY agent from ANY ecosystem can join, as long as it speaks A2A.")
        print()
        print("="*80 + "\n")
        
        # Show what messages the remote agent received
        print("="*80)
        print("  📡 REMOTE A2A AGENT LOG")
        print("="*80)
        print()
        print("Showing last 50 lines of A2A agent server log:")
        print("-"*80)
        import subprocess
        try:
            log_content = subprocess.run(
                ["tail", "-50", "/tmp/a2a_server.log"],
                capture_output=True,
                text=True
            )
            print(log_content.stdout)
        except Exception as e:
            print(f"Could not read log: {e}")
        print("="*80 + "\n")
    
    finally:
        # Clean up: stop the A2A agent server
        if a2a_server_process:
            print("🛑 Stopping A2A agent server...")
            a2a_server_process.terminate()
            a2a_server_process.wait()
            print("✅ A2A agent server stopped\n")


if __name__ == "__main__":
    asyncio.run(main())

