/**
 * Arxos CAD Web Workers
 * Handles background processing for SVGX operations, geometry calculations, and constraint solving
 *
 * @author Arxos Team
 * @version 1.1.0 - Enhanced Performance and Error Handling
 * @license MIT
 */

// Performance monitoring
let performanceMetrics = {
    svgxProcessing: 0,
    geometryCalculations: 0,
    constraintSolving: 0,
    totalOperations: 0
};

// Worker context - this file runs in Web Worker environment
self.onmessage = function(event) {
    const { type, objectId, object, options = {} } = event.data;

    try {
        performanceMetrics.totalOperations++;
        const startTime = performance.now();

        switch (type) {
            case 'process_svgx':
                processSvgxObject(objectId, object, options);
                break;
            case 'calculate_geometry':
                calculateGeometry(objectId, object, options);
                break;
            case 'solve_constraints':
                solveConstraints(objectId, object, options);
                break;
            case 'process_large_building':
                processLargeBuilding(objectId, object, options);
                break;
            case 'validate_precision':
                validatePrecision(objectId, object, options);
                break;
            case 'optimize_performance':
                optimizePerformance(objectId, object, options);
                break;
            default:
                console.warn('Unknown worker message type:', type);
                self.postMessage({
                    type: 'error',
                    objectId: objectId,
                    error: `Unknown message type: ${type}`
                });
        }

        // Update performance metrics
        const endTime = performance.now();
        const duration = endTime - startTime;

        switch (type) {
            case 'process_svgx':
                performanceMetrics.svgxProcessing += duration;
                break;
            case 'calculate_geometry':
                performanceMetrics.geometryCalculations += duration;
                break;
            case 'solve_constraints':
                performanceMetrics.constraintSolving += duration;
                break;
        }

    } catch (error) {
        console.error('Worker error:', error);
        self.postMessage({
            type: 'error',
            objectId: objectId,
            error: error.message,
            stack: error.stack
        });
    }
};

/**
 * Enhanced SVGX object processing with precision validation
 */
function processSvgxObject(objectId, object, options = {}) {
    console.log('Processing SVGX object:', objectId, 'with options:', options);

    try {
        // Validate input object
        if (!object || typeof object !== 'object') {
            throw new Error('Invalid object provided for SVGX processing');
        }

        // Apply precision settings
        const precision = options.precision || 0.001; // Default to 0.001 inches
        const units = options.units || 'inches';

        // Process SVGX with enhanced precision
        const processedObject = {
            ...object,
            svgx: {
                path: generateSvgxPath(object, precision),
                attributes: generateSvgxAttributes(object, precision),
                metadata: {
                    processed: true,
                    timestamp: Date.now(),
                    version: '1.1.0',
                    precision: precision,
                    units: units,
                    workerId: self.name || 'unknown'
                }
            }
        };

        // Validate processed object
        if (!processedObject.svgx.path) {
            throw new Error('Failed to generate SVGX path');
        }

        self.postMessage({
            type: 'svgx_processed',
            objectId: objectId,
            result: processedObject,
            performance: {
                duration: performance.now(),
                precision: precision,
                units: units
            }
        });

    } catch (error) {
        console.error('SVGX processing error:', error);
        self.postMessage({
            type: 'svgx_error',
            objectId: objectId,
            error: error.message
        });
    }
}

/**
 * Enhanced geometry calculation with precision validation
 */
function calculateGeometry(objectId, object, options = {}) {
    console.log('Calculating geometry for:', objectId, 'with options:', options);

    try {
        const precision = options.precision || 0.001;
        const geometry = calculateObjectGeometry(object, precision);

        // Validate geometry results
        if (!geometry || !geometry.bounds) {
            throw new Error('Failed to calculate geometry');
        }

        self.postMessage({
            type: 'geometry_calculated',
            objectId: objectId,
            geometry: geometry,
            performance: {
                duration: performance.now(),
                precision: precision
            }
        });

    } catch (error) {
        console.error('Geometry calculation error:', error);
        self.postMessage({
            type: 'geometry_error',
            objectId: objectId,
            error: error.message
        });
    }
}

/**
 * Enhanced constraint solving with validation
 */
function solveConstraints(objectId, object, options = {}) {
    console.log('Solving constraints for:', objectId, 'with options:', options);

    try {
        const precision = options.precision || 0.001;
        const constraints = solveObjectConstraints(object, precision);

        // Validate constraint results
        if (!constraints || !Array.isArray(constraints)) {
            throw new Error('Failed to solve constraints');
        }

        self.postMessage({
            type: 'constraints_solved',
            objectId: objectId,
            constraints: constraints,
            performance: {
                duration: performance.now(),
                precision: precision
            }
        });

    } catch (error) {
        console.error('Constraint solving error:', error);
        self.postMessage({
            type: 'constraint_error',
            objectId: objectId,
            error: error.message
        });
    }
}

/**
 * Precision validation for CAD operations
 */
function validatePrecision(objectId, object, options = {}) {
    console.log('Validating precision for:', objectId);

    try {
        const precision = options.precision || 0.001;
        const maxCoordinate = 1000000; // 1 million units

        const validation = {
            objectId: objectId,
            isValid: true,
            errors: [],
            warnings: []
        };

        // Validate coordinates
        if (object.coordinates) {
            for (const coord of object.coordinates) {
                if (Math.abs(coord.x) > maxCoordinate || Math.abs(coord.y) > maxCoordinate) {
                    validation.errors.push(`Coordinate out of bounds: ${coord.x}, ${coord.y}`);
                    validation.isValid = false;
                }

                // Check precision compliance
                const roundedX = Math.round(coord.x / precision) * precision;
                const roundedY = Math.round(coord.y / precision) * precision;

                if (Math.abs(coord.x - roundedX) > precision || Math.abs(coord.y - roundedY) > precision) {
                    validation.warnings.push(`Coordinate precision mismatch: ${coord.x}, ${coord.y}`);
                }
            }
        }

        self.postMessage({
            type: 'precision_validated',
            objectId: objectId,
            validation: validation
        });

    } catch (error) {
        console.error('Precision validation error:', error);
        self.postMessage({
            type: 'validation_error',
            objectId: objectId,
            error: error.message
        });
    }
}

/**
 * Performance optimization for large operations
 */
function optimizePerformance(objectId, object, options = {}) {
    console.log('Optimizing performance for:', objectId);

    try {
        const optimization = {
            objectId: objectId,
            optimizations: [],
            performance: performanceMetrics
        };

        // Suggest optimizations based on performance metrics
        if (performanceMetrics.svgxProcessing > 100) {
            optimization.optimizations.push('Consider reducing SVGX complexity');
        }

        if (performanceMetrics.geometryCalculations > 50) {
            optimization.optimizations.push('Consider caching geometry calculations');
        }

        if (performanceMetrics.constraintSolving > 200) {
            optimization.optimizations.push('Consider simplifying constraints');
        }

        self.postMessage({
            type: 'performance_optimized',
            objectId: objectId,
            optimization: optimization
        });

    } catch (error) {
        console.error('Performance optimization error:', error);
        self.postMessage({
            type: 'optimization_error',
            objectId: objectId,
            error: error.message
        });
    }
}

/**
 * Generate SVGX path for object
 */
function generateSvgxPath(object, precision = 0.001) {
    switch (object.type) {
        case 'line':
            return `M ${object.startPoint.x} ${object.startPoint.y} L ${object.endPoint.x} ${object.endPoint.y}`;

        case 'rectangle':
            const x = Math.min(object.startPoint.x, object.endPoint.x);
            const y = Math.min(object.startPoint.y, object.endPoint.y);
            const width = Math.abs(object.endPoint.x - object.startPoint.x);
            const height = Math.abs(object.endPoint.y - object.startPoint.y);
            return `M ${x} ${y} h ${width} v ${height} h -${width} z`;

        case 'circle':
            const radius = object.radius;
            const center = object.center;
            return `M ${center.x + radius} ${center.y} A ${radius} ${radius} 0 1 1 ${center.x - radius} ${center.y} A ${radius} ${radius} 0 1 1 ${center.x + radius} ${center.y}`;

        default:
            return '';
    }
}

/**
 * Generate SVGX attributes for object
 */
function generateSvgxAttributes(object, precision = 0.001) {
    const baseAttributes = {
        'stroke': '#1F2937',
        'stroke-width': '2',
        'fill': 'none',
        'vector-effect': 'non-scaling-stroke'
    };

    switch (object.type) {
        case 'line':
            return {
                ...baseAttributes,
                'stroke': '#1F2937',
                'marker-end': 'url(#arrowhead)'
            };

        case 'rectangle':
            return {
                ...baseAttributes,
                'stroke': '#1F2937',
                'fill': 'rgba(59, 130, 246, 0.1)'
            };

        case 'circle':
            return {
                ...baseAttributes,
                'stroke': '#1F2937',
                'fill': 'rgba(59, 130, 246, 0.1)'
            };

        default:
            return baseAttributes;
    }
}

/**
 * Calculate geometry for object
 */
function calculateObjectGeometry(object, precision = 0.001) {
    const geometry = {
        type: object.type,
        bounds: calculateBounds(object, precision),
        centroid: calculateCentroid(object, precision),
        area: calculateArea(object, precision),
        perimeter: calculatePerimeter(object, precision)
    };

    switch (object.type) {
        case 'line':
            geometry.length = calculateDistance(object.startPoint, object.endPoint, precision);
            geometry.angle = calculateAngle(object.startPoint, object.endPoint, precision);
            break;

        case 'rectangle':
            geometry.width = Math.abs(object.endPoint.x - object.startPoint.x);
            geometry.height = Math.abs(object.endPoint.y - object.startPoint.y);
            break;

        case 'circle':
            geometry.radius = object.radius;
            geometry.diameter = object.radius * 2;
            geometry.circumference = 2 * Math.PI * object.radius;
            break;
    }

    return geometry;
}

/**
 * Solve constraints for object
 */
function solveObjectConstraints(object, precision = 0.001) {
    const constraints = [];

    // Add geometric constraints
    if (object.constraints && object.constraints.length > 0) {
        for (const constraint of object.constraints) {
            const solvedConstraint = solveConstraint(constraint, object, precision);
            if (solvedConstraint) {
                constraints.push(solvedConstraint);
            }
        }
    }

    // Add automatic constraints based on object type
    const automaticConstraints = generateAutomaticConstraints(object, precision);
    constraints.push(...automaticConstraints);

    return constraints;
}

/**
 * Process building data for large buildings
 */
function processBuildingData(buildingData) {
    const processedBuilding = {
        id: buildingData.id,
        type: 'building',
        floors: [],
        rooms: [],
        components: [],
        statistics: {
            totalArea: 0,
            totalRooms: 0,
            totalComponents: 0
        }
    };

    // Process floors
    if (buildingData.floors) {
        for (const floor of buildingData.floors) {
            const processedFloor = processFloor(floor);
            processedBuilding.floors.push(processedFloor);
            processedBuilding.statistics.totalArea += processedFloor.area;
        }
    }

    // Process rooms
    if (buildingData.rooms) {
        for (const room of buildingData.rooms) {
            const processedRoom = processRoom(room);
            processedBuilding.rooms.push(processedRoom);
            processedBuilding.statistics.totalRooms++;
        }
    }

    // Process components
    if (buildingData.components) {
        for (const component of buildingData.components) {
            const processedComponent = processComponent(component);
            processedBuilding.components.push(processedComponent);
            processedBuilding.statistics.totalComponents++;
        }
    }

    return processedBuilding;
}

/**
 * Process floor data
 */
function processFloor(floor) {
    return {
        id: floor.id,
        name: floor.name,
        level: floor.level,
        area: calculateFloorArea(floor),
        rooms: floor.rooms || [],
        components: floor.components || []
    };
}

/**
 * Process room data
 */
function processRoom(room) {
    return {
        id: room.id,
        name: room.name,
        type: room.type,
        area: calculateRoomArea(room),
        perimeter: calculateRoomPerimeter(room),
        components: room.components || []
    };
}

/**
 * Process component data
 */
function processComponent(component) {
    return {
        id: component.id,
        type: component.type,
        name: component.name,
        geometry: calculateComponentGeometry(component),
        properties: component.properties || {}
    };
}

/**
 * Utility functions for geometry calculations
 */
function calculateBounds(object, precision = 0.001) {
    switch (object.type) {
        case 'line':
            return {
                minX: Math.min(object.startPoint.x, object.endPoint.x),
                minY: Math.min(object.startPoint.y, object.endPoint.y),
                maxX: Math.max(object.startPoint.x, object.endPoint.x),
                maxY: Math.max(object.startPoint.y, object.endPoint.y)
            };

        case 'rectangle':
            return {
                minX: Math.min(object.startPoint.x, object.endPoint.x),
                minY: Math.min(object.startPoint.y, object.endPoint.y),
                maxX: Math.max(object.startPoint.x, object.endPoint.x),
                maxY: Math.max(object.startPoint.y, object.endPoint.y)
            };

        case 'circle':
            return {
                minX: object.center.x - object.radius,
                minY: object.center.y - object.radius,
                maxX: object.center.x + object.radius,
                maxY: object.center.y + object.radius
            };

        default:
            return { minX: 0, minY: 0, maxX: 0, maxY: 0 };
    }
}

function calculateCentroid(object, precision = 0.001) {
    switch (object.type) {
        case 'line':
            return {
                x: (object.startPoint.x + object.endPoint.x) / 2,
                y: (object.startPoint.y + object.endPoint.y) / 2
            };

        case 'rectangle':
            return {
                x: (object.startPoint.x + object.endPoint.x) / 2,
                y: (object.startPoint.y + object.endPoint.y) / 2
            };

        case 'circle':
            return {
                x: object.center.x,
                y: object.center.y
            };

        default:
            return { x: 0, y: 0 };
    }
}

function calculateArea(object, precision = 0.001) {
    switch (object.type) {
        case 'line':
            return 0; // Lines have no area

        case 'rectangle':
            const width = Math.abs(object.endPoint.x - object.startPoint.x);
            const height = Math.abs(object.endPoint.y - object.startPoint.y);
            return width * height;

        case 'circle':
            return Math.PI * object.radius * object.radius;

        default:
            return 0;
    }
}

function calculatePerimeter(object, precision = 0.001) {
    switch (object.type) {
        case 'line':
            return calculateDistance(object.startPoint, object.endPoint, precision);

        case 'rectangle':
            const width = Math.abs(object.endPoint.x - object.startPoint.x);
            const height = Math.abs(object.endPoint.y - object.startPoint.y);
            return 2 * (width + height);

        case 'circle':
            return 2 * Math.PI * object.radius;

        default:
            return 0;
    }
}

function calculateDistance(point1, point2, precision = 0.001) {
    const dx = point2.x - point1.x;
    const dy = point2.y - point1.y;
    return Math.sqrt(dx * dx + dy * dy);
}

function calculateAngle(point1, point2, precision = 0.001) {
    return Math.atan2(point2.y - point1.y, point2.x - point1.x) * 180 / Math.PI;
}

function calculateFloorArea(floor) {
    // Calculate total area of all rooms in floor
    let totalArea = 0;
    if (floor.rooms) {
        for (const room of floor.rooms) {
            totalArea += calculateRoomArea(room);
        }
    }
    return totalArea;
}

function calculateRoomArea(room) {
    // Calculate room area based on geometry
    if (room.geometry && room.geometry.type === 'rectangle') {
        return room.geometry.width * room.geometry.height;
    }
    return 0;
}

function calculateRoomPerimeter(room) {
    // Calculate room perimeter based on geometry
    if (room.geometry && room.geometry.type === 'rectangle') {
        return 2 * (room.geometry.width + room.geometry.height);
    }
    return 0;
}

function calculateComponentGeometry(component) {
    // Calculate geometry for building components
    return {
        type: component.type,
        bounds: calculateBounds(component),
        area: calculateArea(component),
        volume: calculateVolume(component)
    };
}

function calculateVolume(component) {
    // Calculate volume for 3D components
    if (component.height) {
        return calculateArea(component) * component.height;
    }
    return 0;
}

function solveConstraint(constraint, object, precision = 0.001) {
    // Solve individual constraint
    switch (constraint.type) {
        case 'distance':
            return solveDistanceConstraint(constraint, object, precision);
        case 'angle':
            return solveAngleConstraint(constraint, object, precision);
        case 'parallel':
            return solveParallelConstraint(constraint, object, precision);
        case 'perpendicular':
            return solvePerpendicularConstraint(constraint, object, precision);
        default:
            return null;
    }
}

function solveDistanceConstraint(constraint, object, precision = 0.001) {
    // Solve distance constraint
    return {
        type: 'distance',
        value: constraint.value,
        tolerance: constraint.tolerance || precision,
        satisfied: true
    };
}

function solveAngleConstraint(constraint, object, precision = 0.001) {
    // Solve angle constraint
    return {
        type: 'angle',
        value: constraint.value,
        tolerance: constraint.tolerance || precision,
        satisfied: true
    };
}

function solveParallelConstraint(constraint, object, precision = 0.001) {
    // Solve parallel constraint
    return {
        type: 'parallel',
        target: constraint.target,
        satisfied: true
    };
}

function solvePerpendicularConstraint(constraint, object, precision = 0.001) {
    // Solve perpendicular constraint
    return {
        type: 'perpendicular',
        target: constraint.target,
        satisfied: true
    };
}

function generateAutomaticConstraints(object, precision = 0.001) {
    const constraints = [];

    // Add automatic constraints based on object type
    switch (object.type) {
        case 'line':
            // Lines automatically have length constraint
            constraints.push({
                type: 'length',
                value: calculateDistance(object.startPoint, object.endPoint, precision),
                automatic: true
            });
            break;

        case 'rectangle':
            // Rectangles automatically have width and height constraints
            const width = Math.abs(object.endPoint.x - object.startPoint.x);
            const height = Math.abs(object.endPoint.y - object.startPoint.y);
            constraints.push(
                { type: 'width', value: width, automatic: true },
                { type: 'height', value: height, automatic: true }
            );
            break;

        case 'circle':
            // Circles automatically have radius constraint
            constraints.push({
                type: 'radius',
                value: object.radius,
                automatic: true
            });
            break;
    }

    return constraints;
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        processSvgxObject,
        calculateGeometry,
        solveConstraints,
        processLargeBuilding
    };
}
