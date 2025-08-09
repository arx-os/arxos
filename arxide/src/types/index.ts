// ArxIDE Type Definitions
// Following Clean Architecture principles with proper type safety

// Core CAD Types
export interface ThreeDObject {
  id: string;
  type: 'box' | 'sphere' | 'cylinder' | 'line' | 'plane';
  position: [number, number, number];
  rotation: [number, number, number];
  scale: [number, number, number];
  color: string;
  material?: string;
  dimensions?: {
    width?: number;
    height?: number;
    depth?: number;
    radius?: number;
  };
  constraints?: any[];
  metadata?: any;
}

export interface Constraint {
  id: string;
  type: 'distance' | 'angle' | 'parallel' | 'perpendicular' | 'coincident' | 'tangent' | 'horizontal' | 'vertical' | 'parametric' | 'dynamic';
  objects: string[];
  parameters: {
    value?: number;
    expression?: string;
    tolerance?: number;
    units?: string;
  };
  status: 'valid' | 'invalid' | 'warning' | 'pending';
  metadata?: {
    description?: string;
    category?: string;
    priority?: number;
    autoSolve?: boolean;
  };
}

export interface Plugin {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  category: 'tool' | 'constraint' | 'export' | 'import' | 'utility' | 'visualization';
  status: 'active' | 'inactive' | 'error' | 'loading';
  enabled: boolean;
  settings: Record<string, any>;
  dependencies: string[];
  permissions: string[];
  metadata: {
    icon?: string;
    homepage?: string;
    repository?: string;
    license?: string;
    tags?: string[];
    size?: number;
    downloads?: number;
    rating?: number;
    lastUpdated?: string;
  };
}

// Application State Types
export interface ProjectData {
  id: string;
  name: string;
  description: string;
  createdAt: Date;
  lastModified: Date;
  objects: ThreeDObject[];
  constraints: Constraint[];
  settings: Record<string, any>;
}

export interface FileInfo {
  path: string;
  name: string;
  size: number;
  lastModified: Date;
  type: 'svgx' | 'svg' | 'json' | 'ifc';
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  status: 'online' | 'offline' | 'away';
  role: 'owner' | 'editor' | 'viewer';
  lastSeen: Date;
  currentActivity: string;
}

export interface CollaborationSession {
  id: string;
  name: string;
  participants: User[];
  projectId: string;
  createdAt: Date;
  isActive: boolean;
}

// Component Props Types
export interface ThreeDViewerProps {
  objects: ThreeDObject[];
  selectedObject?: string;
  onObjectSelect?: (objectId: string) => void;
  onObjectUpdate?: (objectId: string, updates: Partial<ThreeDObject>) => void;
  viewMode: '2D' | '3D';
  onViewModeChange?: (mode: '2D' | '3D') => void;
  precision: number;
  gridSize: number;
}

export interface AdvancedConstraintsProps {
  constraints: Constraint[];
  objects: any[];
  onConstraintAdd: (constraint: Constraint) => void;
  onConstraintUpdate: (constraintId: string, updates: Partial<Constraint>) => void;
  onConstraintDelete: (constraintId: string) => void;
  onConstraintsOptimize: () => void;
  onConstraintSolve: (constraintId: string) => void;
  precision: number;
}

export interface PluginSystemProps {
  plugins: Plugin[];
  onPluginInstall: (pluginId: string) => void;
  onPluginUninstall: (pluginId: string) => void;
  onPluginEnable: (pluginId: string) => void;
  onPluginDisable: (pluginId: string) => void;
  onPluginUpdate: (pluginId: string, settings: Record<string, any>) => void;
  onPluginExecute: (pluginId: string, parameters?: any) => void;
  availablePlugins?: Plugin[];
  onPluginSearch?: (query: string) => void;
  onPluginDownload?: (pluginId: string) => void;
}

export interface AIIntegrationProps {
  suggestions: AISuggestion[];
  onSuggestionApply: (suggestionId: string) => void;
  onSuggestionReject: (suggestionId: string) => void;
  onCommandSubmit: (command: string) => void;
  isProcessing: boolean;
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}

export interface CollaborationSystemProps {
  session: CollaborationSession | null;
  participants: User[];
  onJoinSession: (sessionId: string) => void;
  onLeaveSession: () => void;
  onInviteUser: (userId: string) => void;
  onSendMessage: (message: string) => void;
  messages: CollaborationMessage[];
  isConnected: boolean;
}

export interface CloudSyncProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  syncStatus: 'synced' | 'syncing' | 'conflict' | 'error';
  lastSync: Date | null;
  onSync: () => void;
  onResolveConflict: (resolution: 'local' | 'remote' | 'merge') => void;
}

// AI Types
export interface AISuggestion {
  id: string;
  type: 'design' | 'optimization' | 'analysis' | 'generation' | 'correction';
  title: string;
  description: string;
  confidence: number;
  status: 'pending' | 'applied' | 'rejected' | 'error';
  timestamp: Date;
  metadata?: {
    category?: string;
    priority?: number;
    tags?: string[];
    parameters?: any;
  };
}

// Collaboration Types
export interface CollaborationMessage {
  id: string;
  userId: string;
  userName: string;
  content: string;
  timestamp: Date;
  type: 'text' | 'command' | 'system';
}

// Status Types
export type ApplicationStatus = 'ready' | 'loading' | 'error' | 'building';

// Tab Types
export type ActiveTab = 'cad' | '3d' | 'constraints' | 'plugins' | 'collaboration' | 'ai' | 'cloud';
