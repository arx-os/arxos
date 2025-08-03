import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  ListItemSecondaryAction,
  Avatar,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Badge,
  Tooltip,
  Divider,
  Alert,
  LinearProgress,
  Fab,
  Menu,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import {
  Group as GroupIcon,
  Person as PersonIcon,
  Chat as ChatIcon,
  Comment as CommentIcon,
  History as HistoryIcon,
  Share as ShareIcon,
  Settings as SettingsIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Reply as ReplyIcon,
  MoreVert as MoreVertIcon,
  Add as AddIcon,
  Close as CloseIcon,
  Send as SendIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { io, Socket } from 'socket.io-client';
import * as Y from 'yjs';
import { WebsocketProvider } from 'y-websocket';

interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  status: 'online' | 'away' | 'offline';
  role: 'owner' | 'editor' | 'viewer';
  lastSeen: Date;
  currentActivity?: string;
}

interface Comment {
  id: string;
  author: User;
  content: string;
  timestamp: Date;
  replies: Comment[];
  resolved: boolean;
  objectId?: string;
  position?: [number, number, number];
}

interface CollaborationSession {
  id: string;
  name: string;
  description: string;
  createdAt: Date;
  updatedAt: Date;
  owner: User;
  participants: User[];
  status: 'active' | 'paused' | 'archived';
  permissions: {
    canEdit: boolean;
    canComment: boolean;
    canShare: boolean;
    canExport: boolean;
  };
}

interface CollaborationSystemProps {
  sessionId: string;
  currentUser: User;
  onUserJoin?: (user: User) => void;
  onUserLeave?: (userId: string) => void;
  onCommentAdd?: (comment: Comment) => void;
  onCommentResolve?: (commentId: string) => void;
  onPermissionChange?: (userId: string, permissions: any) => void;
  onSessionEnd?: () => void;
}

// User Presence Component
const UserPresence: React.FC<{
  users: User[];
  currentUser: User;
  onUserClick?: (user: User) => void;
}> = ({ users, currentUser, onUserClick }) => {
  const getStatusColor = (status: User['status']) => {
    switch (status) {
      case 'online': return 'success';
      case 'away': return 'warning';
      case 'offline': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: User['status']) => {
    switch (status) {
      case 'online': return <CheckCircleIcon />;
      case 'away': return <WarningIcon />;
      case 'offline': return <ErrorIcon />;
      default: return <InfoIcon />;
    }
  };

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Active Users ({users.filter(u => u.status === 'online').length})
      </Typography>
      <List>
        {users.map((user) => (
          <ListItem key={user.id} button onClick={() => onUserClick?.(user)}>
            <ListItemAvatar>
              <Badge
                overlap="circular"
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                badgeContent={
                  <Avatar sx={{ width: 12, height: 12 }}>
                    {getStatusIcon(user.status)}
                  </Avatar>
                }
              >
                <Avatar src={user.avatar}>
                  {user.name.charAt(0).toUpperCase()}
                </Avatar>
              </Badge>
            </ListItemAvatar>
            <ListItemText
              primary={user.name}
              secondary={
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    {user.currentActivity || 'Idle'}
                  </Typography>
                  <Chip
                    label={user.role}
                    size="small"
                    color={user.role === 'owner' ? 'primary' : 'default'}
                    sx={{ mt: 0.5 }}
                  />
                </Box>
              }
            />
            <ListItemSecondaryAction>
              {user.id === currentUser.id && (
                <Chip label="You" size="small" color="primary" />
              )}
            </ListItemSecondaryAction>
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

// Comments Component
const CommentsPanel: React.FC<{
  comments: Comment[];
  currentUser: User;
  onAddComment: (content: string, objectId?: string) => void;
  onResolveComment: (commentId: string) => void;
  onReplyComment: (commentId: string, content: string) => void;
}> = ({ comments, currentUser, onAddComment, onResolveComment, onReplyComment }) => {
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState('');

  const handleAddComment = () => {
    if (newComment.trim()) {
      onAddComment(newComment.trim());
      setNewComment('');
    }
  };

  const handleReply = (commentId: string) => {
    if (replyContent.trim()) {
      onReplyComment(commentId, replyContent.trim());
      setReplyContent('');
      setReplyingTo(null);
    }
  };

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Comments ({comments.length})
      </Typography>

      {/* Add new comment */}
      <Box sx={{ mb: 2 }}>
        <TextField
          fullWidth
          multiline
          rows={2}
          placeholder="Add a comment..."
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          sx={{ mb: 1 }}
        />
        <Button
          variant="contained"
          startIcon={<SendIcon />}
          onClick={handleAddComment}
          disabled={!newComment.trim()}
        >
          Add Comment
        </Button>
      </Box>

      {/* Comments list */}
      <List>
        {comments.map((comment) => (
          <Box key={comment.id} sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
              <Avatar src={comment.author.avatar} sx={{ width: 32, height: 32 }}>
                {comment.author.name.charAt(0).toUpperCase()}
              </Avatar>
              <Box sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Typography variant="subtitle2">
                    {comment.author.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {comment.timestamp.toLocaleString()}
                  </Typography>
                  {comment.resolved && (
                    <Chip label="Resolved" size="small" color="success" />
                  )}
                </Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  {comment.content}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    size="small"
                    startIcon={<ReplyIcon />}
                    onClick={() => setReplyingTo(comment.id)}
                  >
                    Reply
                  </Button>
                  {!comment.resolved && (
                    <Button
                      size="small"
                      color="success"
                      onClick={() => onResolveComment(comment.id)}
                    >
                      Resolve
                    </Button>
                  )}
                </Box>

                {/* Reply form */}
                {replyingTo === comment.id && (
                  <Box sx={{ mt: 1, ml: 2 }}>
                    <TextField
                      fullWidth
                      size="small"
                      placeholder="Write a reply..."
                      value={replyContent}
                      onChange={(e) => setReplyContent(e.target.value)}
                      sx={{ mb: 1 }}
                    />
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button
                        size="small"
                        variant="contained"
                        onClick={() => handleReply(comment.id)}
                        disabled={!replyContent.trim()}
                      >
                        Reply
                      </Button>
                      <Button
                        size="small"
                        onClick={() => {
                          setReplyingTo(null);
                          setReplyContent('');
                        }}
                      >
                        Cancel
                      </Button>
                    </Box>
                  </Box>
                )}

                {/* Replies */}
                {comment.replies.length > 0 && (
                  <Box sx={{ ml: 2, mt: 1 }}>
                    {comment.replies.map((reply) => (
                      <Box key={reply.id} sx={{ mb: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <Avatar src={reply.author.avatar} sx={{ width: 24, height: 24 }}>
                            {reply.author.name.charAt(0).toUpperCase()}
                          </Avatar>
                          <Typography variant="subtitle2" sx={{ fontSize: '0.8rem' }}>
                            {reply.author.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {reply.timestamp.toLocaleString()}
                          </Typography>
                        </Box>
                        <Typography variant="body2" sx={{ ml: 3 }}>
                          {reply.content}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                )}
              </Box>
            </Box>
            <Divider sx={{ mt: 1 }} />
          </Box>
        ))}
      </List>
    </Box>
  );
};

// Version History Component
const VersionHistory: React.FC<{
  versions: Array<{
    id: string;
    version: string;
    author: User;
    timestamp: Date;
    description: string;
    changes: string[];
  }>;
  onRestoreVersion?: (versionId: string) => void;
}> = ({ versions, onRestoreVersion }) => {
  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Version History
      </Typography>
      <List>
        {versions.map((version) => (
          <ListItem key={version.id}>
            <ListItemAvatar>
              <Avatar src={version.author.avatar}>
                {version.author.name.charAt(0).toUpperCase()}
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={`Version ${version.version}`}
              secondary={
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    {version.description}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    by {version.author.name} on {version.timestamp.toLocaleString()}
                  </Typography>
                  {version.changes.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      {version.changes.map((change, index) => (
                        <Chip
                          key={index}
                          label={change}
                          size="small"
                          variant="outlined"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                    </Box>
                  )}
                </Box>
              }
            />
            <ListItemSecondaryAction>
              <Button
                size="small"
                onClick={() => onRestoreVersion?.(version.id)}
              >
                Restore
              </Button>
            </ListItemSecondaryAction>
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

// Main Collaboration System Component
export const CollaborationSystem: React.FC<CollaborationSystemProps> = ({
  sessionId,
  currentUser,
  onUserJoin,
  onUserLeave,
  onCommentAdd,
  onCommentResolve,
  onPermissionChange,
  onSessionEnd,
}) => {
  const [users, setUsers] = useState<User[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [session, setSession] = useState<CollaborationSession | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [activeTab, setActiveTab] = useState<'users' | 'comments' | 'history' | 'settings'>('users');
  const [showSettings, setShowSettings] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);

  // WebSocket and Y.js setup
  const socketRef = useRef<Socket | null>(null);
  const ydocRef = useRef<Y.Doc | null>(null);
  const providerRef = useRef<WebsocketProvider | null>(null);

  // Initialize collaboration
  useEffect(() => {
    const initializeCollaboration = async () => {
      try {
        // Initialize Y.js document
        const ydoc = new Y.Doc();
        ydocRef.current = ydoc;

        // Connect to WebSocket provider
        const provider = new WebsocketProvider(
          'ws://localhost:1234', // Replace with your WebSocket server
          sessionId,
          ydoc
        );
        providerRef.current = provider;

        // Initialize Socket.IO for real-time features
        const socket = io('http://localhost:3001'); // Replace with your Socket.IO server
        socketRef.current = socket;

        // Socket event handlers
        socket.on('connect', () => {
          setIsConnected(true);
          socket.emit('join-session', { sessionId, user: currentUser });
        });

        socket.on('user-joined', (user: User) => {
          setUsers(prev => [...prev, user]);
          onUserJoin?.(user);
        });

        socket.on('user-left', (userId: string) => {
          setUsers(prev => prev.filter(u => u.id !== userId));
          onUserLeave?.(userId);
        });

        socket.on('comment-added', (comment: Comment) => {
          setComments(prev => [...prev, comment]);
          onCommentAdd?.(comment);
        });

        socket.on('comment-resolved', (commentId: string) => {
          setComments(prev => 
            prev.map(c => 
              c.id === commentId ? { ...c, resolved: true } : c
            )
          );
          onCommentResolve?.(commentId);
        });

        // Cleanup on unmount
        return () => {
          socket.disconnect();
          provider.destroy();
          ydoc.destroy();
        };
      } catch (error) {
        console.error('Failed to initialize collaboration:', error);
      }
    };

    initializeCollaboration();
  }, [sessionId, currentUser]);

  // Handle comment addition
  const handleAddComment = useCallback((content: string, objectId?: string) => {
    const comment: Comment = {
      id: `comment_${Date.now()}`,
      author: currentUser,
      content,
      timestamp: new Date(),
      replies: [],
      resolved: false,
      objectId,
    };

    socketRef.current?.emit('add-comment', { sessionId, comment });
  }, [sessionId, currentUser]);

  // Handle comment resolution
  const handleResolveComment = useCallback((commentId: string) => {
    socketRef.current?.emit('resolve-comment', { sessionId, commentId });
  }, [sessionId]);

  // Handle comment reply
  const handleReplyComment = useCallback((commentId: string, content: string) => {
    const reply: Comment = {
      id: `reply_${Date.now()}`,
      author: currentUser,
      content,
      timestamp: new Date(),
      replies: [],
      resolved: false,
    };

    socketRef.current?.emit('reply-comment', { sessionId, commentId, reply });
  }, [sessionId, currentUser]);

  // Handle user click
  const handleUserClick = useCallback((user: User) => {
    // Show user details or start private chat
    console.log('User clicked:', user);
  }, []);

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h6">
            Collaboration
            <Chip
              label={isConnected ? 'Connected' : 'Disconnected'}
              color={isConnected ? 'success' : 'error'}
              size="small"
              sx={{ ml: 1 }}
            />
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Share Session">
              <IconButton
                size="small"
                onClick={() => setShowShareDialog(true)}
              >
                <ShareIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Settings">
              <IconButton
                size="small"
                onClick={() => setShowSettings(true)}
              >
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Connection Status */}
        {!isConnected && (
          <Alert severity="warning" sx={{ mb: 1 }}>
            Connecting to collaboration server...
          </Alert>
        )}

        {/* Tab Navigation */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant={activeTab === 'users' ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setActiveTab('users')}
            startIcon={<GroupIcon />}
          >
            Users ({users.length})
          </Button>
          <Button
            variant={activeTab === 'comments' ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setActiveTab('comments')}
            startIcon={<ChatIcon />}
          >
            Comments ({comments.length})
          </Button>
          <Button
            variant={activeTab === 'history' ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setActiveTab('history')}
            startIcon={<HistoryIcon />}
          >
            History
          </Button>
        </Box>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {activeTab === 'users' && (
          <UserPresence
            users={users}
            currentUser={currentUser}
            onUserClick={handleUserClick}
          />
        )}

        {activeTab === 'comments' && (
          <CommentsPanel
            comments={comments}
            currentUser={currentUser}
            onAddComment={handleAddComment}
            onResolveComment={handleResolveComment}
            onReplyComment={handleReplyComment}
          />
        )}

        {activeTab === 'history' && (
          <VersionHistory
            versions={[
              {
                id: 'v1',
                version: '1.0.0',
                author: currentUser,
                timestamp: new Date(),
                description: 'Initial version',
                changes: ['Created project', 'Added basic geometry'],
              },
            ]}
            onRestoreVersion={(versionId) => {
              console.log('Restore version:', versionId);
            }}
          />
        )}

        {activeTab === 'settings' && (
          <Box>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Collaboration Settings
            </Typography>
            <Alert severity="info">
              Settings panel will be implemented here.
            </Alert>
          </Box>
        )}
      </Box>

      {/* Share Dialog */}
      <Dialog open={showShareDialog} onClose={() => setShowShareDialog(false)}>
        <DialogTitle>Share Session</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Share this session with others by sending them the session link.
          </Typography>
          <TextField
            fullWidth
            label="Session Link"
            value={`https://arxide.com/collaborate/${sessionId}`}
            InputProps={{
              readOnly: true,
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowShareDialog(false)}>Close</Button>
          <Button variant="contained">Copy Link</Button>
        </DialogActions>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onClose={() => setShowSettings(false)} maxWidth="md" fullWidth>
        <DialogTitle>Collaboration Settings</DialogTitle>
        <DialogContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Permissions
          </Typography>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Default Role</InputLabel>
            <Select value="viewer" label="Default Role">
              <MenuItem value="viewer">Viewer</MenuItem>
              <MenuItem value="editor">Editor</MenuItem>
              <MenuItem value="owner">Owner</MenuItem>
            </Select>
          </FormControl>

          <Typography variant="h6" sx={{ mb: 2 }}>
            Notifications
          </Typography>
          <Alert severity="info">
            Notification settings will be implemented here.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSettings(false)}>Cancel</Button>
          <Button variant="contained">Save Settings</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}; 