import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
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
from config import get_config, validate_environment, get_health_info

# Get configuration
config = get_config()
logger = logging.getLogger(__name__)

# Validate environment
if not validate_environment():
    logger.error("Environment validation failed")
    exit(1)

app = Flask(__name__)

# Configure CORS
cors_config = config.get_cors_config()
CORS(app, origins=cors_config['origins'], supports_credentials=cors_config['supports_credentials'])

# Configuration from config module
MAX_FILE_SIZE = config.max_file_size
CACHE_ENABLED = config.cache_enabled
CACHE_TTL = config.cache_ttl

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

        # Get health information from config
        health_info = get_health_info()

        return jsonify({
            "status": "healthy",
            "service": "ifcopenshell",
            "version": ifcopenshell.version,
            "timestamp": datetime.utcnow().isoformat(),
            **health_info
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
    """Parse IFC file and return detailed entities for full extraction"""
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
            # ifcopenshell 0.8.x uses file.from_string instead of open(BytesIO)
            model = ifcopenshell.file.from_string(ifc_data.decode('utf-8', errors='ignore'))

            # Extract buildings with details
            building_entities = extract_building_entities(model)

            # Extract floors (IfcBuildingStorey) with details
            floor_entities = extract_floor_entities(model)

            # Extract spaces (rooms) with details
            space_entities = extract_space_entities(model, floor_entities)

            # Extract equipment with details
            equipment_entities = extract_equipment_entities(model, space_entities)

            # Extract relationships
            relationships = extract_relationships(model)

            # Get entity counts for backward compatibility
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

            # ENHANCED: Return detailed entities for full extraction
            result = {
                "success": True,
                # Backward compatible counts
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
                },
                # NEW: Detailed entity arrays for Go side extraction
                "building_entities": building_entities,
                "floor_entities": floor_entities,
                "space_entities": space_entities,
                "equipment_entities": equipment_entities,
                "relationships": relationships
            }

            # Cache the result using advanced caching
            performance_cache.set(cache_key, result, CACHE_TTL)

            # Record performance metrics
            performance_monitor.record_request("parse", processing_time, True)
            performance_monitor.record_memory_usage()

            logger.info(f"IFC parsing completed: {result['total_entities']} total entities, "
                       f"{len(building_entities)} buildings, {len(floor_entities)} floors, "
                       f"{len(space_entities)} spaces, {len(equipment_entities)} equipment "
                       f"in {processing_time:.3f}s")
            return jsonify(result)

        except ifcopenshell.Error as e:
            processing_time = time.time() - start_time
            performance_monitor.record_request("parse", processing_time, False)
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
            processing_time = time.time() - start_time
            performance_monitor.record_request("parse", processing_time, False)
            logger.error(f"Parsing error: {str(e)}")
            error_response = error_handler.handle_error(
                e, {"endpoint": "parse", "file_size": len(ifc_data)}
            )
            return jsonify(error_response), 500

    except Exception as e:
        logger.error(f"Unexpected error in parse_ifc: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal server error: {str(e)}"
            }
        }), 500

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
        model = ifcopenshell.file.from_string(ifc_data.decode('utf-8', errors='ignore'))

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
        model = ifcopenshell.file.from_string(ifc_data.decode('utf-8', errors='ignore'))

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

def extract_building_entities(model):
    """Extract detailed building entities from IFC model"""
    building_entities = []

    for building in model.by_type('IfcBuilding'):
        try:
            # Get GlobalId
            global_id = building.GlobalId if hasattr(building, 'GlobalId') else str(building.id())

            # Get basic attributes
            name = building.Name if hasattr(building, 'Name') and building.Name else 'Unknown Building'
            description = building.Description if hasattr(building, 'Description') and building.Description else ''
            long_name = building.LongName if hasattr(building, 'LongName') and building.LongName else ''

            # Extract address if available
            address = None
            if hasattr(building, 'BuildingAddress') and building.BuildingAddress:
                addr = building.BuildingAddress
                address = {
                    "address_lines": getattr(addr, 'AddressLines', []) or [],
                    "postal_code": getattr(addr, 'PostalCode', ''),
                    "town": getattr(addr, 'Town', ''),
                    "region": getattr(addr, 'Region', ''),
                    "country": getattr(addr, 'Country', '')
                }

            # Get elevation if available
            elevation = 0.0
            if hasattr(building, 'ElevationOfRefHeight') and building.ElevationOfRefHeight:
                elevation = float(building.ElevationOfRefHeight)

            building_entity = {
                "global_id": global_id,
                "name": name,
                "description": description,
                "long_name": long_name,
                "address": address,
                "elevation": elevation,
                "properties": {}
            }

            building_entities.append(building_entity)

        except Exception as e:
            logger.warning(f"Failed to extract building entity: {e}")
            continue

    return building_entities

def extract_floor_entities(model):
    """Extract detailed floor entities (IfcBuildingStorey) from IFC model"""
    floor_entities = []

    for floor in model.by_type('IfcBuildingStorey'):
        try:
            # Get GlobalId
            global_id = floor.GlobalId if hasattr(floor, 'GlobalId') else str(floor.id())

            # Get basic attributes
            name = floor.Name if hasattr(floor, 'Name') and floor.Name else 'Unknown Floor'
            long_name = floor.LongName if hasattr(floor, 'LongName') and floor.LongName else ''
            description = floor.Description if hasattr(floor, 'Description') and floor.Description else ''

            # Get elevation
            elevation = 0.0
            if hasattr(floor, 'Elevation') and floor.Elevation:
                elevation = float(floor.Elevation)

            # Get height if available
            height = 0.0
            # Height might be in property sets - we'll extract later if needed

            floor_entity = {
                "global_id": global_id,
                "name": name,
                "long_name": long_name,
                "description": description,
                "elevation": elevation,
                "height": height,
                "properties": {}
            }

            floor_entities.append(floor_entity)

        except Exception as e:
            logger.warning(f"Failed to extract floor entity: {e}")
            continue

    return floor_entities

def extract_space_entities(model, floor_entities):
    """Extract detailed space entities (rooms) from IFC model"""
    space_entities = []

    # Create mapping of floor GlobalIDs for easy lookup
    floor_map = {floor['global_id']: floor for floor in floor_entities}

    for space in model.by_type('IfcSpace'):
        try:
            # Get GlobalId
            global_id = space.GlobalId if hasattr(space, 'GlobalId') else str(space.id())

            # Get basic attributes
            name = space.Name if hasattr(space, 'Name') and space.Name else 'Unknown Space'
            long_name = space.LongName if hasattr(space, 'LongName') and space.LongName else ''
            description = space.Description if hasattr(space, 'Description') and space.Description else ''

            # Find parent floor using IfcRelContainedInSpatialStructure
            floor_id = None
            try:
                for rel in model.by_type('IfcRelContainedInSpatialStructure'):
                    if space in rel.RelatedElements:
                        relating_structure = rel.RelatingStructure
                        if relating_structure.is_a('IfcBuildingStorey'):
                            floor_id = relating_structure.GlobalId if hasattr(relating_structure, 'GlobalId') else str(relating_structure.id())
                            break
            except:
                pass

            # Extract placement (3D coordinates)
            placement = extract_placement(space)

            # Extract bounding box if available
            bounding_box = extract_bounding_box(space)

            space_entity = {
                "global_id": global_id,
                "name": name,
                "long_name": long_name,
                "description": description,
                "floor_id": floor_id if floor_id else '',
                "placement": placement,
                "bounding_box": bounding_box,
                "properties": {}
            }

            space_entities.append(space_entity)

        except Exception as e:
            logger.warning(f"Failed to extract space entity: {e}")
            continue

    return space_entities

def extract_equipment_entities(model, space_entities):
    """Extract detailed equipment entities from IFC model"""
    equipment_entities = []

    # Create mapping of space GlobalIDs for easy lookup
    space_map = {space['global_id']: space for space in space_entities}

    # Equipment types to extract
    equipment_types = [
        'IfcFlowTerminal', 'IfcDistributionElement', 'IfcFlowController',
        'IfcFlowMovingDevice', 'IfcEnergyConversionDevice', 'IfcFlowStorageDevice',
        'IfcElectricDistributionBoard', 'IfcLightFixture', 'IfcSanitaryTerminal',
        'IfcFireSuppressionTerminal', 'IfcAirTerminal', 'IfcAirTerminalBox'
    ]

    for eq_type in equipment_types:
        for equipment in model.by_type(eq_type):
            try:
                # Get GlobalId
                global_id = equipment.GlobalId if hasattr(equipment, 'GlobalId') else str(equipment.id())

                # Get basic attributes
                name = equipment.Name if hasattr(equipment, 'Name') and equipment.Name else 'Unknown Equipment'
                description = equipment.Description if hasattr(equipment, 'Description') and equipment.Description else ''
                object_type = equipment.is_a()
                tag = equipment.Tag if hasattr(equipment, 'Tag') and equipment.Tag else ''

                # Find parent space using IfcRelContainedInSpatialStructure
                space_id = None
                try:
                    for rel in model.by_type('IfcRelContainedInSpatialStructure'):
                        if equipment in rel.RelatedElements:
                            relating_structure = rel.RelatingStructure
                            if relating_structure.is_a('IfcSpace'):
                                space_id = relating_structure.GlobalId if hasattr(relating_structure, 'GlobalId') else str(relating_structure.id())
                                break
                except:
                    pass

                # Extract placement (3D coordinates)
                placement = extract_placement(equipment)

                # Map to category (will be done on Go side too, but helps with validation)
                category = map_ifc_type_to_category(object_type)

                # Extract property sets
                property_sets = extract_property_sets(equipment)

                equipment_entity = {
                    "global_id": global_id,
                    "name": name,
                    "description": description,
                    "object_type": object_type,
                    "tag": tag,
                    "space_id": space_id if space_id else '',
                    "placement": placement,
                    "category": category,
                    "property_sets": property_sets,
                    "classification": []
                }

                equipment_entities.append(equipment_entity)

            except Exception as e:
                logger.warning(f"Failed to extract equipment entity {eq_type}: {e}")
                continue

    return equipment_entities

def extract_relationships(model):
    """Extract spatial containment relationships from IFC model"""
    relationships = []

    for rel in model.by_type('IfcRelContainedInSpatialStructure'):
        try:
            relating_id = rel.RelatingStructure.GlobalId if hasattr(rel.RelatingStructure, 'GlobalId') else str(rel.RelatingStructure.id())
            related_ids = []

            for element in rel.RelatedElements:
                element_id = element.GlobalId if hasattr(element, 'GlobalId') else str(element.id())
                related_ids.append(element_id)

            relationship = {
                "type": "contains",
                "relating_object": relating_id,
                "related_objects": related_ids,
                "description": "Spatial containment"
            }

            relationships.append(relationship)

        except Exception as e:
            logger.warning(f"Failed to extract relationship: {e}")
            continue

    return relationships

def extract_placement(element):
    """Extract 3D placement from IFC element"""
    try:
        if not hasattr(element, 'ObjectPlacement') or not element.ObjectPlacement:
            return None

        placement = element.ObjectPlacement

        # Handle IfcLocalPlacement
        if placement.is_a('IfcLocalPlacement'):
            if hasattr(placement, 'RelativePlacement') and placement.RelativePlacement:
                rel_placement = placement.RelativePlacement

                if hasattr(rel_placement, 'Location') and rel_placement.Location:
                    location = rel_placement.Location
                    coords = location.Coordinates if hasattr(location, 'Coordinates') else (0, 0, 0)

                    return {
                        "x": float(coords[0]) if len(coords) > 0 else 0.0,
                        "y": float(coords[1]) if len(coords) > 1 else 0.0,
                        "z": float(coords[2]) if len(coords) > 2 else 0.0
                    }

        return None

    except Exception as e:
        logger.debug(f"Could not extract placement: {e}")
        return None

def extract_bounding_box(element):
    """Extract bounding box from IFC element"""
    try:
        # This is complex - requires shape analysis
        # For MVP, return None and let Go side handle it
        return None
    except Exception as e:
        logger.debug(f"Could not extract bounding box: {e}")
        return None

def extract_property_sets(element):
    """Extract property sets (Psets) from IFC element"""
    property_sets = []

    try:
        # Get property sets using ifcopenshell.util.element
        psets = ifcopenshell.util.element.get_psets(element)

        for pset_name, pset_data in psets.items():
            if pset_data:  # Only include non-empty property sets
                property_set = {
                    "name": pset_name,
                    "properties": pset_data
                }
                property_sets.append(property_set)

    except Exception as e:
        logger.debug(f"Could not extract property sets: {e}")

    return property_sets

def map_ifc_type_to_category(ifc_type):
    """Map IFC object type to equipment category"""
    # Electrical
    if ifc_type in ['IfcElectricDistributionBoard', 'IfcElectricFlowStorageDevice',
                     'IfcElectricGenerator', 'IfcElectricMotor', 'IfcElectricTimeControl']:
        return 'electrical'

    # HVAC
    elif ifc_type in ['IfcAirTerminal', 'IfcAirTerminalBox', 'IfcAirToAirHeatRecovery',
                       'IfcBoiler', 'IfcChiller', 'IfcCoil', 'IfcCompressor',
                       'IfcDamper', 'IfcDuctFitting', 'IfcDuctSegment', 'IfcDuctSilencer',
                       'IfcFan', 'IfcFilter', 'IfcHeatExchanger', 'IfcHumidifier',
                       'IfcPipeFitting', 'IfcPipeSegment', 'IfcPump', 'IfcTank',
                       'IfcTubeBundle', 'IfcUnitaryEquipment', 'IfcValve', 'IfcFlowTerminal']:
        return 'hvac'

    # Plumbing
    elif ifc_type in ['IfcSanitaryTerminal', 'IfcWasteTerminal']:
        return 'plumbing'

    # Safety/Fire
    elif ifc_type in ['IfcFireSuppressionTerminal', 'IfcAlarm', 'IfcSensor']:
        return 'safety'

    # Lighting
    elif ifc_type in ['IfcLightFixture', 'IfcLamp']:
        return 'lighting'

    # Communication/Network
    elif ifc_type in ['IfcCommunicationsAppliance', 'IfcAudioVisualAppliance']:
        return 'network'

    else:
        return 'other'

if __name__ == '__main__':
    # Get port from environment or default to 5001
    port = int(os.getenv('PORT', '5001'))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'true').lower() == 'true'

    logger.info(f"Starting IFC OpenShell service on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
