import os
from flask import Flask, request, jsonify
import ifcopenshell
import ifcopenshell.util.element
import io
import logging
from datetime import datetime
import hashlib
import json
from models.validation import validator
from models.spatial import spatial_query
from models.performance import performance_cache, performance_monitor, cache_key_generator
from models.errors import error_handler, IFCParseError, IFCValidationError, SpatialQueryError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 100 * 1024 * 1024))  # 100MB
CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # 1 hour

# Simple in-memory cache for development
cache = {}

def get_cache_key(ifc_data):
    """Generate cache key for IFC data"""
    return hashlib.md5(ifc_data).hexdigest()

def get_from_cache(ifc_data):
    """Get result from cache if available"""
    if not CACHE_ENABLED:
        return None
    
    cache_key = get_cache_key(ifc_data)
    return cache.get(cache_key)

def set_cache(ifc_data, result):
    """Set result in cache"""
    if not CACHE_ENABLED:
        return
    
    cache_key = get_cache_key(ifc_data)
    cache[cache_key] = result

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Test IfcOpenShell availability
        test_model = ifcopenshell.file()
        test_model.create_entity('IfcProject')
        
        return jsonify({
            "status": "healthy",
            "service": "ifcopenshell",
            "version": ifcopenshell.version,
            "timestamp": datetime.utcnow().isoformat(),
            "cache_enabled": CACHE_ENABLED,
            "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024)
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/api/parse', methods=['POST'])
def parse_ifc():
    """Parse IFC file and return entity counts"""
    try:
        if not request.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "NO_DATA",
                    "message": "No IFC data provided"
                }
            }), 400
        
        ifc_data = request.data
        
        # Check file size
        if len(ifc_data) > MAX_FILE_SIZE:
            return jsonify({
                "success": False,
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.1f}MB"
                }
            }), 413
        
        # Check cache first using advanced caching
        cache_key = cache_key_generator.generate_ifc_key(ifc_data, "parse")
        cached_result = performance_cache.get(cache_key)
        if cached_result:
            logger.info("Returning cached parse result")
            performance_monitor.record_request("parse", 0.001, True)
            return jsonify(cached_result)
        
        # Parse IFC file with performance monitoring
        start_time = time.time()
        logger.info(f"Parsing IFC file of size {len(ifc_data)} bytes")
        
        try:
            model = ifcopenshell.open(io.BytesIO(ifc_data))
            
            # Count entities
            buildings = model.by_type('IfcBuilding')
            spaces = model.by_type('IfcSpace')
            equipment = model.by_type('IfcFlowTerminal')
            walls = model.by_type('IfcWall')
            doors = model.by_type('IfcDoor')
            windows = model.by_type('IfcWindow')
            
            # Get IFC version
            try:
                ifc_version = model.schema if hasattr(model, 'schema') else 'Unknown'
            except:
                ifc_version = 'Unknown'
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "buildings": len(buildings),
                "spaces": len(spaces),
                "equipment": len(equipment),
                "walls": len(walls),
                "doors": len(doors),
                "windows": len(windows),
                "total_entities": len(buildings) + len(spaces) + len(equipment) + len(walls) + len(doors) + len(windows),
                "metadata": {
                    "ifc_version": ifc_version,
                    "file_size": len(ifc_data),
                    "processing_time": f"{processing_time:.3f}s",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # Cache the result using advanced caching
            performance_cache.set(cache_key, result, CACHE_TTL)
            
            # Record performance metrics
            performance_monitor.record_request("parse", processing_time, True)
            performance_monitor.record_memory_usage()
            
            logger.info(f"IFC parsing completed: {result['total_entities']} total entities in {processing_time:.3f}s")
            return jsonify(result)
            
        except Exception as e:
            processing_time = time.time() - start_time
            performance_monitor.record_request("parse", processing_time, False)
            raise e
        
        except ifcopenshell.Error as e:
            logger.error(f"IfcOpenShell parsing error: {str(e)}")
            error_response = error_handler.handle_error(
                IFCParseError(f"Failed to parse IFC file: {str(e)}", {
                    "file_size": len(ifc_data),
                    "ifcopenshell_version": ifcopenshell.version
                }),
                {"endpoint": "parse", "file_size": len(ifc_data)}
            )
            return jsonify(error_response), 400
            
        except Exception as e:
            logger.error(f"Parsing error: {str(e)}")
            error_response = error_handler.handle_error(
                e, {"endpoint": "parse", "file_size": len(ifc_data)}
            )
            return jsonify(error_response), 500

@app.route('/api/validate', methods=['POST'])
def validate_ifc():
    """Enhanced IFC validation with buildingSMART compliance"""
    try:
        if not request.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "NO_DATA",
                    "message": "No IFC data provided"
                }
            }), 400
        
        ifc_data = request.data
        
        # Check file size
        if len(ifc_data) > MAX_FILE_SIZE:
            return jsonify({
                "success": False,
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.1f}MB"
                }
            }), 413
        
        # Check cache first
        cache_key = f"validate:{get_cache_key(ifc_data)}"
        if CACHE_ENABLED and cache_key in cache:
            logger.info("Returning cached validation result")
            return jsonify(cache[cache_key])
        
        # Perform comprehensive validation using enhanced validator
        logger.info(f"Starting IFC validation for file of size {len(ifc_data)} bytes")
        validation_result = validator.validate_ifc(ifc_data)
        
        # Format response
        response = {
            "success": True,
            "valid": validation_result.valid,
            "warnings": validation_result.warnings,
            "errors": validation_result.errors,
            "compliance": validation_result.compliance,
            "metadata": validation_result.metadata,
            "entity_counts": validation_result.entity_counts,
            "spatial_issues": validation_result.spatial_issues,
            "schema_issues": validation_result.schema_issues
        }
        
        # Cache the result
        if CACHE_ENABLED:
            cache[cache_key] = response
            logger.info(f"Cached validation result for key {cache_key}")
        
        logger.info(f"IFC validation completed: valid={validation_result.valid}, "
                   f"warnings={len(validation_result.warnings)}, "
                   f"errors={len(validation_result.errors)}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"IFC validation failed: {e}")
        error_response = error_handler.handle_error(
            IFCValidationError(f"Validation failed: {str(e)}", {
                "file_size": len(ifc_data) if 'ifc_data' in locals() else 0
            }),
            {"endpoint": "validate"}
        )
        return jsonify(error_response), 500

@app.route('/api/spatial/query', methods=['POST'])
def spatial_query_endpoint():
    """Spatial query operations endpoint"""
    try:
        if not request.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "NO_DATA",
                    "message": "No IFC data provided"
                }
            }), 400
        
        ifc_data = request.data
        
        # Check file size
        if len(ifc_data) > MAX_FILE_SIZE:
            return jsonify({
                "success": False,
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.1f}MB"
                }
            }), 413
        
        # Parse request parameters
        query_params = request.get_json() or {}
        query_type = query_params.get('operation', 'within_bounds')
        
        # Parse IFC model
        model = ifcopenshell.open(io.BytesIO(ifc_data))
        
        # Execute spatial query based on type
        if query_type == 'within_bounds':
            bounds = query_params.get('bounds', {'min': [0, 0, 0], 'max': [100, 100, 100]})
            result = spatial_query.query_within_bounds(model, bounds)
            
        elif query_type == 'spatial_relationships':
            entity_id = query_params.get('entity_id')
            if not entity_id:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "MISSING_ENTITY_ID",
                        "message": "entity_id is required for spatial_relationships query"
                    }
                }), 400
            result = spatial_query.query_spatial_relationships(model, entity_id)
            
        elif query_type == 'proximity':
            center = query_params.get('center', [0, 0, 0])
            radius = query_params.get('radius', 10.0)
            result = spatial_query.query_proximity(model, center, radius)
            
        elif query_type == 'statistics':
            result = spatial_query.query_spatial_statistics(model)
            
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_QUERY_TYPE",
                    "message": f"Unknown query type: {query_type}"
                }
            }), 400
        
        logger.info(f"Spatial query '{query_type}' completed: {result.get('total_found', 0)} results")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Spatial query failed: {e}")
        error_response = error_handler.handle_error(
            SpatialQueryError(f"Spatial query failed: {str(e)}", {
                "query_type": query_params.get('operation', 'unknown'),
                "file_size": len(ifc_data) if 'ifc_data' in locals() else 0
            }),
            {"endpoint": "spatial_query"}
        )
        return jsonify(error_response), 500

@app.route('/api/spatial/bounds', methods=['POST'])
def get_spatial_bounds():
    """Get spatial bounds of IFC model"""
    try:
        if not request.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "NO_DATA",
                    "message": "No IFC data provided"
                }
            }), 400
        
        ifc_data = request.data
        
        # Check file size
        if len(ifc_data) > MAX_FILE_SIZE:
            return jsonify({
                "success": False,
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.1f}MB"
                }
            }), 413
        
        # Parse IFC model
        model = ifcopenshell.open(io.BytesIO(ifc_data))
        
        # Get spatial statistics which includes bounding box
        result = spatial_query.query_spatial_statistics(model)
        
        if result["success"]:
            bounds_info = result["statistics"]["bounding_box"]
            coverage_info = result["statistics"]["spatial_coverage"]
            
            response = {
                "success": True,
                "bounding_box": bounds_info,
                "spatial_coverage": coverage_info,
                "entity_counts": result["statistics"]["entity_counts"],
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_entities": result["statistics"]["total_entities"]
                }
            }
        else:
            response = result
        
        logger.info("Spatial bounds query completed")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Spatial bounds query failed: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "SPATIAL_BOUNDS_ERROR",
                "message": f"Spatial bounds query failed: {str(e)}"
            }
        }), 500

@app.route('/api/monitoring/health', methods=['GET'])
def detailed_health():
    """Detailed health check with service status"""
    try:
        # Test IfcOpenShell availability
        test_model = ifcopenshell.file()
        test_model.create_entity('IfcProject')
        
        # Get performance metrics
        perf_metrics = performance_monitor.get_metrics()
        cache_stats = performance_cache.get_stats()
        error_stats = error_handler.get_error_statistics()
        
        health_data = {
            "status": "healthy",
            "service": "ifcopenshell",
            "version": ifcopenshell.version,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": perf_metrics.get("uptime_seconds", 0),
            "performance": {
                "requests_total": perf_metrics.get("requests_total", 0),
                "requests_per_second": perf_metrics.get("requests_per_second", 0),
                "error_rate": perf_metrics.get("error_rate", 0),
                "processing_time_p95": perf_metrics.get("processing_time_percentiles", {}).get("p95", 0)
            },
            "cache": cache_stats,
            "errors": error_stats,
            "configuration": {
                "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024),
                "cache_enabled": CACHE_ENABLED,
                "cache_ttl_seconds": CACHE_TTL
            }
        }
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "service": "ifcopenshell",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/api/monitoring/stats', methods=['GET'])
def service_stats():
    """Get detailed service statistics"""
    try:
        perf_metrics = performance_monitor.get_metrics()
        cache_stats = performance_cache.get_stats()
        error_stats = error_handler.get_error_statistics()
        
        stats_data = {
            "success": True,
            "service": "ifcopenshell",
            "timestamp": datetime.utcnow().isoformat(),
            "performance_metrics": perf_metrics,
            "cache_statistics": cache_stats,
            "error_statistics": error_stats,
            "system_info": {
                "python_version": "3.9+",
                "ifcopenshell_version": ifcopenshell.version,
                "flask_version": "2.3.3"
            }
        }
        
        return jsonify(stats_data)
        
    except Exception as e:
        logger.error(f"Stats collection failed: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "STATS_ERROR",
                "message": f"Failed to collect statistics: {str(e)}"
            }
        }), 500

@app.route('/metrics', methods=['GET'])
def metrics():
    """Enhanced service metrics endpoint with performance data"""
    try:
        # Get cache statistics
        cache_stats = performance_cache.get_stats()
        
        # Get performance metrics
        perf_metrics = performance_monitor.get_metrics()
        
        metrics_data = {
            "success": True,
            "service": "ifcopenshell",
            "timestamp": datetime.utcnow().isoformat(),
            "cache_stats": cache_stats,
            "performance_metrics": perf_metrics,
            "configuration": {
                "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024),
                "cache_ttl_seconds": CACHE_TTL,
                "cache_enabled": CACHE_ENABLED
            }
        }
        
        return jsonify(metrics_data)
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "METRICS_ERROR",
                "message": f"Failed to retrieve metrics: {str(e)}"
            }
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)