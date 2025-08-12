import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import {
  ViewportState,
  FractalArxObject,
  TileData,
  TileCoordinate,
  PerformanceBudget,
  DeviceCapabilities,
  UserBehavior,
  CacheStats,
  ScaleLevel,
  BoundingBox,
} from '@/types/fractal';
import { ScaleEngineAPI, CoordinateUtils } from '@/lib/api';

// Scale levels definition (Campus to Schematic)
const SCALE_LEVELS: ScaleLevel[] = [
  { id: 1, name: 'Campus', minScale: 0.01, maxScale: 0.1, pixelsPerMeter: 0.01 },
  { id: 2, name: 'Building', minScale: 0.1, maxScale: 1.0, pixelsPerMeter: 0.1 },
  { id: 3, name: 'Floor', minScale: 1.0, maxScale: 10.0, pixelsPerMeter: 1.0 },
  { id: 4, name: 'Room', minScale: 10.0, maxScale: 100.0, pixelsPerMeter: 10.0 },
  { id: 5, name: 'Fixture', minScale: 100.0, maxScale: 1000.0, pixelsPerMeter: 100.0 },
  { id: 6, name: 'Component', minScale: 1000.0, maxScale: 10000.0, pixelsPerMeter: 1000.0 },
  { id: 7, name: 'Schematic', minScale: 10000.0, maxScale: 100000.0, pixelsPerMeter: 10000.0 },
];

interface FractalStore {
  // Viewport state
  viewport: ViewportState;
  isLoading: boolean;
  
  // Objects and tiles
  visibleObjects: FractalArxObject[];
  loadedTiles: Map<string, TileData>;
  tileLoadQueue: TileCoordinate[];
  
  // Performance
  performanceBudget: PerformanceBudget | null;
  deviceCapabilities: DeviceCapabilities | null;
  currentFps: number;
  cacheStats: CacheStats | null;
  
  // User behavior tracking
  userBehaviorHistory: UserBehavior[];
  predictiveEnabled: boolean;
  
  // Scale levels
  scaleLevels: ScaleLevel[];
  currentScaleLevel: ScaleLevel;
  
  // Debug mode
  debugMode: boolean;
  
  // Actions
  setViewport: (viewport: Partial<ViewportState>) => void;
  zoomTo: (scale: number, center?: { x: number; y: number }, duration?: number) => Promise<void>;
  panTo: (center: { x: number; y: number }, duration?: number) => Promise<void>;
  zoomIn: () => Promise<void>;
  zoomOut: () => Promise<void>;
  resetView: () => Promise<void>;
  
  // Object and tile management
  loadVisibleObjects: () => Promise<void>;
  loadTiles: (tiles: TileCoordinate[]) => Promise<void>;
  preloadArea: (center: { x: number; y: number }, radius: number) => Promise<void>;
  
  // Performance management
  initializePerformance: (capabilities: DeviceCapabilities) => Promise<void>;
  updatePerformanceStats: (fps: number) => void;
  refreshCacheStats: () => Promise<void>;
  
  // User behavior tracking
  trackUserBehavior: (behavior: UserBehavior) => void;
  togglePredictive: () => void;
  
  // Utility
  getScaleLevelForScale: (scale: number) => ScaleLevel;
  getTileKey: (tile: TileCoordinate) => string;
  getBoundsFromViewport: () => BoundingBox;
  toggleDebugMode: () => void;
  
  // Initialization
  initialize: () => Promise<void>;
}

export const useFractalStore = create<FractalStore>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    viewport: {
      center: { x: 0, y: 0 },
      scale: 1.0,
      rotation: 0,
      bounds: { minX: -1000, minY: -1000, maxX: 1000, maxY: 1000 },
      scaleLevel: 3,
    },
    isLoading: false,
    
    visibleObjects: [],
    loadedTiles: new Map(),
    tileLoadQueue: [],
    
    performanceBudget: null,
    deviceCapabilities: null,
    currentFps: 60,
    cacheStats: null,
    
    userBehaviorHistory: [],
    predictiveEnabled: true,
    
    scaleLevels: SCALE_LEVELS,
    currentScaleLevel: SCALE_LEVELS[2], // Floor level
    
    debugMode: false,
    
    // Actions
    setViewport: (newViewport) => {
      set((state) => {
        const viewport = { ...state.viewport, ...newViewport };
        const scaleLevel = get().getScaleLevelForScale(viewport.scale);
        
        return {
          viewport: { ...viewport, scaleLevel: scaleLevel.id },
          currentScaleLevel: scaleLevel,
        };
      });
    },
    
    zoomTo: async (scale, center, duration = 300) => {
      const state = get();
      
      // Track user behavior
      const behavior: UserBehavior = {
        timestamp: new Date(),
        action: 'zoom',
        viewport: state.viewport,
        target: center,
        duration,
      };
      get().trackUserBehavior(behavior);
      
      // Update viewport
      const newCenter = center || state.viewport.center;
      get().setViewport({ scale, center: newCenter });
      
      // Load objects for new viewport
      await get().loadVisibleObjects();
      
      // Trigger API call if needed
      try {
        await ScaleEngineAPI.zoomTo({ scale, center: newCenter, duration });
      } catch (error) {
        console.error('Failed to sync zoom with API:', error);
      }
    },
    
    panTo: async (center, duration = 300) => {
      const state = get();
      
      // Track user behavior
      const behavior: UserBehavior = {
        timestamp: new Date(),
        action: 'pan',
        viewport: state.viewport,
        target: center,
        duration,
      };
      get().trackUserBehavior(behavior);
      
      // Update viewport
      get().setViewport({ center });
      
      // Load objects for new viewport
      await get().loadVisibleObjects();
      
      // Trigger API call if needed
      try {
        await ScaleEngineAPI.panTo({ center, duration });
      } catch (error) {
        console.error('Failed to sync pan with API:', error);
      }
    },
    
    zoomIn: async () => {
      const { viewport } = get();
      const newScale = Math.min(viewport.scale * 2, 100000);
      await get().zoomTo(newScale);
    },
    
    zoomOut: async () => {
      const { viewport } = get();
      const newScale = Math.max(viewport.scale / 2, 0.01);
      await get().zoomTo(newScale);
    },
    
    resetView: async () => {
      await get().zoomTo(1.0, { x: 0, y: 0 });
    },
    
    // Object and tile management
    loadVisibleObjects: async () => {
      set({ isLoading: true });
      
      try {
        const bounds = get().getBoundsFromViewport();
        const { viewport } = get();
        
        const objects = await ScaleEngineAPI.getVisibleObjects(
          bounds,
          viewport.scale,
          viewport.scaleLevel
        );
        
        set({ visibleObjects: objects });
      } catch (error) {
        console.error('Failed to load visible objects:', error);
      } finally {
        set({ isLoading: false });
      }
    },
    
    loadTiles: async (tiles) => {
      const { viewport, loadedTiles } = get();
      
      // Filter out already loaded tiles
      const tilesToLoad = tiles.filter(tile => {
        const key = get().getTileKey(tile);
        return !loadedTiles.has(key);
      });
      
      if (tilesToLoad.length === 0) return;
      
      try {
        const tileRequests = tilesToLoad.map(tile => ({
          coordinate: tile,
          scale: viewport.scale,
          priority: 'normal' as const,
        }));
        
        const response = await ScaleEngineAPI.loadTiles(tileRequests);
        
        // Update loaded tiles (simplified - would need actual tile data)
        set((state) => {
          const newLoadedTiles = new Map(state.loadedTiles);
          
          response.tiles.forEach((tileInfo, index) => {
            const tile = tilesToLoad[index];
            const key = get().getTileKey(tile);
            
            // Create simplified tile data
            const tileData: TileData = {
              coordinate: tile,
              bounds: CoordinateUtils.getTileBounds(tile),
              objects: [], // Would be populated from API response
              metadata: {
                objectCount: tileInfo.objectCount,
                dataSize: tileInfo.dataSize,
                compressed: tileInfo.compressed,
                cacheTime: new Date(),
                loadTime: 0,
              },
            };
            
            newLoadedTiles.set(key, tileData);
          });
          
          return { loadedTiles: newLoadedTiles };
        });
      } catch (error) {
        console.error('Failed to load tiles:', error);
      }
    },
    
    preloadArea: async (center, radius) => {
      try {
        const { viewport } = get();
        await ScaleEngineAPI.preloadArea({
          center,
          radius,
          scale: viewport.scale,
          priority: 'normal',
        });
      } catch (error) {
        console.error('Failed to preload area:', error);
      }
    },
    
    // Performance management
    initializePerformance: async (capabilities) => {
      try {
        const response = await ScaleEngineAPI.initializePerformanceBudget(capabilities);
        set({
          deviceCapabilities: capabilities,
          performanceBudget: response.budget,
        });
      } catch (error) {
        console.error('Failed to initialize performance budget:', error);
      }
    },
    
    updatePerformanceStats: (fps) => {
      set({ currentFps: fps });
    },
    
    refreshCacheStats: async () => {
      try {
        const stats = await ScaleEngineAPI.getCacheStats();
        set({ cacheStats: stats });
      } catch (error) {
        console.error('Failed to refresh cache stats:', error);
      }
    },
    
    // User behavior tracking
    trackUserBehavior: (behavior) => {
      set((state) => {
        const newHistory = [...state.userBehaviorHistory, behavior];
        // Keep only last 100 behaviors
        const trimmedHistory = newHistory.slice(-100);
        return { userBehaviorHistory: trimmedHistory };
      });
    },
    
    togglePredictive: () => {
      set((state) => ({ predictiveEnabled: !state.predictiveEnabled }));
    },
    
    // Utility functions
    getScaleLevelForScale: (scale) => {
      const { scaleLevels } = get();
      return scaleLevels.find(level => 
        scale >= level.minScale && scale < level.maxScale
      ) || scaleLevels[scaleLevels.length - 1];
    },
    
    getTileKey: (tile) => `${tile.z}-${tile.x}-${tile.y}`,
    
    getBoundsFromViewport: () => {
      const { viewport } = get();
      const halfWidth = 1000 / viewport.scale;
      const halfHeight = 1000 / viewport.scale;
      
      return {
        minX: viewport.center.x - halfWidth,
        minY: viewport.center.y - halfHeight,
        maxX: viewport.center.x + halfWidth,
        maxY: viewport.center.y + halfHeight,
      };
    },
    
    toggleDebugMode: () => {
      set((state) => ({ debugMode: !state.debugMode }));
    },
    
    // Initialization
    initialize: async () => {
      // Detect device capabilities
      const capabilities: DeviceCapabilities = {
        memory: (navigator as any).deviceMemory || 4,
        cores: navigator.hardwareConcurrency || 4,
        gpu: 'medium',
        connection: (navigator as any).connection?.effectiveType === '4g' ? 'fast' : 'wifi',
        screenSize: { width: window.innerWidth, height: window.innerHeight },
        pixelRatio: window.devicePixelRatio || 1,
      };
      
      // Initialize performance budget
      await get().initializePerformance(capabilities);
      
      // Load initial objects
      await get().loadVisibleObjects();
      
      // Initial cache stats
      await get().refreshCacheStats();
    },
  }))
);

// Subscribe to viewport changes to load tiles
useFractalStore.subscribe(
  (state) => state.viewport,
  (viewport, previousViewport) => {
    // Calculate tiles needed for current viewport
    const bounds = useFractalStore.getState().getBoundsFromViewport();
    const zoom = Math.round(CoordinateUtils.scaleToZoom(viewport.scale));
    const tiles = CoordinateUtils.getTilesInViewport(bounds, Math.max(0, zoom));
    
    // Load tiles (debounced in practice)
    setTimeout(() => {
      useFractalStore.getState().loadTiles(tiles);
    }, 100);
  }
);