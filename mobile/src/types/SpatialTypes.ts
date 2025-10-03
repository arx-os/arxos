/**
 * Spatial Types - Core spatial data structures for AR functionality
 * Implements Clean Architecture with domain-driven design
 */

export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

export interface Quaternion {
  x: number;
  y: number;
  z: number;
  w: number;
}

export interface Matrix4 {
  elements: number[];
}

export interface BoundingBox {
  min: Vector3;
  max: Vector3;
}

export interface Plane {
  normal: Vector3;
  distance: number;
}

export interface Ray {
  origin: Vector3;
  direction: Vector3;
}

export interface Transform {
  position: Vector3;
  rotation: Quaternion;
  scale: Vector3;
}

export interface SpatialBounds {
  center: Vector3;
  size: Vector3;
  rotation: Quaternion;
}

export interface SpatialRegion {
  id: string;
  bounds: SpatialBounds;
  type: 'room' | 'floor' | 'building' | 'equipment';
  metadata?: Record<string, any>;
}

export interface SpatialQuery {
  center: Vector3;
  radius: number;
  filters?: {
    type?: string;
    status?: string;
    buildingId?: string;
    floorId?: string;
  };
}

export interface SpatialResult<T> {
  items: T[];
  totalCount: number;
  queryTime: number;
  spatialAccuracy: number;
}

// Utility functions for spatial calculations
export class SpatialUtils {
  static distance(a: Vector3, b: Vector3): number {
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    const dz = a.z - b.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }
  
  static normalize(vector: Vector3): Vector3 {
    const length = Math.sqrt(vector.x * vector.x + vector.y * vector.y + vector.z * vector.z);
    if (length === 0) {
      return { x: 0, y: 0, z: 0 };
    }
    return {
      x: vector.x / length,
      y: vector.y / length,
      z: vector.z / length
    };
  }
  
  static dot(a: Vector3, b: Vector3): number {
    return a.x * b.x + a.y * b.y + a.z * b.z;
  }
  
  static cross(a: Vector3, b: Vector3): Vector3 {
    return {
      x: a.y * b.z - a.z * b.y,
      y: a.z * b.x - a.x * b.z,
      z: a.x * b.y - a.y * b.x
    };
  }
  
  static lerp(a: Vector3, b: Vector3, t: number): Vector3 {
    return {
      x: a.x + (b.x - a.x) * t,
      y: a.y + (b.y - a.y) * t,
      z: a.z + (b.z - a.z) * t
    };
  }
  
  static isPointInBounds(point: Vector3, bounds: BoundingBox): boolean {
    return point.x >= bounds.min.x && point.x <= bounds.max.x &&
           point.y >= bounds.min.y && point.y <= bounds.max.y &&
           point.z >= bounds.min.z && point.z <= bounds.max.z;
  }
  
  static calculateBounds(points: Vector3[]): BoundingBox {
    if (points.length === 0) {
      return { min: { x: 0, y: 0, z: 0 }, max: { x: 0, y: 0, z: 0 } };
    }
    
    let minX = points[0].x, minY = points[0].y, minZ = points[0].z;
    let maxX = points[0].x, maxY = points[0].y, maxZ = points[0].z;
    
    for (const point of points) {
      minX = Math.min(minX, point.x);
      minY = Math.min(minY, point.y);
      minZ = Math.min(minZ, point.z);
      maxX = Math.max(maxX, point.x);
      maxY = Math.max(maxY, point.y);
      maxZ = Math.max(maxZ, point.z);
    }
    
    return {
      min: { x: minX, y: minY, z: minZ },
      max: { x: maxX, y: maxY, z: maxZ }
    };
  }
  
  static quaternionFromEuler(x: number, y: number, z: number): Quaternion {
    const c1 = Math.cos(x / 2);
    const s1 = Math.sin(x / 2);
    const c2 = Math.cos(y / 2);
    const s2 = Math.sin(y / 2);
    const c3 = Math.cos(z / 2);
    const s3 = Math.sin(z / 2);
    
    return {
      x: s1 * c2 * c3 - c1 * s2 * s3,
      y: c1 * s2 * c3 + s1 * c2 * s3,
      z: c1 * c2 * s3 - s1 * s2 * c3,
      w: c1 * c2 * c3 + s1 * s2 * s3
    };
  }
  
  static eulerFromQuaternion(q: Quaternion): Vector3 {
    const x = Math.atan2(2 * (q.w * q.x + q.y * q.z), 1 - 2 * (q.x * q.x + q.y * q.y));
    const y = Math.asin(2 * (q.w * q.y - q.z * q.x));
    const z = Math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z));
    
    return { x, y, z };
  }
  
  static transformPoint(point: Vector3, transform: Transform): Vector3 {
    // Apply rotation
    const rotated = this.rotatePoint(point, transform.rotation);
    
    // Apply scale
    const scaled = {
      x: rotated.x * transform.scale.x,
      y: rotated.y * transform.scale.y,
      z: rotated.z * transform.scale.z
    };
    
    // Apply translation
    return {
      x: scaled.x + transform.position.x,
      y: scaled.y + transform.position.y,
      z: scaled.z + transform.position.z
    };
  }
  
  static rotatePoint(point: Vector3, rotation: Quaternion): Vector3 {
    // Convert point to quaternion
    const pointQuat = { x: point.x, y: point.y, z: point.z, w: 0 };
    
    // Apply rotation: result = rotation * point * rotation^-1
    const rotated = this.multiplyQuaternions(
      this.multiplyQuaternions(rotation, pointQuat),
      this.inverseQuaternion(rotation)
    );
    
    return { x: rotated.x, y: rotated.y, z: rotated.z };
  }
  
  static multiplyQuaternions(a: Quaternion, b: Quaternion): Quaternion {
    return {
      x: a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
      y: a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
      z: a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
      w: a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z
    };
  }
  
  static inverseQuaternion(q: Quaternion): Quaternion {
    const lengthSquared = q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w;
    return {
      x: -q.x / lengthSquared,
      y: -q.y / lengthSquared,
      z: -q.z / lengthSquared,
      w: q.w / lengthSquared
    };
  }
}
