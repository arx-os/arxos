'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrthographicCamera } from '@react-three/drei';
import { motion } from 'framer-motion';
import { useFractalStore } from '@/store/fractal-store';
import { useGestures } from '@/hooks/useGestures';
import { usePerformanceMonitor } from '@/hooks/usePerformanceMonitor';
import { ZoomControls } from '@/components/ui/ZoomControls';
import { PerformanceIndicator } from '@/components/ui/PerformanceIndicator';
import { FractalViewerProps } from '@/types/fractal';
import { FractalScene } from './FractalScene';

export const FractalViewer: React.FC<FractalViewerProps> = ({
  initialCenter = { x: 0, y: 0 },
  initialScale = 1.0,
  enablePredictive = true,
  debugMode = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  
  const {
    viewport,
    isLoading,
    performanceBudget,
    currentFps,
    loadedTiles,
    initialize,
    zoomIn,
    zoomOut,
    resetView,
    setViewport,
    toggleDebugMode,
  } = useFractalStore();
  
  const { getCurrentStats, getAverageFPS, memoryUsage } = usePerformanceMonitor(true);
  
  // Initialize the fractal store
  useEffect(() => {
    const init = async () => {
      setViewport({ center: initialCenter, scale: initialScale });
      await initialize();
      setIsInitialized(true);
    };
    
    init();
  }, [initialize, initialCenter, initialScale, setViewport]);
  
  // Gesture handling
  const bind = useGestures({
    enablePredictive,
    scaleRange: { min: 0.01, max: 100000 },
  });
  
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.target !== document.body) return;
      
      switch (event.key) {
        case '+':
        case '=':
          event.preventDefault();
          zoomIn();
          break;
        case '-':
        case '_':
          event.preventDefault();
          zoomOut();
          break;
        case '0':
        case 'Home':
          event.preventDefault();
          resetView();
          break;
        case 'd':
        case 'D':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            toggleDebugMode();
          }
          break;
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [zoomIn, zoomOut, resetView, toggleDebugMode]);
  
  // Handle loading state
  if (!isInitialized) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-arxos-dark">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="w-16 h-16 border-4 border-arxos-blue border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <div className="text-xl text-white mb-2">Initializing Fractal Engine</div>
          <div className="text-sm text-gray-400">
            Loading performance budget and initial objects...
          </div>
        </motion.div>
      </div>
    );
  }
  
  return (
    <div 
      ref={containerRef}
      className="w-full h-screen bg-arxos-dark relative overflow-hidden"
      data-gesture-target
      {...bind()}
    >
      {/* Loading Overlay */}
      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50 bg-arxos-gray/90 backdrop-blur-sm rounded-lg px-4 py-2 border border-gray-600"
        >
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-arxos-blue border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-white">Loading objects...</span>
          </div>
        </motion.div>
      )}
      
      {/* Main 3D Canvas */}
      <Canvas
        style={{ 
          width: '100%', 
          height: '100%',
          cursor: isLoading ? 'wait' : 'grab',
        }}
        gl={{
          antialias: performanceBudget?.qualitySettings.enableShadows !== false,
          alpha: false,
          powerPreference: 'high-performance',
        }}
        onCreated={({ gl, camera }) => {
          // WebGL optimizations
          gl.outputColorSpace = 'srgb';
          gl.toneMapping = 5; // ACESFilmicToneMapping
          gl.toneMappingExposure = 1.2;
          
          // Performance optimizations
          gl.setPixelRatio(Math.min(window.devicePixelRatio, 2));
          
          // Set initial camera position
          camera.position.set(0, 0, 1000);
        }}
      >
        {/* Orthographic camera for 2D-like fractal viewing */}
        <OrthographicCamera
          makeDefault
          left={-window.innerWidth / 2}
          right={window.innerWidth / 2}
          top={window.innerHeight / 2}
          bottom={-window.innerHeight / 2}
          near={0.1}
          far={2000}
          position={[viewport.center.x, viewport.center.y, 1000]}
          zoom={viewport.scale * 100}
        />
        
        {/* Lighting */}
        <ambientLight intensity={0.6} />
        <pointLight position={[100, 100, 100]} intensity={0.8} />
        
        {/* Main fractal scene */}
        <FractalScene 
          viewport={viewport}
          debugMode={debugMode}
        />
      </Canvas>
      
      {/* UI Controls */}
      <ZoomControls
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onReset={resetView}
        currentScale={viewport.scale}
        minScale={0.01}
        maxScale={100000}
      />
      
      {/* Performance Indicator */}
      {performanceBudget && (
        <PerformanceIndicator
          fps={currentFps}
          loadedTiles={loadedTiles.size}
          memoryUsage={memoryUsage}
          budget={performanceBudget}
        />
      )}
      
      {/* Scale Level Indicator */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="fixed top-4 left-4 z-50 bg-arxos-gray/90 backdrop-blur-sm rounded-lg p-3 border border-gray-600"
      >
        <div className="text-sm font-semibold text-white mb-1">
          Scale Level {viewport.scaleLevel}
        </div>
        <div className="text-xs text-gray-300">
          {viewport.scale < 0.1 ? '🏫 Campus View' :
           viewport.scale < 1 ? '🏢 Building View' :
           viewport.scale < 10 ? '🏠 Floor View' :
           viewport.scale < 100 ? '🚪 Room View' :
           viewport.scale < 1000 ? '💡 Fixture View' :
           viewport.scale < 10000 ? '🔧 Component View' : '📐 Schematic View'}
        </div>
        <div className="text-xs text-gray-400 font-mono mt-1">
          Scale: {viewport.scale.toFixed(3)}x
        </div>
        <div className="text-xs text-gray-400 font-mono">
          Center: ({viewport.center.x.toFixed(1)}, {viewport.center.y.toFixed(1)})
        </div>
      </motion.div>
      
      {/* Debug Info */}
      {debugMode && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-4 left-4 z-50 bg-arxos-gray/90 backdrop-blur-sm rounded-lg p-3 border border-gray-600 font-mono text-xs max-w-xs"
        >
          <div className="text-yellow-400 font-semibold mb-2">Debug Info</div>
          <div className="space-y-1 text-gray-300">
            <div>Viewport: {viewport.center.x.toFixed(1)}, {viewport.center.y.toFixed(1)}</div>
            <div>Scale: {viewport.scale.toFixed(4)}x</div>
            <div>Level: {viewport.scaleLevel}</div>
            <div>Loaded Tiles: {loadedTiles.size}</div>
            <div>FPS: {Math.round(currentFps)}</div>
            <div>Avg FPS: {Math.round(getAverageFPS())}</div>
            <div>Memory: {memoryUsage.toFixed(1)} MB</div>
            <div>Objects: {useFractalStore.getState().visibleObjects.length}</div>
            <div>Predictive: {useFractalStore.getState().predictiveEnabled ? 'ON' : 'OFF'}</div>
          </div>
          <div className="mt-2 pt-2 border-t border-gray-600">
            <div className="text-gray-400 text-xs">
              Ctrl+D: Toggle Debug | +/-: Zoom | 0: Reset
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};