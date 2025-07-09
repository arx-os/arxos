"""
Advanced Export & Interoperability CLI

Command-line interface for BIM data export in various industry-standard formats.
Supports IFC-lite, glTF, ASCII-BIM, Excel, Parquet, and GeoJSON formats.
"""

import click
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import time
from datetime import datetime

from services.advanced_export_interoperability import (
    AdvancedExportInteroperabilityService,
    ExportFormat
)

# Initialize service
export_service = AdvancedExportInteroperabilityService()

@click.group()
def export():
    """Advanced Export & Interoperability CLI for BIM data export."""
    pass

@export.command()
@click.option('--input', '-i', 'input_file', required=True, help='Input BIM data file (JSON)')
@click.option('--output', '-o', 'output_file', required=True, help='Output file path')
@click.option('--format', '-f', 'export_format', required=True, 
              type=click.Choice(['ifc-lite', 'gltf', 'ascii-bim', 'excel', 'parquet', 'geojson']),
              help='Export format')
@click.option('--options', '-opt', 'options_file', help='Export options file (JSON)')
@click.option('--validate', is_flag=True, help='Validate data before export')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def export_data(input_file, output_file, export_format, options_file, validate, verbose):
    """
    Export BIM data to specified format.
    
    Examples:
        arx export data -i data.json -o output.ifc -f ifc-lite
        arx export data -i data.json -o output.gltf -f gltf --validate
        arx export data -i data.json -o output.xlsx -f excel --options opts.json
    """
    try:
        if verbose:
            click.echo(f"Starting export: {input_file} -> {output_file} ({export_format})")
        
        # Load input data
        if verbose:
            click.echo("Loading input data...")
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Load options if provided
        options = None
        if options_file:
            if verbose:
                click.echo("Loading export options...")
            with open(options_file, 'r') as f:
                options = json.load(f)
        
        # Validate data if requested
        if validate:
            if verbose:
                click.echo("Validating data...")
            
            validation_result = validate_bim_data(data)
            if not validation_result["valid"]:
                click.echo("❌ Validation failed:", err=True)
                for error in validation_result["errors"]:
                    click.echo(f"  - {error}", err=True)
                sys.exit(1)
            
            if validation_result["warnings"]:
                click.echo("⚠️  Validation warnings:")
                for warning in validation_result["warnings"]:
                    click.echo(f"  - {warning}")
        
        # Perform export
        if verbose:
            click.echo("Performing export...")
        
        start_time = time.time()
        exported_path = export_service.export(
            data=data,
            format=export_format,
            output_path=output_file,
            options=options
        )
        end_time = time.time()
        
        # Verify export
        if not exported_path.exists():
            click.echo("❌ Export failed: File not created", err=True)
            sys.exit(1)
        
        file_size = exported_path.stat().st_size
        export_time = end_time - start_time
        
        click.echo("✅ Export completed successfully!")
        click.echo(f"  Format: {export_format}")
        click.echo(f"  Output: {exported_path}")
        click.echo(f"  Size: {file_size:,} bytes")
        click.echo(f"  Time: {export_time:.2f} seconds")
        
    except Exception as e:
        click.echo(f"❌ Export failed: {str(e)}", err=True)
        sys.exit(1)

@export.command()
@click.option('--input', '-i', 'input_file', required=True, help='Input BIM data file (JSON)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def validate(input_file, verbose):
    """
    Validate BIM data for export.
    
    Examples:
        arx export validate -i data.json
        arx export validate -i data.json --verbose
    """
    try:
        if verbose:
            click.echo(f"Validating BIM data: {input_file}")
        
        # Load input data
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Perform validation
        validation_result = validate_bim_data(data)
        
        if validation_result["valid"]:
            click.echo("✅ Data validation passed!")
            
            if validation_result["warnings"]:
                click.echo("⚠️  Warnings:")
                for warning in validation_result["warnings"]:
                    click.echo(f"  - {warning}")
        else:
            click.echo("❌ Data validation failed:", err=True)
            for error in validation_result["errors"]:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"❌ Validation failed: {str(e)}", err=True)
        sys.exit(1)

@export.command()
def formats():
    """
    List supported export formats.
    
    Examples:
        arx export formats
    """
    formats_info = [
        {
            "format": "ifc-lite",
            "name": "IFC-Lite",
            "description": "Industry Foundation Classes for BIM interoperability",
            "extensions": [".ifc"],
            "category": "BIM"
        },
        {
            "format": "gltf",
            "name": "glTF",
            "description": "3D visualization format for web and mobile",
            "extensions": [".gltf", ".glb"],
            "category": "Visualization"
        },
        {
            "format": "ascii-bim",
            "name": "ASCII-BIM",
            "description": "Text-based BIM format for roundtrip conversion",
            "extensions": [".bim"],
            "category": "BIM"
        },
        {
            "format": "excel",
            "name": "Excel",
            "description": "Microsoft Excel format for data analysis",
            "extensions": [".xlsx"],
            "category": "Analytics"
        },
        {
            "format": "parquet",
            "name": "Parquet",
            "description": "Columnar storage format for big data analytics",
            "extensions": [".parquet"],
            "category": "Analytics"
        },
        {
            "format": "geojson",
            "name": "GeoJSON",
            "description": "Geographic data format for GIS applications",
            "extensions": [".geojson"],
            "category": "GIS"
        }
    ]
    
    click.echo("📋 Supported Export Formats:")
    click.echo()
    
    for fmt in formats_info:
        click.echo(f"🔹 {fmt['name']} ({fmt['format']})")
        click.echo(f"   Description: {fmt['description']}")
        click.echo(f"   Category: {fmt['category']}")
        click.echo(f"   Extensions: {', '.join(fmt['extensions'])}")
        click.echo()

@export.command()
@click.option('--input', '-i', 'input_file', required=True, help='Input BIM data file (JSON)')
@click.option('--output-dir', '-o', 'output_dir', default='./exports', help='Output directory')
@click.option('--formats', '-f', 'export_formats', 
              default='ifc-lite,gltf,excel,geojson',
              help='Comma-separated list of formats to export')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def batch_export(input_file, output_dir, export_formats, verbose):
    """
    Export BIM data to multiple formats in batch.
    
    Examples:
        arx export batch -i data.json
        arx export batch -i data.json -f "ifc-lite,gltf,excel"
        arx export batch -i data.json -o ./exports --verbose
    """
    try:
        if verbose:
            click.echo(f"Starting batch export: {input_file}")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Load input data
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Parse formats
        formats_list = [f.strip() for f in export_formats.split(',')]
        
        # Validate formats
        valid_formats = ['ifc-lite', 'gltf', 'ascii-bim', 'excel', 'parquet', 'geojson']
        invalid_formats = [f for f in formats_list if f not in valid_formats]
        if invalid_formats:
            click.echo(f"❌ Invalid formats: {', '.join(invalid_formats)}", err=True)
            sys.exit(1)
        
        # Generate base filename
        base_name = Path(input_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = []
        total_start_time = time.time()
        
        for fmt in formats_list:
            try:
                if verbose:
                    click.echo(f"Exporting to {fmt}...")
                
                # Generate output filename
                if fmt == 'ifc-lite':
                    output_file = output_path / f"{base_name}_{timestamp}.ifc"
                elif fmt == 'gltf':
                    output_file = output_path / f"{base_name}_{timestamp}.gltf"
                elif fmt == 'ascii-bim':
                    output_file = output_path / f"{base_name}_{timestamp}.bim"
                elif fmt == 'excel':
                    output_file = output_path / f"{base_name}_{timestamp}.xlsx"
                elif fmt == 'parquet':
                    output_file = output_path / f"{base_name}_{timestamp}.parquet"
                elif fmt == 'geojson':
                    output_file = output_path / f"{base_name}_{timestamp}.geojson"
                
                # Perform export
                start_time = time.time()
                exported_path = export_service.export(
                    data=data,
                    format=fmt,
                    output_path=output_file,
                    options=None
                )
                end_time = time.time()
                
                file_size = exported_path.stat().st_size
                export_time = end_time - start_time
                
                results.append({
                    "format": fmt,
                    "success": True,
                    "file_path": str(exported_path),
                    "file_size": file_size,
                    "export_time": export_time
                })
                
                if verbose:
                    click.echo(f"  ✅ {fmt}: {file_size:,} bytes ({export_time:.2f}s)")
                
            except Exception as e:
                results.append({
                    "format": fmt,
                    "success": False,
                    "error": str(e)
                })
                
                if verbose:
                    click.echo(f"  ❌ {fmt}: {str(e)}")
        
        total_time = time.time() - total_start_time
        
        # Summary
        click.echo()
        click.echo("📊 Batch Export Summary:")
        click.echo(f"  Total time: {total_time:.2f} seconds")
        click.echo(f"  Successful: {len([r for r in results if r['success']])}")
        click.echo(f"  Failed: {len([r for r in results if not r['success']])}")
        
        if verbose:
            click.echo()
            click.echo("📁 Exported files:")
            for result in results:
                if result['success']:
                    click.echo(f"  ✅ {result['file_path']} ({result['file_size']:,} bytes)")
                else:
                    click.echo(f"  ❌ {result['format']}: {result['error']}")
        
    except Exception as e:
        click.echo(f"❌ Batch export failed: {str(e)}", err=True)
        sys.exit(1)

def validate_bim_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate BIM data structure.
    
    Args:
        data: BIM data to validate
        
    Returns:
        Validation result with valid flag, errors, and warnings
    """
    errors = []
    warnings = []
    
    # Check required fields
    required_fields = ["elements", "metadata"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check data types
    if "elements" in data and not isinstance(data["elements"], list):
        errors.append("Elements should be a list")
    
    if "metadata" in data and not isinstance(data["metadata"], dict):
        errors.append("Metadata should be a dictionary")
    
    # Check for empty data
    if "elements" in data and len(data["elements"]) == 0:
        warnings.append("No elements found in data")
    
    # Check element structure
    if "elements" in data and isinstance(data["elements"], list):
        for i, element in enumerate(data["elements"]):
            if not isinstance(element, dict):
                errors.append(f"Element {i} should be a dictionary")
            elif "id" not in element:
                warnings.append(f"Element {i} missing 'id' field")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

if __name__ == "__main__":
    export() 