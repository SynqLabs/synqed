# MCP + Zoom Examples with Dynamic Agent Creation

This directory contains example scripts demonstrating AI agents using MCP (Model Context Protocol) tools with Zoom integration. These examples follow synqed best practices where agents are **dynamically created by PlannerLLM** based on the user task.

## Key Principles

### 1. Dynamic Agent Creation
Agents are **not manually created**. Instead:
- User provides a task description
- PlannerLLM analyzes the task
- PlannerLLM creates agent specifications based on requirements
- Agent instances are created from specifications
- Agents are organized into workspaces automatically

### 2. MCP Tools via Context
MCP tools (like Zoom) are **NOT hardcoded in system prompts**. Instead:
- MCP middleware is attached to agents after creation
- Tools are available through `context.mcp` at runtime
- Agents discover available tools dynamically
- No explicit tool listings in agent prompts

### 3. PlannerLLM-Driven Architecture
Following the pattern from `dynamic_agents_email.py`:
- Task breakdown happens FIRST
- Agent specifications created based on subtask requirements
- Agent logic uses `AgentLogicContext`
- Interaction protocols guide agent communication

## Examples

### `single_agent_zoom_mcp.py`
**Single agent dynamically created to handle Zoom tasks**

```bash
python examples/mcp/single_agent_zoom_mcp.py
```

**What it demonstrates:**
- PlannerLLM creates one agent based on task
- Agent has access to Zoom MCP tools via context
- Agent executes Zoom-related tasks (create meetings, list meetings, etc.)
- Tools discovered at runtime, not hardcoded

**Architecture:**
```
User Task → PlannerLLM → Agent Spec → Agent Instance → MCP Middleware → Execution
```

### `two_agents_zoom_mcp.py`
**Two collaborative agents dynamically created for complex tasks**

```bash
python examples/mcp/two_agents_zoom_mcp.py
```

**What it demonstrates:**
- PlannerLLM creates 2+ agents based on task complexity
- Agents collaborate in shared workspace
- Both agents have access to Zoom MCP tools
- Agents discuss and decide who uses which tools
- Role-based task distribution

**Architecture:**
```
User Task → PlannerLLM → Agent Specs → Agent Instances → MCP Middleware
                                                          ↓
                              Workspace ← Collaboration → Execution
```

## Setup

### 1. Deploy Global MCP Server

```bash
cd synq-mcp-server
fly apps create synq-mcp-yourname
./deploy.sh
```

### 2. Configure Zoom Credentials

On Fly.io, set these secrets:

```bash
fly secrets set ZOOM_API_KEY="your-client-id"
fly secrets set ZOOM_API_SECRET="your-client-secret"
fly secrets set ZOOM_ACCOUNT_ID="your-account-id"
```

Get these from: https://marketplace.zoom.us/ (create Server-to-Server OAuth app)

### 3. Set Environment Variables

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export SYNQ_GLOBAL_MCP_ENDPOINT="https://synq-mcp-yourname.fly.dev"
```

### 4. Install Dependencies

```bash
pip install anthropic httpx synqed
cd synqed-python
pip install -e .
```

## How It Works

### Step 1: PlannerLLM Analyzes Task

```python
task_plan, agent_specs = await planner.plan_task_and_create_agent_specs(
    user_task="Schedule team meetings via Zoom",
    agent_provider="anthropic",
    agent_api_key=api_key,
    agent_model="claude-sonnet-4-20250514"
)
```

**PlannerLLM:**
- Breaks down task into subtasks
- Identifies required agent capabilities
- Creates agent specifications (blueprints)
- Determines workspace structure

### Step 2: Create Agents from Specifications

```python
agents = synqed.create_agents_from_specs(agent_specs)
```

**Result:**
- Actual Agent instances created
- Each has appropriate capabilities
- Email addresses auto-generated
- Logic functions configured

### Step 3: Attach MCP Middleware

```python
mcp_middleware = create_mcp_middleware(
    router=None,
    a2a_client=None,
    mode="cloud",
    endpoint=f"{mcp_endpoint}/mcp"
)

for agent in agents:
    mcp_middleware.attach(agent)
```

**Effect:**
- Agents get access to MCP tools via context
- No system prompt modifications needed
- Tools discovered at runtime
- Same middleware for all agents

### Step 4: Execute in Workspace

```python
root_workspace, child_workspaces = await execution_engine.execute_task_plan(
    task_plan=task_plan,
    user_task=user_task
)
```

**Execution:**
- Workspaces created from task plan
- Tasks distributed to agents
- Agents collaborate via email-like messaging
- MCP tools used as needed

## Agent Logic Pattern

Agents use the `AgentLogicContext` pattern:

```python
async def agent_logic(context: synqed.AgentLogicContext) -> dict:
    # Access conversation history
    history = context.get_conversation_history(workspace_wide=True)
    
    # Access latest message
    latest = context.latest_message
    
    # Use MCP tools (available via context)
    if hasattr(context, 'mcp'):
        result = await context.mcp.call_tool('zoom.create_meeting', {
            "topic": "Team Meeting",
            "start_time": "2025-11-25T14:00:00Z",
            "duration": 60
        })
    
    # Return response
    return {...}
```

**Key Points:**
- No explicit MCP tool definitions in prompt
- Tools accessed via `context.mcp`
- Agents discover available tools at runtime
- Clean separation of concerns

## Comparison: Old vs New Approach

### ❌ Old Approach (Hardcoded)

```python
# Manual agent creation
agent = Agent(
    name="zoom_assistant",
    system_prompt="""
    Available tools:
    - zoom.create_meeting(topic, start_time, duration)
    - zoom.list_meetings(type)
    ...
    """
)
```

**Problems:**
- Tools hardcoded in system prompt
- Manual agent creation
- No dynamic task adaptation
- Brittle when tools change

### ✅ New Approach (Dynamic)

```python
# PlannerLLM creates agents
task_plan, agent_specs = await planner.plan_task_and_create_agent_specs(
    user_task="Schedule meetings"
)
agents = synqed.create_agents_from_specs(agent_specs)

# MCP attached via middleware
mcp_middleware.attach(agents[0])
# Tools available via context.mcp (discovered at runtime)
```

**Benefits:**
- Agents created based on task needs
- Tools via context, not system prompt
- Scales to complex multi-agent systems
- Easy to add new tools (no prompt changes)

## Available MCP Tools

When the Global MCP Server is deployed and configured:

### Zoom Tools
- `zoom.create_meeting` - Schedule new meetings
- `zoom.list_meetings` - List upcoming/scheduled meetings
- `zoom.get_meeting` - Get meeting details
- `zoom.delete_meeting` - Cancel meetings
- `zoom.get_user_info` - Get user information

Tools are discovered at runtime - no need to update agent prompts when new tools are added!

## Example Tasks

Try these tasks with the scripts:

### Simple Tasks (Single Agent)
```
"Schedule a team standup meeting every day at 9am for 15 minutes"
"Show me my upcoming Zoom meetings for this week"
"Cancel all meetings scheduled for tomorrow"
```

### Complex Tasks (Multiple Agents)
```
"Organize a product launch with internal planning meetings and client presentations"
"Schedule a conference with 5 speaker sessions and 3 networking breakouts"
"Plan our quarterly review with executive sessions and team retrospectives"
```

## Troubleshooting

### MCP Server Not Reachable
```
⚠️  Could not connect to MCP Server
```

**Solution:**
1. Verify MCP server is deployed: `fly status -a synq-mcp-yourname`
2. Check endpoint is correct: `echo $SYNQ_GLOBAL_MCP_ENDPOINT`
3. Test manually: `curl https://your-mcp-server.fly.dev/health`

### Zoom API Errors
```
❌ Tool failed: Failed to authenticate with Zoom
```

**Solution:**
1. Verify Zoom credentials are set on Fly.io
2. Check app has required scopes (meeting:write:admin, meeting:read:admin)
3. Ensure using Server-to-Server OAuth (not JWT)

### No Agents Created
```
✅ Created 0 agent specification(s)
```

**Solution:**
- Make task more specific
- Include explicit mention of Zoom or meetings
- Check ANTHROPIC_API_KEY is valid

## Further Reading

- [synqed Documentation](../../synqed-python/README.md)
- [Global MCP Server Setup](../../synq-mcp-server/README.md)
- [PlannerLLM Guide](../../synqed-python/docs/planner.md)
- [Dynamic Agent Creation Pattern](../email/dynamic_agents_email.py)

## Key Takeaways

1. **Let PlannerLLM create agents** - Don't hardcode agent definitions
2. **MCP via context** - Tools available at runtime, not in prompts
3. **Task-driven architecture** - Agents adapt to task requirements
4. **Scalable pattern** - Same approach works for 1 agent or 100
5. **Clean separation** - Business logic separate from tool access

