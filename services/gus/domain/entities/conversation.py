"""
Conversation Domain Entity

This module defines the Conversation entity for managing AI agent conversations,
following Domain-Driven Design principles.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid


class MessageRole(Enum):
    """Enum for message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"


class ConversationStatus(Enum):
    """Enum for conversation status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ERROR = "error"


@dataclass
class Message:
    """Value object representing a single message in conversation"""
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    function_call: Optional[Dict[str, Any]] = None
    function_response: Optional[Any] = None
    
    @classmethod
    def create(cls, role: MessageRole, content: str, **kwargs) -> 'Message':
        """Factory method to create a new message"""
        return cls(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=kwargs.get('metadata', {}),
            function_call=kwargs.get('function_call'),
            function_response=kwargs.get('function_response')
        )


@dataclass
class ConversationContext:
    """Value object for conversation context"""
    building_id: Optional[str] = None
    floor_id: Optional[str] = None
    room_id: Optional[str] = None
    system_type: Optional[str] = None  # electrical, hvac, plumbing, etc.
    user_role: Optional[str] = None  # engineer, manager, technician
    preferences: Dict[str, Any] = field(default_factory=dict)
    active_filters: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        return {
            'building_id': self.building_id,
            'floor_id': self.floor_id,
            'room_id': self.room_id,
            'system_type': self.system_type,
            'user_role': self.user_role,
            'preferences': self.preferences,
            'active_filters': self.active_filters
        }


@dataclass
class Conversation:
    """
    Conversation aggregate root entity.
    
    This entity manages the state and behavior of AI agent conversations,
    including message history, context, and metadata.
    """
    id: str
    user_id: str
    session_id: str
    messages: List[Message]
    context: ConversationContext
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Computed properties
    _token_count: int = 0
    _query_count: int = 0
    _action_count: int = 0
    
    @classmethod
    def create(cls, user_id: str, session_id: Optional[str] = None) -> 'Conversation':
        """Factory method to create a new conversation"""
        now = datetime.utcnow()
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id or str(uuid.uuid4()),
            messages=[],
            context=ConversationContext(),
            status=ConversationStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            metadata={}
        )
    
    def add_message(self, role: MessageRole, content: str, **kwargs) -> Message:
        """Add a message to the conversation"""
        message = Message.create(role, content, **kwargs)
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        
        # Update counters
        if role == MessageRole.USER:
            self._query_count += 1
        elif kwargs.get('function_call'):
            self._action_count += 1
            
        return message
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get the most recent messages"""
        return self.messages[-limit:] if self.messages else []
    
    def get_messages_for_llm(self, max_tokens: int = 4000) -> List[Dict[str, str]]:
        """
        Get messages formatted for LLM consumption with token limit.
        
        Returns messages in reverse chronological order until token limit.
        """
        formatted_messages = []
        estimated_tokens = 0
        
        # Always include system message if exists
        system_messages = [m for m in self.messages if m.role == MessageRole.SYSTEM]
        if system_messages:
            formatted_messages.append({
                'role': system_messages[-1].role.value,
                'content': system_messages[-1].content
            })
            estimated_tokens += len(system_messages[-1].content.split()) * 1.3
        
        # Add recent messages until token limit
        for message in reversed(self.messages):
            if message.role == MessageRole.SYSTEM:
                continue
                
            msg_dict = {
                'role': message.role.value,
                'content': message.content
            }
            
            if message.function_call:
                msg_dict['function_call'] = message.function_call
            
            # Rough token estimation (1.3 tokens per word average)
            message_tokens = len(message.content.split()) * 1.3
            if estimated_tokens + message_tokens > max_tokens:
                break
                
            formatted_messages.insert(1 if system_messages else 0, msg_dict)
            estimated_tokens += message_tokens
        
        return formatted_messages
    
    def update_context(self, **kwargs) -> None:
        """Update conversation context"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
        self.updated_at = datetime.utcnow()
    
    def complete(self) -> None:
        """Mark conversation as completed"""
        self.status = ConversationStatus.COMPLETED
        self.updated_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Archive the conversation"""
        self.status = ConversationStatus.ARCHIVED
        self.updated_at = datetime.utcnow()
    
    def mark_error(self, error_message: str) -> None:
        """Mark conversation as having an error"""
        self.status = ConversationStatus.ERROR
        self.metadata['error'] = error_message
        self.updated_at = datetime.utcnow()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get conversation summary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'status': self.status.value,
            'message_count': len(self.messages),
            'query_count': self._query_count,
            'action_count': self._action_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'context': self.context.to_dict()
        }
    
    def __repr__(self) -> str:
        return f"<Conversation {self.id} - {self.status.value} - {len(self.messages)} messages>"