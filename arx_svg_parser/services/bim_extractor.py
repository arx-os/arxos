from models.system_elements import (
    ExtractionResponse, SystemElement, ElectricalElement, FireAlarmElement, PlumbingElement
)
from typing import List, Dict, Any
from lxml import etree as ET
import re

def extract_bim_from_svg(svg_xml: str, building_id: str, floor_id: str) -> ExtractionResponse:
    try:
        root = ET.fromstring(svg_xml.encode('utf-8'))
    except Exception as e:
        return ExtractionResponse(
            building_id=building_id,
            floor_id=floor_id,
            elements=[]
        )

    elements: List[SystemElement] = []
    nsmap = root.nsmap

    # Heuristic mappings for group IDs and label patterns
    group_to_system = {
        'electrical': 'E', 'power': 'E', 'lighting': 'E',
        'plumb': 'P', 'plumbing': 'P',
        'fire': 'FA', 'alarm': 'FA',
        'lowvolt': 'LV', 'lv': 'LV',
        'network': 'N', 'data': 'N', 'telecom': 'N',
        'mech': 'M', 'hvac': 'M',
        'security': 'Security',
        'controls': 'BAS', 'bms': 'BAS',
        'av': 'AV', 'audio': 'AV',
        'structural': 'Structural',
    }

    # Patterns for element type detection
    label_patterns = {
        'outlet': re.compile(r'outlet|receptacle|GFCI', re.I),
        'panel': re.compile(r'panel|transformer', re.I),
        'switch': re.compile(r'switch', re.I),
        'light': re.compile(r'light|fixture', re.I),
        'pipe': re.compile(r'pipe|CW|HW|HWR|SW|G|V', re.I),
        'valve': re.compile(r'valve|PRV|check|ball|gate', re.I),
        'faucet': re.compile(r'faucet|sink', re.I),
        'drain': re.compile(r'drain', re.I),
        'horn': re.compile(r'horn', re.I),
        'strobe': re.compile(r'strobe', re.I),
        'pull_station': re.compile(r'pull', re.I),
        'smoke': re.compile(r'smoke|SD', re.I),
        'heat': re.compile(r'heat|HD', re.I),
        'camera': re.compile(r'CCTV|camera|PTZ', re.I),
        'sensor': re.compile(r'sensor|TS|HS|PS|FS', re.I),
        'controller': re.compile(r'controller|I/O', re.I),
        'display': re.compile(r'display|projector|screen', re.I),
        'speaker': re.compile(r'speaker|SPKR', re.I),
        'mic': re.compile(r'mic', re.I),
        'rack': re.compile(r'rack', re.I),
        'ap': re.compile(r'AP|WAP', re.I),
        # Add more as needed
    }

    def classify_system_and_type(elem: Any, parent: Any, label: str) -> (str, str):
        # Default system/type
        system = 'Structural'
        type_ = 'unknown'
        # Use parent group id if available
        if parent is not None and parent.tag.endswith('g'):
            group_id = parent.get('id', '').lower()
            for key, sys in group_to_system.items():
                if key in group_id:
                    system = sys
                    break
        # Use label patterns to refine type
        if label:
            for t, pat in label_patterns.items():
                if pat.search(label):
                    type_ = t
                    break
        return system, type_

    for elem in root.iter():
        tag = ET.QName(elem).localname
        elem_id = elem.get('id') or f"auto-{tag}-{len(elements)+1}"
        label = elem.get('label') or elem.get('data-label') or elem.get('class') or ''
        parent = elem.getparent()
        system, type_ = classify_system_and_type(elem, parent, label)
        coords = (0.0, 0.0)
        # Geometry extraction by tag
        if tag == 'circle':
            cx = float(elem.get('cx', '0'))
            cy = float(elem.get('cy', '0'))
            coords = (cx, cy)
        elif tag == 'rect':
            x = float(elem.get('x', '0'))
            y = float(elem.get('y', '0'))
            coords = (x, y)
        elif tag == 'ellipse':
            cx = float(elem.get('cx', '0'))
            cy = float(elem.get('cy', '0'))
            coords = (cx, cy)
        elif tag == 'line':
            x1 = float(elem.get('x1', '0'))
            y1 = float(elem.get('y1', '0'))
            coords = (x1, y1)
        elif tag == 'polygon' or tag == 'polyline':
            points = elem.get('points', '').strip().split()
            if points:
                x, y = map(float, points[0].split(','))
                coords = (x, y)
        elif tag == 'path':
            # For now, use the first M command as the coordinate
            d = elem.get('d', '')
            m = re.search(r'M\s*([\d.]+)[, ]+([\d.]+)', d)
            if m:
                coords = (float(m.group(1)), float(m.group(2)))
        elif tag == 'text':
            x = float(elem.get('x', '0'))
            y = float(elem.get('y', '0'))
            coords = (x, y)
            label = elem.text or label
        # Specializations (expand as needed)
        if system == 'E':
            elements.append(ElectricalElement(
                id=elem_id,
                label=label,
                system='E',
                type=type_ if type_ in ElectricalElement.__fields__['type'].type_.__args__ else 'outlet',
                coordinates=coords
            ))
        elif system == 'P':
            elements.append(PlumbingElement(
                id=elem_id,
                label=label,
                system='P',
                type=type_ if type_ in PlumbingElement.__fields__['type'].type_.__args__ else 'pipe',
                coordinates=coords
            ))
        elif system == 'FA':
            elements.append(FireAlarmElement(
                id=elem_id,
                label=label,
                system='FA',
                type=type_ if type_ in FireAlarmElement.__fields__['type'].type_.__args__ else 'horn',
                coordinates=coords
            ))
        else:
            elements.append(SystemElement(
                id=elem_id,
                label=label,
                system=system,
                type=type_,
                coordinates=coords
            ))

    return ExtractionResponse(
        building_id=building_id,
        floor_id=floor_id,
        elements=elements
    ) 