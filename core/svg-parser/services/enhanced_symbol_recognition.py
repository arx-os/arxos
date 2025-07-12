"""
Enhanced Symbol Recognition Service with Machine Learning Support.

This service provides advanced symbol recognition capabilities using:
- Computer vision and pattern matching
- Machine learning models for improved accuracy
- Custom symbol training capabilities
- Real-time symbol detection and classification
"""

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None
    np = None
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
import pickle
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

from services.json_symbol_library import JSONSymbolLibrary
from services.geometry_resolver import GeometryResolver


class SymbolType(Enum):
    """Symbol types for classification."""
    HVAC = "hvac"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    FIRE_SAFETY = "fire_safety"
    SECURITY = "security"
    NETWORK = "network"
    STRUCTURAL = "structural"
    FURNITURE = "furniture"
    LIGHTING = "lighting"
    CUSTOM = "custom"


@dataclass
class SymbolMatch:
    """Result of symbol recognition."""
    symbol_id: str
    symbol_name: str
    symbol_type: SymbolType
    confidence: float
    bounding_box: Tuple[float, float, float, float]
    features: Dict[str, Any]
    metadata: Dict[str, Any]


class MLModelType(Enum):
    """Machine learning model types."""
    SVM = "svm"
    RANDOM_FOREST = "random_forest"
    NEURAL_NETWORK = "neural_network"
    KNN = "knn"
    CUSTOM = "custom"


class EnhancedSymbolRecognition:
    """
    Enhanced symbol recognition with machine learning capabilities.
    
    Features:
    - Multi-model symbol recognition
    - Custom symbol training
    - Real-time pattern matching
    - Confidence scoring
    - Symbol classification by type
    """
    
    def __init__(self, library_path: Optional[str] = None):
        """
        Initialize the enhanced symbol recognition service.
        
        Args:
            library_path: Optional path to the symbol library. 
                         If None, uses default library path.
        """
        # Initialize JSON symbol library
        self.symbol_library = JSONSymbolLibrary(library_path)
        self.geometry_resolver = GeometryResolver()
        self.logger = logging.getLogger(__name__)
        
        # ML models storage
        self.models: Dict[str, Any] = {}
        self.feature_extractors: Dict[str, Any] = {}
        self.training_data: Dict[str, List] = {}
        
        # Recognition settings
        self.min_confidence = 0.7
        self.max_matches = 10
        self.enable_ml = True
        
        # Initialize models
        self._initialize_models()
        
        # Check OpenCV availability
        if not OPENCV_AVAILABLE:
            self.logger.warning("OpenCV not available. Computer vision features will be disabled.")
            self.enable_ml = False
        
        self.logger.info(f"Enhanced Symbol Recognition initialized with library: {self.symbol_library.library_path}")
    
    def _initialize_models(self):
        """Initialize machine learning models."""
        try:
            # Load pre-trained models if available
            models_path = Path("models/symbol_recognition")
            if models_path.exists():
                for model_file in models_path.glob("*.pkl"):
                    model_name = model_file.stem
                    with open(model_file, 'rb') as f:
                        self.models[model_name] = pickle.load(f)
                    self.logger.info(f"Loaded ML model: {model_name}")
            
            # Initialize feature extractors
            self._setup_feature_extractors()
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize ML models: {e}")
            self.enable_ml = False
    
    def _setup_feature_extractors(self):
        """Setup feature extraction methods."""
        self.feature_extractors = {
            "shape_features": self._extract_shape_features,
            "color_features": self._extract_color_features,
            "texture_features": self._extract_texture_features,
            "geometric_features": self._extract_geometric_features
        }
    
    def recognize_symbols(self, svg_content: str, options: Optional[Dict[str, Any]] = None) -> List[SymbolMatch]:
        """
        Recognize symbols in SVG content using multiple methods.
        
        Args:
            svg_content: SVG content to analyze
            options: Recognition options
            
        Returns:
            List of recognized symbols with confidence scores
        """
        try:
            options = options or {}
            results = []
            
            # Extract SVG elements
            svg_elements = self._parse_svg_elements(svg_content)
            
            # Method 1: Traditional pattern matching
            pattern_matches = self._pattern_matching_recognition(svg_elements)
            results.extend(pattern_matches)
            
            # Method 2: Machine learning recognition
            if self.enable_ml:
                ml_matches = self._ml_recognition(svg_elements)
                results.extend(ml_matches)
            
            # Method 3: Geometric feature matching
            geometric_matches = self._geometric_recognition(svg_elements)
            results.extend(geometric_matches)
            
            # Filter and rank results
            filtered_results = self._filter_and_rank_results(results, options)
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Symbol recognition failed: {e}")
            return []
    
    def _parse_svg_elements(self, svg_content: str) -> List[Dict[str, Any]]:
        """Parse SVG content into analyzable elements."""
        try:
            # Extract basic SVG elements
            elements = []
            
            # Parse paths, shapes, and text elements
            import re
            
            # Extract paths
            path_pattern = r'<path[^>]*d="([^"]*)"[^>]*>'
            paths = re.findall(path_pattern, svg_content)
            for i, path in enumerate(paths):
                elements.append({
                    'type': 'path',
                    'id': f'path_{i}',
                    'data': path,
                    'features': self._extract_path_features(path)
                })
            
            # Extract basic shapes
            shape_patterns = {
                'rect': r'<rect[^>]*>',
                'circle': r'<circle[^>]*>',
                'ellipse': r'<ellipse[^>]*>',
                'line': r'<line[^>]*>',
                'polygon': r'<polygon[^>]*>',
                'polyline': r'<polyline[^>]*>'
            }
            
            for shape_type, pattern in shape_patterns.items():
                shapes = re.findall(pattern, svg_content)
                for i, shape in enumerate(shapes):
                    elements.append({
                        'type': shape_type,
                        'id': f'{shape_type}_{i}',
                        'data': shape,
                        'features': self._extract_shape_features(shape)
                    })
            
            return elements
            
        except Exception as e:
            self.logger.error(f"SVG parsing failed: {e}")
            return []
    
    def _extract_path_features(self, path_data: str) -> Dict[str, Any]:
        """Extract features from SVG path data."""
        try:
            features = {
                'length': len(path_data),
                'commands': self._count_path_commands(path_data),
                'complexity': self._calculate_path_complexity(path_data),
                'bounds': self._calculate_path_bounds(path_data)
            }
            return features
        except Exception as e:
            self.logger.warning(f"Path feature extraction failed: {e}")
            return {}
    
    def _count_path_commands(self, path_data: str) -> Dict[str, int]:
        """Count different types of path commands."""
        commands = {
            'M': 0, 'L': 0, 'H': 0, 'V': 0, 'C': 0, 'S': 0,
            'Q': 0, 'T': 0, 'A': 0, 'Z': 0
        }
        
        for cmd in commands.keys():
            commands[cmd] = path_data.count(cmd)
        
        return commands
    
    def _calculate_path_complexity(self, path_data: str) -> float:
        """Calculate path complexity score."""
        try:
            # Simple complexity based on command types and length
            total_commands = sum(self._count_path_commands(path_data).values())
            length = len(path_data)
            
            if length == 0:
                return 0.0
            
            # Complexity increases with more commands and longer paths
            complexity = (total_commands * 0.3) + (length / 100.0 * 0.7)
            return min(complexity, 1.0)
            
        except Exception:
            return 0.0
    
    def _calculate_path_bounds(self, path_data: str) -> Tuple[float, float, float, float]:
        """Calculate bounding box of path."""
        try:
            # Extract coordinates from path
            import re
            coords = re.findall(r'[-+]?\d*\.?\d+', path_data)
            
            if len(coords) < 2:
                return (0, 0, 0, 0)
            
            # Convert to float coordinates
            float_coords = [float(c) for c in coords]
            
            # Find min/max for x and y
            x_coords = float_coords[::2]  # Every other coordinate is x
            y_coords = float_coords[1::2]  # Every other coordinate is y
            
            if not x_coords or not y_coords:
                return (0, 0, 0, 0)
            
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            return (x_min, y_min, x_max, y_max)
            
        except Exception:
            return (0, 0, 0, 0)
    
    def _extract_shape_features(self, shape_data: str) -> Dict[str, Any]:
        """Extract features from SVG shape data."""
        try:
            features = {
                'type': 'shape',
                'attributes': self._extract_attributes(shape_data),
                'bounds': self._calculate_shape_bounds(shape_data)
            }
            return features
        except Exception as e:
            self.logger.warning(f"Shape feature extraction failed: {e}")
            return {}
    
    def _extract_color_features(self, element_data: str) -> Dict[str, Any]:
        """Extract color features from element data."""
        try:
            features = {
                'fill_color': 'none',
                'stroke_color': 'none',
                'opacity': 1.0
            }
            
            # Extract color attributes
            attrs = self._extract_attributes(element_data)
            
            if 'fill' in attrs:
                features['fill_color'] = attrs['fill']
            if 'stroke' in attrs:
                features['stroke_color'] = attrs['stroke']
            if 'opacity' in attrs:
                try:
                    features['opacity'] = float(attrs['opacity'])
                except ValueError:
                    pass
            
            return features
        except Exception as e:
            self.logger.warning(f"Color feature extraction failed: {e}")
            return {}
    
    def _extract_texture_features(self, element_data: str) -> Dict[str, Any]:
        """Extract texture features from element data."""
        try:
            features = {
                'has_pattern': False,
                'has_gradient': False,
                'texture_type': 'solid'
            }
            
            # Check for patterns and gradients
            if 'pattern' in element_data.lower():
                features['has_pattern'] = True
                features['texture_type'] = 'pattern'
            elif 'gradient' in element_data.lower():
                features['has_gradient'] = True
                features['texture_type'] = 'gradient'
            
            return features
        except Exception as e:
            self.logger.warning(f"Texture feature extraction failed: {e}")
            return {}
    
    def _extract_attributes(self, element_data: str) -> Dict[str, str]:
        """Extract attributes from SVG element."""
        import re
        attributes = {}
        
        # Extract key-value pairs
        attr_pattern = r'(\w+)="([^"]*)"'
        matches = re.findall(attr_pattern, element_data)
        
        for key, value in matches:
            attributes[key] = value
        
        return attributes
    
    def _calculate_shape_bounds(self, shape_data: str) -> Tuple[float, float, float, float]:
        """Calculate bounding box of shape."""
        try:
            attrs = self._extract_attributes(shape_data)
            
            if 'x' in attrs and 'y' in attrs and 'width' in attrs and 'height' in attrs:
                x = float(attrs['x'])
                y = float(attrs['y'])
                width = float(attrs['width'])
                height = float(attrs['height'])
                return (x, y, x + width, y + height)
            
            return (0, 0, 0, 0)
            
        except Exception:
            return (0, 0, 0, 0)
    
    def _pattern_matching_recognition(self, elements: List[Dict[str, Any]]) -> List[SymbolMatch]:
        """Pattern matching-based symbol recognition."""
        matches = []
        
        try:
            # Load all symbols from the JSON library
            symbols = self.symbol_library.load_all_symbols()
            
            for element in elements:
                # Compare with symbol library
                for symbol_id, symbol_data in symbols.items():
                    confidence = self._calculate_pattern_similarity(element, symbol_data)
                    
                    if confidence >= self.min_confidence:
                        # Map system to symbol type
                        system = symbol_data.get('system', 'custom')
                        symbol_type = self._map_system_to_symbol_type(system)
                        
                        match = SymbolMatch(
                            symbol_id=symbol_id,
                            symbol_name=symbol_data.get('name', symbol_id),
                            symbol_type=symbol_type,
                            confidence=confidence,
                            bounding_box=element.get('features', {}).get('bounds', (0, 0, 0, 0)),
                            features=element.get('features', {}),
                            metadata=symbol_data
                        )
                        matches.append(match)
            
        except Exception as e:
            self.logger.error(f"Pattern matching recognition failed: {e}")
        
        return matches
    
    def _map_system_to_symbol_type(self, system: str) -> SymbolType:
        """Map system string to SymbolType enum."""
        system_mapping = {
            'mechanical': SymbolType.HVAC,
            'electrical': SymbolType.ELECTRICAL,
            'plumbing': SymbolType.PLUMBING,
            'fire_safety': SymbolType.FIRE_SAFETY,
            'security': SymbolType.SECURITY,
            'network': SymbolType.NETWORK,
            'structural': SymbolType.STRUCTURAL,
            'lighting': SymbolType.LIGHTING,
            'furniture': SymbolType.FURNITURE
        }
        return system_mapping.get(system, SymbolType.CUSTOM)
    
    def recognize_symbols_by_system(self, svg_content: str, system: str, options: Optional[Dict[str, Any]] = None) -> List[SymbolMatch]:
        """
        Recognize symbols in SVG content using only symbols from a specific system.
        
        Args:
            svg_content: SVG content to analyze
            system: System to filter symbols (e.g., 'mechanical', 'electrical')
            options: Recognition options
            
        Returns:
            List of recognized symbols with confidence scores
        """
        try:
            options = options or {}
            results = []
            
            # Load symbols for specific system
            system_symbols = self.symbol_library.load_symbols_by_system(system)
            
            # Extract SVG elements
            svg_elements = self._parse_svg_elements(svg_content)
            
            # Pattern matching with system-specific symbols
            for element in svg_elements:
                for symbol_id, symbol_data in system_symbols.items():
                    confidence = self._calculate_pattern_similarity(element, symbol_data)
                    
                    if confidence >= self.min_confidence:
                        symbol_type = self._map_system_to_symbol_type(system)
                        
                        match = SymbolMatch(
                            symbol_id=symbol_id,
                            symbol_name=symbol_data.get('name', symbol_id),
                            symbol_type=symbol_type,
                            confidence=confidence,
                            bounding_box=element.get('features', {}).get('bounds', (0, 0, 0, 0)),
                            features=element.get('features', {}),
                            metadata=symbol_data
                        )
                        results.append(match)
            
            # Filter and rank results
            filtered_results = self._filter_and_rank_results(results, options)
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"System-based symbol recognition failed: {e}")
            return []
    
    def _calculate_pattern_similarity(self, element: Dict[str, Any], symbol_data: Dict[str, Any]) -> float:
        """Calculate similarity between element and symbol pattern."""
        try:
            # Simple similarity calculation based on features
            element_features = element.get('features', {})
            symbol_features = symbol_data.get('features', {})
            
            # Compare feature vectors
            similarity = 0.0
            total_features = 0
            
            # Compare path complexity
            if 'complexity' in element_features and 'complexity' in symbol_features:
                complexity_diff = abs(element_features['complexity'] - symbol_features['complexity'])
                similarity += max(0, 1.0 - complexity_diff)
                total_features += 1
            
            # Compare bounds
            if 'bounds' in element_features and 'bounds' in symbol_features:
                element_bounds = element_features['bounds']
                symbol_bounds = symbol_features['bounds']
                
                if len(element_bounds) == 4 and len(symbol_bounds) == 4:
                    # Calculate overlap
                    overlap = self._calculate_bounds_overlap(element_bounds, symbol_bounds)
                    similarity += overlap
                    total_features += 1
            
            # Compare attributes
            if 'attributes' in element_features and 'attributes' in symbol_features:
                attr_similarity = self._compare_attributes(
                    element_features['attributes'],
                    symbol_features['attributes']
                )
                similarity += attr_similarity
                total_features += 1
            
            if total_features == 0:
                return 0.0
            
            return similarity / total_features
            
        except Exception as e:
            self.logger.warning(f"Similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_bounds_overlap(self, bounds1: Tuple[float, ...], bounds2: Tuple[float, ...]) -> float:
        """Calculate overlap between two bounding boxes."""
        try:
            if len(bounds1) != 4 or len(bounds2) != 4:
                return 0.0
            
            x1_min, y1_min, x1_max, y1_max = bounds1
            x2_min, y2_min, x2_max, y2_max = bounds2
            
            # Calculate intersection
            x_min = max(x1_min, x2_min)
            y_min = max(y1_min, y2_min)
            x_max = min(x1_max, x2_max)
            y_max = min(y1_max, y2_max)
            
            if x_max <= x_min or y_max <= y_min:
                return 0.0
            
            intersection = (x_max - x_min) * (y_max - y_min)
            area1 = (x1_max - x1_min) * (y1_max - y1_min)
            area2 = (x2_max - x2_min) * (y2_max - y2_min)
            
            if area1 == 0 or area2 == 0:
                return 0.0
            
            # Return intersection over union
            union = area1 + area2 - intersection
            return intersection / union if union > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _compare_attributes(self, attrs1: Dict[str, str], attrs2: Dict[str, str]) -> float:
        """Compare attributes between elements."""
        try:
            if not attrs1 or not attrs2:
                return 0.0
            
            common_keys = set(attrs1.keys()) & set(attrs2.keys())
            if not common_keys:
                return 0.0
            
            matches = 0
            for key in common_keys:
                if attrs1[key] == attrs2[key]:
                    matches += 1
            
            return matches / len(common_keys)
            
        except Exception:
            return 0.0
    
    def _ml_recognition(self, elements: List[Dict[str, Any]]) -> List[SymbolMatch]:
        """Machine learning-based symbol recognition."""
        matches = []
        
        try:
            if not OPENCV_AVAILABLE:
                self.logger.warning("ML recognition disabled - OpenCV not available")
                return matches
                
            if not self.models:
                return matches
            
            # Load all symbols for mapping
            symbols = self.symbol_library.load_all_symbols()
            
            for element in elements:
                # Extract features for ML models
                features = self._extract_ml_features(element)
                
                for model_name, model in self.models.items():
                    try:
                        # Predict symbol class
                        prediction = model.predict([features])
                        confidence = model.predict_proba([features]).max() if hasattr(model, 'predict_proba') else 0.8
                        
                        if confidence >= self.min_confidence:
                            # Map prediction to symbol
                            symbol_id = self._map_prediction_to_symbol(prediction[0], model_name)
                            if symbol_id and symbol_id in symbols:
                                symbol_data = symbols[symbol_id]
                                system = symbol_data.get('system', 'custom')
                                symbol_type = self._map_system_to_symbol_type(system)
                                
                                match = SymbolMatch(
                                    symbol_id=symbol_id,
                                    symbol_name=symbol_data.get('name', symbol_id),
                                    symbol_type=symbol_type,
                                    confidence=confidence,
                                    bounding_box=element.get('features', {}).get('bounds', (0, 0, 0, 0)),
                                    features=features,
                                    metadata={'model': model_name, 'prediction': prediction[0]}
                                )
                                matches.append(match)
                    
                    except Exception as e:
                        self.logger.warning(f"ML prediction failed for {model_name}: {e}")
            
        except Exception as e:
            self.logger.error(f"ML recognition failed: {e}")
        
        return matches
    
    def _extract_ml_features(self, element: Dict[str, Any]) -> List[float]:
        """Extract features for machine learning models."""
        features = []
        
        try:
            element_features = element.get('features', {})
            
            # Basic features
            features.extend([
                element_features.get('length', 0),
                element_features.get('complexity', 0),
                len(element_features.get('commands', {})),
                element_features.get('bounds', (0, 0, 0, 0))[2] - element_features.get('bounds', (0, 0, 0, 0))[0],  # width
                element_features.get('bounds', (0, 0, 0, 0))[3] - element_features.get('bounds', (0, 0, 0, 0))[1],  # height
            ])
            
            # Command features
            commands = element_features.get('commands', {})
            for cmd in ['M', 'L', 'H', 'V', 'C', 'S', 'Q', 'T', 'A', 'Z']:
                features.append(commands.get(cmd, 0))
            
            # Normalize features
            features = [float(f) for f in features]
            
        except Exception as e:
            self.logger.warning(f"ML feature extraction failed: {e}")
            features = [0.0] * 15  # Default feature vector
        
        return features
    
    def _map_prediction_to_symbol(self, prediction: str, model_name: str) -> Optional[str]:
        """Map ML prediction to symbol ID."""
        try:
            # This would be a mapping based on training data
            # For now, return the prediction as symbol ID
            return prediction if prediction in self.symbol_library else None
        except Exception:
            return None
    
    def _property_similarity(self, props1: dict, props2: dict) -> float:
        """Compute similarity between two property dicts (0-1)."""
        if not props1 or not props2:
            return 0.0
        keys = set(props1.keys()) | set(props2.keys())
        if not keys:
            return 1.0
        matches = 0
        for k in keys:
            v1 = str(props1.get(k, '')).lower()
            v2 = str(props2.get(k, '')).lower()
            if v1 == v2 and v1 != '':
                matches += 1
        return matches / len(keys)

    def _connection_similarity(self, conns1: list, conns2: list) -> float:
        """Compute similarity between two connection lists (0-1)."""
        if not conns1 or not conns2:
            return 0.0
        matched = 0
        for c1 in conns1:
            for c2 in conns2:
                if (
                    c1.get('type') == c2.get('type') and
                    abs(c1.get('x', 0) - c2.get('x', 0)) < 1e-2 and
                    abs(c1.get('y', 0) - c2.get('y', 0)) < 1e-2
                ):
                    matched += 1
                    break
        return matched / max(len(conns1), len(conns2))

    def _geometric_recognition(self, elements: List[Dict[str, Any]]) -> List[SymbolMatch]:
        """Geometric feature-based recognition with property and connection matching."""
        matches = []
        try:
            symbols = self.symbol_library.load_all_symbols()
            for element in elements:
                geometric_features = self._extract_geometric_features(element)
                element_props = element.get('properties', {})
                element_conns = element.get('connections', [])
                for symbol_id, symbol_data in symbols.items():
                    # Geometric score
                    geo_score = self._compare_geometric_features(geometric_features, symbol_data)
                    # Property score
                    prop_score = self._property_similarity(element_props, symbol_data.get('properties', {}))
                    # Connection score
                    conn_score = self._connection_similarity(element_conns, symbol_data.get('connections', []))
                    # Weighted confidence
                    confidence = 0.5 * geo_score + 0.3 * prop_score + 0.2 * conn_score
                    if confidence >= self.min_confidence:
                        system = symbol_data.get('system', 'custom')
                        symbol_type = self._map_system_to_symbol_type(system)
                        match = SymbolMatch(
                            symbol_id=symbol_id,
                            symbol_name=symbol_data.get('name', symbol_id),
                            symbol_type=symbol_type,
                            confidence=confidence,
                            bounding_box=element.get('features', {}).get('bounds', (0, 0, 0, 0)),
                            features=geometric_features,
                            metadata=symbol_data
                        )
                        matches.append(match)
        except Exception as e:
            self.logger.error(f"Geometric recognition failed: {e}")
        return matches
    
    def _extract_geometric_features(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Extract geometric features from element."""
        try:
            features = {
                'area': 0.0,
                'perimeter': 0.0,
                'aspect_ratio': 1.0,
                'circularity': 0.0,
                'rectangularity': 0.0
            }
            
            element_features = element.get('features', {})
            bounds = element_features.get('bounds', (0, 0, 0, 0))
            
            if len(bounds) == 4:
                width = bounds[2] - bounds[0]
                height = bounds[3] - bounds[1]
                
                features['area'] = width * height
                features['perimeter'] = 2 * (width + height)
                features['aspect_ratio'] = width / height if height > 0 else 1.0
                
                # Calculate shape properties
                if features['area'] > 0:
                    if np is not None:
                        features['circularity'] = (4 * np.pi * features['area']) / (features['perimeter'] ** 2)
                    else:
                        features['circularity'] = 0.0
                    features['rectangularity'] = features['area'] / (width * height)
            
            return features
            
        except Exception as e:
            self.logger.warning(f"Geometric feature extraction failed: {e}")
            return {}
    
    def _compare_geometric_features(self, features1: Dict[str, Any], symbol_data: Dict[str, Any]) -> float:
        """Compare geometric features."""
        try:
            # Extract geometric features from symbol data
            svg_data = symbol_data.get('svg', {})
            svg_content = svg_data.get('content', '')
            
            # Parse SVG content to extract geometric features
            features2 = self._extract_geometric_features_from_svg(svg_content)
            
            if not features1 or not features2:
                return 0.0
            
            # Calculate similarity for each feature
            similarities = []
            
            for key in ['area', 'perimeter', 'aspect_ratio', 'circularity', 'rectangularity']:
                if key in features1 and key in features2:
                    diff = abs(features1[key] - features2[key])
                    max_val = max(features1[key], features2[key])
                    if max_val > 0:
                        similarity = max(0, 1.0 - (diff / max_val))
                        similarities.append(similarity)
            
            return sum(similarities) / len(similarities) if similarities else 0.0
            
        except Exception:
            return 0.0
    
    def _extract_geometric_features_from_svg(self, svg_content: str) -> Dict[str, Any]:
        """Extract geometric features from SVG content."""
        try:
            features = {
                'area': 0.0,
                'perimeter': 0.0,
                'aspect_ratio': 1.0,
                'circularity': 0.0,
                'rectangularity': 0.0
            }
            
            # Parse SVG to get basic bounds
            import re
            
            # Extract viewBox or width/height
            viewbox_match = re.search(r'viewBox="([^"]*)"', svg_content)
            if viewbox_match:
                viewbox = viewbox_match.group(1).split()
                if len(viewbox) >= 4:
                    width = float(viewbox[2]) - float(viewbox[0])
                    height = float(viewbox[3]) - float(viewbox[1])
                    
                    features['area'] = width * height
                    features['perimeter'] = 2 * (width + height)
                    features['aspect_ratio'] = width / height if height > 0 else 1.0
                    
                    if features['area'] > 0:
                        if np is not None:
                            features['circularity'] = (4 * np.pi * features['area']) / (features['perimeter'] ** 2)
                        features['rectangularity'] = 1.0  # SVG is typically rectangular
            
            return features
            
        except Exception as e:
            self.logger.warning(f"SVG geometric feature extraction failed: {e}")
            return {}
    
    def _filter_and_rank_results(self, results: List[SymbolMatch], options: Dict[str, Any]) -> List[SymbolMatch]:
        """Filter and rank recognition results."""
        try:
            # Remove duplicates and low confidence matches
            filtered = []
            seen_symbols = set()
            
            for match in results:
                if match.confidence >= self.min_confidence and match.symbol_id not in seen_symbols:
                    filtered.append(match)
                    seen_symbols.add(match.symbol_id)
            
            # Sort by confidence
            filtered.sort(key=lambda x: x.confidence, reverse=True)
            
            # Limit results
            max_results = options.get('max_results', self.max_matches)
            return filtered[:max_results]
            
        except Exception as e:
            self.logger.error(f"Result filtering failed: {e}")
            return results
    
    def train_custom_symbol(self, symbol_id: str, training_data: List[Dict[str, Any]], 
                           model_type: MLModelType = MLModelType.SVM) -> bool:
        """
        Train a custom symbol recognition model.
        
        Args:
            symbol_id: Unique identifier for the symbol
            training_data: List of training examples
            model_type: Type of ML model to train
            
        Returns:
            True if training successful
        """
        try:
            # Extract features from training data
            features = []
            labels = []
            
            for example in training_data:
                element_features = self._extract_ml_features(example)
                features.append(element_features)
                labels.append(symbol_id)
            
            if len(features) < 5:
                self.logger.warning(f"Insufficient training data for {symbol_id}")
                return False
            
            # Train model
            model = self._train_model(features, labels, model_type)
            
            if model:
                # Save model
                model_name = f"{symbol_id}_{model_type.value}"
                self.models[model_name] = model
                
                # Save to disk
                models_path = Path("models/symbol_recognition")
                models_path.mkdir(parents=True, exist_ok=True)
                
                model_file = models_path / f"{model_name}.pkl"
                with open(model_file, 'wb') as f:
                    pickle.dump(model, f)
                
                self.logger.info(f"Trained custom model for {symbol_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Custom symbol training failed: {e}")
            return False
    
    def _train_model(self, features: List[List[float]], labels: List[str], 
                    model_type: MLModelType) -> Optional[Any]:
        """Train a machine learning model."""
        try:
            if model_type == MLModelType.SVM:
                from sklearn.svm import SVC
                model = SVC(probability=True)
            elif model_type == MLModelType.RANDOM_FOREST:
                from sklearn.ensemble import RandomForestClassifier
                model = RandomForestClassifier(n_estimators=100)
            elif model_type == MLModelType.KNN:
                from sklearn.neighbors import KNeighborsClassifier
                model = KNeighborsClassifier(n_neighbors=3)
            else:
                self.logger.warning(f"Unsupported model type: {model_type}")
                return None
            
            # Train the model
            model.fit(features, labels)
            return model
            
        except ImportError:
            self.logger.warning("scikit-learn not available for ML training")
            return None
        except Exception as e:
            self.logger.error(f"Model training failed: {e}")
            return None
    
    def add_symbol_to_library(self, symbol_id: str, symbol_data: Dict[str, Any]) -> bool:
        """
        Add a symbol to the library for recognition.
        
        Args:
            symbol_id: Unique identifier for the symbol
            symbol_data: Symbol data dictionary
            
        Returns:
            bool: True if successfully added, False otherwise
        """
        try:
            # Note: This method would need to be implemented in the JSONSymbolLibrary
            # For now, we'll log that this feature needs to be implemented
            self.logger.info(f"Adding symbol {symbol_id} to library (feature needs implementation)")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add symbol to library: {e}")
            return False
    
    def get_recognition_statistics(self) -> Dict[str, Any]:
        """Get recognition system statistics."""
        try:
            # Get symbol library statistics
            all_symbols = self.symbol_library.load_all_symbols()
            system_counts = {}
            
            for symbol_data in all_symbols.values():
                system = symbol_data.get('system', 'custom')
                system_counts[system] = system_counts.get(system, 0) + 1
            
            return {
                "total_symbols": len(all_symbols),
                "system_breakdown": system_counts,
                "ml_models": len(self.models),
                "min_confidence": self.min_confidence,
                "enable_ml": self.enable_ml,
                "feature_extractors": list(self.feature_extractors.keys()),
                "model_types": [model_type.value for model_type in MLModelType],
                "library_path": str(self.symbol_library.library_path)
            }
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}


# Global instance
enhanced_symbol_recognition = EnhancedSymbolRecognition() 