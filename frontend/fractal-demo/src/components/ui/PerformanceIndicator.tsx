'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { PerformanceIndicatorProps } from '@/types/fractal';

export const PerformanceIndicator: React.FC<PerformanceIndicatorProps> = ({
  fps,
  loadedTiles,
  memoryUsage,
  budget,
}) => {
  const getPerformanceStatus = () => {
    if (fps >= budget.targetFramerate - 5) return 'good';
    if (fps >= budget.targetFramerate - 15) return 'warning';
    return 'critical';
  };
  
  const getMemoryStatus = () => {
    const memoryPercent = (memoryUsage / budget.maxMemoryUsage) * 100;
    if (memoryPercent < 70) return 'good';
    if (memoryPercent < 85) return 'warning';
    return 'critical';
  };
  
  const performanceStatus = getPerformanceStatus();
  const memoryStatus = getMemoryStatus();
  const memoryPercent = Math.round((memoryUsage / budget.maxMemoryUsage) * 100);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="fixed bottom-4 right-4 z-50 bg-arxos-gray/90 backdrop-blur-sm rounded-lg p-3 border border-gray-600 min-w-[200px]"
    >
      <div className="text-xs font-semibold text-gray-300 mb-2">Performance</div>
      
      {/* FPS Indicator */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-400">FPS:</span>
        <div className="flex items-center gap-2">
          <span className={`performance-indicator performance-${performanceStatus}`}>
            {Math.round(fps)}
          </span>
          <div className="w-12 h-1 bg-gray-700 rounded-full overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${
                performanceStatus === 'good' ? 'bg-green-500' :
                performanceStatus === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(100, (fps / budget.targetFramerate) * 100)}%` }}
              transition={{ duration: 0.2 }}
            />
          </div>
        </div>
      </div>
      
      {/* Memory Usage */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-400">Memory:</span>
        <div className="flex items-center gap-2">
          <span className={`performance-indicator performance-${memoryStatus}`}>
            {memoryPercent}%
          </span>
          <div className="w-12 h-1 bg-gray-700 rounded-full overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${
                memoryStatus === 'good' ? 'bg-green-500' :
                memoryStatus === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${memoryPercent}%` }}
              transition={{ duration: 0.2 }}
            />
          </div>
        </div>
      </div>
      
      {/* Loaded Tiles */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-400">Tiles:</span>
        <span className="text-xs font-mono text-white">{loadedTiles}</span>
      </div>
      
      {/* Concurrent Limit */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400">Limit:</span>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-white">
            {loadedTiles}/{budget.maxConcurrentTiles}
          </span>
          <div className="w-12 h-1 bg-gray-700 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-arxos-blue rounded-full"
              style={{ width: `${(loadedTiles / budget.maxConcurrentTiles) * 100}%` }}
              transition={{ duration: 0.2 }}
            />
          </div>
        </div>
      </div>
      
      {/* Quality Settings Indicator */}
      <div className="mt-2 pt-2 border-t border-gray-600">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-400">Quality:</span>
          <div className="flex gap-1">
            {/* LOD Level */}
            <div className={`w-2 h-2 rounded-full ${
              budget.qualitySettings.maxLodLevel >= 5 ? 'bg-green-500' :
              budget.qualitySettings.maxLodLevel >= 3 ? 'bg-yellow-500' : 'bg-red-500'
            }`} title={`LOD Level: ${budget.qualitySettings.maxLodLevel}`} />
            
            {/* Shadows */}
            <div className={`w-2 h-2 rounded-full ${
              budget.qualitySettings.enableShadows ? 'bg-green-500' : 'bg-gray-600'
            }`} title={`Shadows: ${budget.qualitySettings.enableShadows ? 'On' : 'Off'}`} />
            
            {/* Reflections */}
            <div className={`w-2 h-2 rounded-full ${
              budget.qualitySettings.enableReflections ? 'bg-green-500' : 'bg-gray-600'
            }`} title={`Reflections: ${budget.qualitySettings.enableReflections ? 'On' : 'Off'}`} />
          </div>
        </div>
      </div>
    </motion.div>
  );
};