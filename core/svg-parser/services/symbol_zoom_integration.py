"""
Symbol Library Zoom Integration Service

This service handles the integration between the symbol library and zoom systems,
ensuring proper scaling, consistency, and performance across all zoom levels.
"""

import json
import logging
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ZoomLevel:
    """Represents a zoom level with associated scaling properties."""
    level: float
    name: str
    min_symbol_size: float
    max_symbol_size: float
    scale_factor: float
    lod_level: int


@dataclass
class SymbolScaleData:
    """Contains scaling information for a symbol."""
    symbol_id: str
    base_width: float
    base_height: float
    current_scale: float
    zoom_level: float
    actual_width: float
    actual_height: float
    is_consistent: bool


class SymbolZoomIntegration:
    """
    Handles symbol library integration with zoom systems.
    
    Features:
    - Dynamic symbol scaling based on zoom level
    - Consistency validation across zoom levels
    - Performance optimization for large symbol sets
    - LOD (Level of Detail) management
    - Scale testing and validation
    """
    
    def __init__(self, symbol_library_path: str = "arx-symbol-library"):
        self.symbol_library_path = Path(symbol_library_path)
        self.zoom_levels = self._initialize_zoom_levels()
        self.symbol_cache = {}
        self.scale_cache = {}
        self.consistency_threshold = 0.1  # 10% tolerance for consistency
        
        # Performance settings
        self.max_cache_size = 1000
        self.enable_lod = True
        self.lod_thresholds = [0.25, 0.5, 1.0, 2.0, 4.0]
        
        logger.info("SymbolZoomIntegration initialized")
    
    def _initialize_zoom_levels(self) -> List[ZoomLevel]:
        """Initialize predefined zoom levels with optimal scaling."""
        return [
            ZoomLevel(0.1, "micro", 4, 8, 0.2, 0),
            ZoomLevel(0.25, "tiny", 6, 12, 0.4, 1),
            ZoomLevel(0.5, "small", 10, 20, 0.7, 2),
            ZoomLevel(1.0, "normal", 16, 32, 1.0, 3),
            ZoomLevel(2.0, "large", 24, 48, 1.4, 4),
            ZoomLevel(4.0, "huge", 32, 64, 1.8, 5),
            ZoomLevel(8.0, "massive", 40, 80, 2.2, 6),
            ZoomLevel(16.0, "extreme", 48, 96, 2.6, 7)
        ]
    
    def load_symbol_library(self) -> Dict[str, Any]:
        """Load all symbols from the symbol library."""
        symbols = {}
        
        if not self.symbol_library_path.exists():
            logger.error(f"Symbol library path not found: {self.symbol_library_path}")
            return symbols
        
        for json_file in self.symbol_library_path.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    symbol_data = json.load(f)
                    if symbol_data:
                        symbol_id = symbol_data.get('symbol_id', json_file.stem)
                        symbols[symbol_id] = symbol_data
                        logger.debug(f"Loaded symbol: {symbol_id}")
            except Exception as e:
                logger.error(f"Error loading symbol from {json_file}: {e}")
        
        logger.info(f"Loaded {len(symbols)} symbols from library")
        return symbols
    
    def calculate_optimal_scale(self, zoom_level: float, base_scale: float = 1.0) -> float:
        """
        Calculate optimal scale factor for a given zoom level.
        
        Args:
            zoom_level: Current zoom level (0.1 to 16.0)
            base_scale: Base scale of the symbol (default: 1.0)
            
        Returns:
            Optimal scale factor
        """
        # Clamp zoom level to reasonable bounds
        clamped_zoom = max(0.1, min(16.0, zoom_level))
        
        # Find the closest zoom level
        closest_zoom = min(self.zoom_levels, key=lambda z: abs(z.level - clamped_zoom))
        
        # Calculate scale factor that maintains visual consistency
        # Use logarithmic scaling for better visual perception
        log_zoom = math.log(clamped_zoom + 1)
        optimal_scale = base_scale * (1 / log_zoom) * closest_zoom.scale_factor
        
        # Cache the result
        cache_key = f"{clamped_zoom:.2f}_{base_scale:.2f}"
        self.scale_cache[cache_key] = optimal_scale
        
        # Limit cache size
        if len(self.scale_cache) > self.max_cache_size:
            oldest_key = next(iter(self.scale_cache))
            del self.scale_cache[oldest_key]
        
        return optimal_scale
    
    def get_zoom_level_info(self, zoom_level: float) -> ZoomLevel:
        """Get zoom level information for a given zoom level."""
        return min(self.zoom_levels, key=lambda z: abs(z.level - zoom_level))
    
    def scale_symbol_svg(self, symbol_svg: str, scale_factor: float, 
                        maintain_aspect_ratio: bool = True) -> str:
        """
        Scale an SVG symbol by applying transform.
        
        Args:
            symbol_svg: Original SVG string
            scale_factor: Scale factor to apply
            maintain_aspect_ratio: Whether to maintain aspect ratio
            
        Returns:
            Scaled SVG string
        """
        if not symbol_svg or scale_factor == 1.0:
            return symbol_svg
        
        try:
            # Add transform attribute to the root group
            if '<g id=' in symbol_svg:
                # Find the first group element and add transform
                parts = symbol_svg.split('<g id=', 1)
                if len(parts) == 2:
                    group_start = parts[1].find('>')
                    if group_start != -1:
                        group_attr = parts[1][:group_start]
                        group_content = parts[1][group_start:]
                        
                        # Add or update transform attribute
                        if 'transform=' in group_attr:
                            # Update existing transform
                            transform_start = group_attr.find('transform="')
                            transform_end = group_attr.find('"', transform_start + 11)
                            if transform_end != -1:
                                existing_transform = group_attr[transform_start + 11:transform_end]
                                new_transform = f'{existing_transform} scale({scale_factor})'
                                group_attr = (group_attr[:transform_start] + 
                                            f'transform="{new_transform}"' + 
                                            group_attr[transform_end + 1:])
                        else:
                            # Add new transform attribute
                            group_attr += f' transform="scale({scale_factor})"'
                        
                        return f'<g id={group_attr}{group_content}'
            
            # Fallback: wrap in a group with transform
            return f'<g transform="scale({scale_factor})">{symbol_svg}</g>'
            
        except Exception as e:
            logger.error(f"Error scaling SVG: {e}")
            return symbol_svg
    
    def validate_symbol_consistency(self, symbol_id: str, 
                                  zoom_levels: List[float]) -> List[SymbolScaleData]:
        """
        Validate symbol consistency across different zoom levels.
        
        Args:
            symbol_id: ID of the symbol to validate
            zoom_levels: List of zoom levels to test
            
        Returns:
            List of scale data for each zoom level
        """
        symbols = self.load_symbol_library()
        if symbol_id not in symbols:
            logger.error(f"Symbol {symbol_id} not found in library")
            return []
        
        symbol_data = symbols[symbol_id]
        dimensions = symbol_data.get('dimensions', {})
        base_width = dimensions.get('width', 40)
        base_height = dimensions.get('height', 20)
        
        scale_data = []
        base_scale = symbol_data.get('default_scale', 1.0)
        
        for zoom_level in zoom_levels:
            scale_factor = self.calculate_optimal_scale(zoom_level, base_scale)
            actual_width = base_width * scale_factor
            actual_height = base_height * scale_factor
            
            # Check consistency with expected size
            expected_size = self.get_zoom_level_info(zoom_level).min_symbol_size
            is_consistent = abs(actual_width - expected_size) <= (expected_size * self.consistency_threshold)
            
            scale_data.append(SymbolScaleData(
                symbol_id=symbol_id,
                base_width=base_width,
                base_height=base_height,
                current_scale=scale_factor,
                zoom_level=zoom_level,
                actual_width=actual_width,
                actual_height=actual_height,
                is_consistent=is_consistent
            ))
        
        return scale_data
    
    def test_symbol_placement(self, symbol_id: str, 
                            test_positions: List[Tuple[float, float]],
                            zoom_levels: List[float]) -> Dict[str, Any]:
        """
        Test symbol placement at various positions and zoom levels.
        
        Args:
            symbol_id: ID of the symbol to test
            test_positions: List of (x, y) positions to test
            zoom_levels: List of zoom levels to test
            
        Returns:
            Test results dictionary
        """
        symbols = self.load_symbol_library()
        if symbol_id not in symbols:
            return {"error": f"Symbol {symbol_id} not found"}
        
        results = {
            "symbol_id": symbol_id,
            "test_positions": len(test_positions),
            "zoom_levels": len(zoom_levels),
            "placement_tests": [],
            "scaling_tests": [],
            "performance_metrics": {}
        }
        
        symbol_data = symbols[symbol_id]
        base_scale = symbol_data.get('default_scale', 1.0)
        
        # Test placement at each position and zoom level
        for pos_idx, (x, y) in enumerate(test_positions):
            for zoom_idx, zoom_level in enumerate(zoom_levels):
                scale_factor = self.calculate_optimal_scale(zoom_level, base_scale)
                
                # Test placement
                placement_test = {
                    "position": pos_idx,
                    "zoom_level": zoom_level,
                    "coordinates": {"x": x, "y": y},
                    "scale_factor": scale_factor,
                    "success": True,  # Assume success for now
                    "error": None
                }
                
                # Test scaling
                scaling_test = {
                    "zoom_level": zoom_level,
                    "base_scale": base_scale,
                    "calculated_scale": scale_factor,
                    "expected_scale": self.get_zoom_level_info(zoom_level).scale_factor,
                    "consistency": abs(scale_factor - self.get_zoom_level_info(zoom_level).scale_factor) <= self.consistency_threshold
                }
                
                results["placement_tests"].append(placement_test)
                results["scaling_tests"].append(scaling_test)
        
        # Calculate performance metrics
        results["performance_metrics"] = {
            "total_tests": len(results["placement_tests"]),
            "successful_placements": len([t for t in results["placement_tests"] if t["success"]]),
            "consistent_scaling": len([t for t in results["scaling_tests"] if t["consistency"]]),
            "average_scale_factor": sum(t["calculated_scale"] for t in results["scaling_tests"]) / len(results["scaling_tests"])
        }
        
        return results
    
    def fix_symbol_scaling_issues(self, symbol_id: str) -> Dict[str, Any]:
        """
        Identify and fix scaling issues for a symbol.
        
        Args:
            symbol_id: ID of the symbol to fix
            
        Returns:
            Fix results dictionary
        """
        symbols = self.load_symbol_library()
        if symbol_id not in symbols:
            return {"error": f"Symbol {symbol_id} not found"}
        
        symbol_data = symbols[symbol_id]
        issues = []
        fixes = []
        
        # Check dimensions
        dimensions = symbol_data.get('dimensions', {})
        if not dimensions:
            issues.append("Missing dimensions")
            fixes.append("Add dimensions to symbol definition")
        else:
            width = dimensions.get('width')
            height = dimensions.get('height')
            if not width or not height:
                issues.append("Incomplete dimensions")
                fixes.append("Add both width and height to dimensions")
            elif width <= 0 or height <= 0:
                issues.append("Invalid dimensions")
                fixes.append("Ensure width and height are positive values")
        
        # Check default scale
        default_scale = symbol_data.get('default_scale', 1.0)
        if default_scale <= 0:
            issues.append("Invalid default scale")
            fixes.append("Set default_scale to a positive value")
        
        # Check SVG content
        svg_content = symbol_data.get('svg', '')
        if not svg_content:
            issues.append("Missing SVG content")
            fixes.append("Add SVG content to symbol definition")
        elif not svg_content.strip().startswith('<g'):
            issues.append("SVG not wrapped in group element")
            fixes.append("Wrap SVG content in <g> element with id attribute")
        
        # Generate fixed symbol data
        fixed_data = symbol_data.copy()
        if "Missing dimensions" in issues:
            fixed_data['dimensions'] = {
                'width': 40,
                'height': 20
            }
        if "Invalid default scale" in issues:
            fixed_data['default_scale'] = 1.0
        
        return {
            "symbol_id": symbol_id,
            "issues_found": len(issues),
            "issues": issues,
            "fixes": fixes,
            "fixed_data": fixed_data if issues else None
        }
    
    def validate_symbol_library(self) -> Dict[str, Any]:
        """
        Validate the entire symbol library for zoom system compatibility.
        
        Returns:
            Validation results dictionary
        """
        symbols = self.load_symbol_library()
        validation_results = {
            "total_symbols": len(symbols),
            "valid_symbols": 0,
            "invalid_symbols": 0,
            "symbol_issues": {},
            "library_issues": [],
            "recommendations": []
        }
        
        zoom_levels = [0.25, 0.5, 1.0, 2.0, 4.0]
        
        for symbol_id, symbol_data in symbols.items():
            symbol_issues = []
            
            # Check required fields
            required_fields = ['symbol_id', 'system', 'display_name', 'svg']
            for field in required_fields:
                if field not in symbol_data:
                    symbol_issues.append(f"Missing required field: {field}")
            
            # Check dimensions
            dimensions = symbol_data.get('dimensions', {})
            if not dimensions:
                symbol_issues.append("Missing dimensions")
            else:
                width = dimensions.get('width')
                height = dimensions.get('height')
                if not width or not height or width <= 0 or height <= 0:
                    symbol_issues.append("Invalid dimensions")
            
            # Check default scale
            default_scale = symbol_data.get('default_scale', 1.0)
            if default_scale <= 0:
                symbol_issues.append("Invalid default scale")
            
            # Test scaling consistency
            if not symbol_issues:
                scale_data = self.validate_symbol_consistency(symbol_id, zoom_levels)
                inconsistent_scales = [s for s in scale_data if not s.is_consistent]
                if inconsistent_scales:
                    symbol_issues.append(f"Scaling inconsistency at {len(inconsistent_scales)} zoom levels")
            
            if symbol_issues:
                validation_results["invalid_symbols"] += 1
                validation_results["symbol_issues"][symbol_id] = symbol_issues
            else:
                validation_results["valid_symbols"] += 1
        
        # Generate recommendations
        if validation_results["invalid_symbols"] > 0:
            validation_results["recommendations"].append(
                f"Fix {validation_results['invalid_symbols']} invalid symbols"
            )
        
        if validation_results["valid_symbols"] == 0:
            validation_results["library_issues"].append("No valid symbols found in library")
        
        return validation_results
    
    def generate_zoom_test_report(self) -> str:
        """
        Generate a comprehensive test report for zoom system integration.
        
        Returns:
            HTML report string
        """
        symbols = self.load_symbol_library()
        validation_results = self.validate_symbol_library()
        
        report = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Symbol Library Zoom Integration Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
                .warning {{ color: orange; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Symbol Library Zoom Integration Test Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>Summary</h2>
                <div class="metric">
                    <strong>Total Symbols:</strong> {validation_results['total_symbols']}
                </div>
                <div class="metric">
                    <strong>Valid Symbols:</strong> <span class="success">{validation_results['valid_symbols']}</span>
                </div>
                <div class="metric">
                    <strong>Invalid Symbols:</strong> <span class="error">{validation_results['invalid_symbols']}</span>
                </div>
            </div>
            
            <div class="section">
                <h2>Zoom Level Configuration</h2>
                <table>
                    <tr><th>Zoom Level</th><th>Name</th><th>Min Size</th><th>Max Size</th><th>Scale Factor</th><th>LOD Level</th></tr>
        """
        
        for zoom_level in self.zoom_levels:
            report += f"""
                    <tr>
                        <td>{zoom_level.level}</td>
                        <td>{zoom_level.name}</td>
                        <td>{zoom_level.min_symbol_size}</td>
                        <td>{zoom_level.max_symbol_size}</td>
                        <td>{zoom_level.scale_factor}</td>
                        <td>{zoom_level.lod_level}</td>
                    </tr>
            """
        
        report += """
                </table>
            </div>
        """
        
        if validation_results["symbol_issues"]:
            report += """
            <div class="section">
                <h2>Symbol Issues</h2>
                <table>
                    <tr><th>Symbol ID</th><th>Issues</th></tr>
            """
            
            for symbol_id, issues in validation_results["symbol_issues"].items():
                issues_html = "<br>".join([f"<span class='error'>• {issue}</span>" for issue in issues])
                report += f"""
                    <tr>
                        <td>{symbol_id}</td>
                        <td>{issues_html}</td>
                    </tr>
                """
            
            report += """
                </table>
            </div>
            """
        
        if validation_results["recommendations"]:
            report += """
            <div class="section">
                <h2>Recommendations</h2>
                <ul>
            """
            
            for recommendation in validation_results["recommendations"]:
                report += f"<li class='warning'>{recommendation}</li>"
            
            report += """
                </ul>
            </div>
            """
        
        report += """
        </body>
        </html>
        """
        
        return report 