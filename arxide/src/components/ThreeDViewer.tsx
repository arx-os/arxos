import React, { useRef, useState, useEffect, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Grid, Box, Sphere, Cylinder, Text, Html } from '@react-three/drei';
import * as THREE from 'three';
import { Box as MuiBox, IconButton, Tooltip, Chip } from '@mui/material';
import {
  ViewInAr as View3DIcon,
  ViewModule as View2DIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  RotateLeft as RotateIcon,
  CenterFocusStrong as CenterIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';

interface ThreeDObject {
  id: string;
  type: 'box' | 'sphere' | 'cylinder' | 'line' | 'plane';
  position: [number, number, number];
  rotation: [number, number, number];
  scale: [number, number, number];
  color: string;
  material?: string;
  dimensions?: {
    width?: number;
    height?: number;
    depth?: number;
    radius?: number;
  };
  constraints?: any[];
  metadata?: any;
}

interface ThreeDViewerProps {
  objects: ThreeDObject[];
  selectedObject?: string;
  onObjectSelect?: (objectId: string) => void;
  onObjectUpdate?: (objectId: string, updates: Partial<ThreeDObject>) => void;
  viewMode: '2D' | '3D';
  onViewModeChange?: (mode: '2D' | '3D') => void;
  precision: number;
  gridSize: number;
}

// 3D Object Component
const ThreeDObject: React.FC<{
  object: ThreeDObject;
  isSelected: boolean;
  onSelect: () => void;
  precision: number;
}> = ({ object, isSelected, onSelect, precision }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  // Apply precision to position
  const precisePosition = useMemo(() => {
    return object.position.map(coord => 
      Math.round(coord / precision) * precision
    ) as [number, number, number];
  }, [object.position, precision]);

  // Handle object selection
  const handleClick = (event: any) => {
    event.stopPropagation();
    onSelect();
  };

  // Render different object types
  const renderObject = () => {
    const commonProps = {
      ref: meshRef,
      position: precisePosition,
      rotation: object.rotation,
      scale: object.scale,
      onClick: handleClick,
      onPointerOver: () => setHovered(true),
      onPointerOut: () => setHovered(false),
    };

    const materialProps = {
      color: object.color,
      transparent: true,
      opacity: hovered || isSelected ? 0.8 : 0.6,
      wireframe: isSelected,
    };

    switch (object.type) {
      case 'box':
        const { width = 1, height = 1, depth = 1 } = object.dimensions || {};
        return (
          <Box args={[width, height, depth]} {...commonProps}>
            <meshStandardMaterial {...materialProps} />
          </Box>
        );

      case 'sphere':
        const { radius = 0.5 } = object.dimensions || {};
        return (
          <Sphere args={[radius, 32, 32]} {...commonProps}>
            <meshStandardMaterial {...materialProps} />
          </Sphere>
        );

      case 'cylinder':
        const { radius: cylRadius = 0.5, height: cylHeight = 1 } = object.dimensions || {};
        return (
          <Cylinder args={[cylRadius, cylRadius, cylHeight, 32]} {...commonProps}>
            <meshStandardMaterial {...materialProps} />
          </Cylinder>
        );

      case 'line':
        const points = [
          new THREE.Vector3(0, 0, 0),
          new THREE.Vector3(object.dimensions?.width || 1, 0, 0)
        ];
        const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
        return (
          <line geometry={lineGeometry} {...commonProps}>
            <lineBasicMaterial color={object.color} linewidth={isSelected ? 3 : 1} />
          </line>
        );

      case 'plane':
        const { width: planeWidth = 1, height: planeHeight = 1 } = object.dimensions || {};
        return (
          <mesh {...commonProps}>
            <planeGeometry args={[planeWidth, planeHeight]} />
            <meshStandardMaterial {...materialProps} />
          </mesh>
        );

      default:
        return null;
    }
  };

  return (
    <group>
      {renderObject()}
      {isSelected && (
        <Html position={precisePosition}>
          <Chip
            label={object.id}
            size="small"
            color="primary"
            variant="outlined"
            sx={{ 
              backgroundColor: 'rgba(0,0,0,0.8)', 
              color: 'white',
              fontSize: '0.7rem'
            }}
          />
        </Html>
      )}
    </group>
  );
};

// Camera Controls Component
const CameraControls: React.FC<{
  onViewModeChange?: (mode: '2D' | '3D') => void;
  viewMode: '2D' | '3D';
}> = ({ onViewModeChange, viewMode }) => {
  const { camera } = useThree();

  // Set camera position based on view mode
  useEffect(() => {
    if (viewMode === '2D') {
      camera.position.set(0, 0, 10);
      camera.lookAt(0, 0, 0);
    } else {
      camera.position.set(5, 5, 5);
      camera.lookAt(0, 0, 0);
    }
  }, [viewMode, camera]);

  return (
    <OrbitControls
      enablePan={true}
      enableZoom={true}
      enableRotate={viewMode === '3D'}
      maxPolarAngle={viewMode === '2D' ? Math.PI / 2 : Math.PI}
      minPolarAngle={viewMode === '2D' ? Math.PI / 2 : 0}
    />
  );
};

// Scene Component
const Scene: React.FC<{
  objects: ThreeDObject[];
  selectedObject?: string;
  onObjectSelect: (objectId: string) => void;
  viewMode: '2D' | '3D';
  precision: number;
  gridSize: number;
}> = ({ objects, selectedObject, onObjectSelect, viewMode, precision, gridSize }) => {
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.4} />
      <directionalLight position={[10, 10, 5]} intensity={0.8} />
      <pointLight position={[-10, -10, -5]} intensity={0.3} />

      {/* Grid */}
      <Grid
        args={[20, 20]}
        cellSize={gridSize}
        cellThickness={0.5}
        cellColor="#6f6f6f"
        sectionSize={gridSize * 5}
        sectionThickness={1}
        sectionColor="#9d4b4b"
        fadeDistance={30}
        fadeStrength={1}
        followCamera={false}
        infiniteGrid={true}
      />

      {/* Objects */}
      {objects.map((object) => (
        <ThreeDObject
          key={object.id}
          object={object}
          isSelected={selectedObject === object.id}
          onSelect={() => onObjectSelect(object.id)}
          precision={precision}
        />
      ))}

      {/* Camera Controls */}
      <CameraControls viewMode={viewMode} />
    </>
  );
};

// Main 3D Viewer Component
export const ThreeDViewer: React.FC<ThreeDViewerProps> = ({
  objects,
  selectedObject,
  onObjectSelect,
  onObjectUpdate,
  viewMode,
  onViewModeChange,
  precision,
  gridSize,
}) => {
  const [showControls, setShowControls] = useState(true);
  const [cameraPosition, setCameraPosition] = useState<[number, number, number]>([5, 5, 5]);

  // Camera controls
  const handleZoomIn = () => {
    // Implementation for zoom in
  };

  const handleZoomOut = () => {
    // Implementation for zoom out
  };

  const handleRotate = () => {
    // Implementation for rotation
  };

  const handleCenter = () => {
    // Implementation for centering view
  };

  const handleViewModeToggle = () => {
    const newMode = viewMode === '2D' ? '3D' : '2D';
    onViewModeChange?.(newMode);
  };

  return (
    <MuiBox sx={{ width: '100%', height: '100%', position: 'relative' }}>
      {/* 3D Canvas */}
      <Canvas
        camera={{ position: cameraPosition, fov: 75 }}
        style={{ background: '#1a1a1a' }}
        gl={{ antialias: true, alpha: true }}
        shadows
      >
        <Scene
          objects={objects}
          selectedObject={selectedObject}
          onObjectSelect={onObjectSelect || (() => {})}
          viewMode={viewMode}
          precision={precision}
          gridSize={gridSize}
        />
      </Canvas>

      {/* Control Panel */}
      {showControls && (
        <MuiBox
          sx={{
            position: 'absolute',
            top: 10,
            right: 10,
            display: 'flex',
            flexDirection: 'column',
            gap: 1,
            backgroundColor: 'rgba(0,0,0,0.8)',
            borderRadius: 1,
            padding: 1,
          }}
        >
          <Tooltip title="Toggle 2D/3D View">
            <IconButton
              size="small"
              onClick={handleViewModeToggle}
              sx={{ color: 'white' }}
            >
              {viewMode === '2D' ? <View3DIcon /> : <View2DIcon />}
            </IconButton>
          </Tooltip>

          <Tooltip title="Zoom In">
            <IconButton
              size="small"
              onClick={handleZoomIn}
              sx={{ color: 'white' }}
            >
              <ZoomInIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Zoom Out">
            <IconButton
              size="small"
              onClick={handleZoomOut}
              sx={{ color: 'white' }}
            >
              <ZoomOutIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Rotate View">
            <IconButton
              size="small"
              onClick={handleRotate}
              sx={{ color: 'white' }}
            >
              <RotateIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Center View">
            <IconButton
              size="small"
              onClick={handleCenter}
              sx={{ color: 'white' }}
            >
              <CenterIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="3D Settings">
            <IconButton
              size="small"
              onClick={() => setShowControls(!showControls)}
              sx={{ color: 'white' }}
            >
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </MuiBox>
      )}

      {/* Status Bar */}
      <MuiBox
        sx={{
          position: 'absolute',
          bottom: 10,
          left: 10,
          backgroundColor: 'rgba(0,0,0,0.8)',
          borderRadius: 1,
          padding: 1,
          color: 'white',
          fontSize: '0.8rem',
        }}
      >
        <div>View Mode: {viewMode}</div>
        <div>Objects: {objects.length}</div>
        <div>Precision: {precision}"</div>
        <div>Grid: {gridSize}"</div>
        {selectedObject && <div>Selected: {selectedObject}</div>}
      </MuiBox>
    </MuiBox>
  );
}; 