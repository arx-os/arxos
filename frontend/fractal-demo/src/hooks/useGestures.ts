import { useGesture } from '@use-gesture/react';
import { useFractalStore } from '@/store/fractal-store';
import { UserBehavior } from '@/types/fractal';

interface UseGesturesOptions {
  onZoom?: (scale: number, center?: { x: number; y: number }) => void;
  onPan?: (center: { x: number; y: number }) => void;
  enablePredictive?: boolean;
  bounds?: {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
  };
  scaleRange?: {
    min: number;
    max: number;
  };
}

export const useGestures = (options: UseGesturesOptions = {}) => {
  const {
    onZoom,
    onPan,
    enablePredictive = true,
    bounds,
    scaleRange = { min: 0.01, max: 100000 },
  } = options;
  
  const {
    viewport,
    setViewport,
    trackUserBehavior,
    preloadArea,
    predictiveEnabled,
  } = useFractalStore();
  
  const bind = useGesture(
    {
      // Wheel zoom
      onWheel: ({ event, delta: [, deltaY], pinching, cancel }) => {
        if (pinching) return cancel();
        
        event.preventDefault();
        
        const rect = (event.target as HTMLElement).getBoundingClientRect();
        const x = event.clientX - rect.left - rect.width / 2;
        const y = event.clientY - rect.top - rect.height / 2;
        
        // Convert screen coordinates to world coordinates
        const worldX = viewport.center.x + x / viewport.scale;
        const worldY = viewport.center.y + y / viewport.scale;
        
        // Calculate new scale
        const scaleFactor = deltaY > 0 ? 0.9 : 1.1;
        const newScale = Math.max(
          scaleRange.min,
          Math.min(scaleRange.max, viewport.scale * scaleFactor)
        );
        
        // Update viewport to zoom into the mouse position
        const scaleChange = newScale / viewport.scale;
        const newCenter = {
          x: worldX - (worldX - viewport.center.x) / scaleChange,
          y: worldY - (worldY - viewport.center.y) / scaleChange,
        };
        
        // Apply bounds if specified
        const boundedCenter = bounds ? {
          x: Math.max(bounds.minX, Math.min(bounds.maxX, newCenter.x)),
          y: Math.max(bounds.minY, Math.min(bounds.maxY, newCenter.y)),
        } : newCenter;
        
        setViewport({ scale: newScale, center: boundedCenter });
        
        // Track user behavior
        const behavior: UserBehavior = {
          timestamp: new Date(),
          action: 'zoom',
          viewport: { ...viewport, scale: newScale, center: boundedCenter },
          target: { x: worldX, y: worldY },
        };
        trackUserBehavior(behavior);
        
        // Predictive preloading
        if (enablePredictive && predictiveEnabled) {
          const preloadRadius = 1000 / newScale; // Adjust based on scale
          preloadArea(boundedCenter, preloadRadius);
        }
        
        // Call external handler
        onZoom?.(newScale, boundedCenter);
      },
      
      // Touch pinch zoom
      onPinch: ({ 
        origin: [ox, oy], 
        first, 
        movement: [ms], 
        offset: [scale], 
        memo 
      }) => {
        if (first) {
          // Store initial state
          const rect = (document.querySelector('[data-gesture-target]') as HTMLElement)?.getBoundingClientRect();
          if (!rect) return memo;
          
          const centerX = ox - rect.left - rect.width / 2;
          const centerY = oy - rect.top - rect.height / 2;
          
          memo = {
            initialScale: viewport.scale,
            initialCenter: { ...viewport.center },
            gestureCenter: {
              x: viewport.center.x + centerX / viewport.scale,
              y: viewport.center.y + centerY / viewport.scale,
            },
          };
        }
        
        if (!memo) return memo;
        
        // Calculate new scale
        const newScale = Math.max(
          scaleRange.min,
          Math.min(scaleRange.max, memo.initialScale * scale)
        );
        
        // Update center to zoom into pinch point
        const scaleChange = newScale / memo.initialScale;
        const newCenter = {
          x: memo.gestureCenter.x - (memo.gestureCenter.x - memo.initialCenter.x) / scaleChange,
          y: memo.gestureCenter.y - (memo.gestureCenter.y - memo.initialCenter.y) / scaleChange,
        };
        
        // Apply bounds if specified
        const boundedCenter = bounds ? {
          x: Math.max(bounds.minX, Math.min(bounds.maxX, newCenter.x)),
          y: Math.max(bounds.minY, Math.min(bounds.maxY, newCenter.y)),
        } : newCenter;
        
        setViewport({ scale: newScale, center: boundedCenter });
        
        // Track behavior on pinch end
        if (scale === 1) { // Gesture ended
          const behavior: UserBehavior = {
            timestamp: new Date(),
            action: 'zoom',
            viewport: { ...viewport, scale: newScale, center: boundedCenter },
            target: memo.gestureCenter,
          };
          trackUserBehavior(behavior);
        }
        
        onZoom?.(newScale, boundedCenter);
        
        return memo;
      },
      
      // Drag pan
      onDrag: ({ 
        movement: [mx, my], 
        delta: [dx, dy], 
        first, 
        last, 
        velocity: [vx, vy],
        memo 
      }) => {
        if (first) {
          memo = {
            initialCenter: { ...viewport.center },
          };
        }
        
        if (!memo) return memo;
        
        // Calculate new center based on movement
        const newCenter = {
          x: memo.initialCenter.x - mx / viewport.scale,
          y: memo.initialCenter.y - my / viewport.scale,
        };
        
        // Apply bounds if specified
        const boundedCenter = bounds ? {
          x: Math.max(bounds.minX, Math.min(bounds.maxX, newCenter.x)),
          y: Math.max(bounds.minY, Math.min(bounds.maxY, newCenter.y)),
        } : newCenter;
        
        setViewport({ center: boundedCenter });
        
        // Track behavior on drag end
        if (last) {
          const behavior: UserBehavior = {
            timestamp: new Date(),
            action: 'pan',
            viewport: { ...viewport, center: boundedCenter },
            target: boundedCenter,
            duration: Date.now() - (memo.startTime || Date.now()),
          };
          trackUserBehavior(behavior);
          
          // Momentum-based predictive preloading
          if (enablePredictive && predictiveEnabled && (Math.abs(vx) > 0.5 || Math.abs(vy) > 0.5)) {
            const futureCenter = {
              x: boundedCenter.x - (vx * 100) / viewport.scale,
              y: boundedCenter.y - (vy * 100) / viewport.scale,
            };
            const preloadRadius = 1500 / viewport.scale;
            preloadArea(futureCenter, preloadRadius);
          }
        }
        
        onPan?.(boundedCenter);
        
        return memo;
      },
      
      // Double tap to zoom
      onDoubleClick: ({ event }) => {
        event.preventDefault();
        
        const rect = (event.target as HTMLElement).getBoundingClientRect();
        const x = event.clientX - rect.left - rect.width / 2;
        const y = event.clientY - rect.top - rect.height / 2;
        
        // Convert to world coordinates
        const worldX = viewport.center.x + x / viewport.scale;
        const worldY = viewport.center.y + y / viewport.scale;
        
        // Zoom in by 2x
        const newScale = Math.min(scaleRange.max, viewport.scale * 2);
        
        // Center on click point
        const newCenter = { x: worldX, y: worldY };
        const boundedCenter = bounds ? {
          x: Math.max(bounds.minX, Math.min(bounds.maxX, newCenter.x)),
          y: Math.max(bounds.minY, Math.min(bounds.maxY, newCenter.y)),
        } : newCenter;
        
        setViewport({ scale: newScale, center: boundedCenter });
        
        // Track behavior
        const behavior: UserBehavior = {
          timestamp: new Date(),
          action: 'zoom',
          viewport: { ...viewport, scale: newScale, center: boundedCenter },
          target: { x: worldX, y: worldY },
        };
        trackUserBehavior(behavior);
        
        onZoom?.(newScale, boundedCenter);
      },
    },
    {
      // Configuration
      drag: {
        filterTaps: true,
        threshold: 5,
      },
      pinch: {
        scaleBounds: { min: scaleRange.min, max: scaleRange.max },
        rubberband: 0.1,
      },
      wheel: {
        preventDefault: true,
      },
    }
  );
  
  return bind;
};