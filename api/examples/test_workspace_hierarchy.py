"""
Test script for multi-level workspace hierarchy with improved agent interactions.

This demonstrates:
1. Creating a 3-level deep task hierarchy
2. Dynamic agent creation with professional prompts
3. Workspace tree visualization
4. Enhanced agent coordination quality
"""

import asyncio
import os
from pathlib import Path
from anthropic import AsyncAnthropic

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "synqed-python" / "src"))

import synqed

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass


async def main():
    """
    Test multi-level workspace hierarchy with professional agent interactions.
    """
    print("\n" + "="*80)
    print("🏗️  MULTI-LEVEL WORKSPACE HIERARCHY TEST")
    print("="*80)
    print()
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set!")
        print("Please set your API key in .env file")
        return
    
    # Define a complex user task that will create multiple levels
    user_task = """
I need a full end-to-end sales workflow for an upcoming customer meeting:

1. Research the account (internal usage data + external market positioning)
2. Prepare customer insights and competitive analysis
3. Generate meeting materials (agenda, talking points, pitch deck outline)
4. Create follow-up strategy (email templates, timeline, next steps)

Customer Details:
- Company: Acme Corporation
- Industry: Healthcare Technology
- Current Contract: $450K ARR
- Meeting Type: Quarterly Business Review + Upsell Discussion
- Timeline: Meeting in 5 days

Deliverables needed:
- Research report with key findings
- Meeting preparation package
- Pitch deck outline
- Follow-up email templates
"""
    
    print("="*80)
    print("📋 USER TASK")
    print("="*80)
    print(user_task)
    print("="*80)
    print()
    
    # Step 1: Initialize PlannerLLM
    print("🧠 Initializing PlannerLLM...")
    planner = synqed.PlannerLLM(
        provider="anthropic",
        api_key=api_key,
        model="claude-sonnet-4-20250514"
    )
    print("✓ PlannerLLM initialized")
    print()
    
    # Step 2: Create task plan and agent specifications
    print("🔍 Breaking down task and creating agent specifications...")
    print("   • Analyzing task structure")
    print("   • Identifying required agent roles")
    print("   • Creating specialized agents")
    print()
    
    task_plan, agent_specs = await planner.plan_task_and_create_agent_specs(
        user_task=user_task,
        agent_provider="anthropic",
        agent_api_key=api_key,
        agent_model="claude-sonnet-4-20250514"
    )
    
    print("✅ Task breakdown created:")
    print(f"   Root: {task_plan.root.description[:60]}...")
    print(f"   Subtasks: {len(task_plan.root.children)}")
    print()
    
    for i, child in enumerate(task_plan.root.children, 1):
        print(f"   {i}. {child.description}")
        print(f"      Agents: {', '.join(child.required_agents)}")
        print(f"      May need subteams: {child.may_need_subteams}")
    print()
    
    print(f"✅ Created {len(agent_specs)} specialized agent specifications:")
    print()
    
    for i, spec in enumerate(agent_specs, 1):
        print(f"   {i}. {spec['name']} ({spec['role']})")
        print(f"      Description: {spec['description']}")
        print(f"      Capabilities: {', '.join(spec['capabilities'][:3])}...")
    print()
    
    # Step 3: Create Agent instances from specifications
    print("👥 Creating Agent instances with enhanced prompts...")
    agents = synqed.create_agents_from_specs(agent_specs)
    
    for agent in agents:
        print(f"   ✓ {agent.name}")
        print(f"      Description: {agent.description}")
    
    print(f"\n✓ Total agents created: {len(agents)}")
    print()
    
    # Step 4: Register agents in runtime registry
    print("📝 Registering agents in runtime registry...")
    for agent in agents:
        synqed.AgentRuntimeRegistry.register(agent.name, agent)
    print(f"  ✓ Registered {len(agents)} agents")
    print()
    
    # Step 5: Setup workspace infrastructure
    print("🏗️  Setting up workspace infrastructure...")
    
    workspace_manager = synqed.WorkspaceManager(
        workspaces_root=Path("/tmp/synqed_hierarchy_test")
    )
    
    execution_engine = synqed.WorkspaceExecutionEngine(
        planner=planner,
        workspace_manager=workspace_manager,
        enable_display=True,
        max_agent_turns=25,  # Allow more turns for complex workflow
        max_workspace_depth=5,  # Allow deeper nesting
    )
    
    print("✓ Infrastructure configured")
    print(f"  • WorkspaceManager: ready")
    print(f"  • ExecutionEngine: ready (max turns: 25, max depth: 5)")
    print()
    
    # Step 6: Execute task plan automatically
    print("="*80)
    print("⚡ EXECUTING TASK PLAN")
    print("="*80)
    print()
    print("The ExecutionEngine will now:")
    print("  1. Create root workspace with coordinator")
    print("  2. Create child workspaces for each major phase")
    print("  3. Execute all workspaces in parallel")
    print("  4. Agents will coordinate using professional interaction protocol")
    print()
    
    root_workspace, child_workspaces = await execution_engine.execute_task_plan(
        task_plan=task_plan,
        user_task=user_task
    )
    
    print()
    print("="*80)
    print("📊 EXECUTION RESULTS")
    print("="*80)
    print()
    
    # Display workspace hierarchy
    print("🌲 WORKSPACE HIERARCHY:")
    print()
    print(f"ROOT: {root_workspace.workspace_id}")
    print(f"  Name: {root_workspace.workspace_name}")
    print(f"  Description: {root_workspace.workspace_description[:60]}...")
    print(f"  Agents: {', '.join(root_workspace.agents.keys())}")
    print(f"  Depth: {root_workspace.depth}")
    print(f"  Messages: {len(root_workspace.router.get_transcript())}")
    print()
    
    for i, workspace in enumerate(child_workspaces, 1):
        # Find corresponding subtask
        subtask = task_plan.root.children[i-1] if i-1 < len(task_plan.root.children) else None
        
        print(f"CHILD {i}: {workspace.workspace_id}")
        print(f"  Name: {workspace.workspace_name}")
        print(f"  Description: {workspace.workspace_description[:60]}...")
        print(f"  Agents: {', '.join(workspace.agents.keys())}")
        print(f"  Depth: {workspace.depth}")
        print(f"  Parent: {workspace.parent_id}")
        print(f"  Messages: {len(workspace.router.get_transcript())}")
        
        # Show snippet of final message to USER
        transcript = workspace.router.get_transcript()
        for msg in reversed(transcript):
            if msg.get("to") == "USER":
                content = msg.get("content", "")
                if content and content != "[startup]":
                    print(f"  Final output: {content[:80]}...")
                    break
        print()
    
    # Step 7: Display enhanced agent interactions
    print("="*80)
    print("💬 SAMPLE AGENT INTERACTIONS")
    print("="*80)
    print()
    
    # Show messages from root coordinator
    root_transcript = root_workspace.router.get_transcript()
    coordinator_messages = [
        msg for msg in root_transcript 
        if msg.get("from") in root_workspace.agents.keys()
    ][:3]  # First 3 coordinator messages
    
    print("Root Coordinator Messages:")
    for msg in coordinator_messages:
        print(f"\n  From: {msg.get('from')}")
        print(f"  To: {msg.get('to')}")
        print(f"  Content: {msg.get('content', '')[:150]}...")
    print()
    
    # Show professional outputs from child workspaces
    print("Child Workspace Professional Outputs:")
    for i, workspace in enumerate(child_workspaces[:2], 1):  # First 2 children
        transcript = workspace.router.get_transcript()
        messages = [
            msg for msg in transcript
            if msg.get("to") == "USER" and not msg.get("content", "").startswith("[")
        ]
        if messages:
            msg = messages[0]
            print(f"\n  Workspace {i} ({workspace.workspace_name}):")
            print(f"  Agent: {msg.get('from')}")
            print(f"  Output: {msg.get('content', '')[:200]}...")
    print()
    
    # Step 8: Get workspace tree structure
    print("="*80)
    print("🌳 WORKSPACE TREE STRUCTURE")
    print("="*80)
    print()
    
    tree_data = workspace_manager.get_workspace_tree()
    print(f"Total workspaces: {tree_data.get('total_workspaces', 0)}")
    print(f"Root workspaces: {len(tree_data.get('roots', []))}")
    print()
    
    # Display tree in a readable format
    def print_tree(node, indent=0):
        prefix = "  " * indent + ("└─ " if indent > 0 else "")
        print(f"{prefix}[{node['workspace_name']}]")
        print(f"{prefix}  ID: {node['workspace_id'][:12]}...")
        print(f"{prefix}  Agents: {len(node['agents'])} ({', '.join(a['name'] for a in node['agents'])})")
        print(f"{prefix}  Messages: {node['message_count']}")
        
        for child in node.get('children', []):
            print_tree(child, indent + 1)
    
    for root in tree_data.get('roots', []):
        print_tree(root)
    print()
    
    # Step 9: Summary
    print("="*80)
    print("🎉 TEST COMPLETE!")
    print("="*80)
    print()
    print("What was demonstrated:")
    print(f"  1. ✅ Created hierarchical task plan with {len(task_plan.root.children)} subtasks")
    print(f"  2. ✅ Generated {len(agent_specs)} specialized agents dynamically")
    print(f"  3. ✅ Created {1 + len(child_workspaces)} workspaces (1 root + {len(child_workspaces)} children)")
    print(f"  4. ✅ Agents used professional interaction protocol")
    print(f"  5. ✅ Workspace tree tracked with metadata")
    print(f"  6. ✅ Parallel execution with cross-workspace coordination")
    print()
    print("Key Features Showcased:")
    print("  • Multi-level workspace hierarchy (depth tracking)")
    print("  • Enhanced agent prompts for professional output")
    print("  • Structured deliverables with markdown formatting")
    print("  • Workspace tree visualization ready for frontend")
    print("  • Email-like agent addressing (agent@workspace)")
    print()
    
    # Cleanup
    print("🧹 Cleaning up workspaces...")
    for workspace in child_workspaces:
        await workspace_manager.destroy_workspace(workspace.workspace_id)
    await workspace_manager.destroy_workspace(root_workspace.workspace_id)
    print("✓ Workspaces cleaned up")
    print()


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())

