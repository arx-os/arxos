"""
Persistence, Export, and Interoperability System for SVG-BIM

This module provides comprehensive persistence, export, and interoperability features:
- Robust serialization for all BIM types (to_dict, from_dict, to_json, from_json)
- Exporters for IFC, gbXML, and other BIM formats (JSON/CSV for MVP)
- Database integration hooks for SQL, NoSQL, and graph databases
- Interoperability with external BIM systems
"""

import json
import csv
import xml.etree.ElementTree as ET
import sqlite3
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import uuid
import pickle
from abc import ABC, abstractmethod

from models.bim import (
    BIMModel, Room, Wall, Door, Window, Device, HVACZone, AirHandler, VAVBox,
    ElectricalCircuit, ElectricalPanel, ElectricalOutlet, PlumbingSystem,
    PlumbingFixture, Valve, FireAlarmSystem, SmokeDetector, SecuritySystem,
    Camera, Label, Geometry, GeometryType
)
from utils.errors import ExportError, ValidationError, PersistenceError

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    IFC = "ifc"
    GBXML = "gbxml"
    PICKLE = "pickle"
    SQLITE = "sqlite"


class DatabaseType(Enum):
    """Supported database types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    NEO4J = "neo4j"


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


@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_type: DatabaseType
    connection_string: str
    table_name: str = "bim_models"
    create_tables: bool = True
    batch_size: int = 1000


class BIMSerializer:
    """Robust serialization for all BIM types."""
    
    @staticmethod
    def to_dict(obj: Any) -> Dict[str, Any]:
        """Convert any BIM object to dictionary."""
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        elif isinstance(obj, (list, tuple)):
            return [BIMSerializer.to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: BIMSerializer.to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return {k: BIMSerializer.to_dict(v) for k, v in obj.__dict__.items()}
        else:
            return obj
    
    @staticmethod
    def from_dict(data: Dict[str, Any], target_class: type) -> Any:
        """Create BIM object from dictionary."""
        if hasattr(target_class, 'from_dict'):
            return target_class.from_dict(data)
        elif hasattr(target_class, 'parse_obj'):
            return target_class.parse_obj(data)
        else:
            return target_class(**data)
    
    @staticmethod
    def to_json(obj: Any, pretty: bool = True) -> str:
        """Convert BIM object to JSON string."""
        data = BIMSerializer.to_dict(obj)
        if pretty:
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)
    
    @staticmethod
    def from_json(json_str: str, target_class: type) -> Any:
        """Create BIM object from JSON string."""
        data = json.loads(json_str)
        return BIMSerializer.from_dict(data, target_class)
    
    @staticmethod
    def to_pickle(obj: Any) -> bytes:
        """Convert BIM object to pickle bytes."""
        return pickle.dumps(obj)
    
    @staticmethod
    def from_pickle(pickle_bytes: bytes) -> Any:
        """Create BIM object from pickle bytes."""
        return pickle.loads(pickle_bytes)


class BIMExporter:
    """Export BIM models to various formats."""
    
    def __init__(self):
        self.serializer = BIMSerializer()
    
    def export_bim_model(self, bim_model: BIMModel, options: ExportOptions) -> Union[str, bytes]:
        """Export BIM model to specified format."""
        try:
            if options.format == ExportFormat.JSON:
                return self._export_to_json(bim_model, options)
            elif options.format == ExportFormat.XML:
                return self._export_to_xml(bim_model, options)
            elif options.format == ExportFormat.CSV:
                return self._export_to_csv(bim_model, options)
            elif options.format == ExportFormat.IFC:
                return self._export_to_ifc(bim_model, options)
            elif options.format == ExportFormat.GBXML:
                return self._export_to_gbxml(bim_model, options)
            elif options.format == ExportFormat.PICKLE:
                return self._export_to_pickle(bim_model, options)
            else:
                raise ExportError(f"Unsupported export format: {options.format}")
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise ExportError(f"Export failed: {e}") from e
    
    def _export_to_json(self, bim_model: BIMModel, options: ExportOptions) -> str:
        """Export to JSON format."""
        data = self.serializer.to_dict(bim_model)
        
        # Filter data based on options
        if not options.include_metadata:
            data.pop('metadata', None)
        if not options.include_geometry:
            self._remove_geometry_from_dict(data)
        if not options.include_properties:
            self._remove_properties_from_dict(data)
        if not options.include_relationships:
            self._remove_relationships_from_dict(data)
        
        if options.pretty_print:
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)
    
    def _export_to_xml(self, bim_model: BIMModel, options: ExportOptions) -> str:
        """Export to XML format."""
        data = self.serializer.to_dict(bim_model)
        
        # Filter data based on options
        if not options.include_metadata:
            data.pop('metadata', None)
        if not options.include_geometry:
            self._remove_geometry_from_dict(data)
        if not options.include_properties:
            self._remove_properties_from_dict(data)
        if not options.include_relationships:
            self._remove_relationships_from_dict(data)
        
        root = self._dict_to_xml('BIMModel', data)
        return ET.tostring(root, encoding='unicode', method='xml')
    
    def _export_to_csv(self, bim_model: BIMModel, options: ExportOptions) -> str:
        """Export to CSV format."""
        # Flatten BIM model to CSV format
        csv_data = []
        
        # Add rooms
        for room in bim_model.rooms:
            csv_data.append({
                'type': 'room',
                'id': room.id,
                'name': room.name,
                'room_type': room.room_type.value if room.room_type else '',
                'room_number': room.room_number or '',
                'area': room.area or '',
                'floor_level': room.floor_level or '',
                'ceiling_height': room.ceiling_height or '',
                'occupants': room.occupants or ''
            })
        
        # Add walls
        for wall in bim_model.walls:
            csv_data.append({
                'type': 'wall',
                'id': wall.id,
                'name': wall.name,
                'wall_type': wall.wall_type or '',
                'thickness': wall.thickness or '',
                'height': wall.height or ''
            })
        
        # Add devices
        for device in bim_model.devices:
            csv_data.append({
                'type': 'device',
                'id': device.id,
                'name': device.name,
                'system_type': device.system_type.value if device.system_type else '',
                'category': device.category.value if device.category else '',
                'manufacturer': device.manufacturer or '',
                'model': device.model or ''
            })
        
        # Convert to CSV string
        if not csv_data:
            return ""
        
        output = []
        fieldnames = csv_data[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
        
        return ''.join(output)
    
    def _export_to_ifc(self, bim_model: BIMModel, options: ExportOptions) -> str:
        """Export to IFC format (simplified)."""
        # Generate simplified IFC content
        ifc_content = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('BIM Model Export'),'2;1');
FILE_NAME('{bim_model.name or "bim_model"}.ifc','{datetime.now().isoformat()}',('User'),('Organization'),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('{bim_model.id}',$,{bim_model.name or "BIM Model"},{bim_model.description or ""},$,$,$,$,(#2),#3);
#2=IFCOWNERHISTORY(#4,$,.ADDED.,$,$,$,.NOCHANGE.,{datetime.now().isoformat()});
#3=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#5,$);
#4=IFCPERSONANDORGANIZATION(#6,#7,$);
#5=IFCDIRECTION((0.,0.,1.));
#6=IFCPERSON('','','',$,$,$);
#7=IFCORGANIZATION('','',$,$,$);
"""
        
        # Add rooms
        for i, room in enumerate(bim_model.rooms, 10):
            ifc_content += f"#{i}=IFCBUILDINGSTOREY('{room.id}',$,{room.name or 'Room'},$,$,#1,$,$,.ELEMENT.,$);\n"
        
        # Add walls
        for i, wall in enumerate(bim_model.walls, 100):
            ifc_content += f"#{i}=IFCWALL('{wall.id}',$,{wall.name or 'Wall'},$,$,#1,$,$,.ELEMENT.,$);\n"
        
        ifc_content += "ENDSEC;\nEND-ISO-10303-21;"
        return ifc_content
    
    def _export_to_gbxml(self, bim_model: BIMModel, options: ExportOptions) -> str:
        """Export to gbXML format (simplified)."""
        gbxml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<gbXML version="0.37" temperatureUnit="C" lengthUnit="Meters" areaUnit="SquareMeters" volumeUnit="CubicMeters" useSIUnitsForResults="true" xmlns="http://www.gbxml.org/schema">
  <Campus id="Campus_1">
    <Location>
      <Latitude>0</Latitude>
      <Longitude>0</Longitude>
      <Elevation>0</Elevation>
    </Location>
    <Building id="Building_1" buildingType="Office">
      <Area>1000</Area>
      <Storey id="Storey_1">
"""
        
        # Add rooms
        for room in bim_model.rooms:
            gbxml_content += f"""        <Space id="{room.id}" conditionType="HeatedAndCooled">
          <Name>{room.name or 'Room'}</Name>
          <Area>{room.area or 100}</Area>
          <Volume>{room.area * (room.ceiling_height or 3) if room.area and room.ceiling_height else 300}</Volume>
        </Space>
"""
        
        gbxml_content += """      </Storey>
    </Building>
  </Campus>
</gbXML>"""
        return gbxml_content
    
    def _export_to_pickle(self, bim_model: BIMModel, options: ExportOptions) -> bytes:
        """Export to pickle format."""
        return self.serializer.to_pickle(bim_model)
    
    def _dict_to_xml(self, tag: str, data: Any) -> ET.Element:
        """Convert dictionary to XML element."""
        elem = ET.Element(tag)
        if isinstance(data, dict):
            for k, v in data.items():
                child = self._dict_to_xml(k, v)
                elem.append(child)
        elif isinstance(data, list):
            for item in data:
                child = self._dict_to_xml('item', item)
                elem.append(child)
        else:
            elem.text = str(data)
        return elem
    
    def _remove_geometry_from_dict(self, data: Dict[str, Any]) -> None:
        """Remove geometry from dictionary recursively."""
        if isinstance(data, dict):
            data.pop('geometry', None)
            for value in data.values():
                if isinstance(value, (dict, list)):
                    self._remove_geometry_from_dict(value)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._remove_geometry_from_dict(item)
    
    def _remove_properties_from_dict(self, data: Dict[str, Any]) -> None:
        """Remove properties from dictionary recursively."""
        if isinstance(data, dict):
            data.pop('properties', None)
            for value in data.values():
                if isinstance(value, (dict, list)):
                    self._remove_properties_from_dict(value)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._remove_properties_from_dict(item)
    
    def _remove_relationships_from_dict(self, data: Dict[str, Any]) -> None:
        """Remove relationships from dictionary recursively."""
        if isinstance(data, dict):
            data.pop('relationships', None)
            data.pop('children', None)
            data.pop('parent_id', None)
            for value in data.values():
                if isinstance(value, (dict, list)):
                    self._remove_relationships_from_dict(value)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._remove_relationships_from_dict(item)


class DatabaseInterface(ABC):
    """Abstract base class for database interfaces."""
    
    @abstractmethod
    def connect(self) -> None:
        """Connect to database."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from database."""
        pass
    
    @abstractmethod
    def save_bim_model(self, bim_model: BIMModel, model_id: str) -> None:
        """Save BIM model to database."""
        pass
    
    @abstractmethod
    def load_bim_model(self, model_id: str) -> BIMModel:
        """Load BIM model from database."""
        pass
    
    @abstractmethod
    def list_models(self) -> List[str]:
        """List all model IDs in database."""
        pass
    
    @abstractmethod
    def delete_model(self, model_id: str) -> None:
        """Delete model from database."""
        pass


class SQLiteInterface(DatabaseInterface):
    """SQLite database interface."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None
    
    def connect(self) -> None:
        """Connect to SQLite database."""
        try:
            self.connection = sqlite3.connect(self.config.connection_string)
            if self.config.create_tables:
                self._create_tables()
            logger.info(f"Connected to SQLite database: {self.config.connection_string}")
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise PersistenceError(f"Failed to connect to SQLite: {e}") from e
    
    def disconnect(self) -> None:
        """Disconnect from SQLite database."""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from SQLite database")
    
    def save_bim_model(self, bim_model: BIMModel, model_id: str) -> None:
        """Save BIM model to SQLite."""
        try:
            if not self.connection:
                self.connect()
            
            # Convert BIM model to JSON
            model_data = BIMSerializer.to_json(bim_model, pretty=False)
            
            # Save to database
            cursor = self.connection.cursor()
            cursor.execute(f"""
                INSERT OR REPLACE INTO {self.config.table_name} 
                (model_id, model_data, created_at, updated_at) 
                VALUES (?, ?, ?, ?)
            """, (model_id, model_data, datetime.now(), datetime.now()))
            
            self.connection.commit()
            logger.info(f"Saved BIM model {model_id} to SQLite")
            
        except Exception as e:
            logger.error(f"Failed to save BIM model to SQLite: {e}")
            raise PersistenceError(f"Failed to save BIM model to SQLite: {e}") from e
    
    def load_bim_model(self, model_id: str) -> BIMModel:
        """Load BIM model from SQLite."""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT model_data FROM {self.config.table_name} 
                WHERE model_id = ?
            """, (model_id,))
            
            result = cursor.fetchone()
            if not result:
                raise PersistenceError(f"Model {model_id} not found in database")
            
            model_data = result[0]
            bim_model = BIMSerializer.from_json(model_data, BIMModel)
            logger.info(f"Loaded BIM model {model_id} from SQLite")
            return bim_model
            
        except Exception as e:
            logger.error(f"Failed to load BIM model from SQLite: {e}")
            raise PersistenceError(f"Failed to load BIM model from SQLite: {e}") from e
    
    def list_models(self) -> List[str]:
        """List all model IDs in SQLite."""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT model_id FROM {self.config.table_name}")
            
            results = cursor.fetchall()
            model_ids = [row[0] for row in results]
            logger.info(f"Found {len(model_ids)} models in SQLite")
            return model_ids
            
        except Exception as e:
            logger.error(f"Failed to list models from SQLite: {e}")
            raise PersistenceError(f"Failed to list models from SQLite: {e}") from e
    
    def delete_model(self, model_id: str) -> None:
        """Delete model from SQLite."""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            cursor.execute(f"DELETE FROM {self.config.table_name} WHERE model_id = ?", (model_id,))
            
            self.connection.commit()
            logger.info(f"Deleted BIM model {model_id} from SQLite")
            
        except Exception as e:
            logger.error(f"Failed to delete BIM model from SQLite: {e}")
            raise PersistenceError(f"Failed to delete BIM model from SQLite: {e}") from e
    
    def _create_tables(self) -> None:
        """Create tables in SQLite database."""
        cursor = self.connection.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.table_name} (
                model_id TEXT PRIMARY KEY,
                model_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.connection.commit()
        logger.info(f"Created table {self.config.table_name} in SQLite")


class PersistenceExportManager:
    """Main manager for persistence, export, and interoperability."""
    
    def __init__(self):
        self.exporter = BIMExporter()
        self.serializer = BIMSerializer()
        self.database_interfaces: Dict[DatabaseType, DatabaseInterface] = {}
    
    def export_bim_model(self, bim_model: BIMModel, file_path: str, 
                        options: ExportOptions) -> None:
        """Export BIM model to file."""
        try:
            # Export to specified format
            export_data = self.exporter.export_bim_model(bim_model, options)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                if isinstance(export_data, bytes):
                    with open(file_path, 'wb') as f:
                        f.write(export_data)
                else:
                    f.write(export_data)
            
            logger.info(f"Exported BIM model to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export BIM model: {e}")
            raise ExportError(f"Failed to export BIM model: {e}") from e
    
    def save_bim_model_to_database(self, bim_model: BIMModel, model_id: str,
                                  db_config: DatabaseConfig) -> None:
        """Save BIM model to database."""
        try:
            # Get or create database interface
            if db_config.db_type not in self.database_interfaces:
                if db_config.db_type == DatabaseType.SQLITE:
                    self.database_interfaces[db_config.db_type] = SQLiteInterface(db_config)
                else:
                    raise PersistenceError(f"Unsupported database type: {db_config.db_type}")
            
            db_interface = self.database_interfaces[db_config.db_type]
            db_interface.save_bim_model(bim_model, model_id)
            
        except Exception as e:
            logger.error(f"Failed to save BIM model to database: {e}")
            raise PersistenceError(f"Failed to save BIM model to database: {e}") from e
    
    def load_bim_model_from_database(self, model_id: str, 
                                   db_config: DatabaseConfig) -> BIMModel:
        """Load BIM model from database."""
        try:
            # Get or create database interface
            if db_config.db_type not in self.database_interfaces:
                if db_config.db_type == DatabaseType.SQLITE:
                    self.database_interfaces[db_config.db_type] = SQLiteInterface(db_config)
                else:
                    raise PersistenceError(f"Unsupported database type: {db_config.db_type}")
            
            db_interface = self.database_interfaces[db_config.db_type]
            return db_interface.load_bim_model(model_id)
            
        except Exception as e:
            logger.error(f"Failed to load BIM model from database: {e}")
            raise PersistenceError(f"Failed to load BIM model from database: {e}") from e
    
    def list_database_models(self, db_config: DatabaseConfig) -> List[str]:
        """List all models in database."""
        try:
            # Get or create database interface
            if db_config.db_type not in self.database_interfaces:
                if db_config.db_type == DatabaseType.SQLITE:
                    self.database_interfaces[db_config.db_type] = SQLiteInterface(db_config)
                else:
                    raise PersistenceError(f"Unsupported database type: {db_config.db_type}")
            
            db_interface = self.database_interfaces[db_config.db_type]
            return db_interface.list_models()
            
        except Exception as e:
            logger.error(f"Failed to list database models: {e}")
            raise PersistenceError(f"Failed to list database models: {e}") from e
    
    def delete_database_model(self, model_id: str, db_config: DatabaseConfig) -> None:
        """Delete model from database."""
        try:
            # Get or create database interface
            if db_config.db_type not in self.database_interfaces:
                if db_config.db_type == DatabaseType.SQLITE:
                    self.database_interfaces[db_config.db_type] = SQLiteInterface(db_config)
                else:
                    raise PersistenceError(f"Unsupported database type: {db_config.db_type}")
            
            db_interface = self.database_interfaces[db_config.db_type]
            db_interface.delete_model(model_id)
            
        except Exception as e:
            logger.error(f"Failed to delete database model: {e}")
            raise PersistenceError(f"Failed to delete database model: {e}") from e
    
    def close_database_connections(self) -> None:
        """Close all database connections."""
        for db_interface in self.database_interfaces.values():
            db_interface.disconnect()
        self.database_interfaces.clear()
        logger.info("Closed all database connections")


# Convenience functions
def create_persistence_manager() -> PersistenceExportManager:
    """Create a new persistence export manager."""
    return PersistenceExportManager()


def export_bim_model(bim_model: BIMModel, file_path: str, 
                    format_type: ExportFormat = ExportFormat.JSON,
                    **options) -> None:
    """Export BIM model to file with specified format."""
    manager = create_persistence_manager()
    export_options = ExportOptions(format=format_type, **options)
    manager.export_bim_model(bim_model, file_path, export_options)


def save_bim_model_to_database(bim_model: BIMModel, model_id: str,
                              db_type: DatabaseType = DatabaseType.SQLITE,
                              connection_string: str = ":memory:",
                              **config_options) -> None:
    """Save BIM model to database."""
    manager = create_persistence_manager()
    db_config = DatabaseConfig(
        db_type=db_type,
        connection_string=connection_string,
        **config_options
    )
    manager.save_bim_model_to_database(bim_model, model_id, db_config)


def load_bim_model_from_database(model_id: str,
                                db_type: DatabaseType = DatabaseType.SQLITE,
                                connection_string: str = ":memory:",
                                **config_options) -> BIMModel:
    """Load BIM model from database."""
    manager = create_persistence_manager()
    db_config = DatabaseConfig(
        db_type=db_type,
        connection_string=connection_string,
        **config_options
    )
    return manager.load_bim_model_from_database(model_id, db_config) 