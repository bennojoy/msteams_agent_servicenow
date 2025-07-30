"""
State Manager for Teams Agent Bot.

This module manages persistent agent state across conversations.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from utils.logger import get_logger

logger = get_logger(__name__)


class AgentType(Enum):
    """Enum for different agent types."""
    CONCIERGE = "concierge"
    AZURE_VM = "azure_vm"
    SERVICENOW_CATALOG = "servicenow_catalog"
    SERVICENOW_CATALOG_CREATION = "servicenow_catalog_creation"
    SERVICENOW_VARIABLES = "servicenow_variables"


@dataclass
class ConversationState:
    """State for a single conversation."""
    
    user_id: str
    """The user ID."""
    
    room_id: str
    """The room/channel ID."""
    
    current_agent: str
    """The currently active agent name."""
    
    conversation_history: List[Dict[str, Any]]
    """The conversation history."""
    
    last_activity: datetime
    """Last activity timestamp."""
    
    metadata: Dict[str, Any]
    """Additional metadata."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "user_id": self.user_id,
            "room_id": self.room_id,
            "current_agent": self.current_agent,
            "conversation_history": self.conversation_history,
            "last_activity": self.last_activity.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationState":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            room_id=data["room_id"],
            current_agent=data["current_agent"],
            conversation_history=data["conversation_history"],
            last_activity=datetime.fromisoformat(data["last_activity"]),
            metadata=data.get("metadata", {})
        )


class StateManager:
    """Manages persistent agent state across conversations."""
    
    def __init__(self, cleanup_interval: int = 3600):
        """
        Initialize the state manager.
        
        Args:
            cleanup_interval: How often to clean up old conversations (seconds)
        """
        self._conversations: Dict[str, ConversationState] = {}
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Start cleanup task
        self._start_cleanup_task()
    
    def _get_conversation_key(self, user_id: str, room_id: str) -> str:
        """Get the key for a conversation."""
        return f"{user_id}:{room_id}"
    
    def get_current_agent(self, user_id: str, room_id: str) -> Optional[str]:
        """
        Get the currently active agent for a user/room.
        
        Args:
            user_id: The user ID
            room_id: The room ID
            
        Returns:
            The current agent name or None if not found
        """
        key = self._get_conversation_key(user_id, room_id)
        if key in self._conversations:
            state = self._conversations[key]
            # Update last activity
            state.last_activity = datetime.now()
            return state.current_agent
        return None
    
    def set_current_agent(self, user_id: str, room_id: str, agent_name: str) -> None:
        """
        Set the currently active agent for a user/room.
        
        Args:
            user_id: The user ID
            room_id: The room ID
            agent_name: The agent name
        """
        key = self._get_conversation_key(user_id, room_id)
        
        if key in self._conversations:
            # Update existing conversation
            state = self._conversations[key]
            state.current_agent = agent_name
            state.last_activity = datetime.now()
        else:
            # Create new conversation
            state = ConversationState(
                user_id=user_id,
                room_id=room_id,
                current_agent=agent_name,
                conversation_history=[],
                last_activity=datetime.now(),
                metadata={}
            )
            self._conversations[key] = state
        
        logger.info({
            "event": "agent_state_updated",
            "user_id": user_id,
            "room_id": room_id,
            "agent_name": agent_name
        })
    
    def add_conversation_history(self, user_id: str, room_id: str, message: Dict[str, Any]) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            user_id: The user ID
            room_id: The room ID
            message: The message to add
        """
        key = self._get_conversation_key(user_id, room_id)
        
        if key in self._conversations:
            state = self._conversations[key]
            state.conversation_history.append(message)
            state.last_activity = datetime.now()
            
            # Keep only last 50 messages to prevent memory bloat
            if len(state.conversation_history) > 50:
                state.conversation_history = state.conversation_history[-50:]
    
    def get_conversation_state(self, user_id: str, room_id: str) -> Optional[ConversationState]:
        """
        Get the full conversation state.
        
        Args:
            user_id: The user ID
            room_id: The room ID
            
        Returns:
            The conversation state or None if not found
        """
        key = self._get_conversation_key(user_id, room_id)
        return self._conversations.get(key)
    
    def clear_conversation(self, user_id: str, room_id: str) -> None:
        """
        Clear a conversation (reset to concierge agent).
        
        Args:
            user_id: The user ID
            room_id: The room ID
        """
        key = self._get_conversation_key(user_id, room_id)
        
        if key in self._conversations:
            state = self._conversations[key]
            state.current_agent = "ConciergeAgent"
            state.conversation_history = []
            state.last_activity = datetime.now()
            
            logger.info({
                "event": "conversation_cleared",
                "user_id": user_id,
                "room_id": room_id
            })
    
    def _start_cleanup_task(self) -> None:
        """Start the cleanup task."""
        async def cleanup_old_conversations():
            while True:
                try:
                    await asyncio.sleep(self._cleanup_interval)
                    self._cleanup_old_conversations()
                except Exception as e:
                    logger.error({
                        "event": "cleanup_task_error",
                        "error": str(e)
                    })
        
        self._cleanup_task = asyncio.create_task(cleanup_old_conversations())
    
    def _cleanup_old_conversations(self, max_age_hours: int = 24) -> None:
        """
        Clean up conversations older than max_age_hours.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        keys_to_remove = []
        
        for key, state in self._conversations.items():
            if state.last_activity < cutoff_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._conversations[key]
        
        if keys_to_remove:
            logger.info({
                "event": "conversations_cleaned_up",
                "count": len(keys_to_remove)
            })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the state manager."""
        return {
            "total_conversations": len(self._conversations),
            "agents_in_use": list(set(state.current_agent for state in self._conversations.values()))
        }


# Global state manager instance
state_manager = StateManager()


def get_state_manager() -> StateManager:
    """Get the global state manager instance."""
    return state_manager 