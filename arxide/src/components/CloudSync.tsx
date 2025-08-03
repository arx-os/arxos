import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  LinearProgress,
  Card,
  CardContent,
  CardActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Badge,
  CircularProgress,
} from '@mui/material';
import {
  Cloud as CloudIcon,
  CloudUpload as CloudUploadIcon,
  CloudDownload as CloudDownloadIcon,
  CloudSync as CloudSyncIcon,
  CloudOff as CloudOffIcon,
  CloudDone as CloudDoneIcon,
  Sync as SyncIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Delete as DeleteIcon,
  Restore as RestoreIcon,
  Share as ShareIcon,
  Lock as LockIcon,
  Public as PublicIcon,
  Folder as FolderIcon,
  Star as StarIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';

interface CloudFile {
  id: string;
  name: string;
  path: string;
  size: number;
  lastModified: Date;
  version: string;
  status: 'synced' | 'pending' | 'conflict' | 'error';
  metadata: {
    description?: string;
    tags?: string[];
    isPublic?: boolean;
    sharedWith?: string[];
    thumbnail?: string;
  };
}

interface SyncStatus {
  isConnected: boolean;
  isSyncing: boolean;
  lastSync: Date | null;
  syncProgress: number;
  pendingChanges: number;
  conflicts: number;
  errors: number;
}

interface CloudSyncProps {
  onFileUpload?: (file: File) => Promise<void>;
  onFileDownload?: (fileId: string) => Promise<void>;
  onFileDelete?: (fileId: string) => Promise<void>;
  onFileShare?: (fileId: string, users: string[]) => Promise<void>;
  onSyncStart?: () => Promise<void>;
  onSyncStop?: () => Promise<void>;
  onConflictResolve?: (fileId: string, resolution: 'local' | 'remote') => Promise<void>;
}

// Cloud File List Component
const CloudFileList: React.FC<{
  files: CloudFile[];
  onFileSelect: (file: CloudFile) => void;
  onFileDownload: (fileId: string) => void;
  onFileDelete: (fileId: string) => void;
  onFileShare: (fileId: string) => void;
}> = ({ files, onFileSelect, onFileDownload, onFileDelete, onFileShare }) => {
  const getStatusColor = (status: CloudFile['status']) => {
    switch (status) {
      case 'synced': return 'success';
      case 'pending': return 'warning';
      case 'conflict': return 'error';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: CloudFile['status']) => {
    switch (status) {
      case 'synced': return <CloudDoneIcon />;
      case 'pending': return <CloudSyncIcon />;
      case 'conflict': return <WarningIcon />;
      case 'error': return <ErrorIcon />;
      default: return <CloudIcon />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Cloud Files ({files.length})
      </Typography>
      <List>
        {files.map((file) => (
          <ListItem key={file.id} button onClick={() => onFileSelect(file)}>
            <ListItemIcon>
              <Badge
                overlap="circular"
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                badgeContent={
                  <Avatar sx={{ width: 12, height: 12 }}>
                    {getStatusIcon(file.status)}
                  </Avatar>
                }
              >
                <Avatar>
                  <FolderIcon />
                </Avatar>
              </Badge>
            </ListItemIcon>
            <ListItemText
              primary={file.name}
              secondary={
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    {file.path} • {formatFileSize(file.size)} • v{file.version}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Modified: {file.lastModified.toLocaleString()}
                  </Typography>
                  {file.metadata.tags && (
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                      {file.metadata.tags.map((tag, index) => (
                        <Chip key={index} label={tag} size="small" variant="outlined" />
                      ))}
                    </Box>
                  )}
                </Box>
              }
            />
            <ListItemSecondaryAction>
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                <Tooltip title="Download">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      onFileDownload(file.id);
                    }}
                  >
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Share">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      onFileShare(file.id);
                    }}
                  >
                    <ShareIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete">
                  <IconButton
                    size="small"
                    color="error"
                    onClick={(e) => {
                      e.stopPropagation();
                      onFileDelete(file.id);
                    }}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </ListItemSecondaryAction>
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

// Sync Status Component
const SyncStatus: React.FC<{
  status: SyncStatus;
  onSyncStart: () => void;
  onSyncStop: () => void;
}> = ({ status, onSyncStart, onSyncStop }) => {
  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Sync Status</Typography>
          <Chip
            icon={status.isConnected ? <CloudDoneIcon /> : <CloudOffIcon />}
            label={status.isConnected ? 'Connected' : 'Disconnected'}
            color={status.isConnected ? 'success' : 'error'}
            size="small"
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="primary">
              {status.pendingChanges}
            </Typography>
            <Typography variant="caption">Pending</Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="error">
              {status.conflicts}
            </Typography>
            <Typography variant="caption">Conflicts</Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="error">
              {status.errors}
            </Typography>
            <Typography variant="caption">Errors</Typography>
          </Box>
        </Box>

        {status.isSyncing && (
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Syncing...</Typography>
              <Typography variant="body2">{status.syncProgress}%</Typography>
            </Box>
            <LinearProgress variant="determinate" value={status.syncProgress} />
          </Box>
        )}

        <Box sx={{ display: 'flex', gap: 1 }}>
          {status.isSyncing ? (
            <Button
              variant="outlined"
              color="error"
              startIcon={<StopIcon />}
              onClick={onSyncStop}
            >
              Stop Sync
            </Button>
          ) : (
            <Button
              variant="contained"
              startIcon={<SyncIcon />}
              onClick={onSyncStart}
              disabled={!status.isConnected}
            >
              Start Sync
            </Button>
          )}
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            disabled={status.isSyncing}
          >
            Refresh
          </Button>
        </Box>

        {status.lastSync && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Last sync: {status.lastSync.toLocaleString()}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

// Conflict Resolution Component
const ConflictResolution: React.FC<{
  conflicts: CloudFile[];
  onResolve: (fileId: string, resolution: 'local' | 'remote') => void;
}> = ({ conflicts, onResolve }) => {
  if (conflicts.length === 0) {
    return (
      <Alert severity="success">
        No conflicts detected. All files are in sync.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Conflicts ({conflicts.length})
      </Typography>
      <Alert severity="warning" sx={{ mb: 2 }}>
        The following files have conflicts between local and cloud versions.
      </Alert>
      <List>
        {conflicts.map((file) => (
          <ListItem key={file.id}>
            <ListItemIcon>
              <WarningIcon color="warning" />
            </ListItemIcon>
            <ListItemText
              primary={file.name}
              secondary={`Version conflict detected. Choose which version to keep.`}
            />
            <ListItemSecondaryAction>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => onResolve(file.id, 'local')}
                >
                  Keep Local
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => onResolve(file.id, 'remote')}
                >
                  Keep Remote
                </Button>
              </Box>
            </ListItemSecondaryAction>
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

// Main Cloud Sync Component
export const CloudSync: React.FC<CloudSyncProps> = ({
  onFileUpload,
  onFileDownload,
  onFileDelete,
  onFileShare,
  onSyncStart,
  onSyncStop,
  onConflictResolve,
}) => {
  const [files, setFiles] = useState<CloudFile[]>([]);
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({
    isConnected: true,
    isSyncing: false,
    lastSync: new Date(),
    syncProgress: 0,
    pendingChanges: 3,
    conflicts: 1,
    errors: 0,
  });
  const [activeTab, setActiveTab] = useState<'files' | 'sync' | 'conflicts' | 'settings'>('files');
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<CloudFile | null>(null);
  const [autoSync, setAutoSync] = useState(true);

  // Mock cloud files
  useEffect(() => {
    const mockFiles: CloudFile[] = [
      {
        id: 'file_1',
        name: 'Project_Design.svgx',
        path: '/projects/design/',
        size: 2048576,
        lastModified: new Date(Date.now() - 3600000),
        version: '1.2.0',
        status: 'synced',
        metadata: {
          description: 'Main project design file',
          tags: ['design', 'main', 'project'],
          isPublic: false,
          sharedWith: ['user1@example.com'],
        },
      },
      {
        id: 'file_2',
        name: 'Component_Library.svgx',
        path: '/libraries/components/',
        size: 1048576,
        lastModified: new Date(Date.now() - 7200000),
        version: '2.1.0',
        status: 'pending',
        metadata: {
          description: 'Reusable component library',
          tags: ['library', 'components', 'reusable'],
          isPublic: true,
        },
      },
      {
        id: 'file_3',
        name: 'Assembly_Model.svgx',
        path: '/assemblies/',
        size: 3145728,
        lastModified: new Date(Date.now() - 1800000),
        version: '1.0.5',
        status: 'conflict',
        metadata: {
          description: 'Assembly model with conflicts',
          tags: ['assembly', 'model', 'conflict'],
          isPublic: false,
        },
      },
    ];

    setFiles(mockFiles);
  }, []);

  // Handle file selection
  const handleFileSelect = useCallback((file: CloudFile) => {
    setSelectedFile(file);
    console.log('Selected file:', file);
  }, []);

  // Handle file download
  const handleFileDownload = useCallback((fileId: string) => {
    onFileDownload?.(fileId);
  }, [onFileDownload]);

  // Handle file delete
  const handleFileDelete = useCallback((fileId: string) => {
    if (window.confirm('Are you sure you want to delete this file?')) {
      onFileDelete?.(fileId);
      setFiles(prev => prev.filter(f => f.id !== fileId));
    }
  }, [onFileDelete]);

  // Handle file share
  const handleFileShare = useCallback((fileId: string) => {
    setSelectedFile(files.find(f => f.id === fileId) || null);
    setShowShareDialog(true);
  }, [files]);

  // Handle sync start
  const handleSyncStart = useCallback(() => {
    setSyncStatus(prev => ({ ...prev, isSyncing: true, syncProgress: 0 }));
    
    // Simulate sync progress
    const interval = setInterval(() => {
      setSyncStatus(prev => {
        if (prev.syncProgress >= 100) {
          clearInterval(interval);
          return {
            ...prev,
            isSyncing: false,
            lastSync: new Date(),
            pendingChanges: 0,
            conflicts: 0,
          };
        }
        return {
          ...prev,
          syncProgress: prev.syncProgress + 10,
        };
      });
    }, 500);

    onSyncStart?.();
  }, [onSyncStart]);

  // Handle sync stop
  const handleSyncStop = useCallback(() => {
    setSyncStatus(prev => ({ ...prev, isSyncing: false }));
    onSyncStop?.();
  }, [onSyncStop]);

  // Handle conflict resolution
  const handleConflictResolve = useCallback((fileId: string, resolution: 'local' | 'remote') => {
    setFiles(prev =>
      prev.map(f => f.id === fileId ? { ...f, status: 'synced' } : f)
    );
    setSyncStatus(prev => ({ ...prev, conflicts: prev.conflicts - 1 }));
    onConflictResolve?.(fileId, resolution);
  }, [onConflictResolve]);

  // Get conflicts
  const conflicts = files.filter(f => f.status === 'conflict');

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h6">
            Cloud Sync
            <Chip
              label={syncStatus.isConnected ? 'Connected' : 'Disconnected'}
              color={syncStatus.isConnected ? 'success' : 'error'}
              size="small"
              sx={{ ml: 1 }}
            />
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              size="small"
              variant="contained"
              startIcon={<CloudUploadIcon />}
              onClick={() => setShowUploadDialog(true)}
            >
              Upload
            </Button>
            <Tooltip title="Sync Settings">
              <IconButton
                size="small"
                onClick={() => setActiveTab('settings')}
              >
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Tab Navigation */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant={activeTab === 'files' ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setActiveTab('files')}
            startIcon={<FolderIcon />}
          >
            Files ({files.length})
          </Button>
          <Button
            variant={activeTab === 'sync' ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setActiveTab('sync')}
            startIcon={<CloudSyncIcon />}
          >
            Sync Status
          </Button>
          <Button
            variant={activeTab === 'conflicts' ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setActiveTab('conflicts')}
            startIcon={<WarningIcon />}
          >
            Conflicts ({conflicts.length})
          </Button>
        </Box>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {activeTab === 'files' && (
          <CloudFileList
            files={files}
            onFileSelect={handleFileSelect}
            onFileDownload={handleFileDownload}
            onFileDelete={handleFileDelete}
            onFileShare={handleFileShare}
          />
        )}

        {activeTab === 'sync' && (
          <SyncStatus
            status={syncStatus}
            onSyncStart={handleSyncStart}
            onSyncStop={handleSyncStop}
          />
        )}

        {activeTab === 'conflicts' && (
          <ConflictResolution
            conflicts={conflicts}
            onResolve={handleConflictResolve}
          />
        )}

        {activeTab === 'settings' && (
          <Box>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Sync Settings
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={autoSync}
                  onChange={(e) => setAutoSync(e.target.checked)}
                />
              }
              label="Auto-sync"
            />
            <Alert severity="info" sx={{ mt: 2 }}>
              Additional sync settings will be implemented here.
            </Alert>
          </Box>
        )}
      </Box>

      {/* Upload Dialog */}
      <Dialog open={showUploadDialog} onClose={() => setShowUploadDialog(false)}>
        <DialogTitle>Upload to Cloud</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Select files to upload to the cloud.
          </Typography>
          <Button
            variant="contained"
            component="label"
            startIcon={<UploadIcon />}
          >
            Choose Files
            <input
              type="file"
              hidden
              multiple
              accept=".svgx,.dxf,.ifc"
              onChange={(e) => {
                const files = e.target.files;
                if (files) {
                  Array.from(files).forEach(file => {
                    onFileUpload?.(file);
                  });
                }
                setShowUploadDialog(false);
              }}
            />
          </Button>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowUploadDialog(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Share Dialog */}
      <Dialog open={showShareDialog} onClose={() => setShowShareDialog(false)}>
        <DialogTitle>Share File</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Share "{selectedFile?.name}" with other users.
          </Typography>
          <TextField
            fullWidth
            label="Email addresses (comma-separated)"
            placeholder="user1@example.com, user2@example.com"
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={<Switch />}
            label="Make file public"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowShareDialog(false)}>Cancel</Button>
          <Button variant="contained">Share</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}; 