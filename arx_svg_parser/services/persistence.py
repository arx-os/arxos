"""
Persistence Service for SVG-BIM System

Provides functions to save/load BIM assemblies and SVGs in various formats (JSON, XML, SVG),
with robust error handling and user-friendly API.
"""
import json
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
import logging
from pathlib import Path
from utils.errors import ExportError, ValidationError

logger = logging.getLogger(__name__)

class PersistenceService:
    """
    Service for saving and loading BIM assemblies and SVGs.
    """
    def save_bim_json(self, bim_data: Dict[str, Any], file_path: str) -> None:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(bim_data, f, indent=2)
            logger.info(f"BIM data saved to JSON: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save BIM JSON: {e}")
            raise ExportError(f"Failed to save BIM JSON: {e}") from e

    def load_bim_json(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"BIM data loaded from JSON: {file_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load BIM JSON: {e}")
            raise ValidationError(f"Failed to load BIM JSON: {e}") from e

    def save_bim_xml(self, bim_data: Dict[str, Any], file_path: str) -> None:
        try:
            root = self._dict_to_xml('BIMAssembly', bim_data)
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            logger.info(f"BIM data saved to XML: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save BIM XML: {e}")
            raise ExportError(f"Failed to save BIM XML: {e}") from e

    def load_bim_xml(self, file_path: str) -> Dict[str, Any]:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            data = self._xml_to_dict(root)
            logger.info(f"BIM data loaded from XML: {file_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load BIM XML: {e}")
            raise ValidationError(f"Failed to load BIM XML: {e}") from e

    def save_svg(self, svg_content: str, file_path: str) -> None:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            logger.info(f"SVG saved: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save SVG: {e}")
            raise ExportError(f"Failed to save SVG: {e}") from e

    def load_svg(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"SVG loaded: {file_path}")
            return content
        except Exception as e:
            logger.error(f"Failed to load SVG: {e}")
            raise ValidationError(f"Failed to load SVG: {e}") from e

    def _dict_to_xml(self, tag: str, d: Any) -> ET.Element:
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