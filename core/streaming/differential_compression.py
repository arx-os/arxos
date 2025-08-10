"""
Differential Compression System for 14KB Architecture.

Implements parent-child inheritance and delta compression for ArxObjects,
reducing bundle size by storing only differences between similar objects.
"""

import hashlib
import json
import logging
import time
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict
import difflib

logger = logging.getLogger(__name__)


@dataclass
class ObjectDelta:
    """Represents differences between two ArxObjects."""
    
    base_object_id: str
    target_object_id: str
    differences: Dict[str, Any]
    compression_ratio: float
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert delta to dictionary representation."""
        return {
            'base_object_id': self.base_object_id,
            'target_object_id': self.target_object_id,
            'differences': self.differences,
            'compression_ratio': self.compression_ratio,
            'created_at': self.created_at,
            'delta_type': 'differential'
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObjectDelta':
        """Create ObjectDelta from dictionary."""
        return cls(
            base_object_id=data['base_object_id'],
            target_object_id=data['target_object_id'],
            differences=data['differences'],
            compression_ratio=data['compression_ratio'],
            created_at=data.get('created_at', time.time())
        )


@dataclass
class CompressionTemplate:
    """Template for similar objects sharing common properties."""
    
    template_id: str
    base_properties: Dict[str, Any]
    object_ids: Set[str] = field(default_factory=set)
    similarity_score: float = 0.0
    created_at: float = field(default_factory=time.time)
    usage_count: int = 0
    
    def add_object(self, object_id: str) -> None:
        """Add object to template."""
        self.object_ids.add(object_id)
        self.usage_count += 1
    
    def remove_object(self, object_id: str) -> None:
        """Remove object from template."""
        self.object_ids.discard(object_id)
    
    def calculate_size_savings(self, original_sizes: List[int]) -> Dict[str, Any]:
        """Calculate compression savings for template."""
        if not original_sizes:
            return {'savings_bytes': 0, 'compression_ratio': 1.0}
        
        template_size = len(json.dumps(self.base_properties).encode())
        total_original_size = sum(original_sizes)
        
        # Estimate delta sizes (typically 10-30% of original)
        estimated_delta_size = sum(size * 0.2 for size in original_sizes)
        compressed_size = template_size + estimated_delta_size
        
        savings_bytes = total_original_size - compressed_size
        compression_ratio = compressed_size / total_original_size if total_original_size > 0 else 1.0
        
        return {
            'savings_bytes': max(0, savings_bytes),
            'compression_ratio': compression_ratio,
            'template_size': template_size,
            'estimated_deltas_size': estimated_delta_size,
            'original_total_size': total_original_size
        }


class DifferentialCompression:
    """
    Differential compression system for ArxObjects.
    
    Implements the 14KB principle's differential compression strategy:
    - Store only deltas between similar objects (99% identical outlets)
    - Use parent-child inheritance for common properties  
    - Create templates for object families
    - Binary encode coordinate data for space efficiency
    """
    
    def __init__(self, similarity_threshold: float = 0.9, max_templates: int = 100):
        """
        Initialize differential compression system.
        
        Args:
            similarity_threshold: Minimum similarity for template creation (0.9 = 90%)
            max_templates: Maximum number of templates to maintain
        """
        self.similarity_threshold = similarity_threshold
        self.max_templates = max_templates
        
        # Template storage
        self.templates: Dict[str, CompressionTemplate] = {}
        self.object_to_template: Dict[str, str] = {}  # object_id -> template_id
        
        # Delta storage
        self.deltas: Dict[str, ObjectDelta] = {}  # target_id -> delta
        
        # Similarity analysis cache
        self.similarity_cache: Dict[str, float] = {}  # hash(obj1+obj2) -> similarity
        
        # Performance metrics
        self.metrics = {
            'objects_compressed': 0,
            'templates_created': 0,
            'total_size_savings_bytes': 0,
            'average_compression_ratio': 0.0,
            'similarity_cache_hits': 0,
            'compression_time_ms': 0.0
        }
        
        logger.info(f"Initialized DifferentialCompression with similarity threshold {similarity_threshold}")
    
    def compress_object(self, arxobject_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress ArxObject using differential compression.
        
        Args:
            arxobject_data: ArxObject data dictionary
            
        Returns:
            Compressed object representation
        """
        start_time = time.time()
        
        object_id = arxobject_data.get('id', '')
        if not object_id:
            logger.warning("Object missing ID, cannot compress")
            return arxobject_data
        
        # Check if object already has template
        if object_id in self.object_to_template:
            template_id = self.object_to_template[object_id]
            template = self.templates.get(template_id)
            
            if template:
                # Return delta from existing template
                delta = self._create_delta_from_template(arxobject_data, template)
                self._update_compression_metrics(arxobject_data, delta, time.time() - start_time)
                return delta.to_dict()
        
        # Find best matching template
        best_template, similarity = self._find_best_template(arxobject_data)
        
        if best_template and similarity >= self.similarity_threshold:
            # Use existing template
            delta = self._create_delta_from_template(arxobject_data, best_template)
            best_template.add_object(object_id)
            self.object_to_template[object_id] = best_template.template_id
            
            self._update_compression_metrics(arxobject_data, delta, time.time() - start_time)
            return delta.to_dict()
        
        # Create new template if beneficial
        similar_objects = self._find_similar_objects(arxobject_data)
        
        if len(similar_objects) >= 2:  # Need at least 2 similar objects for template
            new_template = self._create_template(arxobject_data, similar_objects)
            delta = self._create_delta_from_template(arxobject_data, new_template)
            
            self._update_compression_metrics(arxobject_data, delta, time.time() - start_time)
            return delta.to_dict()
        
        # No compression benefit, return original with marker
        elapsed_ms = (time.time() - start_time) * 1000
        self.metrics['compression_time_ms'] = (
            (self.metrics['compression_time_ms'] + elapsed_ms) / 2
        )
        
        result = arxobject_data.copy()
        result['compression_info'] = {
            'compressed': False,
            'reason': 'no_similar_objects',
            'processing_time_ms': elapsed_ms
        }
        
        return result
    
    def _find_best_template(self, arxobject_data: Dict[str, Any]) -> Tuple[Optional[CompressionTemplate], float]:
        """Find best matching template for object."""
        
        best_template = None
        best_similarity = 0.0
        
        object_type = arxobject_data.get('type', '')
        system_type = arxobject_data.get('system_type', '')
        
        # Filter templates by object and system type for efficiency
        candidate_templates = [
            template for template in self.templates.values()
            if (template.base_properties.get('type', '') == object_type and
                template.base_properties.get('system_type', '') == system_type)
        ]
        
        for template in candidate_templates:
            similarity = self._calculate_similarity(arxobject_data, template.base_properties)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_template = template
        
        return best_template, best_similarity
    
    def _find_similar_objects(self, arxobject_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find objects similar to given object."""
        
        similar_objects = []
        object_type = arxobject_data.get('type', '')
        system_type = arxobject_data.get('system_type', '')
        
        # In production, this would query the spatial engine or database
        # For now, simulate finding similar objects based on templates
        for template in self.templates.values():
            if (template.base_properties.get('type', '') == object_type and
                template.base_properties.get('system_type', '') == system_type):
                
                similarity = self._calculate_similarity(arxobject_data, template.base_properties)
                if similarity >= self.similarity_threshold:
                    similar_objects.append(template.base_properties)
        
        return similar_objects
    
    def _calculate_similarity(self, obj1: Dict[str, Any], obj2: Dict[str, Any]) -> float:
        """Calculate similarity score between two objects (0.0 - 1.0)."""
        
        # Create cache key
        obj1_hash = hashlib.md5(json.dumps(obj1, sort_keys=True).encode()).hexdigest()[:8]
        obj2_hash = hashlib.md5(json.dumps(obj2, sort_keys=True).encode()).hexdigest()[:8]
        cache_key = f"{obj1_hash}_{obj2_hash}"
        
        # Check cache
        if cache_key in self.similarity_cache:
            self.metrics['similarity_cache_hits'] += 1
            return self.similarity_cache[cache_key]
        
        # Calculate similarity
        similarity = self._compute_object_similarity(obj1, obj2)
        
        # Cache result
        self.similarity_cache[cache_key] = similarity
        
        return similarity
    
    def _compute_object_similarity(self, obj1: Dict[str, Any], obj2: Dict[str, Any]) -> float:
        """Compute detailed similarity between objects."""
        
        # Weight factors for different properties
        property_weights = {
            'type': 0.3,           # Object type is very important
            'system_type': 0.2,    # System type is important
            'geometry': 0.2,       # Geometry similarity
            'metadata': 0.15,      # Metadata similarity
            'precision': 0.1,      # Precision level
            'other': 0.05          # Other properties
        }
        
        weighted_similarity = 0.0
        
        # Type similarity
        type_sim = 1.0 if obj1.get('type') == obj2.get('type') else 0.0
        weighted_similarity += type_sim * property_weights['type']
        
        # System type similarity
        system_sim = 1.0 if obj1.get('system_type') == obj2.get('system_type') else 0.0
        weighted_similarity += system_sim * property_weights['system_type']
        
        # Geometry similarity
        geom_sim = self._calculate_geometry_similarity(
            obj1.get('geometry', {}),
            obj2.get('geometry', {})
        )
        weighted_similarity += geom_sim * property_weights['geometry']
        
        # Metadata similarity
        meta_sim = self._calculate_metadata_similarity(
            obj1.get('metadata', {}),
            obj2.get('metadata', {})
        )
        weighted_similarity += meta_sim * property_weights['metadata']
        
        # Precision similarity
        prec_sim = 1.0 if obj1.get('precision') == obj2.get('precision') else 0.8
        weighted_similarity += prec_sim * property_weights['precision']
        
        return min(1.0, weighted_similarity)  # Cap at 1.0
    
    def _calculate_geometry_similarity(self, geom1: Dict[str, Any], geom2: Dict[str, Any]) -> float:
        """Calculate geometry similarity score."""
        
        if not geom1 or not geom2:
            return 0.0
        
        # Compare dimensions (most important for similarity)
        dim_keys = ['length', 'width', 'height']
        dimension_similarity = 0.0
        valid_dims = 0
        
        for key in dim_keys:
            if key in geom1 and key in geom2:
                val1, val2 = geom1[key], geom2[key]
                if val1 > 0 and val2 > 0:
                    # Calculate relative difference
                    diff_ratio = abs(val1 - val2) / max(val1, val2)
                    dim_similarity = max(0.0, 1.0 - diff_ratio)
                    dimension_similarity += dim_similarity
                    valid_dims += 1
        
        if valid_dims > 0:
            dimension_similarity /= valid_dims
        
        # Compare shape type
        shape_similarity = 1.0 if geom1.get('shape_type') == geom2.get('shape_type') else 0.7
        
        # Weighted combination
        return (dimension_similarity * 0.7) + (shape_similarity * 0.3)
    
    def _calculate_metadata_similarity(self, meta1: Dict[str, Any], meta2: Dict[str, Any]) -> float:
        """Calculate metadata similarity score."""
        
        if not meta1 or not meta2:
            return 0.0
        
        # Important metadata fields for similarity
        important_fields = ['manufacturer', 'model_number', 'material', 'specification']
        
        field_similarities = []
        
        for field in important_fields:
            val1 = meta1.get(field, '').lower()
            val2 = meta2.get(field, '').lower()
            
            if val1 and val2:
                # Use sequence matcher for string similarity
                similarity = difflib.SequenceMatcher(None, val1, val2).ratio()
                field_similarities.append(similarity)
            elif val1 == val2:  # Both empty
                field_similarities.append(1.0)
            else:  # One empty, one not
                field_similarities.append(0.0)
        
        return sum(field_similarities) / len(field_similarities) if field_similarities else 0.0
    
    def _create_template(self, 
                        arxobject_data: Dict[str, Any], 
                        similar_objects: List[Dict[str, Any]]) -> CompressionTemplate:
        """Create new compression template from similar objects."""
        
        # Generate template ID
        object_type = arxobject_data.get('type', 'unknown')
        timestamp = str(int(time.time() * 1000))[-6:]  # Last 6 digits of timestamp
        template_id = f"{object_type}_template_{timestamp}"
        
        # Extract common properties
        common_properties = self._extract_common_properties([arxobject_data] + similar_objects)
        
        # Calculate similarity score
        similarities = [
            self._calculate_similarity(arxobject_data, similar_obj)
            for similar_obj in similar_objects
        ]
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        
        # Create template
        template = CompressionTemplate(
            template_id=template_id,
            base_properties=common_properties,
            similarity_score=avg_similarity
        )
        
        template.add_object(arxobject_data.get('id', ''))
        
        # Store template
        self.templates[template_id] = template
        self.object_to_template[arxobject_data.get('id', '')] = template_id
        
        # Maintain template limit
        if len(self.templates) > self.max_templates:
            self._evict_least_used_template()
        
        self.metrics['templates_created'] += 1
        
        logger.debug(f"Created template {template_id} with {len(similar_objects)+1} objects, "
                    f"similarity: {avg_similarity:.2f}")
        
        return template
    
    def _extract_common_properties(self, objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract common properties from list of objects."""
        
        if not objects:
            return {}
        
        # Start with first object as base
        common_props = objects[0].copy()
        
        # Remove properties that vary between objects
        for obj in objects[1:]:
            keys_to_remove = []
            
            for key, value in common_props.items():
                if key not in obj or obj[key] != value:
                    # For geometric properties, check if they're "similar enough"
                    if key == 'geometry' and isinstance(value, dict) and isinstance(obj.get(key), dict):
                        # Keep geometry if dimensions are very similar
                        geom_similarity = self._calculate_geometry_similarity(value, obj[key])
                        if geom_similarity < 0.95:  # 95% similarity threshold for templates
                            keys_to_remove.append(key)
                    else:
                        keys_to_remove.append(key)
            
            for key in keys_to_remove:
                common_props.pop(key, None)
        
        # Always keep essential identifying properties
        essential_props = ['type', 'system_type', 'precision']
        for prop in essential_props:
            if prop in objects[0]:
                common_props[prop] = objects[0][prop]
        
        return common_props
    
    def _create_delta_from_template(self, 
                                   arxobject_data: Dict[str, Any], 
                                   template: CompressionTemplate) -> ObjectDelta:
        """Create delta from object to template."""
        
        differences = {}
        
        # Find all properties that differ from template
        for key, value in arxobject_data.items():
            template_value = template.base_properties.get(key)
            
            if template_value is None or template_value != value:
                differences[key] = value
        
        # Calculate compression ratio
        original_size = len(json.dumps(arxobject_data).encode())
        delta_size = len(json.dumps(differences).encode())
        template_size = len(json.dumps(template.base_properties).encode())
        
        # Amortize template size across all objects using it
        amortized_template_size = template_size / max(len(template.object_ids), 1)
        compressed_size = delta_size + amortized_template_size
        
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        
        return ObjectDelta(
            base_object_id=template.template_id,
            target_object_id=arxobject_data.get('id', ''),
            differences=differences,
            compression_ratio=compression_ratio
        )
    
    def _evict_least_used_template(self) -> None:
        """Evict least used template to maintain template limit."""
        
        if not self.templates:
            return
        
        # Find least used template
        least_used_id = min(self.templates.keys(), 
                           key=lambda tid: self.templates[tid].usage_count)
        
        least_used = self.templates[least_used_id]
        
        # Remove object mappings
        for object_id in least_used.object_ids:
            self.object_to_template.pop(object_id, None)
        
        # Remove template
        del self.templates[least_used_id]
        
        logger.debug(f"Evicted template {least_used_id} with {least_used.usage_count} uses")
    
    def _update_compression_metrics(self, 
                                  original_data: Dict[str, Any], 
                                  delta: ObjectDelta, 
                                  processing_time: float) -> None:
        """Update compression performance metrics."""
        
        self.metrics['objects_compressed'] += 1
        
        # Calculate size savings
        original_size = len(json.dumps(original_data).encode())
        compressed_size = len(json.dumps(delta.to_dict()).encode())
        size_savings = original_size - compressed_size
        
        self.metrics['total_size_savings_bytes'] += max(0, size_savings)
        
        # Update average compression ratio
        current_avg = self.metrics['average_compression_ratio']
        new_ratio = delta.compression_ratio
        self.metrics['average_compression_ratio'] = (current_avg + new_ratio) / 2
        
        # Update processing time
        processing_ms = processing_time * 1000
        current_time = self.metrics['compression_time_ms']
        self.metrics['compression_time_ms'] = (current_time + processing_ms) / 2
    
    def decompress_object(self, compressed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decompress object from delta representation.
        
        Args:
            compressed_data: Compressed object data
            
        Returns:
            Full object data
        """
        # Check if this is actually compressed
        if compressed_data.get('compression_info', {}).get('compressed', True) == False:
            return compressed_data
        
        # Check if it's a delta
        if 'base_object_id' not in compressed_data:
            return compressed_data
        
        delta = ObjectDelta.from_dict(compressed_data)
        
        # Get base template
        template = self.templates.get(delta.base_object_id)
        if not template:
            logger.error(f"Template {delta.base_object_id} not found for decompression")
            return compressed_data
        
        # Reconstruct full object
        full_object = template.base_properties.copy()
        full_object.update(delta.differences)
        
        return full_object
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Get comprehensive compression statistics."""
        
        # Template statistics
        template_stats = {}
        total_objects_in_templates = 0
        
        for template_id, template in self.templates.items():
            template_stats[template_id] = {
                'object_count': len(template.object_ids),
                'similarity_score': template.similarity_score,
                'usage_count': template.usage_count,
                'base_properties_count': len(template.base_properties)
            }
            total_objects_in_templates += len(template.object_ids)
        
        return {
            'compression_metrics': self.metrics.copy(),
            'template_count': len(self.templates),
            'objects_using_templates': total_objects_in_templates,
            'template_statistics': template_stats,
            'cache_size': len(self.similarity_cache),
            'configuration': {
                'similarity_threshold': self.similarity_threshold,
                'max_templates': self.max_templates
            }
        }
    
    def optimize_templates(self) -> Dict[str, Any]:
        """Optimize template usage and remove inefficient templates."""
        
        start_time = time.time()
        optimizations = []
        
        # Remove templates with low usage or poor compression
        templates_to_remove = []
        
        for template_id, template in self.templates.items():
            # Remove templates with very few objects
            if len(template.object_ids) < 2:
                templates_to_remove.append(template_id)
                optimizations.append(f"Removed template {template_id}: insufficient objects")
                continue
            
            # Remove templates with poor similarity
            if template.similarity_score < self.similarity_threshold - 0.1:
                templates_to_remove.append(template_id)
                optimizations.append(f"Removed template {template_id}: low similarity")
                continue
        
        # Remove identified templates
        for template_id in templates_to_remove:
            template = self.templates[template_id]
            
            # Remove object mappings
            for object_id in template.object_ids:
                self.object_to_template.pop(object_id, None)
            
            # Remove template
            del self.templates[template_id]
        
        # Clear similarity cache to free memory
        cache_size_before = len(self.similarity_cache)
        self.similarity_cache.clear()
        optimizations.append(f"Cleared similarity cache ({cache_size_before} entries)")
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            'optimization_completed': True,
            'optimizations_performed': optimizations,
            'templates_removed': len(templates_to_remove),
            'templates_remaining': len(self.templates),
            'processing_time_ms': elapsed_ms
        }