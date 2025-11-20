"""
Code Review A2A Agent - Built with a2a-python SDK (NOT Synqed)

ARCHITECTURE DIAGRAM:
┌──────────────────────────────────────────────────────────┐
│ Standalone A2A Agent Server (http://localhost:8001)      │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ A2A HTTP Server (Starlette + uvicorn)                │ │
│ │                                                      │ │
│ │ Endpoints:                                           │ │
│ │ • GET  /.well-known/agent-card.json  (AgentCard)     │ │
│ │ • POST /  (JSON-RPC: message/send, task/get, etc.)   │ │
│ └─────────────────┬────────────────────────────────────┘ │
│                   │                                      │
│                   ▼                                      │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ LoggingRequestHandler (A2A Request Handler)          │ │
│ │ • Processes JSON-RPC requests                        │ │
│ │ • Extracts messages from A2A format                  │ │
│ │ • Logs all requests/responses                        │ │
│ └─────────────────┬────────────────────────────────────┘ │
│                   │                                      │
│                   ▼                                      │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ CodeReviewAgentExecutor (A2A AgentExecutor)          │ │
│ │ • Implements A2A execute() interface                 │ │
│ │ • Manages event queue for responses                  │ │
│ └─────────────────┬────────────────────────────────────┘ │
│                   │                                      │
│                   ▼                                      │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ CodeReviewAgent (Core Logic)                         │ │
│ │ • Uses Claude API for code review                    │ │
│ │ • Analyzes code and provides feedback                │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘

SYNQED INTEGRATION:
When used with Synqed, messages flow like this:

Synqed Workspace → RemoteA2AAgent → HTTP POST to localhost:8001
                                  → JSON-RPC "message/send"
                                  → Response flows back via A2A protocol

This is a REAL A2A agent built using the a2a-python SDK.
It demonstrates that Synqed can route to agents built with ANY framework,
as long as they implement the A2A protocol.

This agent:
- Built with a2a-python SDK (not Synqed)
- Exposes A2A endpoints (AgentCard, message/send, etc.)
- Can be hosted anywhere
- Synqed routes to it via RemoteA2AAgent

Run: python code_review_a2a_agent.py
Then it will be available at http://localhost:8001
"""

import asyncio
import os
import logging
import json
from dotenv import load_dotenv
from typing import Any, Dict

# A2A SDK imports
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler, RequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskStore
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Message,
    Task,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeReviewAgent:
    """
    Core agent logic for code review.
    
    This agent uses an LLM to perform code review analysis.
    Built with standard Python + LLM calls (not Synqed).
    """
    
    def __init__(self):
        """Initialize the code review agent."""
        self.name = "CodeReviewAgent"
    
    async def review(self, message: str) -> str:
        """
        Perform code review on the given message/request.
        
        Args:
            message: The user's request or code to review
            
        Returns:
            Code review analysis as a string
        """
        # Use Anthropic Claude for code review
        import anthropic
        
        client = anthropic.AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        prompt = f"""You are a code review expert agent.

User request: {message}

Provide insightful code review feedback. If the user provides code, analyze it.
If they describe a concept, explain code quality principles related to it.

Keep your response concise (2-3 paragraphs).

Return JSON format: {{"send_to": "Coordinator", "content": "Your analysis"}}"""
        
        response = await client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text.strip()


class CodeReviewAgentExecutor(AgentExecutor):
    """
    A2A Agent Executor for Code Review.
    
    This implements the A2A AgentExecutor interface, making our agent
    compatible with the A2A protocol.
    """
    
    def __init__(self):
        """Initialize the executor with the core agent."""
        self.agent = CodeReviewAgent()
        logger.info("CodeReviewAgentExecutor initialized")
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Execute the agent logic.
        
        This is called when the agent receives a message via A2A protocol.
        
        Args:
            context: Request context containing the incoming message
            event_queue: Queue for emitting response events
        """
        logger.info("=" * 80)
        logger.info("EXECUTING CODE REVIEW AGENT")
        logger.info("=" * 80)
        
        # Log the raw context for debugging
        logger.info(f"Context type: {type(context)}")
        logger.info(f"Context attributes: {dir(context)}")
        
        # Extract the user message from context
        # context.message contains the A2A Message object
        user_message = ""
        if context.message:
            logger.info(f"Message type: {type(context.message)}")
            logger.info(f"Message ID: {getattr(context.message, 'message_id', 'N/A')}")
            logger.info(f"Message role: {getattr(context.message, 'role', 'N/A')}")
            
            if hasattr(context.message, 'parts') and context.message.parts:
                logger.info(f"Number of message parts: {len(context.message.parts)}")
                for i, part in enumerate(context.message.parts):
                    logger.info(f"Part {i}: type={type(part)}")
                    
                    # Try multiple ways to extract text from Part
                    text_content = None
                    
                    # Method 1: Direct text attribute
                    if hasattr(part, 'text'):
                        text_content = part.text
                        logger.info(f"Part {i} - Method 1 (direct .text): {text_content}")
                    
                    # Method 2: root attribute (for pydantic RootModel/discriminated unions)
                    if not text_content and hasattr(part, 'root'):
                        logger.info(f"Part {i} - Trying root attribute: {type(part.root)}")
                        if hasattr(part.root, 'text'):
                            text_content = part.root.text
                            logger.info(f"Part {i} - Method 2 (root.text): {text_content}")
                        elif isinstance(part.root, str):
                            text_content = part.root
                            logger.info(f"Part {i} - Method 2 (root is str): {text_content}")
                    
                    # Method 3: model_dump to see structure
                    if not text_content and hasattr(part, 'model_dump'):
                        part_dict = part.model_dump()
                        logger.info(f"Part {i} - model_dump: {part_dict}")
                        if 'text' in part_dict:
                            text_content = part_dict['text']
                            logger.info(f"Part {i} - Method 3 (model_dump['text']): {text_content}")
                        elif 'root' in part_dict and isinstance(part_dict['root'], dict) and 'text' in part_dict['root']:
                            text_content = part_dict['root']['text']
                            logger.info(f"Part {i} - Method 3 (model_dump['root']['text']): {text_content}")
                    
                    if text_content:
                        logger.info(f"Part {i} extracted text (first 200 chars): {text_content[:200]}...")
                        user_message += text_content
                    else:
                        logger.warning(f"Part {i} - Could not extract text content!")
        else:
            logger.warning("No message in context!")
        
        logger.info(f"Final extracted message (length={len(user_message)}): {user_message[:200]}...")
        
        if not user_message:
            logger.error("Empty message extracted from context!")
            await event_queue.enqueue_event(
                new_agent_text_message("Error: No message content received")
            )
            return
        
        # Process with the agent
        logger.info("Calling agent.review()...")
        result = await self.agent.review(user_message)
        
        logger.info(f"Agent generated response (length={len(result)}): {result[:200]}...")
        
        # Emit the response via event queue
        # This will be picked up by the A2A server and sent back to the caller
        logger.info("Enqueuing response event...")
        await event_queue.enqueue_event(new_agent_text_message(result))
        
        logger.info("✅ Code review agent execution complete")
        logger.info("=" * 80)
    
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue
    ) -> None:
        """
        Cancel task execution.
        
        For this simple agent, we don't support cancellation.
        """
        logger.warning("Cancel requested but not supported")
        raise Exception("Cancel not supported for CodeReviewAgent")


class LoggingRequestHandler(DefaultRequestHandler):
    """
    Custom request handler that logs all incoming requests for debugging.
    
    This extends DefaultRequestHandler to add logging without changing behavior.
    """
    
    def __init__(self, agent_executor: AgentExecutor, task_store: TaskStore):
        """Initialize with agent executor and task store."""
        super().__init__(agent_executor=agent_executor, task_store=task_store)
        self._agent_executor = agent_executor  # Keep reference for fallback
        logger.info("LoggingRequestHandler initialized")
    
    async def handle_request(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming JSON-RPC request with detailed logging.
        
        Args:
            request_body: The parsed JSON-RPC request
            
        Returns:
            JSON-RPC response
        """
        logger.info("=" * 80)
        logger.info("INCOMING JSON-RPC REQUEST")
        logger.info("=" * 80)
        logger.info(f"Raw request body:\n{json.dumps(request_body, indent=2)}")
        
        # Extract key components
        method = request_body.get("method", "UNKNOWN")
        params = request_body.get("params", {})
        rpc_id = request_body.get("id", "UNKNOWN")
        
        logger.info(f"Method: {method}")
        logger.info(f"ID: {rpc_id}")
        logger.info(f"Params keys: {list(params.keys())}")
        
        if "message" in params:
            message = params["message"]
            logger.info(f"Message structure: {json.dumps(message, indent=2)}")
        
        if "configuration" in params:
            config = params["configuration"]
            logger.info(f"Configuration: {json.dumps(config, indent=2)}")
        
        logger.info("Delegating to parent DefaultRequestHandler...")
        
        # Delegate to parent implementation
        try:
            response = await super().handle_request(request_body)
            logger.info("=" * 80)
            logger.info("OUTGOING JSON-RPC RESPONSE")
            logger.info("=" * 80)
            logger.info(f"Response:\n{json.dumps(response, indent=2)}")
            logger.info("=" * 80)
            return response
        except Exception as e:
            logger.error(f"❌ Error from DefaultRequestHandler: {e}", exc_info=True)
            logger.info("Attempting fallback manual processing...")
            
            # Fallback: Process manually if DefaultRequestHandler fails
            try:
                return await self._handle_message_manually(request_body, method, params, rpc_id)
            except Exception as fallback_error:
                logger.error(f"❌ Fallback handler also failed: {fallback_error}", exc_info=True)
                # Return JSON-RPC error response
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)} (fallback: {str(fallback_error)})"
                    },
                    "id": rpc_id
                }
    
    async def _handle_message_manually(
        self,
        request_body: Dict[str, Any],
        method: str,
        params: Dict[str, Any],
        rpc_id: Any
    ) -> Dict[str, Any]:
        """
        Manually handle message/send request if DefaultRequestHandler fails.
        
        This ensures compatibility with Synqed's exact JSON-RPC format.
        """
        logger.info("🔧 Manual message handling...")
        
        if method != "message/send":
            raise ValueError(f"Unsupported method: {method}")
        
        # Extract message from params
        message_data = params.get("message")
        if not message_data:
            raise ValueError("No 'message' in params")
        
        # Extract message content
        parts = message_data.get("parts", [])
        content = ""
        for part in parts:
            if "text" in part:
                content += part["text"]
        
        logger.info(f"Extracted content: {content[:200]}...")
        
        # Create a mock RequestContext
        from a2a.types import Message, MessagePart
        
        message = Message(
            message_id=message_data.get("message_id", "manual-msg"),
            context_id=message_data.get("context_id"),
            role=message_data.get("role", "ROLE_USER"),
            parts=[MessagePart(text=content)]
        )
        
        context = RequestContext(message=message, task_id=None)
        event_queue = EventQueue()
        
        # Execute the agent
        logger.info("Executing agent manually...")
        await self._agent_executor.execute(context, event_queue)
        
        # Collect events (the response)
        events = []
        while not event_queue.empty():
            event = await event_queue.dequeue_event()
            events.append(event)
            logger.info(f"Event collected: {event}")
        
        # Build response from events
        if events:
            # The first event should be the agent's response
            response_message = events[0]
            
            # Build Task response
            task = {
                "task_id": f"task-{id(message)}",
                "context_id": message_data.get("context_id"),
                "status": {
                    "state": "COMPLETED",
                    "message": response_message
                },
                "artifacts": [response_message]
            }
            
            logger.info(f"✅ Manual processing complete. Task: {json.dumps(task, indent=2)}")
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "task": task
                },
                "id": rpc_id
            }
        else:
            raise ValueError("No events generated by agent")


def create_agent_card(host: str, port: int) -> AgentCard:
    """
    Create the AgentCard for this agent.
    
    The AgentCard is published at /.well-known/agent-card.json
    and describes the agent's capabilities, skills, and how to call it.
    
    Args:
        host: Host where agent is running
        port: Port where agent is running
        
    Returns:
        AgentCard describing this agent
    """
    skill = AgentSkill(
        id='code_review',
        name='Code Review',
        description='Analyzes code and provides quality feedback',
        tags=['code', 'review', 'quality', 'analysis'],
        examples=[
            'Review this Python function',
            'Analyze code quality',
            'What are best practices for error handling?'
        ],
    )
    
    return AgentCard(
        name='Code Review Agent',
        description='Expert code review agent built with A2A SDK (not Synqed)',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
        ),
        skills=[skill],
    )


def main(host: str = 'localhost', port: int = 8001):
    """
    Start the Code Review A2A Agent server.
    
    This creates an A2A-compliant HTTP server that:
    - Publishes AgentCard at /.well-known/agent-card.json
    - Accepts messages at POST / (JSON-RPC)
    - Returns structured A2A responses
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    logger.info("=" * 80)
    logger.info(f"🚀 Starting Code Review A2A Agent on {host}:{port}")
    logger.info("=" * 80)
    
    # Create agent card
    agent_card = create_agent_card(host, port)
    logger.info(f"✅ Agent card created: {agent_card.name}")
    
    # Create request handler with logging
    request_handler = LoggingRequestHandler(
        agent_executor=CodeReviewAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    logger.info("✅ Request handler created (with logging)")
    
    # Create A2A Starlette application
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    logger.info("✅ A2A server application created")
    
    # Build and run the server
    app = server.build()
    
    logger.info("=" * 80)
    logger.info(f"🌍 Code Review A2A Agent running at http://{host}:{port}")
    logger.info(f"📄 AgentCard available at http://{host}:{port}/.well-known/agent-card.json")
    logger.info("✅ Ready to receive A2A messages from Synqed or any A2A client")
    logger.info("🔍 Logging enabled - will show all requests/responses")
    logger.info("=" * 80)
    
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == '__main__':
    main()

