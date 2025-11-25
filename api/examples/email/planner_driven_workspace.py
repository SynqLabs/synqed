"""
PlannerLLM-Driven Workspace - Fully Automated Agent Creation & Coordination

This demonstrates the AUTOMATED approach where PlannerLLM handles everything:
1. USER provides a task description
2. PlannerLLM analyzes it and CREATES agents dynamically
3. PlannerLLM creates a hierarchical task breakdown
4. Framework creates workspace and routes messages
5. Agents collaborate using GLOBAL INTERACTION PROTOCOL

Key Difference from single_workspace.py:
- NO manual agent creation (alice, bob, charlie)
- PlannerLLM determines what agents are needed based on the task
- Agent logic is generated automatically via create_agents_from_specs()
- Same quality interaction, but fully automated

This approach is ideal when:
- You don't know in advance what agents are needed
- Task requirements vary and need flexible agent composition
- You want the LLM to decide the optimal team structure

Setup:
1. install: pip install synqed anthropic python-dotenv
2. create .env file with: ANTHROPIC_API_KEY='your-key-here'
3. run: python planner_driven_workspace.py
"""
import asyncio
import os
import logging
from pathlib import Path
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


async def main():
    print("\n" + "="*80)
    print("  🤖 PlannerLLM-Driven Workspace")
    print("  Fully automated agent creation and coordination")
    print("="*80 + "\n")
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set!")
        return
    
    # Step 1: Create PlannerLLM
    planner = synqed.PlannerLLM(
        provider="anthropic",
        api_key=api_key,
        model="claude-sonnet-4-20250514"
    )
    
    print("✓ PlannerLLM initialized")
    print()
    
    # Step 2: Define the task
    user_task = "Plan a magical tea party"
    
    print("📋 USER TASK")
    print("="*80)
    print(f"{user_task}\n")
    print("="*80)
    print()
    
    # Step 3: Let PlannerLLM create agent specifications dynamically
    print("🤖 PlannerLLM is analyzing the task and creating agent specifications...")
    
    agent_specs = await planner.create_agents_from_task(
        user_task=user_task,
        provider="anthropic",
        api_key=api_key,
        model="claude-sonnet-4-20250514"
    )
    
    print(f"✓ PlannerLLM created {len(agent_specs)} agent specifications:")
    for spec in agent_specs:
        caps = ", ".join(spec.get("capabilities", [])[:3])
        print(f"   • {spec['name']} ({spec.get('role', 'team')}): {caps}...")
    print()
    
    # Step 4: Create actual Agent instances from specifications
    print("🔧 Creating Agent instances from specifications...")
    
    agents = synqed.create_agents_from_specs(agent_specs)
    
    print(f"✓ Created {len(agents)} agents:")
    for agent in agents:
        print(f"   ✓ {agent.email} - {agent.description}")
    print()
    
    # Step 5: Register agents with runtime registry
    for agent in agents:
        synqed.AgentRuntimeRegistry.register(agent.name, agent)
    
    print(f"✓ Registered {len(agents)} agents in runtime registry")
    print()
    
    # Step 6: Create workspace manager and execution engine
    workspace_manager = synqed.WorkspaceManager(
        workspaces_root=Path("/tmp/synqed_workspaces")
    )
    
    execution_engine = synqed.WorkspaceExecutionEngine(
        planner=planner,
        workspace_manager=workspace_manager,
        enable_display=True,
        max_agent_turns=15,
    )
    
    print("✓ Execution engine configured")
    print()
    
    # Step 7: Use PlannerLLM to create the task breakdown
    print("🤔 PlannerLLM is creating the task breakdown...")
    
    task_plan = await planner.plan_task(user_task)
    
    print("✓ PlannerLLM created task breakdown:")
    print(f"   Root task: {task_plan.root.description}")
    print(f"   Required agents: {task_plan.root.required_agents}")
    if task_plan.root.children:
        print(f"   Subtasks: {len(task_plan.root.children)}")
        for i, child in enumerate(task_plan.root.children, 1):
            agents_str = ", ".join(child.required_agents) if child.required_agents else "none"
            print(f"     {i}. {child.description} [{agents_str}]")
    print()
    
    # Step 8: Create workspace - aggregate all agents for single workspace mode
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
    
    # Step 9: Send subtasks to appropriate agents
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
    
    # Step 10: Execute the workspace
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
    
    # Generate agent email list for summary
    agent_emails = ", ".join([agent.email for agent in agents])
    
    print()
    print("="*80)
    print("✅ PlannerLLM-driven demo complete!")
    print(f"   • Workspace: {workspace.workspace_id}")
    print(f"   • Agents (auto-generated): {agent_emails}")
    print(f"   • All communication happened in ONE workspace")
    print(f"   • Agents were created dynamically by PlannerLLM")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

