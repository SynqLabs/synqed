# Single Workspace Email Communication

This example demonstrates how **multiple agents can communicate via email addresses within a single workspace**.

## Overview

Unlike the parallel workspaces example where each conversation happens in separate workspaces, this example shows:

- **ONE workspace** containing multiple agents
- Agents have **email identities** (e.g., `alice@wonderland`, `bob@builder`)
- Within the workspace, agents communicate using **agent names** (e.g., `alice`, `bob`, `charlie`)
- All messages are **routed within the same workspace**
- Real-time conversation display shows the collaborative flow

## Architecture

```
┌─────────────────────────────────────────────────┐
│           Single Workspace                       │
│  (tea-party-planning)                           │
│                                                  │
│  ┌──────────────┐   ┌──────────────┐           │
│  │    Alice     │───│     Bob      │           │
│  │ @wonderland  │   │  @builder    │           │
│  └──────┬───────┘   └──────┬───────┘           │
│         │                   │                    │
│         └───────┬───────────┘                   │
│                 │                                │
│         ┌───────┴────────┐                      │
│         │    Charlie     │                      │
│         │    @chef       │                      │
│         └────────────────┘                      │
│                                                  │
│  All agents share the same workspace memory     │
│  Messages routed by email address               │
└─────────────────────────────────────────────────┘
```

## Agents

1. **Alice** (`alice@wonderland`)
   - Project coordinator
   - Curious explorer from Wonderland
   - Orchestrates the tea party planning

2. **Bob** (`bob@builder`)
   - Construction specialist
   - Handles setup and building aspects
   - Works on physical infrastructure

3. **Charlie** (`charlie@chef`)
   - Culinary expert
   - Creates the menu and food plan
   - Focuses on beverages and cuisine

## How It Works

### 1. Agent Definition with Email

Each agent is created with a `role` parameter that forms their email domain:

```python
alice = synqed.Agent(
    name="alice",
    description="A curious explorer from Wonderland",
    logic=alice_logic,
    role="wonderland",  # Creates email: alice@wonderland
)
```

### 2. Workspace Communication with Email Identities

Each agent has an email identity, but within the workspace they communicate using agent names:

```python
# Alice sending to Bob (using agent name within workspace)
{
    "send_to": "bob",
    "content": "Can you help build a treehouse for the tea party?"
}

# Bob responding to Alice
{
    "send_to": "alice",
    "content": "I'll build tables and decorations!"
}

# Charlie responding to Alice
{
    "send_to": "alice",
    "content": "I'll prepare magical tea and pastries!"
}
```

**Note**: Agents have email addresses as their identity (`alice@wonderland`, `bob@builder`, `charlie@chef`), but use short names (`alice`, `bob`, `charlie`) for routing within the shared workspace.

### 3. Single Workspace Routing

- All agents are registered in ONE workspace
- Messages are routed based on email addresses
- The workspace maintains shared conversation history
- Agents can see all messages in the workspace context

## Key Features

### Email Identities with Name-Based Routing
- Each agent has an email identity (`name@role`) for external identification
- Within the workspace, agents use short names (`alice`, `bob`, `charlie`) for routing
- Simple and efficient communication within the shared workspace context

### Shared Context
- All agents share the same workspace memory
- Each agent can see the full conversation history
- Enables true multi-agent collaboration

### Flexible Communication
- Agents can message any other agent in the workspace
- Dynamic conversation flow (not just sequential)
- Natural back-and-forth coordination
- Direct peer-to-peer collaboration (e.g., Bob ↔ Charlie)

## Usage

### Prerequisites

```bash
pip install synqed anthropic python-dotenv
```

Create a `.env` file with:
```
ANTHROPIC_API_KEY=your-key-here
```

### Run the Example

```bash
python single_workspace_email.py
```

### Expected Output

```
================================================================================
  📧 Single Workspace Email Communication
  Three agents collaborating in ONE workspace via email addresses
================================================================================

👥 Agents created:
   ✓ alice@wonderland - A curious explorer from Wonderland, project coordinator
   ✓ bob@builder - A helpful construction worker, setup specialist
   ✓ charlie@chef - An expert chef specializing in tea party cuisine

✓ Agents registered in runtime registry
✓ Execution engine configured
✓ Workspace created: tea-party-planning-abc123

================================================================================
📋 USER TASK
================================================================================
Alice, coordinate with Bob and Charlie to plan a magical tea party...

================================================================================
💬 CONVERSATION (Real-time)
================================================================================

USER → alice: Alice, coordinate with Bob and Charlie...
alice → bob: Hi Bob! Can you help with the construction setup?
bob → alice: I'll build enchanted tables and whimsical decorations!
alice → charlie: Charlie, can you handle the food and beverages?
charlie → alice: I'll prepare magical tea and wonderland pastries!
alice → bob: Bob, coordinate with Charlie to finalize the designs!
bob → charlie: How does my table setup work with your menu service needs?
charlie → bob: Perfect! I'll adjust the menu presentation to fit your layout.
bob → alice: Design finalized with Charlie - all coordinated!
charlie → alice: Menu finalized with Bob - everything works together!
alice → USER: Here's our complete coordinated tea party plan: [DONE]

================================================================================
✅ Email communication demo complete!
   • Workspace: tea-party-planning-abc123
   • Agents: alice@wonderland, bob@builder, charlie@chef
   • All communication happened in ONE workspace
================================================================================
```

## Comparison with Other Patterns

### vs. Parallel Workspaces
| Single Workspace | Parallel Workspaces |
|-----------------|---------------------|
| One shared workspace | Multiple independent workspaces |
| Shared conversation history | Separate conversation histories |
| All agents see all messages | Agents only see their workspace messages |
| Agents have email identities | Each conversation in separate workspace |
| Better for **collaboration** | Better for **isolation** |
| Example: Team planning a project | Example: Multiple customer conversations |

### vs. Cloud Email Communication
| Workspace-Based | Cloud Email (send_email.py) |
|----------------|----------------------------|
| Local workspace routing | Cloud-based email delivery |
| Name-based within workspace | Full email address routing |
| Synchronous execution | Asynchronous email delivery |
| Shared memory/context | Separate inbox handling |
| Better for **team collaboration** | Better for **distributed agents** |

## Customization

### Add More Agents

```python
# Create a new agent
diana = synqed.Agent(
    name="diana",
    description="Decorator and designer",
    logic=diana_logic,
    role="designer",  # Email: diana@designer
)

# Register it
synqed.AgentRuntimeRegistry.register("diana", diana)
synqed.AgentRuntimeRegistry.register(diana.email, diana)

# Add to workspace task
task_node = synqed.TaskTreeNode(
    required_agents=["alice", "bob", "charlie", "diana"],
    ...
)
```

### Change the Task

Modify the initial task to explore different collaboration scenarios:

```python
# Event planning
task = "Plan a corporate conference with Alice, Bob, and Charlie"

# Product development
task = "Design a new product with the team"

# Content creation
task = "Create a marketing campaign collaboratively"
```

### Adjust Agent Behavior

Modify the system prompts in each agent's logic function to change:
- Communication style
- Expertise areas
- Decision-making patterns
- Collaboration strategies

## Technical Details

### Agent Logic Structure

Each agent's logic function:
1. Receives `AgentLogicContext` with conversation history
2. Calls LLM API with conversation context
3. Returns JSON with `send_to` (email address) and `content`
4. Framework automatically parses and routes the message

### Workspace Execution

The `WorkspaceExecutionEngine`:
- Manages message routing within the workspace
- Enforces `max_agent_turns` to prevent infinite loops
- Displays messages in real-time if `enable_display=True`
- Handles agent scheduling based on message queue

### Email Resolution

When an agent sends to an email address:
1. Framework extracts recipient from `send_to` field
2. Looks up agent in `AgentRuntimeRegistry` by email
3. Routes message to the resolved agent
4. Agent receives message in its next execution

## Benefits

✅ **Natural Communication**: Email addresses are familiar and intuitive

✅ **Flexible Routing**: Agents can message any team member dynamically

✅ **Shared Context**: All agents have access to the full conversation

✅ **Scalable**: Easy to add new agents to the workspace

✅ **Real-World Pattern**: Mimics how human teams communicate

## Use Cases

- **Team Collaboration**: Multiple specialists working together
- **Project Planning**: Coordinating across different roles
- **Problem Solving**: Experts from different domains collaborating
- **Creative Work**: Writers, editors, designers working together
- **Customer Service**: Team handling complex customer inquiries

## Next Steps

- Explore `parallel_workspaces.py` for isolated multi-agent conversations
- Check out `send_email.py` for cloud-based email delivery
- Review `workspace.py` for more workspace features
- Read the synqed documentation for advanced patterns

