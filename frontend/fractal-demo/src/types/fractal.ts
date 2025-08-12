// Core fractal system types
export interface FractalCoordinate {
  x: number;
  y: number;
  z: number;
}

export interface BoundingBox {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

export interface TileCoordinate {
  z: number; // zoom level
  x: number;
  y: number;
}

export interface ScaleLevel {
  id: number;
  name: string;
  minScale: number;
  maxScale: number;
  pixelsPerMeter: number;
}

// Fractal ArxObject types
export interface FractalArxObject {
  id: string;
  name: string;
  type: string;
  scaleLevel: number;
  position: FractalCoordinate;
  bounds: BoundingBox;
  parentId?: string;
  children: string[];
  lastModified: Date;
  contributors: string[];
  biltReward: number;
  visibility: VisibilityRule;
  detailLevels: DetailLevel[];
}

export interface VisibilityRule {
  minScale: number;
  maxScale: number;
  priority: 'immediate' | 'high' | 'normal' | 'low';
  lodStrategy: 'progressive' | 'immediate' | 'lazy';
}

export interface DetailLevel {
  level: number;
  name: string;
  minScale: number;
  data?: any;
  loadStatus: 'pending' | 'loading' | 'loaded' | 'error';
}

// Tile and loading types
export interface TileData {
  coordinate: TileCoordinate;
  bounds: BoundingBox;
  objects: FractalArxObject[];
  vectorData?: VectorTileData;
  metadata: TileMetadata;
}

export interface VectorTileData {
  features: GeoJSONFeature[];
  compression: 'none' | 'gzip' | 'pbf';
}

export interface GeoJSONFeature {
  type: 'Feature';
  geometry: {
    type: string;
    coordinates: any;
  };
  properties: {
    id: string;
    name: string;
    type: string;
    scaleLevel: number;
    [key: string]: any;
  };
}

export interface TileMetadata {
  objectCount: number;
  dataSize: number;
  compressed: boolean;
  cacheTime: Date;
  loadTime: number;
}

// Performance and loading types
export interface PerformanceBudget {
  maxConcurrentTiles: number;
  targetFramerate: number;
  maxMemoryUsage: number;
  tileLoadTimeout: number;
  qualitySettings: QualitySettings;
}

export interface QualitySettings {
  maxLodLevel: number;
  textureResolution: number;
  geometryDetail: number;
  enableShadows: boolean;
  enableReflections: boolean;
}

export interface DeviceCapabilities {
  memory: number;
  cores: number;
  gpu: 'low' | 'medium' | 'high' | 'discrete';
  connection: 'slow' | 'fast' | 'wifi' | 'cellular';
  screenSize: { width: number; height: number };
  pixelRatio: number;
}

// Viewport and navigation types
export interface ViewportState {
  center: { x: number; y: number };
  scale: number;
  rotation: number;
  bounds: BoundingBox;
  scaleLevel: number;
}

export interface ZoomRequest {
  targetScale: number;
  center?: { x: number; y: number };
  duration?: number;
  easing?: 'linear' | 'easeInOut' | 'easeOut' | 'spring';
}

export interface PanRequest {
  deltaX: number;
  deltaY: number;
  duration?: number;
}

// WebSocket and real-time types
export interface RealtimeUpdate {
  type: 'object_update' | 'object_create' | 'object_delete' | 'contribution_update';
  objectId: string;
  data: Partial<FractalArxObject>;
  timestamp: Date;
}

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: Date;
}

// API Response types
export interface LoadTilesResponse {
  tiles: Array<{
    coordinate: TileCoordinate;
    objectCount: number;
    dataSize: number;
    source: 'vector' | 'raster';
    compressed: boolean;
  }>;
}

export interface ProgressiveDetailsResponse {
  objectId: string;
  scale: number;
  detailsLoaded: number;
  details: Array<{
    level: number;
    type: string;
    loadTime: number;
    source: string;
    compressed: boolean;
  }>;
}

export interface CacheStats {
  tiles: {
    memoryHits: number;
    redisHits: number;
    databaseHits: number;
    misses: number;
    totalSize: number;
  };
  details: {
    loadedObjects: number;
    cachedDetails: number;
    averageLoadTime: number;
  };
  prediction: {
    accuracy: number;
    predictionsUsed: number;
    cacheHitImprovement: number;
  };
}

// User behavior and prediction types
export interface UserBehavior {
  timestamp: Date;
  action: 'zoom' | 'pan' | 'click' | 'hover';
  viewport: ViewportState;
  target?: { x: number; y: number; objectId?: string };
  duration?: number;
}

export interface PredictionResult {
  nextViewport: ViewportState;
  confidence: number;
  suggestedPreloads: TileCoordinate[];
}

// Component prop types
export interface ZoomControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
  currentScale: number;
  minScale: number;
  maxScale: number;
}

export interface PerformanceIndicatorProps {
  fps: number;
  loadedTiles: number;
  memoryUsage: number;
  budget: PerformanceBudget;
}

export interface FractalViewerProps {
  initialCenter?: { x: number; y: number };
  initialScale?: number;
  enablePredictive?: boolean;
  debugMode?: boolean;
}