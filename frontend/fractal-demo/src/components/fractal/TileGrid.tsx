'use client';

import React, { useMemo } from 'react';
import { ViewportState, TileData, TileCoordinate } from '@/types/fractal';
import { CoordinateUtils } from '@/lib/api';

interface TileGridProps {
  viewport: ViewportState;
  loadedTiles: Map<string, TileData>;
}

export const TileGrid: React.FC<TileGridProps> = ({
  viewport,
  loadedTiles,
}) => {
  // Calculate visible tiles
  const visibleTiles = useMemo(() => {
    const bounds = {
      minX: viewport.center.x - 1000 / viewport.scale,
      minY: viewport.center.y - 1000 / viewport.scale,
      maxX: viewport.center.x + 1000 / viewport.scale,
      maxY: viewport.center.y + 1000 / viewport.scale,
    };
    
    const zoom = Math.max(0, Math.round(CoordinateUtils.scaleToZoom(viewport.scale)));
    const tiles = CoordinateUtils.getTilesInViewport(bounds, zoom);
    
    return tiles.map(tile => {
      const tileBounds = CoordinateUtils.getTileBounds(tile);
      const key = `${tile.z}-${tile.x}-${tile.y}`;
      const tileData = loadedTiles.get(key);
      
      return {
        coordinate: tile,
        bounds: tileBounds,
        loaded: !!tileData,
        objectCount: tileData?.metadata.objectCount || 0,
        key,
      };
    });
  }, [viewport, loadedTiles]);
  
  return (
    <group>
      {visibleTiles.map(tile => {
        const width = tile.bounds.maxX - tile.bounds.minX;
        const height = tile.bounds.maxY - tile.bounds.minY;
        const centerX = (tile.bounds.minX + tile.bounds.maxX) / 2;
        const centerY = (tile.bounds.minY + tile.bounds.maxY) / 2;
        
        return (
          <group key={tile.key}>
            {/* Tile boundary */}
            <lineSegments
              position={[centerX, centerY, -1]}
            >
              <edgesGeometry>
                <planeGeometry args={[width, height]} />
              </edgesGeometry>
              <lineBasicMaterial 
                color={tile.loaded ? '#00ff00' : '#ff4444'} 
                opacity={tile.loaded ? 0.6 : 0.3}
                transparent 
              />
            </lineSegments>
            
            {/* Tile info (when zoomed in enough) */}
            {viewport.scale > 1 && (
              <mesh position={[centerX, centerY, -0.5]}>
                <planeGeometry args={[width * 0.8, height * 0.8]} />
                <meshBasicMaterial
                  color={tile.loaded ? '#004400' : '#440000'}
                  opacity={0.1}
                  transparent
                />
              </mesh>
            )}
          </group>
        );
      })}
      
      {/* Grid coordinates (when very zoomed in) */}
      {viewport.scale > 10 && visibleTiles.map(tile => {
        const centerX = (tile.bounds.minX + tile.bounds.maxX) / 2;
        const centerY = (tile.bounds.minY + tile.bounds.maxY) / 2;
        
        return (
          <mesh key={`label-${tile.key}`} position={[centerX, centerY, 0]}>
            <planeGeometry args={[0.1, 0.1]} />
            <meshBasicMaterial color={tile.loaded ? '#00ff00' : '#ff4444'} />
          </mesh>
        );
      })}
    </group>
  );
};