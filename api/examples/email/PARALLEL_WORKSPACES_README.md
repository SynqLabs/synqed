# Parallel Workspaces with Email Communication

This example demonstrates running **3 parallel workspaces** with email addressing, where multiple independent conversations happen simultaneously.

## Overview

Three agents communicate via email in three parallel workspaces:

1. **Workspace 1**: `alice@wonderland` ↔ `bob@builder` (treehouse construction)
2. **Workspace 2**: `alice@wonderland` ↔ `charlie@design` (design aesthetics)
3. **Workspace 3**: `bob@builder` ↔ `charlie@design` (material-design collaboration)

Each workspace operates independently with its own conversation thread.

## Agents

- **alice@wonderland** - A curious explorer
- **bob@builder** - A helpful construction worker
- **charlie@design** - A creative designer

## Files

1. **agent_alice.py** - Alice agent (curious explorer)
2. **agent_bob.py** - Bob agent (helpful builder)
3. **agent_charlie.py** - Charlie agent (creative designer)
4. **parallel_workspaces.py** - Main script that runs 3 parallel conversations

## Requirements

```bash
pip install synqed anthropic python-dotenv
```

## Setup

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY='sk-ant-...'
```

Or create a `.env` file in the parent directory:
```
ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

### Simple: Run the parallel demo

```bash
python parallel_workspaces.py
```

This will:
1. Create and register all 3 agents with their email addresses
2. Register their runtimes for auto-workspace creation
3. Create 3 independent workspaces
4. Send initial messages to each workspace
5. Execute all 3 conversations in parallel using `asyncio.gather()`
6. Display results from all conversations

### Advanced: Customize max turns

Edit `parallel_workspaces.py` and change the `max_agent_turns` parameter:

```python
asyncio.run(main(max_agent_turns=10))  # Default is 8
```

## Example Output

```
================================================================================
🚀 PARALLEL WORKSPACES DEMO: 3 Simultaneous Email Conversations
================================================================================

📧 Agents:
  ✓ alice@wonderland
  ✓ bob@builder
  ✓ charlie@design

Registering agents on cloud...
✓ Registered alice@wonderland
✓ Registered bob@builder
✓ Registered charlie@design

Registering agent runtimes...
✓ Runtime registered for alice@wonderland
✓ Runtime registered for bob@builder
✓ Runtime registered for charlie@design

Configuring auto-workspaces (max_agent_turns=8)...
✓ Auto-workspace configured

================================================================================
🎬 STARTING 3 PARALLEL CONVERSATIONS
================================================================================

🏗️ Workspace 1: Treehouse Construction
   alice@wonderland → bob@builder
   Message: "Hi Bob! I need your help building a magical treehouse..."

🎨 Workspace 2: Design Aesthetics
   alice@wonderland → charlie@design
   Message: "Hey Charlie! I'm working on a treehouse project..."

🤝 Workspace 3: Material Design Collaboration
   bob@builder → charlie@design
   Message: "Charlie, I'm building a treehouse. What materials..."

Setting up Workspace 1: Treehouse Construction...
✓ Created workspace: workspace_1234

Setting up Workspace 2: Design Aesthetics...
✓ Created workspace: workspace_5678

Setting up Workspace 3: Material Design Collaboration...
✓ Created workspace: workspace_9012

================================================================================
⚡ EXECUTING 3 WORKSPACES IN PARALLEL
================================================================================

🏗️ Starting: Workspace 1: Treehouse Construction (ID: workspace_1234)
🎨 Starting: Workspace 2: Design Aesthetics (ID: workspace_5678)
🤝 Starting: Workspace 3: Material Design Collaboration (ID: workspace_9012)

⏳ Processing all conversations in parallel...

💬 Bob's response: Great idea! For a magical treehouse, I'd suggest using enchanted oak...

🎨 Charlie's response: Ooh, I love this! Let's go with pastel colors and flowing curves...

💬 Charlie's response: For whimsical design, I'd recommend lightweight cedar or bamboo...

💬 Alice's response: Enchanted oak sounds perfect! What about the foundation?

💬 Alice's response: Pastel colors would be amazing! What about the roof?

💬 Bob's response: Cedar is perfect! Should we use natural finish or stain?

...

================================================================================
📊 RESULTS SUMMARY
================================================================================

✅ Workspace 1: Treehouse Construction
   alice@wonderland ↔ bob@builder

✅ Workspace 2: Design Aesthetics
   alice@wonderland ↔ charlie@design

✅ Workspace 3: Material Design Collaboration
   bob@builder ↔ charlie@design

================================================================================
🎉 ALL PARALLEL CONVERSATIONS COMPLETE!
================================================================================
```

## How It Works

### 1. Agent Setup
Each agent is created with:
- A unique name (alice, bob, charlie)
- A role (wonderland, builder, design)
- Email format: `name@role`
- AI logic using Anthropic Claude

### 2. Workspace Creation
For each conversation:
- Sender sends email to recipient via cloud
- Auto-workspace manager creates a workspace
- Initial message is routed to the workspace

### 3. Parallel Execution
```python
# Create tasks for each workspace
tasks = [
    asyncio.create_task(execution_engine.run(workspace1_id)),
    asyncio.create_task(execution_engine.run(workspace2_id)),
    asyncio.create_task(execution_engine.run(workspace3_id)),
]

# Execute all in parallel
await asyncio.gather(*tasks)
```

### 4. Independent Processing
- Each workspace maintains its own conversation history
- Agents respond based on their workspace context
- No cross-contamination between workspaces
- All conversations progress simultaneously

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Synqed Cloud Infrastructure                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                 ┌────────────┼────────────┐
                 │            │            │
         ┌───────▼─────┐ ┌───▼─────┐ ┌────▼──────┐
         │ Workspace 1 │ │ Workspace 2 │ │ Workspace 3 │
         │ (Thread 1)  │ │ (Thread 2)  │ │ (Thread 3)  │
         └─────────────┘ └─────────────┘ └────────────┘
              │ ▲            │ ▲            │ ▲
              ▼ │            ▼ │            ▼ │
         ┌─────────┐    ┌──────────┐   ┌──────────┐
         │  Alice  │    │  Alice   │   │   Bob    │
         │   ↕     │    │    ↕     │   │    ↕     │
         │   Bob   │    │ Charlie  │   │ Charlie  │
         └─────────┘    └──────────┘   └──────────┘
```

## Key Features

- ✅ **3 Parallel Workspaces** - Independent conversations running simultaneously
- ✅ **Email Addressing** - Simple `name@role` format for all agents
- ✅ **Auto-Workspace Creation** - Automatic workspace management
- ✅ **Async Execution** - Uses `asyncio.gather()` for true parallelism
- ✅ **Thread Isolation** - Each workspace has its own conversation history
- ✅ **Cloud Routing** - All messages routed through synqed cloud
- ✅ **Real-time Display** - Agent responses printed as they happen
- ✅ **Error Handling** - Graceful handling of failures in individual workspaces

## Customization

### Change Conversation Topics
Edit the `conversations` list in `parallel_workspaces.py`:

```python
conversations = [
    {
        "name": "Workspace 1: Your Topic",
        "sender": alice,
        "recipient": bob,
        "thread_id": "unique-thread-id",
        "message": "Your message here",
        "emoji": "🔥"
    },
    # ... add more conversations
]
```

### Add More Agents
1. Create a new agent file (e.g., `agent_dave.py`)
2. Import it in `parallel_workspaces.py`
3. Add it to the `agents` list
4. Create new conversation pairs

### Adjust Max Turns
Change how many exchanges happen per workspace:

```python
asyncio.run(main(max_agent_turns=15))  # More exchanges
```

### Change AI Model
Edit each agent's logic function:

```python
response = await anthropic_client.messages.create(
    model="claude-3-5-sonnet-20241022",  # Different model
    max_tokens=200,  # More tokens
    # ...
)
```

## Benefits of Parallel Workspaces

1. **Efficiency** - Multiple conversations progress simultaneously
2. **Scalability** - Can handle many concurrent conversations
3. **Independence** - Each workspace has isolated state
4. **Real-world Simulation** - Mimics how agents would operate in production
5. **Resource Optimization** - Maximizes API and compute utilization

## Notes

- Each workspace maintains independent conversation history
- Agents can participate in multiple workspaces simultaneously
- Uses asyncio for true parallel execution
- All messages are authenticated and encrypted via synqed cloud
- Workspaces automatically clean up after completion

## License

See the main LICENSE file in the repository root.

