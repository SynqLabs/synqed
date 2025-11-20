"""
Parallel Research Teams - TRUE Parallel Execution with Autonomous Agents

HIERARCHY DIAGRAM:
┌────────────────────────────────────────────────────────────────┐
│ ROOT WORKSPACE                                                 │
│ ┌─────────────────────────────────────────┐                    │
│ │  Research Coordinator                   │                    │
│ │  (broadcasts to all 3 teams at once)    │                    │
│ └────────────┬────────────┬────────────┬──┘                    │
└──────────────┼────────────┼────────────┼───────────────────────┘
               │            │            │
       ┌───────┘            │            └────────┐
       │                    │                     │
       ▼                    ▼                     ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ AI TEAM     │      │ CLIMATE TEAM│      │ SPACE TEAM  │
│ WORKSPACE   │      │ WORKSPACE   │      │ WORKSPACE   │
├─────────────┤      ├─────────────┤      ├─────────────┤
│ • AI        │      │ • Climate   │      │ • Space     │
│   Research  │      │   Research  │      │   Research  │
│   Lead      │      │   Lead      │      │   Lead      │
│             │      │             │      │             │
│ • AI Sr     │      │ • Climate   │      │ • Space Sr  │
│   Research  │      │   Sr Res    │      │   Research  │
│   Assistant │      │   Assistant │      │   Assistant │
│             │      │             │      │             │
│ • AI Jr     │      │ • Climate   │      │ • Space Jr  │
│   Research  │      │   Jr Res    │      │   Research  │
│   Assistant │      │   Assistant │      │   Assistant │
│   (collab)  │      │   (collab)  │      │   (collab)  │
└─────────────┘      └─────────────┘      └─────────────┘
  (3 agents)           (3 agents)           (3 agents)

TOTAL: 10 agents across 4 workspaces (1 root + 3 child teams)

This example demonstrates TRUE PARALLEL workspace execution with AUTONOMOUS agent decision-making:

1. Research Coordinator receives a multi-topic research request
2. Coordinator DECIDES to broadcast to ALL 3 teams in ONE turn
   {"send_to": ["AI Research Lead", "Climate Research Lead", "Space Research Lead"]}
3. All 3 teams receive work SIMULTANEOUSLY and execute in PARALLEL
4. Within each team workspace, agents AUTONOMOUSLY DECIDE their workflow:
   - Agents read conversation history and DECIDE next actions
   - Lead may delegate to Senior, ask for improvements, or send final report to Coordinator
   - Senior may collaborate with Junior, synthesize findings, or send to Lead
   - Junior reviews and adds complementary research when Senior engages them
   - NO HARDCODED PHASES - agents decide when work is complete!
5. Teams complete work independently when THEY decide it's ready
6. Coordinator waits for all 3 reports, then DECIDES to synthesize and send to USER

🧠 AUTONOMOUS DECISION-MAKING:
Unlike hardcoded workflows, agents here make their own decisions based on:
- Reading full conversation history
- Evaluating quality of work received
- Deciding when more collaboration is needed
- Determining when work is complete and ready to escalate
This mirrors the pattern in workspace.py where Writer/Editor autonomously collaborate!

🚀 BROADCAST DELEGATION:
The Coordinator sends to multiple recipients in a single response, enabling true
parallel delegation. All teams receive their tasks at the same moment, not sequentially.

⚡ PARALLEL EXECUTION:
The WorkspaceExecutionEngine runs all workspaces concurrently using asyncio.gather,
so all 3 teams work simultaneously. This provides significant speedup for independent
workloads:
- Sequential: Time = Team₁ + Team₂ + Team₃
- Parallel: Time ≈ max(Team₁, Team₂, Team₃)
- Potential 3x speedup!

🤝 EMERGENT COLLABORATION:
Within each workspace, collaboration patterns EMERGE from agent decisions:
- Agents decide when to delegate, collaborate, or escalate
- Workflow adapts based on quality of work and feedback
- No predetermined number of rounds - agents work until satisfied
- Lead decides when report is polished enough to send to Coordinator
- Coordinator decides when all reports are sufficient to synthesize for USER

Setup:
1. install: pip install synqed anthropic python-dotenv
2. create .env file with: ANTHROPIC_API_KEY='your-key-here'
3. run: python parallel_three_teams.py
"""
import asyncio
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Import the synqed API
import synqed

# Load environment variables
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)


# ============================================================================
# Research Coordinator (Orchestrator)
# ============================================================================

async def coordinator_logic(context: synqed.AgentLogicContext) -> dict:
    """
    Research Coordinator autonomously manages parallel research teams using BROADCAST.
    
    Uses broadcast delegation to send to all 3 teams simultaneously in ONE turn:
    {"send_to": ["Team1", "Team2", "Team3"], "content": "..."}
    
    This achieves TRUE PARALLEL delegation - all teams receive work at the same time!
    """
    import anthropic
    
    # Get latest message
    latest_message = context.latest_message
    if not latest_message:
        return context.build_response("USER", "Ready to coordinate parallel research!")
    
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    # Autonomous decision-making system prompt
    system_prompt = (
        "You are a Research Coordinator managing 3 specialized research teams:\n"
        "- AI Research Lead (AI topics)\n"
        "- Climate Research Lead (climate topics)\n"
        "- Space Research Lead (space topics)\n"
        "\n"
        "WORKFLOW - YOU DECIDE:\n"
        "1. When USER gives you a multi-topic research task → BROADCAST to all 3 leads at once using a LIST:\n"
        '   {"send_to": ["AI Research Lead", "Climate Research Lead", "Space Research Lead"], "content": "task description"}\n'
        "2. Each team will work independently and send you their research when ready\n"
        "3. When you have received reports from ALL 3 teams → synthesize into one comprehensive summary for USER\n"
        "4. If any team's report is incomplete or unclear → ask that specific team for clarification\n"
        "\n"
        "IMPORTANT:\n"
        "- For BROADCAST (multiple recipients): use a LIST: {\"send_to\": [\"Agent1\", \"Agent2\"], \"content\": \"...\"}\n"
        "- For SINGLE recipient: use a STRING: {\"send_to\": \"Agent1\", \"content\": \"...\"}\n"
        "- Only send to USER when you have complete research from all 3 teams and have synthesized it."
    )
    
    conversation_text = context.get_conversation_history()
    conversation_text += "\n\nRespond with JSON: {\"send_to\": \"target\", \"content\": \"message\"}"
    
    resp = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=600,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    return resp.content[0].text.strip()


# ============================================================================
# Lead Researcher Logic (Generic for all teams)
# ============================================================================

async def lead_researcher_logic(context: synqed.AgentLogicContext) -> dict:
    """Generic lead researcher that autonomously decides workflow with senior assistant."""
    import anthropic
    
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    # Get agent name to determine specialty
    agent_name = context.agent_name or "Lead Researcher"
    
    if "AI" in agent_name:
        specialty = "artificial intelligence and machine learning"
        topic_focus = "Latest advances in Large Language Models and AI agents"
        senior_assistant = "AI Senior Research Assistant"
    elif "Climate" in agent_name:
        specialty = "climate change and environmental science"
        topic_focus = "Recent breakthroughs in climate change mitigation technology"
        senior_assistant = "Climate Senior Research Assistant"
    elif "Space" in agent_name:
        specialty = "space exploration and astronomy"
        topic_focus = "Current status of Mars exploration missions"
        senior_assistant = "Space Senior Research Assistant"
    else:
        specialty = "general research"
        topic_focus = "general research topic"
        senior_assistant = "Senior Research Assistant"
    
    latest_message = context.latest_message
    if not latest_message:
        return context.build_response(senior_assistant, "Ready to lead research!")
    
    # Autonomous decision-making system prompt (like workspace.py)
    system_prompt = (
        f"You are a Lead Researcher specializing in {specialty}. "
        f"You work with {senior_assistant} (who collaborates with a junior assistant). "
        "\n\nWORKFLOW - YOU DECIDE:\n"
        f"1. If you receive a task from Research Coordinator and need research done → delegate to {senior_assistant}\n"
        f"2. If {senior_assistant} sends findings that need improvement → send feedback back to {senior_assistant}\n"
        "3. If the research is COMPLETE and GOOD → synthesize a polished 100-150 word summary and send to Research Coordinator\n"
        "\n"
        "Be thorough but efficient. The research should be comprehensive and well-sourced. "
        "When ready to send to Research Coordinator, make sure your summary is polished and complete. "
        "Always respond with JSON (send_to is a STRING for single recipient):\n"
        f'{{"send_to": "{senior_assistant}", "content": "your message"}}\n'
        f'OR {{"send_to": "Research Coordinator", "content": "your message"}}'
    )
    
    conversation_text = context.get_conversation_history()
    conversation_text += "\n\nRespond with JSON: {\"send_to\": \"target\", \"content\": \"message\"}"
    
    resp = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    return resp.content[0].text.strip()


# ============================================================================
# Senior Research Assistant Logic (Coordinates with Junior Assistant)
# ============================================================================

async def senior_assistant_logic(context: synqed.AgentLogicContext) -> dict:
    """Senior assistant that autonomously decides how to collaborate with junior assistant."""
    import anthropic
    
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    # Get agent name to determine specialty
    agent_name = context.agent_name or "Senior Research Assistant"
    
    if "AI" in agent_name:
        specialty = "artificial intelligence and machine learning"
        lead = "AI Research Lead"
        junior = "AI Junior Research Assistant"
    elif "Climate" in agent_name:
        specialty = "climate change and environmental science"
        lead = "Climate Research Lead"
        junior = "Climate Junior Research Assistant"
    elif "Space" in agent_name:
        specialty = "space exploration and astronomy"
        lead = "Space Research Lead"
        junior = "Space Junior Research Assistant"
    else:
        specialty = "general research"
        lead = "Lead Researcher"
        junior = "Junior Research Assistant"
    
    latest_message = context.latest_message
    if not latest_message:
        return context.build_response(junior, "Ready to coordinate research!")
    
    # Autonomous decision-making system prompt
    system_prompt = (
        f"You are a Senior Research Assistant specializing in {specialty}. "
        f"You coordinate research with {junior} and report to {lead}. "
        "\n\nWORKFLOW - YOU DECIDE:\n"
        f"1. If {lead} gives you a task → do initial research, then send to {junior} for review and additional findings\n"
        f"2. If {junior} sends complementary research → synthesize both your work and theirs\n"
        f"3. If the combined work is comprehensive → send to {lead}\n"
        f"4. If {lead} asks for improvements → collaborate with {junior} to enhance specific areas\n"
        f"5. If work needs more depth → work with {junior} again\n"
        "\n"
        "Be thorough and collaborative. Make sure research is well-rounded before sending to Lead. "
        "Always respond with JSON (send_to is a STRING for single recipient):\n"
        f'{{"send_to": "{junior}", "content": "your message"}}\n'
        f'OR {{"send_to": "{lead}", "content": "your message"}}'
    )
    
    conversation_text = context.get_conversation_history()
    conversation_text += f"\n\nRespond with JSON: {{\"send_to\": \"target\", \"content\": \"message\"}}"
    
    resp = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    return resp.content[0].text.strip()


# ============================================================================
# Junior Research Assistant Logic (Collaborates with Senior Assistant)
# ============================================================================

async def junior_assistant_logic(context: synqed.AgentLogicContext) -> dict:
    """Junior assistant that reviews senior's work and adds complementary findings."""
    import anthropic
    
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    # Get agent name to determine specialty
    agent_name = context.agent_name or "Junior Research Assistant"
    
    if "AI" in agent_name:
        specialty = "artificial intelligence and machine learning"
        senior = "AI Senior Research Assistant"
    elif "Climate" in agent_name:
        specialty = "climate change and environmental science"
        senior = "Climate Senior Research Assistant"
    elif "Space" in agent_name:
        specialty = "space exploration and astronomy"
        senior = "Space Senior Research Assistant"
    else:
        specialty = "general research"
        senior = "Senior Research Assistant"
    
    latest_message = context.latest_message
    if not latest_message:
        return context.build_response(senior, "Ready to collaborate!")
    
    system_prompt = (
        f"You are a Junior Research Assistant specializing in {specialty}. "
        f"{senior} is sharing research with you. Your role:\n"
        "1. Review their findings carefully\n"
        "2. Add complementary research from different angles\n"
        "3. Find additional examples, data, or perspectives they may have missed\n"
        "4. If they're asking for help with improvements, focus on those areas\n\n"
        "Be constructive and add value. Always respond with JSON: "
        f'{{"send_to": "{senior}", "content": "your review and additional findings"}}'
    )
    
    conversation_text = context.get_conversation_history()
    conversation_text += f"\n\nRespond with JSON: {{\"send_to\": \"{senior}\", \"content\": \"additions\"}}"
    
    resp = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=250,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    return resp.content[0].text.strip()


# ============================================================================
# Main Execution
# ============================================================================

async def main():
    print("\n" + "="*80)
    print("  🚀 Parallel Research Teams Demo - TRUE PARALLEL EXECUTION")
    print("  Coordinator BROADCASTS to 3 Teams → All work SIMULTANEOUSLY")
    print("  Each team has 3 agents: Lead + Senior Assistant + Junior Assistant")
    print("  Assistants COLLABORATE with each other before reporting to Lead")
    print("="*80 + "\n")
    
    # Step 1: Register all agent prototypes
    coordinator = synqed.Agent(
        name="Research Coordinator",
        description="Coordinates parallel research across multiple teams",
        logic=coordinator_logic,
        default_target="USER"
    )
    
    # AI Team (3 agents: Lead + Senior Assistant + Junior Assistant)
    ai_lead = synqed.Agent(
        name="AI Research Lead",
        description="Lead researcher for AI topics",
        logic=lead_researcher_logic,
        default_target="AI Senior Research Assistant"
    )
    
    ai_senior = synqed.Agent(
        name="AI Senior Research Assistant",
        description="Senior research assistant for AI topics",
        logic=senior_assistant_logic,
        default_target="AI Junior Research Assistant"
    )
    
    ai_junior = synqed.Agent(
        name="AI Junior Research Assistant",
        description="Junior research assistant for AI topics",
        logic=junior_assistant_logic,
        default_target="AI Senior Research Assistant"
    )
    
    # Climate Team (3 agents: Lead + Senior Assistant + Junior Assistant)
    climate_lead = synqed.Agent(
        name="Climate Research Lead",
        description="Lead researcher for climate topics",
        logic=lead_researcher_logic,
        default_target="Climate Senior Research Assistant"
    )
    
    climate_senior = synqed.Agent(
        name="Climate Senior Research Assistant",
        description="Senior research assistant for climate topics",
        logic=senior_assistant_logic,
        default_target="Climate Junior Research Assistant"
    )
    
    climate_junior = synqed.Agent(
        name="Climate Junior Research Assistant",
        description="Junior research assistant for climate topics",
        logic=junior_assistant_logic,
        default_target="Climate Senior Research Assistant"
    )
    
    # Space Team (3 agents: Lead + Senior Assistant + Junior Assistant)
    space_lead = synqed.Agent(
        name="Space Research Lead",
        description="Lead researcher for space topics",
        logic=lead_researcher_logic,
        default_target="Space Senior Research Assistant"
    )
    
    space_senior = synqed.Agent(
        name="Space Senior Research Assistant",
        description="Senior research assistant for space topics",
        logic=senior_assistant_logic,
        default_target="Space Junior Research Assistant"
    )
    
    space_junior = synqed.Agent(
        name="Space Junior Research Assistant",
        description="Junior research assistant for space topics",
        logic=junior_assistant_logic,
        default_target="Space Senior Research Assistant"
    )
    
    # Register all agents
    synqed.AgentRuntimeRegistry.register("Research Coordinator", coordinator)
    
    synqed.AgentRuntimeRegistry.register("AI Research Lead", ai_lead)
    synqed.AgentRuntimeRegistry.register("AI Senior Research Assistant", ai_senior)
    synqed.AgentRuntimeRegistry.register("AI Junior Research Assistant", ai_junior)
    
    synqed.AgentRuntimeRegistry.register("Climate Research Lead", climate_lead)
    synqed.AgentRuntimeRegistry.register("Climate Senior Research Assistant", climate_senior)
    synqed.AgentRuntimeRegistry.register("Climate Junior Research Assistant", climate_junior)
    
    synqed.AgentRuntimeRegistry.register("Space Research Lead", space_lead)
    synqed.AgentRuntimeRegistry.register("Space Senior Research Assistant", space_senior)
    synqed.AgentRuntimeRegistry.register("Space Junior Research Assistant", space_junior)
    
    print("✅ Registered 10 agents (1 coordinator + 3 teams of 3)\n")
    
    # Step 2: Create workspace manager and planner
    workspace_manager = synqed.WorkspaceManager(workspaces_root=Path("/tmp/synqed_parallel_research"))
    
    planner = synqed.PlannerLLM(
        provider="anthropic",
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model="claude-sonnet-4-5"
    )
    
    # Step 3: Create workspace hierarchy
    root_task_node = synqed.TaskTreeNode(
        id="root",
        description="Coordinate parallel research",
        required_agents=["Research Coordinator"],
        may_need_subteams=True,
        children=[
            synqed.TaskTreeNode(
                id="ai-team",
                description="AI research",
                required_agents=[
                    "AI Research Lead",
                    "AI Senior Research Assistant",
                    "AI Junior Research Assistant"
                ],
                may_need_subteams=False,
                children=[]
            ),
            synqed.TaskTreeNode(
                id="climate-team",
                description="Climate research",
                required_agents=[
                    "Climate Research Lead",
                    "Climate Senior Research Assistant",
                    "Climate Junior Research Assistant"
                ],
                may_need_subteams=False,
                children=[]
            ),
            synqed.TaskTreeNode(
                id="space-team",
                description="Space research",
                required_agents=[
                    "Space Research Lead",
                    "Space Senior Research Assistant",
                    "Space Junior Research Assistant"
                ],
                may_need_subteams=False,
                children=[]
            )
        ]
    )
    
    # Create root workspace
    root_workspace = await workspace_manager.create_workspace(
        task_tree_node=root_task_node,
        parent_workspace_id=None
    )
    
    print(f"✅ Created root workspace: {root_workspace.workspace_id}")
    print(f"   Agent: {list(root_workspace.agents.keys())}\n")
    
    # Create AI Team workspace
    ai_team_node = root_task_node.children[0]
    ai_workspace = await workspace_manager.create_workspace(
        task_tree_node=ai_team_node,
        parent_workspace_id=root_workspace.workspace_id
    )
    
    print(f"✅ Created AI Team workspace: {ai_workspace.workspace_id}")
    print(f"   Agents: {list(ai_workspace.agents.keys())}\n")
    
    # Create Climate Team workspace
    climate_team_node = root_task_node.children[1]
    climate_workspace = await workspace_manager.create_workspace(
        task_tree_node=climate_team_node,
        parent_workspace_id=root_workspace.workspace_id
    )
    
    print(f"✅ Created Climate Team workspace: {climate_workspace.workspace_id}")
    print(f"   Agents: {list(climate_workspace.agents.keys())}\n")
    
    # Create Space Team workspace
    space_team_node = root_task_node.children[2]
    space_workspace = await workspace_manager.create_workspace(
        task_tree_node=space_team_node,
        parent_workspace_id=root_workspace.workspace_id
    )
    
    print(f"✅ Created Space Team workspace: {space_workspace.workspace_id}")
    print(f"   Agents: {list(space_workspace.agents.keys())}\n")
    
    # Step 4: Create execution engine
    execution_engine = synqed.WorkspaceExecutionEngine(
        planner=planner,
        workspace_manager=workspace_manager,
        enable_display=True,
        max_agent_turns=50,  # Allow enough turns for 3 parallel teams with assistant collaboration
        max_workspace_depth=3,
    )
    
    print("✅ Created execution engine with parallel workspace support\n")
    
    # Step 5: Send initial task
    task = (
        "Research three cutting-edge topics:\n"
        "1. Latest advances in Large Language Models and AI agents\n"
        "2. Recent breakthroughs in climate change mitigation technology\n"
        "3. Current status of Mars exploration missions\n\n"
        "Each team should provide a brief summary (100-150 words) of the most important recent developments."
    )
    
    print(f"📋 Task: {task}\n")
    print("="*80)
    print("  EXECUTION LOG (Watch for PARALLEL execution)")
    print("="*80 + "\n")
    
    await root_workspace.route_message("USER", "Research Coordinator", task, manager=workspace_manager)
    
    # Step 6: Execute (all teams will run in parallel)
    import time
    start_time = time.time()
    
    try:
        await execution_engine.run(root_workspace.workspace_id)
    except Exception as e:
        print(f"\n❌ Error during execution: {e}\n")
        import traceback
        traceback.print_exc()
        raise
    
    elapsed_time = time.time() - start_time
    
    # Step 7: Display results
    print("\n" + "="*80)
    print("  EXECUTION SUMMARY")
    print("="*80 + "\n")
    
    print(f"⏱️  Execution time: {elapsed_time:.2f} seconds\n")
    
    print("📊 Workspace Hierarchy:")
    print(f"   Root: {root_workspace.workspace_id} (Coordinator)")
    print(f"   ├─ AI Team: {ai_workspace.workspace_id}")
    print(f"   ├─ Climate Team: {climate_workspace.workspace_id}")
    print(f"   └─ Space Team: {space_workspace.workspace_id}")
    print()
    
    # Get completion status for each workspace
    root_status = root_workspace.get_completion_status()
    ai_status = ai_workspace.get_completion_status()
    climate_status = climate_workspace.get_completion_status()
    space_status = space_workspace.get_completion_status()
    
    print("📈 Message Statistics:")
    print(f"   Root: {root_status['total_messages']} messages")
    print(f"   AI Team: {ai_status['total_messages']} messages")
    print(f"   Climate Team: {climate_status['total_messages']} messages")
    print(f"   Space Team: {space_status['total_messages']} messages")
    print(f"   Total: {root_status['total_messages'] + ai_status['total_messages'] + climate_status['total_messages'] + space_status['total_messages']} messages")
    print()
    
    print(f"✅ Status: {root_status['status_message']}\n")
    
    # Display transcripts
    root_workspace.display_transcript(title="ROOT - Research Coordinator")
    ai_workspace.display_transcript(title="AI TEAM")
    climate_workspace.display_transcript(title="CLIMATE TEAM")
    space_workspace.display_transcript(title="SPACE TEAM")
    
    # Clean up
    await workspace_manager.destroy_workspace(root_workspace.workspace_id)
    
    print("="*80)
    print("✅ Parallel execution demo complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

