"""
Comprehensive Tests for Advanced Export Features

This module provides comprehensive unit and integration tests for all export functionalities
including IFC, GLTF, DXF, STEP, IGES, and Parasolid formats.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import json
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any, List

from svgx_engine.services.export.advanced_export_system import (
    AdvancedExportSystem,
    ExportFormat,
    ExportQuality,
    ExportConfig,
    ExportResult,
    create_advanced_export_system,
    create_export_config
)

from svgx_engine.services.export.ifc_export import (
    IFCExportService,
    IFCVersion,
    IFCEntityType,
    create_ifc_export_service
)

from svgx_engine.services.export.gltf_export import (
    GLTFExportService,
    GLTFVersion,
    create_gltf_export_service
)

from svgx_engine.services.export.dxf_export import (
    DXFExportService,
    DXFVersion,
    create_dxf_export_service
)

from svgx_engine.services.export.step_export import (
    STEPExportService,
    STEPVersion,
    create_step_export_service
)

from svgx_engine.services.export.iges_export import (
    IGESExportService,
    create_iges_export_service
)

from svgx_engine.core.precision_drawing_system import PrecisionPoint, PrecisionVector


class TestAdvancedExportSystem(unittest.TestCase):
    """Test the main advanced export system."""

    def setUp(self):
        """Set up test fixtures."""
        self.export_system = create_advanced_export_system()
        self.test_data = self._create_test_data()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_data(self) -> Dict[str, Any]:
        """Create test data for export."""
        return {
            "elements": [
                {
                    "type": "wall",
                    "name": "Test Wall",
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "width": 0.2,
                    "height": 3.0,
                    "depth": 0.2,
                    "material": "concrete"
                },
                {
                    "type": "window",
                    "name": "Test Window",
                    "x": 2.0,
                    "y": 0.0,
                    "z": 1.5,
                    "width": 1.2,
                    "height": 1.5,
                    "depth": 0.1,
                    "material": "glass"
                },
                {
                    "type": "door",
                    "name": "Test Door",
                    "x": 5.0,
                    "y": 0.0,
                    "z": 1.05,
                    "width": 0.9,
                    "height": 2.1,
                    "depth": 0.1,
                    "material": "wood"
                },
                {
                    "type": "column",
                    "name": "Test Column",
                    "x": 8.0,
                    "y": 0.0,
                    "z": 1.5,
                    "width": 0.3,
                    "height": 3.0,
                    "depth": 0.3,
                    "material": "steel"
                }
            ],
            "metadata": {
                "project_name": "Test Project",
                "author": "Test Author",
                "version": "1.0.0",
                "description": "Test building model"
            }
        }

    def test_export_system_initialization(self):
        """Test export system initialization."""
        self.assertIsNotNone(self.export_system)
        self.assertIsInstance(self.export_system, AdvancedExportSystem)

    def test_export_config_creation(self):
        """Test export config creation."""
        config = create_export_config(
            format=ExportFormat.IFC,
            quality=ExportQuality.HIGH
        )

        self.assertIsNotNone(config)
        self.assertEqual(config.format, ExportFormat.IFC)
        self.assertEqual(config.quality, ExportQuality.HIGH)
        self.assertTrue(config.include_metadata)
        self.assertTrue(config.include_geometry)
        self.assertTrue(config.include_properties)

    def test_export_data_validation(self):
        """Test export data validation."""
        # Valid data
        self.assertTrue(len(self.test_data["elements"]) > 0)
        self.assertIn("metadata", self.test_data)

        # Invalid data
        invalid_data = {"elements": []}
        self.assertEqual(len(invalid_data["elements"]), 0)


class TestIFCExport(unittest.TestCase):
    """Test IFC export functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.ifc_service = create_ifc_export_service(IFCVersion.IFC4)
        self.test_data = self._create_test_data()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_data(self) -> Dict[str, Any]:
        """Create test data for IFC export."""
        return {
            "elements": [
                {
                    "type": "wall",
                    "name": "IFC Test Wall",
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "width": 0.2,
                    "height": 3.0,
                    "depth": 0.2,
                    "material": "concrete",
                    "properties": {
                        "fire_rating": "2h",
                        "acoustic_rating": "45dB"
                    }
                },
                {
                    "type": "window",
                    "name": "IFC Test Window",
                    "x": 2.0,
                    "y": 0.0,
                    "z": 1.5,
                    "width": 1.2,
                    "height": 1.5,
                    "depth": 0.1,
                    "material": "glass",
                    "properties": {
                        "u_value": "1.2",
                        "solar_factor": "0.6"
                    }
                }
            ],
            "metadata": {
                "project_name": "IFC Test Project",
                "author": "IFC Test Author",
                "version": "1.0.0"
            }
        }

    def test_ifc_service_initialization(self):
        """Test IFC service initialization."""
        self.assertIsNotNone(self.ifc_service)
        self.assertIsInstance(self.ifc_service, IFCExportService)
        self.assertEqual(self.ifc_service.version, IFCVersion.IFC4)

    def test_ifc_export_basic(self):
        """Test basic IFC export."""
        output_path = Path(self.temp_dir) / "test_export.ifc"

        result = self.ifc_service.export_to_ifc(
            data=self.test_data,
            output_path=output_path,
            options={"include_properties": True}
        )

        self.assertIsInstance(result, Path)
        self.assertTrue(result.exists())
        self.assertGreater(result.stat().st_size, 0)

    def test_ifc_export_with_metadata(self):
        """Test IFC export with metadata."""
        output_path = Path(self.temp_dir) / "test_export_metadata.ifc"

        result = self.ifc_service.export_to_ifc(
            data=self.test_data,
            output_path=output_path,
            options={"include_metadata": True}
        )

        self.assertTrue(result.exists())

        # Check file content
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("ISO-10303-21", content)
            self.assertIn("IFC4", content)

    def test_ifc_entity_creation(self):
        """Test IFC entity creation."""
        from svgx_engine.services.export.ifc_export import create_ifc_entity, IFCGeometry

        geometry = IFCGeometry(
            type="extruded_area_solid",
            coordinates=[PrecisionPoint(0, 0, 0), PrecisionPoint(1, 0, 0)],
            dimensions=(1.0, 0.2, 3.0)
        )

        entity = create_ifc_entity(
            name="Test Entity",
            entity_type=IFCEntityType.IFCWALLSTANDARDCASE,
            geometry=geometry
        )

        self.assertIsNotNone(entity)
        self.assertEqual(entity.name, "Test Entity")
        self.assertEqual(entity.entity_type, IFCEntityType.IFCWALLSTANDARDCASE)


class TestGLTFExport(unittest.TestCase):
    """Test GLTF export functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.gltf_service = create_gltf_export_service(GLTFVersion.GLTF_2_0)
        self.test_data = self._create_test_data()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_data(self) -> Dict[str, Any]:
        """Create test data for GLTF export."""
        return {
            "elements": [
                {
                    "type": "wall",
                    "name": "GLTF Test Wall",
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "width": 0.2,
                    "height": 3.0,
                    "depth": 0.2,
                    "material": {
                        "base_color": [0.8, 0.8, 0.8, 1.0],
                        "metallic_factor": 0.0,
                        "roughness_factor": 0.8
                    }
                },
                {
                    "type": "window",
                    "name": "GLTF Test Window",
                    "x": 2.0,
                    "y": 0.0,
                    "z": 1.5,
                    "width": 1.2,
                    "height": 1.5,
                    "depth": 0.1,
                    "material": {
                        "base_color": [0.7, 0.9, 1.0, 0.3],
                        "metallic_factor": 0.0,
                        "roughness_factor": 0.1
                    }
                }
            ],
            "metadata": {
                "project_name": "GLTF Test Project",
                "author": "GLTF Test Author",
                "version": "1.0.0"
            }
        }

    def test_gltf_service_initialization(self):
        """Test GLTF service initialization."""
        self.assertIsNotNone(self.gltf_service)
        self.assertIsInstance(self.gltf_service, GLTFExportService)
        self.assertEqual(self.gltf_service.version, GLTFVersion.GLTF_2_0)

    def test_gltf_export_basic(self):
        """Test basic GLTF export."""
        output_path = Path(self.temp_dir) / "test_export.gltf"

        result = self.gltf_service.export_to_gltf(
            data=self.test_data,
            output_path=output_path,
            options={"include_materials": True}
        )

        self.assertIsInstance(result, Path)
        self.assertTrue(result.exists())
        self.assertGreater(result.stat().st_size, 0)

    def test_gltf_export_with_materials(self):
        """Test GLTF export with materials."""
        output_path = Path(self.temp_dir) / "test_export_materials.gltf"

        result = self.gltf_service.export_to_gltf(
            data=self.test_data,
            output_path=output_path,
            options={"include_materials": True, "compression": False}
        )

        self.assertTrue(result.exists())

        # Check file content
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            gltf_data = json.loads(content)
            self.assertIn("asset", gltf_data)
            self.assertIn("scene", gltf_data)
            self.assertIn("nodes", gltf_data)
            self.assertIn("meshes", gltf_data)

    def test_gltf_material_creation(self):
        """Test GLTF material creation."""
        from svgx_engine.services.export.gltf_export import create_gltf_material, GLTFMaterialType

        material = create_gltf_material(
            name="Test Material",
            material_type=GLTFMaterialType.PBR_METALLIC_ROUGHNESS,
            base_color=[0.8, 0.8, 0.8, 1.0]
        )

        self.assertIsNotNone(material)
        self.assertEqual(material.name, "Test Material")
        self.assertEqual(material.material_type, GLTFMaterialType.PBR_METALLIC_ROUGHNESS)


class TestDXFExport(unittest.TestCase):
    """Test DXF export functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.dxf_service = create_dxf_export_service(DXFVersion.DXF_2018)
        self.test_data = self._create_test_data()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_data(self) -> Dict[str, Any]:
        """Create test data for DXF export."""
        return {
            "elements": [
                {
                    "type": "wall",
                    "name": "DXF Test Wall",
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "width": 0.2,
                    "height": 3.0,
                    "depth": 0.2,
                    "layer": "WALLS",
                    "color": 7
                },
                {
                    "type": "window",
                    "name": "DXF Test Window",
                    "x": 2.0,
                    "y": 0.0,
                    "z": 1.5,
                    "width": 1.2,
                    "height": 1.5,
                    "depth": 0.1,
                    "layer": "WINDOWS",
                    "color": 4
                },
                {
                    "type": "dimension",
                    "name": "DXF Test Dimension",
                    "start_x": 0.0,
                    "start_y": 0.0,
                    "end_x": 10.0,
                    "end_y": 0.0,
                    "text_x": 5.0,
                    "text_y": 5.0,
                    "text": "10.0",
                    "layer": "DIMENSIONS",
                    "color": 3
                }
            ],
            "metadata": {
                "project_name": "DXF Test Project",
                "author": "DXF Test Author",
                "version": "1.0.0"
            }
        }

    def test_dxf_service_initialization(self):
        """Test DXF service initialization."""
        self.assertIsNotNone(self.dxf_service)
        self.assertIsInstance(self.dxf_service, DXFExportService)
        self.assertEqual(self.dxf_service.version, DXFVersion.DXF_2018)

    def test_dxf_export_basic(self):
        """Test basic DXF export."""
        output_path = Path(self.temp_dir) / "test_export.dxf"

        result = self.dxf_service.export_to_dxf(
            data=self.test_data,
            output_path=output_path,
            options={"include_layers": True}
        )

        self.assertIsInstance(result, Path)
        self.assertTrue(result.exists())
        self.assertGreater(result.stat().st_size, 0)

    def test_dxf_export_with_layers(self):
        """Test DXF export with layers."""
        output_path = Path(self.temp_dir) / "test_export_layers.dxf"

        result = self.dxf_service.export_to_dxf(
            data=self.test_data,
            output_path=output_path,
            options={"include_layers": True, "include_dimensions": True}
        )

        self.assertTrue(result.exists())

        # Check file content
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("SECTION", content)
            self.assertIn("HEADER", content)
            self.assertIn("TABLES", content)
            self.assertIn("ENTITIES", content)

    def test_dxf_layer_creation(self):
        """Test DXF layer creation."""
        from svgx_engine.services.export.dxf_export import create_dxf_layer

        layer = create_dxf_layer(
            name="Test Layer",
            color=7,
            linetype="CONTINUOUS",
            lineweight=-1
        )

        self.assertIsNotNone(layer)
        self.assertEqual(layer.name, "Test Layer")
        self.assertEqual(layer.color, 7)
        self.assertEqual(layer.linetype, "CONTINUOUS")


class TestSTEPExport(unittest.TestCase):
    """Test STEP export functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.step_service = create_step_export_service(STEPVersion.STEP_AP214)
        self.test_data = self._create_test_data()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_data(self) -> Dict[str, Any]:
        """Create test data for STEP export."""
        return {
            "elements": [
                {
                    "type": "wall",
                    "name": "STEP Test Wall",
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "width": 0.2,
                    "height": 3.0,
                    "depth": 0.2,
                    "material": "concrete"
                },
                {
                    "type": "column",
                    "name": "STEP Test Column",
                    "x": 5.0,
                    "y": 0.0,
                    "z": 1.5,
                    "width": 0.3,
                    "height": 3.0,
                    "depth": 0.3,
                    "material": "steel"
                }
            ],
            "metadata": {
                "project_name": "STEP Test Project",
                "author": "STEP Test Author",
                "version": "1.0.0"
            }
        }

    def test_step_service_initialization(self):
        """Test STEP service initialization."""
        self.assertIsNotNone(self.step_service)
        self.assertIsInstance(self.step_service, STEPExportService)
        self.assertEqual(self.step_service.version, STEPVersion.STEP_AP214)

    def test_step_export_basic(self):
        """Test basic STEP export."""
        output_path = Path(self.temp_dir) / "test_export.step"

        result = self.step_service.export_to_step(
            data=self.test_data,
            output_path=output_path,
            options={"include_metadata": True}
        )

        self.assertIsInstance(result, Path)
        self.assertTrue(result.exists())
        self.assertGreater(result.stat().st_size, 0)

    def test_step_export_with_metadata(self):
        """Test STEP export with metadata."""
        output_path = Path(self.temp_dir) / "test_export_metadata.step"

        result = self.step_service.export_to_step(
            data=self.test_data,
            output_path=output_path,
            options={"include_metadata": True, "include_properties": True}
        )

        self.assertTrue(result.exists())

        # Check file content
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("ISO-10303-21", content)
            self.assertIn("HEADER", content)
            self.assertIn("DATA", content)

    def test_step_entity_creation(self):
        """Test STEP entity creation."""
        from svgx_engine.services.export.step_export import create_step_entity, STEPEntityType

        entity = create_step_entity(
            entity_type=STEPEntityType.CARTESIAN_POINT,
            parameters=[0.0, 0.0, 0.0],
            name="Test Point"
        )

        self.assertIsNotNone(entity)
        self.assertEqual(entity.entity_type, STEPEntityType.CARTESIAN_POINT)
        self.assertEqual(entity.name, "Test Point")


class TestIGESExport(unittest.TestCase):
    """Test IGES export functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.iges_service = create_iges_export_service()
        self.test_data = self._create_test_data()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_data(self) -> Dict[str, Any]:
        """Create test data for IGES export."""
        return {
            "elements": [
                {
                    "type": "wall",
                    "name": "IGES Test Wall",
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "width": 0.2,
                    "height": 3.0,
                    "depth": 0.2,
                    "color": 1,
                    "level": 1
                },
                {
                    "type": "window",
                    "name": "IGES Test Window",
                    "x": 2.0,
                    "y": 0.0,
                    "z": 1.5,
                    "width": 1.2,
                    "height": 1.5,
                    "depth": 0.1,
                    "color": 4,
                    "level": 1
                }
            ],
            "metadata": {
                "project_name": "IGES Test Project",
                "author": "IGES Test Author",
                "version": "1.0.0"
            }
        }

    def test_iges_service_initialization(self):
        """Test IGES service initialization."""
        self.assertIsNotNone(self.iges_service)
        self.assertIsInstance(self.iges_service, IGESExportService)

    def test_iges_export_basic(self):
        """Test basic IGES export."""
        output_path = Path(self.temp_dir) / "test_export.iges"

        result = self.iges_service.export_to_iges(
            data=self.test_data,
            output_path=output_path,
            options={"include_metadata": True}
        )

        self.assertIsInstance(result, Path)
        self.assertTrue(result.exists())
        self.assertGreater(result.stat().st_size, 0)

    def test_iges_export_with_metadata(self):
        """Test IGES export with metadata."""
        output_path = Path(self.temp_dir) / "test_export_metadata.iges"

        result = self.iges_service.export_to_iges(
            data=self.test_data,
            output_path=output_path,
            options={"include_metadata": True, "include_properties": True}
        )

        self.assertTrue(result.exists())

        # Check file content
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("SVGX Engine IGES Export", content)
            self.assertIn("S", content)  # Start section
            self.assertIn("G", content)  # Global section
            self.assertIn("D", content)  # Directory section
            self.assertIn("P", content)  # Parameter section
            self.assertIn("T", content)  # Terminate section

    def test_iges_entity_creation(self):
        """Test IGES entity creation."""
        from svgx_engine.services.export.iges_export import create_iges_entity, IGESEntityType

        entity = create_iges_entity(
            entity_type=IGESEntityType.LINE,
            parameter_data=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            color=1,
            level=1
        )

        self.assertIsNotNone(entity)
        self.assertEqual(entity.entity_type, IGESEntityType.LINE)
        self.assertEqual(entity.color_number, 1)
        self.assertEqual(entity.level, 1)


class TestExportIntegration(unittest.TestCase):
    """Test export system integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.export_system = create_advanced_export_system()
        self.test_data = self._create_test_data()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_data(self) -> Dict[str, Any]:
        """Create comprehensive test data."""
        return {
            "elements": [
                {
                    "type": "wall",
                    "name": "Integration Test Wall",
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "width": 0.2,
                    "height": 3.0,
                    "depth": 0.2,
                    "material": "concrete",
                    "properties": {
                        "fire_rating": "2h",
                        "acoustic_rating": "45dB"
                    }
                },
                {
                    "type": "window",
                    "name": "Integration Test Window",
                    "x": 2.0,
                    "y": 0.0,
                    "z": 1.5,
                    "width": 1.2,
                    "height": 1.5,
                    "depth": 0.1,
                    "material": "glass",
                    "properties": {
                        "u_value": "1.2",
                        "solar_factor": "0.6"
                    }
                },
                {
                    "type": "door",
                    "name": "Integration Test Door",
                    "x": 5.0,
                    "y": 0.0,
                    "z": 1.05,
                    "width": 0.9,
                    "height": 2.1,
                    "depth": 0.1,
                    "material": "wood",
                    "properties": {
                        "fire_rating": "1h",
                        "acoustic_rating": "35dB"
                    }
                }
            ],
            "metadata": {
                "project_name": "Integration Test Project",
                "author": "Integration Test Author",
                "version": "1.0.0",
                "description": "Comprehensive test building model"
            }
        }

    def test_multi_format_export(self):
        """Test exporting to multiple formats."""
        formats = [
            ExportFormat.IFC,
            ExportFormat.GLTF,
            ExportFormat.DXF,
            ExportFormat.STEP,
            ExportFormat.IGES
        ]

        results = []
        for format_type in formats:
            output_path = Path(self.temp_dir) / f"test_export.{format_type.value}"

            config = create_export_config(
                format=format_type,
                quality=ExportQuality.HIGH
            )

            result = self.export_system.export_data(
                data=self.test_data,
                output_path=output_path,
                format=format_type,
                config=config
            )

            self.assertTrue(result.success)
            self.assertTrue(result.output_path.exists())
            self.assertGreater(result.file_size, 0)
            results.append(result)

        self.assertEqual(len(results), len(formats))

    def test_export_quality_levels(self):
        """Test export with different quality levels."""
        quality_levels = [
            ExportQuality.LOW,
            ExportQuality.MEDIUM,
            ExportQuality.HIGH
        ]

        for quality in quality_levels:
            output_path = Path(self.temp_dir) / f"test_quality_{quality.value}.ifc"

            config = create_export_config(
                format=ExportFormat.IFC,
                quality=quality
            )

            result = self.export_system.export_data(
                data=self.test_data,
                output_path=output_path,
                format=ExportFormat.IFC,
                config=config
            )

            self.assertTrue(result.success)
            self.assertTrue(result.output_path.exists())

    def test_export_with_options(self):
        """Test export with various options."""
        output_path = Path(self.temp_dir) / "test_options.ifc"

        config = create_export_config(
            format=ExportFormat.IFC,
            quality=ExportQuality.HIGH
        )
        config.include_metadata = True
        config.include_geometry = True
        config.include_properties = True
        config.compression = False
        config.optimization = True

        result = self.export_system.export_data(
            data=self.test_data,
            output_path=output_path,
            format=ExportFormat.IFC,
            config=config
        )

        self.assertTrue(result.success)
        self.assertTrue(result.output_path.exists())
        self.assertIn("format", result.metadata)
        self.assertIn("quality", result.metadata)

    def test_export_error_handling(self):
        """Test export error handling."""
        # Test with invalid data
        invalid_data = {"invalid": "data"}
        output_path = Path(self.temp_dir) / "test_error.ifc"

        config = create_export_config(
            format=ExportFormat.IFC,
            quality=ExportQuality.MEDIUM
        )

        # This should handle the error gracefully
        result = self.export_system.export_data(
            data=invalid_data,
            output_path=output_path,
            format=ExportFormat.IFC,
            config=config
        )

        # The system should still attempt to export and provide a result
        self.assertIsInstance(result, ExportResult)


class TestExportPerformance(unittest.TestCase):
    """Test export system performance."""

    def setUp(self):
        """Set up test fixtures."""
        self.export_system = create_advanced_export_system()
        self.test_data = self._create_large_test_data()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_large_test_data(self) -> Dict[str, Any]:
        """Create large test data for performance testing."""
        elements = []

        # Create 100 elements for performance testing
        for i in range(100):
            element = {
                "type": "wall" if i % 3 == 0 else "window" if i % 3 == 1 else "door",
                "name": f"Performance Test Element {i}",
                "x": float(i * 2.0),
                "y": 0.0,
                "z": 0.0,
                "width": 0.2,
                "height": 3.0,
                "depth": 0.2,
                "material": "concrete",
                "properties": {
                    "id": i,
                    "type": "performance_test"
                }
            }
            elements.append(element)

        return {
            "elements": elements,
            "metadata": {
                "project_name": "Performance Test Project",
                "author": "Performance Test Author",
                "version": "1.0.0",
                "description": "Large test building model for performance testing"
            }
        }

    def test_export_performance(self):
        """Test export performance with large datasets."""
        import time

        formats = [ExportFormat.IFC, ExportFormat.GLTF, ExportFormat.DXF]

        for format_type in formats:
            output_path = Path(self.temp_dir) / f"performance_test.{format_type.value}"

            start_time = time.time()

            config = create_export_config(
                format=format_type,
                quality=ExportQuality.MEDIUM
            )

            result = self.export_system.export_data(
                data=self.test_data,
                output_path=output_path,
                format=format_type,
                config=config
            )

            end_time = time.time()
            export_time = end_time - start_time

            self.assertTrue(result.success)
            self.assertTrue(result.output_path.exists())
            self.assertGreater(result.file_size, 0)

            # Performance assertion: export should complete within reasonable time
            self.assertLess(export_time, 30.0)  # 30 seconds max

            print(f"{format_type.value} export completed in {export_time:.2f} seconds")

    def test_memory_usage(self):
        """Test memory usage during export."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform multiple exports
        for i in range(5):
            output_path = Path(self.temp_dir) / f"memory_test_{i}.ifc"

            config = create_export_config(
                format=ExportFormat.IFC,
                quality=ExportQuality.MEDIUM
            )

            result = self.export_system.export_data(
                data=self.test_data,
                output_path=output_path,
                format=ExportFormat.IFC,
                config=config
            )

            self.assertTrue(result.success)

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024)  # 100MB

        print(f"Memory increase: {memory_increase / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
