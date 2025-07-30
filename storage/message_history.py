"""
Message history storage for Teams Agent Bot.

This module provides a storage system for managing conversation history
per user, including message storage, retrieval, and cleanup functionality.
It supports both in-memory storage and can be extended for persistent storage.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from config.settings import settings
from utils.logger import get_logger, log_function_call, log_function_result, log_error_with_context

logger = get_logger(__name__)


class MessageRole(Enum):
    """Enumeration for message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    HANDOFF = "handoff"


@dataclass
class Message:
    """
    Represents a single message in the conversation history.
    
    Attributes:
        id: Unique message identifier
        role: Role of the message sender (user/assistant/system)
        content: Message content
        timestamp: When the message was created
        metadata: Additional message metadata
    """
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }


@dataclass
class Conversation:
    """
    Represents a conversation thread for a specific user.
    
    Attributes:
        user_id: Unique user identifier
        thread_id: OpenAI thread ID
        messages: List of messages in the conversation
        created_at: When the conversation was created
        last_updated: When the conversation was last updated
        metadata: Additional conversation metadata
    """
    user_id: str
    thread_id: str
    messages: List[Message]
    created_at: datetime
    last_updated: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary."""
        return {
            "user_id": self.user_id,
            "thread_id": self.thread_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata or {}
        }


class MessageHistoryManager:
    """
    Manages message history for all users.
    
    This class provides a centralized interface for storing, retrieving,
    and managing conversation history. It includes automatic cleanup
    of old conversations and enforces message limits.
    """
    
    def __init__(self):
        """Initialize the message history manager."""
        self._conversations: Dict[str, Conversation] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task = None
        
        logger.info("Message history manager initialized")
    
    def _start_cleanup_task(self):
        """Start the cleanup task if not already running."""
        if self._cleanup_task is None:
            try:
                self._cleanup_task = asyncio.create_task(self._cleanup_old_conversations())
                logger.info("Started cleanup task")
            except RuntimeError:
                # No event loop running, will start later
                logger.debug("No event loop running, cleanup task will start later")
    
    async def get_or_create_conversation(self, user_id: str, thread_id: str) -> Conversation:
        """
        Get existing conversation or create a new one.
        
        Args:
            user_id: User identifier
            thread_id: OpenAI thread ID
            
        Returns:
            Conversation object
        """
        log_function_call(logger, "get_or_create_conversation", user_id=user_id, thread_id=thread_id)
        
        # Start cleanup task if not already running
        self._start_cleanup_task()
        
        async with self._lock:
            if user_id in self._conversations:
                conversation = self._conversations[user_id]
                # Update thread_id if it changed
                if conversation.thread_id != thread_id:
                    conversation.thread_id = thread_id
                    conversation.last_updated = datetime.utcnow()
                    logger.info("Updated thread_id for existing conversation", 
                              user_id=user_id, old_thread_id=conversation.thread_id, new_thread_id=thread_id)
                log_function_result(logger, "get_or_create_conversation", "existing", user_id=user_id)
                return conversation
            
            # Create new conversation
            conversation = Conversation(
                user_id=user_id,
                thread_id=thread_id,
                messages=[],
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                metadata={}
            )
            self._conversations[user_id] = conversation
            
            log_function_result(logger, "get_or_create_conversation", "new", user_id=user_id)
            return conversation
    
    async def add_message(self, user_id: str, role: MessageRole, content: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> Message:
        """
        Add a message to a user's conversation.
        
        Args:
            user_id: User identifier
            role: Message role
            content: Message content
            metadata: Optional message metadata
            
        Returns:
            Created message object
            
        Raises:
            ValueError: If user conversation doesn't exist
        """
        log_function_call(logger, "add_message", user_id=user_id, role=role.value, content_length=len(content))
        
        async with self._lock:
            if user_id not in self._conversations:
                raise ValueError(f"No conversation found for user {user_id}")
            
            conversation = self._conversations[user_id]
            
            # Create message
            message = Message(
                id=f"{user_id}_{len(conversation.messages)}_{datetime.utcnow().timestamp()}",
                role=role,
                content=content,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Add to conversation
            conversation.messages.append(message)
            conversation.last_updated = datetime.utcnow()
            
            # Enforce message limit
            if len(conversation.messages) > settings.agent.max_history_messages:
                # Remove oldest messages (keep the limit)
                excess = len(conversation.messages) - settings.agent.max_history_messages
                conversation.messages = conversation.messages[excess:]
                logger.info(f"Removed {excess} old messages to maintain limit", 
                          user_id=user_id, limit=settings.agent.max_history_messages)
            
            log_function_result(logger, "add_message", message.id, 
                              message_id=message.id, user_id=user_id, message_count=len(conversation.messages))
            return message
    
    async def get_conversation(self, user_id: str) -> Optional[Conversation]:
        """
        Get a user's conversation.
        
        Args:
            user_id: User identifier
            
        Returns:
            Conversation object or None if not found
        """
        log_function_call(logger, "get_conversation", user_id=user_id)
        
        async with self._lock:
            conversation = self._conversations.get(user_id)
            if conversation:
                log_function_result(logger, "get_conversation", "found", 
                                  user_id=user_id, message_count=len(conversation.messages))
            else:
                log_function_result(logger, "get_conversation", "not_found", user_id=user_id)
            return conversation
    
    async def get_messages(self, user_id: str, limit: Optional[int] = None) -> List[Message]:
        """
        Get messages from a user's conversation.
        
        Args:
            user_id: User identifier
            limit: Maximum number of messages to return (None for all)
            
        Returns:
            List of messages
        """
        log_function_call(logger, "get_messages", user_id=user_id, limit=limit)
        
        async with self._lock:
            conversation = self._conversations.get(user_id)
            if not conversation:
                log_function_result(logger, "get_messages", [], user_id=user_id)
                return []
            
            messages = conversation.messages
            if limit:
                messages = messages[-limit:]
            
            log_function_result(logger, "get_messages", len(messages), 
                              user_id=user_id, returned_count=len(messages))
            return messages
    
    async def get_conversation_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of a user's conversation.
        
        Args:
            user_id: User identifier
            
        Returns:
            Conversation summary dictionary or None if not found
        """
        log_function_call(logger, "get_conversation_summary", user_id=user_id)
        
        async with self._lock:
            conversation = self._conversations.get(user_id)
            if not conversation:
                log_function_result(logger, "get_conversation_summary", None, user_id=user_id)
                return None
            
            summary = {
                "user_id": conversation.user_id,
                "thread_id": conversation.thread_id,
                "message_count": len(conversation.messages),
                "created_at": conversation.created_at.isoformat(),
                "last_updated": conversation.last_updated.isoformat(),
                "metadata": conversation.metadata
            }
            
            log_function_result(logger, "get_conversation_summary", summary, user_id=user_id)
            return summary
    
    async def clear_conversation(self, user_id: str) -> bool:
        """
        Clear a user's conversation history.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if conversation was cleared, False if not found
        """
        log_function_call(logger, "clear_conversation", user_id=user_id)
        
        async with self._lock:
            if user_id in self._conversations:
                del self._conversations[user_id]
                log_function_result(logger, "clear_conversation", True, user_id=user_id)
                return True
            else:
                log_function_result(logger, "clear_conversation", False, user_id=user_id)
                return False
    
    async def _cleanup_old_conversations(self):
        """Clean up conversations older than the retention period."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff_date = datetime.utcnow() - timedelta(days=settings.agent.history_retention_days)
                removed_count = 0
                
                async with self._lock:
                    user_ids_to_remove = []
                    
                    for user_id, conversation in self._conversations.items():
                        if conversation.last_updated < cutoff_date:
                            user_ids_to_remove.append(user_id)
                    
                    for user_id in user_ids_to_remove:
                        del self._conversations[user_id]
                        removed_count += 1
                
                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} old conversations", 
                              removed_count=removed_count, cutoff_date=cutoff_date.isoformat())
                
            except Exception as e:
                log_error_with_context(logger, e, {"operation": "cleanup_old_conversations"})
    
    async def get_all_conversations(self) -> Dict[str, Conversation]:
        """
        Get all conversations (for debugging/admin purposes).
        
        Returns:
            Dictionary of all conversations
        """
        log_function_call(logger, "get_all_conversations")
        
        async with self._lock:
            conversations = self._conversations.copy()
            log_function_result(logger, "get_all_conversations", len(conversations), 
                              conversation_count=len(conversations))
            return conversations
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        log_function_call(logger, "get_stats")
        
        async with self._lock:
            total_conversations = len(self._conversations)
            total_messages = sum(len(conv.messages) for conv in self._conversations.values())
            
            # Count messages by role
            role_counts = {"user": 0, "assistant": 0, "system": 0, "handoff": 0}
            for conv in self._conversations.values():
                for msg in conv.messages:
                    role = msg.role.value
                    if role in role_counts:
                        role_counts[role] += 1
            
            stats = {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "messages_by_role": role_counts,
                "max_history_messages": settings.agent.max_history_messages,
                "history_retention_days": settings.agent.history_retention_days,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            log_function_result(logger, "get_stats", stats)
            return stats

    async def get_handoff_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get handoff history for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of handoff events
        """
        log_function_call(logger, "get_handoff_history", user_id=user_id)
        
        async with self._lock:
            conversation = self._conversations.get(user_id)
            if not conversation:
                log_function_result(logger, "get_handoff_history", [], user_id=user_id)
                return []
            
            handoffs = []
            for msg in conversation.messages:
                if msg.role == MessageRole.HANDOFF:
                    handoffs.append({
                        "timestamp": msg.timestamp.isoformat(),
                        "content": msg.content,
                        "metadata": msg.metadata
                    })
            
            log_function_result(logger, "get_handoff_history", len(handoffs), 
                              user_id=user_id, handoff_count=len(handoffs))
            return handoffs


# Global message history manager instance
message_history = MessageHistoryManager() 