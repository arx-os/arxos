"""
Conversation Repository Implementation

This module provides persistence for conversation entities using
PostgreSQL with proper clean architecture separation.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import structlog

from domain.entities.conversation import (
    Conversation, ConversationContext, Message, MessageRole, ConversationStatus
)

logger = structlog.get_logger()


class ConversationRepository:
    """
    Repository for persisting and retrieving conversations.
    
    This implementation uses PostgreSQL for storage while keeping
    the domain layer independent of persistence details.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize repository with database connection pool.
        
        Args:
            db_pool: AsyncPG connection pool
        """
        self.db_pool = db_pool
        logger.info("Initialized ConversationRepository")
    
    async def create_tables(self):
        """Create necessary database tables if they don't exist"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS gus_conversations (
                    id UUID PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    context JSONB NOT NULL DEFAULT '{}',
                    metadata JSONB NOT NULL DEFAULT '{}',
                    token_count INTEGER DEFAULT 0,
                    query_count INTEGER DEFAULT 0,
                    action_count INTEGER DEFAULT 0,
                    INDEX idx_user_id (user_id),
                    INDEX idx_session_id (session_id),
                    INDEX idx_status (status),
                    INDEX idx_updated_at (updated_at)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS gus_messages (
                    id UUID PRIMARY KEY,
                    conversation_id UUID NOT NULL REFERENCES gus_conversations(id) ON DELETE CASCADE,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{}',
                    function_call JSONB,
                    function_response JSONB,
                    INDEX idx_conversation_id (conversation_id),
                    INDEX idx_timestamp (timestamp)
                )
            """)
            
            logger.info("Database tables created/verified")
    
    async def save(self, conversation: Conversation) -> None:
        """
        Save or update a conversation.
        
        Args:
            conversation: Conversation entity to save
        """
        async with self.db_pool.acquire() as conn:
            # Serialize context
            context_json = json.dumps(conversation.context.to_dict())
            metadata_json = json.dumps(conversation.metadata)
            
            # Upsert conversation
            await conn.execute("""
                INSERT INTO gus_conversations 
                (id, user_id, session_id, status, created_at, updated_at, 
                 context, metadata, token_count, query_count, action_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at,
                    context = EXCLUDED.context,
                    metadata = EXCLUDED.metadata,
                    token_count = EXCLUDED.token_count,
                    query_count = EXCLUDED.query_count,
                    action_count = EXCLUDED.action_count
            """, 
                conversation.id,
                conversation.user_id,
                conversation.session_id,
                conversation.status.value,
                conversation.created_at,
                conversation.updated_at,
                context_json,
                metadata_json,
                conversation._token_count,
                conversation._query_count,
                conversation._action_count
            )
            
            # Save new messages (we'll track which ones are already saved)
            # In production, you'd want to track this more efficiently
            existing_message_ids = await conn.fetch("""
                SELECT id FROM gus_messages WHERE conversation_id = $1
            """, conversation.id)
            
            existing_ids = {row['id'] for row in existing_message_ids}
            
            for message in conversation.messages:
                if message.id not in existing_ids:
                    await conn.execute("""
                        INSERT INTO gus_messages
                        (id, conversation_id, role, content, timestamp, 
                         metadata, function_call, function_response)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                        message.id,
                        conversation.id,
                        message.role.value,
                        message.content,
                        message.timestamp,
                        json.dumps(message.metadata),
                        json.dumps(message.function_call) if message.function_call else None,
                        json.dumps(message.function_response) if message.function_response else None
                    )
            
            logger.debug(f"Saved conversation {conversation.id}")
    
    async def get(self, conversation_id: str) -> Optional[Conversation]:
        """
        Retrieve a conversation by ID.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation entity or None if not found
        """
        async with self.db_pool.acquire() as conn:
            # Get conversation
            row = await conn.fetchrow("""
                SELECT * FROM gus_conversations WHERE id = $1
            """, conversation_id)
            
            if not row:
                return None
            
            # Get messages
            message_rows = await conn.fetch("""
                SELECT * FROM gus_messages 
                WHERE conversation_id = $1 
                ORDER BY timestamp ASC
            """, conversation_id)
            
            # Reconstruct conversation
            conversation = self._row_to_conversation(row, message_rows)
            
            logger.debug(f"Retrieved conversation {conversation_id}")
            return conversation
    
    async def get_by_session(self, session_id: str) -> Optional[Conversation]:
        """
        Retrieve active conversation by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Active conversation or None
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM gus_conversations 
                WHERE session_id = $1 AND status = $2
                ORDER BY updated_at DESC
                LIMIT 1
            """, session_id, ConversationStatus.ACTIVE.value)
            
            if not row:
                return None
            
            # Get messages
            message_rows = await conn.fetch("""
                SELECT * FROM gus_messages 
                WHERE conversation_id = $1 
                ORDER BY timestamp ASC
            """, row['id'])
            
            return self._row_to_conversation(row, message_rows)
    
    async def list_user_conversations(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
        status: Optional[ConversationStatus] = None
    ) -> List[Conversation]:
        """
        List conversations for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of conversations
            offset: Offset for pagination
            status: Optional status filter
            
        Returns:
            List of conversations
        """
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT * FROM gus_conversations 
                WHERE user_id = $1
            """
            params = [user_id]
            
            if status:
                query += " AND status = $2"
                params.append(status.value)
            
            query += " ORDER BY updated_at DESC LIMIT $%d OFFSET $%d" % (
                len(params) + 1, len(params) + 2
            )
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            
            conversations = []
            for row in rows:
                # For list view, we might not need all messages
                message_rows = await conn.fetch("""
                    SELECT * FROM gus_messages 
                    WHERE conversation_id = $1 
                    ORDER BY timestamp DESC
                    LIMIT 5
                """, row['id'])
                
                conversations.append(self._row_to_conversation(row, message_rows))
            
            return conversations
    
    async def delete_old_conversations(self, days: int = 30) -> int:
        """
        Delete conversations older than specified days.
        
        Args:
            days: Number of days to keep conversations
            
        Returns:
            Number of conversations deleted
        """
        async with self.db_pool.acquire() as conn:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await conn.execute("""
                DELETE FROM gus_conversations 
                WHERE updated_at < $1 AND status != $2
            """, cutoff_date, ConversationStatus.ACTIVE.value)
            
            deleted_count = int(result.split()[-1])
            logger.info(f"Deleted {deleted_count} old conversations")
            return deleted_count
    
    async def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get conversation statistics.
        
        Args:
            user_id: Optional user ID for user-specific stats
            
        Returns:
            Statistics dictionary
        """
        async with self.db_pool.acquire() as conn:
            if user_id:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_conversations,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_conversations,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_conversations,
                        SUM(query_count) as total_queries,
                        SUM(action_count) as total_actions,
                        SUM(token_count) as total_tokens,
                        AVG(query_count) as avg_queries_per_conversation,
                        MAX(updated_at) as last_activity
                    FROM gus_conversations
                    WHERE user_id = $1
                """, user_id)
            else:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_conversations,
                        COUNT(DISTINCT user_id) as unique_users,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_conversations,
                        SUM(query_count) as total_queries,
                        SUM(action_count) as total_actions,
                        SUM(token_count) as total_tokens,
                        AVG(query_count) as avg_queries_per_conversation,
                        MAX(updated_at) as last_activity
                    FROM gus_conversations
                """)
            
            return dict(stats)
    
    def _row_to_conversation(self, row: asyncpg.Record, message_rows: List[asyncpg.Record]) -> Conversation:
        """Convert database rows to Conversation entity"""
        # Reconstruct context
        context_data = json.loads(row['context']) if row['context'] else {}
        context = ConversationContext(**context_data)
        
        # Reconstruct messages
        messages = []
        for msg_row in message_rows:
            message = Message(
                id=str(msg_row['id']),
                role=MessageRole(msg_row['role']),
                content=msg_row['content'],
                timestamp=msg_row['timestamp'],
                metadata=json.loads(msg_row['metadata']) if msg_row['metadata'] else {},
                function_call=json.loads(msg_row['function_call']) if msg_row['function_call'] else None,
                function_response=json.loads(msg_row['function_response']) if msg_row['function_response'] else None
            )
            messages.append(message)
        
        # Create conversation
        conversation = Conversation(
            id=str(row['id']),
            user_id=row['user_id'],
            session_id=row['session_id'],
            messages=messages,
            context=context,
            status=ConversationStatus(row['status']),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
        
        # Restore counters
        conversation._token_count = row['token_count'] or 0
        conversation._query_count = row['query_count'] or 0
        conversation._action_count = row['action_count'] or 0
        
        return conversation