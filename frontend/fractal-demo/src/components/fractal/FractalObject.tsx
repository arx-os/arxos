'use client';

import React, { useMemo, useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Mesh, Color, Vector3 } from 'three';
import { Html } from '@react-three/drei';
import { FractalArxObject, ViewportState } from '@/types/fractal';
import { useFractalStore } from '@/store/fractal-store';
import { motion } from 'framer-motion';

interface FractalObjectProps {
  object: FractalArxObject;
  viewport: ViewportState;
  debugMode?: boolean;
}

export const FractalObject: React.FC<FractalObjectProps> = ({
  object,
  viewport,
  debugMode = false,
}) => {
  const meshRef = useRef<Mesh>(null);
  const [hovered, setHovered] = useState(false);
  const [clicked, setClicked] = useState(false);
  
  const { zoomTo, trackUserBehavior } = useFractalStore();
  
  // Calculate object dimensions
  const dimensions = useMemo(() => {
    const width = object.bounds.maxX - object.bounds.minX;
    const height = object.bounds.maxY - object.bounds.minY;
    return { width, height };
  }, [object.bounds]);
  
  // Calculate opacity based on scale and distance from viewport center
  const opacity = useMemo(() => {
    const distance = Math.sqrt(
      Math.pow(object.position.x - viewport.center.x, 2) +
      Math.pow(object.position.y - viewport.center.y, 2)
    );
    
    const maxDistance = 1000 / viewport.scale;
    const distanceFactor = Math.max(0, 1 - (distance / maxDistance));
    
    // Scale-based opacity
    const scaleDiff = Math.abs(viewport.scaleLevel - object.scaleLevel);
    const scaleFactor = scaleDiff === 0 ? 1 : scaleDiff === 1 ? 0.5 : 0.1;
    
    return Math.min(1, distanceFactor * scaleFactor * (hovered ? 1.5 : 1));
  }, [object.position, viewport.center, viewport.scale, viewport.scaleLevel, object.scaleLevel, hovered]);
  
  // Color based on object type and scale level
  const color = useMemo(() => {
    const colors = {
      building: '#4ade80',    // Green
      floor: '#60a5fa',      // Blue
      room: '#fbbf24',       // Yellow
      fixture: '#f472b6',    // Pink
      component: '#a78bfa',  // Purple
      schematic: '#fb7185',  // Rose
    };
    
    const baseColor = colors[object.type as keyof typeof colors] || '#6b7280';
    const color = new Color(baseColor);
    
    // Adjust brightness based on BILT reward
    const brightness = 0.5 + (object.biltReward / 200); // Scale 0.5-1.0
    color.multiplyScalar(brightness);
    
    return color;
  }, [object.type, object.biltReward]);
  
  // Handle click - zoom into object
  const handleClick = (event: any) => {
    event.stopPropagation();
    
    // Calculate zoom level to fit object
    const padding = 1.5;
    const scaleX = (window.innerWidth / dimensions.width) / padding;
    const scaleY = (window.innerHeight / dimensions.height) / padding;
    const targetScale = Math.min(scaleX, scaleY, viewport.scale * 4);
    
    // Center on object
    const center = {
      x: object.position.x,
      y: object.position.y,
    };
    
    // Track user behavior
    trackUserBehavior({
      timestamp: new Date(),
      action: 'click',
      viewport,
      target: { x: center.x, y: center.y, objectId: object.id },
    });
    
    // Zoom to object
    zoomTo(targetScale, center, 500);
    
    setClicked(true);
    setTimeout(() => setClicked(false), 200);
  };
  
  // Animation frame updates
  useFrame(() => {
    if (meshRef.current) {
      // Subtle floating animation based on object ID (for variety)
      const time = Date.now() * 0.001;
      const offset = parseInt(object.id.slice(-2)) || 0;
      const floatY = Math.sin(time + offset) * 0.1;
      
      meshRef.current.position.y = object.position.y + floatY;
      
      // Scale animation when clicked
      if (clicked) {
        meshRef.current.scale.setScalar(1.2);
      } else if (hovered) {
        meshRef.current.scale.setScalar(1.1);
      } else {
        meshRef.current.scale.setScalar(1.0);
      }
    }
  });
  
  // Don't render if too transparent or too far
  if (opacity < 0.01) return null;
  
  return (
    <group>
      {/* Main object mesh */}
      <mesh
        ref={meshRef}
        position={[object.position.x, object.position.y, object.position.z]}
        onClick={handleClick}
        onPointerEnter={() => setHovered(true)}
        onPointerLeave={() => setHovered(false)}
      >
        {/* Geometry based on object type */}
        {object.type === 'building' && (
          <boxGeometry args={[dimensions.width, dimensions.height, dimensions.width * 0.5]} />
        )}
        {object.type === 'floor' && (
          <planeGeometry args={[dimensions.width, dimensions.height]} />
        )}
        {object.type === 'room' && (
          <ringGeometry args={[0, Math.max(dimensions.width, dimensions.height) / 2, 8]} />
        )}
        {object.type === 'fixture' && (
          <circleGeometry args={[Math.max(dimensions.width, dimensions.height) / 2, 6]} />
        )}
        {object.type === 'component' && (
          <cylinderGeometry args={[dimensions.width / 2, dimensions.width / 2, dimensions.height, 6]} />
        )}
        {object.type === 'schematic' && (
          <octahedronGeometry args={[Math.max(dimensions.width, dimensions.height) / 2]} />
        )}
        
        {/* Material */}
        <meshPhongMaterial
          color={color}
          transparent
          opacity={opacity}
          emissive={hovered ? color.clone().multiplyScalar(0.2) : new Color(0x000000)}
          wireframe={debugMode}
        />
      </mesh>
      
      {/* Object label (when zoomed in enough) */}
      {viewport.scale > 10 && opacity > 0.5 && (
        <Html
          position={[object.position.x, object.position.y + dimensions.height / 2 + 5, 0]}
          center
        >
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: opacity, y: 0 }}
            className="bg-black/80 text-white text-xs px-2 py-1 rounded pointer-events-none whitespace-nowrap"
          >
            <div className="font-medium">{object.name}</div>
            {debugMode && (
              <div className="text-gray-400 text-xs">
                ID: {object.id.slice(0, 8)}...
              </div>
            )}
            {object.biltReward > 0 && (
              <div className="text-yellow-400 text-xs">
                🪙 {object.biltReward} BILT
              </div>
            )}
          </motion.div>
        </Html>
      )}
      
      {/* Bounding box visualization (debug mode) */}
      {debugMode && (
        <lineSegments
          position={[
            (object.bounds.minX + object.bounds.maxX) / 2,
            (object.bounds.minY + object.bounds.maxY) / 2,
            object.position.z
          ]}
        >
          <edgesGeometry>
            <boxGeometry args={[dimensions.width, dimensions.height, 1]} />
          </edgesGeometry>
          <lineBasicMaterial color="#ffffff" opacity={0.3} transparent />
        </lineSegments>
      )}
      
      {/* Contributors indicator */}
      {object.contributors.length > 1 && viewport.scale > 50 && (
        <Html
          position={[
            object.position.x + dimensions.width / 2,
            object.position.y + dimensions.height / 2,
            0
          ]}
          center
        >
          <div className="bg-blue-500/80 text-white text-xs px-1 py-0.5 rounded-full pointer-events-none">
            {object.contributors.length} 👥
          </div>
        </Html>
      )}
      
      {/* Detail level indicators */}
      {object.detailLevels.length > 1 && viewport.scale > 100 && (
        <Html
          position={[
            object.position.x - dimensions.width / 2,
            object.position.y + dimensions.height / 2,
            0
          ]}
          center
        >
          <div className="flex gap-1 pointer-events-none">
            {object.detailLevels.map((detail, index) => (
              <div
                key={index}
                className={`w-2 h-2 rounded-full ${
                  detail.loadStatus === 'loaded' ? 'bg-green-400' :
                  detail.loadStatus === 'loading' ? 'bg-yellow-400 animate-pulse' :
                  detail.loadStatus === 'error' ? 'bg-red-400' : 'bg-gray-400'
                }`}
                title={`${detail.name}: ${detail.loadStatus}`}
              />
            ))}
          </div>
        </Html>
      )}
    </group>
  );
};