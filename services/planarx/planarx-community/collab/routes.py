"""
Collaboration API Routes
FastAPI routes for real-time collaboration, comments, and notifications
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging

from .realtime_editor import realtime_editor
from .annotations import annotation_manager
from ..notifications.collab_events import collab_notification_service
from ..auth.auth_utils import get_current_user
from ..models.draft import Draft
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collab", tags=["collaboration"])


# WebSocket connection handler
@router.websocket("/ws/{draft_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    draft_id: str,
    token: str
):
    """WebSocket endpoint for real-time collaboration"""
    
    try:
        await websocket.accept()
        
        # Validate token and get user
        try:
            user = get_current_user(token)
        except Exception as e:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Join collaboration session
        session_id = await realtime_editor.join_session(
            websocket, user.id, draft_id, user.display_name
        )
        
        # Add to notification service
        collab_notification_service.add_websocket_connection(user.id, websocket)
        
        try:
            async for message in websocket:
                data = json.loads(message)
                await realtime_editor.handle_client(websocket, data)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user.id}")
        finally:
            # Clean up
            if session_id:
                await realtime_editor.leave_session(session_id, user.id)
            collab_notification_service.remove_websocket_connection(user.id, websocket)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=4000, reason="Internal error")


# Comment Thread Routes
@router.post("/threads")
async def create_thread(
    draft_id: str,
    arx_object_id: str,
    object_type: str,
    object_path: str,
    title: str,
    description: str,
    priority: str = "normal",
    tags: List[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Create a new comment thread"""
    
    try:
        thread = annotation_manager.create_thread(
            draft_id=draft_id,
            arx_object_id=arx_object_id,
            object_type=object_type,
            object_path=object_path,
            title=title,
            description=description,
            created_by=current_user.id,
            priority=priority,
            tags=tags or []
        )
        
        # Notify draft subscribers
        # This would typically get subscribers from draft model
        subscribers = [current_user.id]  # Placeholder
        
        collab_notification_service.notify_comment_added(
            draft_id=draft_id,
            draft_title="Draft",  # Would get from draft model
            comment_id=thread.id,
            author_id=current_user.id,
            author_name=current_user.display_name,
            comment_preview=description,
            subscribers=subscribers
        )
        
        return {
            "success": True,
            "thread": annotation_manager.get_thread_summary(thread.id)
        }
        
    except Exception as e:
        logger.error(f"Error creating thread: {e}")
        raise HTTPException(status_code=500, detail="Failed to create thread")


@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a comment thread"""
    
    thread = annotation_manager.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    return {
        "success": True,
        "thread": annotation_manager.get_thread_summary(thread_id)
    }


@router.post("/threads/{thread_id}/comments")
async def add_comment(
    thread_id: str,
    content: str,
    comment_type: str = "general",
    parent_id: Optional[str] = None,
    metadata: Dict = None,
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a thread"""
    
    try:
        from ..notifications.collab_events import NotificationType
        
        comment = annotation_manager.add_comment(
            thread_id=thread_id,
            author_id=current_user.id,
            author_name=current_user.display_name,
            content=content,
            comment_type=NotificationType(comment_type),
            parent_id=parent_id,
            metadata=metadata or {}
        )
        
        # Get thread for notification
        thread = annotation_manager.get_thread(thread_id)
        if thread:
            # Notify thread subscribers
            collab_notification_service.notify_comment_added(
                draft_id=thread.draft_id,
                draft_title="Draft",  # Would get from draft model
                comment_id=comment.id,
                author_id=current_user.id,
                author_name=current_user.display_name,
                comment_preview=content,
                subscribers=thread.subscribers
            )
            
            # Notify mentioned users
            for mentioned_user_id in comment.mentions:
                collab_notification_service.notify_mention(
                    draft_id=thread.draft_id,
                    draft_title="Draft",
                    comment_id=comment.id,
                    mentioned_user_id=mentioned_user_id,
                    author_id=current_user.id,
                    author_name=current_user.display_name,
                    mention_preview=content
                )
        
        return {
            "success": True,
            "comment": {
                "id": comment.id,
                "author_id": comment.author_id,
                "author_name": comment.author_name,
                "content": comment.content,
                "comment_type": comment.comment_type.value,
                "created_at": comment.created_at.isoformat(),
                "mentions": comment.mentions
            }
        }
        
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to add comment")


@router.put("/threads/{thread_id}/resolve")
async def resolve_thread(
    thread_id: str,
    resolution_note: str = "",
    current_user: User = Depends(get_current_user)
):
    """Resolve a comment thread"""
    
    success = annotation_manager.resolve_thread(
        thread_id, current_user.id, resolution_note
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Get thread for notification
    thread = annotation_manager.get_thread(thread_id)
    if thread:
        collab_notification_service.notify_thread_resolved(
            thread_id=thread_id,
            thread_title=thread.title,
            resolver_id=current_user.id,
            resolver_name=current_user.display_name,
            subscribers=thread.subscribers
        )
    
    return {"success": True, "message": "Thread resolved"}


@router.post("/threads/{thread_id}/assign")
async def assign_thread(
    thread_id: str,
    assigned_to: str,
    current_user: User = Depends(get_current_user)
):
    """Assign a thread to a user"""
    
    success = annotation_manager.assign_thread(
        thread_id, assigned_to, current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    collab_notification_service.notify_thread_assigned(
        thread_id=thread_id,
        thread_title="Thread",  # Would get from thread
        assignee_id=assigned_to,
        assigner_id=current_user.id,
        assigner_name=current_user.display_name
    )
    
    return {"success": True, "message": "Thread assigned"}


@router.post("/threads/{thread_id}/subscribe")
async def subscribe_to_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user)
):
    """Subscribe to a thread"""
    
    success = annotation_manager.subscribe_to_thread(thread_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    return {"success": True, "message": "Subscribed to thread"}


@router.delete("/threads/{thread_id}/subscribe")
async def unsubscribe_from_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unsubscribe from a thread"""
    
    success = annotation_manager.unsubscribe_from_thread(thread_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    return {"success": True, "message": "Unsubscribed from thread"}


@router.get("/drafts/{draft_id}/threads")
async def get_draft_threads(
    draft_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all threads for a draft"""
    
    threads = annotation_manager.get_threads_by_draft(draft_id)
    
    return {
        "success": True,
        "threads": [
            annotation_manager.get_thread_summary(thread.id)
            for thread in threads
        ]
    }


@router.get("/objects/{object_id}/threads")
async def get_object_threads(
    object_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all threads for an ArxObject"""
    
    threads = annotation_manager.get_threads_by_object(object_id)
    
    return {
        "success": True,
        "threads": [
            annotation_manager.get_thread_summary(thread.id)
            for thread in threads
        ]
    }


@router.get("/user/threads")
async def get_user_threads(
    current_user: User = Depends(get_current_user)
):
    """Get threads for current user"""
    
    threads = annotation_manager.get_user_threads(current_user.id)
    
    return {
        "success": True,
        "threads": [
            annotation_manager.get_thread_summary(thread.id)
            for thread in threads
        ]
    }


# Annotation Routes
@router.post("/threads/{thread_id}/annotations")
async def add_annotation(
    thread_id: str,
    annotation_type: str,
    coordinates: Dict,
    content: str,
    style: Dict = None,
    current_user: User = Depends(get_current_user)
):
    """Add a visual annotation to a thread"""
    
    try:
        annotation = annotation_manager.add_annotation(
            thread_id=thread_id,
            annotation_type=annotation_type,
            coordinates=coordinates,
            content=content,
            created_by=current_user.id,
            style=style or {}
        )
        
        return {
            "success": True,
            "annotation": {
                "id": annotation.id,
                "annotation_type": annotation.annotation_type,
                "coordinates": annotation.coordinates,
                "style": annotation.style,
                "content": annotation.content,
                "created_at": annotation.created_at.isoformat(),
                "created_by": annotation.created_by
            }
        }
        
    except Exception as e:
        logger.error(f"Error adding annotation: {e}")
        raise HTTPException(status_code=500, detail="Failed to add annotation")


@router.get("/threads/{thread_id}/annotations")
async def get_thread_annotations(
    thread_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all annotations for a thread"""
    
    annotations = annotation_manager.get_annotations(thread_id)
    
    return {
        "success": True,
        "annotations": [
            {
                "id": annotation.id,
                "annotation_type": annotation.annotation_type,
                "coordinates": annotation.coordinates,
                "style": annotation.style,
                "content": annotation.content,
                "created_at": annotation.created_at.isoformat(),
                "created_by": annotation.created_by
            }
            for annotation in annotations
        ]
    }


# Notification Routes
@router.get("/notifications")
async def get_notifications(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Get notifications for current user"""
    
    from ..notifications.collab_events import NotificationStatus
    
    status_enum = None
    if status:
        status_enum = NotificationStatus(status)
    
    notifications = collab_notification_service.get_user_notifications(
        current_user.id, status_enum, limit, offset
    )
    
    return {
        "success": True,
        "notifications": [
            {
                "id": notification.id,
                "type": notification.notification_type.value,
                "priority": notification.priority.value,
                "status": notification.status.value,
                "title": notification.title,
                "message": notification.message,
                "created_at": notification.created_at.isoformat(),
                "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
                "read_at": notification.read_at.isoformat() if notification.read_at else None,
                "actions": notification.actions
            }
            for notification in notifications
        ]
    }


@router.get("/notifications/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user)
):
    """Get unread notification count"""
    
    count = collab_notification_service.get_unread_count(current_user.id)
    
    return {
        "success": True,
        "unread_count": count
    }


@router.get("/notifications/stats")
async def get_notification_stats(
    current_user: User = Depends(get_current_user)
):
    """Get notification statistics"""
    
    stats = collab_notification_service.get_notification_stats(current_user.id)
    
    return {
        "success": True,
        "stats": stats
    }


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    
    success = collab_notification_service.mark_notification_read(
        notification_id, current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True, "message": "Notification marked as read"}


@router.put("/notifications/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read"""
    
    count = collab_notification_service.mark_all_notifications_read(current_user.id)
    
    return {
        "success": True,
        "message": f"Marked {count} notifications as read"
    }


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""
    
    success = collab_notification_service.delete_notification(
        notification_id, current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True, "message": "Notification deleted"}


# Collaboration Session Routes
@router.get("/sessions/{draft_id}/stats")
async def get_session_stats(
    draft_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get collaboration session statistics"""
    
    # Find session for draft
    session_id = realtime_editor.draft_sessions.get(draft_id)
    if not session_id:
        return {
            "success": True,
            "stats": {
                "active_users": 0,
                "total_edits": 0,
                "current_version": 0,
                "is_active": False
            }
        }
    
    stats = realtime_editor.get_session_stats(session_id)
    
    return {
        "success": True,
        "stats": stats
    }


@router.get("/sessions/user")
async def get_user_sessions(
    current_user: User = Depends(get_current_user)
):
    """Get sessions user is participating in"""
    
    session_ids = realtime_editor.get_user_sessions(current_user.id)
    sessions = []
    
    for session_id in session_ids:
        stats = realtime_editor.get_session_stats(session_id)
        sessions.append(stats)
    
    return {
        "success": True,
        "sessions": sessions
    }


# Search Routes
@router.get("/search/threads")
async def search_threads(
    query: str,
    draft_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Search comment threads"""
    
    threads = annotation_manager.search_threads(query, draft_id)
    
    return {
        "success": True,
        "threads": [
            annotation_manager.get_thread_summary(thread.id)
            for thread in threads
        ]
    }


# Reaction Routes
@router.post("/comments/{comment_id}/reactions")
async def add_reaction(
    comment_id: str,
    reaction_type: str,
    current_user: User = Depends(get_current_user)
):
    """Add a reaction to a comment"""
    
    success = annotation_manager.add_reaction(
        comment_id, current_user.id, reaction_type
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    return {"success": True, "message": "Reaction added"}


@router.delete("/comments/{comment_id}/reactions/{reaction_type}")
async def remove_reaction(
    comment_id: str,
    reaction_type: str,
    current_user: User = Depends(get_current_user)
):
    """Remove a reaction from a comment"""
    
    success = annotation_manager.remove_reaction(
        comment_id, current_user.id, reaction_type
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    return {"success": True, "message": "Reaction removed"} 