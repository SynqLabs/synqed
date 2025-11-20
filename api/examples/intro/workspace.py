"""
Two Agents Collaborating - Workspace-based multi-agent communication

This demonstrates the new Workspace-based multi-agent messaging system:
1. Agents run in a Workspace (logical routing domain)
2. Agents maintain their own internal conversation memory
3. Workspace routes messages between agents using MessageRouter
4. WorkspaceExecutionEngine executes agents with event-driven scheduling
5. True agent-to-agent communication via structured actions

Setup:
1. install: pip install synqed anthropic python-dotenv
2. create .env file with: ANTHROPIC_API_KEY='your-key-here'
3. run: python two_agents_collaborating.py
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

# Configure logging (set to WARNING to reduce noise, display handles output)
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)


# ============================================================================
# Agent Logic Functions
# ============================================================================

async def writer_logic(context: synqed.AgentLogicContext) -> dict:
    """
    Writer agent logic
    
    The synqed API now handles:
    - Conversation history extraction (context.get_conversation_history())
    - Markdown code block stripping (automatic in Agent.process())
    - JSON parsing and validation (automatic in Agent.process())
    - Partial/truncated JSON handling (automatic in Agent.process())
    
    Returns:
        dict with "send_to" and "content" keys OR just a string (will be auto-parsed)
    """
    import anthropic
    
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    system_prompt = (
        "You are a creative writer collaborating with an editor. "
        "You write drafts and send them to the Editor for review. "
        "IMPORTANT: ONLY send to USER when the Editor explicitly says 'APPROVED' or 'send to USER'. "
        "Otherwise, ALWAYS send your drafts and revisions to the Editor for feedback. "
        "When Editor approves, use: "
        '{"send_to": "USER", "content": "your final story here"}. '
        "For all drafts and revisions, use: "
        '{"send_to": "Editor", "content": "your draft here"}. '
        "Keep stories under 500 words. Write complete stories, not fragments."
    )
    
    # Get the latest message from memory
    latest_message = context.latest_message
    if not latest_message:
        return context.build_response("Editor", "I'm ready to start writing!")
    
    # Get conversation history automatically!
    # This includes both received AND sent messages, with automatic JSON parsing
    conversation_text = context.get_conversation_history()
    
    # Add instruction to respond
    conversation_text += "\n\nRespond with JSON: {\"send_to\": \"Editor\", \"content\": \"your response\"}"
    
    # Call Anthropic API (async)
    resp = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=800,  
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    # Return the response text
    # The Agent.process() method will automatically:
    # - Strip markdown code blocks
    # - Parse JSON
    # - Handle partial/truncated JSON
    # - Wrap non-JSON responses
    return resp.content[0].text.strip()


async def editor_logic(context: synqed.AgentLogicContext) -> dict:
    """
    Editor agent logic
    
    The synqed API now handles all the boilerplate automatically.
    
    Returns:
        dict with "send_to" and "content" keys OR just a string (will be auto-parsed)
    """
    import anthropic
    
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    system_prompt = (
        "You are an editor collaborating with a writer. "
        "Your job is to review drafts and provide feedback until the story is complete and polished. "
        "WORKFLOW: "
        "1. Writer sends you a draft → You provide specific feedback and send back to Writer "
        "2. Writer revises and sends back → You review again "
        "3. When story is COMPLETE and GOOD, respond with: 'APPROVED - This is ready. Send to USER.' "
        "4. Writer will then send the final version to USER "
        "\n"
        "Be thorough but concise. Check for: completeness, coherence, emotional impact. "
        "Do NOT approve until the story is finished (no cut-offs) and compelling. "
        "Limit to 2-3 revision rounds maximum. "
        "Always respond with JSON: "
        '{"send_to": "Writer", "content": "your feedback or approval here"}'
    )
    
    # Get the latest message from memory
    latest_message = context.latest_message
    if not latest_message:
        return context.build_response("Writer", "I'm ready to edit!")
    
    # Get conversation history automatically
    conversation_text = context.get_conversation_history()
    
    # Add instruction to respond
    conversation_text += "\n\nRespond with JSON: {\"send_to\": \"Writer\", \"content\": \"your response\"}"
    
    # Call Anthropic API (async)
    resp = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,  # Enough for detailed feedback
        system=system_prompt,
        messages=[{"role": "user", "content": conversation_text}],
    )
    
    # 🎯 NEW API: Just return the response text!
    # All parsing and validation happens automatically
    return resp.content[0].text.strip()


# ============================================================================
# Main Execution
# ============================================================================

async def main():
    print("\n" + "="*80)
    print("  Multi-Agent Collaboration - Real-Time Message Display")
    print("  Writer and Editor collaborating on a story")
    print("="*80 + "\n")
    
    # Step 1: Create agents
    writer_agent = synqed.Agent(
        name="Writer",
        description="a creative writer specializing in storytelling and narrative",
        logic=writer_logic,
        default_target="Editor"
    )
    
    editor_agent = synqed.Agent(
        name="Editor",
        description="an editor who reviews and improves written content",
        logic=editor_logic,
        default_target="Writer"
    )
    
    # Step 2: Register agents 
    synqed.AgentRuntimeRegistry.register("Writer", writer_agent)
    synqed.AgentRuntimeRegistry.register("Editor", editor_agent)
    
    # Step 3: Create workspace manager and execution engine
    workspace_manager = synqed.WorkspaceManager(workspaces_root=Path("/tmp/synqed_workspaces"))
    
    planner = synqed.PlannerLLM(
        provider="anthropic",
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model="claude-sonnet-4-5"
    )
    
    # Create execution engine
    # Set max_agent_turns to control how many times agents can respond
    execution_engine = synqed.WorkspaceExecutionEngine(
        planner=planner,
        workspace_manager=workspace_manager,
        enable_display=True,  # Real-time message display
        max_agent_turns=10,  # Maximum 10 agent responses (Writer should send to USER before this)
    )
    
    # Step 4: Create workspace
    task_node = synqed.TaskTreeNode(
        id="collaboration-task",
        description="Writer and Editor collaborating on a story",
        required_agents=["Writer", "Editor"],
        may_need_subteams=False
    )
    
    workspace = await workspace_manager.create_workspace(
        task_tree_node=task_node,
        parent_workspace_id=None
    )
    
    # Step 5: Send user task to Writer
    task = "write a short story about a robot learning to paint. max 5 sentences."
    
    print(f"📋 Task: {task}\n")
    
    await workspace.route_message("USER", "Writer", task, manager=workspace_manager)
    
    # Step 6: Execute the workspace (messages will display in real-time)
    await execution_engine.run(workspace.workspace_id)
    
    # Display transcript with one line
    workspace.display_transcript(title="COMPLETE CONVERSATION TRANSCRIPT")
    
    # Display summary with one line
    workspace.print_summary()
    
    # Clean up
    await workspace_manager.destroy_workspace(workspace.workspace_id)
    
    print("="*80)
    print("✅ Demo complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
