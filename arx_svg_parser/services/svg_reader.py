import base64
from lxml import etree as ET
from lxml.etree import QName

SVG_NS = "http://www.w3.org/2000/svg"

def read_svg(svg_base64):
    try:
        svg_bytes = base64.b64decode(svg_base64)
        svg_str = svg_bytes.decode('utf-8')
        root = ET.fromstring(svg_str.encode('utf-8'))
    except Exception as e:
        return {"error": f"Failed to decode or parse SVG: {str(e)}"}

    # Count common SVG elements (using localname for namespace-agnostic search)
    tags = ['rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'path', 'text', 'g']
    summary = {tag: 0 for tag in tags}
    for elem in root.iter():
        tag = ET.QName(elem).localname
        if tag in summary:
            summary[tag] += 1

    summary['total_elements'] = sum(summary.values())
    return summary 

def enhance_svg_for_bim(svg_str, bim_objects):
    """
    Enhances SVG by:
    - Injecting <g id="arx-objects"> if not present
    - Annotating <use> and <symbol> tags with BIMObject data
    - Adding data-* attributes for placement
    Args:
        svg_str (str): SVG XML as string
        bim_objects (list): List of dicts with at least object_id, x, y, rotation, etc.
    Returns:
        str: Modified SVG XML as string
    """
    try:
        root = ET.fromstring(svg_str.encode('utf-8'))
    except Exception as e:
        return svg_str  # Return original if parse fails

    # Find or create <g id="arx-objects">
    arx_group = None
    for g in root.findall(f'.//{{{SVG_NS}}}g'):
        if g.get('id') == 'arx-objects':
            arx_group = g
            break
    if arx_group is None:
        arx_group = ET.Element(QName(SVG_NS, 'g'), id='arx-objects')
        root.append(arx_group)

    # Map BIM objects by object_id for quick lookup
    bim_map = {obj['object_id']: obj for obj in bim_objects if 'object_id' in obj}

    # Annotate <use> and <symbol> tags
    for tag in ['use', 'symbol']:
        for elem in root.findall(f'.//{{{SVG_NS}}}{tag}'):
            # Try to match by id or href
            obj_id = elem.get('id') or elem.get(f'{{http://www.w3.org/1999/xlink}}href')
            if obj_id and obj_id in bim_map:
                bim = bim_map[obj_id]
                # Add data-* attributes
                elem.set('data-bim-object-id', bim['object_id'])
                if 'x' in bim:
                    elem.set('data-x', str(bim['x']))
                if 'y' in bim:
                    elem.set('data-y', str(bim['y']))
                if 'rotation' in bim:
                    elem.set('data-rotation', str(bim['rotation']))
                if 'tags' in bim:
                    elem.set('data-tags', ','.join(map(str, bim['tags'])))
                # Optionally wrap in <g> for grouping
                parent = elem.getparent()
                if parent is not None and parent.tag != f'{{{SVG_NS}}}g':
                    g = ET.Element(QName(SVG_NS, 'g'))
                    g.set('data-bim-object-id', bim['object_id'])
                    parent.replace(elem, g)
                    g.append(elem)
                # Move to arx-objects group if not already
                if elem.getparent() is not arx_group:
                    arx_group.append(elem)

    # Optionally: add <g> wrappers for any BIM objects not present in SVG
    # (skipped for now)

    # Return modified SVG as string
    return ET.tostring(root, encoding='unicode') 