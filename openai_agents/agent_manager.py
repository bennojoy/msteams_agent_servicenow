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

from agents import Agent, Runner, trace, RunContextWrapper, TResponseInputItem
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
    handoffs=[]  # Will be set after all agents are created
)
azure_vm_agent = Agent[UserContext](
    name="AzureVMAgent",
    instructions=azure_vm_agent_instructions,
    tools=get_azure_vm_tools(),
    handoffs=[]  # Will be set after all agents are created
)
servicenow_variables_agent = Agent[UserContext](
    name="ServiceNowVariablesAgent",
    instructions=servicenow_variables_agent_instructions,
    tools=get_servicenow_variables_tools(),
    handoffs=[]  # Will be set after all agents are created
)
servicenow_catalog_creation_agent = Agent[UserContext](
    name="ServiceNowCatalogCreationAgent",
    instructions=servicenow_catalog_creation_agent_instructions,
    tools=get_servicenow_catalog_tools(),
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
        
        # 6. Run the agent with conversation history
        input_data = conversation_history + [{"role": "user", "content": message}]
        result = await Runner.run(
            starting_agent=starting_agent,
            input=input_data,
            context=context,
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