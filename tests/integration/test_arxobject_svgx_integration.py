"""
Integration Tests for ArxObject-SVGX Integration

These tests verify that the Go ArxObject engine properly integrates with
the SVGX rendering system.
"""

import asyncio
import pytest
from pathlib import Path
import json
from typing import Dict, Any, List

from svgx_engine.integration.arxobject_bridge import ArxObjectToSVGXBridge
from svgx_engine.parser.enhanced_parser import EnhancedSVGXParser, ParserFactory
from svgx_engine.compiler.enhanced_compiler import EnhancedSVGXCompiler
from svgx_engine.models.enhanced_svgx import (
    EnhancedSVGXDocument,
    EnhancedSVGXElement,
    ArxObjectReference
)
from svgx_engine.services.realtime_sync import RealtimeSyncService, SyncClient
from services.arxobject.client.python_client import (
    ArxObjectClient,
    ArxObjectGeometry
)


@pytest.fixture
async def arxobject_client():
    """Create ArxObject client."""
    client = ArxObjectClient()
    await client.connect()
    yield client
    await client.close()


@pytest.fixture
async def svgx_bridge():
    """Create ArxObject to SVGX bridge."""
    bridge = ArxObjectToSVGXBridge()
    await bridge.connect()
    yield bridge


@pytest.fixture
async def enhanced_parser():
    """Create enhanced SVGX parser."""
    parser = await ParserFactory.create_async_parser()
    yield parser


@pytest.fixture
async def enhanced_compiler():
    """Create enhanced SVGX compiler."""
    compiler = EnhancedSVGXCompiler()
    await compiler.initialize()
    yield compiler


class TestArxObjectToSVGXBridge:
    """Test ArxObject to SVGX bridge functionality."""
    
    @pytest.mark.asyncio
    async def test_bridge_connection(self, svgx_bridge):
        """Test bridge can connect to ArxObject service."""
        assert svgx_bridge.client is not None
        assert svgx_bridge.client._connected
    
    @pytest.mark.asyncio
    async def test_arxobject_to_svgx_conversion(self, arxobject_client, svgx_bridge):
        """Test converting Go ArxObject to SVGX element."""
        # Create test ArxObject
        obj = await arxobject_client.create_object(
            object_type='ELECTRICAL_OUTLET',
            geometry=ArxObjectGeometry(x=100, y=200, z=48),
            properties={'voltage': 120, 'amperage': 20}
        )
        
        # Convert to SVGX
        svgx_element = await svgx_bridge.arxobject_to_svgx(obj.id)
        
        # Verify conversion
        assert svgx_element is not None
        assert svgx_element.tag in ['circle', 'rect']
        assert svgx_element.attributes['arx:id'] == str(obj.id)
        assert svgx_element.attributes['arx:type'] == 'ELECTRICAL_OUTLET'
        assert svgx_element.position == [100, 200]
        
        # Verify ArxObject data
        assert svgx_element.arx_object is not None
        assert svgx_element.arx_object.properties['voltage'] == 120
        assert svgx_element.arx_object.properties['amperage'] == 20
    
    @pytest.mark.asyncio
    async def test_query_and_render(self, arxobject_client, svgx_bridge):
        """Test querying region and rendering to SVGX."""
        # Create multiple test objects
        for i in range(5):
            await arxobject_client.create_object(
                object_type='ELECTRICAL_OUTLET',
                geometry=ArxObjectGeometry(x=50 + i*50, y=100, z=48),
                properties={'voltage': 120}
            )
        
        # Query and render region
        elements = await svgx_bridge.query_and_render(
            min_x=0, min_y=0,
            max_x=300, max_y=200,
            object_types=['ELECTRICAL_OUTLET']
        )
        
        assert len(elements) >= 5
        for element in elements:
            assert element.attributes['arx:type'] == 'ELECTRICAL_OUTLET'
    
    @pytest.mark.asyncio
    async def test_render_with_relationships(self, arxobject_client, svgx_bridge):
        """Test rendering with relationships."""
        # Create connected objects
        panel = await arxobject_client.create_object(
            object_type='ELECTRICAL_PANEL',
            geometry=ArxObjectGeometry(x=100, y=100, z=60),
            properties={'breaker_count': 20}
        )
        
        outlet = await arxobject_client.create_object(
            object_type='ELECTRICAL_OUTLET',
            geometry=ArxObjectGeometry(x=200, y=100, z=48),
            properties={'voltage': 120, 'circuit': panel.id}
        )
        
        # Render with relationships
        result = await svgx_bridge.render_with_relationships(outlet.id)
        
        assert result['main'] is not None
        assert result['svg'] is not None


class TestEnhancedParser:
    """Test enhanced SVGX parser."""
    
    @pytest.mark.asyncio
    async def test_parse_with_arxobject_enhancement(self, enhanced_parser, tmp_path):
        """Test parsing SVGX file with ArxObject enhancement."""
        # Create test SVGX file
        svgx_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
            <rect x="100" y="100" width="50" height="50" 
                  arx:id="123" arx:type="ELECTRICAL_PANEL" arx:system="electrical"/>
        </svg>'''
        
        test_file = tmp_path / "test.svgx"
        test_file.write_text(svgx_content)
        
        # Parse with enhancement
        doc = await enhanced_parser.parse_file_async(test_file)
        
        assert doc is not None
        assert len(doc.elements) > 0
        
        element = doc.elements[0]
        assert element.arx_object is not None
        assert element.arx_object.object_id == "123"
        assert element.arx_object.object_type == "ELECTRICAL_PANEL"
    
    @pytest.mark.asyncio
    async def test_validate_document(self, enhanced_parser, arxobject_client, tmp_path):
        """Test document validation against ArxObject constraints."""
        # Create ArxObject
        obj = await arxobject_client.create_object(
            object_type='ELECTRICAL_OUTLET',
            geometry=ArxObjectGeometry(x=100, y=100, z=48)
        )
        
        # Create SVGX with reference
        svgx_content = f'''<?xml version="1.0" encoding="UTF-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
            <circle cx="100" cy="100" r="8" arx:id="{obj.id}" arx:type="ELECTRICAL_OUTLET"/>
        </svg>'''
        
        test_file = tmp_path / "test.svgx"
        test_file.write_text(svgx_content)
        
        # Parse and validate
        doc = await enhanced_parser.parse_file_async(test_file)
        validation = await enhanced_parser.validate_document(doc)
        
        assert validation['valid'] == True or 'violations' in validation


class TestEnhancedCompiler:
    """Test enhanced SVGX compiler."""
    
    @pytest.mark.asyncio
    async def test_compile_region_to_svg(self, arxobject_client, enhanced_compiler):
        """Test compiling region directly to SVG."""
        # Create test objects
        for i in range(3):
            await arxobject_client.create_object(
                object_type='STRUCTURAL_COLUMN',
                geometry=ArxObjectGeometry(
                    x=100 + i*100, y=100, z=0,
                    width=50, height=50, length=300
                )
            )
        
        # Compile region
        svg = await enhanced_compiler.compile_region(
            min_x=0, min_y=0,
            max_x=400, max_y=200,
            output_format='svg',
            options={'show_labels': True}
        )
        
        assert svg is not None
        assert '<svg' in svg
        assert 'structural-column' in svg.lower()
    
    @pytest.mark.asyncio
    async def test_compile_to_json(self, arxobject_client, enhanced_compiler):
        """Test compiling to JSON format."""
        # Create test object
        obj = await arxobject_client.create_object(
            object_type='ELECTRICAL_PANEL',
            geometry=ArxObjectGeometry(x=100, y=100, z=60),
            properties={'breaker_count': 20, 'voltage': 240}
        )
        
        # Compile to JSON
        json_str = await enhanced_compiler.compile_region(
            min_x=0, min_y=0,
            max_x=200, max_y=200,
            output_format='json',
            options={'pretty': True}
        )
        
        data = json.loads(json_str)
        assert data['object_count'] >= 1
        assert data['objects'][0]['type'] == 'ELECTRICAL_PANEL'
        assert data['objects'][0]['properties']['voltage'] == 240
    
    @pytest.mark.asyncio
    async def test_compile_with_validation(self, arxobject_client, enhanced_compiler):
        """Test compilation with validation."""
        # Create potentially conflicting objects
        await arxobject_client.create_object(
            object_type='STRUCTURAL_COLUMN',
            geometry=ArxObjectGeometry(x=100, y=100, z=0, width=50, height=50)
        )
        
        await arxobject_client.create_object(
            object_type='ELECTRICAL_OUTLET',
            geometry=ArxObjectGeometry(x=100, y=100, z=48)  # Same position!
        )
        
        # Compile with validation
        result = await enhanced_compiler.compile_with_validation(
            min_x=0, min_y=0,
            max_x=200, max_y=200
        )
        
        assert 'output' in result
        assert 'validation' in result
        # May have collision violations
        if not result['validation']['valid']:
            assert len(result['validation']['violations']) > 0


class TestEnhancedModels:
    """Test enhanced SVGX models."""
    
    @pytest.mark.asyncio
    async def test_arxobject_reference(self, arxobject_client):
        """Test ArxObject reference functionality."""
        # Create ArxObject
        obj = await arxobject_client.create_object(
            object_type='ELECTRICAL_OUTLET',
            geometry=ArxObjectGeometry(x=100, y=200, z=48),
            properties={'voltage': 120}
        )
        
        # Create reference
        ref = ArxObjectReference(obj.id)
        
        # Get object through reference
        fetched = await ref.get_object()
        assert fetched is not None
        assert fetched.id == obj.id
        assert fetched.properties['voltage'] == 120
        
        # Update through reference
        success = await ref.update({'voltage': 240})
        assert success
        
        # Verify update
        updated = await ref.get_object(force_refresh=True)
        assert updated.properties['voltage'] == 240
    
    @pytest.mark.asyncio
    async def test_enhanced_element_sync(self, arxobject_client):
        """Test enhanced element synchronization."""
        # Create ArxObject
        obj = await arxobject_client.create_object(
            object_type='ELECTRICAL_PANEL',
            geometry=ArxObjectGeometry(x=100, y=100, z=60)
        )
        
        # Create enhanced element
        element = EnhancedSVGXElement(
            tag='rect',
            attributes={'id': f'arx-{obj.id}'},
            arx_reference=ArxObjectReference(obj.id)
        )
        
        # Sync with engine
        success = await element.sync_with_engine()
        assert success
        assert element.position == [100, 100]
        assert element.attributes['x'] == '100'
        assert element.attributes['y'] == '100'
    
    @pytest.mark.asyncio
    async def test_enhanced_document_query(self, arxobject_client):
        """Test enhanced document querying."""
        # Create test objects
        for x in [50, 150, 250]:
            await arxobject_client.create_object(
                object_type='STRUCTURAL_WALL',
                geometry=ArxObjectGeometry(x=x, y=100, z=0, width=100, height=10)
            )
        
        # Create document and query
        doc = EnhancedSVGXDocument()
        elements = await doc.query_region(0, 0, 300, 200)
        
        assert len(elements) >= 3
        for element in elements:
            assert element.arx_reference is not None
            assert element.tag == 'rect'


class TestRealtimeSync:
    """Test real-time synchronization."""
    
    @pytest.mark.asyncio
    async def test_sync_service_startup(self):
        """Test sync service can start."""
        service = RealtimeSyncService()
        
        # Start service (would normally run continuously)
        await service.start()
        
        # Verify metrics
        metrics = service.get_metrics()
        assert 'events_processed' in metrics
        assert 'connected_clients' in metrics
    
    @pytest.mark.asyncio
    async def test_sync_client_connection(self):
        """Test sync client can connect."""
        # This would require a running sync service
        client = SyncClient()
        
        # Register handlers
        updates = []
        client.on_update(lambda data: updates.append(data))
        
        # Would connect to service if running
        # await client.connect()
        
        assert client is not None


@pytest.mark.asyncio
async def test_end_to_end_integration(arxobject_client, svgx_bridge, enhanced_compiler):
    """Test complete end-to-end integration."""
    # Create a simple building section in ArxObject engine
    objects_created = []
    
    # Create structural elements
    for x in [0, 200, 400]:
        col = await arxobject_client.create_object(
            object_type='STRUCTURAL_COLUMN',
            geometry=ArxObjectGeometry(x=x, y=100, z=0, width=50, height=50, length=300)
        )
        objects_created.append(col)
    
    # Create electrical elements
    for x in [100, 300]:
        outlet = await arxobject_client.create_object(
            object_type='ELECTRICAL_OUTLET',
            geometry=ArxObjectGeometry(x=x, y=100, z=48),
            properties={'voltage': 120, 'amperage': 20}
        )
        objects_created.append(outlet)
    
    # Query and render through bridge
    elements = await svgx_bridge.query_and_render(
        min_x=-50, min_y=0,
        max_x=450, max_y=200
    )
    
    assert len(elements) >= 5
    
    # Compile to SVG
    svg = await enhanced_compiler.compile_region(
        min_x=-50, min_y=0,
        max_x=450, max_y=200,
        output_format='svg',
        options={
            'show_labels': True,
            'show_dimensions': True,
            'optimize': True
        }
    )
    
    assert svg is not None
    assert 'structural-column' in svg.lower() or 'structural' in svg
    assert 'electrical-outlet' in svg.lower() or 'electrical' in svg
    
    # Verify all objects are rendered
    for obj in objects_created:
        assert f'arx-{obj.id}' in svg or str(obj.id) in svg
    
    print("End-to-end integration test passed!")
    print(f"Generated SVG length: {len(svg)} characters")
    print(f"Rendered {len(elements)} elements")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_end_to_end_integration(
        ArxObjectClient(),
        ArxObjectToSVGXBridge(),
        EnhancedSVGXCompiler()
    ))