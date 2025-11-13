/**
 * Context Linking Utilities
 *
 * Utilities for linking collaboration messages to building elements
 * and vice versa (bi-directional context awareness).
 */

import type {
  ElementReference,
  CollaborationMessage,
  ElementType,
} from "../types";

/**
 * Create an element reference from floor plan data
 */
export function createElementReference(
  type: ElementType,
  id: string,
  options?: {
    name?: string;
    buildingPath?: string;
    floorId?: string;
  }
): ElementReference {
  return {
    type,
    id,
    name: options?.name,
    buildingPath: options?.buildingPath,
    floorId: options?.floorId,
  };
}

/**
 * Check if a message has an element reference
 */
export function hasElementReference(
  message: CollaborationMessage
): boolean {
  return (
    message.envelope.type === "comment" &&
    "elementRef" in (message.envelope.payload || {})
  );
}

/**
 * Extract element reference from a message
 */
export function getElementReference(
  message: CollaborationMessage
): ElementReference | null {
  if (!hasElementReference(message)) {
    return null;
  }

  const payload = message.envelope.payload as {
    elementRef?: ElementReference;
  };
  return payload.elementRef || null;
}

/**
 * Filter messages by element reference
 */
export function filterMessagesByElement(
  messages: CollaborationMessage[],
  elementRef: ElementReference
): CollaborationMessage[] {
  return messages.filter((message) => {
    const ref = getElementReference(message);
    if (!ref) return false;

    return (
      ref.type === elementRef.type &&
      ref.id === elementRef.id &&
      (elementRef.floorId ? ref.floorId === elementRef.floorId : true) &&
      (elementRef.buildingPath
        ? ref.buildingPath === elementRef.buildingPath
        : true)
    );
  });
}

/**
 * Group messages by element type
 */
export function groupMessagesByElementType(
  messages: CollaborationMessage[]
): Map<ElementType, CollaborationMessage[]> {
  const groups = new Map<ElementType, CollaborationMessage[]>();

  messages.forEach((message) => {
    const ref = getElementReference(message);
    if (!ref) return;

    const existing = groups.get(ref.type) || [];
    groups.set(ref.type, [...existing, message]);
  });

  return groups;
}

/**
 * Get all unique element references from messages
 */
export function extractElementReferences(
  messages: CollaborationMessage[]
): ElementReference[] {
  const refs: ElementReference[] = [];
  const seen = new Set<string>();

  messages.forEach((message) => {
    const ref = getElementReference(message);
    if (!ref) return;

    const key = `${ref.type}:${ref.id}:${ref.floorId || ""}:${ref.buildingPath || ""}`;
    if (!seen.has(key)) {
      seen.add(key);
      refs.push(ref);
    }
  });

  return refs;
}

/**
 * Count messages per element reference
 */
export function countMessagesByElement(
  messages: CollaborationMessage[]
): Map<string, number> {
  const counts = new Map<string, number>();

  messages.forEach((message) => {
    const ref = getElementReference(message);
    if (!ref) return;

    const key = `${ref.type}:${ref.id}`;
    counts.set(key, (counts.get(key) || 0) + 1);
  });

  return counts;
}

/**
 * Format element reference for display
 */
export function formatElementReference(ref: ElementReference): string {
  const parts: string[] = [];

  if (ref.buildingPath) {
    parts.push(ref.buildingPath);
  }

  if (ref.floorId) {
    parts.push(`Floor ${ref.floorId}`);
  }

  parts.push(`${ref.type}: ${ref.name || ref.id}`);

  return parts.join(" → ");
}

/**
 * Check if two element references match
 */
export function matchesElementReference(
  ref1: ElementReference,
  ref2: ElementReference
): boolean {
  return (
    ref1.type === ref2.type &&
    ref1.id === ref2.id &&
    ref1.floorId === ref2.floorId &&
    ref1.buildingPath === ref2.buildingPath
  );
}

/**
 * Parse element ID from various formats
 * (e.g., "room:123", "equipment-abc", etc.)
 */
export function parseElementId(elementId: string): {
  type: ElementType | null;
  id: string;
} {
  const patterns: Array<{ regex: RegExp; type: ElementType }> = [
    { regex: /^room[:\-_](.+)$/i, type: "room" },
    { regex: /^equipment[:\-_](.+)$/i, type: "equipment" },
    { regex: /^floor[:\-_](.+)$/i, type: "floor" },
    { regex: /^building[:\-_](.+)$/i, type: "building" },
    { regex: /^wall[:\-_](.+)$/i, type: "wall" },
    { regex: /^door[:\-_](.+)$/i, type: "door" },
    { regex: /^window[:\-_](.+)$/i, type: "window" },
  ];

  for (const { regex, type } of patterns) {
    const match = elementId.match(regex);
    if (match) {
      return { type, id: match[1] };
    }
  }

  return { type: null, id: elementId };
}
