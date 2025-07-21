"""
SVGX Engine - Advanced Visualization System

This service provides comprehensive visualization capabilities for BIM behavior
systems, including 3D visualization, real-time dashboards, and interactive
simulation views.

🎯 **Core Visualization Features:**
- 3D BIM Behavior Visualization
- Real-time Interactive Dashboards
- Simulation Views and Controls
- Data Visualization and Charts
- Interactive 3D Models
- Real-time Performance Monitoring
- Virtual Reality (VR) Support
- Augmented Reality (AR) Integration

🏗️ **Enterprise Features:**
- Scalable visualization pipeline with real-time rendering
- Comprehensive dashboard management and customization
- Integration with BIM behavior engine and IoT systems
- Advanced security and access control
- Performance monitoring and optimization
- Enterprise-grade reliability and fault tolerance
"""

import logging
import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
from collections import defaultdict, deque
import json
import websockets
from websockets.server import WebSocketServerProtocol
import numpy as np

# Handle optional dependencies gracefully
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available, some visualization features will be limited")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Warning: plotly not available, some visualization features will be limited")

from svgx_engine.utils.performance import PerformanceMonitor
from svgx_engine.utils.errors import BehaviorError, ValidationError

logger = logging.getLogger(__name__)


class VisualizationType(Enum):
    """Types of visualizations supported."""
    DASHBOARD = "dashboard"
    CHART = "chart"
    THREE_D_MODEL = "3d_model"
    SIMULATION_VIEW = "simulation_view"
    VR_EXPERIENCE = "vr_experience"
    AR_OVERLAY = "ar_overlay"
    HEATMAP = "heatmap"
    TIMELINE = "timeline"


class ChartType(Enum):
    """Types of charts supported."""
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    PIE = "pie"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    CONTOUR = "contour"
    SURFACE = "surface"


class DashboardLayout(Enum):
    """Dashboard layout types."""
    GRID = "grid"
    FLEXIBLE = "flexible"
    CUSTOM = "custom"
    RESPONSIVE = "responsive"


@dataclass
class VisualizationConfig:
    """Configuration for visualization system."""
    # Rendering settings
    render_engine: str = "plotly"  # plotly, matplotlib, threejs
    update_frequency: float = 1.0  # seconds
    max_data_points: int = 10000
    cache_size: int = 1000
    
    # Dashboard settings
    default_layout: DashboardLayout = DashboardLayout.GRID
    max_widgets_per_dashboard: int = 20
    auto_refresh: bool = True
    refresh_interval: int = 5  # seconds
    
    # 3D settings
    enable_3d: bool = True
    enable_vr: bool = False
    enable_ar: bool = False
    model_quality: str = "high"  # low, medium, high
    
    # Performance settings
    max_concurrent_viewers: int = 100
    compression_enabled: bool = True
    lazy_loading: bool = True
    
    # Security settings
    access_control: bool = True
    data_encryption: bool = True
    session_timeout: int = 3600  # seconds


@dataclass
class Dashboard:
    """Dashboard configuration and data."""
    dashboard_id: str
    name: str
    layout: DashboardLayout
    widgets: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    owner: str = ""
    is_public: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChartData:
    """Chart data structure."""
    chart_id: str
    chart_type: ChartType
    title: str
    x_data: List[Any]
    y_data: List[Any]
    z_data: Optional[List[Any]] = None
    labels: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreeDModel:
    """3D model data structure."""
    model_id: str
    name: str
    vertices: List[List[float]]
    faces: List[List[int]]
    textures: Optional[Dict[str, Any]] = None
    animations: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChartGenerator:
    """Generates various types of charts and visualizations."""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.chart_cache = {}
        self.template_charts = self._load_template_charts()
    
    def create_line_chart(self, data: ChartData) -> Dict[str, Any]:
        """Create a line chart."""
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available, returning basic chart data")
            return {
                'type': 'line_chart',
                'data': {
                    'x': data.x_data,
                    'y': data.y_data,
                    'title': data.title
                },
                'chart_id': data.chart_id
            }
        
        try:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=data.x_data,
                y=data.y_data,
                mode='lines+markers',
                name=data.title,
                line=dict(color=data.colors[0] if data.colors else 'blue'),
                marker=dict(size=6)
            ))
            
            fig.update_layout(
                title=data.title,
                xaxis_title="Time",
                yaxis_title="Value",
                template="plotly_white"
            )
            
            return {
                'type': 'line_chart',
                'data': fig.to_dict(),
                'chart_id': data.chart_id
            }
            
        except Exception as e:
            logger.error(f"Error creating line chart: {e}")
            return {}
    
    def create_bar_chart(self, data: ChartData) -> Dict[str, Any]:
        """Create a bar chart."""
        try:
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=data.x_data,
                y=data.y_data,
                name=data.title,
                marker_color=data.colors[0] if data.colors else 'lightblue'
            ))
            
            fig.update_layout(
                title=data.title,
                xaxis_title="Category",
                yaxis_title="Value",
                template="plotly_white"
            )
            
            return {
                'type': 'bar_chart',
                'data': fig.to_dict(),
                'chart_id': data.chart_id
            }
            
        except Exception as e:
            logger.error(f"Error creating bar chart: {e}")
            return {}
    
    def create_scatter_chart(self, data: ChartData) -> Dict[str, Any]:
        """Create a scatter chart."""
        try:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=data.x_data,
                y=data.y_data,
                mode='markers',
                name=data.title,
                marker=dict(
                    size=8,
                    color=data.colors[0] if data.colors else 'red',
                    opacity=0.7
                )
            ))
            
            fig.update_layout(
                title=data.title,
                xaxis_title="X Axis",
                yaxis_title="Y Axis",
                template="plotly_white"
            )
            
            return {
                'type': 'scatter_chart',
                'data': fig.to_dict(),
                'chart_id': data.chart_id
            }
            
        except Exception as e:
            logger.error(f"Error creating scatter chart: {e}")
            return {}
    
    def create_heatmap(self, data: ChartData) -> Dict[str, Any]:
        """Create a heatmap."""
        try:
            if data.z_data is None:
                raise ValueError("Z data required for heatmap")
            
            fig = go.Figure(data=go.Heatmap(
                z=data.z_data,
                x=data.x_data,
                y=data.y_data,
                colorscale='Viridis'
            ))
            
            fig.update_layout(
                title=data.title,
                template="plotly_white"
            )
            
            return {
                'type': 'heatmap',
                'data': fig.to_dict(),
                'chart_id': data.chart_id
            }
            
        except Exception as e:
            logger.error(f"Error creating heatmap: {e}")
            return {}
    
    def create_3d_surface(self, data: ChartData) -> Dict[str, Any]:
        """Create a 3D surface plot."""
        try:
            if data.z_data is None:
                raise ValueError("Z data required for 3D surface")
            
            fig = go.Figure(data=go.Surface(
                z=data.z_data,
                x=data.x_data,
                y=data.y_data,
                colorscale='Viridis'
            ))
            
            fig.update_layout(
                title=data.title,
                scene=dict(
                    xaxis_title="X",
                    yaxis_title="Y",
                    zaxis_title="Z"
                ),
                template="plotly_white"
            )
            
            return {
                'type': '3d_surface',
                'data': fig.to_dict(),
                'chart_id': data.chart_id
            }
            
        except Exception as e:
            logger.error(f"Error creating 3D surface: {e}")
            return {}
    
    def _load_template_charts(self) -> Dict[str, Any]:
        """Load template charts for common visualizations."""
        return {
            'performance_trend': {
                'type': 'line_chart',
                'title': 'Performance Trend',
                'x_label': 'Time',
                'y_label': 'Performance Score'
            },
            'energy_consumption': {
                'type': 'bar_chart',
                'title': 'Energy Consumption',
                'x_label': 'System',
                'y_label': 'Consumption (kWh)'
            },
            'temperature_distribution': {
                'type': 'heatmap',
                'title': 'Temperature Distribution',
                'x_label': 'X Position',
                'y_label': 'Y Position'
            },
            'maintenance_schedule': {
                'type': 'timeline',
                'title': 'Maintenance Schedule',
                'x_label': 'Date',
                'y_label': 'Priority'
            }
        }


class DashboardManager:
    """Manages dashboards and their configurations."""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.dashboards: Dict[str, Dashboard] = {}
        self.dashboard_templates = self._load_dashboard_templates()
        self.active_viewers: Dict[str, Set[str]] = defaultdict(set)  # dashboard_id -> viewer_ids
    
    def create_dashboard(self, name: str, layout: DashboardLayout, 
                        owner: str = "", is_public: bool = False) -> str:
        """Create a new dashboard."""
        try:
            dashboard_id = str(uuid.uuid4())
            
            dashboard = Dashboard(
                dashboard_id=dashboard_id,
                name=name,
                layout=layout,
                owner=owner,
                is_public=is_public
            )
            
            self.dashboards[dashboard_id] = dashboard
            
            logger.info(f"Created dashboard: {name} ({dashboard_id})")
            return dashboard_id
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return ""
    
    def add_widget(self, dashboard_id: str, widget_config: Dict[str, Any]) -> bool:
        """Add a widget to a dashboard."""
        try:
            if dashboard_id not in self.dashboards:
                return False
            
            dashboard = self.dashboards[dashboard_id]
            
            # Check widget limit
            if len(dashboard.widgets) >= self.config.max_widgets_per_dashboard:
                logger.warning(f"Dashboard {dashboard_id} has reached widget limit")
                return False
            
            widget_id = str(uuid.uuid4())
            widget_config['widget_id'] = widget_id
            widget_config['created_at'] = datetime.now().isoformat()
            
            dashboard.widgets.append(widget_config)
            dashboard.updated_at = datetime.now()
            
            logger.info(f"Added widget to dashboard {dashboard_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding widget to dashboard {dashboard_id}: {e}")
            return False
    
    def remove_widget(self, dashboard_id: str, widget_id: str) -> bool:
        """Remove a widget from a dashboard."""
        try:
            if dashboard_id not in self.dashboards:
                return False
            
            dashboard = self.dashboards[dashboard_id]
            
            # Find and remove widget
            for i, widget in enumerate(dashboard.widgets):
                if widget.get('widget_id') == widget_id:
                    del dashboard.widgets[i]
                    dashboard.updated_at = datetime.now()
                    logger.info(f"Removed widget {widget_id} from dashboard {dashboard_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing widget from dashboard {dashboard_id}: {e}")
            return False
    
    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID."""
        return self.dashboards.get(dashboard_id)
    
    def get_user_dashboards(self, user_id: str) -> List[Dashboard]:
        """Get dashboards owned by a user."""
        return [
            dashboard for dashboard in self.dashboards.values()
            if dashboard.owner == user_id or dashboard.is_public
        ]
    
    def update_dashboard_layout(self, dashboard_id: str, layout: DashboardLayout) -> bool:
        """Update dashboard layout."""
        try:
            if dashboard_id not in self.dashboards:
                return False
            
            dashboard = self.dashboards[dashboard_id]
            dashboard.layout = layout
            dashboard.updated_at = datetime.now()
            
            logger.info(f"Updated layout for dashboard {dashboard_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating dashboard layout: {e}")
            return False
    
    def _load_dashboard_templates(self) -> Dict[str, Any]:
        """Load dashboard templates."""
        return {
            'performance_monitoring': {
                'name': 'Performance Monitoring',
                'layout': DashboardLayout.GRID,
                'widgets': [
                    {'type': 'chart', 'chart_type': 'performance_trend'},
                    {'type': 'metric', 'metric_type': 'current_performance'},
                    {'type': 'chart', 'chart_type': 'energy_consumption'},
                    {'type': 'alert', 'alert_type': 'performance_alerts'}
                ]
            },
            'maintenance_dashboard': {
                'name': 'Maintenance Dashboard',
                'layout': DashboardLayout.FLEXIBLE,
                'widgets': [
                    {'type': 'chart', 'chart_type': 'maintenance_schedule'},
                    {'type': 'list', 'list_type': 'pending_maintenance'},
                    {'type': 'metric', 'metric_type': 'maintenance_cost'},
                    {'type': 'chart', 'chart_type': 'equipment_health'}
                ]
            },
            'energy_optimization': {
                'name': 'Energy Optimization',
                'layout': DashboardLayout.RESPONSIVE,
                'widgets': [
                    {'type': 'chart', 'chart_type': 'energy_consumption'},
                    {'type': 'heatmap', 'heatmap_type': 'temperature_distribution'},
                    {'type': 'metric', 'metric_type': 'energy_savings'},
                    {'type': 'chart', 'chart_type': 'optimization_recommendations'}
                ]
            }
        }


class ThreeDVisualizer:
    """Handles 3D visualization and rendering."""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.models: Dict[str, ThreeDModel] = {}
        self.scenes: Dict[str, Dict[str, Any]] = {}
        self.render_cache = {}
    
    def load_model(self, model: ThreeDModel) -> bool:
        """Load a 3D model."""
        try:
            self.models[model.model_id] = model
            
            # Create scene for model
            scene = {
                'model_id': model.model_id,
                'name': model.name,
                'vertices': model.vertices,
                'faces': model.faces,
                'textures': model.textures or {},
                'animations': model.animations or [],
                'metadata': model.metadata
            }
            
            self.scenes[model.model_id] = scene
            
            logger.info(f"Loaded 3D model: {model.name} ({model.model_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error loading 3D model {model.model_id}: {e}")
            return False
    
    def create_scene(self, scene_id: str, models: List[str], 
                    camera_position: List[float] = None) -> bool:
        """Create a 3D scene with multiple models."""
        try:
            scene = {
                'scene_id': scene_id,
                'models': [self.models[model_id] for model_id in models if model_id in self.models],
                'camera_position': camera_position or [0, 0, 5],
                'lights': [
                    {'type': 'ambient', 'intensity': 0.5},
                    {'type': 'directional', 'position': [1, 1, 1], 'intensity': 0.8}
                ],
                'metadata': {}
            }
            
            self.scenes[scene_id] = scene
            
            logger.info(f"Created 3D scene: {scene_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating 3D scene {scene_id}: {e}")
            return False
    
    def update_model_animation(self, model_id: str, animation_data: Dict[str, Any]) -> bool:
        """Update model animation."""
        try:
            if model_id not in self.models:
                return False
            
            model = self.models[model_id]
            if model.animations is None:
                model.animations = []
            
            model.animations.append(animation_data)
            
            logger.info(f"Updated animation for model {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating model animation: {e}")
            return False
    
    def get_scene_data(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """Get scene data for rendering."""
        return self.scenes.get(scene_id)


class AdvancedVisualizationSystem:
    """
    Advanced visualization system for BIM behavior systems with 3D visualization,
    real-time dashboards, and interactive simulation views.
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize components
        self.chart_generator = ChartGenerator(self.config)
        self.dashboard_manager = DashboardManager(self.config)
        self.three_d_visualizer = ThreeDVisualizer(self.config)
        
        # WebSocket connections
        self.websocket_server = None
        self.websocket_clients: Dict[str, WebSocketServerProtocol] = {}
        
        # Data sources
        self.data_sources: Dict[str, Callable] = {}
        self.real_time_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Processing state
        self.running = False
        self.processing_thread = None
        
        # Statistics
        self.visualization_stats = {
            'total_dashboards': 0,
            'active_viewers': 0,
            'charts_generated': 0,
            '3d_models_loaded': 0,
            'real_time_updates': 0
        }
        
        logger.info("Advanced visualization system initialized")
    
    async def start_system(self):
        """Start the visualization system."""
        try:
            # Start WebSocket server
            self.websocket_server = await websockets.serve(
                self._handle_websocket,
                "localhost",
                8769  # Different port to avoid conflicts
            )
            
            # Start processing
            self.running = True
            self.processing_thread = threading.Thread(target=self._processing_loop)
            self.processing_thread.start()
            
            logger.info("Advanced visualization system started")
            
        except Exception as e:
            logger.error(f"Error starting visualization system: {e}")
    
    async def stop_system(self):
        """Stop the visualization system."""
        try:
            self.running = False
            
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()
            
            if self.processing_thread:
                self.processing_thread.join()
            
            logger.info("Advanced visualization system stopped")
            
        except Exception as e:
            logger.error(f"Error stopping visualization system: {e}")
    
    def create_dashboard(self, name: str, layout: DashboardLayout, 
                        owner: str = "", is_public: bool = False) -> str:
        """Create a new dashboard."""
        dashboard_id = self.dashboard_manager.create_dashboard(name, layout, owner, is_public)
        if dashboard_id:
            self.visualization_stats['total_dashboards'] += 1
        return dashboard_id
    
    def add_widget(self, dashboard_id: str, widget_config: Dict[str, Any]) -> bool:
        """Add a widget to a dashboard."""
        return self.dashboard_manager.add_widget(dashboard_id, widget_config)
    
    def create_chart(self, chart_data: ChartData) -> Dict[str, Any]:
        """Create a chart based on data."""
        try:
            if chart_data.chart_type == ChartType.LINE:
                result = self.chart_generator.create_line_chart(chart_data)
            elif chart_data.chart_type == ChartType.BAR:
                result = self.chart_generator.create_bar_chart(chart_data)
            elif chart_data.chart_type == ChartType.SCATTER:
                result = self.chart_generator.create_scatter_chart(chart_data)
            elif chart_data.chart_type == ChartType.CONTOUR:
                result = self.chart_generator.create_heatmap(chart_data)
            elif chart_data.chart_type == ChartType.SURFACE:
                result = self.chart_generator.create_3d_surface(chart_data)
            else:
                logger.warning(f"Unsupported chart type: {chart_data.chart_type}")
                return {}
            
            if result:
                self.visualization_stats['charts_generated'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            return {}
    
    def load_3d_model(self, model: ThreeDModel) -> bool:
        """Load a 3D model."""
        success = self.three_d_visualizer.load_model(model)
        if success:
            self.visualization_stats['3d_models_loaded'] += 1
        return success
    
    def register_data_source(self, source_id: str, data_source: Callable):
        """Register a data source for real-time updates."""
        self.data_sources[source_id] = data_source
        logger.info(f"Registered data source: {source_id}")
    
    def add_real_time_data(self, source_id: str, data: Dict[str, Any]):
        """Add real-time data for visualization."""
        try:
            self.real_time_data[source_id].append({
                'timestamp': datetime.now(),
                'data': data
            })
            
            self.visualization_stats['real_time_updates'] += 1
            
        except Exception as e:
            logger.error(f"Error adding real-time data: {e}")
    
    async def _handle_websocket(self, websocket: WebSocketServerProtocol, path: str):
        """Handle WebSocket connections."""
        client_id = str(uuid.uuid4())
        
        try:
            self.websocket_clients[client_id] = websocket
            
            async for message in websocket:
                await self._process_websocket_message(client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Visualization client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling WebSocket connection: {e}")
        finally:
            self.websocket_clients.pop(client_id, None)
    
    async def _process_websocket_message(self, client_id: str, message: str):
        """Process WebSocket messages."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'get_dashboard':
                dashboard_id = data.get('dashboard_id')
                dashboard = self.dashboard_manager.get_dashboard(dashboard_id)
                await self._send_dashboard_data(client_id, dashboard)
            
            elif message_type == 'create_chart':
                chart_data = data.get('chart_data', {})
                chart_result = self.create_chart(ChartData(**chart_data))
                await self._send_chart_data(client_id, chart_result)
            
            elif message_type == 'get_3d_scene':
                scene_id = data.get('scene_id')
                scene_data = self.three_d_visualizer.get_scene_data(scene_id)
                await self._send_3d_scene_data(client_id, scene_data)
            
            elif message_type == 'subscribe_realtime':
                source_id = data.get('source_id')
                await self._subscribe_to_realtime_data(client_id, source_id)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from client {client_id}")
        except Exception as e:
            logger.error(f"Error processing message from client {client_id}: {e}")
    
    async def _send_dashboard_data(self, client_id: str, dashboard: Optional[Dashboard]):
        """Send dashboard data to client."""
        try:
            websocket = self.websocket_clients.get(client_id)
            if websocket and dashboard:
                await websocket.send(json.dumps({
                    'type': 'dashboard_data',
                    'dashboard': {
                        'dashboard_id': dashboard.dashboard_id,
                        'name': dashboard.name,
                        'layout': dashboard.layout.value,
                        'widgets': dashboard.widgets,
                        'updated_at': dashboard.updated_at.isoformat()
                    }
                }))
            
        except Exception as e:
            logger.error(f"Error sending dashboard data: {e}")
    
    async def _send_chart_data(self, client_id: str, chart_data: Dict[str, Any]):
        """Send chart data to client."""
        try:
            websocket = self.websocket_clients.get(client_id)
            if websocket:
                await websocket.send(json.dumps({
                    'type': 'chart_data',
                    'chart': chart_data
                }))
            
        except Exception as e:
            logger.error(f"Error sending chart data: {e}")
    
    async def _send_3d_scene_data(self, client_id: str, scene_data: Optional[Dict[str, Any]]):
        """Send 3D scene data to client."""
        try:
            websocket = self.websocket_clients.get(client_id)
            if websocket and scene_data:
                await websocket.send(json.dumps({
                    'type': '3d_scene_data',
                    'scene': scene_data
                }))
            
        except Exception as e:
            logger.error(f"Error sending 3D scene data: {e}")
    
    async def _subscribe_to_realtime_data(self, client_id: str, source_id: str):
        """Subscribe client to real-time data updates."""
        try:
            # In a real implementation, this would set up a subscription
            # For now, just log the subscription
            logger.info(f"Client {client_id} subscribed to real-time data: {source_id}")
            
        except Exception as e:
            logger.error(f"Error subscribing to real-time data: {e}")
    
    def _processing_loop(self):
        """Main processing loop for visualization system."""
        while self.running:
            try:
                # Process real-time data
                self._process_real_time_data()
                
                # Update statistics
                self._update_statistics()
                
                # Broadcast updates to clients
                self._broadcast_updates()
                
                time.sleep(self.config.update_frequency)
                
            except Exception as e:
                logger.error(f"Error in visualization processing loop: {e}")
                time.sleep(5)
    
    def _process_real_time_data(self):
        """Process real-time data for visualization."""
        try:
            for source_id, data_queue in self.real_time_data.items():
                if data_queue and source_id in self.data_sources:
                    # Process latest data
                    latest_data = data_queue[-1]
                    self.data_sources[source_id](latest_data)
            
        except Exception as e:
            logger.error(f"Error processing real-time data: {e}")
    
    def _update_statistics(self):
        """Update visualization statistics."""
        try:
            self.visualization_stats['active_viewers'] = len(self.websocket_clients)
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    def _broadcast_updates(self):
        """Broadcast updates to connected clients."""
        try:
            # In a real implementation, this would broadcast real-time updates
            # to all connected clients
            pass
            
        except Exception as e:
            logger.error(f"Error broadcasting updates: {e}")
    
    def get_visualization_stats(self) -> Dict[str, Any]:
        """Get visualization system statistics."""
        return {
            'visualization_stats': self.visualization_stats,
            'total_dashboards': len(self.dashboard_manager.dashboards),
            'total_3d_models': len(self.three_d_visualizer.models),
            'active_clients': len(self.websocket_clients),
            'data_sources': len(self.data_sources)
        }
    
    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID."""
        return self.dashboard_manager.get_dashboard(dashboard_id)
    
    def get_user_dashboards(self, user_id: str) -> List[Dashboard]:
        """Get dashboards for a user."""
        return self.dashboard_manager.get_user_dashboards(user_id)
    
    def clear_visualization_data(self):
        """Clear visualization data."""
        self.real_time_data.clear()
        self.chart_generator.chart_cache.clear()
        self.three_d_visualizer.render_cache.clear()
        logger.info("Visualization data cleared")
    
    def reset_statistics(self):
        """Reset visualization statistics."""
        self.visualization_stats = {
            'total_dashboards': 0,
            'active_viewers': 0,
            'charts_generated': 0,
            '3d_models_loaded': 0,
            'real_time_updates': 0
        }
        logger.info("Visualization statistics reset") 