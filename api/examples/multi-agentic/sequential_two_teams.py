"""
Orchestrator with Two Teams - Sequential and Hierarchical Multi-Workspace Demo

HIERARCHY DIAGRAM:
┌────────────────────────────────────────────────────────────────┐
│ ROOT WORKSPACE                                                 │
│ ┌─────────────────────────────────────────┐                    │
│ │  Project Manager (Orchestrator)         │                    │
│ │  • Receives task from USER              │                    │
│ │  • Plans and delegates to teams         │                    │
│ │  • Synthesizes results                  │                    │
│ └────────────┬────────────────────────────┘                    │
└──────────────┼───────────────────────────────────────────────┬─┘
               │                                               │
               │ delegates                                     │
       ┌───────┴──────────┐                         ┌───────-──┴────────┐
       │                  │                         │                   │
       ▼                  │                         ▼                   │
┌──────────────────┐      │              ┌──────────────────┐           │
│ RESEARCH TEAM    │      │              │ DEVELOPMENT TEAM │           │
│ WORKSPACE        │      │              │ WORKSPACE        │           │
├──────────────────┤      │              ├──────────────────┤           │
│ • Research Lead  │      │              │ • Tech Lead      │           │
│   (coordinates)  │      │              │   (coordinates)  │           │
│                  │      │              │                  │           │
│ • Data Analyst   │      │              │ • Backend Dev    │           │
│   (gathers data) │      │              │   (API design)   │           │
│                  │      │              │                  │           │
│ • Report Writer  │      │              │ • Frontend Dev   │           │
│   (writes report)│      │              │   (UI design)    │           │
└──────────────────┘      │              └──────────────────┘           │
  (3 agents)              │                (3 agents)                   │
       │                  │                     │                       │
       │ returns result   │                     │ returns result        │
       └──────────────────┘                     └───────────────────────┘
                          ▲                     ▲
                          └─────────────────────┘
                          Project Manager receives
                          [subteam_result] messages

TOTAL: 7 agents across 3 workspaces
• 1 orchestrator (Project Manager)
• 2 teams × 3 agents each (Research + Development)

This demonstrates the orchestrator pattern with hierarchical workspaces:
1. Root workspace: Project Manager (orchestrator) plans and delegates
2. Research Team workspace: 3 agents (Research Lead, Data Analyst, Report Writer)
3. Development Team workspace: 3 agents (Tech Lead, Backend Dev, Frontend Dev)

Architecture:
- PlannerLLM creates a hierarchical task tree with subteams
- WorkspaceManager creates nested workspaces (1 root + 2 child workspaces)
- Each workspace has independent agents with their own memory
- Parent workspace can delegate to child workspaces
- Child workspaces return results to parent via [subteam_result] messages

Setup:
1. install: pip install synqed anthropic python-dotenv
2. create .env file with: ANTHROPIC_API_KEY='your-key-here'
3. run: python orchestrator_two_teams.py
"""
import asyncio
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

import synqed

# Load environment variables
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Configure logging (set to WARNING to reduce noise)
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)


# ============================================================================
# Project Manager Agent (Orchestrator) Logic
# ============================================================================

async def project_manager_logic(context: synqed.AgentLogicContext) -> dict:
    """
    Project Manager acts as an orchestrator, delegating tasks to specialized teams.
        
    This agent:
    - Receives the overall project task from USER
    - Plans and breaks down the work
    - Delegates to Research Team and Development Team
    - Aggregates results and reports back to USER
    """
    import anthropic
    
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    system_prompt = (
        "You are a Project Manager orchestrating a software project. "
        "You have two specialized team leads available:\n"
        "1. Research Lead - leads the research team (market research, analysis, documentation)\n"
        "2. Tech Lead - leads the development team (technical implementation, coding)\n\n"
        "You operate in a SINGLE TURN per task. In each response you must make a complete, "
        "self-contained decision based on all available information.\n"
        "If the research and technical data in the conversation already look sufficient, "
        "you MUST synthesize them yourself and respond directly to the USER with a final summary.\n"
        "Do NOT ask any agent for 'final' or 'next' rounds. Never send repeated instructions. "
        "Never assume there will be another turn.\n\n"
        "Your workflow:\n"
        "1. Read the entire conversation history (including research + technical plans).\n"
        "2. Decide whether more information is strictly necessary.\n"
        "3a. If NOT necessary: synthesize results and respond to USER with a final structured summary.\n"
        "3b. If necessary: send exactly ONE clear, bounded task to either Research Lead or Tech Lead.\n\n"
        "Always respond with strict JSON only, no prose around it: "
        '{"send_to": "Research Lead" | "Tech Lead" | "USER", "content": "your response"}'
    )
    
    # Get latest message
    latest_message = context.latest_message
    if not latest_message:
        return context.build_response("USER", "I'm ready to manage your project!")
    
    # Get conversation history automatically
    # Note: For orchestrators, we want to see subteam_result messages
    conversation_text = context.get_conversation_history(include_system_messages=True)
    
    # Add instruction to respond
    conversation_text += "\n\nRespond with JSON: {\"send_to\": \"target\", \"content\": \"your response\"}"
    
    # Call Anthropic API
    resp = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=600,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    # Return the response. All parsing happens automatically
    return resp.content[0].text.strip()


# ============================================================================
# Research Team Agents (3 agents)
# ============================================================================

# State tracking for Research Lead (module-level to persist across calls)
_research_lead_state = {}

async def research_lead_logic(context: synqed.AgentLogicContext) -> dict:
    """Research Lead coordinates the research team with state machine"""
    import anthropic
    
    # State machine: WAITING_FOR_DATA -> READY_TO_WRITE -> DONE
    latest_message = context.latest_message
    workspace_id = context.workspace.workspace_id if context.workspace else "default"
    state_key = f"{workspace_id}:Research Lead"
    
    if state_key not in _research_lead_state:
        _research_lead_state[state_key] = "WAITING_FOR_DATA"
    
    current_state = _research_lead_state[state_key]
    
    # If already DONE, ignore new messages
    if current_state == "DONE":
        return None
    
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    system_prompt = (
        "You are a Research Lead coordinating a research team for a social media analytics dashboard product. "
        "You have two teammates: Data Analyst and Report Writer.\n\n"
        "IMPORTANT OPERATING MODE:\n"
        "- Treat each response as a SINGLE PASS. You will not get multiple rounds.\n"
        "- If some data is missing, you MUST fill gaps yourself using your own reasoning instead of asking for more rounds.\n"
        "- Do NOT send repeated 'FINAL DATA REQUEST' messages or multi-step instructions.\n\n"
        "Workflow:\n"
        "1. If you receive a high-level research task from Project Manager, you may send ONE clear request to Data Analyst.\n"
        "2. When you receive structured data from Data Analyst, you:\n"
        "   - Clean it up mentally\n"
        "   - Ensure it covers competitors, user needs, market gaps, and feature priorities\n"
        "   - If any part is missing, infer it yourself.\n"
        "3. Then you instruct Report Writer ONCE to compile a comprehensive report, passing along all key structured points.\n"
        "4. Finally, you forward the completed report to Project Manager.\n\n"
        "Response format:\n"
        "- Always respond with strict JSON only: "
        '{"send_to": "Data Analyst" | "Report Writer" | "Project Manager", "content": "message"}'
    )
    
    if not latest_message:
        return context.build_response("Data Analyst", "Ready to lead research!")
    
    # Update state based on sender
    if latest_message.from_agent == "Data Analyst" and current_state == "WAITING_FOR_DATA":
        _research_lead_state[state_key] = "READY_TO_WRITE"
    
    # Get conversation history automatically
    conversation_text = context.get_conversation_history()
    conversation_text += "\n\nRespond with JSON: {\"send_to\": \"target\", \"content\": \"message\"}"
    
    resp = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    # Check if response is to Project Manager (final state)
    response_text = resp.content[0].text.strip()
    if '"send_to": "Project Manager"' in response_text or '"send_to":"Project Manager"' in response_text:
        _research_lead_state[state_key] = "DONE"
    
    # Return the response
    return response_text


async def data_analyst_logic(context: synqed.AgentLogicContext) -> dict:
    """Data Analyst gathers and analyzes data"""
    import anthropic
    
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    system_prompt = (
        "You are a Data Analyst on a research team studying the market for a social media analytics dashboard. "
        "You operate in a SINGLE RESPONSE and must provide COMPLETE data.\n\n"
        "Your job in ONE message:\n"
        "- Summarize competitor landscape (Hootsuite, Sprout Social, Buffer Analyze, Iconosquare, Brandwatch, Rival IQ, Emplifi or similar)\n"
        "- Capture user pain points, must-have features, nice-to-have features\n"
        "- Identify market gaps and differentiation opportunities\n"
        "- Suggest MVP vs future features\n\n"
        "You MUST provide a concise but complete, structured overview covering all of the above. "
        "Do NOT ask any other agent for more information. Do NOT emit partial phases.\n\n"
        "Always respond with strict JSON only: "
        '{"send_to": "Research Lead", "content": "your full structured analysis"}'
    )
    
    latest_message = context.latest_message
    if not latest_message:
        return context.build_response("Research Lead", "Ready to analyze data!")
    
    # conversation building
    conversation_text = (
        f"Research Lead asked: {latest_message.content}\n\n"
        "Provide your data analysis. Respond with JSON: {\"send_to\": \"Research Lead\", \"content\": \"your analysis\"}"
    )
    
    resp = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    # Return the response!
    return resp.content[0].text.strip()


async def report_writer_logic(context: synqed.AgentLogicContext) -> dict:
    """Report Writer creates final research reports"""
    import anthropic
    
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    system_prompt = (
        "You are a Report Writer on a research team. "
        "You create clear, well-structured reports from the research and analysis data in the conversation.\n\n"
        "You operate in ONE PASS:\n"
        "- Read all prior messages (from Research Lead and Data Analyst).\n"
        "- Assume the data is complete enough; if something is missing, you infer it yourself.\n"
        "- Write a coherent market research report for a social media analytics dashboard product that can be handed directly to the Project Manager.\n"
        "- The report should include: market overview, competitor analysis, user needs, market gaps, and feature recommendations (MVP vs future phases).\n"
        "- Keep the report concise but comprehensive (800-1200 words max).\n\n"
        "Always respond with strict JSON only: "
        '{"send_to": "Research Lead", "content": "final market research report"}'
    )
    
    latest_message = context.latest_message
    if not latest_message:
        return context.build_response("Research Lead", "Ready to write reports!")
    
    # Conversation building
    conversation_text = (
        f"Research Lead asked: {latest_message.content}\n\n"
        "Create the report. Respond with JSON: {\"send_to\": \"Research Lead\", \"content\": \"your report\"}"
    )
    
    resp = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    # Return the response
    return resp.content[0].text.strip()


# ============================================================================
# Development Team Agents (3 agents)
# ============================================================================

# State tracking for Tech Lead (module-level to persist across calls)
_tech_lead_state = {}

async def tech_lead_logic(context: synqed.AgentLogicContext) -> dict:
    """Tech Lead coordinates the development team with state machine"""
    import anthropic
    
    # State machine: WAITING_FOR_INSTRUCTIONS -> GATHERING_SUBPLANS -> FINALIZING_REPORT -> DONE
    latest_message = context.latest_message
    workspace_id = context.workspace.workspace_id if context.workspace else "default"
    state_key = f"{workspace_id}:Tech Lead"
    
    if state_key not in _tech_lead_state:
        _tech_lead_state[state_key] = "WAITING_FOR_INSTRUCTIONS"
    
    current_state = _tech_lead_state[state_key]
    
    # If already DONE, ignore new messages
    if current_state == "DONE":
        return None
    
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    system_prompt = (
        "You are a Tech Lead coordinating a development team building a social media analytics dashboard. "
        "You have two teammates: Backend Dev and Frontend Dev.\n\n"
        "OPERATING MODE:\n"
        "- You MUST NOT produce the complete plan in one pass.\n"
        "- You MUST delegate to BOTH Backend Dev and Frontend Dev before producing any final plan.\n"
        "- The workflow MUST always be:\n"
        "   1. Receive instructions from Project Manager\n"
        "   2. Send ONE task to Backend Dev asking for backend implementation details\n"
        "   3. Send ONE task to Frontend Dev asking for frontend implementation details\n"
        "   4. When both backend and frontend plans arrive, synthesize them into a final full technical plan\n"
        "   5. Send final synthesized plan to Project Manager\n\n"
        "Structure:\n"
        "- If message is from Project Manager → send_to Backend Dev\n"
        "- If message is from Backend Dev but NOT Frontend Dev → send_to Frontend Dev\n"
        "- If message is from BOTH Backend Dev and Frontend Dev → send_to Project Manager with final plan\n\n"
        "Always respond with strict JSON only: "
        "{\"send_to\": \"Backend Dev\" | \"Frontend Dev\" | \"Project Manager\", \"content\": \"message\"}"
    )
    
    if not latest_message:
        return context.build_response("Backend Dev", "Ready to lead development!")

    # Track receipt of backend and frontend messages
    if 'backend_received' not in _tech_lead_state:
        _tech_lead_state['backend_received'] = False
    if 'frontend_received' not in _tech_lead_state:
        _tech_lead_state['frontend_received'] = False

    if latest_message.from_agent == "Backend Dev":
        _tech_lead_state['backend_received'] = True
    if latest_message.from_agent == "Frontend Dev":
        _tech_lead_state['frontend_received'] = True

    # Update state based on activity
    if latest_message.from_agent == "Project Manager" and current_state == "WAITING_FOR_INSTRUCTIONS":
        _tech_lead_state[state_key] = "GATHERING_SUBPLANS"
    elif latest_message.from_agent in ["Backend Dev", "Frontend Dev"] and current_state == "GATHERING_SUBPLANS":
        _tech_lead_state[state_key] = "FINALIZING_REPORT"

    # Get conversation history automatically
    conversation_text = context.get_conversation_history()
    conversation_text += "\n\nRespond with JSON: {\"send_to\": \"target\", \"content\": \"message\"}"

    resp = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )

    response_text = resp.content[0].text.strip()
    # Enforce that final plan only goes to Project Manager when both backend + frontend have replied
    if _tech_lead_state['backend_received'] and _tech_lead_state['frontend_received']:
        if '"send_to": "Project Manager"' in response_text or '"send_to":"Project Manager"' in response_text:
            _tech_lead_state[state_key] = "DONE"
    else:
        # Prevent premature finalization
        if '"send_to": "Project Manager"' in response_text:
            # Redirect improperly early completion → Frontend Dev
            response_text = response_text.replace("Project Manager", "Frontend Dev")

    # Return the response
    return response_text


async def backend_dev_logic(context: synqed.AgentLogicContext) -> dict:
    """Backend Developer implements server-side features"""
    import anthropic
    
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    system_prompt = (
        "You are a Backend Developer specializing in server-side implementation for a social media analytics dashboard.\n"
        "You operate in a SINGLE RESPONSE and must provide a clear implementation plan.\n\n"
        "Your response should cover:\n"
        "- Backend tech stack (language, framework)\n"
        "- Database choice and schema approach (multi-tenant, time-series)\n"
        "- Data ingestion and rate limiting strategy for multiple social APIs\n"
        "- Batch vs real-time processing\n"
        "- Cloud deployment approach with cost-awareness\n\n"
        "Always respond with strict JSON only: "
        '{"send_to": "Tech Lead", "content": "your backend implementation plan"}'
    )
    
    latest_message = context.latest_message
    if not latest_message:
        return context.build_response("Tech Lead", "Ready to code backend!")
    
    conversation_text = (
        f"Tech Lead asked: {latest_message.content}\n\n"
        "Provide backend implementation plan. Respond with JSON: {\"send_to\": \"Tech Lead\", \"content\": \"your plan\"}"
    )
    
    resp = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    # Return the response
    return resp.content[0].text.strip()


async def frontend_dev_logic(context: synqed.AgentLogicContext) -> dict:
    """Frontend Developer implements client-side features"""
    import anthropic
    
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    system_prompt = (
        "You are a Frontend Developer specializing in UI/UX implementation for a social media analytics dashboard.\n"
        "You operate in a SINGLE RESPONSE and must provide a clear implementation plan.\n\n"
        "Your response should cover:\n"
        "- Frontend tech stack (framework, build tooling, styling)\n"
        "- Core dashboard layout and components (widgets, charts, filters)\n"
        "- Handling real-time updates and responsive design\n"
        "- Authentication flows and integration with backend APIs\n\n"
        "Always respond with strict JSON only: "
        '{"send_to": "Tech Lead", "content": "your frontend implementation plan"}'
    )
    
    latest_message = context.latest_message
    if not latest_message:
        return context.build_response("Tech Lead", "Ready to code frontend!")
    
    # Conversation building
    conversation_text = (
        f"Tech Lead asked: {latest_message.content}\n\n"
        "Provide frontend implementation plan. Respond with JSON: {\"send_to\": \"Tech Lead\", \"content\": \"your plan\"}"
    )
    
    resp = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    # Return the response!
    return resp.content[0].text.strip()


# ============================================================================
# Main Execution
# ============================================================================

async def main():
    print("\n" + "="*80)
    print("  Multi-Team Orchestrator Demo")
    print("  1 Project Manager → 2 Teams (Research + Development, 3 agents each)")
    print("="*80 + "\n")
    
    # ========================================================================
    # Step 1: Register all agent prototypes
    # ========================================================================
    
    # Project Manager (orchestrator in root workspace)
    project_manager = synqed.Agent(
        name="Project Manager",
        description="Project manager who orchestrates teams",
        logic=project_manager_logic,
        default_target="USER"
    )
    
    # Research Team agents
    research_lead = synqed.Agent(
        name="Research Lead",
        description="Research team leader",
        logic=research_lead_logic,
        default_target="Data Analyst"
    )
    
    data_analyst = synqed.Agent(
        name="Data Analyst",
        description="Data analysis specialist",
        logic=data_analyst_logic,
        default_target="Research Lead"
    )
    
    report_writer = synqed.Agent(
        name="Report Writer",
        description="Report writing specialist",
        logic=report_writer_logic,
        default_target="Research Lead"
    )
    
    # Development Team agents
    tech_lead = synqed.Agent(
        name="Tech Lead",
        description="Development team leader",
        logic=tech_lead_logic,
        default_target="Backend Dev"
    )
    
    backend_dev = synqed.Agent(
        name="Backend Dev",
        description="Backend development specialist",
        logic=backend_dev_logic,
        default_target="Tech Lead"
    )
    
    frontend_dev = synqed.Agent(
        name="Frontend Dev",
        description="Frontend development specialist",
        logic=frontend_dev_logic,
        default_target="Tech Lead"
    )
    
    # Register all agents
    synqed.AgentRuntimeRegistry.register("Project Manager", project_manager)
    synqed.AgentRuntimeRegistry.register("Research Lead", research_lead)
    synqed.AgentRuntimeRegistry.register("Data Analyst", data_analyst)
    synqed.AgentRuntimeRegistry.register("Report Writer", report_writer)
    synqed.AgentRuntimeRegistry.register("Tech Lead", tech_lead)
    synqed.AgentRuntimeRegistry.register("Backend Dev", backend_dev)
    synqed.AgentRuntimeRegistry.register("Frontend Dev", frontend_dev)
    
    print("Registered 7 agents (1 orchestrator + 2 teams of 3)\n")
    
    # ========================================================================
    # Step 2: Create workspace manager and planner
    # ========================================================================
    
    workspace_manager = synqed.WorkspaceManager(workspaces_root=Path("/tmp/synqed_orchestrator_demo"))
    
    planner = synqed.PlannerLLM(
        provider="anthropic",
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model="claude-sonnet-4-5"
    )
    
    # ========================================================================
    # Step 3: Create hierarchical workspace structure
    # ========================================================================
    
    # Root workspace: Project Manager
    root_task_node = synqed.TaskTreeNode(
        id="root",
        description="Orchestrate project with specialized teams",
        required_agents=["Project Manager"],
        may_need_subteams=True,
        children=[
            synqed.TaskTreeNode(
                id="research-team",
                description="Research and analysis tasks",
                required_agents=["Research Lead", "Data Analyst", "Report Writer"],
                may_need_subteams=False,
                children=[]
            ),
            synqed.TaskTreeNode(
                id="dev-team",
                description="Development and implementation tasks",
                required_agents=["Tech Lead", "Backend Dev", "Frontend Dev"],
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
    
    print(f"Created root workspace: {root_workspace.workspace_id}")
    print(f"   Agents: {list(root_workspace.agents.keys())}\n")
    
    # Create Research Team workspace (child of root)
    research_team_node = root_task_node.children[0]
    research_workspace = await workspace_manager.create_workspace(
        task_tree_node=research_team_node,
        parent_workspace_id=root_workspace.workspace_id
    )
    
    print(f"Created Research Team workspace: {research_workspace.workspace_id}")
    print(f"   Agents: {list(research_workspace.agents.keys())}\n")
    
    # Create Development Team workspace (child of root)
    dev_team_node = root_task_node.children[1]
    dev_workspace = await workspace_manager.create_workspace(
        task_tree_node=dev_team_node,
        parent_workspace_id=root_workspace.workspace_id
    )
    
    print(f"Created Development Team workspace: {dev_workspace.workspace_id}")
    print(f"   Agents: {list(dev_workspace.agents.keys())}\n")
    
    # ========================================================================
    # Step 4: Create execution engine
    # ========================================================================
    
    execution_engine = synqed.WorkspaceExecutionEngine(
        planner=planner,
        workspace_manager=workspace_manager,
        enable_display=True,  # Real-time message display
        max_agent_turns=25,  # Allow more turns for hierarchical execution
        max_workspace_depth=3,  # Root + 2 child workspaces
    )
    
    print("Created execution engine\n")
    
    # ========================================================================
    # Step 5: Send initial task to Project Manager
    # ========================================================================
    
    task = (
        "Build a social media analytics dashboard. "
        "We need market research on competitors and user needs, "
        "plus a technical implementation plan for both backend and frontend."
    )
    
    print(f"📋 Task: {task}\n")
    print("="*80)
    print("  EXECUTION LOG (Real-time messages)")
    print("="*80 + "\n")
    
    await root_workspace.route_message("USER", "Project Manager", task, manager=workspace_manager)
    
    # ========================================================================
    # Step 6: Execute the entire workspace hierarchy
    # ========================================================================
    
    await execution_engine.run(root_workspace.workspace_id)
    
    # ========================================================================
    # Step 7: Display results
    # ========================================================================
    
    print("\n" + "="*80)
    print("  EXECUTION SUMMARY")
    print("="*80 + "\n")
    
    # Display workspace hierarchy
    print("Workspace Hierarchy:")
    print(f"   Root: {root_workspace.workspace_id} (Project Manager)")
    print(f"   ├─ Research Team: {research_workspace.workspace_id}")
    print(f"   │  └─ Agents: Research Lead, Data Analyst, Report Writer")
    print(f"   └─ Development Team: {dev_workspace.workspace_id}")
    print(f"      └─ Agents: Tech Lead, Backend Dev, Frontend Dev")
    print()
    
    #  Get completion status for each workspace
    root_status = root_workspace.get_completion_status()
    research_status = research_workspace.get_completion_status()
    dev_status = dev_workspace.get_completion_status()
    
    print(f"Message Statistics:")
    print(f"   Root workspace: {root_status['total_messages']} messages")
    print(f"   Research Team: {research_status['total_messages']} messages")
    print(f"   Development Team: {dev_status['total_messages']} messages")
    print(f"   Total: {root_status['total_messages'] + research_status['total_messages'] + dev_status['total_messages']} messages")
    print()
    
    # Use built-in completion status
    print(f"Root Workspace Status:")
    print(f"   {root_status['status_message']}")
    print()
    
    # ========================================================================
    # Step 8: Display transcripts
    # ========================================================================
    
    # Display transcripts using built-in utilities
    root_workspace.display_transcript(title="ROOT WORKSPACE - Project Manager")
    research_workspace.display_transcript(title="RESEARCH TEAM WORKSPACE")
    dev_workspace.display_transcript(title="DEVELOPMENT TEAM WORKSPACE")
    
    # ========================================================================
    # Step 9: Clean up
    # ========================================================================
    
    await workspace_manager.destroy_workspace(root_workspace.workspace_id)
    
    print("="*80)
    print("✅ Demo complete! All workspaces cleaned up.")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

