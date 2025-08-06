"""
SVGX to IFC Compiler for BIM export.

This module compiles SVGX content to IFC format for BIM interoperability.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SVGXToIFCCompiler:
    """Compiler for converting SVGX to IFC format."""

    def __init__(self):
        self.ifc_version = "IFC4"
        self.project_name = "SVGX_Project"
        self.project_description = "Generated from SVGX content"

    def compile(self, svgx_content: str) -> str:
        """
        Compile SVGX content to IFC format.

        Args:
            svgx_content: SVGX content as string

        Returns:
            IFC content as string
        """
        try:
            # Parse SVGX content using the parser
            from svgx_engine.parser import SVGXParser

            parser = SVGXParser()
            elements = parser.parse(svgx_content)

            # Generate IFC content
            ifc_content = self._generate_ifc_content(elements)

            return ifc_content

        except Exception as e:
            logger.error(f"Failed to compile SVGX to IFC: {e}")
            raise ValueError(f"Compilation failed: {e}")

    def _generate_ifc_content(self, elements: List) -> str:
        """
        Generate IFC content from SVGX elements.

        Args:
            elements: List of parsed SVGX elements

        Returns:
            IFC content as string
        """
        # Start IFC file
        ifc_lines = [
            "ISO-10303-21;",
            "HEADER;",
            f"FILE_DESCRIPTION(('SVGX to IFC export'),'2;1');",
            f"FILE_NAME('{self.project_name}.ifc','{self.project_description}',('Arxos Team'),('Arxos'),'','','');",
            f"FILE_SCHEMA(('{self.ifc_version}'));",
            "ENDSEC;",
            "",
            "DATA;",
            "",
        ]

        # Generate IFC entities
        entity_id = 1

        # Add project
        ifc_lines.extend(self._generate_project_entity(entity_id))
        entity_id += 1

        # Add site
        ifc_lines.extend(self._generate_site_entity(entity_id, entity_id - 1))
        entity_id += 1

        # Add building
        ifc_lines.extend(self._generate_building_entity(entity_id, entity_id - 1))
        entity_id += 1

        # Add building storey
        ifc_lines.extend(self._generate_storey_entity(entity_id, entity_id - 1))
        entity_id += 1

        # Process SVGX objects
        for element in elements:
            if element.arx_object:
                ifc_lines.extend(
                    self._generate_object_entities(element, entity_id, entity_id - 1)
                )
                entity_id += self._count_entities_for_object(element)

        # End IFC file
        ifc_lines.extend(["ENDSEC;", "END-ISO-10303-21;"])

        return "\n".join(ifc_lines)

    def _generate_project_entity(self, entity_id: int) -> List[str]:
        """Generate IFC project entity."""
        return [
            f"#{entity_id}=IFCPROJECT('{self.project_name}',$,{self.project_description},$,$,$,$,());"
        ]

    def _generate_site_entity(self, entity_id: int, project_id: int) -> List[str]:
        """Generate IFC site entity."""
        return [
            f"#{entity_id}=IFCSITE('Site1',$,{self.project_description},$,$,#{project_id},$,$,.ELEMENT.,(0.,0.),$,$);"
        ]

    def _generate_building_entity(self, entity_id: int, site_id: int) -> List[str]:
        """Generate IFC building entity."""
        return [
            f"#{entity_id}=IFCBUILDING('Building1',$,{self.project_description},$,$,#{site_id},$,$,.ELEMENT.,$,$,$);"
        ]

    def _generate_storey_entity(self, entity_id: int, building_id: int) -> List[str]:
        """Generate IFC building storey entity."""
        return [
            f"#{entity_id}=IFCBUILDINGSTOREY('Storey1',$,{self.project_description},$,$,#{building_id},$,$,.ELEMENT.,0.);"
        ]

    def _generate_object_entities(
        self, element, start_id: int, container_id: int
    ) -> List[str]:
        """Generate IFC entities for an SVGX object."""
        entities = []
        current_id = start_id

        obj = element.arx_object
        obj_type = obj.object_type.lower()

        if "room" in obj_type:
            entities.extend(self._generate_room_entity(current_id, container_id, obj))
            current_id += 1
        elif "wall" in obj_type:
            entities.extend(self._generate_wall_entity(current_id, container_id, obj))
            current_id += 1
        elif "electrical" in obj_type:
            entities.extend(
                self._generate_electrical_entity(current_id, container_id, obj)
            )
            current_id += 1
        elif "mechanical" in obj_type:
            entities.extend(
                self._generate_mechanical_entity(current_id, container_id, obj)
            )
            current_id += 1
        else:
            # Generic object
            entities.extend(
                self._generate_generic_entity(current_id, container_id, obj)
            )
            current_id += 1

        return entities

    def _generate_room_entity(
        self, entity_id: int, container_id: int, obj
    ) -> List[str]:
        """Generate IFC room entity."""
        return [
            f"#{entity_id}=IFCSPACE('{obj.object_id}',$,{obj.object_type},$,$,#{container_id},$,$,.ELEMENT.,$,$,$);"
        ]

    def _generate_wall_entity(
        self, entity_id: int, container_id: int, obj
    ) -> List[str]:
        """Generate IFC wall entity."""
        return [
            f"#{entity_id}=IFCWALL('{obj.object_id}',$,{obj.object_type},$,$,#{container_id},$,$,.ELEMENT.,$);"
        ]

    def _generate_electrical_entity(
        self, entity_id: int, container_id: int, obj
    ) -> List[str]:
        """Generate IFC electrical entity."""
        return [
            f"#{entity_id}=IFCDISTRIBUTIONELEMENT('{obj.object_id}',$,{obj.object_type},$,$,#{container_id},$,$,.ELEMENT.,$);"
        ]

    def _generate_mechanical_entity(
        self, entity_id: int, container_id: int, obj
    ) -> List[str]:
        """Generate IFC mechanical entity."""
        return [
            f"#{entity_id}=IFCDISTRIBUTIONELEMENT('{obj.object_id}',$,{obj.object_type},$,$,#{container_id},$,$,.ELEMENT.,$);"
        ]

    def _generate_generic_entity(
        self, entity_id: int, container_id: int, obj
    ) -> List[str]:
        """Generate generic IFC entity."""
        return [
            f"#{entity_id}=IFCBUILDINGELEMENTPROXY('{obj.object_id}',$,{obj.object_type},$,$,#{container_id},$,$,.ELEMENT.,$);"
        ]

    def _count_entities_for_object(self, element) -> int:
        """Count how many IFC entities are needed for an object."""
        # Basic implementation - one entity per object
        return 1

    def compile_file(self, input_file: str, output_file: str):
        """
        Compile SVGX file to IFC file.

        Args:
            input_file: Path to input SVGX file
            output_file: Path to output IFC file
        """
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                svgx_content = f.read()

            ifc_content = self.compile(svgx_content)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(ifc_content)

            logger.info(f"Compiled {input_file} to {output_file}")

        except Exception as e:
            logger.error(f"Failed to compile file {input_file}: {e}")
            raise
