from lxml import etree as ET
from lxml.etree import QName

SVG_NS = "http://www.w3.org/2000/svg"
NSMAP = {None: SVG_NS}


def write_svg(svg_str, annotations):
    try:
        root = ET.fromstring(svg_str.encode('utf-8'))
    except Exception as e:
        return {"error": f"Failed to parse SVG: {str(e)}"}

    for ann in annotations:
        ann_type = ann.get('type')
        coords = ann.get('coordinates', [0, 0])
        if ann_type == 'note':
            text = ann.get('text', '')
            text_elem = ET.Element(QName(SVG_NS, 'text'), nsmap=root.nsmap, x=str(coords[0]), y=str(coords[1]), fill='red', font_size='32')
            text_elem.text = text
            root.append(text_elem)
        elif ann_type == 'device':
            circle_elem = ET.Element(QName(SVG_NS, 'circle'), nsmap=root.nsmap, cx=str(coords[0]), cy=str(coords[1]), r='20', fill='blue')
            root.append(circle_elem)
            # Optionally add device id as text
            device_id = ann.get('id')
            if device_id:
                text_elem = ET.Element(QName(SVG_NS, 'text'), nsmap=root.nsmap, x=str(coords[0]), y=str(coords[1]+30), fill='blue', font_size='24')
                text_elem.text = device_id
                root.append(text_elem)
        # Add more annotation types as needed

    return ET.tostring(root, encoding='unicode', pretty_print=True) 