"""
Simple In-Memory Agent State Manager for Teams Agent Bot.

This module manages which agent is currently active for each user.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class UserAgentState:
    """State for a single user's agent session."""
    
    user_id: str
    """The user ID."""
    
    current_agent: str
    """The currently active agent name."""
    
    last_activity: datetime
    """Last activity timestamp."""
    
    conversation_count: int
    """Number of messages in this session."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "user_id": self.user_id,
            "current_agent": self.current_agent,
            "last_activity": self.last_activity.isoformat(),
            "conversation_count": self.conversation_count
        }


class AgentStateManager:
    """Simple in-memory manager for tracking which agent is active per user."""
    
    def __init__(self, cleanup_interval_hours: int = 24):
        """
        Initialize the agent state manager.
        
        Args:
            cleanup_interval_hours: How often to clean up old sessions (hours)
        """
        self._user_states: Dict[str, UserAgentState] = {}
        self._cleanup_interval_hours = cleanup_interval_hours
        self._default_agent = "ConciergeAgent"
    
    def get_current_agent(self, user_id: str) -> str:
        """
        Get the currently active agent for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            The current agent name (defaults to ConciergeAgent if not found)
        """
        if user_id in self._user_states:
            state = self._user_states[user_id]
            # Update last activity
            state.last_activity = datetime.now()
            state.conversation_count += 1
            
            logger.info({
                "event": "agent_state_retrieved",
                "user_id": user_id,
                "current_agent": state.current_agent,
                "conversation_count": state.conversation_count
            })
            
            return state.current_agent
        
        # Return default agent if no state exists
        logger.info({
            "event": "agent_state_not_found",
            "user_id": user_id,
            "default_agent": self._default_agent
        })
        
        return self._default_agent
    
    def set_current_agent(self, user_id: str, agent_name: str) -> None:
        """
        Set the currently active agent for a user.
        
        Args:
            user_id: The user ID
            agent_name: The agent name
        """
        if user_id in self._user_states:
            # Update existing state
            state = self._user_states[user_id]
            state.current_agent = agent_name
            state.last_activity = datetime.now()
        else:
            # Create new state
            state = UserAgentState(
                user_id=user_id,
                current_agent=agent_name,
                last_activity=datetime.now(),
                conversation_count=1
            )
            self._user_states[user_id] = state
        
        logger.info({
            "event": "agent_state_updated",
            "user_id": user_id,
            "agent_name": agent_name,
            "conversation_count": state.conversation_count
        })
    
    def clear_user_state(self, user_id: str) -> None:
        """
        Clear a user's state (reset to default agent).
        
        Args:
            user_id: The user ID
        """
        if user_id in self._user_states:
            del self._user_states[user_id]
            
            logger.info({
                "event": "user_state_cleared",
                "user_id": user_id
            })
    
    def cleanup_old_sessions(self, max_age_hours: Optional[int] = None) -> int:
        """
        Clean up sessions older than max_age_hours.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup (uses cleanup_interval_hours if None)
            
        Returns:
            Number of sessions cleaned up
        """
        if max_age_hours is None:
            max_age_hours = self._cleanup_interval_hours
            
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        keys_to_remove = []
        
        for user_id, state in self._user_states.items():
            if state.last_activity < cutoff_time:
                keys_to_remove.append(user_id)
        
        for user_id in keys_to_remove:
            del self._user_states[user_id]
        
        if keys_to_remove:
            logger.info({
                "event": "old_sessions_cleaned_up",
                "count": len(keys_to_remove),
                "max_age_hours": max_age_hours
            })
        
        return len(keys_to_remove)
    
    def get_user_state(self, user_id: str) -> Optional[UserAgentState]:
        """
        Get the full state for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            The user state or None if not found
        """
        return self._user_states.get(user_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the state manager."""
        agent_counts = {}
        for state in self._user_states.values():
            agent_counts[state.current_agent] = agent_counts.get(state.current_agent, 0) + 1
        
        return {
            "total_users": len(self._user_states),
            "agent_distribution": agent_counts,
            "oldest_session": min((state.last_activity for state in self._user_states.values()), default=None),
            "newest_session": max((state.last_activity for state in self._user_states.values()), default=None)
        }
    
    def list_all_users(self) -> Dict[str, str]:
        """
        Get a list of all users and their current agents.
        
        Returns:
            Dictionary mapping user_id to agent_name
        """
        return {
            user_id: state.current_agent 
            for user_id, state in self._user_states.items()
        }


# Global state manager instance
agent_state_manager = AgentStateManager()


def get_agent_state_manager() -> AgentStateManager:
    """Get the global agent state manager instance."""
    return agent_state_manager 