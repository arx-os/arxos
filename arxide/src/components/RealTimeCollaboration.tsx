import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Box, Typography, Paper, Grid, Avatar, Chip, Button,
         List, ListItem, ListItemAvatar, ListItemText, ListItemSecondaryAction,
         Dialog, DialogTitle, DialogContent, DialogActions, TextField,
         IconButton, Tooltip, Badge, Divider, Alert, CircularProgress } from '@mui/material';
import {
  Group, Person, Edit, Visibility, VisibilityOff, Sync,
  History, Share, Lock, LockOpen, Chat, VideoCall,
  ScreenShare, Mic, MicOff, Videocam, VideocamOff,
  MoreVert, Settings, Refresh, Close
} from '@mui/icons-material';

interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  status: 'online' | 'away' | 'busy' | 'offline';
  role: 'owner' | 'editor' | 'viewer' | 'commenter';
  lastSeen: Date;
  currentActivity: string;
  permissions: string[];
  isTyping: boolean;
  cursorPosition?: { x: number; y: number };
  selectedObjects?: string[];
}

interface Comment {
  id: string;
  userId: string;
  userName: string;
  content: string;
  timestamp: Date;
  position?: { x: number; y: number };
  objectId?: string;
  status: 'active' | 'resolved' | 'archived';
  replies: Comment[];
}

interface Version {
  id: string;
  version: string;
  timestamp: Date;
  author: User;
  description: string;
  changes: any[];
  fileSize: number;
}

interface Conflict {
  id: string;
  type: 'object' | 'property' | 'constraint' | 'comment';
  objectId?: string;
  propertyName?: string;
  user1: User;
  user2: User;
  value1: any;
  value2: any;
  timestamp: Date;
  status: 'pending' | 'resolved' | 'auto-resolved';
  resolution?: 'user1' | 'user2' | 'merged' | 'manual';
}

interface RealTimeCollaborationProps {
  sessionId: string;
  currentUser: User;
  onUserJoin: (user: User) => void;
  onUserLeave: (userId: string) => void;
  onCommentAdd: (comment: Comment) => void;
  onCommentResolve: (commentId: string) => void;
  onPermissionChange: (userId: string, permissions: string[]) => void;
  onSessionEnd: () => void;
  onConflictResolve: (conflictId: string, resolution: string) => void;
  onVersionCreate: (version: Version) => void;
  onVersionRestore: (versionId: string) => void;
}

export const RealTimeCollaboration: React.FC<RealTimeCollaborationProps> = ({
  sessionId,
  currentUser,
  onUserJoin,
  onUserLeave,
  onCommentAdd,
  onCommentResolve,
  onPermissionChange,
  onSessionEnd,
  onConflictResolve,
  onVersionCreate,
  onVersionRestore
}) => {
  const [users, setUsers] = useState<User[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [versions, setVersions] = useState<Version[]>([]);
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('connecting');
  const [showUserList, setShowUserList] = useState(true);
  const [showComments, setShowComments] = useState(false);
  const [showVersions, setShowVersions] = useState(false);
  const [showConflicts, setShowConflicts] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    initializeWebSocket();
    return () => {
      cleanupWebSocket();
    };
  }, [sessionId]);

  const initializeWebSocket = () => {
    try {
      const ws = new WebSocket(`wss://api.arxos.com/collaboration/${sessionId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        sendUserJoin();
        startHeartbeat();
      };

      ws.onmessage = (event) => {
        handleWebSocketMessage(JSON.parse(event.data));
      };

      ws.onclose = () => {
        console.log('❌ WebSocket disconnected');
        setIsConnected(false);
        setConnectionStatus('disconnected');
        stopHeartbeat();
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };

    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      setConnectionStatus('error');
    }
  };

  const cleanupWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
    }
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
  };

  const startHeartbeat = () => {
    heartbeatRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'heartbeat', userId: currentUser.id }));
      }
    }, 30000); // 30 second heartbeat
  };

  const stopHeartbeat = () => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
    }
  };

  const sendUserJoin = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'user_join',
        user: currentUser
      }));
    }
  };

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'user_joined':
        setUsers(prev => [...prev, message.user]);
        onUserJoin(message.user);
        break;

      case 'user_left':
        setUsers(prev => prev.filter(u => u.id !== message.userId));
        onUserLeave(message.userId);
        break;

      case 'user_activity':
        setUsers(prev => prev.map(u =>
          u.id === message.userId
            ? { ...u, currentActivity: message.activity, lastSeen: new Date() }
            : u
        ));
        break;

      case 'user_typing':
        setTypingUsers(prev =>
          message.isTyping
            ? [...prev.filter(id => id !== message.userId), message.userId]
            : prev.filter(id => id !== message.userId)
        );
        break;

      case 'comment_added':
        setComments(prev => [...prev, message.comment]);
        onCommentAdd(message.comment);
        break;

      case 'comment_resolved':
        setComments(prev => prev.map(c =>
          c.id === message.commentId
            ? { ...c, status: 'resolved' as const }
            : c
        ));
        onCommentResolve(message.commentId);
        break;

      case 'version_created':
        setVersions(prev => [message.version, ...prev]);
        onVersionCreate(message.version);
        break;

      case 'conflict_detected':
        setConflicts(prev => [...prev, message.conflict]);
        break;

      case 'conflict_resolved':
        setConflicts(prev => prev.map(c =>
          c.id === message.conflictId
            ? { ...c, status: 'resolved' as const, resolution: message.resolution }
            : c
        ));
        onConflictResolve(message.conflictId, message.resolution);
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  };

  const sendTypingStatus = (isTyping: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'user_typing',
        userId: currentUser.id,
        isTyping
      }));
    }
  };

  const handleCommentSubmit = () => {
    if (!newComment.trim()) return;

    const comment: Comment = {
      id: `comment_${Date.now()}`,
      userId: currentUser.id,
      userName: currentUser.name,
      content: newComment,
      timestamp: new Date(),
      status: 'active',
      replies: []
    };

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'comment_add',
        comment
      }));
    }

    setNewComment('');
    setIsTyping(false);
    sendTypingStatus(false);
  };

  const handleCommentChange = (value: string) => {
    setNewComment(value);

    if (!isTyping) {
      setIsTyping(true);
      sendTypingStatus(true);
    }

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
      sendTypingStatus(false);
    }, 2000);
  };

  const resolveConflict = (conflictId: string, resolution: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'resolve_conflict',
        conflictId,
        resolution
      }));
    }
  };

  const createVersion = () => {
    const version: Version = {
      id: `version_${Date.now()}`,
      version: `v${versions.length + 1}.0`,
      timestamp: new Date(),
      author: currentUser,
      description: `Version ${versions.length + 1} created by ${currentUser.name}`,
      changes: [],
      fileSize: 1024 * 1024 // 1MB placeholder
    };

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'create_version',
        version
      }));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'success';
      case 'away': return 'warning';
      case 'busy': return 'error';
      case 'offline': return 'default';
      default: return 'default';
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner': return <Lock />;
      case 'editor': return <Edit />;
      case 'viewer': return <Visibility />;
      case 'commenter': return <Chat />;
      default: return <Person />;
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Group color="primary" />
              Real-Time Collaboration
            </Typography>
            <Chip
              label={connectionStatus}
              color={connectionStatus === 'connected' ? 'success' : 'error'}
              size="small"
            />
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Users">
              <IconButton onClick={() => setShowUserList(!showUserList)}>
                <Badge badgeContent={users.length} color="primary">
                  <Group />
                </Badge>
              </IconButton>
            </Tooltip>
            <Tooltip title="Comments">
              <IconButton onClick={() => setShowComments(!showComments)}>
                <Badge badgeContent={comments.filter(c => c.status === 'active').length} color="primary">
                  <Chat />
                </Badge>
              </IconButton>
            </Tooltip>
            <Tooltip title="Versions">
              <IconButton onClick={() => setShowVersions(!showVersions)}>
                <History />
              </IconButton>
            </Tooltip>
            <Tooltip title="Conflicts">
              <IconButton onClick={() => setShowConflicts(!showConflicts)}>
                <Badge badgeContent={conflicts.filter(c => c.status === 'pending').length} color="error">
                  <Sync />
                </Badge>
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Paper>

      {/* Content */}
      <Box sx={{ flex: 1, display: 'flex', gap: 2, overflow: 'hidden' }}>
        {/* Main Collaboration Area */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* User Activity Feed */}
          <Paper sx={{ p: 2, mb: 2, flex: 1 }}>
            <Typography variant="h6" gutterBottom>
              Live Activity
            </Typography>

            <Box sx={{ mb: 2 }}>
              {typingUsers.length > 0 && (
                <Alert severity="info" sx={{ mb: 1 }}>
                  {typingUsers.map(id => users.find(u => u.id === id)?.name).join(', ')} is typing...
                </Alert>
              )}
            </Box>

            <List sx={{ maxHeight: 300, overflow: 'auto' }}>
              {users.map(user => (
                <ListItem key={user.id}>
                  <ListItemAvatar>
                    <Avatar src={user.avatar}>
                      {user.name.charAt(0)}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={user.name}
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={user.status}
                          color={getStatusColor(user.status) as any}
                          size="small"
                        />
                        <Typography variant="body2" color="text.secondary">
                          {user.currentActivity}
                        </Typography>
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Tooltip title={user.role}>
                      <IconButton size="small">
                        {getRoleIcon(user.role)}
                      </IconButton>
                    </Tooltip>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Paper>

          {/* Comments Section */}
          {showComments && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Comments
              </Typography>

              <Box sx={{ mb: 2 }}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  placeholder="Add a comment..."
                  value={newComment}
                  onChange={(e) => handleCommentChange(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleCommentSubmit()}
                />
                <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    variant="contained"
                    onClick={handleCommentSubmit}
                    disabled={!newComment.trim()}
                  >
                    Add Comment
                  </Button>
                </Box>
              </Box>

              <List sx={{ maxHeight: 200, overflow: 'auto' }}>
                {comments.map(comment => (
                  <ListItem key={comment.id}>
                    <ListItemAvatar>
                      <Avatar src={comment.userName.charAt(0)}>
                        {comment.userName.charAt(0)}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={comment.userName}
                      secondary={
                        <Box>
                          <Typography variant="body2">
                            {comment.content}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {comment.timestamp.toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                    {comment.status === 'active' && (
                      <ListItemSecondaryAction>
                        <Button
                          size="small"
                          onClick={() => onCommentResolve(comment.id)}
                        >
                          Resolve
                        </Button>
                      </ListItemSecondaryAction>
                    )}
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}
        </Box>

        {/* Sidebar */}
        <Box sx={{ width: 300, display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Versions */}
          {showVersions && (
            <Paper sx={{ p: 2, flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">
                  Versions
                </Typography>
                <Button size="small" onClick={createVersion}>
                  Create Version
                </Button>
              </Box>

              <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                {versions.map(version => (
                  <ListItem key={version.id}>
                    <ListItemText
                      primary={version.version}
                      secondary={
                        <Box>
                          <Typography variant="body2">
                            {version.description}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {version.timestamp.toLocaleString()} by {version.author.name}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Button
                        size="small"
                        onClick={() => onVersionRestore(version.id)}
                      >
                        Restore
                      </Button>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}

          {/* Conflicts */}
          {showConflicts && (
            <Paper sx={{ p: 2, flex: 1 }}>
              <Typography variant="h6" gutterBottom>
                Conflicts
              </Typography>

              <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                {conflicts.map(conflict => (
                  <ListItem key={conflict.id}>
                    <ListItemText
                      primary={`${conflict.type} conflict`}
                      secondary={
                        <Box>
                          <Typography variant="body2">
                            {conflict.user1.name} vs {conflict.user2.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {conflict.timestamp.toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                    {conflict.status === 'pending' && (
                      <ListItemSecondaryAction>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button
                            size="small"
                            onClick={() => resolveConflict(conflict.id, 'user1')}
                          >
                            {conflict.user1.name}
                          </Button>
                          <Button
                            size="small"
                            onClick={() => resolveConflict(conflict.id, 'user2')}
                          >
                            {conflict.user2.name}
                          </Button>
                        </Box>
                      </ListItemSecondaryAction>
                    )}
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}
        </Box>
      </Box>
    </Box>
  );
};
