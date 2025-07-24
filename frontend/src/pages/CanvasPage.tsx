import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import SVGXCanvas from '../components/Canvas/SVGXCanvas';
import Toolbar from '../components/Toolbar/Toolbar';
import Sidebar from '../components/Sidebar/Sidebar';
import CollaborationPanel from '../components/Collaboration/CollaborationPanel';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import toast from 'react-hot-toast';

// Types
export interface CanvasData {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  objects: any[];
  collaborators: string[];
}

const CanvasPage: React.FC = () => {
  const { canvasId } = useParams<{ canvasId: string }>();
  const navigate = useNavigate();
  const { user, apiClient } = useAuth();
  const { isConnected, connect, disconnect } = useWebSocket();
  
  const [canvasData, setCanvasData] = useState<CanvasData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionId] = useState(`session_${Date.now()}_${user?.user_id}`);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [collaborationOpen, setCollaborationOpen] = useState(false);

  // Load canvas data
  useEffect(() => {
    const loadCanvas = async () => {
      if (!canvasId) {
        setError('No canvas ID provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await apiClient.get(`/runtime/canvas/${canvasId}`);
        setCanvasData(response.data);
      } catch (error: any) {
        console.error('Failed to load canvas:', error);
        setError(error.response?.data?.message || 'Failed to load canvas');
        toast.error('Failed to load canvas');
      } finally {
        setLoading(false);
      }
    };

    loadCanvas();
  }, [canvasId, apiClient]);

  // Connect to WebSocket when canvas is loaded
  useEffect(() => {
    if (canvasData && canvasId) {
      connect(canvasId, sessionId);
    }

    return () => {
      disconnect();
    };
  }, [canvasData, canvasId, sessionId, connect, disconnect]);

  // Handle canvas object changes
  const handleObjectChange = useCallback(async (objects: any[]) => {
    if (!canvasId) return;

    try {
      // Update local state
      setCanvasData(prev => prev ? { ...prev, objects } : null);

      // Send to server
      await apiClient.post('/runtime/ui-event/', {
        event_type: 'canvas_update',
        canvas_id: canvasId,
        data: { objects },
      });
    } catch (error) {
      console.error('Failed to update canvas:', error);
      toast.error('Failed to save changes');
    }
  }, [canvasId, apiClient]);

  // Handle selection change
  const handleSelectionChange = useCallback((selectedIds: string[]) => {
    // Handle selection change logic
    console.log('Selected objects:', selectedIds);
  }, []);

  // Handle canvas save
  const handleSave = useCallback(async () => {
    if (!canvasData) return;

    try {
      await apiClient.post(`/runtime/canvas/${canvasId}/save`, {
        objects: canvasData.objects,
      });
      toast.success('Canvas saved successfully');
    } catch (error) {
      console.error('Failed to save canvas:', error);
      toast.error('Failed to save canvas');
    }
  }, [canvasData, canvasId, apiClient]);

  // Handle canvas export
  const handleExport = useCallback(async (format: 'svg' | 'png' | 'pdf') => {
    if (!canvasId) return;

    try {
      const response = await apiClient.post(`/runtime/canvas/${canvasId}/export`, {
        format,
      });
      
      // Download the file
      const blob = new Blob([response.data], { type: 'application/octet-stream' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `canvas_${canvasId}.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      toast.success(`Canvas exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Failed to export canvas:', error);
      toast.error('Failed to export canvas');
    }
  }, [canvasId, apiClient]);

  // Handle undo/redo
  const handleUndo = useCallback(async () => {
    if (!canvasId) return;

    try {
      const response = await apiClient.post('/runtime/undo/', {
        canvas_id: canvasId,
      });
      
      if (response.data.success) {
        setCanvasData(prev => prev ? { ...prev, objects: response.data.objects } : null);
        toast.success('Undo completed');
      }
    } catch (error) {
      console.error('Failed to undo:', error);
      toast.error('Failed to undo');
    }
  }, [canvasId, apiClient]);

  const handleRedo = useCallback(async () => {
    if (!canvasId) return;

    try {
      const response = await apiClient.post('/runtime/redo/', {
        canvas_id: canvasId,
      });
      
      if (response.data.success) {
        setCanvasData(prev => prev ? { ...prev, objects: response.data.objects } : null);
        toast.success('Redo completed');
      }
    } catch (error) {
      console.error('Failed to redo:', error);
      toast.error('Failed to redo');
    }
  }, [canvasId, apiClient]);

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Error Loading Canvas</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // No canvas data
  if (!canvasData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-600 mb-4">Canvas Not Found</h2>
          <button
            onClick={() => navigate('/')}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        canvasData={canvasData}
        onSave={handleSave}
        onExport={handleExport}
      />

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <Toolbar
          onMenuClick={() => setSidebarOpen(true)}
          onCollaborationClick={() => setCollaborationOpen(!collaborationOpen)}
          onUndo={handleUndo}
          onRedo={handleRedo}
          onSave={handleSave}
          isConnected={isConnected}
          canvasName={canvasData.name}
        />

        {/* Canvas Container */}
        <div className="flex-1 relative">
          <SVGXCanvas
            canvasId={canvasId!}
            sessionId={sessionId}
            initialObjects={canvasData.objects}
            onObjectChange={handleObjectChange}
            onSelectionChange={handleSelectionChange}
            readOnly={!isConnected}
          />
        </div>
      </div>

      {/* Collaboration Panel */}
      <CollaborationPanel
        isOpen={collaborationOpen}
        onClose={() => setCollaborationOpen(false)}
        canvasId={canvasId!}
        sessionId={sessionId}
      />

      {/* Connection Status */}
      {!isConnected && (
        <div className="fixed top-4 right-4 bg-yellow-500 text-white px-4 py-2 rounded-lg shadow-lg">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
            <span>Connecting...</span>
          </div>
        </div>
      )}

      {/* Keyboard Shortcuts Info */}
      <div className="fixed bottom-4 right-4 bg-black bg-opacity-75 text-white px-3 py-2 rounded-lg text-sm">
        <div className="space-y-1">
          <div>Ctrl+Z: Undo</div>
          <div>Ctrl+Y: Redo</div>
          <div>Delete: Delete selected</div>
          <div>Ctrl+A: Select all</div>
        </div>
      </div>
    </div>
  );
};

export default CanvasPage; 