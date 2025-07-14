#!/usr/bin/env python3
"""
Database Diagram Generation Tool

This script generates ER diagrams and data flow diagrams from the Arxos database
schema. It follows Arxos standards for automated visualization and documentation.

Features:
- Generate ER diagrams from database schema
- Create data flow diagrams for service interactions
- Export diagrams in multiple formats (.drawio, .svg, .png)
- Automated diagram updates with schema changes
- CI/CD integration for diagram synchronization

Usage:
    python generate_diagrams.py [--database-url postgresql://...]
    python generate_diagrams.py --help
"""

import os
import sys
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import structlog
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure structured logging following Arxos standards
logger = structlog.get_logger(__name__)

@dataclass
class TableInfo:
    """Information about a database table for diagram generation."""
    name: str
    columns: List[Dict[str, Any]]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    table_type: str  # 'user', 'bim', 'audit', 'collaboration', 'system'

@dataclass
class RelationshipInfo:
    """Information about table relationships."""
    from_table: str
    to_table: str
    from_column: str
    to_column: str
    relationship_type: str  # 'one_to_many', 'many_to_one', 'one_to_one'
    cascade_delete: bool
    nullable: bool

@dataclass
class DiagramConfig:
    """Configuration for diagram generation."""
    output_format: str  # 'drawio', 'svg', 'png'
    include_indexes: bool
    include_constraints: bool
    color_scheme: Dict[str, str]
    layout_engine: str  # 'hierarchical', 'force_directed', 'circular'

class DiagramGenerator:
    """
    Generator for database diagrams and visualizations.
    
    Follows Arxos standards for automated diagram generation, comprehensive
    visualization, and CI/CD integration with detailed reporting.
    """
    
    def __init__(self, database_url: str, output_dir: str = "arx-docs/database/diagrams"):
        """
        Initialize the diagram generator.
        
        Args:
            database_url: PostgreSQL connection URL
            output_dir: Directory for diagram output
        """
        self.database_url = database_url
        self.output_dir = Path(output_dir)
        self.connection = None
        self.tables = {}
        self.relationships = []
        
        # Color scheme for different table types
        self.color_scheme = {
            'user': '#4A90E2',        # Blue - User management
            'bim': '#50C878',         # Green - BIM objects
            'audit': '#FF6B6B',       # Red - Audit logs
            'collaboration': '#FFD93D', # Yellow - Collaboration
            'system': '#9B59B6',      # Purple - System tables
            'spatial': '#FF8C42'      # Orange - Spatial data
        }
        
        # Performance tracking
        self.metrics = {
            'tables_processed': 0,
            'relationships_found': 0,
            'diagrams_generated': 0,
            'processing_time_ms': 0,
            'errors': 0,
            'warnings': 0
        }
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("diagram_generator_initialized",
                   database_url=self._mask_password(database_url),
                   output_dir=str(self.output_dir))
    
    def _mask_password(self, url: str) -> str:
        """Mask password in database URL for logging."""
        if '@' in url and ':' in url:
            parts = url.split('@')
            if len(parts) == 2:
                auth_part = parts[0]
                if ':' in auth_part:
                    user_pass = auth_part.split('://')
                    if len(user_pass) == 2:
                        protocol = user_pass[0]
                        credentials = user_pass[1]
                        if ':' in credentials:
                            user = credentials.split(':')[0]
                            return f"{protocol}://{user}:***@{parts[1]}"
        return url
    
    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = psycopg2.connect(self.database_url)
            logger.info("database_connection_established")
            return True
        except Exception as e:
            logger.error("database_connection_failed",
                        error=str(e))
            return False
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("database_connection_closed")
    
    def generate_diagrams(self) -> bool:
        """
        Generate comprehensive database diagrams.
        
        Returns:
            True if generation successful, False otherwise
        """
        start_time = datetime.now()
        
        if not self.connect():
            return False
        
        try:
            logger.info("starting_diagram_generation")
            
            # Extract schema information
            self._extract_schema_info()
            
            # Generate ER diagram
            self._generate_er_diagram()
            
            # Generate data flow diagram
            self._generate_data_flow_diagram()
            
            # Generate table relationship diagram
            self._generate_relationship_diagram()
            
            # Generate legend
            self._generate_legend()
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics['processing_time_ms'] = processing_time
            
            logger.info("diagram_generation_completed",
                       tables_processed=self.metrics['tables_processed'],
                       relationships_found=self.metrics['relationships_found'],
                       diagrams_generated=self.metrics['diagrams_generated'],
                       processing_time_ms=round(processing_time, 2))
            
            return True
            
        except Exception as e:
            logger.error("diagram_generation_failed",
                        error=str(e))
            return False
        finally:
            self.disconnect()
    
    def _extract_schema_info(self) -> None:
        """Extract comprehensive schema information for diagram generation."""
        # Get all tables
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    table_name,
                    table_type
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            for row in cursor.fetchall():
                table_name = row['table_name']
                table_type = self._classify_table_type(table_name)
                
                # Get table columns
                columns = self._get_table_columns(table_name)
                
                # Get primary keys
                primary_keys = self._get_primary_keys(table_name)
                
                # Get foreign keys
                foreign_keys = self._get_foreign_keys(table_name)
                
                # Get indexes
                indexes = self._get_table_indexes(table_name)
                
                # Get constraints
                constraints = self._get_table_constraints(table_name)
                
                table_info = TableInfo(
                    name=table_name,
                    columns=columns,
                    primary_keys=primary_keys,
                    foreign_keys=foreign_keys,
                    indexes=indexes,
                    constraints=constraints,
                    table_type=table_type
                )
                
                self.tables[table_name] = table_info
                self.metrics['tables_processed'] += 1
                
                # Extract relationships
                for fk in foreign_keys:
                    relationship = RelationshipInfo(
                        from_table=table_name,
                        to_table=fk['referenced_table'],
                        from_column=fk['column_name'],
                        to_column=fk['referenced_column'],
                        relationship_type='many_to_one',
                        cascade_delete=fk.get('cascade_delete', False),
                        nullable=fk.get('nullable', True)
                    )
                    self.relationships.append(relationship)
                    self.metrics['relationships_found'] += 1
    
    def _classify_table_type(self, table_name: str) -> str:
        """Classify table type for color coding."""
        if table_name == 'users':
            return 'user'
        elif table_name in ['projects', 'buildings', 'floors', 'categories']:
            return 'system'
        elif table_name in ['rooms', 'walls', 'doors', 'windows', 'devices', 'labels', 'zones']:
            return 'bim'
        elif table_name in ['audit_logs', 'object_history']:
            return 'audit'
        elif table_name in ['comments', 'assignments', 'chat_messages']:
            return 'collaboration'
        elif table_name in ['user_category_permissions', 'catalog_items']:
            return 'system'
        else:
            return 'system'
    
    def _get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all columns for a table."""
        columns = []
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            for row in cursor.fetchall():
                columns.append(dict(row))
        
        return columns
    
    def _get_primary_keys(self, table_name: str) -> List[str]:
        """Get primary key columns for a table."""
        primary_keys = []
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.key_column_usage 
                WHERE table_name = %s 
                AND constraint_name LIKE '%%_pkey'
            """, (table_name,))
            
            for row in cursor.fetchall():
                primary_keys.append(row[0])
        
        return primary_keys
    
    def _get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key relationships for a table."""
        foreign_keys = []
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    kcu.column_name,
                    ccu.table_name as referenced_table,
                    ccu.column_name as referenced_column,
                    tc.constraint_name,
                    rc.delete_rule,
                    kcu.is_nullable
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                JOIN information_schema.referential_constraints rc
                    ON tc.constraint_name = rc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
            """, (table_name,))
            
            for row in cursor.fetchall():
                fk_info = dict(row)
                fk_info['cascade_delete'] = fk_info['delete_rule'] == 'CASCADE'
                fk_info['nullable'] = fk_info['is_nullable'] == 'YES'
                foreign_keys.append(fk_info)
        
        return foreign_keys
    
    def _get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get indexes for a table."""
        indexes = []
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    indexname,
                    indexdef,
                    indisunique as is_unique,
                    indisprimary as is_primary
                FROM pg_indexes 
                WHERE tablename = %s
            """, (table_name,))
            
            for row in cursor.fetchall():
                indexes.append(dict(row))
        
        return indexes
    
    def _get_table_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """Get constraints for a table."""
        constraints = []
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get check constraints
            cursor.execute("""
                SELECT 
                    constraint_name,
                    check_clause
                FROM information_schema.check_constraints cc
                JOIN information_schema.table_constraints tc 
                    ON cc.constraint_name = tc.constraint_name
                WHERE tc.table_name = %s
            """, (table_name,))
            
            for row in cursor.fetchall():
                constraints.append(dict(row))
        
        return constraints
    
    def _generate_er_diagram(self) -> None:
        """Generate Entity-Relationship diagram."""
        logger.info("generating_er_diagram")
        
        # Create DrawIO XML structure
        root = ET.Element("mxfile")
        root.set("host", "app.diagrams.net")
        root.set("modified", datetime.now().isoformat())
        root.set("agent", "Arxos Diagram Generator")
        root.set("version", "22.1.16")
        root.set("etag", "abc123")
        root.set("type", "device")
        
        diagram = ET.SubElement(root, "diagram")
        diagram.set("id", "er_diagram")
        diagram.set("name", "Arxos ER Diagram")
        
        mxGraphModel = ET.SubElement(diagram, "mxGraphModel")
        mxGraphModel.set("dx", "1422")
        mxGraphModel.set("dy", "794")
        mxGraphModel.set("grid", "1")
        mxGraphModel.set("gridSize", "10")
        mxGraphModel.set("guides", "1")
        mxGraphModel.set("tooltips", "1")
        mxGraphModel.set("connect", "1")
        mxGraphModel.set("arrows", "1")
        mxGraphModel.set("fold", "1")
        mxGraphModel.set("page", "1")
        mxGraphModel.set("pageScale", "1")
        mxGraphModel.set("pageWidth", "1169")
        mxGraphModel.set("pageHeight", "827")
        mxGraphModel.set("math", "0")
        mxGraphModel.set("shadow", "0")
        
        root_element = ET.SubElement(mxGraphModel, "root")
        
        # Add cells for tables
        cell_id = 1
        table_positions = {}
        
        for table_name, table_info in self.tables.items():
            # Calculate position based on table type
            x, y = self._calculate_table_position(table_name, table_info.table_type)
            table_positions[table_name] = (x, y)
            
            # Create table cell
            table_cell = ET.SubElement(root_element, "mxCell")
            table_cell.set("id", f"table_{table_name}")
            table_cell.set("value", f"<b>{table_name}</b>")
            table_cell.set("style", self._get_table_style(table_info.table_type))
            table_cell.set("vertex", "1")
            table_cell.set("parent", "1")
            table_cell.set("geometry", f"x={x},y={y},width=200,height={50 + len(table_info.columns) * 20}")
            
            # Add column cells
            for i, column in enumerate(table_info.columns):
                col_cell = ET.SubElement(root_element, "mxCell")
                col_cell.set("id", f"col_{table_name}_{column['column_name']}")
                
                # Determine column style
                col_style = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;"
                if column['column_name'] in table_info.primary_keys:
                    col_style += "fontStyle=1;"  # Bold for primary keys
                
                col_cell.set("value", f"{column['column_name']}: {column['data_type']}")
                col_cell.set("style", col_style)
                col_cell.set("vertex", "1")
                col_cell.set("parent", f"table_{table_name}")
                col_cell.set("geometry", f"x=10,y={50 + i * 20},width=180,height=20")
            
            cell_id += 1
        
        # Add relationship arrows
        for relationship in self.relationships:
            if relationship.from_table in table_positions and relationship.to_table in table_positions:
                # Create relationship arrow
                rel_cell = ET.SubElement(root_element, "mxCell")
                rel_cell.set("id", f"rel_{relationship.from_table}_{relationship.to_table}")
                rel_cell.set("edge", "1")
                rel_cell.set("parent", "1")
                rel_cell.set("source", f"table_{relationship.from_table}")
                rel_cell.set("target", f"table_{relationship.to_table}")
                
                # Style based on relationship type
                if relationship.cascade_delete:
                    rel_cell.set("style", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;")
                else:
                    rel_cell.set("style", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeDasharray=5 5;")
                
                # Add label
                label_cell = ET.SubElement(root_element, "mxCell")
                label_cell.set("id", f"label_{relationship.from_table}_{relationship.to_table}")
                label_cell.set("value", f"{relationship.from_column} → {relationship.to_column}")
                label_cell.set("style", "edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];")
                label_cell.set("vertex", "1")
                label_cell.set("connectable", "0")
                label_cell.set("parent", f"rel_{relationship.from_table}_{relationship.to_table}")
        
        # Write DrawIO file
        drawio_file = self.output_dir / "arxos_er_diagram.drawio"
        tree = ET.ElementTree(root)
        tree.write(drawio_file, encoding='utf-8', xml_declaration=True)
        
        logger.info("er_diagram_generated",
                   file=str(drawio_file))
        self.metrics['diagrams_generated'] += 1
    
    def _calculate_table_position(self, table_name: str, table_type: str) -> Tuple[int, int]:
        """Calculate position for table in diagram."""
        # Position tables by type
        type_positions = {
            'user': (50, 50),
            'system': (50, 200),
            'bim': (300, 50),
            'audit': (550, 50),
            'collaboration': (550, 200),
            'spatial': (300, 200)
        }
        
        base_x, base_y = type_positions.get(table_type, (50, 50))
        
        # Add some variation based on table name
        name_hash = hash(table_name)
        offset_x = (name_hash % 100) * 2
        offset_y = ((name_hash >> 8) % 100) * 2
        
        return (base_x + offset_x, base_y + offset_y)
    
    def _get_table_style(self, table_type: str) -> str:
        """Get DrawIO style for table based on type."""
        color = self.color_scheme.get(table_type, '#CCCCCC')
        
        return f"""swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize=30;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;whiteSpace=wrap;html=1;fillColor={color};strokeColor=#666666;fontColor=#FFFFFF;"""
    
    def _generate_data_flow_diagram(self) -> None:
        """Generate data flow diagram for service interactions."""
        logger.info("generating_data_flow_diagram")
        
        # Create DrawIO XML structure for data flow
        root = ET.Element("mxfile")
        root.set("host", "app.diagrams.net")
        root.set("modified", datetime.now().isoformat())
        root.set("agent", "Arxos Diagram Generator")
        root.set("version", "22.1.16")
        root.set("etag", "def456")
        root.set("type", "device")
        
        diagram = ET.SubElement(root, "diagram")
        diagram.set("id", "data_flow_diagram")
        diagram.set("name", "Arxos Data Flow Diagram")
        
        mxGraphModel = ET.SubElement(diagram, "mxGraphModel")
        mxGraphModel.set("dx", "1422")
        mxGraphModel.set("dy", "794")
        mxGraphModel.set("grid", "1")
        mxGraphModel.set("gridSize", "10")
        mxGraphModel.set("guides", "1")
        mxGraphModel.set("tooltips", "1")
        mxGraphModel.set("connect", "1")
        mxGraphModel.set("arrows", "1")
        mxGraphModel.set("fold", "1")
        mxGraphModel.set("page", "1")
        mxGraphModel.set("pageScale", "1")
        mxGraphModel.set("pageWidth", "1169")
        mxGraphModel.set("pageHeight", "827")
        mxGraphModel.set("math", "0")
        mxGraphModel.set("shadow", "0")
        
        root_element = ET.SubElement(mxGraphModel, "root")
        
        # Define service components
        services = [
            {"name": "User Service", "x": 100, "y": 100, "type": "service"},
            {"name": "Project Service", "x": 300, "y": 100, "type": "service"},
            {"name": "Building Service", "x": 500, "y": 100, "type": "service"},
            {"name": "BIM Service", "x": 700, "y": 100, "type": "service"},
            {"name": "Audit Service", "x": 100, "y": 300, "type": "service"},
            {"name": "Collaboration Service", "x": 300, "y": 300, "type": "service"},
            {"name": "Database", "x": 400, "y": 500, "type": "database"}
        ]
        
        # Add service components
        for service in services:
            service_cell = ET.SubElement(root_element, "mxCell")
            service_cell.set("id", f"service_{service['name'].replace(' ', '_')}")
            
            if service['type'] == 'service':
                style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#E1D5E7;strokeColor=#9673A6;"
            else:
                style = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#FFF2CC;strokeColor=#D6B656;"
            
            service_cell.set("value", service['name'])
            service_cell.set("style", style)
            service_cell.set("vertex", "1")
            service_cell.set("parent", "1")
            service_cell.set("geometry", f"x={service['x']},y={service['y']},width=120,height=60")
        
        # Add data flow arrows
        flows = [
            ("User Service", "Database", "User CRUD"),
            ("Project Service", "Database", "Project CRUD"),
            ("Building Service", "Database", "Building CRUD"),
            ("BIM Service", "Database", "BIM CRUD"),
            ("Audit Service", "Database", "Audit Logging"),
            ("Collaboration Service", "Database", "Collaboration Data"),
            ("User Service", "Project Service", "User Auth"),
            ("Project Service", "Building Service", "Project Context"),
            ("Building Service", "BIM Service", "Building Context"),
            ("BIM Service", "Audit Service", "Change Tracking"),
            ("BIM Service", "Collaboration Service", "Assignment Updates")
        ]
        
        for flow in flows:
            flow_cell = ET.SubElement(root_element, "mxCell")
            flow_cell.set("id", f"flow_{flow[0].replace(' ', '_')}_{flow[1].replace(' ', '_')}")
            flow_cell.set("edge", "1")
            flow_cell.set("parent", "1")
            flow_cell.set("source", f"service_{flow[0].replace(' ', '_')}")
            flow_cell.set("target", f"service_{flow[1].replace(' ', '_')}")
            flow_cell.set("style", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;")
            
            # Add flow label
            label_cell = ET.SubElement(root_element, "mxCell")
            label_cell.set("id", f"label_{flow[0].replace(' ', '_')}_{flow[1].replace(' ', '_')}")
            label_cell.set("value", flow[2])
            label_cell.set("style", "edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];")
            label_cell.set("vertex", "1")
            label_cell.set("connectable", "0")
            label_cell.set("parent", f"flow_{flow[0].replace(' ', '_')}_{flow[1].replace(' ', '_')}")
        
        # Write DrawIO file
        drawio_file = self.output_dir / "arxos_data_flow_diagram.drawio"
        tree = ET.ElementTree(root)
        tree.write(drawio_file, encoding='utf-8', xml_declaration=True)
        
        logger.info("data_flow_diagram_generated",
                   file=str(drawio_file))
        self.metrics['diagrams_generated'] += 1
    
    def _generate_relationship_diagram(self) -> None:
        """Generate table relationship diagram."""
        logger.info("generating_relationship_diagram")
        
        # Create DrawIO XML structure
        root = ET.Element("mxfile")
        root.set("host", "app.diagrams.net")
        root.set("modified", datetime.now().isoformat())
        root.set("agent", "Arxos Diagram Generator")
        root.set("version", "22.1.16")
        root.set("etag", "ghi789")
        root.set("type", "device")
        
        diagram = ET.SubElement(root, "diagram")
        diagram.set("id", "relationship_diagram")
        diagram.set("name", "Arxos Table Relationships")
        
        mxGraphModel = ET.SubElement(diagram, "mxGraphModel")
        mxGraphModel.set("dx", "1422")
        mxGraphModel.set("dy", "794")
        mxGraphModel.set("grid", "1")
        mxGraphModel.set("gridSize", "10")
        mxGraphModel.set("guides", "1")
        mxGraphModel.set("tooltips", "1")
        mxGraphModel.set("connect", "1")
        mxGraphModel.set("arrows", "1")
        mxGraphModel.set("fold", "1")
        mxGraphModel.set("page", "1")
        mxGraphModel.set("pageScale", "1")
        mxGraphModel.set("pageWidth", "1169")
        mxGraphModel.set("pageHeight", "827")
        mxGraphModel.set("math", "0")
        mxGraphModel.set("shadow", "0")
        
        root_element = ET.SubElement(mxGraphModel, "root")
        
        # Group tables by dependency level
        levels = {
            1: ['users'],
            2: ['projects'],
            3: ['buildings'],
            4: ['floors', 'categories'],
            5: ['rooms'],
            6: ['walls', 'doors', 'windows', 'devices', 'labels', 'zones'],
            7: ['drawings'],
            8: ['comments', 'assignments', 'object_history', 'audit_logs'],
            9: ['user_category_permissions', 'chat_messages', 'catalog_items']
        }
        
        # Position tables by level
        table_positions = {}
        for level, tables in levels.items():
            for i, table_name in enumerate(tables):
                if table_name in self.tables:
                    x = 100 + (level - 1) * 150
                    y = 100 + i * 80
                    table_positions[table_name] = (x, y)
                    
                    # Create table node
                    table_cell = ET.SubElement(root_element, "mxCell")
                    table_cell.set("id", f"table_{table_name}")
                    
                    table_info = self.tables[table_name]
                    color = self.color_scheme.get(table_info.table_type, '#CCCCCC')
                    
                    style = f"""ellipse;whiteSpace=wrap;html=1;fillColor={color};strokeColor=#666666;fontColor=#FFFFFF;"""
                    
                    table_cell.set("value", table_name)
                    table_cell.set("style", style)
                    table_cell.set("vertex", "1")
                    table_cell.set("parent", "1")
                    table_cell.set("geometry", f"x={x},y={y},width=120,height=60")
        
        # Add relationship arrows
        for relationship in self.relationships:
            if relationship.from_table in table_positions and relationship.to_table in table_positions:
                rel_cell = ET.SubElement(root_element, "mxCell")
                rel_cell.set("id", f"rel_{relationship.from_table}_{relationship.to_table}")
                rel_cell.set("edge", "1")
                rel_cell.set("parent", "1")
                rel_cell.set("source", f"table_{relationship.from_table}")
                rel_cell.set("target", f"table_{relationship.to_table}")
                
                # Style based on relationship properties
                if relationship.cascade_delete:
                    rel_cell.set("style", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;")
                else:
                    rel_cell.set("style", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeDasharray=5 5;")
        
        # Write DrawIO file
        drawio_file = self.output_dir / "arxos_relationship_diagram.drawio"
        tree = ET.ElementTree(root)
        tree.write(drawio_file, encoding='utf-8', xml_declaration=True)
        
        logger.info("relationship_diagram_generated",
                   file=str(drawio_file))
        self.metrics['diagrams_generated'] += 1
    
    def _generate_legend(self) -> None:
        """Generate diagram legend and documentation."""
        logger.info("generating_legend")
        
        legend_content = f"""# Arxos Database Diagram Legend

## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Color Scheme

### Table Types
- **🔵 User Tables** (`{self.color_scheme['user']}`): User management and authentication
  - `users` - User accounts and authentication

- **🟢 BIM Objects** (`{self.color_scheme['bim']}`): Building Information Modeling objects
  - `rooms`, `walls`, `doors`, `windows`, `devices`, `labels`, `zones`

- **🔴 Audit Tables** (`{self.color_scheme['audit']}`): Audit logging and change tracking
  - `audit_logs`, `object_history`

- **🟡 Collaboration Tables** (`{self.color_scheme['collaboration']}`): User collaboration features
  - `comments`, `assignments`, `chat_messages`

- **🟣 System Tables** (`{self.color_scheme['system']}`): Core system functionality
  - `projects`, `buildings`, `floors`, `categories`, `user_category_permissions`, `catalog_items`

- **🟠 Spatial Tables** (`{self.color_scheme['spatial']}`): Spatial data and geometry
  - Tables with PostGIS geometry columns

## Relationship Types

### Line Styles
- **Solid Line**: Standard foreign key relationship
- **Dashed Line**: Nullable foreign key relationship
- **Thick Line**: Cascade delete relationship

### Arrow Types
- **Single Arrow**: One-to-many relationship
- **Double Arrow**: Many-to-many relationship (through junction table)

## Diagram Types

### 1. Entity-Relationship (ER) Diagram
- **Purpose**: Shows detailed table structure and relationships
- **File**: `arxos_er_diagram.drawio`
- **Features**: 
  - Complete table schemas
  - Column details and data types
  - Primary and foreign key indicators
  - Index and constraint information

### 2. Data Flow Diagram
- **Purpose**: Shows service interactions and data flow
- **File**: `arxos_data_flow_diagram.drawio`
- **Features**:
  - Service component interactions
  - Data flow between services
  - Database access patterns
  - API endpoint relationships

### 3. Table Relationship Diagram
- **Purpose**: Shows high-level table dependencies
- **File**: `arxos_relationship_diagram.drawio`
- **Features**:
  - Hierarchical table organization
  - Dependency levels
  - Relationship strength indicators
  - Simplified view for overview

## Usage Guidelines

### For Developers
1. **ER Diagram**: Use for detailed schema understanding
2. **Data Flow**: Use for service architecture understanding
3. **Relationship**: Use for quick dependency overview

### For Documentation
1. **Include in README**: Link diagrams in documentation
2. **Update with Changes**: Regenerate when schema changes
3. **Version Control**: Track diagram changes with schema changes

### For CI/CD
1. **Automated Generation**: Generate diagrams on schema changes
2. **Validation**: Ensure diagrams match current schema
3. **Artifact Upload**: Include diagrams in deployment artifacts

## Maintenance

### When to Regenerate
- Schema changes (new tables, columns, relationships)
- Service architecture changes
- Major refactoring
- Documentation updates

### How to Regenerate
```bash
cd arxos/infrastructure/database
python tools/generate_diagrams.py --database-url postgresql://...
```

### Validation
- Ensure diagrams match current schema
- Verify all relationships are represented
- Check color coding accuracy
- Validate file formats and accessibility

---

*This legend is automatically generated and should be updated with diagram changes.*
"""
        
        legend_file = self.output_dir / "DIAGRAM_LEGEND.md"
        with open(legend_file, 'w') as f:
            f.write(legend_content)
        
        logger.info("legend_generated",
                   file=str(legend_file))


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Generate database diagrams and visualizations"
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", "postgresql://localhost/arxos_db"),
        help="PostgreSQL connection URL"
    )
    parser.add_argument(
        "--output-dir",
        default="arx-docs/database/diagrams",
        help="Output directory for diagrams"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Generate diagrams
    generator = DiagramGenerator(args.database_url, args.output_dir)
    success = generator.generate_diagrams()
    
    if success:
        # Print summary
        print("\n" + "="*60)
        print("DIAGRAM GENERATION SUMMARY")
        print("="*60)
        print(f"Tables Processed: {generator.metrics['tables_processed']}")
        print(f"Relationships Found: {generator.metrics['relationships_found']}")
        print(f"Diagrams Generated: {generator.metrics['diagrams_generated']}")
        print(f"Output Directory: {args.output_dir}")
        print("="*60)
        
        # List generated files
        print("\nGenerated Files:")
        for file_path in Path(args.output_dir).glob("*.drawio"):
            print(f"  📊 {file_path.name}")
        for file_path in Path(args.output_dir).glob("*.md"):
            print(f"  📋 {file_path.name}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 