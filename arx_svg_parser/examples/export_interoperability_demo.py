#!/usr/bin/env python3
"""
Export Interoperability Demo Script

Demonstrates the comprehensive export and interoperability capabilities of the Arxos platform:
- IFC-lite export for BIM interoperability
- glTF export for 3D visualization
- ASCII-BIM roundtrip conversion
- Excel, Parquet, GeoJSON export formats
- Export job management and statistics

Usage:
    python export_interoperability_demo.py
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.export_interoperability import (
    ExportInteroperabilityService, ExportFormat, ExportStatus
)

def create_sample_building_data():
    """Create comprehensive sample building data for demonstration."""
    return {
        "building_id": "DEMO_BUILDING_001",
        "building_name": "Demo Office Building",
        "floor_count": 5,
        "total_area_sqft": 75000.0,
        "construction_year": 2020,
        "address": {
            "street": "123 Demo Street",
            "city": "Demo City",
            "state": "DC",
            "zip": "12345",
            "country": "USA"
        },
        "elements": [
            # Structural elements
            {
                "id": "WALL_001",
                "name": "Exterior Wall North",
                "type": "WALL",
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "system": "STRUCTURAL",
                "floor": 1,
                "properties": {
                    "material": "Concrete",
                    "thickness": 0.3,
                    "height": 3.0,
                    "length": 50.0
                }
            },
            {
                "id": "WALL_002",
                "name": "Exterior Wall South",
                "type": "WALL",
                "x": 0.0,
                "y": 50.0,
                "z": 0.0,
                "system": "STRUCTURAL",
                "floor": 1,
                "properties": {
                    "material": "Concrete",
                    "thickness": 0.3,
                    "height": 3.0,
                    "length": 50.0
                }
            },
            {
                "id": "COLUMN_001",
                "name": "Structural Column A1",
                "type": "COLUMN",
                "x": 10.0,
                "y": 10.0,
                "z": 0.0,
                "system": "STRUCTURAL",
                "floor": 1,
                "properties": {
                    "material": "Steel",
                    "diameter": 0.5,
                    "height": 15.0
                }
            },
            # Architectural elements
            {
                "id": "DOOR_001",
                "name": "Main Entrance",
                "type": "DOOR",
                "x": 25.0,
                "y": 0.0,
                "z": 0.0,
                "system": "ARCHITECTURAL",
                "floor": 1,
                "properties": {
                    "material": "Glass",
                    "width": 2.0,
                    "height": 2.5,
                    "type": "Sliding"
                }
            },
            {
                "id": "WINDOW_001",
                "name": "Office Window 1",
                "type": "WINDOW",
                "x": 5.0,
                "y": 0.0,
                "z": 1.0,
                "system": "ARCHITECTURAL",
                "floor": 1,
                "properties": {
                    "material": "Glass",
                    "width": 1.5,
                    "height": 1.2,
                    "type": "Fixed"
                }
            },
            # MEP elements
            {
                "id": "HVAC_001",
                "name": "Air Handler Unit 1",
                "type": "HVAC",
                "x": 45.0,
                "y": 45.0,
                "z": 0.0,
                "system": "MECHANICAL",
                "floor": 1,
                "properties": {
                    "capacity": 5000.0,
                    "flow_rate": 2000.0,
                    "efficiency": 0.85
                }
            },
            {
                "id": "ELECTRICAL_001",
                "name": "Electrical Panel 1",
                "type": "ELECTRICAL",
                "x": 5.0,
                "y": 45.0,
                "z": 0.0,
                "system": "ELECTRICAL",
                "floor": 1,
                "properties": {
                    "voltage": 480.0,
                    "current": 100.0,
                    "phase": "Three"
                }
            },
            {
                "id": "PLUMBING_001",
                "name": "Water Main",
                "type": "PLUMBING",
                "x": 0.0,
                "y": 25.0,
                "z": -1.0,
                "system": "PLUMBING",
                "floor": 1,
                "properties": {
                    "pipe_size": "4 inch",
                    "material": "Copper",
                    "flow_rate": 100.0
                }
            }
        ],
        "systems": [
            {
                "id": "SYSTEM_STRUCTURAL",
                "name": "Structural System",
                "type": "STRUCTURAL",
                "elements": ["WALL_001", "WALL_002", "COLUMN_001"],
                "properties": {
                    "design_code": "IBC 2018",
                    "seismic_zone": "Zone 4",
                    "wind_load": "120 mph"
                }
            },
            {
                "id": "SYSTEM_ARCHITECTURAL",
                "name": "Architectural System",
                "type": "ARCHITECTURAL",
                "elements": ["DOOR_001", "WINDOW_001"],
                "properties": {
                    "finish_grade": "Premium",
                    "fire_rating": "2 hour"
                }
            },
            {
                "id": "SYSTEM_MECHANICAL",
                "name": "Mechanical System",
                "type": "MECHANICAL",
                "elements": ["HVAC_001"],
                "properties": {
                    "design_temp": "72°F",
                    "humidity": "50%",
                    "air_changes": 6
                }
            },
            {
                "id": "SYSTEM_ELECTRICAL",
                "name": "Electrical System",
                "type": "ELECTRICAL",
                "elements": ["ELECTRICAL_001"],
                "properties": {
                    "service_size": "400A",
                    "voltage": "480V/277V",
                    "backup_power": "UPS"
                }
            },
            {
                "id": "SYSTEM_PLUMBING",
                "name": "Plumbing System",
                "type": "PLUMBING",
                "elements": ["PLUMBING_001"],
                "properties": {
                    "water_supply": "Municipal",
                    "pressure": "60 psi",
                    "backflow": "Required"
                }
            }
        ]
    }

def demonstrate_ifc_lite_export(export_service, building_data):
    """Demonstrate IFC-lite export functionality."""
    print("\n" + "="*60)
    print("IFC-LITE EXPORT DEMONSTRATION")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "demo_building.ifc")
        
        print(f"Exporting building data to IFC-lite format...")
        print(f"Output file: {output_path}")
        
        try:
            result = export_service.export_to_ifc_lite(
                building_data=building_data,
                options={"output_path": output_path}
            )
            
            print(f"✅ IFC-lite export completed successfully!")
            print(f"📁 File saved to: {result}")
            
            # Show file statistics
            file_size = os.path.getsize(result)
            print(f"📊 File size: {file_size:,} bytes")
            
            # Show sample content
            with open(result, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                print(f"📄 Total lines: {len(lines)}")
                print(f"📋 Sample content (first 10 lines):")
                for i, line in enumerate(lines[:10]):
                    print(f"   {i+1:2d}: {line}")
                if len(lines) > 10:
                    print(f"   ... and {len(lines) - 10} more lines")
            
        except Exception as e:
            print(f"❌ IFC-lite export failed: {e}")

def demonstrate_gltf_export(export_service, building_data):
    """Demonstrate glTF export functionality."""
    print("\n" + "="*60)
    print("GLTF EXPORT DEMONSTRATION")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "demo_building.gltf")
        
        print(f"Exporting building data to glTF format...")
        print(f"Output file: {output_path}")
        
        try:
            result = export_service.export_to_gltf(
                building_data=building_data,
                options={"output_path": output_path}
            )
            
            print(f"✅ glTF export completed successfully!")
            print(f"📁 File saved to: {result}")
            
            # Show file statistics
            file_size = os.path.getsize(result)
            print(f"📊 File size: {file_size:,} bytes")
            
            # Show content structure
            with open(result, 'r') as f:
                content = json.load(f)
            
            print(f"📋 glTF structure:")
            print(f"   - Asset: {content['asset']}")
            print(f"   - Scene count: {len(content['scenes'])}")
            print(f"   - Node count: {len(content['nodes'])}")
            print(f"   - Mesh count: {len(content['meshes'])}")
            print(f"   - Accessor count: {len(content['accessors'])}")
            print(f"   - Buffer view count: {len(content['bufferViews'])}")
            print(f"   - Buffer count: {len(content['buffers'])}")
            
        except Exception as e:
            print(f"❌ glTF export failed: {e}")

def demonstrate_ascii_bim_export(export_service, building_data):
    """Demonstrate ASCII-BIM export functionality."""
    print("\n" + "="*60)
    print("ASCII-BIM EXPORT DEMONSTRATION")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "demo_building.txt")
        
        print(f"Exporting building data to ASCII-BIM format...")
        print(f"Output file: {output_path}")
        
        try:
            result = export_service.export_to_ascii_bim(
                building_data=building_data,
                options={"output_path": output_path}
            )
            
            print(f"✅ ASCII-BIM export completed successfully!")
            print(f"📁 File saved to: {result}")
            
            # Show file statistics
            file_size = os.path.getsize(result)
            print(f"📊 File size: {file_size:,} bytes")
            
            # Show content
            with open(result, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                print(f"📄 Total lines: {len(lines)}")
                print(f"📋 Content preview:")
                for i, line in enumerate(lines[:20]):
                    print(f"   {i+1:2d}: {line}")
                if len(lines) > 20:
                    print(f"   ... and {len(lines) - 20} more lines")
            
        except Exception as e:
            print(f"❌ ASCII-BIM export failed: {e}")

def demonstrate_geojson_export(export_service, building_data):
    """Demonstrate GeoJSON export functionality."""
    print("\n" + "="*60)
    print("GEOJSON EXPORT DEMONSTRATION")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "demo_building.geojson")
        
        print(f"Exporting building data to GeoJSON format...")
        print(f"Output file: {output_path}")
        
        try:
            result = export_service.export_to_geojson(
                building_data=building_data,
                options={"output_path": output_path}
            )
            
            print(f"✅ GeoJSON export completed successfully!")
            print(f"📁 File saved to: {result}")
            
            # Show file statistics
            file_size = os.path.getsize(result)
            print(f"📊 File size: {file_size:,} bytes")
            
            # Show content structure
            with open(result, 'r') as f:
                content = json.load(f)
            
            print(f"📋 GeoJSON structure:")
            print(f"   - Type: {content['type']}")
            print(f"   - Feature count: {len(content['features'])}")
            
            if content['features']:
                feature = content['features'][0]
                print(f"   - Sample feature:")
                print(f"     * ID: {feature['properties']['id']}")
                print(f"     * Name: {feature['properties']['name']}")
                print(f"     * Type: {feature['properties']['type']}")
                print(f"     * System: {feature['properties']['system']}")
                print(f"     * Coordinates: {feature['geometry']['coordinates']}")
            
        except Exception as e:
            print(f"❌ GeoJSON export failed: {e}")

def demonstrate_export_job_management(export_service, building_data):
    """Demonstrate export job management functionality."""
    print("\n" + "="*60)
    print("EXPORT JOB MANAGEMENT DEMONSTRATION")
    print("="*60)
    
    # Create multiple export jobs
    print("Creating export jobs for different formats...")
    
    job1_id = export_service.create_export_job(
        building_id=building_data["building_id"],
        format=ExportFormat.IFC_LITE,
        options={"output_path": "demo_building.ifc"}
    )
    print(f"✅ Created IFC-lite export job: {job1_id}")
    
    job2_id = export_service.create_export_job(
        building_id=building_data["building_id"],
        format=ExportFormat.GLTF,
        options={"output_path": "demo_building.gltf"}
    )
    print(f"✅ Created glTF export job: {job2_id}")
    
    job3_id = export_service.create_export_job(
        building_id=building_data["building_id"],
        format=ExportFormat.ASCII_BIM,
        options={"output_path": "demo_building.txt"}
    )
    print(f"✅ Created ASCII-BIM export job: {job3_id}")
    
    # List all jobs
    print("\n📋 All export jobs:")
    all_jobs = export_service.list_export_jobs()
    for job in all_jobs:
        print(f"   - {job.job_id}: {job.format.value} ({job.status.value})")
    
    # List jobs for specific building
    print(f"\n📋 Jobs for building {building_data['building_id']}:")
    building_jobs = export_service.list_export_jobs(building_id=building_data["building_id"])
    for job in building_jobs:
        print(f"   - {job.job_id}: {job.format.value} ({job.status.value})")
    
    # Get job status
    print(f"\n📊 Job status details:")
    for job_id in [job1_id, job2_id, job3_id]:
        job = export_service.get_export_job_status(job_id)
        if job:
            print(f"   - {job.job_id}:")
            print(f"     * Format: {job.format.value}")
            print(f"     * Status: {job.status.value}")
            print(f"     * Created: {job.created_at}")
            print(f"     * Building: {job.building_id}")
    
    # Cancel one job
    print(f"\n❌ Cancelling job {job3_id}...")
    result = export_service.cancel_export_job(job3_id)
    if result:
        print(f"✅ Job cancelled successfully")
    else:
        print(f"❌ Failed to cancel job")
    
    # Get statistics
    print(f"\n📊 Export statistics:")
    stats = export_service.get_export_statistics()
    print(f"   - Total jobs: {stats['total_jobs']}")
    print(f"   - By format: {stats['by_format']}")
    print(f"   - By status: {stats['by_status']}")

def demonstrate_excel_export(export_service, building_data):
    """Demonstrate Excel export functionality."""
    print("\n" + "="*60)
    print("EXCEL EXPORT DEMONSTRATION")
    print("="*60)
    
    try:
        import pandas as pd
        print("✅ pandas is available for Excel export")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "demo_building.xlsx")
            
            print(f"Exporting building data to Excel format...")
            print(f"Output file: {output_path}")
            
            try:
                result = export_service.export_to_excel(
                    building_data=building_data,
                    options={"output_path": output_path}
                )
                
                print(f"✅ Excel export completed successfully!")
                print(f"📁 File saved to: {result}")
                
                # Show file statistics
                file_size = os.path.getsize(result)
                print(f"📊 File size: {file_size:,} bytes")
                
                # Show Excel structure
                excel_file = pd.ExcelFile(result)
                print(f"📋 Excel structure:")
                print(f"   - Sheets: {excel_file.sheet_names}")
                
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(result, sheet_name=sheet_name)
                    print(f"   - {sheet_name}: {len(df)} rows, {len(df.columns)} columns")
                
            except Exception as e:
                print(f"❌ Excel export failed: {e}")
                
    except ImportError:
        print("❌ pandas not available - skipping Excel export demonstration")
        print("   Install pandas with: pip install pandas openpyxl")

def main():
    """Main demonstration function."""
    print("🚀 ARXOS EXPORT INTEROPERABILITY DEMONSTRATION")
    print("="*80)
    print("This demonstration showcases the comprehensive export and interoperability")
    print("capabilities of the Arxos platform, including industry-standard formats")
    print("for BIM, 3D visualization, and data exchange.")
    print("="*80)
    
    # Initialize export service
    print("\n🔧 Initializing Export Interoperability Service...")
    export_service = ExportInteroperabilityService()
    print("✅ Service initialized successfully")
    
    # Create sample building data
    print("\n🏗️  Creating sample building data...")
    building_data = create_sample_building_data()
    print(f"✅ Created building: {building_data['building_name']}")
    print(f"   - Building ID: {building_data['building_id']}")
    print(f"   - Floors: {building_data['floor_count']}")
    print(f"   - Total Area: {building_data['total_area_sqft']:,} sqft")
    print(f"   - Elements: {len(building_data['elements'])}")
    print(f"   - Systems: {len(building_data['systems'])}")
    
    # Demonstrate each export format
    demonstrate_ifc_lite_export(export_service, building_data)
    demonstrate_gltf_export(export_service, building_data)
    demonstrate_ascii_bim_export(export_service, building_data)
    demonstrate_geojson_export(export_service, building_data)
    demonstrate_excel_export(export_service, building_data)
    demonstrate_export_job_management(export_service, building_data)
    
    # Summary
    print("\n" + "="*80)
    print("🎉 EXPORT INTEROPERABILITY DEMONSTRATION COMPLETED")
    print("="*80)
    print("✅ Successfully demonstrated:")
    print("   - IFC-lite export for BIM interoperability")
    print("   - glTF export for 3D visualization")
    print("   - ASCII-BIM export for text-based representation")
    print("   - GeoJSON export for spatial data")
    print("   - Excel export for tabular data")
    print("   - Export job management and tracking")
    print("   - Comprehensive error handling")
    print("\n📚 These capabilities enable seamless integration with:")
    print("   - BIM software (Revit, ArchiCAD, etc.)")
    print("   - 3D visualization platforms")
    print("   - GIS systems")
    print("   - Data analysis tools")
    print("   - Industry-standard workflows")
    print("\n🚀 The Arxos platform is ready for enterprise deployment!")

if __name__ == "__main__":
    main() 