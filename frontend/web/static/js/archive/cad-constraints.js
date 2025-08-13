/**
 * Arxos CAD Constraint System
 * Handles geometric constraints for CAD-level precision and relationships
 *
 * @author Arxos Team
 * @version 1.1.0 - Enhanced Precision and CAD Integration
 * @license MIT
 */

class ConstraintSolver {
    constructor() {
        this.constraints = new Map();
        this.constraintId = 0;
        this.solverActive = false;

        // Constraint types
        this.constraintTypes = {
            'DISTANCE': 'distance',
            'ANGLE': 'angle',
            'PARALLEL': 'parallel',
            'PERPENDICULAR': 'perpendicular',
            'COINCIDENT': 'coincident',
            'TANGENT': 'tangent',
            'HORIZONTAL': 'horizontal',
            'VERTICAL': 'vertical'
        };

        // Enhanced precision settings
        this.precision = 0.001; // 0.001 inches
        this.anglePrecision = 0.1; // 0.1 degrees
        this.maxIterations = 100; // Maximum solver iterations
        this.convergenceTolerance = 0.0001; // Convergence tolerance
    }

    /**
     * Add a geometric constraint with enhanced validation
     * @param {string} type - Constraint type
     * @param {Object} params - Constraint parameters
     * @returns {string} Constraint ID
     */
    addConstraint(type, params) {
        // Validate constraint type
        if (!this.constraintTypes[type.toUpperCase()]) {
            throw new Error(`Invalid constraint type: ${type}`);
        }

        // Validate constraint parameters
        this.validateConstraint(type, params);

        const constraintId = `constraint_${++this.constraintId}`;

        const constraint = {
            id: constraintId,
            type: type.toLowerCase(),
            params: params,
            active: true,
            tolerance: this.precision,
            createdAt: Date.now(),
            iterations: 0,
            lastError: null
        };

        this.constraints.set(constraintId, constraint);
        console.log(`Added constraint: ${type}`, constraint);

        return constraintId;
    }

    /**
     * Remove a constraint
     * @param {string} constraintId - Constraint ID to remove
     */
    removeConstraint(constraintId) {
        if (this.constraints.has(constraintId)) {
            this.constraints.delete(constraintId);
            console.log(`Removed constraint: ${constraintId}`);
        }
    }

    /**
     * Solve all active constraints with enhanced convergence
     * @param {Array} objects - Array of objects to apply constraints to
     * @returns {Array} Updated objects
     */
    solveConstraints(objects) {
        if (this.solverActive) return objects; // Prevent recursive solving

        this.solverActive = true;
        let updatedObjects = [...objects];
        let iteration = 0;
        let maxError = Infinity;

        try {
            // Iterative constraint solving with convergence checking
            while (iteration < this.maxIterations && maxError > this.convergenceTolerance) {
                maxError = 0;

                for (const [constraintId, constraint] of this.constraints) {
                    if (constraint.active) {
                        const result = this.applyConstraint(constraint, updatedObjects);
                        updatedObjects = result.objects;
                        maxError = Math.max(maxError, result.error || 0);
                        constraint.iterations = iteration;
                    }
                }

                iteration++;
            }

            // Log solver statistics
            console.log(`Constraint solver completed in ${iteration} iterations with max error: ${maxError}`);

        } catch (error) {
            console.error('Constraint solving error:', error);
        } finally {
            this.solverActive = false;
        }

        return updatedObjects;
    }

    /**
     * Apply a specific constraint to objects with enhanced precision
     * @param {Object} constraint - Constraint to apply
     * @param {Array} objects - Objects to apply constraint to
     * @returns {Object} Result with updated objects and error
     */
    applyConstraint(constraint, objects) {
        let error = 0;
        let updatedObjects = [...objects];

        try {
            switch (constraint.type) {
                case 'distance':
                    const distanceResult = this.applyDistanceConstraint(constraint, updatedObjects);
                    updatedObjects = distanceResult.objects;
                    error = distanceResult.error;
                    break;

                case 'angle':
                    const angleResult = this.applyAngleConstraint(constraint, updatedObjects);
                    updatedObjects = angleResult.objects;
                    error = angleResult.error;
                    break;

                case 'parallel':
                    const parallelResult = this.applyParallelConstraint(constraint, updatedObjects);
                    updatedObjects = parallelResult.objects;
                    error = parallelResult.error;
                    break;

                case 'perpendicular':
                    const perpendicularResult = this.applyPerpendicularConstraint(constraint, updatedObjects);
                    updatedObjects = perpendicularResult.objects;
                    error = perpendicularResult.error;
                    break;

                case 'coincident':
                    const coincidentResult = this.applyCoincidentConstraint(constraint, updatedObjects);
                    updatedObjects = coincidentResult.objects;
                    error = coincidentResult.error;
                    break;

                case 'horizontal':
                    const horizontalResult = this.applyHorizontalConstraint(constraint, updatedObjects);
                    updatedObjects = horizontalResult.objects;
                    error = horizontalResult.error;
                    break;

                case 'vertical':
                    const verticalResult = this.applyVerticalConstraint(constraint, updatedObjects);
                    updatedObjects = verticalResult.objects;
                    error = verticalResult.error;
                    break;

                default:
                    console.warn(`Unknown constraint type: ${constraint.type}`);
            }

            constraint.lastError = error;

        } catch (error) {
            console.error(`Error applying constraint ${constraint.id}:`, error);
            constraint.lastError = Infinity;
        }

        return { objects: updatedObjects, error: error };
    }

    /**
     * Enhanced distance constraint with precision validation
     * @param {Object} constraint - Distance constraint
     * @param {Array} objects - Objects to apply constraint to
     * @returns {Object} Result with updated objects and error
     */
    applyDistanceConstraint(constraint, objects) {
        const { object1Id, object2Id, distance, tolerance = this.precision } = constraint.params;

        const obj1 = objects.find(obj => obj.id === object1Id);
        const obj2 = objects.find(obj => obj.id === object2Id);

        if (!obj1 || !obj2) {
            console.warn('Objects not found for distance constraint');
            return { objects: objects, error: Infinity };
        }

        // Calculate current distance
        const currentDistance = this.calculateDistance(obj1, obj2);
        const distanceDiff = Math.abs(currentDistance - distance);

        // Check if constraint is satisfied within tolerance
        if (distanceDiff <= tolerance) {
            console.log(`Distance constraint satisfied: ${currentDistance} ≈ ${distance} (tolerance: ${tolerance})`);
            return { objects: objects, error: 0 };
        }

        // Apply constraint by adjusting object positions
        const adjustmentFactor = (distance - currentDistance) / currentDistance;
        const dx = obj2.x - obj1.x;
        const dy = obj2.y - obj1.y;

        // Move second object to satisfy constraint
        const newX = obj1.x + dx * (1 + adjustmentFactor);
        const newY = obj1.y + dy * (1 + adjustmentFactor);

        // Apply precision to new coordinates
        const precisionX = Math.round(newX / this.precision) * this.precision;
        const precisionY = Math.round(newY / this.precision) * this.precision;

        obj2.x = precisionX;
        obj2.y = precisionY;

        console.log(`Applied distance constraint: ${currentDistance} → ${distance}`);
        return { objects: objects, error: distanceDiff };
    }

    /**
     * Enhanced angle constraint with precision validation
     * @param {Object} constraint - Angle constraint
     * @param {Array} objects - Objects to apply constraint to
     * @returns {Object} Result with updated objects and error
     */
    applyAngleConstraint(constraint, objects) {
        const { object1Id, object2Id, angle, tolerance = this.anglePrecision } = constraint.params;

        const obj1 = objects.find(obj => obj.id === object1Id);
        const obj2 = objects.find(obj => obj.id === object2Id);

        if (!obj1 || !obj2) {
            console.warn('Objects not found for angle constraint');
            return { objects: objects, error: Infinity };
        }

        // Calculate current angle
        const currentAngle = this.calculateAngle(obj1, obj2);
        const angleDiff = Math.abs(currentAngle - angle);

        // Normalize angle difference
        const normalizedDiff = Math.min(angleDiff, 360 - angleDiff);

        // Check if constraint is satisfied within tolerance
        if (normalizedDiff <= tolerance) {
            console.log(`Angle constraint satisfied: ${currentAngle}° ≈ ${angle}° (tolerance: ${tolerance}°)`);
            return { objects: objects, error: 0 };
        }

        // Apply constraint by rotating second object
        const rotationAngle = angle - currentAngle;
        const center = { x: obj1.x, y: obj1.y };

        this.rotateObject(obj2, center, rotationAngle);

        console.log(`Applied angle constraint: ${currentAngle}° → ${angle}°`);
        return { objects: objects, error: normalizedDiff };
    }

    /**
     * Enhanced parallel constraint with precision validation
     * @param {Object} constraint - Parallel constraint
     * @param {Array} objects - Objects to apply constraint to
     * @returns {Object} Result with updated objects and error
     */
    applyParallelConstraint(constraint, objects) {
        const { object1Id, object2Id, tolerance = this.anglePrecision } = constraint.params;

        const obj1 = objects.find(obj => obj.id === object1Id);
        const obj2 = objects.find(obj => obj.id === object2Id);

        if (!obj1 || !obj2) {
            console.warn('Objects not found for parallel constraint');
            return { objects: objects, error: Infinity };
        }

        // Calculate angles of both objects
        const angle1 = this.getObjectAngle(obj1);
        const angle2 = this.getObjectAngle(obj2);

        // Check if objects are already parallel
        const angleDiff = Math.abs(angle1 - angle2);
        const normalizedDiff = Math.min(angleDiff, 180 - angleDiff);

        if (normalizedDiff <= tolerance) {
            console.log(`Parallel constraint satisfied: ${angle1}° ≈ ${angle2}° (tolerance: ${tolerance}°)`);
            return { objects: objects, error: 0 };
        }

        // Make objects parallel by adjusting second object's angle
        const targetAngle = angle1;
        this.setObjectAngle(obj2, targetAngle);

        console.log(`Applied parallel constraint: ${angle2}° → ${targetAngle}°`);
        return { objects: objects, error: normalizedDiff };
    }

    /**
     * Enhanced perpendicular constraint with precision validation
     * @param {Object} constraint - Perpendicular constraint
     * @param {Array} objects - Objects to apply constraint to
     * @returns {Object} Result with updated objects and error
     */
    applyPerpendicularConstraint(constraint, objects) {
        const { object1Id, object2Id, tolerance = this.anglePrecision } = constraint.params;

        const obj1 = objects.find(obj => obj.id === object1Id);
        const obj2 = objects.find(obj => obj.id === object2Id);

        if (!obj1 || !obj2) {
            console.warn('Objects not found for perpendicular constraint');
            return { objects: objects, error: Infinity };
        }

        // Calculate angles of both objects
        const angle1 = this.getObjectAngle(obj1);
        const angle2 = this.getObjectAngle(obj2);

        // Calculate target perpendicular angle
        const targetAngle = angle1 + 90;
        const normalizedTargetAngle = ((targetAngle % 360) + 360) % 360;

        // Check if objects are already perpendicular
        const angleDiff = Math.abs(angle2 - normalizedTargetAngle);
        const normalizedDiff = Math.min(angleDiff, 180 - angleDiff);

        if (normalizedDiff <= tolerance) {
            console.log(`Perpendicular constraint satisfied: ${angle2}° ≈ ${normalizedTargetAngle}° (tolerance: ${tolerance}°)`);
            return { objects: objects, error: 0 };
        }

        // Make objects perpendicular by adjusting second object's angle
        this.setObjectAngle(obj2, normalizedTargetAngle);

        console.log(`Applied perpendicular constraint: ${angle2}° → ${normalizedTargetAngle}°`);
        return { objects: objects, error: normalizedDiff };
    }

    /**
     * Enhanced coincident constraint with precision validation
     * @param {Object} constraint - Coincident constraint
     * @param {Array} objects - Objects to apply constraint to
     * @returns {Object} Result with updated objects and error
     */
    applyCoincidentConstraint(constraint, objects) {
        const { object1Id, object2Id, tolerance = this.precision } = constraint.params;

        const obj1 = objects.find(obj => obj.id === object1Id);
        const obj2 = objects.find(obj => obj.id === object2Id);

        if (!obj1 || !obj2) {
            console.warn('Objects not found for coincident constraint');
            return { objects: objects, error: Infinity };
        }

        // Calculate distance between objects
        const distance = this.calculateDistance(obj1, obj2);

        // Check if objects are already coincident
        if (distance <= tolerance) {
            console.log(`Coincident constraint satisfied: distance ${distance} ≤ ${tolerance}`);
            return { objects: objects, error: 0 };
        }

        // Make objects coincident by moving second object to first object's position
        obj2.x = obj1.x;
        obj2.y = obj1.y;

        console.log(`Applied coincident constraint: moved object ${object2Id} to ${object1Id}`);
        return { objects: objects, error: distance };
    }

    /**
     * Enhanced horizontal constraint with precision validation
     * @param {Object} constraint - Horizontal constraint
     * @param {Array} objects - Objects to apply constraint to
     * @returns {Object} Result with updated objects and error
     */
    applyHorizontalConstraint(constraint, objects) {
        const { objectId, tolerance = this.anglePrecision } = constraint.params;

        const obj = objects.find(obj => obj.id === objectId);
        if (!obj) {
            console.warn('Object not found for horizontal constraint');
            return { objects: objects, error: Infinity };
        }

        // Get current angle
        const currentAngle = this.getObjectAngle(obj);

        // Check if object is already horizontal
        const angleDiff = Math.abs(currentAngle - 0);
        const normalizedDiff = Math.min(angleDiff, 180 - angleDiff);

        if (normalizedDiff <= tolerance) {
            console.log(`Horizontal constraint satisfied: ${currentAngle}° ≈ 0° (tolerance: ${tolerance}°)`);
            return { objects: objects, error: 0 };
        }

        // Make object horizontal
        this.setObjectAngle(obj, 0);

        console.log(`Applied horizontal constraint: ${currentAngle}° → 0°`);
        return { objects: objects, error: normalizedDiff };
    }

    /**
     * Enhanced vertical constraint with precision validation
     * @param {Object} constraint - Vertical constraint
     * @param {Array} objects - Objects to apply constraint to
     * @returns {Object} Result with updated objects and error
     */
    applyVerticalConstraint(constraint, objects) {
        const { objectId, tolerance = this.anglePrecision } = constraint.params;

        const obj = objects.find(obj => obj.id === objectId);
        if (!obj) {
            console.warn('Object not found for vertical constraint');
            return { objects: objects, error: Infinity };
        }

        // Get current angle
        const currentAngle = this.getObjectAngle(obj);

        // Check if object is already vertical
        const angleDiff = Math.abs(currentAngle - 90);
        const normalizedDiff = Math.min(angleDiff, 180 - angleDiff);

        if (normalizedDiff <= tolerance) {
            console.log(`Vertical constraint satisfied: ${currentAngle}° ≈ 90° (tolerance: ${tolerance}°)`);
            return { objects: objects, error: 0 };
        }

        // Make object vertical
        this.setObjectAngle(obj, 90);

        console.log(`Applied vertical constraint: ${currentAngle}° → 90°`);
        return { objects: objects, error: normalizedDiff };
    }

    /**
     * Calculate distance between two objects
     * @param {Object} obj1 - First object
     * @param {Object} obj2 - Second object
     * @returns {number} Distance
     */
    calculateDistance(obj1, obj2) {
        const dx = obj2.x - obj1.x;
        const dy = obj2.y - obj1.y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    /**
     * Calculate angle between two objects
     * @param {Object} obj1 - First object
     * @param {Object} obj2 - Second object
     * @returns {number} Angle in degrees
     */
    calculateAngle(obj1, obj2) {
        return Math.atan2(obj2.y - obj1.y, obj2.x - obj1.x) * 180 / Math.PI;
    }

    /**
     * Get direction vector between two objects
     * @param {Object} obj1 - First object
     * @param {Object} obj2 - Second object
     * @returns {Object} Direction vector
     */
    getDirection(obj1, obj2) {
        const distance = this.calculateDistance(obj1, obj2);
        if (distance === 0) return { x: 0, y: 0 };

        return {
            x: (obj2.x - obj1.x) / distance,
            y: (obj2.y - obj1.y) / distance
        };
    }

    /**
     * Get angle of an object
     * @param {Object} obj - Object to get angle for
     * @returns {number} Angle in degrees
     */
    getObjectAngle(obj) {
        // This would depend on the object type and structure
        // For now, assume objects have an angle property
        return obj.angle || 0;
    }

    /**
     * Set angle of an object
     * @param {Object} obj - Object to set angle for
     * @param {number} angle - Angle in degrees
     */
    setObjectAngle(obj, angle) {
        obj.angle = angle;
        // Additional logic for rotating object geometry would go here
    }

    /**
     * Rotate an object around a center point
     * @param {Object} obj - Object to rotate
     * @param {Object} center - Center point
     * @param {number} angle - Angle in degrees
     */
    rotateObject(obj, center, angle) {
        const radians = angle * Math.PI / 180;
        const cos = Math.cos(radians);
        const sin = Math.sin(radians);

        const dx = obj.x - center.x;
        const dy = obj.y - center.y;

        obj.x = center.x + dx * cos - dy * sin;
        obj.y = center.y + dx * sin + dy * cos;

        // Update object angle
        obj.angle = (obj.angle || 0) + angle;
    }

    /**
     * Validate constraint parameters
     * @param {string} type - Constraint type
     * @param {Object} params - Constraint parameters
     * @returns {boolean} True if valid
     */
    validateConstraint(type, params) {
        switch (type) {
            case this.constraintTypes.DISTANCE:
                return params.object1Id && params.object2Id && typeof params.distance === 'number';
            case this.constraintTypes.ANGLE:
                return params.object1Id && params.object2Id && typeof params.angle === 'number';
            case this.constraintTypes.PARALLEL:
            case this.constraintTypes.PERPENDICULAR:
                return params.object1Id && params.object2Id;
            case this.constraintTypes.COINCIDENT:
                return params.object1Id && params.object2Id && params.point;
            case this.constraintTypes.HORIZONTAL:
            case this.constraintTypes.VERTICAL:
                return params.objectId;
            default:
                return false;
        }
    }

    /**
     * Get all constraints for an object
     * @param {string} objectId - Object ID
     * @returns {Array} Array of constraints
     */
    getConstraintsForObject(objectId) {
        const objectConstraints = [];

        for (const [constraintId, constraint] of this.constraints) {
            if (constraint.params.object1Id === objectId ||
                constraint.params.object2Id === objectId ||
                constraint.params.objectId === objectId) {
                objectConstraints.push(constraint);
            }
        }

        return objectConstraints;
    }

    /**
     * Clear all constraints
     */
    clearConstraints() {
        this.constraints.clear();
        console.log('All constraints cleared');
    }

    /**
     * Get constraint statistics
     * @returns {Object} Constraint statistics
     */
    getStatistics() {
        const stats = {
            total: this.constraints.size,
            byType: {},
            active: 0
        };

        for (const [constraintId, constraint] of this.constraints) {
            if (constraint.active) stats.active++;

            if (!stats.byType[constraint.type]) {
                stats.byType[constraint.type] = 0;
            }
            stats.byType[constraint.type]++;
        }

        return stats;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConstraintSolver;
}
