"""
Persistence Service for SVGX Engine

Provides functions to save/load SVGX documents and related data in various formats
(JSON, XML, SVGX, SVG), with robust error handling and user-friendly API.
Enhanced for SVGX-specific data structures and workflows.
"""

import json
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import logging

try:
    try:
    from ..utils.errors import PersistenceError, ValidationError
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import PersistenceError, ValidationError
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import PersistenceError, ValidationError
from ..models.svgx import SVGXDocument, SVGXElement, ArxObject, ArxBehavior, ArxPhysics

logger = logging.getLogger(__name__)


class SVGXPersistenceService:
    """
    Service for saving and loading SVGX documents and related data.
    """
    
    def save_svgx_document(self, svgx_document: SVGXDocument, file_path: str) -> None:
        """Save SVGX document to file."""
        try:
            # Convert SVGX document to dictionary
            doc_data = self._svgx_document_to_dict(svgx_document)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"SVGX document saved: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save SVGX document: {e}")
            raise PersistenceError(f"Failed to save SVGX document: {e}") from e
    
    def load_svgx_document(self, file_path: str) -> SVGXDocument:
        """Load SVGX document from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
            
            # Convert dictionary to SVGX document
            svgx_document = self._dict_to_svgx_document(doc_data)
            
            logger.info(f"SVGX document loaded: {file_path}")
            return svgx_document
        except Exception as e:
            logger.error(f"Failed to load SVGX document: {e}")
            raise ValidationError(f"Failed to load SVGX document: {e}") from e
    
    def save_svgx_json(self, svgx_data: Dict[str, Any], file_path: str) -> None:
        """Save SVGX data to JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(svgx_data, f, indent=2, ensure_ascii=False)
            logger.info(f"SVGX data saved to JSON: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save SVGX JSON: {e}")
            raise PersistenceError(f"Failed to save SVGX JSON: {e}") from e
    
    def load_svgx_json(self, file_path: str) -> Dict[str, Any]:
        """Load SVGX data from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"SVGX data loaded from JSON: {file_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load SVGX JSON: {e}")
            raise ValidationError(f"Failed to load SVGX JSON: {e}") from e
    
    def save_svgx_xml(self, svgx_data: Dict[str, Any], file_path: str) -> None:
        """Save SVGX data to XML file."""
        try:
            root = self._dict_to_xml('SVGXDocument', svgx_data)
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            logger.info(f"SVGX data saved to XML: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save SVGX XML: {e}")
            raise PersistenceError(f"Failed to save SVGX XML: {e}") from e
    
    def load_svgx_xml(self, file_path: str) -> Dict[str, Any]:
        """Load SVGX data from XML file."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            data = self._xml_to_dict(root)
            logger.info(f"SVGX data loaded from XML: {file_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load SVGX XML: {e}")
            raise ValidationError(f"Failed to load SVGX XML: {e}") from e
    
    def save_svg(self, svg_content: str, file_path: str) -> None:
        """Save SVG content to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            logger.info(f"SVG saved: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save SVG: {e}")
            raise PersistenceError(f"Failed to save SVG: {e}") from e
    
    def load_svg(self, file_path: str) -> str:
        """Load SVG content from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"SVG loaded: {file_path}")
            return content
        except Exception as e:
            logger.error(f"Failed to load SVG: {e}")
            raise ValidationError(f"Failed to load SVG: {e}") from e
    
    def save_arx_object(self, arx_object: ArxObject, file_path: str) -> None:
        """Save ArxObject to file."""
        try:
            obj_data = self._arx_object_to_dict(arx_object)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(obj_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"ArxObject saved: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save ArxObject: {e}")
            raise PersistenceError(f"Failed to save ArxObject: {e}") from e
    
    def load_arx_object(self, file_path: str) -> ArxObject:
        """Load ArxObject from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                obj_data = json.load(f)
            
            arx_object = self._dict_to_arx_object(obj_data)
            
            logger.info(f"ArxObject loaded: {file_path}")
            return arx_object
        except Exception as e:
            logger.error(f"Failed to load ArxObject: {e}")
            raise ValidationError(f"Failed to load ArxObject: {e}") from e
    
    def save_arx_behavior(self, arx_behavior: ArxBehavior, file_path: str) -> None:
        """Save ArxBehavior to file."""
        try:
            behavior_data = self._arx_behavior_to_dict(arx_behavior)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(behavior_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"ArxBehavior saved: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save ArxBehavior: {e}")
            raise PersistenceError(f"Failed to save ArxBehavior: {e}") from e
    
    def load_arx_behavior(self, file_path: str) -> ArxBehavior:
        """Load ArxBehavior from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                behavior_data = json.load(f)
            
            arx_behavior = self._dict_to_arx_behavior(behavior_data)
            
            logger.info(f"ArxBehavior loaded: {file_path}")
            return arx_behavior
        except Exception as e:
            logger.error(f"Failed to load ArxBehavior: {e}")
            raise ValidationError(f"Failed to load ArxBehavior: {e}") from e
    
    def save_arx_physics(self, arx_physics: ArxPhysics, file_path: str) -> None:
        """Save ArxPhysics to file."""
        try:
            physics_data = self._arx_physics_to_dict(arx_physics)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(physics_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"ArxPhysics saved: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save ArxPhysics: {e}")
            raise PersistenceError(f"Failed to save ArxPhysics: {e}") from e
    
    def load_arx_physics(self, file_path: str) -> ArxPhysics:
        """Load ArxPhysics from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                physics_data = json.load(f)
            
            arx_physics = self._dict_to_arx_physics(physics_data)
            
            logger.info(f"ArxPhysics loaded: {file_path}")
            return arx_physics
        except Exception as e:
            logger.error(f"Failed to load ArxPhysics: {e}")
            raise ValidationError(f"Failed to load ArxPhysics: {e}") from e
    
    def _svgx_document_to_dict(self, svgx_document: SVGXDocument) -> Dict[str, Any]:
        """Convert SVGX document to dictionary."""
        return {
            'version': svgx_document.version,
            'elements': [self._svgx_element_to_dict(elem) for elem in svgx_document.elements],
            'metadata': svgx_document.metadata,
            'created_at': svgx_document.created_at.isoformat() if svgx_document.created_at else None,
            'updated_at': svgx_document.updated_at.isoformat() if svgx_document.updated_at else None
        }
    
    def _dict_to_svgx_document(self, doc_data: Dict[str, Any]) -> SVGXDocument:
        """Convert dictionary to SVGX document."""
        from datetime import datetime
        
        elements = [self._dict_to_svgx_element(elem_data) for elem_data in doc_data.get('elements', [])]
        
        created_at = None
        if doc_data.get('created_at'):
            created_at = datetime.fromisoformat(doc_data['created_at'])
        
        updated_at = None
        if doc_data.get('updated_at'):
            updated_at = datetime.fromisoformat(doc_data['updated_at'])
        
        return SVGXDocument(
            version=doc_data.get('version', '1.0'),
            elements=elements,
            metadata=doc_data.get('metadata', {}),
            created_at=created_at,
            updated_at=updated_at
        )
    
    def _svgx_element_to_dict(self, element: SVGXElement) -> Dict[str, Any]:
        """Convert SVGX element to dictionary."""
        return {
            'tag': element.tag,
            'attributes': element.attributes,
            'content': element.content,
            'position': element.position,
            'children': [self._svgx_element_to_dict(child) for child in element.children],
            'arx_object': self._arx_object_to_dict(element.arx_object) if element.arx_object else None,
            'arx_behavior': self._arx_behavior_to_dict(element.arx_behavior) if element.arx_behavior else None,
            'arx_physics': self._arx_physics_to_dict(element.arx_physics) if element.arx_physics else None
        }
    
    def _dict_to_svgx_element(self, element_data: Dict[str, Any]) -> SVGXElement:
        """Convert dictionary to SVGX element."""
        element = SVGXElement(
            tag=element_data['tag'],
            attributes=element_data['attributes'],
            content=element_data['content'],
            position=element_data['position']
        )
        
        # Add children
        for child_data in element_data.get('children', []):
            child = self._dict_to_svgx_element(child_data)
            element.add_child(child)
        
        # Add arx objects
        if element_data.get('arx_object'):
            element.arx_object = self._dict_to_arx_object(element_data['arx_object'])
        
        if element_data.get('arx_behavior'):
            element.arx_behavior = self._dict_to_arx_behavior(element_data['arx_behavior'])
        
        if element_data.get('arx_physics'):
            element.arx_physics = self._dict_to_arx_physics(element_data['arx_physics'])
        
        return element
    
    def _arx_object_to_dict(self, arx_object: ArxObject) -> Dict[str, Any]:
        """Convert ArxObject to dictionary."""
        return {
            'object_id': arx_object.object_id,
            'object_type': arx_object.object_type,
            'system': arx_object.system,
            'properties': arx_object.properties,
            'geometry': arx_object.geometry,
            'behavior': self._arx_behavior_to_dict(arx_object.behavior) if arx_object.behavior else None,
            'physics': self._arx_physics_to_dict(arx_object.physics) if arx_object.physics else None
        }
    
    def _dict_to_arx_object(self, object_data: Dict[str, Any]) -> ArxObject:
        """Convert dictionary to ArxObject."""
        behavior = None
        if object_data.get('behavior'):
            behavior = self._dict_to_arx_behavior(object_data['behavior'])
        
        physics = None
        if object_data.get('physics'):
            physics = self._dict_to_arx_physics(object_data['physics'])
        
        return ArxObject(
            object_id=object_data['object_id'],
            object_type=object_data['object_type'],
            system=object_data.get('system'),
            properties=object_data.get('properties', {}),
            geometry=object_data.get('geometry'),
            behavior=behavior,
            physics=physics
        )
    
    def _arx_behavior_to_dict(self, arx_behavior: ArxBehavior) -> Dict[str, Any]:
        """Convert ArxBehavior to dictionary."""
        return {
            'variables': arx_behavior.variables,
            'calculations': arx_behavior.calculations,
            'triggers': arx_behavior.triggers
        }
    
    def _dict_to_arx_behavior(self, behavior_data: Dict[str, Any]) -> ArxBehavior:
        """Convert dictionary to ArxBehavior."""
        arx_behavior = ArxBehavior()
        
        for name, var_data in behavior_data.get('variables', {}).items():
            arx_behavior.add_variable(name, var_data['value'], var_data.get('unit'))
        
        for name, formula in behavior_data.get('calculations', {}).items():
            arx_behavior.add_calculation(name, formula)
        
        for trigger in behavior_data.get('triggers', []):
            arx_behavior.add_trigger(trigger['event'], trigger['action'])
        
        return arx_behavior
    
    def _arx_physics_to_dict(self, arx_physics: ArxPhysics) -> Dict[str, Any]:
        """Convert ArxPhysics to dictionary."""
        return {
            'mass': arx_physics.mass,
            'anchor': arx_physics.anchor,
            'forces': arx_physics.forces
        }
    
    def _dict_to_arx_physics(self, physics_data: Dict[str, Any]) -> ArxPhysics:
        """Convert dictionary to ArxPhysics."""
        arx_physics = ArxPhysics()
        
        if physics_data.get('mass'):
            mass_data = physics_data['mass']
            arx_physics.set_mass(mass_data['value'], mass_data.get('unit', 'kg'))
        
        if physics_data.get('anchor'):
            arx_physics.set_anchor(physics_data['anchor'])
        
        for force in physics_data.get('forces', []):
            arx_physics.add_force(force['type'], force.get('direction'), force.get('value'))
        
        return arx_physics
    
    def _dict_to_xml(self, tag: str, d: Any) -> ET.Element:
        """Convert dictionary to XML element."""
        elem = ET.Element(tag)
        if isinstance(d, dict):
            for k, v in d.items():
                child = self._dict_to_xml(k, v)
                elem.append(child)
        elif isinstance(d, list):
            for item in d:
                child = self._dict_to_xml('item', item)
                elem.append(child)
        else:
            elem.text = str(d)
        return elem
    
    def _xml_to_dict(self, elem: ET.Element) -> Any:
        """Convert XML element to dictionary."""
        children = list(elem)
        if not children:
            return elem.text
        result = {}
        for child in children:
            key = child.tag
            value = self._xml_to_dict(child)
            if key in result:
                if not isinstance(result[key], list):
                    result[key] = [result[key]]
                result[key].append(value)
            else:
                result[key] = value
        return result 