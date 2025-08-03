import React, { useEffect, useState, useRef } from 'react';
import { Box, AppBar, Toolbar, Typography, IconButton, Menu, MenuItem, 
         Drawer, List, ListItem, ListItemIcon, ListItemText, Divider,
         Dialog, DialogTitle, DialogContent, DialogActions, Button,
         TextField, Alert, Snackbar, Tooltip, Chip, Tabs, Tab } from '@mui/material';
import {
  Menu as MenuIcon,
  Save as SaveIcon,
  FolderOpen as OpenIcon,
  Settings as SettingsIcon,
  Help as HelpIcon,
  ExitToApp as ExitIcon,
  FileDownload as ExportIcon,
  FileUpload as ImportIcon,
  Code as CodeIcon,
  Notifications as NotificationsIcon,
  AccountCircle as AccountIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  ViewInAr as View3DIcon,
  ViewModule as View2DIcon,
  Extension as PluginIcon,
  AutoFixHigh as ConstraintIcon,
  Build as BuildIcon,
  Group as GroupIcon,
  SmartToy as AIIcon,
  Cloud as CloudIcon
} from '@mui/icons-material';
import { ThreeDViewer } from './ThreeDViewer';
import { AdvancedConstraints } from './AdvancedConstraints';
import { PluginSystem } from './PluginSystem';
import { CollaborationSystem } from './CollaborationSystem';
import { AIIntegration } from './AIIntegration';
import { CloudSync } from './CloudSync';
import { invoke } from '@tauri-apps/api/tauri';
import { open, save } from '@tauri-apps/api/dialog';
import { appWindow } from '@tauri-apps/api/window';
import { listen } from '@tauri-apps/api/event';
import { isPermissionGranted, requestPermission, sendNotification } from '@tauri-apps/api/notification';

interface ArxIDEApplicationProps {}

interface FileInfo {
  name: string;
  path: string;
  lastModified: Date;
  size: number;
}

interface ProjectData {
  id: string;
  name: string;
  description: string;
  createdAt: Date;
  lastModified: Date;
  objects: any[];
  constraints: any[];
  settings: any;
}

export const ArxIDEApplication: React.FC<ArxIDEApplicationProps> = () => {
  // State management
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [currentFile, setCurrentFile] = useState<FileInfo | null>(null);
  const [projectData, setProjectData] = useState<ProjectData | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isCollaborating, setIsCollaborating] = useState(false);
  const [notifications, setNotifications] = useState<string[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  
  // Advanced features state
  const [viewMode, setViewMode] = useState<'2D' | '3D'>('2D');
  const [selectedObject, setSelectedObject] = useState<string | null>(null);
  const [constraints, setConstraints] = useState<any[]>([]);
  const [plugins, setPlugins] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'cad' | '3d' | 'constraints' | 'plugins' | 'collaboration' | 'ai' | 'cloud'>('cad');
  
  // Professional features state
  const [collaborationSession, setCollaborationSession] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState({
    id: 'user_001',
    name: 'John Doe',
    email: 'john@example.com',
    avatar: undefined,
    status: 'online' as const,
    role: 'owner' as const,
    lastSeen: new Date(),
    currentActivity: 'Editing design',
  });
  const [aiEnabled, setAiEnabled] = useState(true);
  const [cloudSyncEnabled, setCloudSyncEnabled] = useState(true);
  
  // Menu state
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  
  // CAD Engine reference
  const cadEngineRef = useRef<any>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  // Initialize CAD Engine and desktop features
  useEffect(() => {
    initializeArxIDE();
    setupDesktopFeatures();
    setupEventListeners();
  }, []);
  
  /**
   * Initialize ArxIDE with CAD engine and desktop features
   */
  const initializeArxIDE = async () => {
    try {
      console.log('🚀 Initializing ArxIDE Desktop CAD...');
      
      // Initialize CAD Engine (from browser CAD)
      if (typeof window !== 'undefined') {
        // Load CAD engine scripts
        await loadCadScripts();
        
        // Initialize CAD engine
        if (window.CadEngine) {
          cadEngineRef.current = new window.CadEngine();
          await cadEngineRef.current.initialize('cad-canvas');
          console.log('✅ CAD Engine initialized');
        }
        
        // Initialize constraint solver
        if (window.ConstraintSolver) {
          const constraintSolver = new window.ConstraintSolver();
          if (cadEngineRef.current) {
            cadEngineRef.current.constraintSolver = constraintSolver;
          }
          console.log('✅ Constraint Solver initialized');
        }
      }
      
      // Initialize desktop features
      await initializeDesktopFeatures();
      
      console.log('✅ ArxIDE initialized successfully');
      
    } catch (error) {
      console.error('❌ Failed to initialize ArxIDE:', error);
      showNotification('Failed to initialize ArxIDE', 'error');
    }
  };
  
  /**
   * Load CAD engine scripts
   */
  const loadCadScripts = async () => {
    const scripts = [
      '/static/js/cad-constraints.js',
      '/static/js/cad-engine.js',
      '/static/js/cad-workers.js',
      '/static/js/arx-objects.js',
      '/static/js/cad-api-client.js',
      '/static/js/cad-collaboration.js',
      '/static/js/cad-ai-integration.js',
      '/static/js/cad-ui.js',
      '/static/js/ai-assistant.js'
    ];
    
    for (const script of scripts) {
      try {
        await loadScript(script);
      } catch (error) {
        console.warn(`Failed to load script: ${script}`, error);
      }
    }
  };
  
  /**
   * Load script dynamically
   */
  const loadScript = (src: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
      document.head.appendChild(script);
    });
  };
  
  /**
   * Initialize desktop-specific features
   */
  const initializeDesktopFeatures = async () => {
    try {
      // Request notification permissions
      const permissionGranted = await isPermissionGranted();
      if (!permissionGranted) {
        const permission = await requestPermission();
        console.log('Notification permission:', permission);
      }
      
      // Set up window event listeners
      await appWindow.listen('tauri://close-requested', () => {
        handleAppClose();
      });
      
      // Set up file system watchers
      await setupFileWatchers();
      
      console.log('✅ Desktop features initialized');
      
    } catch (error) {
      console.error('Failed to initialize desktop features:', error);
    }
  };
  
  /**
   * Set up desktop event listeners
   */
  const setupEventListeners = () => {
    // Listen for file system events
    listen('file-changed', (event) => {
      console.log('File changed:', event);
      showNotification('File changed externally', 'info');
    });
    
    // Listen for system notifications
    listen('system-notification', (event) => {
      console.log('System notification:', event);
      addNotification(event.payload as string);
    });
  };
  
  /**
   * Set up file system watchers
   */
  const setupFileWatchers = async () => {
    if (currentFile?.path) {
      try {
        await invoke('watch_file', { path: currentFile.path });
      } catch (error) {
        console.warn('Failed to set up file watcher:', error);
      }
    }
  };
  
  /**
   * Handle app close with unsaved changes
   */
  const handleAppClose = async () => {
    if (hasUnsavedChanges()) {
      const result = await showUnsavedChangesDialog();
      if (result === 'save') {
        await saveFile();
      } else if (result === 'cancel') {
        return; // Don't close
      }
    }
    
    // Close the app
    await appWindow.close();
  };
  
  /**
   * Check for unsaved changes
   */
  const hasUnsavedChanges = (): boolean => {
    // Implementation would check if current data differs from saved data
    return false; // Placeholder
  };
  
  /**
   * Show unsaved changes dialog
   */
  const showUnsavedChangesDialog = (): Promise<'save' | 'discard' | 'cancel'> => {
    return new Promise((resolve) => {
      // Implementation would show a dialog
      resolve('discard'); // Placeholder
    });
  };
  
  /**
   * File operations
   */
  const newFile = async () => {
    try {
      setCurrentFile(null);
      setProjectData({
        id: generateId(),
        name: 'Untitled Project',
        description: '',
        createdAt: new Date(),
        lastModified: new Date(),
        objects: [],
        constraints: [],
        settings: {}
      });
      
      // Clear CAD canvas
      if (cadEngineRef.current) {
        cadEngineRef.current.clearCanvas();
      }
      
      showNotification('New file created', 'success');
      
    } catch (error) {
      console.error('Failed to create new file:', error);
      showNotification('Failed to create new file', 'error');
    }
  };
  
  const openFile = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{
          name: 'SVGX Files',
          extensions: ['svgx']
        }, {
          name: 'All Files',
          extensions: ['*']
        }]
      });
      
      if (selected) {
        const filePath = selected as string;
        const fileData = await invoke('read_file', { path: filePath });
        
        // Parse SVGX data
        const projectData = JSON.parse(fileData as string);
        setProjectData(projectData);
        
        // Load into CAD engine
        if (cadEngineRef.current) {
          cadEngineRef.current.loadProject(projectData);
        }
        
        setCurrentFile({
          name: filePath.split('/').pop() || 'Unknown',
          path: filePath,
          lastModified: new Date(),
          size: (fileData as string).length
        });
        
        showNotification('File opened successfully', 'success');
      }
      
    } catch (error) {
      console.error('Failed to open file:', error);
      showNotification('Failed to open file', 'error');
    }
  };
  
  const saveFile = async () => {
    try {
      if (!currentFile) {
        return await saveFileAs();
      }
      
      // Get current project data
      const projectData = getCurrentProjectData();
      
      // Save to file
      await invoke('write_file', {
        path: currentFile.path,
        content: JSON.stringify(projectData, null, 2)
      });
      
      setCurrentFile({
        ...currentFile,
        lastModified: new Date(),
        size: JSON.stringify(projectData).length
      });
      
      showNotification('File saved successfully', 'success');
      
    } catch (error) {
      console.error('Failed to save file:', error);
      showNotification('Failed to save file', 'error');
    }
  };
  
  const saveFileAs = async () => {
    try {
      const selected = await save({
        filters: [{
          name: 'SVGX Files',
          extensions: ['svgx']
        }]
      });
      
      if (selected) {
        const filePath = selected as string;
        const projectData = getCurrentProjectData();
        
        await invoke('write_file', {
          path: filePath,
          content: JSON.stringify(projectData, null, 2)
        });
        
        setCurrentFile({
          name: filePath.split('/').pop() || 'Unknown',
          path: filePath,
          lastModified: new Date(),
          size: JSON.stringify(projectData).length
        });
        
        showNotification('File saved successfully', 'success');
      }
      
    } catch (error) {
      console.error('Failed to save file:', error);
      showNotification('Failed to save file', 'error');
    }
  };
  
  /**
   * Export operations
   */
  const exportToDXF = async () => {
    try {
      const selected = await save({
        filters: [{
          name: 'DXF Files',
          extensions: ['dxf']
        }]
      });
      
      if (selected) {
        const filePath = selected as string;
        const dxfData = await invoke('export_to_dxf', {
          path: filePath,
          projectData: getCurrentProjectData()
        });
        
        showNotification('Exported to DXF successfully', 'success');
      }
      
    } catch (error) {
      console.error('Failed to export to DXF:', error);
      showNotification('Failed to export to DXF', 'error');
    }
  };
  
  const exportToIFC = async () => {
    try {
      const selected = await save({
        filters: [{
          name: 'IFC Files',
          extensions: ['ifc']
        }]
      });
      
      if (selected) {
        const filePath = selected as string;
        const ifcData = await invoke('export_to_ifc', {
          path: filePath,
          projectData: getCurrentProjectData()
        });
        
        showNotification('Exported to IFC successfully', 'success');
      }
      
    } catch (error) {
      console.error('Failed to export to IFC:', error);
      showNotification('Failed to export to IFC', 'error');
    }
  };
  
  /**
   * Get current project data
   */
  const getCurrentProjectData = (): ProjectData => {
    if (!projectData) {
      return {
        id: generateId(),
        name: 'Untitled Project',
        description: '',
        createdAt: new Date(),
        lastModified: new Date(),
        objects: [],
        constraints: [],
        settings: {}
      };
    }
    
    // Get objects from CAD engine
    const objects = cadEngineRef.current ? 
      Array.from(cadEngineRef.current.arxObjects.values()) : [];
    
    // Get constraints from constraint solver
    const constraints = cadEngineRef.current?.constraintSolver ? 
      Array.from(cadEngineRef.current.constraintSolver.constraints.values()) : [];
    
    return {
      ...projectData,
      objects,
      constraints,
      lastModified: new Date()
    };
  };
  
  /**
   * Utility functions
   */
  const generateId = (): string => {
    return `arx_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };
  
  const showNotification = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
    addNotification(message);
    
    // Send system notification
    sendNotification({
      title: 'ArxIDE',
      body: message,
      icon: type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'
    });
  };
  
  const addNotification = (message: string) => {
    setNotifications(prev => [...prev, message]);
  };
  
  const removeNotification = (index: number) => {
    setNotifications(prev => prev.filter((_, i) => i !== index));
  };
  
  /**
   * Menu handlers
   */
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };
  
  const handleMenuClose = () => {
    setAnchorEl(null);
  };
  
  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };
  
  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };
  
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* App Bar */}
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={toggleDrawer}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ArxIDE - Professional CAD
            {currentFile && (
              <Chip 
                label={currentFile.name} 
                size="small" 
                sx={{ ml: 2 }}
                color="primary"
                variant="outlined"
              />
            )}
          </Typography>
          
          <Tooltip title="Toggle Dark Mode">
            <IconButton color="inherit" onClick={toggleDarkMode}>
              {isDarkMode ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Notifications">
            <IconButton color="inherit">
              <NotificationsIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Account">
            <IconButton color="inherit">
              <AccountIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>
      
      {/* Main Content */}
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <Drawer
          variant="temporary"
          open={drawerOpen}
          onClose={toggleDrawer}
          sx={{
            '& .MuiDrawer-paper': {
              width: 240,
              boxSizing: 'border-box',
            },
          }}
        >
          <List>
            <ListItem button onClick={newFile}>
              <ListItemIcon>
                <CodeIcon />
              </ListItemIcon>
              <ListItemText primary="New File" />
            </ListItem>
            
            <ListItem button onClick={openFile}>
              <ListItemIcon>
                <OpenIcon />
              </ListItemIcon>
              <ListItemText primary="Open File" />
            </ListItem>
            
            <ListItem button onClick={saveFile}>
              <ListItemIcon>
                <SaveIcon />
              </ListItemIcon>
              <ListItemText primary="Save" />
            </ListItem>
            
            <Divider />
            
            <ListItem button onClick={exportToDXF}>
              <ListItemIcon>
                <ExportIcon />
              </ListItemIcon>
              <ListItemText primary="Export to DXF" />
            </ListItem>
            
            <ListItem button onClick={exportToIFC}>
              <ListItemIcon>
                <ExportIcon />
              </ListItemIcon>
              <ListItemText primary="Export to IFC" />
            </ListItem>
            
            <Divider />
            
            <ListItem button onClick={() => setShowSettings(true)}>
              <ListItemIcon>
                <SettingsIcon />
              </ListItemIcon>
              <ListItemText primary="Settings" />
            </ListItem>
            
            <ListItem button onClick={() => setShowHelp(true)}>
              <ListItemIcon>
                <HelpIcon />
              </ListItemIcon>
              <ListItemText primary="Help" />
            </ListItem>
          </List>
        </Drawer>
        
        {/* Main Content Area */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Tab Navigation */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={activeTab} 
              onChange={(_, newValue) => setActiveTab(newValue)}
              variant="scrollable"
              scrollButtons="auto"
            >
              <Tab 
                label="2D CAD" 
                value="cad" 
                icon={<View2DIcon />}
                iconPosition="start"
              />
              <Tab 
                label="3D View" 
                value="3d" 
                icon={<View3DIcon />}
                iconPosition="start"
              />
              <Tab 
                label="Constraints" 
                value="constraints" 
                icon={<ConstraintIcon />}
                iconPosition="start"
              />
                        <Tab 
            label="Plugins" 
            value="plugins" 
            icon={<PluginIcon />}
            iconPosition="start"
          />
          <Tab 
            label="Collaboration" 
            value="collaboration" 
            icon={<GroupIcon />}
            iconPosition="start"
          />
          <Tab 
            label="AI Assistant" 
            value="ai" 
            icon={<AIIcon />}
            iconPosition="start"
          />
          <Tab 
            label="Cloud Sync" 
            value="cloud" 
            icon={<CloudIcon />}
            iconPosition="start"
          />
            </Tabs>
          </Box>

          {/* Content based on active tab */}
          {activeTab === 'cad' && (
            <Box sx={{ flex: 1, position: 'relative' }}>
              <canvas
                ref={canvasRef}
                id="cad-canvas"
                style={{
                  width: '100%',
                  height: '100%',
                  backgroundColor: isDarkMode ? '#1a1a1a' : '#ffffff'
                }}
              />
            </Box>
          )}

          {activeTab === '3d' && (
            <ThreeDViewer
              objects={projectData?.objects || []}
              selectedObject={selectedObject}
              onObjectSelect={setSelectedObject}
              onObjectUpdate={(objectId, updates) => {
                // Handle 3D object updates
                console.log('3D object update:', objectId, updates);
              }}
              viewMode={viewMode}
              onViewModeChange={setViewMode}
              precision={0.001}
              gridSize={0.1}
            />
          )}

          {activeTab === 'constraints' && (
            <AdvancedConstraints
              constraints={constraints}
              objects={projectData?.objects || []}
              onConstraintAdd={(constraint) => {
                setConstraints([...constraints, constraint]);
              }}
              onConstraintUpdate={(constraintId, updates) => {
                setConstraints(constraints.map(c => 
                  c.id === constraintId ? { ...c, ...updates } : c
                ));
              }}
              onConstraintDelete={(constraintId) => {
                setConstraints(constraints.filter(c => c.id !== constraintId));
              }}
              onConstraintsOptimize={() => {
                // Handle constraint optimization
                console.log('Optimizing constraints...');
              }}
              onConstraintSolve={(constraintId) => {
                // Handle constraint solving
                console.log('Solving constraint:', constraintId);
              }}
              precision={0.001}
            />
          )}

          {activeTab === 'plugins' && (
            <PluginSystem
              plugins={plugins}
              onPluginInstall={(pluginId) => {
                // Handle plugin installation
                console.log('Installing plugin:', pluginId);
              }}
              onPluginUninstall={(pluginId) => {
                setPlugins(plugins.filter(p => p.id !== pluginId));
              }}
              onPluginEnable={(pluginId) => {
                setPlugins(plugins.map(p => 
                  p.id === pluginId ? { ...p, enabled: true } : p
                ));
              }}
              onPluginDisable={(pluginId) => {
                setPlugins(plugins.map(p => 
                  p.id === pluginId ? { ...p, enabled: false } : p
                ));
              }}
              onPluginUpdate={(pluginId, settings) => {
                setPlugins(plugins.map(p => 
                  p.id === pluginId ? { ...p, settings } : p
                ));
              }}
              onPluginExecute={(pluginId, parameters) => {
                // Handle plugin execution
                console.log('Executing plugin:', pluginId, parameters);
              }}
              availablePlugins={[
                {
                  id: 'sample-tool',
                  name: 'Sample Tool',
                  version: '1.0.0',
                  description: 'A sample plugin for demonstration',
                  author: 'Arxos Team',
                  category: 'tool',
                  status: 'active',
                  enabled: true,
                  settings: {},
                  dependencies: [],
                  permissions: [],
                  metadata: {
                    tags: ['sample', 'demo'],
                    rating: 4.5,
                  }
                }
              ]}
            />
          )}

          {activeTab === 'collaboration' && (
            <CollaborationSystem
              sessionId={collaborationSession || 'session_001'}
              currentUser={currentUser}
              onUserJoin={(user) => {
                console.log('User joined:', user);
              }}
              onUserLeave={(userId) => {
                console.log('User left:', userId);
              }}
              onCommentAdd={(comment) => {
                console.log('Comment added:', comment);
              }}
              onCommentResolve={(commentId) => {
                console.log('Comment resolved:', commentId);
              }}
              onPermissionChange={(userId, permissions) => {
                console.log('Permission changed:', userId, permissions);
              }}
              onSessionEnd={() => {
                setCollaborationSession(null);
              }}
            />
          )}

          {activeTab === 'ai' && (
            <AIIntegration
              onSuggestionApply={(suggestion) => {
                console.log('AI suggestion applied:', suggestion);
              }}
              onSuggestionReject={(suggestionId) => {
                console.log('AI suggestion rejected:', suggestionId);
              }}
              onConversationStart={(prompt) => {
                console.log('AI conversation started:', prompt);
              }}
              onAutoComplete={async (partial) => {
                // Simulate AI auto-complete
                return `Completed: ${partial}`;
              }}
              onDesignAnalysis={async (design) => {
                // Simulate AI design analysis
                return { analysis: 'Design analysis completed' };
              }}
              onOptimization={async (parameters) => {
                // Simulate AI optimization
                return { optimization: 'Optimization completed' };
              }}
            />
          )}

          {activeTab === 'cloud' && (
            <CloudSync
              onFileUpload={async (file) => {
                console.log('File uploaded:', file);
              }}
              onFileDownload={async (fileId) => {
                console.log('File downloaded:', fileId);
              }}
              onFileDelete={async (fileId) => {
                console.log('File deleted:', fileId);
              }}
              onFileShare={async (fileId, users) => {
                console.log('File shared:', fileId, users);
              }}
              onSyncStart={async () => {
                console.log('Sync started');
              }}
              onSyncStop={async () => {
                console.log('Sync stopped');
              }}
              onConflictResolve={async (fileId, resolution) => {
                console.log('Conflict resolved:', fileId, resolution);
              }}
            />
          )}
        </Box>
      </Box>
      
      {/* Notifications */}
      <Snackbar
        open={notifications.length > 0}
        autoHideDuration={6000}
        onClose={() => removeNotification(0)}
      >
        <Alert severity="info" onClose={() => removeNotification(0)}>
          {notifications[0]}
        </Alert>
      </Snackbar>
      
      {/* Settings Dialog */}
      <Dialog open={showSettings} onClose={() => setShowSettings(false)} maxWidth="md" fullWidth>
        <DialogTitle>ArxIDE Settings</DialogTitle>
        <DialogContent>
          <Typography variant="h6" gutterBottom>
            CAD Settings
          </Typography>
          <TextField
            fullWidth
            label="Default Precision"
            defaultValue="0.001"
            margin="normal"
          />
          <TextField
            fullWidth
            label="Grid Size"
            defaultValue="0.1"
            margin="normal"
          />
          
          <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
            System Settings
          </Typography>
          <TextField
            fullWidth
            label="Auto-save Interval (minutes)"
            defaultValue="5"
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSettings(false)}>Cancel</Button>
          <Button onClick={() => setShowSettings(false)} variant="contained">
            Save Settings
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Help Dialog */}
      <Dialog open={showHelp} onClose={() => setShowHelp(false)} maxWidth="md" fullWidth>
        <DialogTitle>ArxIDE Help</DialogTitle>
        <DialogContent>
          <Typography variant="h6" gutterBottom>
            Getting Started
          </Typography>
          <Typography paragraph>
            ArxIDE is a professional desktop CAD application for building information modeling.
          </Typography>
          
          <Typography variant="h6" gutterBottom>
            Keyboard Shortcuts
          </Typography>
          <Typography component="div">
            <ul>
              <li><strong>Ctrl+N:</strong> New File</li>
              <li><strong>Ctrl+O:</strong> Open File</li>
              <li><strong>Ctrl+S:</strong> Save</li>
              <li><strong>Ctrl+Shift+S:</strong> Save As</li>
              <li><strong>Ctrl+Z:</strong> Undo</li>
              <li><strong>Ctrl+Y:</strong> Redo</li>
            </ul>
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowHelp(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}; 