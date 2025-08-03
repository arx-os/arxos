/**
 * Arxos CAD Constraint System
 * Handles geometric constraints for CAD-level precision and relationships
 * 
 * @author Arxos Team
 * @version 1.0.0
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
        
        // Precision settings
        this.precision = 0.001; // 0.001 inches
        this.anglePrecision = 0.1; // 0.1 degrees
    }

    /**
     * Add a geometric constraint
     * @param {string} type - Constraint type
     * @param {Object} params - Constraint parameters
     * @returns {string} Constraint ID
     */
    addConstraint(type, params) {
        const constraintId = `constraint_${++this.constraintId}`;
        
        const constraint = {
            id: constraintId,
            type: type,
            params: params,
            active: true,
            tolerance: this.precision,
            createdAt: Date.now()
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
     * Solve all active constraints
     * @param {Array} objects - Array of objects to apply constraints to
     * @returns {Array} Updated objects
     */
    solveConstraints(objects) {
        if (this.solverActive) return objects; // Prevent recursive solving
        
        this.solverActive = true;
        const updatedObjects = [...objects];
        
        try {
            for (const [constraintId, constraint] of this.constraints) {
                if (constraint.active) {
                    updatedObjects = this.applyConstraint(constraint, updatedObjects);
                }
            }
        } catch (error) {
            console.error('Constraint solving error:', error);
        } finally {
            this.solverActive = false;
        }
        
        return updatedObjects;
    }

    /**
     * Apply a specific constraint to objects
     * @param {Object} constraint - Constraint to apply
     * @param {Array} objects - Objects to apply constraint to
     * @returns {Array} Updated objects
     */
    applyConstraint(constraint, objects) {
        switch (constraint.type) {
            case this.constraintTypes.DISTANCE:
                return this.applyDistanceConstraint(constraint, objects);
            case this.constraintTypes.ANGLE:
                return this.applyAngleConstraint(constraint, objects);
            case this.constraintTypes.PARALLEL:
                return this.applyParallelConstraint(constraint, objects);
            case this.constraintTypes.PERPENDICULAR:
                return this.applyPerpendicularConstraint(constraint, objects);
            case this.constraintTypes.COINCIDENT:
                return this.applyCoincidentConstraint(constraint, objects);
            case this.constraintTypes.HORIZONTAL:
                return this.applyHorizontalConstraint(constraint, objects);
            case this.constraintTypes.VERTICAL:
                return this.applyVerticalConstraint(constraint, objects);
            default:
                console.warn(`Unknown constraint type: ${constraint.type}`);
                return objects;
        }
    }

    /**
     * Apply distance constraint
     * @param {Object} constraint - Distance constraint
     * @param {Array} objects - Objects to apply to
     * @returns {Array} Updated objects
     */
    applyDistanceConstraint(constraint, objects) {
        const { object1Id, object2Id, distance } = constraint.params;
        
        const obj1 = objects.find(obj => obj.id === object1Id);
        const obj2 = objects.find(obj => obj.id === object2Id);
        
        if (!obj1 || !obj2) return objects;
        
        const currentDistance = this.calculateDistance(obj1, obj2);
        const difference = distance - currentDistance;
        
        if (Math.abs(difference) > this.precision) {
            // Adjust objects to meet distance constraint
            const direction = this.getDirection(obj1, obj2);
            const adjustment = difference / 2;
            
            obj1.x -= direction.x * adjustment;
            obj1.y -= direction.y * adjustment;
            obj2.x += direction.x * adjustment;
            obj2.y += direction.y * adjustment;
        }
        
        return objects;
    }

    /**
     * Apply angle constraint
     * @param {Object} constraint - Angle constraint
     * @param {Array} objects - Objects to apply to
     * @returns {Array} Updated objects
     */
    applyAngleConstraint(constraint, objects) {
        const { object1Id, object2Id, angle } = constraint.params;
        
        const obj1 = objects.find(obj => obj.id === object1Id);
        const obj2 = objects.find(obj => obj.id === object2Id);
        
        if (!obj1 || !obj2) return objects;
        
        const currentAngle = this.calculateAngle(obj1, obj2);
        const angleDifference = angle - currentAngle;
        
        if (Math.abs(angleDifference) > this.anglePrecision) {
            // Rotate objects to meet angle constraint
            this.rotateObject(obj2, obj1, angleDifference);
        }
        
        return objects;
    }

    /**
     * Apply parallel constraint
     * @param {Object} constraint - Parallel constraint
     * @param {Array} objects - Objects to apply to
     * @returns {Array} Updated objects
     */
    applyParallelConstraint(constraint, objects) {
        const { object1Id, object2Id } = constraint.params;
        
        const obj1 = objects.find(obj => obj.id === object1Id);
        const obj2 = objects.find(obj => obj.id === object2Id);
        
        if (!obj1 || !obj2) return objects;
        
        const angle1 = this.getObjectAngle(obj1);
        const angle2 = this.getObjectAngle(obj2);
        const angleDifference = angle1 - angle2;
        
        // Make objects parallel (0 or 180 degrees)
        const targetAngle = Math.abs(angleDifference) > 90 ? angle1 + 180 : angle1;
        this.setObjectAngle(obj2, targetAngle);
        
        return objects;
    }

    /**
     * Apply perpendicular constraint
     * @param {Object} constraint - Perpendicular constraint
     * @param {Array} objects - Objects to apply to
     * @returns {Array} Updated objects
     */
    applyPerpendicularConstraint(constraint, objects) {
        const { object1Id, object2Id } = constraint.params;
        
        const obj1 = objects.find(obj => obj.id === object1Id);
        const obj2 = objects.find(obj => obj.id === object2Id);
        
        if (!obj1 || !obj2) return objects;
        
        const angle1 = this.getObjectAngle(obj1);
        const targetAngle = angle1 + 90; // Perpendicular angle
        this.setObjectAngle(obj2, targetAngle);
        
        return objects;
    }

    /**
     * Apply coincident constraint
     * @param {Object} constraint - Coincident constraint
     * @param {Array} objects - Objects to apply to
     * @returns {Array} Updated objects
     */
    applyCoincidentConstraint(constraint, objects) {
        const { object1Id, object2Id, point } = constraint.params;
        
        const obj1 = objects.find(obj => obj.id === object1Id);
        const obj2 = objects.find(obj => obj.id === object2Id);
        
        if (!obj1 || !obj2) return objects;
        
        // Move objects to be coincident at the specified point
        obj1.x = point.x;
        obj1.y = point.y;
        obj2.x = point.x;
        obj2.y = point.y;
        
        return objects;
    }

    /**
     * Apply horizontal constraint
     * @param {Object} constraint - Horizontal constraint
     * @param {Array} objects - Objects to apply to
     * @returns {Array} Updated objects
     */
    applyHorizontalConstraint(constraint, objects) {
        const { objectId } = constraint.params;
        
        const obj = objects.find(obj => obj.id === objectId);
        if (!obj) return objects;
        
        // Make object horizontal (0 degrees)
        this.setObjectAngle(obj, 0);
        
        return objects;
    }

    /**
     * Apply vertical constraint
     * @param {Object} constraint - Vertical constraint
     * @param {Array} objects - Objects to apply to
     * @returns {Array} Updated objects
     */
    applyVerticalConstraint(constraint, objects) {
        const { objectId } = constraint.params;
        
        const obj = objects.find(obj => obj.id === objectId);
        if (!obj) return objects;
        
        // Make object vertical (90 degrees)
        this.setObjectAngle(obj, 90);
        
        return objects;
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