"""
Enhanced SVGX Models with ArxObject Integration

These models properly reference the Go ArxObject engine while maintaining
backward compatibility with existing SVGX code.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from svgx_engine.integration.arxobject_bridge import get_arxobject_bridge
from svgx_engine.models.svgx import (
    SVGXDocument as BaseSVGXDocument,
    SVGXElement as BaseSVGXElement,
    ArxObject as LegacyArxObject,
    ArxBehavior,
    ArxPhysics
)

# Import Go ArxObject types
from services.arxobject.client.python_client import (
    ArxObject as GoArxObject,
    ArxObjectGeometry
)


class ArxObjectReference:
    """
    Reference to a real ArxObject in the Go engine.
    
    This replaces the simple metadata approach with actual object references.
    """
    
    def __init__(self, object_id: Union[int, str]):
        """
        Initialize ArxObject reference.
        
        Args:
            object_id: ID of the ArxObject in the Go engine
        """
        self.object_id = int(object_id) if isinstance(object_id, str) else object_id
        self._cached_object: Optional[GoArxObject] = None
        self._cache_timestamp: Optional[datetime] = None
        self._bridge = get_arxobject_bridge()
    
    async def get_object(self, force_refresh: bool = False) -> Optional[GoArxObject]:
        """
        Get the actual ArxObject from the Go engine.
        
        Args:
            force_refresh: Force refresh from engine even if cached
            
        Returns:
            GoArxObject or None if not found
        """
        # Check cache (valid for 60 seconds)
        if not force_refresh and self._cached_object and self._cache_timestamp:
            age = (datetime.utcnow() - self._cache_timestamp).total_seconds()
            if age < 60:
                return self._cached_object
        
        # Fetch from Go engine
        try:
            self._cached_object = await self._bridge.client.get_object(self.object_id)
            self._cache_timestamp = datetime.utcnow()
            return self._cached_object
        except Exception as e:
            print(f"Failed to fetch ArxObject {self.object_id}: {e}")
            return None
    
    async def update(self, changes: Dict[str, Any]) -> bool:
        """
        Update the ArxObject in the Go engine.
        
        Args:
            changes: Properties to update
            
        Returns:
            True if successful
        """
        try:
            updated = await self._bridge.client.update_object(
                self.object_id,
                properties=changes
            )
            self._cached_object = updated
            self._cache_timestamp = datetime.utcnow()
            return True
        except Exception as e:
            print(f"Failed to update ArxObject {self.object_id}: {e}")
            return False
    
    async def validate(self) -> Dict[str, Any]:
        """
        Validate the ArxObject against constraints.
        
        Returns:
            Validation result
        """
        try:
            collisions = await self._bridge.client.check_collisions(self.object_id)
            return {
                'valid': len(collisions) == 0,
                'collisions': collisions
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    @property
    def id(self) -> int:
        """Get object ID."""
        return self.object_id
    
    def to_legacy(self) -> LegacyArxObject:
        """
        Convert to legacy ArxObject for backward compatibility.
        
        Returns:
            Legacy ArxObject with metadata
        """
        if self._cached_object:
            return LegacyArxObject(
                object_id=str(self.object_id),
                object_type=self._cached_object.type,
                properties=self._cached_object.properties or {},
                geometry={
                    'x': self._cached_object.geometry.x,
                    'y': self._cached_object.geometry.y,
                    'z': self._cached_object.geometry.z,
                    'width': self._cached_object.geometry.width,
                    'height': self._cached_object.geometry.height,
                    'length': self._cached_object.geometry.length,
                }
            )
        else:
            return LegacyArxObject(
                object_id=str(self.object_id),
                object_type='unknown',
                properties={}
            )


@dataclass
class EnhancedSVGXElement(BaseSVGXElement):
    """
    Enhanced SVGX element that references real ArxObjects.
    
    This maintains compatibility while adding powerful new capabilities.
    """
    
    arx_reference: Optional[ArxObjectReference] = None
    validation_state: Optional[Dict[str, Any]] = None
    sync_version: int = 0
    
    def __post_init__(self):
        """Initialize ArxObject reference if needed."""
        # If we have legacy arx_object, create reference
        if self.arx_object and self.arx_object.object_id:
            self.arx_reference = ArxObjectReference(self.arx_object.object_id)
    
    async def sync_with_engine(self) -> bool:
        """
        Synchronize element with Go ArxObject engine.
        
        Returns:
            True if sync successful
        """
        if not self.arx_reference:
            return False
        
        # Get latest from engine
        go_obj = await self.arx_reference.get_object(force_refresh=True)
        
        if go_obj:
            # Update position
            self.position = [go_obj.geometry.x, go_obj.geometry.y]
            
            # Update attributes
            self.attributes['x'] = str(go_obj.geometry.x)
            self.attributes['y'] = str(go_obj.geometry.y)
            self.attributes['arx:version'] = str(go_obj.version)
            
            # Update legacy arx_object if present
            if self.arx_object:
                self.arx_object.properties.update(go_obj.properties or {})
            
            self.sync_version = go_obj.version
            return True
        
        return False
    
    async def validate(self) -> Dict[str, Any]:
        """
        Validate element against ArxObject constraints.
        
        Returns:
            Validation result
        """
        if self.arx_reference:
            result = await self.arx_reference.validate()
            self.validation_state = result
            
            # Update visual state based on validation
            if not result['valid']:
                self.attributes['class'] = self.attributes.get('class', '') + ' invalid'
                self.attributes['arx:validation'] = 'failed'
            else:
                self.attributes['arx:validation'] = 'passed'
            
            return result
        
        return {'valid': True, 'message': 'No ArxObject reference'}
    
    async def update_in_engine(self, changes: Dict[str, Any]) -> bool:
        """
        Update the referenced ArxObject in the engine.
        
        Args:
            changes: Properties to update
            
        Returns:
            True if successful
        """
        if self.arx_reference:
            success = await self.arx_reference.update(changes)
            
            if success:
                # Re-sync to get updated state
                await self.sync_with_engine()
            
            return success
        
        return False
    
    def to_svg(self) -> str:
        """Convert to SVG string with ArxObject data."""
        svg = f'<{self.tag}'
        
        # Add all attributes
        for key, value in self.attributes.items():
            svg += f' {key}="{value}"'
        
        # Add ArxObject reference
        if self.arx_reference:
            svg += f' arx:ref="{self.arx_reference.id}"'
        
        # Add validation state
        if self.validation_state:
            if not self.validation_state['valid']:
                svg += ' class="invalid"'
        
        if self.children or self.content:
            svg += '>'
            
            if self.content:
                svg += self.content
            
            for child in self.children:
                if hasattr(child, 'to_svg'):
                    svg += child.to_svg()
            
            svg += f'</{self.tag}>'
        else:
            svg += '/>'
        
        return svg


@dataclass
class EnhancedSVGXDocument(BaseSVGXDocument):
    """
    Enhanced SVGX document with ArxObject engine integration.
    
    This document type can work with both legacy metadata and real ArxObjects.
    """
    
    enhanced_elements: List[EnhancedSVGXElement] = field(default_factory=list)
    arxobject_cache: Dict[int, GoArxObject] = field(default_factory=dict)
    sync_enabled: bool = True
    last_sync: Optional[datetime] = None
    
    async def sync_all_elements(self) -> Dict[str, Any]:
        """
        Synchronize all elements with ArxObject engine.
        
        Returns:
            Sync report
        """
        if not self.sync_enabled:
            return {'synced': 0, 'failed': 0, 'message': 'Sync disabled'}
        
        synced = 0
        failed = 0
        
        # Sync enhanced elements
        for element in self.enhanced_elements:
            if await element.sync_with_engine():
                synced += 1
            else:
                failed += 1
        
        # Also sync legacy elements if they have ArxObject data
        for element in self.elements:
            if element.arx_object and element.arx_object.object_id:
                # Convert to enhanced element
                enhanced = self._upgrade_element(element)
                if await enhanced.sync_with_engine():
                    synced += 1
                else:
                    failed += 1
        
        self.last_sync = datetime.utcnow()
        
        return {
            'synced': synced,
            'failed': failed,
            'timestamp': self.last_sync.isoformat()
        }
    
    async def validate_all(self) -> Dict[str, Any]:
        """
        Validate all elements against ArxObject constraints.
        
        Returns:
            Validation report
        """
        violations = []
        
        for element in self.enhanced_elements:
            result = await element.validate()
            if not result['valid']:
                violations.append({
                    'element_id': element.attributes.get('id'),
                    'arx_id': element.arx_reference.id if element.arx_reference else None,
                    'violations': result
                })
        
        return {
            'valid': len(violations) == 0,
            'violation_count': len(violations),
            'violations': violations
        }
    
    async def query_region(
        self,
        min_x: float, min_y: float,
        max_x: float, max_y: float
    ) -> List[EnhancedSVGXElement]:
        """
        Query ArxObjects in region and create elements.
        
        Args:
            min_x, min_y, max_x, max_y: Region bounds
            
        Returns:
            List of enhanced elements
        """
        bridge = get_arxobject_bridge()
        
        # Query from Go engine
        arxobjects = await bridge.client.query_region(
            min_x, min_y, 0,
            max_x, max_y, 100
        )
        
        elements = []
        for obj in arxobjects:
            # Convert to enhanced element
            element = await self._create_element_from_arxobject(obj)
            elements.append(element)
            
            # Cache the object
            self.arxobject_cache[obj.id] = obj
        
        return elements
    
    async def _create_element_from_arxobject(
        self,
        obj: GoArxObject
    ) -> EnhancedSVGXElement:
        """Create enhanced element from Go ArxObject."""
        # Determine SVG tag based on type
        tag = self._get_svg_tag(obj.type)
        
        element = EnhancedSVGXElement(
            tag=tag,
            attributes={
                'id': f'arx-{obj.id}',
                'x': str(obj.geometry.x),
                'y': str(obj.geometry.y),
                'width': str(obj.geometry.width),
                'height': str(obj.geometry.height),
                'class': self._get_css_class(obj.type),
                'arx:id': str(obj.id),
                'arx:type': obj.type,
                'arx:version': str(obj.version)
            },
            position=[obj.geometry.x, obj.geometry.y],
            arx_reference=ArxObjectReference(obj.id)
        )
        
        # Add legacy ArxObject for compatibility
        element.arx_object = LegacyArxObject(
            object_id=str(obj.id),
            object_type=obj.type,
            properties=obj.properties or {}
        )
        
        return element
    
    def _upgrade_element(self, element: BaseSVGXElement) -> EnhancedSVGXElement:
        """Upgrade legacy element to enhanced element."""
        enhanced = EnhancedSVGXElement(
            tag=element.tag,
            attributes=element.attributes,
            content=element.content,
            position=element.position,
            children=element.children,
            arx_object=element.arx_object,
            arx_behavior=element.arx_behavior,
            arx_physics=element.arx_physics
        )
        
        # Create ArxObject reference if possible
        if element.arx_object and element.arx_object.object_id:
            enhanced.arx_reference = ArxObjectReference(element.arx_object.object_id)
        
        return enhanced
    
    def _get_svg_tag(self, object_type: str) -> str:
        """Get SVG tag for object type."""
        if 'OUTLET' in object_type:
            return 'circle'
        elif 'PANEL' in object_type or 'WALL' in object_type:
            return 'rect'
        elif 'PIPE' in object_type or 'BEAM' in object_type:
            return 'line'
        return 'rect'
    
    def _get_css_class(self, object_type: str) -> str:
        """Get CSS class for object type."""
        if 'ELECTRICAL' in object_type:
            return 'electrical'
        elif 'STRUCTURAL' in object_type:
            return 'structural'
        elif 'PLUMBING' in object_type:
            return 'plumbing'
        return 'building-element'
    
    def to_svg(self) -> str:
        """Export document to SVG."""
        svg = '<?xml version="1.0" encoding="UTF-8"?>\n'
        svg += '<svg xmlns="http://www.w3.org/2000/svg" '
        svg += 'xmlns:arx="http://arxos.io/svgx">\n'
        
        # Add metadata
        if self.metadata:
            svg += '  <metadata>\n'
            for key, value in self.metadata.items():
                svg += f'    <{key}>{value}</{key}>\n'
            svg += '  </metadata>\n'
        
        # Add elements
        for element in self.enhanced_elements:
            svg += '  ' + element.to_svg() + '\n'
        
        for element in self.elements:
            if hasattr(element, 'to_svg'):
                svg += '  ' + element.to_svg() + '\n'
        
        svg += '</svg>'
        return svg