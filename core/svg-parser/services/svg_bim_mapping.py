"""
SVG-to-BIM Mapping Table

Maps SVG element type, layer, and properties to BIM subclasses for automatic typing in the assembly pipeline.
"""

# Example mapping: (svg_type, layer) -> BIM class name
SVG_BIM_MAPPING = {
    ('rect', 'walls'): 'Wall',
    ('rect', 'doors'): 'Door',
    ('rect', 'windows'): 'Window',
    ('rect', 'hvac'): 'HVACZone',
    ('rect', 'electrical'): 'ElectricalPanel',
    ('rect', 'plumbing'): 'PlumbingSystem',
    ('circle', 'smoke_detectors'): 'SmokeDetector',
    ('circle', 'cameras'): 'Camera',
    ('rect', 'furniture'): 'Device',
    # Add more as needed
}

# Fallback mapping by SVG type only
SVG_TYPE_FALLBACK = {
    'rect': 'BIMElement',
    'circle': 'Device',
    'line': 'BIMElement',
    'polygon': 'BIMElement',
    # Add more as needed
}

def get_bim_class_for_svg(svg_element: dict) -> str:
    """
    Given an SVG element dict, return the BIM class name to instantiate.
    """
    svg_type = svg_element.get('type')
    layer = svg_element.get('metadata', {}).get('layer')
    # Try (type, layer) mapping first
    if (svg_type, layer) in SVG_BIM_MAPPING:
        return SVG_BIM_MAPPING[(svg_type, layer)]
    # Fallback to type-only mapping
    if svg_type in SVG_TYPE_FALLBACK:
        return SVG_TYPE_FALLBACK[svg_type]
    # Default fallback
    return 'BIMElement' 