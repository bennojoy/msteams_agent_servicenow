"""
Pydantic models for agent interactions.
"""

from typing import Optional
from pydantic import BaseModel


class UserContext(BaseModel):
    """Context for user interactions with agents."""
    
    sender_id: str
    """The ID of the user sending the message."""
    
    name: Optional[str] = None
    """The name of the user."""
    
    room: str
    """The room/channel where the message was sent."""
    
    current_agent: Optional[str] = None
    """The name of the currently active agent (for state persistence)."""
    
    conversation_state: Optional[dict] = None
    """Additional conversation state data.""" 