import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { Stage, Layer, Rect, Circle, Line, Text, Group } from 'react-konva';
import { useWebSocket } from '../../contexts/WebSocketContext';
import { useAuth } from '../../contexts/AuthContext';
import { useHotkeys } from 'react-hotkeys-hook';
import toast from 'react-hot-toast';

// Types
export interface CanvasObject {
  id: string;
  type: 'rect' | 'circle' | 'line' | 'text' | 'group';
  x: number;
  y: number;
  width?: number;
  height?: number;
  radius?: number;
  points?: number[];
  text?: string;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  fontSize?: number;
  fontFamily?: string;
  locked?: boolean;
  lockedBy?: string;
  selected?: boolean;
  children?: CanvasObject[];
}

export interface CanvasState {
  objects: CanvasObject[];
  selectedObjects: string[];
  tool: 'select' | 'rect' | 'circle' | 'line' | 'text' | 'move';
  zoom: number;
  pan: { x: number; y: number };
  grid: boolean;
  snap: boolean;
}

export interface SVGXCanvasProps {
  canvasId: string;
  sessionId: string;
  initialObjects?: CanvasObject[];
  onObjectChange?: (objects: CanvasObject[]) => void;
  onSelectionChange?: (selectedIds: string[]) => void;
  readOnly?: boolean;
}

// Canvas Component
const SVGXCanvas: React.FC<SVGXCanvasProps> = ({
  canvasId,
  sessionId,
  initialObjects = [],
  onObjectChange,
  onSelectionChange,
  readOnly = false,
}) => {
  const { user } = useAuth();
  const { isConnected, sendMessage, subscribe } = useWebSocket();
  const stageRef = useRef<any>(null);
  const [canvasState, setCanvasState] = useState<CanvasState>({
    objects: initialObjects,
    selectedObjects: [],
    tool: 'select',
    zoom: 1,
    pan: { x: 0, y: 0 },
    grid: true,
    snap: true,
  });

  const [isDrawing, setIsDrawing] = useState(false);
  const [drawingObject, setDrawingObject] = useState<CanvasObject | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  // Connect to WebSocket on mount
  useEffect(() => {
    if (isConnected) {
      // Subscribe to collaboration events
      const unsubscribeEdit = subscribe('edit_operation', handleRemoteEdit);
      const unsubscribeLock = subscribe('lock_update', handleLockUpdate);
      const unsubscribeUser = subscribe('user_activity', handleUserActivity);

      return () => {
        unsubscribeEdit();
        unsubscribeLock();
        unsubscribeUser();
      };
    }
  }, [isConnected, subscribe]);

  // Handle remote edits
  const handleRemoteEdit = useCallback((data: any) => {
    const { operation, objectId } = data;
    
    setCanvasState(prev => {
      const newObjects = [...prev.objects];
      const objectIndex = newObjects.findIndex(obj => obj.id === objectId);
      
      if (objectIndex !== -1) {
        // Apply remote edit
        newObjects[objectIndex] = { ...newObjects[objectIndex], ...operation };
        onObjectChange?.(newObjects);
      }
      
      return { ...prev, objects: newObjects };
    });
  }, [onObjectChange]);

  // Handle lock updates
  const handleLockUpdate = useCallback((data: any) => {
    const { objectId, locked, lockedBy } = data;
    
    setCanvasState(prev => {
      const newObjects = prev.objects.map(obj => 
        obj.id === objectId 
          ? { ...obj, locked, lockedBy }
          : obj
      );
      
      return { ...prev, objects: newObjects };
    });
  }, []);

  // Handle user activity
  const handleUserActivity = useCallback((data: any) => {
    const { activity, userId } = data;
    if (userId !== user?.user_id) {
      toast.info(`${data.username}: ${activity}`);
    }
  }, [user]);

  // Mouse event handlers
  const handleMouseDown = useCallback((e: any) => {
    if (readOnly) return;

    const pos = e.target.getStage().getPointerPosition();
    setMousePos(pos);

    if (canvasState.tool === 'select') {
      handleSelectMouseDown(e);
    } else {
      handleDrawingMouseDown(pos);
    }
  }, [canvasState.tool, readOnly]);

  const handleMouseMove = useCallback((e: any) => {
    const pos = e.target.getStage().getPointerPosition();
    setMousePos(pos);

    if (isDrawing && drawingObject) {
      handleDrawingMouseMove(pos);
    }
  }, [isDrawing, drawingObject]);

  const handleMouseUp = useCallback(() => {
    if (isDrawing && drawingObject) {
      handleDrawingMouseUp();
    }
  }, [isDrawing, drawingObject]);

  // Selection handling
  const handleSelectMouseDown = useCallback((e: any) => {
    const clickedOnEmpty = e.target === e.target.getStage();
    
    if (clickedOnEmpty) {
      setCanvasState(prev => ({ ...prev, selectedObjects: [] }));
      onSelectionChange?.([]);
    } else {
      const clickedId = e.target.attrs.id;
      setCanvasState(prev => ({ 
        ...prev, 
        selectedObjects: [clickedId] 
      }));
      onSelectionChange?.([clickedId]);
    }
  }, [onSelectionChange]);

  // Drawing handling
  const handleDrawingMouseDown = useCallback((pos: { x: number; y: number }) => {
    const newObject: CanvasObject = {
      id: `obj_${Date.now()}`,
      type: canvasState.tool as any,
      x: pos.x,
      y: pos.y,
      fill: '#ff0000',
      stroke: '#000000',
      strokeWidth: 2,
    };

    if (canvasState.tool === 'rect') {
      newObject.width = 0;
      newObject.height = 0;
    } else if (canvasState.tool === 'circle') {
      newObject.radius = 0;
    } else if (canvasState.tool === 'line') {
      newObject.points = [0, 0];
    } else if (canvasState.tool === 'text') {
      newObject.text = 'Text';
      newObject.fontSize = 16;
      newObject.fontFamily = 'Arial';
    }

    setDrawingObject(newObject);
    setIsDrawing(true);
  }, [canvasState.tool]);

  const handleDrawingMouseMove = useCallback((pos: { x: number; y: number }) => {
    if (!drawingObject) return;

    const updatedObject = { ...drawingObject };

    if (canvasState.tool === 'rect') {
      updatedObject.width = pos.x - drawingObject.x;
      updatedObject.height = pos.y - drawingObject.y;
    } else if (canvasState.tool === 'circle') {
      const dx = pos.x - drawingObject.x;
      const dy = pos.y - drawingObject.y;
      updatedObject.radius = Math.sqrt(dx * dx + dy * dy);
    } else if (canvasState.tool === 'line') {
      updatedObject.points = [0, 0, pos.x - drawingObject.x, pos.y - drawingObject.y];
    }

    setDrawingObject(updatedObject);
  }, [drawingObject, canvasState.tool]);

  const handleDrawingMouseUp = useCallback(() => {
    if (!drawingObject) return;

    // Add object to canvas
    setCanvasState(prev => {
      const newObjects = [...prev.objects, drawingObject];
      onObjectChange?.(newObjects);
      return { ...prev, objects: newObjects };
    });

    // Send edit operation to server
    sendMessage({
      event_type: 'edit_operation',
      canvas_id: canvasId,
      object_id: drawingObject.id,
      data: { operation: 'add', object: drawingObject },
    });

    setDrawingObject(null);
    setIsDrawing(false);
  }, [drawingObject, canvasId, sendMessage, onObjectChange]);

  // Keyboard shortcuts
  useHotkeys('delete, backspace', () => {
    if (canvasState.selectedObjects.length > 0) {
      handleDelete();
    }
  }, [canvasState.selectedObjects]);

  useHotkeys('ctrl+z', () => {
    handleUndo();
  });

  useHotkeys('ctrl+y', () => {
    handleRedo();
  });

  useHotkeys('ctrl+a', (e) => {
    e.preventDefault();
    handleSelectAll();
  });

  // Tool handlers
  const handleDelete = useCallback(() => {
    setCanvasState(prev => {
      const newObjects = prev.objects.filter(
        obj => !prev.selectedObjects.includes(obj.id)
      );
      onObjectChange?.(newObjects);
      return { ...prev, objects: newObjects, selectedObjects: [] };
    });
  }, [onObjectChange]);

  const handleUndo = useCallback(() => {
    // Implement undo functionality
    toast.info('Undo functionality to be implemented');
  }, []);

  const handleRedo = useCallback(() => {
    // Implement redo functionality
    toast.info('Redo functionality to be implemented');
  }, []);

  const handleSelectAll = useCallback(() => {
    setCanvasState(prev => {
      const allIds = prev.objects.map(obj => obj.id);
      onSelectionChange?.(allIds);
      return { ...prev, selectedObjects: allIds };
    });
  }, [onSelectionChange]);

  // Render objects
  const renderObject = useCallback((obj: CanvasObject) => {
    const isSelected = canvasState.selectedObjects.includes(obj.id);
    const isLocked = obj.locked && obj.lockedBy !== user?.user_id;

    const commonProps = {
      id: obj.id,
      x: obj.x,
      y: obj.y,
      fill: isLocked ? '#cccccc' : obj.fill,
      stroke: isSelected ? '#0066ff' : obj.stroke,
      strokeWidth: isSelected ? 3 : obj.strokeWidth,
      opacity: isLocked ? 0.5 : 1,
    };

    switch (obj.type) {
      case 'rect':
        return (
          <Rect
            {...commonProps}
            width={obj.width || 0}
            height={obj.height || 0}
          />
        );
      
      case 'circle':
        return (
          <Circle
            {...commonProps}
            radius={obj.radius || 0}
          />
        );
      
      case 'line':
        return (
          <Line
            {...commonProps}
            points={obj.points || []}
          />
        );
      
      case 'text':
        return (
          <Text
            {...commonProps}
            text={obj.text || ''}
            fontSize={obj.fontSize || 16}
            fontFamily={obj.fontFamily || 'Arial'}
          />
        );
      
      case 'group':
        return (
          <Group {...commonProps}>
            {obj.children?.map(child => renderObject(child))}
          </Group>
        );
      
      default:
        return null;
    }
  }, [canvasState.selectedObjects, user]);

  // Render grid
  const renderGrid = useCallback(() => {
    if (!canvasState.grid) return null;

    const gridSize = 20;
    const stage = stageRef.current;
    if (!stage) return null;

    const width = stage.width();
    const height = stage.height();
    const lines = [];

    // Vertical lines
    for (let i = 0; i <= width; i += gridSize) {
      lines.push(
        <Line
          key={`v${i}`}
          points={[i, 0, i, height]}
          stroke="#e0e0e0"
          strokeWidth={1}
        />
      );
    }

    // Horizontal lines
    for (let i = 0; i <= height; i += gridSize) {
      lines.push(
        <Line
          key={`h${i}`}
          points={[0, i, width, i]}
          stroke="#e0e0e0"
          strokeWidth={1}
        />
      );
    }

    return lines;
  }, [canvasState.grid]);

  return (
    <div className="relative w-full h-full bg-white">
      {/* Canvas Toolbar */}
      <div className="absolute top-4 left-4 z-10 bg-white rounded-lg shadow-lg p-2">
        <div className="flex space-x-2">
          <button
            onClick={() => setCanvasState(prev => ({ ...prev, tool: 'select' }))}
            className={`px-3 py-2 rounded ${canvasState.tool === 'select' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            Select
          </button>
          <button
            onClick={() => setCanvasState(prev => ({ ...prev, tool: 'rect' }))}
            className={`px-3 py-2 rounded ${canvasState.tool === 'rect' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            Rectangle
          </button>
          <button
            onClick={() => setCanvasState(prev => ({ ...prev, tool: 'circle' }))}
            className={`px-3 py-2 rounded ${canvasState.tool === 'circle' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            Circle
          </button>
          <button
            onClick={() => setCanvasState(prev => ({ ...prev, tool: 'line' }))}
            className={`px-3 py-2 rounded ${canvasState.tool === 'line' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            Line
          </button>
          <button
            onClick={() => setCanvasState(prev => ({ ...prev, tool: 'text' }))}
            className={`px-3 py-2 rounded ${canvasState.tool === 'text' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            Text
          </button>
        </div>
      </div>

      {/* Canvas */}
      <Stage
        ref={stageRef}
        width={window.innerWidth}
        height={window.innerHeight - 100}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        scaleX={canvasState.zoom}
        scaleY={canvasState.zoom}
        x={canvasState.pan.x}
        y={canvasState.pan.y}
      >
        <Layer>
          {/* Grid */}
          {renderGrid()}
          
          {/* Objects */}
          {canvasState.objects.map(renderObject)}
          
          {/* Drawing object */}
          {drawingObject && renderObject(drawingObject)}
        </Layer>
      </Stage>

      {/* Status Bar */}
      <div className="absolute bottom-4 left-4 z-10 bg-white rounded-lg shadow-lg p-2">
        <div className="flex space-x-4 text-sm">
          <span>Tool: {canvasState.tool}</span>
          <span>Objects: {canvasState.objects.length}</span>
          <span>Selected: {canvasState.selectedObjects.length}</span>
          <span>Zoom: {Math.round(canvasState.zoom * 100)}%</span>
          <span>Mouse: ({Math.round(mousePos.x)}, {Math.round(mousePos.y)})</span>
          <span className={isConnected ? 'text-green-600' : 'text-red-600'}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SVGXCanvas; 