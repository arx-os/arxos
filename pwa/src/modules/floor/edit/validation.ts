/**
 * Client-side validation for edit operations
 *
 * Validates edit operations before sending them to the agent
 * to catch common errors early and provide better UX.
 */

import type { AnyEditOperation } from "./operations";
import type { Room, Equipment } from "../../../lib/wasm/geometry";

/**
 * Validation result
 */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

/**
 * Create a successful validation result
 */
function createValidResult(): ValidationResult {
  return {
    valid: true,
    errors: [],
    warnings: [],
  };
}

/**
 * Create a failed validation result
 */
function createInvalidResult(errors: string[]): ValidationResult {
  return {
    valid: false,
    errors,
    warnings: [],
  };
}

/**
 * Add a warning to a validation result
 */
function addWarning(
  result: ValidationResult,
  warning: string
): ValidationResult {
  return {
    ...result,
    warnings: [...result.warnings, warning],
  };
}

/**
 * Validate room dimensions
 */
function validateRoomDimensions(
  width: number,
  height: number
): ValidationResult {
  const errors: string[] = [];

  // Check minimum dimensions (e.g., 0.5m x 0.5m)
  const MIN_DIMENSION = 0.5;
  if (width < MIN_DIMENSION) {
    errors.push(`Room width must be at least ${MIN_DIMENSION}m`);
  }
  if (height < MIN_DIMENSION) {
    errors.push(`Room height must be at least ${MIN_DIMENSION}m`);
  }

  // Check maximum dimensions (e.g., 100m x 100m)
  const MAX_DIMENSION = 100;
  if (width > MAX_DIMENSION) {
    errors.push(`Room width cannot exceed ${MAX_DIMENSION}m`);
  }
  if (height > MAX_DIMENSION) {
    errors.push(`Room height cannot exceed ${MAX_DIMENSION}m`);
  }

  if (errors.length > 0) {
    return createInvalidResult(errors);
  }

  let result = createValidResult();

  // Add warnings for unusual dimensions
  if (width > 50 || height > 50) {
    result = addWarning(result, "Large room dimensions detected");
  }

  return result;
}

/**
 * Validate room position
 */
function validateRoomPosition(x: number, y: number): ValidationResult {
  const errors: string[] = [];

  // Check for valid coordinates (not NaN or Infinity)
  if (!Number.isFinite(x) || !Number.isFinite(y)) {
    errors.push("Room position must be valid finite numbers");
  }

  // Check bounds (e.g., -1000m to 1000m)
  const MAX_COORDINATE = 1000;
  if (Math.abs(x) > MAX_COORDINATE || Math.abs(y) > MAX_COORDINATE) {
    errors.push(`Room position out of bounds (max ±${MAX_COORDINATE}m)`);
  }

  if (errors.length > 0) {
    return createInvalidResult(errors);
  }

  return createValidResult();
}

/**
 * Validate equipment position
 */
function validateEquipmentPosition(
  x: number,
  y: number,
  z: number
): ValidationResult {
  const errors: string[] = [];

  // Check for valid coordinates
  if (
    !Number.isFinite(x) ||
    !Number.isFinite(y) ||
    !Number.isFinite(z)
  ) {
    errors.push("Equipment position must be valid finite numbers");
  }

  // Check bounds
  const MAX_COORDINATE = 1000;
  if (
    Math.abs(x) > MAX_COORDINATE ||
    Math.abs(y) > MAX_COORDINATE ||
    Math.abs(z) > MAX_COORDINATE
  ) {
    errors.push(`Equipment position out of bounds (max ±${MAX_COORDINATE}m)`);
  }

  if (errors.length > 0) {
    return createInvalidResult(errors);
  }

  return createValidResult();
}

/**
 * Validate an edit operation
 */
export function validateOperation(
  operation: AnyEditOperation
): ValidationResult {
  switch (operation.type) {
    case "add-room": {
      const room = operation.room;
      const errors: string[] = [];

      // Validate required fields
      if (!room.name) {
        errors.push("Room name is required");
      }

      if (errors.length > 0) {
        return createInvalidResult(errors);
      }

      // Validate bounds if provided
      if (room.bounds) {
        const { min, max } = room.bounds;
        if (min && max) {
          // Calculate dimensions from bounds
          const width = max.x - min.x;
          const height = max.y - min.y;
          const dimResult = validateRoomDimensions(width, height);
          if (!dimResult.valid) {
            return dimResult;
          }

          // Validate position (center or min point)
          const posResult = validateRoomPosition(min.x, min.y);
          if (!posResult.valid) {
            return posResult;
          }
        }
      }

      return createValidResult();
    }

    case "delete-room": {
      if (!operation.roomId) {
        return createInvalidResult(["Room ID is required"]);
      }
      return createValidResult();
    }

    case "move-room": {
      const errors: string[] = [];

      if (!operation.roomId) {
        errors.push("Room ID is required");
      }

      if (errors.length > 0) {
        return createInvalidResult(errors);
      }

      return validateRoomPosition(operation.toX, operation.toY);
    }

    case "resize-room": {
      const errors: string[] = [];

      if (!operation.roomId) {
        errors.push("Room ID is required");
      }

      if (errors.length > 0) {
        return createInvalidResult(errors);
      }

      return validateRoomDimensions(
        operation.toWidth,
        operation.toHeight
      );
    }

    case "add-equipment": {
      const equipment = operation.equipment;
      const errors: string[] = [];

      // Validate required fields
      if (!equipment.name) {
        errors.push("Equipment name is required");
      }

      if (errors.length > 0) {
        return createInvalidResult(errors);
      }

      // Validate position if provided
      if (equipment.position) {
        const { x, y, z = 0 } = equipment.position;
        const posResult = validateEquipmentPosition(x, y, z);
        if (!posResult.valid) {
          return posResult;
        }
      }

      return createValidResult();
    }

    case "delete-equipment": {
      if (!operation.equipmentId) {
        return createInvalidResult(["Equipment ID is required"]);
      }
      return createValidResult();
    }

    case "move-equipment": {
      const errors: string[] = [];

      if (!operation.equipmentId) {
        errors.push("Equipment ID is required");
      }

      if (errors.length > 0) {
        return createInvalidResult(errors);
      }

      return validateEquipmentPosition(
        operation.toX,
        operation.toY,
        operation.toZ
      );
    }

    default:
      // Wall operations not yet implemented
      return createValidResult();
  }
}

/**
 * Validate a batch of operations
 */
export function validateBatch(
  operations: AnyEditOperation[]
): ValidationResult {
  const allErrors: string[] = [];
  const allWarnings: string[] = [];

  for (const operation of operations) {
    const result = validateOperation(operation);
    if (!result.valid) {
      allErrors.push(
        `Operation ${operation.id}: ${result.errors.join(", ")}`
      );
    }
    if (result.warnings.length > 0) {
      allWarnings.push(
        `Operation ${operation.id}: ${result.warnings.join(", ")}`
      );
    }
  }

  if (allErrors.length > 0) {
    return {
      valid: false,
      errors: allErrors,
      warnings: allWarnings,
    };
  }

  return {
    valid: true,
    errors: [],
    warnings: allWarnings,
  };
}
