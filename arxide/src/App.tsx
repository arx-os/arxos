import React, { useState, useEffect, useRef } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { open } from '@tauri-apps/api/dialog';
import { readTextFile, writeTextFile } from '@tauri-apps/api/fs';
import './App.css';

interface ArxObject {
  id: string;
  type: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
  properties: Record<string, any>;
}

interface Project {
  id: string;
  name: string;
  description: string;
  createdAt: Date;
  lastModified: Date;
}

interface CadState {
  objects: ArxObject[];
  selectedObjects: string[];
  currentTool: string;
  precision: number;
  gridSize: number;
  gridSnap: boolean;
}

function App() {
  const [greetMsg, setGreetMsg] = useState('');
  const [name, setName] = useState('');
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [cadState, setCadState] = useState<CadState>({
    objects: [],
    selectedObjects: [],
    currentTool: 'select',
    precision: 0.001,
    gridSize: 0.1,
    gridSnap: true
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const cadEngineRef = useRef<any>(null);

  // Initialize ArxIDE
  useEffect(() => {
    initializeArxIDE();
  }, []);

  const initializeArxIDE = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Initialize Tauri backend
      await invoke('initialize_arxide');
      
      // Load recent projects
      await loadRecentProjects();
      
      // Initialize CAD engine
      await initializeCadEngine();
      
      console.log('ArxIDE initialized successfully');
    } catch (err) {
      console.error('Failed to initialize ArxIDE:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const loadRecentProjects = async () => {
    try {
      const projectData = await invoke('get_recent_projects');
      setProjects(projectData as Project[]);
    } catch (err) {
      console.warn('Failed to load recent projects:', err);
    }
  };

  const initializeCadEngine = async () => {
    if (!canvasRef.current) return;

    try {
      // Initialize CAD engine with enhanced precision
      const CadEngine = (window as any).CadEngine;
      if (CadEngine) {
        cadEngineRef.current = new CadEngine();
        await cadEngineRef.current.initialize(canvasRef.current.id);
        
        // Set up event listeners
        cadEngineRef.current.addEventListener('objectSelected', (data: any) => {
          setCadState(prev => ({
            ...prev,
            selectedObjects: [data.object.id]
          }));
        });
        
        cadEngineRef.current.addEventListener('objectCreated', (data: any) => {
          setCadState(prev => ({
            ...prev,
            objects: [...prev.objects, data.object]
          }));
        });
        
        console.log('CAD Engine initialized');
      }
    } catch (err) {
      console.error('Failed to initialize CAD Engine:', err);
    }
  };

  const greet = async () => {
    if (name === '') return;
    
    try {
      const msg = await invoke('greet', { name });
      setGreetMsg(msg as string);
    } catch (err) {
      console.error('Failed to greet:', err);
      setError(err instanceof Error ? err.message : 'Greet failed');
    }
  };

  const createNewProject = async () => {
    try {
      setIsLoading(true);
      
      const projectName = prompt('Enter project name:');
      if (!projectName) return;
      
      const projectData = await invoke('create_project', {
        name: projectName,
        description: 'New ArxIDE project'
      });
      
      const newProject = projectData as Project;
      setCurrentProject(newProject);
      setProjects(prev => [newProject, ...prev]);
      
      // Reset CAD state
      setCadState({
        objects: [],
        selectedObjects: [],
        currentTool: 'select',
        precision: 0.001,
        gridSize: 0.1,
        gridSnap: true
      });
      
      console.log('New project created:', newProject);
    } catch (err) {
      console.error('Failed to create project:', err);
      setError(err instanceof Error ? err.message : 'Failed to create project');
    } finally {
      setIsLoading(false);
    }
  };

  const openProject = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{
          name: 'ArxIDE Projects',
          extensions: ['arx', 'json']
        }]
      });
      
      if (selected && typeof selected === 'string') {
        await loadProject(selected);
      }
    } catch (err) {
      console.error('Failed to open project:', err);
      setError(err instanceof Error ? err.message : 'Failed to open project');
    }
  };

  const loadProject = async (filePath: string) => {
    try {
      setIsLoading(true);
      
      const fileContent = await readTextFile(filePath);
      const projectData = JSON.parse(fileContent);
      
      setCurrentProject(projectData.project);
      setCadState(projectData.cadState);
      
      console.log('Project loaded:', projectData.project.name);
    } catch (err) {
      console.error('Failed to load project:', err);
      setError(err instanceof Error ? err.message : 'Failed to load project');
    } finally {
      setIsLoading(false);
    }
  };

  const saveProject = async () => {
    if (!currentProject) {
      setError('No project to save');
      return;
    }
    
    try {
      setIsLoading(true);
      
      const projectData = {
        project: currentProject,
        cadState: cadState,
        metadata: {
          saved: new Date().toISOString(),
          version: '1.1.0'
        }
      };
      
      const filePath = await open({
        directory: false,
        multiple: false,
        filters: [{
          name: 'ArxIDE Projects',
          extensions: ['arx']
        }]
      });
      
      if (filePath && typeof filePath === 'string') {
        await writeTextFile(filePath, JSON.stringify(projectData, null, 2));
        console.log('Project saved:', filePath);
      }
    } catch (err) {
      console.error('Failed to save project:', err);
      setError(err instanceof Error ? err.message : 'Failed to save project');
    } finally {
      setIsLoading(false);
    }
  };

  const exportToSVGX = async () => {
    try {
      setIsLoading(true);
      
      if (!cadEngineRef.current) {
        throw new Error('CAD Engine not initialized');
      }
      
      const svgxData = await cadEngineRef.current.exportToSVGX();
      
      const filePath = await open({
        directory: false,
        multiple: false,
        filters: [{
          name: 'SVGX Files',
          extensions: ['svgx']
        }]
      });
      
      if (filePath && typeof filePath === 'string') {
        await writeTextFile(filePath, svgxData);
        console.log('Exported to SVGX:', filePath);
      }
    } catch (err) {
      console.error('Failed to export to SVGX:', err);
      setError(err instanceof Error ? err.message : 'Failed to export to SVGX');
    } finally {
      setIsLoading(false);
    }
  };

  const setCurrentTool = (tool: string) => {
    setCadState(prev => ({ ...prev, currentTool: tool }));
    
    if (cadEngineRef.current) {
      cadEngineRef.current.setCurrentTool(tool);
    }
  };

  const setPrecision = (precision: number) => {
    setCadState(prev => ({ ...prev, precision }));
    
    if (cadEngineRef.current) {
      cadEngineRef.current.setPrecisionLevel(precision === 0.01 ? 'UI' : 
                                           precision === 0.001 ? 'EDIT' : 'COMPUTE');
    }
  };

  const setGridSize = (gridSize: number) => {
    setCadState(prev => ({ ...prev, gridSize }));
    
    if (cadEngineRef.current) {
      cadEngineRef.current.gridSize = gridSize;
    }
  };

  const toggleGridSnap = () => {
    setCadState(prev => ({ ...prev, gridSnap: !prev.gridSnap }));
    
    if (cadEngineRef.current) {
      cadEngineRef.current.gridSnappingEnabled = !cadState.gridSnap;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-white">Loading ArxIDE...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="bg-red-900 rounded-lg p-6 max-w-md">
          <div className="text-red-400 text-xl font-semibold mb-4">Error</div>
          <div className="text-white mb-4">{error}</div>
          <button 
            onClick={() => setError(null)}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
          >
            Dismiss
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-blue-400">ArxIDE</h1>
            <div className="text-sm text-gray-400">Professional Desktop CAD</div>
          </div>
          
          <div className="flex items-center space-x-4">
            {currentProject && (
              <div className="text-sm text-gray-400">
                Project: {currentProject.name}
              </div>
            )}
            
            <button
              onClick={createNewProject}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-sm"
            >
              New Project
            </button>
            
            <button
              onClick={openProject}
              className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded text-sm"
            >
              Open Project
            </button>
            
            <button
              onClick={saveProject}
              disabled={!currentProject}
              className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded text-sm disabled:opacity-50"
            >
              Save Project
            </button>
            
            <button
              onClick={exportToSVGX}
              disabled={!currentProject}
              className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded text-sm disabled:opacity-50"
            >
              Export SVGX
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Left Panel - Tools */}
        <div className="w-64 bg-gray-800 border-r border-gray-700 p-4">
          <h3 className="text-lg font-semibold mb-4">Tools</h3>
          
          {/* Drawing Tools */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-300 mb-2">Drawing</h4>
            <div className="space-y-2">
              {['select', 'line', 'rectangle', 'circle'].map(tool => (
                <button
                  key={tool}
                  onClick={() => setCurrentTool(tool)}
                  className={`w-full text-left p-2 rounded text-sm transition-colors ${
                    cadState.currentTool === tool
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                  }`}
                >
                  {tool.charAt(0).toUpperCase() + tool.slice(1)}
                </button>
              ))}
            </div>
          </div>
          
          {/* Precision Controls */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-300 mb-2">Precision</h4>
            <div className="space-y-2">
              <select
                value={cadState.precision}
                onChange={(e) => setPrecision(parseFloat(e.target.value))}
                className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm"
              >
                <option value={0.01}>UI (0.01")</option>
                <option value={0.001}>Edit (0.001")</option>
                <option value={0.0001}>Compute (0.0001")</option>
              </select>
            </div>
          </div>
          
          {/* Grid Controls */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-300 mb-2">Grid</h4>
            <div className="space-y-2">
              <select
                value={cadState.gridSize}
                onChange={(e) => setGridSize(parseFloat(e.target.value))}
                className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm"
              >
                <option value={0.01}>0.01"</option>
                <option value={0.1}>0.1"</option>
                <option value={1}>1"</option>
                <option value={12}>12"</option>
              </select>
              
              <label className="flex items-center space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={cadState.gridSnap}
                  onChange={toggleGridSnap}
                  className="rounded"
                />
                <span>Snap to Grid</span>
              </label>
            </div>
          </div>
          
          {/* Project Info */}
          {currentProject && (
            <div className="border-t border-gray-700 pt-4">
              <h4 className="text-sm font-medium text-gray-300 mb-2">Project Info</h4>
              <div className="text-xs text-gray-400 space-y-1">
                <div>Created: {currentProject.createdAt.toLocaleDateString()}</div>
                <div>Modified: {currentProject.lastModified.toLocaleDateString()}</div>
                <div>Objects: {cadState.objects.length}</div>
              </div>
            </div>
          )}
        </div>

        {/* Center - Canvas */}
        <div className="flex-1 relative">
          <canvas
            ref={canvasRef}
            id="arxide-canvas"
            className="w-full h-full bg-white"
          />
          
          {/* Status Bar */}
          <div className="absolute bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 p-2">
            <div className="flex items-center justify-between text-sm">
              <div className="text-gray-400">
                Tool: {cadState.currentTool} | Precision: {cadState.precision}" | Grid: {cadState.gridSize}"
              </div>
              <div className="text-gray-400">
                Objects: {cadState.objects.length} | Selected: {cadState.selectedObjects.length}
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Properties */}
        <div className="w-80 bg-gray-800 border-l border-gray-700 p-4">
          <h3 className="text-lg font-semibold mb-4">Properties</h3>
          
          {cadState.selectedObjects.length === 0 ? (
            <div className="text-gray-400 text-sm">Select an object to view properties</div>
          ) : (
            <div className="space-y-4">
              {cadState.selectedObjects.map(objectId => {
                const object = cadState.objects.find(obj => obj.id === objectId);
                if (!object) return null;
                
                return (
                  <div key={objectId} className="border border-gray-700 rounded p-3">
                    <h4 className="font-medium text-white mb-2">{object.type}</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">X:</span>
                        <span className="text-white">{object.x.toFixed(3)}"</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Y:</span>
                        <span className="text-white">{object.y.toFixed(3)}"</span>
                      </div>
                      {object.width && (
                        <div className="flex justify-between">
                          <span className="text-gray-400">Width:</span>
                          <span className="text-white">{object.width.toFixed(3)}"</span>
                        </div>
                      )}
                      {object.height && (
                        <div className="flex justify-between">
                          <span className="text-gray-400">Height:</span>
                          <span className="text-white">{object.height.toFixed(3)}"</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App; 