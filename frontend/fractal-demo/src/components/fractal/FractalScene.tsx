'use client';

import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Group, Vector3 } from 'three';
import { useFractalStore } from '@/store/fractal-store';
import { ViewportState, FractalArxObject } from '@/types/fractal';
import { FractalObject } from './FractalObject';
import { TileGrid } from './TileGrid';

interface FractalSceneProps {
  viewport: ViewportState;
  debugMode: boolean;
}

export const FractalScene: React.FC<FractalSceneProps> = ({
  viewport,
  debugMode,
}) => {
  const groupRef = useRef<Group>(null);
  const { visibleObjects, loadedTiles, currentScaleLevel } = useFractalStore();
  
  // Camera position based on viewport
  const cameraPosition = useMemo(() => {
    return new Vector3(viewport.center.x, viewport.center.y, 1000);
  }, [viewport.center.x, viewport.center.y]);
  
  // Filter objects based on current scale level
  const filteredObjects = useMemo(() => {
    return visibleObjects.filter(obj => {
      // Show objects at current scale level or one level above/below for smooth transitions
      const levelDiff = Math.abs(obj.scaleLevel - viewport.scaleLevel);
      return levelDiff <= 1;
    });
  }, [visibleObjects, viewport.scaleLevel]);
  
  // Group objects by scale level for different rendering strategies
  const objectsByLevel = useMemo(() => {
    const grouped: { [level: number]: FractalArxObject[] } = {};
    
    filteredObjects.forEach(obj => {
      if (!grouped[obj.scaleLevel]) {
        grouped[obj.scaleLevel] = [];
      }
      grouped[obj.scaleLevel].push(obj);
    });
    
    return grouped;
  }, [filteredObjects]);
  
  // Update group position and scale on frame
  useFrame(({ camera }) => {
    if (groupRef.current) {
      // Smooth camera movement
      camera.position.lerp(cameraPosition, 0.1);
      camera.updateProjectionMatrix();
    }
  });
  
  // Generate procedural objects for demonstration when no API data
  const proceduralObjects = useMemo(() => {
    if (visibleObjects.length > 0) return [];
    
    const objects: FractalArxObject[] = [];
    const bounds = {
      minX: viewport.center.x - 1000 / viewport.scale,
      minY: viewport.center.y - 1000 / viewport.scale,
      maxX: viewport.center.x + 1000 / viewport.scale,
      maxY: viewport.center.y + 1000 / viewport.scale,
    };
    
    // Generate objects based on scale level
    let gridSize: number;
    let objectType: string;
    let count: number;
    
    if (viewport.scale < 0.1) {
      // Campus level - buildings
      gridSize = 100;
      objectType = 'building';
      count = 20;
    } else if (viewport.scale < 1) {
      // Building level - floors
      gridSize = 20;
      objectType = 'floor';
      count = 50;
    } else if (viewport.scale < 10) {
      // Floor level - rooms
      gridSize = 5;
      objectType = 'room';
      count = 100;
    } else if (viewport.scale < 100) {
      // Room level - fixtures
      gridSize = 1;
      objectType = 'fixture';
      count = 200;
    } else if (viewport.scale < 1000) {
      // Fixture level - components
      gridSize = 0.2;
      objectType = 'component';
      count = 300;
    } else {
      // Component level - schematics
      gridSize = 0.05;
      objectType = 'schematic';
      count = 500;
    }
    
    for (let i = 0; i < count; i++) {
      const x = bounds.minX + (Math.random() * (bounds.maxX - bounds.minX));
      const y = bounds.minY + (Math.random() * (bounds.maxY - bounds.minY));
      
      objects.push({
        id: `procedural-${viewport.scaleLevel}-${i}`,
        name: `${objectType}-${i}`,
        type: objectType,
        scaleLevel: viewport.scaleLevel,
        position: { x, y, z: 0 },
        bounds: {
          minX: x - gridSize / 2,
          minY: y - gridSize / 2,
          maxX: x + gridSize / 2,
          maxY: y + gridSize / 2,
        },
        children: [],
        lastModified: new Date(),
        contributors: ['demo-user'],
        biltReward: Math.floor(Math.random() * 100),
        visibility: {
          minScale: currentScaleLevel.minScale,
          maxScale: currentScaleLevel.maxScale,
          priority: 'normal',
          lodStrategy: 'progressive',
        },
        detailLevels: [
          {
            level: 1,
            name: 'Basic',
            minScale: currentScaleLevel.minScale,
            loadStatus: 'loaded',
          },
        ],
      });
    }
    
    return objects;
  }, [visibleObjects.length, viewport.center, viewport.scale, viewport.scaleLevel, currentScaleLevel]);
  
  const allObjects = visibleObjects.length > 0 ? filteredObjects : proceduralObjects;
  
  return (
    <group ref={groupRef}>
      {/* Tile Grid (for debugging) */}
      {debugMode && (
        <TileGrid 
          viewport={viewport}
          loadedTiles={loadedTiles}
        />
      )}
      
      {/* Fractal Objects */}
      {Object.entries(objectsByLevel).map(([level, objects]) => (
        <group key={`level-${level}`}>
          {objects.map(obj => (
            <FractalObject
              key={obj.id}
              object={obj}
              viewport={viewport}
              debugMode={debugMode}
            />
          ))}
        </group>
      ))}
      
      {/* Procedural Objects (when no API data) */}
      {visibleObjects.length === 0 && (
        <group>
          {proceduralObjects.map(obj => (
            <FractalObject
              key={obj.id}
              object={obj}
              viewport={viewport}
              debugMode={debugMode}
            />
          ))}
        </group>
      )}
      
      {/* Grid lines for reference */}
      {debugMode && (
        <group>
          {/* X-axis lines */}
          {Array.from({ length: 20 }, (_, i) => {
            const y = (i - 10) * 100;
            return (
              <line key={`x-${i}`}>
                <bufferGeometry>
                  <bufferAttribute
                    attach="attributes-position"
                    count={2}
                    array={new Float32Array([-1000, y, 0, 1000, y, 0])}
                    itemSize={3}
                  />
                </bufferGeometry>
                <lineBasicMaterial color="#333333" />
              </line>
            );
          })}
          
          {/* Y-axis lines */}
          {Array.from({ length: 20 }, (_, i) => {
            const x = (i - 10) * 100;
            return (
              <line key={`y-${i}`}>
                <bufferGeometry>
                  <bufferAttribute
                    attach="attributes-position"
                    count={2}
                    array={new Float32Array([x, -1000, 0, x, 1000, 0])}
                    itemSize={3}
                  />
                </bufferGeometry>
                <lineBasicMaterial color="#333333" />
              </line>
            );
          })}
        </group>
      )}
    </group>
  );
};