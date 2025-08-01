"""
Agent Manager for Teams Agent Bot using OpenAI Agents SDK.

This module manages agent interactions using the openai-agents framework
with proper context handling and message history.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from agents import Agent, Runner, trace, RunContextWrapper, TResponseInputItem, RunHooks
from pydantic import BaseModel

from config.settings import settings
from utils.logger import get_logger, log_function_call, log_function_result, log_error_with_context
from storage.message_history import message_history, MessageRole
from openai_agents.azure_vm_tools import get_azure_vm_tools
from openai_agents.servicenow_catalog_tools import get_servicenow_catalog_tools
from openai_agents.servicenow_variables_tools import get_servicenow_variables_tools
from openai_agents.instructions.concierge_agent import concierge_agent_instructions
from openai_agents.instructions.azure_vm_agent import azure_vm_agent_instructions
from openai_agents.instructions.servicenow_catalog_creation_agent import servicenow_catalog_creation_agent_instructions
from openai_agents.instructions.servicenow_variables_agent import servicenow_variables_agent_instructions
from openai_agents.models import UserContext
from openai_agents.agent_state_manager import get_agent_state_manager

logger = get_logger(__name__)


# ---------- JSON Logger Setup ----------
class JSONFormatter(logging.Formatter):
    def format(self, record):
        if isinstance(record.msg, dict):
            return json.dumps(record.msg)
        return json.dumps({"event": record.msg})

agent_logger = logging.getLogger("agent_logger")
agent_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
agent_logger.addHandler(agent_logger)


# ---------- Conversation History Manager ----------
class ConversationHistoryManager:
    """Manages conversation history for users using the input parameter approach."""
    
    def __init__(self):
        self._conversations: Dict[str, List[TResponseInputItem]] = {}
    
    def get_conversation_history(self, user_id: str) -> List[TResponseInputItem]:
        """Get conversation history for a user."""
        return self._conversations.get(user_id, [])
    
    def add_message(self, user_id: str, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        if user_id not in self._conversations:
            self._conversations[user_id] = []
        
        message: TResponseInputItem = {
            "role": role,
            "content": content
        }
        self._conversations[user_id].append(message)
        logger.debug(f"Added message to conversation for user {user_id}: {role}")
    
    def update_conversation_from_result(self, user_id: str, result) -> None:
        """Update conversation history from a run result."""
        if hasattr(result, 'to_input_list'):
            self._conversations[user_id] = result.to_input_list()
            logger.debug(f"Updated conversation history for user {user_id}")
    
    def clear_conversation(self, user_id: str) -> None:
        """Clear conversation history for a user."""
        if user_id in self._conversations:
            del self._conversations[user_id]
            logger.info(f"Cleared conversation history for user {user_id}")


# Global conversation history manager
conversation_manager = ConversationHistoryManager()


# ---------- User Context ----------
# UserContext is now imported from openai_agents.models


# ---------- Agent Instructions ----------
# Instructions are now imported from separate files:
# - openai_agents.instructions.concierge_agent
# - openai_agents.instructions.azure_vm_agent


# ---------- Agents Setup ----------

# First, create all agents without handoffs to avoid circular dependencies
concierge_agent = Agent[UserContext](
    name="ConciergeAgent",
    instructions=concierge_agent_instructions,
    model="gpt-4o-mini",
    handoffs=[]  # Will be set after all agents are created
)
azure_vm_agent = Agent[UserContext](
    name="AzureVMAgent",
    instructions=azure_vm_agent_instructions,
    tools=get_azure_vm_tools(),
    model="gpt-4o-mini",
    handoffs=[]  # Will be set after all agents are created
)
servicenow_variables_agent = Agent[UserContext](
    name="ServiceNowVariablesAgent",
    instructions=servicenow_variables_agent_instructions,
    tools=get_servicenow_variables_tools(),
    model="gpt-4o-mini",
    handoffs=[]  # Will be set after all agents are created
)
servicenow_catalog_creation_agent = Agent[UserContext](
    name="ServiceNowCatalogCreationAgent",
    instructions=servicenow_catalog_creation_agent_instructions,
    tools=get_servicenow_catalog_tools(),
    model="gpt-4o-mini",
    handoffs=[]  # Will be set after all agents are created
)

# Now set up the handoffs after all agents are created
concierge_agent.handoffs = [azure_vm_agent, servicenow_catalog_creation_agent, servicenow_variables_agent]
azure_vm_agent.handoffs = [concierge_agent]
servicenow_variables_agent.handoffs = [concierge_agent]
servicenow_catalog_creation_agent.handoffs = [servicenow_variables_agent, concierge_agent]



# ---------- Agent Lookup Dictionary ----------
AGENT_LOOKUP = {
    "ConciergeAgent": concierge_agent,
    "AzureVMAgent": azure_vm_agent,
    "ServiceNowCatalogCreationAgent": servicenow_catalog_creation_agent,
    "ServiceNowVariablesAgent": servicenow_variables_agent,
}


# ---------- State Manager ----------
state_manager = get_agent_state_manager()


class WaitNotificationHooks(RunHooks):
    """Hooks for sending wait notifications when long-running tools start."""
    
    def __init__(self, user_id: str = "", room_id: str = "", message_callback=None):
        self.user_id = user_id
        self.room_id = room_id
        self.message_callback = message_callback  # Callback function to send messages
        self.notified_tools = set()  # Track which tools we've already notified for
        
    async def on_tool_start(self, context, agent, tool):
        # Check if this tool is enabled for this agent
        if not settings.wait_tools.is_wait_tool(agent.name, tool.name):
            # Tool is not enabled for this agent - this should be handled by tool filtering
            logger.warning(f"Tool {tool.name} not enabled for agent {agent.name}")
            return
            
        # Check if this tool should trigger a wait message (create/modify tools)
        create_modify_tools = [
            "create_catalog_item", "create_and_publish_catalog_item", "publish_catalog_item",
            "create_string_variable", "create_boolean_variable", "create_choice_variable",
            "create_multiple_choice_variable", "create_date_variable",
            "create_vm", "start_vm", "stop_vm", "delete_vm"
        ]
        
        should_show_wait = tool.name in create_modify_tools
        
        if should_show_wait and tool.name not in self.notified_tools:
            self.notified_tools.add(tool.name)
            
            # Send wait message if callback is available
            if self.message_callback:
                try:
                    await self.message_callback("While I am on it, please wait...")
                except Exception as e:
                    logger.warning(f"Failed to send wait message: {e}")
            else:
                # For CLI testing, just log the wait message
                logger.info(f"⏳ {agent.name} is working on {tool.name}... Please wait.")





async def process_user_message(user_id: str, room_id: str = "default", message: str = "", user_name: Optional[str] = None) -> str:
    """
    Process a user message with persistent agent state and conversation history.
    
    Args:
        user_id: The user ID
        room_id: The room/channel ID (optional, defaults to "default")
        message: The user's message
        user_name: Optional user name
        
    Returns:
        The agent's response
    """
    log_function_call(logger, "process_user_message", 
                     user_id=user_id, room_id=room_id, message_length=len(message))
    
    try:
        # Check for special commands first
        message_lower = message.strip().lower()
        
        if message_lower == "/reset":
            # Clear conversation history and reset to concierge agent
            conversation_manager.clear_conversation(user_id)
            state_manager.set_current_agent(user_id, "ConciergeAgent")
            logger.info({
                "event": "conversation_reset",
                "user_id": user_id,
                "command": "/reset"
            })
            return "🔄 **Conversation reset!** I'm now your concierge assistant. How can I help you today?"
        
        elif message_lower == "/help":
            # Show available commands
            help_text = """
🤖 **Available Commands:**

**/reset** - Clear conversation history and switch to concierge agent
**/help** - Show this help message
**/status** - Show current agent and conversation stats
**/clear** - Clear conversation history (keep current agent)
**/agents** - List available agents

**Available Agents:**
• **Concierge** - General assistance and questions
• **Azure VM** - Create and manage Azure virtual machines
• **ServiceNow Catalog** - Create ServiceNow catalog items
• **ServiceNow Variables** - Add variables to catalog items

Just type your question or request normally to get started!
            """
            return help_text.strip()
        
        elif message_lower == "/status":
            # Show current status
            current_agent = state_manager.get_current_agent(user_id)
            conversation_count = len(conversation_manager.get_conversation_history(user_id))
            stats = state_manager.get_stats()
            
            status_text = f"""
📊 **Current Status:**

**User ID:** {user_id}
**Current Agent:** {current_agent}
**Messages in Conversation:** {conversation_count}
**Total Conversations:** {stats.get('total_conversations', 0)}
**Active Users:** {stats.get('active_users', 0)}
            """
            return status_text.strip()
        
        elif message_lower == "/clear":
            # Clear conversation history but keep current agent
            conversation_manager.clear_conversation(user_id)
            current_agent = state_manager.get_current_agent(user_id)
            logger.info({
                "event": "conversation_cleared",
                "user_id": user_id,
                "command": "/clear",
                "current_agent": current_agent
            })
            return f"🗑️ **Conversation history cleared!** I'm still your {current_agent} assistant. What would you like to do?"
        
        elif message_lower == "/agents":
            # List available agents
            agents_text = """
🤖 **Available Agents:**

**ConciergeAgent** - General assistance, questions, and help
**AzureVMAgent** - Create, manage, and monitor Azure virtual machines
**ServiceNowCatalogCreationAgent** - Create and publish ServiceNow catalog items
**ServiceNowVariablesAgent** - Add variables and fields to catalog items

**Usage:** Just ask me to help with any of these tasks, and I'll automatically switch to the right agent!
            """
            return agents_text.strip()
        
        # 1. Get the current agent for this user
        current_agent_name = state_manager.get_current_agent(user_id)
        
        # 2. Get the actual agent object
        starting_agent = AGENT_LOOKUP.get(current_agent_name, concierge_agent)
        
        logger.info({
            "event": "starting_agent_determined",
            "user_id": user_id,
            "current_agent_name": current_agent_name,
            "starting_agent": starting_agent.name
        })
        
        # 3. Get conversation history for this user
        conversation_history = conversation_manager.get_conversation_history(user_id)
        
        # 4. Add the current message to history
        conversation_manager.add_message(user_id, "user", message)
        
        # 5. Create user context
        context = UserContext(
            sender_id=user_id,
            room=room_id,
            name=user_name,
            current_agent=current_agent_name
        )
        
        # 6. Create wait notification hooks (no message callback for CLI/testing)
        hooks = WaitNotificationHooks(user_id=user_id, room_id=room_id)
        
        # 7. Run the agent with conversation history and hooks
        input_data = conversation_history + [{"role": "user", "content": message}]
        result = await Runner.run(
            starting_agent=starting_agent,
            input=input_data,
            context=context,
            hooks=hooks,
            max_turns=10
        )
        
        # 5. Store which agent finished (for next message)
        final_agent_name = result.last_agent.name
        state_manager.set_current_agent(user_id, final_agent_name)
        
        # 6. Log the result
        log_function_result(logger, "process_user_message", {
            "final_agent": final_agent_name,
            "response_length": len(str(result.final_output))
        })
        
        # 7. Update conversation history from the result
        conversation_manager.update_conversation_from_result(user_id, result)

        return str(result.final_output)
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "process_user_message",
            "user_id": user_id,
            "room_id": room_id
        })
        return f"Sorry, I encountered an error: {str(e)}"


def get_agent_stats() -> Dict[str, Any]:
    """Get statistics about agent usage."""
    return state_manager.get_stats()


def list_active_users() -> Dict[str, str]:
    """Get a list of all active users and their current agents."""
    return state_manager.list_all_users()


def clear_user_session(user_id: str) -> None:
    """Clear a user's session (reset to concierge agent and clear conversation history)."""
    state_manager.clear_user_state(user_id)
    conversation_manager.clear_conversation(user_id) 