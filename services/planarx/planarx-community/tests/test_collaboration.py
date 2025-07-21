"""
Collaboration System Tests
Tests for real-time editing, comment threads, annotations, and notifications
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from services.collab.realtime_editor
from services.collab.annotations
from services.notifications.collab_events
from services.collab.routes
from services.main


class TestRealtimeEditor:
    """Test real-time collaboration editor"""
    
    def setup_method(self):
        self.editor = RealtimeEditor()
        self.mock_websocket = Mock()
        self.mock_websocket.send = AsyncMock()
    
    def test_create_session(self):
        """Test creating a collaboration session"""
        session = CollaborationSession(
            draft_id="test-draft",
            session_id="test-session",
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            active_users={},
            edit_history=[],
            version=0,
            is_active=True,
            permissions={}
        )
        
        assert session.draft_id == "test-draft"
        assert session.session_id == "test-session"
        assert session.is_active == True
        assert session.version == 0
    
    def test_edit_operation(self):
        """Test creating edit operations"""
        edit_op = EditOperation(
            id="test-edit",
            draft_id="test-draft",
            user_id="test-user",
            edit_type=EditType.INSERT,
            timestamp=datetime.utcnow(),
            position={"x": 10, "y": 20},
            content="test content",
            metadata={"test": "data"},
            version=1
        )
        
        assert edit_op.id == "test-edit"
        assert edit_op.edit_type == EditType.INSERT
        assert edit_op.content == "test content"
        assert edit_op.version == 1
    
    def test_user_presence(self):
        """Test user presence tracking"""
        presence = UserPresence(
            user_id="test-user",
            display_name="Test User",
            status=PresenceStatus.ONLINE,
            last_seen=datetime.utcnow(),
            current_section="main",
            cursor_position={"x": 0, "y": 0},
            is_typing=False
        )
        
        assert presence.user_id == "test-user"
        assert presence.status == PresenceStatus.ONLINE
        assert presence.is_typing == False
    
    @pytest.mark.asyncio
    async def test_join_session(self):
        """Test joining a collaboration session"""
        session_id = await self.editor.join_session(
            self.mock_websocket,
            "test-user",
            "test-draft",
            "Test User"
        )
        
        assert session_id in self.editor.sessions
        session = self.editor.sessions[session_id]
        assert session.draft_id == "test-draft"
        assert "test-user" in session.active_users
    
    @pytest.mark.asyncio
    async def test_leave_session(self):
        """Test leaving a collaboration session"""
        # First join a session
        session_id = await self.editor.join_session(
            self.mock_websocket,
            "test-user",
            "test-draft",
            "Test User"
        )
        
        # Then leave it
        await self.editor.leave_session(session_id, "test-user")
        
        session = self.editor.sessions[session_id]
        assert "test-user" not in session.active_users
    
    @pytest.mark.asyncio
    async def test_handle_edit_operation(self):
        """Test handling edit operations"""
        # Join session first
        session_id = await self.editor.join_session(
            self.mock_websocket,
            "test-user",
            "test-draft",
            "Test User"
        )
        
        # Handle edit operation
        operation_data = {
            "type": "insert",
            "position": {"x": 10, "y": 20},
            "content": "test content",
            "metadata": {"test": "data"}
        }
        
        await self.editor.handle_edit_operation(session_id, "test-user", operation_data)
        
        session = self.editor.sessions[session_id]
        assert len(session.edit_history) == 1
        assert session.version == 1
    
    def test_get_session_stats(self):
        """Test getting session statistics"""
        session = CollaborationSession(
            draft_id="test-draft",
            session_id="test-session",
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            active_users={"user1": Mock(), "user2": Mock()},
            edit_history=[Mock(), Mock()],
            version=2,
            is_active=True,
            permissions={}
        )
        
        self.editor.sessions["test-session"] = session
        
        stats = self.editor.get_session_stats("test-session")
        assert stats["active_users"] == 2
        assert stats["total_edits"] == 2
        assert stats["current_version"] == 2


class TestAnnotationManager:
    """Test annotation and comment thread management"""
    
    def setup_method(self):
        self.manager = AnnotationManager()
    
    def test_create_thread(self):
        """Test creating a comment thread"""
        thread = self.manager.create_thread(
            draft_id="test-draft",
            arx_object_id="test-object",
            object_type="element",
            object_path="/main",
            title="Test Thread",
            description="Test description",
            created_by="test-user",
            priority="normal",
            tags=["test", "demo"]
        )
        
        assert thread.id in self.manager.threads
        assert thread.title == "Test Thread"
        assert thread.status == CommentStatus.ACTIVE
        assert "test-user" in thread.subscribers
    
    def test_add_comment(self):
        """Test adding a comment to a thread"""
        # Create thread first
        thread = self.manager.create_thread(
            draft_id="test-draft",
            arx_object_id="test-object",
            object_type="element",
            object_path="/main",
            title="Test Thread",
            description="Test description",
            created_by="test-user"
        )
        
        # Add comment
        comment = self.manager.add_comment(
            thread_id=thread.id,
            author_id="test-user",
            author_name="Test User",
            content="Test comment content",
            comment_type=CommentType.GENERAL
        )
        
        assert comment.id in [c.id for c in thread.comments]
        assert comment.content == "Test comment content"
        assert comment.author_id == "test-user"
    
    def test_reply_to_comment(self):
        """Test replying to a comment"""
        # Create thread and comment
        thread = self.manager.create_thread(
            draft_id="test-draft",
            arx_object_id="test-object",
            object_type="element",
            object_path="/main",
            title="Test Thread",
            description="Test description",
            created_by="test-user"
        )
        
        comment = self.manager.add_comment(
            thread_id=thread.id,
            author_id="user1",
            author_name="User 1",
            content="Original comment",
            comment_type=CommentType.GENERAL
        )
        
        # Reply to comment
        reply = self.manager.reply_to_comment(
            comment_id=comment.id,
            author_id="user2",
            author_name="User 2",
            content="Reply to comment",
            comment_type=CommentType.GENERAL
        )
        
        assert reply.parent_id == comment.id
        assert reply.content == "Reply to comment"
    
    def test_resolve_thread(self):
        """Test resolving a thread"""
        thread = self.manager.create_thread(
            draft_id="test-draft",
            arx_object_id="test-object",
            object_type="element",
            object_path="/main",
            title="Test Thread",
            description="Test description",
            created_by="test-user"
        )
        
        success = self.manager.resolve_thread(thread.id, "resolver", "Resolved")
        
        assert success == True
        assert thread.status == CommentStatus.RESOLVED
    
    def test_assign_thread(self):
        """Test assigning a thread"""
        thread = self.manager.create_thread(
            draft_id="test-draft",
            arx_object_id="test-object",
            object_type="element",
            object_path="/main",
            title="Test Thread",
            description="Test description",
            created_by="test-user"
        )
        
        success = self.manager.assign_thread(thread.id, "assignee", "assigner")
        
        assert success == True
        assert thread.assigned_to == "assignee"
    
    def test_add_reaction(self):
        """Test adding reactions to comments"""
        thread = self.manager.create_thread(
            draft_id="test-draft",
            arx_object_id="test-object",
            object_type="element",
            object_path="/main",
            title="Test Thread",
            description="Test description",
            created_by="test-user"
        )
        
        comment = self.manager.add_comment(
            thread_id=thread.id,
            author_id="test-user",
            author_name="Test User",
            content="Test comment",
            comment_type=CommentType.GENERAL
        )
        
        success = self.manager.add_reaction(comment.id, "user1", "like")
        
        assert success == True
        assert "like" in comment.reactions
        assert "user1" in comment.reactions["like"]
    
    def test_extract_mentions(self):
        """Test extracting mentions from content"""
        content = "Hello @user1 and @user2, please review this"
        mentions = self.manager._extract_mentions(content)
        
        assert len(mentions) == 2
        assert "user-user1" in mentions
        assert "user-user2" in mentions
    
    def test_get_thread_summary(self):
        """Test getting thread summary"""
        thread = self.manager.create_thread(
            draft_id="test-draft",
            arx_object_id="test-object",
            object_type="element",
            object_path="/main",
            title="Test Thread",
            description="Test description",
            created_by="test-user"
        )
        
        # Add some comments
        self.manager.add_comment(
            thread_id=thread.id,
            author_id="user1",
            author_name="User 1",
            content="Comment 1",
            comment_type=CommentType.GENERAL
        )
        
        self.manager.add_comment(
            thread_id=thread.id,
            author_id="user2",
            author_name="User 2",
            content="Comment 2",
            comment_type=CommentType.QUESTION
        )
        
        summary = self.manager.get_thread_summary(thread.id)
        
        assert summary["title"] == "Test Thread"
        assert summary["comment_count"] == 2
        assert summary["status"] == "active"
        assert len(summary["comments"]) == 2
    
    def test_add_annotation(self):
        """Test adding annotations"""
        thread = self.manager.create_thread(
            draft_id="test-draft",
            arx_object_id="test-object",
            object_type="element",
            object_path="/main",
            title="Test Thread",
            description="Test description",
            created_by="test-user"
        )
        
        annotation = self.manager.add_annotation(
            thread_id=thread.id,
            annotation_type="highlight",
            coordinates={"x": 100, "y": 200},
            content="Test annotation",
            created_by="test-user",
            style={"color": "#ff0000"}
        )
        
        assert annotation.id in [a.id for a in self.manager.annotations[thread.id]]
        assert annotation.annotation_type == "highlight"
        assert annotation.content == "Test annotation"


class TestCollaborationNotificationService:
    """Test collaboration notification service"""
    
    def setup_method(self):
        self.service = CollaborationNotificationService()
    
    def test_create_notification(self):
        """Test creating a notification"""
        notification = self.service.create_notification(
            user_id="test-user",
            notification_type=NotificationType.COMMENT_ADDED,
            title="New Comment",
            message="A new comment was added",
            priority=NotificationPriority.NORMAL
        )
        
        assert notification.id in self.service.notifications
        assert notification.user_id == "test-user"
        assert notification.notification_type == NotificationType.COMMENT_ADDED
        assert notification.status == NotificationStatus.PENDING
    
    def test_create_notification_from_template(self):
        """Test creating notification from template"""
        template_data = {
            "draft_id": "test-draft",
            "draft_title": "Test Draft",
            "author_id": "test-user",
            "author_name": "Test User"
        }
        
        notification = self.service.create_notification_from_template(
            user_id="test-user",
            notification_type=NotificationType.DRAFT_UPDATED,
            template_data=template_data
        )
        
        assert notification.title == "Draft 'Test Draft' has been updated"
        assert "Test User" in notification.message
    
    def test_notify_draft_updated(self):
        """Test notifying about draft updates"""
        subscribers = ["user1", "user2", "user3"]
        
        self.service.notify_draft_updated(
            draft_id="test-draft",
            draft_title="Test Draft",
            updater_id="updater",
            updater_name="Updater User",
            subscribers=subscribers
        )
        
        # Check that notifications were created for subscribers (except updater)
        user_notifications = self.service.get_user_notifications("user1")
        assert len(user_notifications) == 1
        assert user_notifications[0].notification_type == NotificationType.DRAFT_UPDATED
    
    def test_notify_comment_added(self):
        """Test notifying about new comments"""
        subscribers = ["user1", "user2"]
        
        self.service.notify_comment_added(
            draft_id="test-draft",
            draft_title="Test Draft",
            comment_id="test-comment",
            author_id="author",
            author_name="Author User",
            comment_preview="Test comment preview",
            subscribers=subscribers
        )
        
        user_notifications = self.service.get_user_notifications("user1")
        assert len(user_notifications) == 1
        assert user_notifications[0].notification_type == NotificationType.COMMENT_ADDED
    
    def test_notify_mention(self):
        """Test notifying mentioned users"""
        self.service.notify_mention(
            draft_id="test-draft",
            draft_title="Test Draft",
            comment_id="test-comment",
            mentioned_user_id="mentioned-user",
            author_id="author",
            author_name="Author User",
            mention_preview="Hello @mentioned-user"
        )
        
        user_notifications = self.service.get_user_notifications("mentioned-user")
        assert len(user_notifications) == 1
        assert user_notifications[0].notification_type == NotificationType.MENTION
    
    def test_mark_notification_read(self):
        """Test marking notification as read"""
        notification = self.service.create_notification(
            user_id="test-user",
            notification_type=NotificationType.COMMENT_ADDED,
            title="Test",
            message="Test message"
        )
        
        success = self.service.mark_notification_read(notification.id, "test-user")
        
        assert success == True
        assert notification.status == NotificationStatus.READ
        assert notification.read_at is not None
    
    def test_mark_all_notifications_read(self):
        """Test marking all notifications as read"""
        # Create multiple notifications
        for i in range(3):
            self.service.create_notification(
                user_id="test-user",
                notification_type=NotificationType.COMMENT_ADDED,
                title=f"Test {i}",
                message=f"Test message {i}"
            )
        
        count = self.service.mark_all_notifications_read("test-user")
        
        assert count == 3
        user_notifications = self.service.get_user_notifications("test-user")
        assert all(n.status == NotificationStatus.READ for n in user_notifications)
    
    def test_get_unread_count(self):
        """Test getting unread notification count"""
        # Create notifications
        self.service.create_notification(
            user_id="test-user",
            notification_type=NotificationType.COMMENT_ADDED,
            title="Test 1",
            message="Test message 1"
        )
        
        self.service.create_notification(
            user_id="test-user",
            notification_type=NotificationType.COMMENT_ADDED,
            title="Test 2",
            message="Test message 2"
        )
        
        # Mark one as read
        notifications = self.service.get_user_notifications("test-user")
        self.service.mark_notification_read(notifications[0].id, "test-user")
        
        unread_count = self.service.get_unread_count("test-user")
        assert unread_count == 1
    
    def test_get_notification_stats(self):
        """Test getting notification statistics"""
        # Create notifications of different types
        self.service.create_notification(
            user_id="test-user",
            notification_type=NotificationType.COMMENT_ADDED,
            title="Comment",
            message="Comment message"
        )
        
        self.service.create_notification(
            user_id="test-user",
            notification_type=NotificationType.DRAFT_UPDATED,
            title="Update",
            message="Update message"
        )
        
        stats = self.service.get_notification_stats("test-user")
        
        assert stats["total_count"] == 2
        assert stats["unread_count"] == 2
        assert "comment_added" in stats["type_counts"]
        assert "draft_updated" in stats["type_counts"]


class TestCollaborationRoutes:
    """Test collaboration API routes"""
    
    def setup_method(self):
        self.client = TestClient(app)
        # Add collaboration routes to app
        app.include_router(router)
    
    @patch('planarx_community.collab.routes.get_current_user')
    def test_create_thread(self, mock_get_user):
        """Test creating a comment thread via API"""
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_get_user.return_value = mock_user
        
        response = self.client.post("/collab/threads", json={
            "draft_id": "test-draft",
            "arx_object_id": "test-object",
            "object_type": "element",
            "object_path": "/main",
            "title": "Test Thread",
            "description": "Test description",
            "priority": "normal",
            "tags": ["test", "demo"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "thread" in data
    
    @patch('planarx_community.collab.routes.get_current_user')
    def test_add_comment(self, mock_get_user):
        """Test adding a comment via API"""
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_user.display_name = "Test User"
        mock_get_user.return_value = mock_user
        
        # Create thread first
        thread = annotation_manager.create_thread(
            draft_id="test-draft",
            arx_object_id="test-object",
            object_type="element",
            object_path="/main",
            title="Test Thread",
            description="Test description",
            created_by="test-user"
        )
        
        response = self.client.post(f"/collab/threads/{thread.id}/comments", json={
            "content": "Test comment content",
            "comment_type": "general",
            "metadata": {"test": "data"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "comment" in data
    
    @patch('planarx_community.collab.routes.get_current_user')
    def test_resolve_thread(self, mock_get_user):
        """Test resolving a thread via API"""
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_get_user.return_value = mock_user
        
        # Create thread
        thread = annotation_manager.create_thread(
            draft_id="test-draft",
            arx_object_id="test-object",
            object_type="element",
            object_path="/main",
            title="Test Thread",
            description="Test description",
            created_by="test-user"
        )
        
        response = self.client.put(f"/collab/threads/{thread.id}/resolve", json={
            "resolution_note": "Resolved successfully"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    @patch('planarx_community.collab.routes.get_current_user')
    def test_get_notifications(self, mock_get_user):
        """Test getting notifications via API"""
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_get_user.return_value = mock_user
        
        # Create a notification
        collab_notification_service.create_notification(
            user_id="test-user",
            notification_type=NotificationType.COMMENT_ADDED,
            title="Test Notification",
            message="Test message"
        )
        
        response = self.client.get("/collab/notifications")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["notifications"]) > 0
    
    @patch('planarx_community.collab.routes.get_current_user')
    def test_mark_notification_read(self, mock_get_user):
        """Test marking notification as read via API"""
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_get_user.return_value = mock_user
        
        # Create a notification
        notification = collab_notification_service.create_notification(
            user_id="test-user",
            notification_type=NotificationType.COMMENT_ADDED,
            title="Test Notification",
            message="Test message"
        )
        
        response = self.client.put(f"/collab/notifications/{notification.id}/read")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    @patch('planarx_community.collab.routes.get_current_user')
    def test_get_unread_count(self, mock_get_user):
        """Test getting unread count via API"""
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_get_user.return_value = mock_user
        
        # Create notifications
        collab_notification_service.create_notification(
            user_id="test-user",
            notification_type=NotificationType.COMMENT_ADDED,
            title="Test 1",
            message="Test message 1"
        )
        
        collab_notification_service.create_notification(
            user_id="test-user",
            notification_type=NotificationType.DRAFT_UPDATED,
            title="Test 2",
            message="Test message 2"
        )
        
        response = self.client.get("/collab/notifications/unread-count")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["unread_count"] == 2


class TestCollaborationIntegration:
    """Integration tests for collaboration features"""
    
    def setup_method(self):
        self.editor = RealtimeEditor()
        self.annotation_manager = AnnotationManager()
        self.notification_service = CollaborationNotificationService()
    
    @pytest.mark.asyncio
    async def test_full_collaboration_workflow(self):
        """Test complete collaboration workflow"""
        # 1. Create a draft and start collaboration session
        draft_id = "test-draft"
        user1_id = "user1"
        user2_id = "user2"
        
        # 2. Join session
        mock_ws1 = Mock()
        mock_ws1.send = AsyncMock()
        
        session_id = await self.editor.join_session(
            mock_ws1, user1_id, draft_id, "User 1"
        )
        
        # 3. Create comment thread
        thread = self.annotation_manager.create_thread(
            draft_id=draft_id,
            arx_object_id="test-object",
            object_type="element",
            object_path="/main",
            title="Integration Test Thread",
            description="Testing full workflow",
            created_by=user1_id
        )
        
        # 4. Add comment
        comment = self.annotation_manager.add_comment(
            thread_id=thread.id,
            author_id=user1_id,
            author_name="User 1",
            content="Initial comment",
            comment_type=CommentType.GENERAL
        )
        
        # 5. Notify about comment
        self.notification_service.notify_comment_added(
            draft_id=draft_id,
            draft_title="Test Draft",
            comment_id=comment.id,
            author_id=user1_id,
            author_name="User 1",
            comment_preview="Initial comment",
            subscribers=[user2_id]
        )
        
        # 6. User 2 joins and replies
        mock_ws2 = Mock()
        mock_ws2.send = AsyncMock()
        
        await self.editor.join_session(
            mock_ws2, user2_id, draft_id, "User 2"
        )
        
        reply = self.annotation_manager.reply_to_comment(
            comment_id=comment.id,
            author_id=user2_id,
            author_name="User 2",
            content="Reply to comment",
            comment_type=CommentType.GENERAL
        )
        
        # 7. Notify about reply
        self.notification_service.notify_comment_reply(
            draft_id=draft_id,
            draft_title="Test Draft",
            comment_id=reply.id,
            parent_author_id=user1_id,
            author_id=user2_id,
            author_name="User 2",
            reply_preview="Reply to comment"
        )
        
        # 8. Add annotation
        annotation = self.annotation_manager.add_annotation(
            thread_id=thread.id,
            annotation_type="highlight",
            coordinates={"x": 100, "y": 200},
            content="Test annotation",
            created_by=user1_id
        )
        
        # 9. Resolve thread
        self.annotation_manager.resolve_thread(thread.id, user1_id, "Resolved")
        
        # 10. Verify results
        session = self.editor.sessions[session_id]
        assert len(session.active_users) == 2
        assert user1_id in session.active_users
        assert user2_id in session.active_users
        
        thread = self.annotation_manager.get_thread(thread.id)
        assert thread.status == CommentStatus.RESOLVED
        assert len(thread.comments) == 2
        
        user1_notifications = self.notification_service.get_user_notifications(user1_id)
        assert len(user1_notifications) == 1  # Reply notification
        
        user2_notifications = self.notification_service.get_user_notifications(user2_id)
        assert len(user2_notifications) == 1  # Comment notification
        
        annotations = self.annotation_manager.get_annotations(thread.id)
        assert len(annotations) == 1
        assert annotations[0].content == "Test annotation"


if __name__ == "__main__":
    pytest.main([__file__]) 