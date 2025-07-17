"""
SVGX Engine Persistence Export Service.

This service provides persistent export capabilities for SVGX Engine including:
- Robust serialization for all SVGX types
- Exporters for multiple formats (JSON, XML, CSV, IFC, gbXML, SVGX)
- Database integration hooks for SQL, NoSQL, and graph databases
- Interoperability with external BIM systems
- SVGX-specific persistence strategies
- Job management and monitoring
- Performance optimization and error recovery
"""

import json
import csv
import xml.etree.ElementTree as ET
import sqlite3
import logging
import time
import threading
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import uuid
import pickle
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed

from svgx_engine.services.export_interoperability import SVGXExportInteroperabilityService

try:
    from svgx_engine.utils.performance import PerformanceMonitor
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.performance import PerformanceMonitor

from svgx_engine.models.svgx import SVGXDocument, SVGXElement
from svgx_engine.models.bim import BIMElement, BIMSystem, BIMSpace

try:
    from svgx_engine.utils.errors import (
        PersistenceExportError, ExportError, ValidationError, 
        DatabaseError, JobError
    )
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import (
        PersistenceExportError, ExportError, ValidationError, 
        DatabaseError, JobError
    )



class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    IFC = "ifc"
    GBXML = "gbxml"
    SVGX = "svgx"
    PICKLE = "pickle"
    SQLITE = "sqlite"


class DatabaseType(Enum):
    """Supported database types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    NEO4J = "neo4j"


class JobStatus(Enum):
    """Export job status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class ExportOptions:
    """Options for export operations."""
    format: ExportFormat
    include_metadata: bool = True
    include_geometry: bool = True
    include_properties: bool = True
    include_relationships: bool = True
    pretty_print: bool = True
    compression: bool = False
    coordinate_system: str = "local"
    units: str = "meters"
    svgx_optimization_enabled: bool = True
    batch_size: int = 1000
    timeout: int = 300  # 5 minutes


@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_type: DatabaseType
    connection_string: str
    table_name: str = "svgx_models"
    create_tables: bool = True
    batch_size: int = 1000


@dataclass
class ExportJob:
    """Export job information."""
    job_id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    total_items: int = 0
    processed_items: int = 0
    error_message: Optional[str] = None
    result_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SVGXSerializer:
    """Robust serialization for all SVGX types."""
    
    @staticmethod
    def to_dict(obj: Any) -> Dict[str, Any]:
        """Convert any SVGX object to dictionary."""
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        elif isinstance(obj, (list, tuple)):
            return [SVGXSerializer.to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: SVGXSerializer.to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return {k: SVGXSerializer.to_dict(v) for k, v in obj.__dict__.items()}
        else:
            return obj
    
    @staticmethod
    def from_dict(data: Dict[str, Any], target_class: type) -> Any:
        """Create SVGX object from dictionary."""
        if hasattr(target_class, 'from_dict'):
            return target_class.from_dict(data)
        elif hasattr(target_class, 'parse_obj'):
            return target_class.parse_obj(data)
        else:
            return target_class(**data)
    
    @staticmethod
    def to_json(obj: Any, pretty: bool = True) -> str:
        """Convert SVGX object to JSON string."""
        data = SVGXSerializer.to_dict(obj)
        
        # Filter data based on options
        if not options.include_metadata:
            data.pop('metadata', None)
        if not options.include_geometry:
            self._remove_geometry_from_dict(data)
        if not options.include_properties:
            self._remove_properties_from_dict(data)
        if not options.include_relationships:
            self._remove_relationships_from_dict(data)
        
        # Apply SVGX optimizations if enabled
        if options.svgx_optimization_enabled:
            data = self._apply_svgx_optimizations(data)
        
        if options.pretty_print:
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)
    
    @staticmethod
    def from_json(json_str: str, target_class: type) -> Any:
        """Create SVGX object from JSON string."""
        data = json.loads(json_str)
        return SVGXSerializer.from_dict(data, target_class)
    
    @staticmethod
    def to_pickle(obj: Any) -> bytes:
        """Convert SVGX object to pickle bytes."""
        return pickle.dumps(obj)
    
    @staticmethod
    def from_pickle(pickle_bytes: bytes) -> Any:
        """Create SVGX object from pickle bytes."""
        return pickle.loads(pickle_bytes)


class SVGXExporter:
    """Export SVGX documents to various formats."""
    
    def __init__(self):
        self.serializer = SVGXSerializer()
        self.logger = logging.getLogger(__name__)
    
    def export_svgx_document(self, svgx_document: SVGXDocument, options: ExportOptions) -> Union[str, bytes]:
        """Export SVGX document to specified format."""
        try:
            if options.format == ExportFormat.JSON:
                return self._export_to_json(svgx_document, options)
            elif options.format == ExportFormat.XML:
                return self._export_to_xml(svgx_document, options)
            elif options.format == ExportFormat.CSV:
                return self._export_to_csv(svgx_document, options)
            elif options.format == ExportFormat.IFC:
                return self._export_to_ifc(svgx_document, options)
            elif options.format == ExportFormat.GBXML:
                return self._export_to_gbxml(svgx_document, options)
            elif options.format == ExportFormat.SVGX:
                return self._export_to_svgx(svgx_document, options)
            elif options.format == ExportFormat.PICKLE:
                return self._export_to_pickle(svgx_document, options)
            else:
                raise ExportError(f"Unsupported export format: {options.format}")
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            raise ExportError(f"Export failed: {e}") from e
    
    def _export_to_json(self, svgx_document: SVGXDocument, options: ExportOptions) -> str:
        """Export to JSON format."""
        data = self.serializer.to_dict(svgx_document)
        
        # Filter data based on options
        if not options.include_metadata:
            data.pop('metadata', None)
        if not options.include_geometry:
            self._remove_geometry_from_dict(data)
        if not options.include_properties:
            self._remove_properties_from_dict(data)
        if not options.include_relationships:
            self._remove_relationships_from_dict(data)
        
        # Apply SVGX optimizations if enabled
        if options.svgx_optimization_enabled:
            data = self._apply_svgx_optimizations(data)
        
        if options.pretty_print:
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)
    
    def _export_to_xml(self, svgx_document: SVGXDocument, options: ExportOptions) -> str:
        """Export to XML format."""
        data = self.serializer.to_dict(svgx_document)
        
        # Filter data based on options
        if not options.include_metadata:
            data.pop('metadata', None)
        if not options.include_geometry:
            self._remove_geometry_from_dict(data)
        if not options.include_properties:
            self._remove_properties_from_dict(data)
        if not options.include_relationships:
            self._remove_relationships_from_dict(data)
        
        # Apply SVGX optimizations if enabled
        if options.svgx_optimization_enabled:
            data = self._apply_svgx_optimizations(data)
        
        root = self._dict_to_xml('SVGXDocument', data)
        return ET.tostring(root, encoding='unicode', method='xml')
    
    def _export_to_csv(self, svgx_document: SVGXDocument, options: ExportOptions) -> str:
        """Export to CSV format."""
        # Extract elements for CSV export
        elements = []
        for element in svgx_document.elements:
            element_data = {
                'id': element.id,
                'type': element.tag,
                'properties': json.dumps(element.properties),
                'metadata': json.dumps(element.metadata)
            }
            elements.append(element_data)
        
        # Write to CSV
        output = []
        if elements:
            fieldnames = elements[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(elements)
        
        return ''.join(output)
    
    def _export_to_ifc(self, svgx_document: SVGXDocument, options: ExportOptions) -> str:
        """Export to IFC format."""
        # Convert SVGX to IFC format
        ifc_content = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('SVGX Export'),'2;1');
FILE_NAME('{svgx_document.id}.ifc','{datetime.now().isoformat()}',('SVGX Engine'),('SVGX Engine'),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('{svgx_document.id}',#2,'SVGX Project',$,#3,$,$,$,(#4),#5);
#2=IFCOWNERHISTORY(#6,$,.ADDED.,$,#6,$,0);
#3=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#7,$);
#4=IFCUNITASSIGNMENT((#8,#9,#10));
#5=IFCGEOMETRICREPRESENTATIONSUBCONTEXT('Body','Model',*,*,*,*,#3,$,.MODEL_VIEW.,$);
#6=IFCPERSONANDORGANIZATION(#11,#12,$);
#7=IFCDIRECTION((0.,0.,1.));
#8=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#9=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
#10=IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
#11=IFCPERSON('SVGX','Engine',$,$,$,$,$,$);
#12=IFCORGANIZATION('SVGX','Engine',$,$);
ENDSEC;
END-ISO-10303-21;"""
        
        return ifc_content
    
    def _export_to_gbxml(self, svgx_document: SVGXDocument, options: ExportOptions) -> str:
        """Export to gbXML format."""
        # Convert SVGX to gbXML format
        gbxml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<gbXML xmlns="http://www.gbxml.org/schema" 
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
       xsi:schemaLocation="http://www.gbxml.org/schema http://www.gbxml.org/schema/0-37/GreenBuildingXML_Ver6_01.xsd"
       version="0.37" temperatureUnit="C" lengthUnit="Meters" areaUnit="SquareMeters" volumeUnit="CubicMeters" useSIUnitsForResults="true">
  <Campus id="SVGX_Campus">
    <Building id="SVGX_Building" buildingType="SVGX" area="0">
      <Space id="SVGX_Space" conditionType="HeatedAndCooled">
        <Name>SVGX Space</Name>
        <Area>0</Area>
        <Volume>0</Volume>
      </Space>
    </Building>
  </Campus>
</gbXML>"""
        
        return gbxml_content
    
    def _export_to_svgx(self, svgx_document: SVGXDocument, options: ExportOptions) -> str:
        """Export to SVGX format."""
        # Export as native SVGX format
        svgx_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svgx:document xmlns:svgx="http://www.svgx.org/schema" 
               id="{svgx_document.id}"
               version="1.0"
               created="{datetime.now().isoformat()}">
    <svgx:metadata>
        <svgx:property name="document_id" value="{svgx_document.id}"/>
        <svgx:property name="element_count" value="{len(svgx_document.elements)}"/>
        <svgx:property name="export_format" value="svgx"/>
    </svgx:metadata>
    <svgx:elements>"""
        
        for element in svgx_document.elements:
            svgx_content += f"""
        <svgx:element id="{element.id}" type="{element.tag}">
            <svgx:properties>{json.dumps(element.properties)}</svgx:properties>
            <svgx:metadata>{json.dumps(element.metadata)}</svgx:metadata>
        </svgx:element>"""
        
        svgx_content += """
    </svgx:elements>
</svgx:document>"""
        
        return svgx_content
    
    def _export_to_pickle(self, svgx_document: SVGXDocument, options: ExportOptions) -> bytes:
        """Export to pickle format."""
        return self.serializer.to_pickle(svgx_document)
    
    def _dict_to_xml(self, tag: str, data: Any) -> ET.Element:
        """Convert dictionary to XML element."""
        element = ET.Element(tag)
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    child = self._dict_to_xml(key, value)
                    element.append(child)
                elif isinstance(value, list):
                    for item in value:
                        child = self._dict_to_xml(key, item)
                        element.append(child)
                else:
                    child = ET.SubElement(element, key)
                    child.text = str(value)
        else:
            element.text = str(data)
        
        return element
    
    def _remove_geometry_from_dict(self, data: Dict[str, Any]) -> None:
        """Remove geometry data from dictionary."""
        if isinstance(data, dict):
            data.pop('geometry', None)
            data.pop('coordinates', None)
            data.pop('bounds', None)
            for value in data.values():
                if isinstance(value, dict):
                    self._remove_geometry_from_dict(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            self._remove_geometry_from_dict(item)
    
    def _remove_properties_from_dict(self, data: Dict[str, Any]) -> None:
        """Remove properties data from dictionary."""
        if isinstance(data, dict):
            data.pop('properties', None)
            data.pop('attributes', None)
            for value in data.values():
                if isinstance(value, dict):
                    self._remove_properties_from_dict(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            self._remove_properties_from_dict(item)
    
    def _remove_relationships_from_dict(self, data: Dict[str, Any]) -> None:
        """Remove relationships data from dictionary."""
        if isinstance(data, dict):
            data.pop('relationships', None)
            data.pop('connections', None)
            data.pop('dependencies', None)
            for value in data.values():
                if isinstance(value, dict):
                    self._remove_relationships_from_dict(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            self._remove_relationships_from_dict(item)
    
    def _apply_svgx_optimizations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply SVGX-specific optimizations to data."""
        # Remove unnecessary whitespace and optimize structure
        if isinstance(data, dict):
            # Remove empty fields
            data = {k: v for k, v in data.items() if v is not None and v != ""}
            
            # Optimize metadata
            if 'metadata' in data and isinstance(data['metadata'], dict):
                data['metadata'] = {k: v for k, v in data['metadata'].items() 
                                  if v is not None and v != ""}
        
        return data


class DatabaseInterface(ABC):
    """Abstract database interface."""
    
    @abstractmethod
    def connect(self) -> None:
        """Connect to database."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from database."""
        pass
    
    @abstractmethod
    def save_svgx_document(self, svgx_document: SVGXDocument, document_id: str) -> None:
        """Save SVGX document to database."""
        pass
    
    @abstractmethod
    def load_svgx_document(self, document_id: str) -> SVGXDocument:
        """Load SVGX document from database."""
        pass
    
    @abstractmethod
    def list_documents(self) -> List[str]:
        """List all document IDs."""
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> None:
        """Delete document from database."""
        pass


class SQLiteInterface(DatabaseInterface):
    """SQLite database interface."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> None:
        """Connect to SQLite database."""
        try:
            self.connection = sqlite3.connect(self.config.connection_string)
            if self.config.create_tables:
                self._create_tables()
        except Exception as e:
            self.logger.error(f"Failed to connect to SQLite: {e}")
            raise DatabaseError(f"SQLite connection failed: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from SQLite database."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def save_svgx_document(self, svgx_document: SVGXDocument, document_id: str) -> None:
        """Save SVGX document to SQLite."""
        try:
            if not self.connection:
                self.connect()
            
            # Serialize document
            document_data = SVGXSerializer.to_json(svgx_document, pretty=False)
            
            # Save to database
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO svgx_documents 
                (document_id, document_data, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (
                document_id,
                document_data,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            self.connection.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to save SVGX document: {e}")
            raise DatabaseError(f"Failed to save document: {e}")
    
    def load_svgx_document(self, document_id: str) -> SVGXDocument:
        """Load SVGX document from SQLite."""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT document_data FROM svgx_documents 
                WHERE document_id = ?
            """, (document_id,))
            
            row = cursor.fetchone()
            if not row:
                raise DatabaseError(f"Document not found: {document_id}")
            
            # Deserialize document
            document_data = json.loads(row[0])
            return SVGXDocument(**document_data)
            
        except Exception as e:
            self.logger.error(f"Failed to load SVGX document: {e}")
            raise DatabaseError(f"Failed to load document: {e}")
    
    def list_documents(self) -> List[str]:
        """List all document IDs."""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            cursor.execute("SELECT document_id FROM svgx_documents")
            
            return [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"Failed to list documents: {e}")
            raise DatabaseError(f"Failed to list documents: {e}")
    
    def delete_document(self, document_id: str) -> None:
        """Delete document from SQLite."""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM svgx_documents WHERE document_id = ?", (document_id,))
            self.connection.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to delete SVGX document: {e}")
            raise DatabaseError(f"Failed to delete document: {e}")
    
    def _create_tables(self) -> None:
        """Create database tables."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS svgx_documents (
                    document_id TEXT PRIMARY KEY,
                    document_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            self.connection.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")
            raise DatabaseError(f"Failed to create tables: {e}")


class SVGXPersistenceExportService:
    """
    SVGX Engine Persistence Export Service.
    
    Provides persistent export capabilities for SVGX Engine including
    robust serialization, multi-format export, database integration,
    and job management with monitoring.
    """
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the Persistence Export Service.
        
        Args:
            options: Configuration options
        """
        self.options = {
            'enable_persistence': True,
            'enable_job_monitoring': True,
            'enable_svgx_optimization': True,
            'max_job_timeout': 300,  # 5 minutes
            'max_concurrent_jobs': 5,
            'job_queue_size': 100,
            'database_type': DatabaseType.SQLITE,
            'database_connection': ':memory:'
        }
        if options:
            self.options.update(options)
        
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize components
        self.exporter = SVGXExporter()
        self.job_queue = {}
        self.job_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=self.options['max_concurrent_jobs'])
        
        # Initialize database interface
        db_config = DatabaseConfig(
            db_type=self.options['database_type'],
            connection_string=self.options['database_connection']
        )
        self.database = SQLiteInterface(db_config)
        
        self.logger.info("Persistence Export Service initialized")
    
    def export_svgx_document(self, svgx_document: SVGXDocument, 
                            file_path: str, options: ExportOptions) -> None:
        """
        Export SVGX document to file.
        
        Args:
            svgx_document: SVGX document to export
            file_path: Output file path
            options: Export options
        """
        try:
            self.logger.info(f"Starting export to {file_path}")
            
            # Export document
            export_data = self.exporter.export_svgx_document(svgx_document, options)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                if isinstance(export_data, bytes):
                    f.write(export_data.decode('utf-8'))
                else:
                    f.write(export_data)
            
            self.logger.info(f"Export completed successfully: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            raise PersistenceExportError(f"Export failed: {e}")
    
    def save_svgx_document_to_database(self, svgx_document: SVGXDocument, 
                                      document_id: str, db_config: DatabaseConfig) -> None:
        """
        Save SVGX document to database.
        
        Args:
            svgx_document: SVGX document to save
            document_id: Document ID
            db_config: Database configuration
        """
        try:
            self.logger.info(f"Saving document {document_id} to database")
            
            # Create database interface
            if db_config.db_type == DatabaseType.SQLITE:
                db_interface = SQLiteInterface(db_config)
            else:
                raise DatabaseError(f"Unsupported database type: {db_config.db_type}")
            
            # Save document
            db_interface.connect()
            db_interface.save_svgx_document(svgx_document, document_id)
            db_interface.disconnect()
            
            self.logger.info(f"Document {document_id} saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save document: {e}")
            raise PersistenceExportError(f"Failed to save document: {e}")
    
    def load_svgx_document_from_database(self, document_id: str, 
                                        db_config: DatabaseConfig) -> SVGXDocument:
        """
        Load SVGX document from database.
        
        Args:
            document_id: Document ID
            db_config: Database configuration
            
        Returns:
            SVGXDocument loaded from database
        """
        try:
            self.logger.info(f"Loading document {document_id} from database")
            
            # Create database interface
            if db_config.db_type == DatabaseType.SQLITE:
                db_interface = SQLiteInterface(db_config)
            else:
                raise DatabaseError(f"Unsupported database type: {db_config.db_type}")
            
            # Load document
            db_interface.connect()
            document = db_interface.load_svgx_document(document_id)
            db_interface.disconnect()
            
            self.logger.info(f"Document {document_id} loaded successfully")
            return document
            
        except Exception as e:
            self.logger.error(f"Failed to load document: {e}")
            raise PersistenceExportError(f"Failed to load document: {e}")
    
    def create_export_job(self, svgx_document: SVGXDocument, 
                         file_path: str, options: ExportOptions) -> str:
        """
        Create an export job.
        
        Args:
            svgx_document: SVGX document to export
            file_path: Output file path
            options: Export options
            
        Returns:
            Job ID
        """
        try:
            job_id = str(uuid.uuid4())
            
            job = ExportJob(
                job_id=job_id,
                status=JobStatus.PENDING,
                created_at=datetime.now(),
                total_items=len(svgx_document.elements),
                metadata={
                    'file_path': file_path,
                    'format': options.format.value,
                    'document_id': svgx_document.id
                }
            )
            
            # Add to job queue
            with self.job_lock:
                self.job_queue[job_id] = job
            
            # Submit job for processing
            self.executor.submit(self._process_export_job, job_id, svgx_document, file_path, options)
            
            self.logger.info(f"Created export job {job_id}")
            return job_id
            
        except Exception as e:
            self.logger.error(f"Failed to create export job: {e}")
            raise JobError(f"Failed to create export job: {e}")
    
    def _process_export_job(self, job_id: str, svgx_document: SVGXDocument, 
                           file_path: str, options: ExportOptions):
        """Process export job."""
        try:
            # Update job status
            with self.job_lock:
                if job_id in self.job_queue:
                    job = self.job_queue[job_id]
                    job.status = JobStatus.IN_PROGRESS
                    job.started_at = datetime.now()
            
            # Process export
            self.export_svgx_document(svgx_document, file_path, options)
            
            # Update job status
            with self.job_lock:
                if job_id in self.job_queue:
                    job = self.job_queue[job_id]
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now()
                    job.progress = 100.0
                    job.processed_items = job.total_items
                    job.result_path = file_path
            
            self.logger.info(f"Export job {job_id} completed successfully")
            
        except Exception as e:
            # Update job status
            with self.job_lock:
                if job_id in self.job_queue:
                    job = self.job_queue[job_id]
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now()
                    job.error_message = str(e)
            
            self.logger.error(f"Export job {job_id} failed: {e}")
    
    def get_job_status(self, job_id: str) -> Optional[ExportJob]:
        """
        Get job status.
        
        Args:
            job_id: Job ID
            
        Returns:
            ExportJob or None if not found
        """
        with self.job_lock:
            return self.job_queue.get(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel export job.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if cancelled successfully
        """
        try:
            with self.job_lock:
                if job_id in self.job_queue:
                    job = self.job_queue[job_id]
                    if job.status in [JobStatus.PENDING, JobStatus.IN_PROGRESS]:
                        job.status = JobStatus.CANCELLED
                        job.completed_at = datetime.now()
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    def list_database_documents(self, db_config: DatabaseConfig) -> List[str]:
        """
        List all documents in database.
        
        Args:
            db_config: Database configuration
            
        Returns:
            List of document IDs
        """
        try:
            # Create database interface
            if db_config.db_type == DatabaseType.SQLITE:
                db_interface = SQLiteInterface(db_config)
            else:
                raise DatabaseError(f"Unsupported database type: {db_config.db_type}")
            
            # List documents
            db_interface.connect()
            documents = db_interface.list_documents()
            db_interface.disconnect()
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Failed to list documents: {e}")
            raise PersistenceExportError(f"Failed to list documents: {e}")
    
    def delete_database_document(self, document_id: str, db_config: DatabaseConfig) -> None:
        """
        Delete document from database.
        
        Args:
            document_id: Document ID
            db_config: Database configuration
        """
        try:
            # Create database interface
            if db_config.db_type == DatabaseType.SQLITE:
                db_interface = SQLiteInterface(db_config)
            else:
                raise DatabaseError(f"Unsupported database type: {db_config.db_type}")
            
            # Delete document
            db_interface.connect()
            db_interface.delete_document(document_id)
            db_interface.disconnect()
            
            self.logger.info(f"Document {document_id} deleted successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to delete document: {e}")
            raise PersistenceExportError(f"Failed to delete document: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        with self.job_lock:
            job_stats = {
                'total_jobs': len(self.job_queue),
                'pending_jobs': len([j for j in self.job_queue.values() if j.status == JobStatus.PENDING]),
                'in_progress_jobs': len([j for j in self.job_queue.values() if j.status == JobStatus.IN_PROGRESS]),
                'completed_jobs': len([j for j in self.job_queue.values() if j.status == JobStatus.COMPLETED]),
                'failed_jobs': len([j for j in self.job_queue.values() if j.status == JobStatus.FAILED]),
                'cancelled_jobs': len([j for j in self.job_queue.values() if j.status == JobStatus.CANCELLED])
            }
        
        return {
            **job_stats,
            'performance_metrics': self.performance_monitor.get_metrics()
        }
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            # Clear job queue
            with self.job_lock:
                self.job_queue.clear()
            
            self.logger.info("Persistence Export Service cleaned up")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup: {e}")
            raise PersistenceExportError(f"Cleanup failed: {e}")


SVGXPersistenceExportService = SVGXPersistenceExportService
PersistenceExportService = SVGXPersistenceExportService

def create_persistence_export_service(options: Optional[Dict[str, Any]] = None) -> SVGXPersistenceExportService:
    """
    Create a Persistence Export Service instance.
    
    Args:
        options: Configuration options
        
    Returns:
        SVGXPersistenceExportService instance
    """
    return SVGXPersistenceExportService(options) 