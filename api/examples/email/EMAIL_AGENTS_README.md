# Simple Email Communication with Synqed Agents

Three simple scripts demonstrating synqed agents communicating via email addresses using Anthropic AI.

## Overview

- **alice@wonderland** - A curious explorer
- **bob@builder** - A helpful builder

Each agent is in its own file. A third script sends an email from Alice to Bob, and Bob's response is printed to terminal.

## Files

1. **agent_alice.py** - Creates and registers Alice
2. **agent_bob.py** - Creates and registers Bob
3. **send_email.py** - Alice sends Bob an email

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

### Option 1: Run agents individually first

```bash
# Terminal 1: Create and register Alice
python agent_alice.py

# Terminal 2: Create and register Bob  
python agent_bob.py

# Terminal 3: Send email from Alice to Bob
python send_email.py
```

### Option 2: Just send the email (simplest)

The `send_email.py` script creates and registers both agents automatically:

```bash
python send_email.py
```

This will:
1. Create both agents with their email addresses
2. Register them on the synqed cloud
3. Register their runtimes
4. Send a message from Alice to Bob
5. Print Bob's response to the terminal

## Example Output

```
======================================================================
📧 SENDING EMAIL: alice@wonderland → bob@builder
======================================================================

✓ Created alice@wonderland
✓ Created bob@builder

Registering agents...
✓ Registered alice@wonderland
✓ Registered bob@builder

Registering runtimes...
✓ Registered runtime for alice@wonderland
✓ Registered runtime for bob@builder

Sending message from alice@wonderland to bob@builder...
Message: "Hi Bob! Can you help me with something?"

✅ Email sent! (Message ID: msg_...)

Processing message through auto-workspace...

======================================================================
📨 BOB'S RESPONSE:
======================================================================
Of course, Alice! What do you need help with?
======================================================================

✅ Bob processed the message!

======================================================================
✅ DONE
======================================================================
```

## How It Works

1. **Synqed Agents**: Each agent is created using `synqed.Agent()` with:
   - A name (e.g., "alice")
   - A role (e.g., "wonderland") 
   - Email is automatically: `name@role`
   - An AI logic function using Anthropic API

2. **Cloud Registration**: Agents are registered on synqed cloud with cryptographic keys

3. **Runtime Registration**: Agents register their runtime to enable auto-workspace creation

4. **Email Sending**: Alice sends an email to Bob's email address

5. **Auto-Processing**: Synqed automatically:
   - Creates a workspace
   - Routes the message to Bob
   - Calls Bob's logic function
   - Bob's response is printed to terminal

## Key Features

- ✓ **Synqed agents** - Using full synqed infrastructure
- ✓ **Anthropic AI** - Claude Sonnet 4 for natural responses
- ✓ **Email addressing** - Simple name@role format
- ✓ **Auto-workspace** - Automatic workspace creation
- ✓ **Cloud messaging** - Messages routed through synqed cloud
- ✓ **Terminal output** - Bob's response printed to console

## Architecture

```
agent_alice.py              send_email.py              agent_bob.py
     │                           │                           │
     ├─ Create Alice             ├─ Alice sends email       ├─ Create Bob
     ├─ Register on cloud        │   to bob@builder         ├─ Register on cloud
     └─ Register runtime         │                           └─ Register runtime
                                 │
                                 ▼
                        Synqed Cloud
                    (Auto-workspace routing)
                                 │
                                 ▼
                         Bob processes message
                                 │
                                 ▼
                        Response → Terminal
```

## Customization

You can easily modify:

- **Agent personalities**: Change the `system_prompt` in each agent's logic function
- **Email content**: Modify the `message` in `send_email.py`
- **Response format**: Adjust how Bob's response is printed
- **AI model**: Change `claude-sonnet-4-20250514` to another Anthropic model
- **Email addresses**: Change `name` and `role` parameters

## Notes

- Agents use Anthropic's Claude Sonnet 4 by default
- Conversation history is maintained per workspace
- Messages are routed through synqed cloud infrastructure
- Each agent can process messages independently
- Bob's logic function includes the terminal output

## License

See the main LICENSE file in the repository root.
