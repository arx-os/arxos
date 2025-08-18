# Training Data Specification

## Overview

This document defines the training data requirements for the Arxos AI conversion system, including dataset structure, building type templates, and pattern learning specifications.

## Dataset Structure

### Core Training Data Components

```python
class TrainingDataset:
    def __init__(self):
        self.components = {
            'pdf_files': [],           # Source PDF floor plans
            'annotations': [],         # Ground truth annotations
            'building_metadata': [],   # Building type, size, location
            'validation_data': [],     # Field-validated corrections
            'patterns': [],           # Learned patterns
            'confidence_scores': []    # Historical confidence data
        }
```

### Data Organization

```
training_data/
├── buildings/
│   ├── office/
│   │   ├── small/        # <10,000 sqft
│   │   ├── medium/       # 10,000-100,000 sqft
│   │   └── large/        # >100,000 sqft
│   ├── residential/
│   │   ├── single_family/
│   │   ├── multi_family/
│   │   └── high_rise/
│   ├── healthcare/
│   │   ├── hospitals/
│   │   ├── clinics/
│   │   └── medical_offices/
│   └── industrial/
│       ├── warehouses/
│       ├── manufacturing/
│       └── distribution/
├── patterns/
│   ├── architectural_symbols/
│   ├── room_layouts/
│   ├── system_configurations/
│   └── text_patterns/
└── validations/
    ├── successful/
    ├── failed/
    └── corrections/
```

## Training Dataset Requirements

### Minimum Dataset Size

| Building Type | Minimum Examples | Recommended | Ideal |
|--------------|------------------|-------------|-------|
| Office | 50 | 200 | 500+ |
| Residential | 100 | 400 | 1000+ |
| Healthcare | 30 | 120 | 300+ |
| Industrial | 40 | 160 | 400+ |
| Educational | 40 | 160 | 400+ |
| Retail | 30 | 120 | 300+ |

### Quality Requirements

```python
class DataQualityRequirements:
    def __init__(self):
        self.pdf_quality = {
            'min_resolution': 150,  # DPI
            'max_resolution': 600,  # DPI
            'vector_content': 0.7,  # 70% vector vs raster
            'text_legibility': 0.8,  # 80% OCR success rate
            'scale_present': True    # Must have scale indicator
        }
        
        self.annotation_quality = {
            'completeness': 0.95,    # 95% of objects annotated
            'accuracy': 0.98,        # 98% position accuracy
            'consistency': 1.0,      # 100% consistent labeling
            'relationships': 0.90    # 90% relationships identified
        }
```

## Building Type Templates

### Office Building Template

```python
OFFICE_TEMPLATE = {
    'typical_elements': {
        'workstations': {
            'size_range': (50, 150),  # sqft
            'count_range': (10, 500),
            'patterns': ['grid', 'cluster', 'open']
        },
        'conference_rooms': {
            'size_range': (100, 1000),
            'count_range': (2, 50),
            'equipment': ['table', 'chairs', 'display']
        },
        'support_spaces': [
            'reception', 'break_room', 'copy_room', 
            'storage', 'it_closet', 'electrical_room'
        ]
    },
    'systems': {
        'hvac': 'vav_with_reheat',
        'electrical': 'panel_per_floor',
        'networking': 'idf_per_floor'
    },
    'validation_priorities': [
        'typical_floor_layout',
        'core_services',
        'workstation_dimensions'
    ]
}
```

### Hospital Template

```python
HOSPITAL_TEMPLATE = {
    'typical_elements': {
        'patient_rooms': {
            'size_range': (200, 400),
            'types': ['single', 'double', 'icu'],
            'required_features': ['bathroom', 'headwall']
        },
        'clinical_spaces': [
            'operating_room', 'emergency', 'imaging',
            'laboratory', 'pharmacy'
        ],
        'support_spaces': [
            'nurse_station', 'equipment_room', 
            'clean_utility', 'soiled_utility'
        ]
    },
    'systems': {
        'hvac': 'critical_environment',
        'electrical': 'emergency_power',
        'medical_gas': True,
        'nurse_call': True
    },
    'validation_priorities': [
        'life_safety_systems',
        'patient_room_headwalls',
        'critical_infrastructure'
    ]
}
```

### Residential Template

```python
RESIDENTIAL_TEMPLATE = {
    'typical_elements': {
        'units': {
            'types': ['studio', '1br', '2br', '3br'],
            'size_range': (400, 2000),
            'required_spaces': ['kitchen', 'bathroom', 'living']
        },
        'common_areas': [
            'lobby', 'corridors', 'amenity_spaces',
            'laundry', 'storage', 'parking'
        ]
    },
    'systems': {
        'hvac': 'individual_units',
        'electrical': 'meter_per_unit',
        'plumbing': 'stacked_wet_walls'
    },
    'validation_priorities': [
        'typical_unit_layout',
        'vertical_stacks',
        'egress_paths'
    ]
}
```

## Pattern Library

### Architectural Symbols

```python
SYMBOL_PATTERNS = {
    'doors': {
        'single_swing': {'width': (30, 36), 'arc': True},
        'double_swing': {'width': (60, 72), 'arc': True},
        'sliding': {'width': (36, 96), 'arc': False},
        'overhead': {'width': (96, 192), 'arc': False}
    },
    'windows': {
        'fixed': {'width': (24, 120)},
        'operable': {'width': (24, 60)},
        'storefront': {'width': (60, 240)}
    },
    'fixtures': {
        'toilet': {'size': (24, 30)},
        'sink': {'size': (18, 24)},
        'shower': {'size': (36, 60)}
    },
    'equipment': {
        'elevator': {'size': (60, 84)},
        'stairs': {'width': (44, 60)}
    }
}
```

### Text Patterns

```python
TEXT_PATTERNS = {
    'room_numbers': [
        r'^\d{3,4}$',           # 101, 2045
        r'^[A-Z]\d{2,3}$',     # A101, B23
        r'^\d{1,2}-\d{2,3}$'   # 1-101, 12-23
    ],
    'room_names': [
        r'^(CONF|CONFERENCE)',
        r'^(OFF|OFFICE)',
        r'^(STOR|STORAGE)',
        r'^(ELEC|ELECTRICAL)',
        r'^(MECH|MECHANICAL)'
    ],
    'dimensions': [
        r'\d+\'-\d+"',          # 10'-6"
        r'\d+\.\d+m',          # 3.5m
        r'\d+ ?mm'             # 1500mm
    ]
}
```

## Training Process

### Data Augmentation

```python
class DataAugmentation:
    def augment_training_data(self, original_data):
        augmented = []
        
        # Rotation augmentation
        for angle in [90, 180, 270]:
            augmented.append(self.rotate(original_data, angle))
        
        # Scale augmentation
        for scale in [0.8, 0.9, 1.1, 1.2]:
            augmented.append(self.scale(original_data, scale))
        
        # Noise augmentation
        for noise_level in [0.05, 0.1]:
            augmented.append(self.add_noise(original_data, noise_level))
        
        # Missing data augmentation
        for missing_ratio in [0.1, 0.2]:
            augmented.append(self.remove_random(original_data, missing_ratio))
        
        return augmented
```

### Pattern Learning Pipeline

```python
class PatternLearner:
    def learn_from_validations(self, validated_objects):
        patterns = {
            'spatial': self.learn_spatial_patterns(validated_objects),
            'dimensional': self.learn_dimensional_patterns(validated_objects),
            'relational': self.learn_relational_patterns(validated_objects),
            'system': self.learn_system_patterns(validated_objects)
        }
        
        return patterns
    
    def learn_spatial_patterns(self, objects):
        """Learn common spatial arrangements"""
        patterns = []
        
        # Detect grid patterns
        if self.is_grid_pattern(objects):
            patterns.append({
                'type': 'grid',
                'spacing': self.calculate_grid_spacing(objects),
                'confidence': 0.85
            })
        
        # Detect linear patterns
        if self.is_linear_pattern(objects):
            patterns.append({
                'type': 'linear',
                'spacing': self.calculate_linear_spacing(objects),
                'confidence': 0.80
            })
        
        return patterns
```

## Validation Data Collection

### Field Validation Structure

```python
class ValidationData:
    def __init__(self):
        self.structure = {
            'object_id': str,
            'original_confidence': float,
            'validation_type': str,  # dimension, visual, count
            'validated_value': any,
            'validator_confidence': float,
            'validator_id': str,
            'timestamp': datetime,
            'evidence': {
                'photos': [],
                'measurements': [],
                'notes': str
            },
            'impact': {
                'confidence_improvement': float,
                'cascaded_objects': int,
                'pattern_learned': bool
            }
        }
```

### Validation Feedback Loop

```python
def incorporate_validation_feedback(validation_data):
    """Incorporate field validation into training data"""
    
    # Update confidence models
    update_confidence_model(validation_data)
    
    # Learn new patterns
    if validation_data['pattern_learned']:
        add_to_pattern_library(validation_data)
    
    # Adjust extraction parameters
    if validation_data['confidence_improvement'] > 0.2:
        tune_extraction_parameters(validation_data)
    
    # Update building templates
    update_building_template(validation_data)
    
    # Retrain if significant changes
    if should_retrain(validation_data):
        schedule_retraining()
```

## Quality Metrics

### Training Data Quality Scores

```python
def calculate_data_quality_score(dataset):
    scores = {
        'completeness': check_completeness(dataset),
        'accuracy': check_accuracy(dataset),
        'diversity': check_diversity(dataset),
        'balance': check_balance(dataset),
        'recency': check_recency(dataset)
    }
    
    weights = {
        'completeness': 0.25,
        'accuracy': 0.35,
        'diversity': 0.20,
        'balance': 0.10,
        'recency': 0.10
    }
    
    overall_score = sum(
        scores[key] * weights[key] 
        for key in scores
    )
    
    return overall_score, scores
```

### Pattern Recognition Accuracy

```python
def evaluate_pattern_recognition():
    metrics = {
        'symbol_recognition': {
            'doors': 0.92,
            'windows': 0.89,
            'fixtures': 0.85,
            'equipment': 0.88
        },
        'text_extraction': {
            'room_numbers': 0.94,
            'room_names': 0.87,
            'dimensions': 0.82
        },
        'spatial_patterns': {
            'grid_detection': 0.86,
            'linear_detection': 0.91,
            'cluster_detection': 0.78
        }
    }
    
    return metrics
```

## Data Privacy & Security

### Anonymization Requirements

```python
class DataAnonymizer:
    def anonymize_building_data(self, data):
        """Remove sensitive information from training data"""
        
        # Remove location specifics
        data['address'] = self.generalize_location(data['address'])
        
        # Remove occupant information
        data = self.remove_personal_info(data)
        
        # Remove proprietary equipment details
        data = self.generalize_equipment(data)
        
        # Maintain structural information
        data = self.preserve_structure(data)
        
        return data
```

### Data Retention Policy

- **Raw PDFs**: 90 days after processing
- **Extracted ArxObjects**: Indefinite (anonymized)
- **Validation Data**: Indefinite (aggregated)
- **Personal Information**: Never stored
- **Building Addresses**: Generalized to city level

## Continuous Learning

### Online Learning Pipeline

```python
class OnlineLearning:
    def update_from_production(self, production_data):
        """Continuously improve from production usage"""
        
        # Collect high-confidence validations
        validated = filter_high_confidence(production_data)
        
        # Update pattern library
        self.pattern_library.update(validated)
        
        # Adjust confidence thresholds
        self.confidence_model.adjust(validated)
        
        # Identify new patterns
        new_patterns = self.detect_new_patterns(validated)
        
        # Schedule batch retraining
        if len(new_patterns) > threshold:
            self.schedule_retraining(new_patterns)
```

### A/B Testing Framework

```python
def ab_test_extraction_methods():
    """Test different extraction approaches"""
    
    variants = {
        'A': current_extraction_method,
        'B': experimental_extraction_method
    }
    
    results = {
        'A': {'confidence': [], 'speed': [], 'accuracy': []},
        'B': {'confidence': [], 'speed': [], 'accuracy': []}
    }
    
    # Run tests
    for pdf in test_set:
        for variant_name, method in variants.items():
            result = method(pdf)
            results[variant_name]['confidence'].append(result.confidence)
            results[variant_name]['speed'].append(result.time)
            results[variant_name]['accuracy'].append(result.accuracy)
    
    # Analyze results
    winner = analyze_ab_test(results)
    
    return winner
```

## Best Practices

### Data Collection Guidelines
1. Collect diverse building types and sizes
2. Include various PDF quality levels
3. Maintain balanced dataset across categories
4. Regularly update with new building standards
5. Validate ground truth with field measurements

### Pattern Library Maintenance
1. Review patterns quarterly
2. Remove obsolete patterns
3. Add industry-standard updates
4. Version control pattern changes
5. Document pattern confidence levels

### Quality Assurance
1. Cross-validate with multiple annotators
2. Perform regular accuracy audits
3. Track confidence score calibration
4. Monitor false positive/negative rates
5. Maintain validation feedback loop