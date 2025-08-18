# Confidence System Documentation

## Overview

The Arxos Confidence System is a multi-dimensional framework that quantifies uncertainty in AI-extracted building data. Unlike traditional binary (correct/incorrect) systems, our confidence scoring enables **honest AI assessment**, strategic validation prioritization, and progressive accuracy improvement.

## Core Philosophy

### Honest Uncertainty Communication
The system explicitly communicates what it knows and what it doesn't know, enabling:
- Transparent AI limitations acknowledgment
- Strategic human intervention
- Risk-aware decision making
- Progressive improvement through targeted validation

### Multi-Dimensional Assessment
Confidence is not a single score but a composite of multiple dimensions:
- **Classification Confidence**: How sure we are about what an object is
- **Position Confidence**: Spatial accuracy certainty
- **Properties Confidence**: Attribute data reliability
- **Relationship Confidence**: Connection validity assessment

## Confidence Score Structure

```python
class ConfidenceScore:
    def __init__(self):
        self.classification = 0.0  # Object type certainty (0-1)
        self.position = 0.0        # Spatial accuracy (0-1)
        self.properties = 0.0      # Data accuracy (0-1)
        self.relationships = 0.0   # Connection validity (0-1)
        self.overall = 0.0         # Weighted average (0-1)
    
    def calculate_overall(self, weights=None):
        """Calculate weighted overall confidence"""
        if weights is None:
            weights = {
                'classification': 0.35,
                'position': 0.30,
                'properties': 0.20,
                'relationships': 0.15
            }
        
        self.overall = (
            self.classification * weights['classification'] +
            self.position * weights['position'] +
            self.properties * weights['properties'] +
            self.relationships * weights['relationships']
        )
        return self.overall
```

## Confidence Calculation Methods

### Classification Confidence

```python
def calculate_classification_confidence(element, context):
    """Calculate how confident we are about object type"""
    
    confidence = 0.0
    
    # Symbol matching confidence
    if element.matches_known_symbol():
        confidence = 0.95  # Known architectural symbol
    elif element.has_text_label():
        confidence = 0.85  # Has identifying text
    elif element.matches_pattern():
        confidence = 0.75  # Matches common pattern
    else:
        confidence = 0.50  # Best guess based on context
    
    # Context validation boost
    if context.validates_element_type(element):
        confidence = min(1.0, confidence + 0.10)
    
    # Ambiguity penalty
    if element.has_multiple_interpretations():
        confidence *= 0.80
    
    return confidence
```

### Position Confidence

```python
def calculate_position_confidence(element, extraction_method):
    """Calculate spatial accuracy confidence"""
    
    base_confidence = {
        'vector_direct': 0.95,      # Direct from PDF vectors
        'vector_computed': 0.85,    # Computed from vectors
        'ocr_with_dims': 0.75,      # OCR with dimensions
        'image_detection': 0.65,    # Computer vision detection
        'inference': 0.50           # Inferred from context
    }
    
    confidence = base_confidence.get(extraction_method, 0.40)
    
    # Scale detection adjustment
    if not element.has_known_scale():
        confidence *= 0.70  # Unknown scale reduces confidence
    
    # Alignment validation
    if element.aligns_with_grid():
        confidence = min(1.0, confidence + 0.05)
    
    return confidence
```

### Properties Confidence

```python
def calculate_properties_confidence(element):
    """Calculate confidence in object properties/attributes"""
    
    total_properties = len(element.properties)
    confident_properties = 0
    
    for prop_name, prop_value in element.properties.items():
        prop_confidence = 0.0
        
        # Source-based confidence
        if prop_value.source == 'direct_text':
            prop_confidence = 0.90
        elif prop_value.source == 'ocr':
            prop_confidence = 0.75
        elif prop_value.source == 'inference':
            prop_confidence = 0.60
        elif prop_value.source == 'default':
            prop_confidence = 0.40
        
        # Validation boost
        if prop_value.validated_by_pattern():
            prop_confidence = min(1.0, prop_confidence + 0.10)
        
        if prop_confidence > 0.60:
            confident_properties += 1
    
    return confident_properties / max(total_properties, 1)
```

### Relationship Confidence

```python
def calculate_relationship_confidence(relationship, source_confidence, target_confidence):
    """Calculate confidence in object relationships"""
    
    # Base confidence from relationship type
    type_confidence = {
        'physical_connection': 0.85,  # Clear physical connection
        'spatial_adjacency': 0.80,    # Objects are adjacent
        'logical_grouping': 0.70,     # Same system/zone
        'inferred_connection': 0.50    # Inferred relationship
    }
    
    base = type_confidence.get(relationship.type, 0.40)
    
    # Factor in object confidences
    object_factor = (source_confidence + target_confidence) / 2
    
    # Distance penalty for spatial relationships
    if relationship.has_distance():
        if relationship.distance > relationship.expected_distance * 2:
            base *= 0.70  # Too far apart
    
    return base * object_factor
```

## Confidence Thresholds

### Operational Thresholds

```python
class ConfidenceThresholds:
    # Visualization thresholds
    HIGH_CONFIDENCE = 0.85      # Green - Minimal validation needed
    MEDIUM_CONFIDENCE = 0.60    # Yellow - Selective validation
    LOW_CONFIDENCE = 0.60        # Red - Validation required
    
    # Operational thresholds
    AUTO_ACCEPT = 0.90          # Can be used without validation
    REQUIRES_REVIEW = 0.70      # Needs human review
    REQUIRES_VALIDATION = 0.50  # Must be field validated
    REJECT = 0.30               # Too uncertain to use
    
    # System thresholds
    PROPAGATION_MINIMUM = 0.75  # Min confidence to propagate
    PATTERN_LEARNING = 0.80     # Min to learn patterns from
    TRUSTED_SOURCE = 0.95       # Trusted for training
```

### Visual Indicators

```css
/* Confidence-based styling */
.confidence-high {
    border-color: #10b981;  /* Green */
    background: rgba(16, 185, 129, 0.1);
}

.confidence-medium {
    border-color: #f59e0b;  /* Yellow */
    background: rgba(245, 158, 11, 0.1);
}

.confidence-low {
    border-color: #ef4444;  /* Red */
    background: rgba(239, 68, 68, 0.1);
    animation: pulse 2s infinite;
}

.confidence-validated {
    border-color: #3b82f6;  /* Blue */
    background: rgba(59, 130, 246, 0.1);
}
```

## Confidence Improvement Strategies

### Progressive Enhancement

```python
class ConfidenceEnhancer:
    def enhance_through_validation(self, arxobject, validation):
        """Improve confidence through field validation"""
        
        if validation.type == 'dimension_verification':
            # Dimension validation improves position confidence
            arxobject.confidence.position = min(1.0, 
                arxobject.confidence.position + 0.25)
            
            # Also improves related objects
            self.propagate_position_confidence(arxobject)
        
        elif validation.type == 'type_confirmation':
            # Type confirmation maximizes classification
            arxobject.confidence.classification = 0.95
            
            # Learn pattern for similar objects
            self.learn_classification_pattern(arxobject)
        
        elif validation.type == 'property_verification':
            # Property validation improves specific property
            arxobject.confidence.properties = min(1.0,
                arxobject.confidence.properties + 0.20)
        
        # Recalculate overall
        arxobject.confidence.calculate_overall()
        
        return arxobject
```

### Pattern-Based Improvement

```python
def improve_through_patterns(self, arxobjects):
    """Improve confidence by detecting patterns"""
    
    # Group similar objects
    groups = self.group_by_similarity(arxobjects)
    
    for group in groups:
        if len(group) > 5:  # Pattern threshold
            # Calculate group statistics
            avg_confidence = self.calculate_average_confidence(group)
            
            if avg_confidence > 0.75:
                # High-confidence pattern detected
                for obj in group:
                    if obj.confidence.overall < avg_confidence:
                        # Boost low-confidence similar objects
                        obj.confidence.overall = min(
                            avg_confidence,
                            obj.confidence.overall + 0.10
                        )
```

### Relationship Validation

```python
def validate_through_relationships(self, arxobject):
    """Use relationships to validate confidence"""
    
    # Check relationship consistency
    for relationship in arxobject.relationships:
        target = self.get_object(relationship.target_id)
        
        # Mutual validation
        if self.validates_mutual_relationship(arxobject, target):
            # Boost both objects' relationship confidence
            arxobject.confidence.relationships = min(1.0,
                arxobject.confidence.relationships + 0.05)
            target.confidence.relationships = min(1.0,
                target.confidence.relationships + 0.05)
        
        # Propagate high confidence
        if target.confidence.overall > 0.85:
            if relationship.type in ['connected_to', 'part_of']:
                # Strong relationship with high-confidence object
                arxobject.confidence.overall = min(
                    target.confidence.overall * 0.9,
                    arxobject.confidence.overall + 0.10
                )
```

## Confidence Propagation

### Spatial Propagation

```python
def propagate_spatial_confidence(self, validated_object):
    """Propagate confidence to spatially related objects"""
    
    # Find nearby objects
    nearby = self.find_objects_within_distance(
        validated_object, 
        distance=5.0  # meters
    )
    
    for obj in nearby:
        if obj.type == validated_object.type:
            # Same type nearby - likely similar confidence
            confidence_boost = 0.15
        else:
            # Different type - smaller boost
            confidence_boost = 0.05
        
        # Apply distance decay
        distance = self.calculate_distance(validated_object, obj)
        decay = 1.0 - (distance / 5.0)
        confidence_boost *= decay
        
        # Update confidence
        obj.confidence.position = min(1.0,
            obj.confidence.position + confidence_boost)
```

### System Propagation

```python
def propagate_system_confidence(self, validated_object):
    """Propagate confidence through system connections"""
    
    # Trace system connections
    system_objects = self.trace_system(validated_object)
    
    for obj in system_objects:
        # Calculate propagation factor
        hops = self.calculate_hops(validated_object, obj)
        propagation_factor = 0.9 ** hops  # 10% decay per hop
        
        # Only propagate if factor is significant
        if propagation_factor > 0.5:
            confidence_boost = 0.10 * propagation_factor
            obj.confidence.relationships = min(1.0,
                obj.confidence.relationships + confidence_boost)
```

## Uncertainty Management

### Uncertainty Identification

```python
class UncertaintyAnalyzer:
    def identify_critical_uncertainties(self, arxobjects):
        """Identify uncertainties that most impact system"""
        
        uncertainties = []
        
        for obj in arxobjects:
            if obj.confidence.overall < 0.60:
                impact_score = self.calculate_impact(obj)
                
                uncertainty = {
                    'object_id': obj.id,
                    'type': obj.type,
                    'confidence': obj.confidence.overall,
                    'impact_score': impact_score,
                    'validation_priority': impact_score / (1 - obj.confidence.overall),
                    'reasons': self.analyze_uncertainty_reasons(obj)
                }
                
                uncertainties.append(uncertainty)
        
        # Sort by validation priority
        return sorted(uncertainties, 
                     key=lambda x: x['validation_priority'], 
                     reverse=True)
```

### Strategic Resolution

```python
def generate_resolution_strategy(self, uncertainties):
    """Generate strategic plan to resolve uncertainties"""
    
    strategy = {
        'immediate': [],     # Critical, easy to validate
        'high_priority': [], # High impact, moderate effort
        'normal': [],        # Standard validation
        'low_priority': []   # Nice to have
    }
    
    for uncertainty in uncertainties:
        effort = self.estimate_validation_effort(uncertainty)
        impact = uncertainty['impact_score']
        
        # Strategic categorization
        if impact > 0.8 and effort < 0.3:
            strategy['immediate'].append(uncertainty)
        elif impact > 0.6:
            strategy['high_priority'].append(uncertainty)
        elif impact > 0.3:
            strategy['normal'].append(uncertainty)
        else:
            strategy['low_priority'].append(uncertainty)
    
    return strategy
```

## Monitoring & Analytics

### Confidence Metrics

```python
class ConfidenceMetrics:
    def calculate_building_confidence(self, building_id):
        """Calculate overall building confidence metrics"""
        
        arxobjects = self.get_building_objects(building_id)
        
        metrics = {
            'total_objects': len(arxobjects),
            'average_confidence': np.mean([o.confidence.overall for o in arxobjects]),
            'high_confidence_ratio': len([o for o in arxobjects if o.confidence.overall > 0.85]) / len(arxobjects),
            'validation_needed': len([o for o in arxobjects if o.confidence.overall < 0.60]),
            'confidence_distribution': {
                'high': len([o for o in arxobjects if o.confidence.overall > 0.85]),
                'medium': len([o for o in arxobjects if 0.60 <= o.confidence.overall <= 0.85]),
                'low': len([o for o in arxobjects if o.confidence.overall < 0.60])
            },
            'improvement_potential': self.calculate_improvement_potential(arxobjects)
        }
        
        return metrics
```

### Validation Impact Tracking

```python
def track_validation_impact(self, validation):
    """Track the impact of validations on confidence"""
    
    before_confidence = validation.object.confidence.overall
    after_confidence = validation.updated_object.confidence.overall
    
    impact = {
        'validation_id': validation.id,
        'object_id': validation.object.id,
        'confidence_improvement': after_confidence - before_confidence,
        'cascaded_objects': len(validation.affected_objects),
        'total_confidence_gain': sum([
            obj.confidence_delta for obj in validation.affected_objects
        ]),
        'time_invested': validation.duration,
        'roi': self.calculate_validation_roi(validation)
    }
    
    self.store_impact_metrics(impact)
    return impact
```

## Best Practices

### Setting Realistic Confidence
1. Start with conservative estimates
2. Use source quality as baseline
3. Apply context validation carefully
4. Account for ambiguity explicitly
5. Update based on validation feedback

### Communicating Uncertainty
1. Use visual indicators consistently
2. Provide uncertainty reasons
3. Suggest validation actions
4. Show confidence trends
5. Highlight improvement opportunities

### Strategic Validation
1. Prioritize high-impact uncertainties
2. Batch similar validations
3. Use pattern validation
4. Propagate validated confidence
5. Track validation ROI

## Future Enhancements

### Machine Learning Integration
- Confidence prediction models
- Automatic threshold adjustment
- Pattern-based confidence boosting
- Anomaly detection for low confidence

### Advanced Propagation
- Multi-hop confidence propagation
- Cross-building confidence transfer
- Temporal confidence decay
- Confidence inheritance patterns