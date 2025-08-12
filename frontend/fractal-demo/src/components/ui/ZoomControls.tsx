'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ZoomControlsProps } from '@/types/fractal';

export const ZoomControls: React.FC<ZoomControlsProps> = ({
  onZoomIn,
  onZoomOut,
  onReset,
  currentScale,
  minScale,
  maxScale,
}) => {
  const scalePercentage = Math.round(currentScale * 100);
  const zoomLevel = Math.log2(currentScale / minScale) / Math.log2(maxScale / minScale);
  
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="fixed top-4 right-4 z-50 flex flex-col gap-2 bg-arxos-gray/90 backdrop-blur-sm rounded-lg p-3 border border-gray-600"
    >
      {/* Zoom In Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onZoomIn}
        disabled={currentScale >= maxScale}
        className="zoom-control disabled:opacity-50 disabled:cursor-not-allowed w-10 h-10 flex items-center justify-center text-xl font-bold"
        title={`Zoom in (${Math.round(currentScale * 2 * 100)}%)`}
      >
        +
      </motion.button>
      
      {/* Scale Indicator */}
      <div className="text-center text-xs text-gray-300 py-2 min-w-[80px]">
        <div className="font-mono font-bold">{scalePercentage}%</div>
        <div className="text-xs text-gray-400">
          {currentScale < 0.1 ? 'Campus' :
           currentScale < 1 ? 'Building' :
           currentScale < 10 ? 'Floor' :
           currentScale < 100 ? 'Room' :
           currentScale < 1000 ? 'Fixture' :
           currentScale < 10000 ? 'Component' : 'Schematic'}
        </div>
      </div>
      
      {/* Zoom Level Bar */}
      <div className="w-2 h-24 bg-gray-700 rounded-full mx-auto relative">
        <motion.div
          className="absolute bottom-0 w-full bg-arxos-blue rounded-full"
          style={{ height: `${zoomLevel * 100}%` }}
          transition={{ duration: 0.2 }}
        />
        <motion.div
          className="absolute w-3 h-3 bg-white rounded-full border-2 border-arxos-blue -left-0.5"
          style={{ bottom: `${Math.max(0, Math.min(100, zoomLevel * 100))}%` }}
          transition={{ duration: 0.2 }}
        />
      </div>
      
      {/* Zoom Out Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onZoomOut}
        disabled={currentScale <= minScale}
        className="zoom-control disabled:opacity-50 disabled:cursor-not-allowed w-10 h-10 flex items-center justify-center text-xl font-bold"
        title={`Zoom out (${Math.round(currentScale / 2 * 100)}%)`}
      >
        −
      </motion.button>
      
      {/* Reset Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onReset}
        className="zoom-control w-10 h-10 flex items-center justify-center text-xs"
        title="Reset view (100%)"
      >
        ⌂
      </motion.button>
    </motion.div>
  );
};