import { useEffect, useRef, useCallback } from 'react';
import { useFractalStore } from '@/store/fractal-store';

interface PerformanceStats {
  fps: number;
  frameTime: number;
  memoryUsage: number;
  domNodes: number;
  activeAnimations: number;
}

export const usePerformanceMonitor = (enabled: boolean = true) => {
  const frameCount = useRef(0);
  const lastTime = useRef(Date.now());
  const fpsHistory = useRef<number[]>([]);
  const animationFrame = useRef<number>();
  
  const { 
    updatePerformanceStats, 
    performanceBudget, 
    loadedTiles 
  } = useFractalStore();
  
  const getMemoryUsage = useCallback((): number => {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return memory.usedJSHeapSize / 1024 / 1024; // MB
    }
    // Fallback estimation based on DOM nodes and loaded tiles
    const domNodes = document.querySelectorAll('*').length;
    const estimatedMemory = (domNodes * 0.001) + (loadedTiles.size * 0.5);
    return estimatedMemory;
  }, [loadedTiles.size]);
  
  const measurePerformance = useCallback((): PerformanceStats => {
    const now = Date.now();
    const deltaTime = now - lastTime.current;
    
    if (deltaTime >= 1000) {
      // Calculate FPS
      const fps = (frameCount.current / deltaTime) * 1000;
      fpsHistory.current.push(fps);
      
      // Keep only last 60 samples (for 1 minute history at 1 FPS sampling)
      if (fpsHistory.current.length > 60) {
        fpsHistory.current.shift();
      }
      
      // Reset counters
      frameCount.current = 0;
      lastTime.current = now;
      
      // Update store
      updatePerformanceStats(fps);
      
      return {
        fps,
        frameTime: 1000 / fps,
        memoryUsage: getMemoryUsage(),
        domNodes: document.querySelectorAll('*').length,
        activeAnimations: document.getAnimations?.()?.length || 0,
      };
    }
    
    frameCount.current++;
    
    // Return current stats
    const currentFps = fpsHistory.current.length > 0 
      ? fpsHistory.current[fpsHistory.current.length - 1] 
      : 60;
    
    return {
      fps: currentFps,
      frameTime: 1000 / currentFps,
      memoryUsage: getMemoryUsage(),
      domNodes: document.querySelectorAll('*').length,
      activeAnimations: document.getAnimations?.()?.length || 0,
    };
  }, [updatePerformanceStats, getMemoryUsage]);
  
  const checkPerformanceBudget = useCallback((stats: PerformanceStats) => {
    if (!performanceBudget) return;
    
    const warnings: string[] = [];
    
    // Check FPS
    if (stats.fps < performanceBudget.targetFramerate - 10) {
      warnings.push(`Low FPS: ${Math.round(stats.fps)} (target: ${performanceBudget.targetFramerate})`);
    }
    
    // Check memory usage
    if (stats.memoryUsage > performanceBudget.maxMemoryUsage * 0.9) {
      warnings.push(`High memory usage: ${Math.round(stats.memoryUsage)}MB`);
    }
    
    // Check DOM nodes (performance indicator)
    if (stats.domNodes > 5000) {
      warnings.push(`High DOM node count: ${stats.domNodes}`);
    }
    
    // Check active animations
    if (stats.activeAnimations > 20) {
      warnings.push(`Many active animations: ${stats.activeAnimations}`);
    }
    
    // Log warnings in development
    if (process.env.NODE_ENV === 'development' && warnings.length > 0) {
      console.warn('Performance Budget Warnings:', warnings);
    }
    
    return warnings;
  }, [performanceBudget]);
  
  const tick = useCallback(() => {
    if (!enabled) return;
    
    const stats = measurePerformance();
    checkPerformanceBudget(stats);
    
    animationFrame.current = requestAnimationFrame(tick);
  }, [enabled, measurePerformance, checkPerformanceBudget]);
  
  useEffect(() => {
    if (!enabled) return;
    
    animationFrame.current = requestAnimationFrame(tick);
    
    return () => {
      if (animationFrame.current) {
        cancelAnimationFrame(animationFrame.current);
      }
    };
  }, [enabled, tick]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationFrame.current) {
        cancelAnimationFrame(animationFrame.current);
      }
    };
  }, []);
  
  const getAverageFPS = useCallback((): number => {
    if (fpsHistory.current.length === 0) return 60;
    
    const sum = fpsHistory.current.reduce((acc, fps) => acc + fps, 0);
    return sum / fpsHistory.current.length;
  }, []);
  
  const getPerformanceGrade = useCallback((): 'excellent' | 'good' | 'fair' | 'poor' => {
    const avgFPS = getAverageFPS();
    const targetFPS = performanceBudget?.targetFramerate || 60;
    
    if (avgFPS >= targetFPS - 2) return 'excellent';
    if (avgFPS >= targetFPS - 10) return 'good';
    if (avgFPS >= targetFPS - 20) return 'fair';
    return 'poor';
  }, [getAverageFPS, performanceBudget]);
  
  const getCurrentStats = useCallback((): PerformanceStats => {
    return measurePerformance();
  }, [measurePerformance]);
  
  return {
    getCurrentStats,
    getAverageFPS,
    getPerformanceGrade,
    fpsHistory: fpsHistory.current,
    memoryUsage: getMemoryUsage(),
  };
};