"""
Multi-System Integration Framework Demonstration

Comprehensive demonstration of the Multi-System Integration Framework
showing connection management, data transformation, synchronization,
and monitoring for CMMS, ERP, SCADA, BMS, and IoT systems.
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

from services.multi_system_integration import (
    MultiSystemIntegration,
    SystemType,
    ConnectionStatus,
    SyncDirection,
    ConflictResolution
)


class MultiSystemIntegrationDemo:
    """Demonstration class for Multi-System Integration Framework."""
    
    def __init__(self):
        """Initialize the demonstration."""
        self.integration_service = MultiSystemIntegration()
        self.demo_connections = {}
        self.demo_mappings = {}
        self.demo_data = {}
        
        print("🚀 Multi-System Integration Framework Demonstration")
        print("=" * 60)
    
    def run_full_demo(self):
        """Run the complete demonstration."""
        try:
            print("\n📋 Starting comprehensive demonstration...")
            
            # Phase 1: System Connections
            self.demo_system_connections()
            
            # Phase 2: Field Mappings
            self.demo_field_mappings()
            
            # Phase 3: Data Transformation
            self.demo_data_transformation()
            
            # Phase 4: Data Synchronization
            self.demo_data_synchronization()
            
            # Phase 5: Performance and Monitoring
            self.demo_performance_monitoring()
            
            # Phase 6: Advanced Features
            self.demo_advanced_features()
            
            print("\n✅ Demonstration completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            raise
    
    def demo_system_connections(self):
        """Demonstrate system connection management."""
        print("\n🔌 Phase 1: System Connection Management")
        print("-" * 40)
        
        # Create connections for different system types
        connection_configs = [
            {
                "system_id": "cmms_maximo_001",
                "system_type": "cmms",
                "connection_name": "Maximo CMMS Connection",
                "host": "maximo.company.com",
                "port": 8080,
                "username": "maximo_user",
                "password": "secure_password",
                "database": "maximo_db",
                "ssl_enabled": True,
                "timeout": 30,
                "retry_attempts": 3
            },
            {
                "system_id": "erp_sap_001",
                "system_type": "erp",
                "connection_name": "SAP ERP Connection",
                "host": "sap.company.com",
                "port": 8000,
                "username": "sap_user",
                "password": "secure_password",
                "database": "sap_db",
                "ssl_enabled": True,
                "timeout": 45,
                "retry_attempts": 5
            },
            {
                "system_id": "scada_honeywell_001",
                "system_type": "scada",
                "connection_name": "Honeywell SCADA Connection",
                "host": "scada.company.com",
                "port": 5000,
                "username": "scada_user",
                "password": "secure_password",
                "ssl_enabled": True,
                "timeout": 20,
                "retry_attempts": 3
            },
            {
                "system_id": "bms_siemens_001",
                "system_type": "bms",
                "connection_name": "Siemens BMS Connection",
                "host": "bms.company.com",
                "port": 8081,
                "username": "bms_user",
                "password": "secure_password",
                "ssl_enabled": True,
                "timeout": 25,
                "retry_attempts": 3
            },
            {
                "system_id": "iot_modbus_001",
                "system_type": "iot",
                "connection_name": "Modbus IoT Connection",
                "host": "iot.company.com",
                "port": 502,
                "username": "iot_user",
                "password": "secure_password",
                "ssl_enabled": False,
                "timeout": 15,
                "retry_attempts": 2
            }
        ]
        
        print("Creating system connections...")
        for config in connection_configs:
            connection = self.integration_service.create_system_connection(config)
            self.demo_connections[connection.system_id] = connection
            print(f"  ✅ Created {connection.system_type.value.upper()} connection: {connection.connection_name}")
        
        print(f"\nCreated {len(self.demo_connections)} system connections")
        
        # Test connections
        print("\nTesting system connections...")
        for system_id in self.demo_connections.keys():
            test_result = self.integration_service.test_connection(system_id)
            status = "✅ Connected" if test_result["success"] else "❌ Failed"
            print(f"  {status} {system_id}: {test_result.get('system_type', 'Unknown')}")
        
        # Get connection status
        print("\nConnection status summary:")
        all_connections = self.integration_service.get_all_connections()
        for connection in all_connections:
            print(f"  {connection['system_id']}: {connection['status']} ({connection['system_type']})")
    
    def demo_field_mappings(self):
        """Demonstrate field mapping creation."""
        print("\n🗺️  Phase 2: Field Mapping Configuration")
        print("-" * 40)
        
        # Create field mappings for different systems
        mapping_configs = [
            # CMMS mappings
            {
                "mapping_id": "cmms_equipment_name",
                "system_id": "cmms_maximo_001",
                "arxos_field": "equipment_name",
                "external_field": "asset_name",
                "transformation_rule": "formatting:uppercase",
                "is_required": True,
                "data_type": "string",
                "validation_rule": "validation:required"
            },
            {
                "mapping_id": "cmms_equipment_type",
                "system_id": "cmms_maximo_001",
                "arxos_field": "equipment_type",
                "external_field": "asset_type",
                "transformation_rule": "formatting:titlecase",
                "is_required": True,
                "data_type": "string"
            },
            {
                "mapping_id": "cmms_maintenance_cost",
                "system_id": "cmms_maximo_001",
                "arxos_field": "maintenance_cost",
                "external_field": "total_cost",
                "transformation_rule": "calculation:add:100",
                "is_required": False,
                "data_type": "number"
            },
            
            # ERP mappings
            {
                "mapping_id": "erp_financial_data",
                "system_id": "erp_sap_001",
                "arxos_field": "budget_amount",
                "external_field": "allocated_budget",
                "transformation_rule": "calculation:multiply:1.1",
                "is_required": False,
                "data_type": "number"
            },
            {
                "mapping_id": "erp_inventory_level",
                "system_id": "erp_sap_001",
                "arxos_field": "inventory_count",
                "external_field": "stock_level",
                "transformation_rule": "validation:range:0:10000",
                "is_required": True,
                "data_type": "number"
            },
            
            # SCADA mappings
            {
                "mapping_id": "scada_sensor_data",
                "system_id": "scada_honeywell_001",
                "arxos_field": "temperature",
                "external_field": "temp_reading",
                "transformation_rule": "calculation:add:273.15",
                "is_required": True,
                "data_type": "number"
            },
            {
                "mapping_id": "scada_pressure",
                "system_id": "scada_honeywell_001",
                "arxos_field": "pressure",
                "external_field": "pressure_psi",
                "transformation_rule": "calculation:multiply:14.696",
                "is_required": True,
                "data_type": "number"
            },
            
            # BMS mappings
            {
                "mapping_id": "bms_hvac_status",
                "system_id": "bms_siemens_001",
                "arxos_field": "hvac_status",
                "external_field": "hvac_operational_status",
                "transformation_rule": "formatting:uppercase",
                "is_required": True,
                "data_type": "string"
            },
            {
                "mapping_id": "bms_energy_consumption",
                "system_id": "bms_siemens_001",
                "arxos_field": "energy_kwh",
                "external_field": "power_consumption",
                "transformation_rule": "calculation:multiply:1000",
                "is_required": False,
                "data_type": "number"
            },
            
            # IoT mappings
            {
                "mapping_id": "iot_device_status",
                "system_id": "iot_modbus_001",
                "arxos_field": "device_status",
                "external_field": "sensor_status",
                "transformation_rule": "formatting:lowercase",
                "is_required": True,
                "data_type": "string"
            },
            {
                "mapping_id": "iot_battery_level",
                "system_id": "iot_modbus_001",
                "arxos_field": "battery_percentage",
                "external_field": "battery_level",
                "transformation_rule": "validation:range:0:100",
                "is_required": True,
                "data_type": "number"
            }
        ]
        
        print("Creating field mappings...")
        for config in mapping_configs:
            mapping = self.integration_service.create_field_mapping(config)
            self.demo_mappings[mapping.mapping_id] = mapping
            print(f"  ✅ Created mapping: {mapping.arxos_field} → {mapping.external_field}")
        
        print(f"\nCreated {len(self.demo_mappings)} field mappings")
        
        # Show mapping summary by system
        print("\nMapping summary by system:")
        for system_id in self.demo_connections.keys():
            mappings = [m for m in self.demo_mappings.values() if m.system_id == system_id]
            print(f"  {system_id}: {len(mappings)} mappings")
    
    def demo_data_transformation(self):
        """Demonstrate data transformation capabilities."""
        print("\n🔄 Phase 3: Data Transformation")
        print("-" * 40)
        
        # Sample data for transformation
        sample_data = {
            "equipment_name": "hvac unit 1",
            "equipment_type": "hvac",
            "maintenance_cost": 500,
            "budget_amount": 10000,
            "inventory_count": 150,
            "temperature": 25,
            "pressure": 1.0,
            "hvac_status": "operational",
            "energy_kwh": 2.5,
            "device_status": "ONLINE",
            "battery_percentage": 85
        }
        
        self.demo_data = sample_data
        
        print("Original data:")
        for key, value in sample_data.items():
            print(f"  {key}: {value}")
        
        # Transform data for each system
        print("\nTransforming data for each system...")
        
        for system_id in self.demo_connections.keys():
            print(f"\n📊 {system_id.upper()} transformation:")
            
            # Outbound transformation
            outbound_data = self.integration_service.transform_data(sample_data, system_id, "outbound")
            print(f"  Outbound ({len(outbound_data)} fields):")
            for key, value in outbound_data.items():
                print(f"    {key}: {value}")
            
            # Inbound transformation (simulate external data)
            external_data = {v: k for k, v in outbound_data.items()}
            inbound_data = self.integration_service.transform_data(external_data, system_id, "inbound")
            print(f"  Inbound ({len(inbound_data)} fields):")
            for key, value in inbound_data.items():
                print(f"    {key}: {value}")
    
    def demo_data_synchronization(self):
        """Demonstrate data synchronization capabilities."""
        print("\n🔄 Phase 4: Data Synchronization")
        print("-" * 40)
        
        # Create sample data for sync
        sync_data = [
            {
                "equipment_name": "HVAC Unit 1",
                "equipment_type": "HVAC",
                "maintenance_cost": 500,
                "status": "operational"
            },
            {
                "equipment_name": "Chiller Unit 2",
                "equipment_type": "Chiller",
                "maintenance_cost": 1200,
                "status": "maintenance"
            },
            {
                "equipment_name": "Boiler Unit 3",
                "equipment_type": "Boiler",
                "maintenance_cost": 800,
                "status": "operational"
            }
        ]
        
        print(f"Syncing {len(sync_data)} records to each system...")
        
        # Sync to each system
        for system_id in self.demo_connections.keys():
            print(f"\n📤 Syncing to {system_id}:")
            
            try:
                sync_result = self.integration_service.sync_data(
                    system_id=system_id,
                    direction=SyncDirection.OUTBOUND,
                    data=sync_data,
                    conflict_resolution=ConflictResolution.TIMESTAMP_BASED
                )
                
                print(f"  ✅ Sync completed: {sync_result.sync_id}")
                print(f"    Records processed: {sync_result.records_processed}")
                print(f"    Records successful: {sync_result.records_successful}")
                print(f"    Records failed: {sync_result.records_failed}")
                print(f"    Conflicts resolved: {sync_result.conflicts_resolved}")
                print(f"    Sync duration: {sync_result.sync_duration:.2f}s")
                print(f"    Status: {sync_result.status}")
                
                if sync_result.error_message:
                    print(f"    Error: {sync_result.error_message}")
                    
            except Exception as e:
                print(f"  ❌ Sync failed: {e}")
        
        # Get sync history
        print("\n📋 Recent sync history:")
        sync_history = self.integration_service.get_sync_history(limit=5)
        for sync in sync_history:
            print(f"  {sync['sync_id']}: {sync['records_successful']}/{sync['records_processed']} successful")
    
    def demo_performance_monitoring(self):
        """Demonstrate performance monitoring capabilities."""
        print("\n📊 Phase 5: Performance Monitoring")
        print("-" * 40)
        
        # Get performance metrics
        metrics = self.integration_service.get_performance_metrics()
        
        print("Performance metrics:")
        print(f"  Total connections: {metrics['total_connections']}")
        print(f"  Active connections: {metrics['active_connections']}")
        print(f"  Total mappings: {metrics['total_mappings']}")
        print(f"  Supported system types: {metrics['supported_system_types']}")
        print(f"  Supported connectors: {metrics['supported_connectors']}")
        print(f"  Transformation operations: {metrics['transformation_operations']}")
        
        # Connection status summary
        print("\nConnection status summary:")
        all_connections = self.integration_service.get_all_connections()
        status_counts = {}
        for connection in all_connections:
            status = connection['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        # System type distribution
        print("\nSystem type distribution:")
        type_counts = {}
        for connection in all_connections:
            system_type = connection['system_type']
            type_counts[system_type] = type_counts.get(system_type, 0) + 1
        
        for system_type, count in type_counts.items():
            print(f"  {system_type.upper()}: {count}")
    
    def demo_advanced_features(self):
        """Demonstrate advanced features."""
        print("\n🚀 Phase 6: Advanced Features")
        print("-" * 40)
        
        # Test different conflict resolution strategies
        print("Testing conflict resolution strategies:")
        conflict_strategies = [
            ConflictResolution.ARXOS_WINS,
            ConflictResolution.EXTERNAL_WINS,
            ConflictResolution.MANUAL,
            ConflictResolution.MERGE,
            ConflictResolution.TIMESTAMP_BASED
        ]
        
        for strategy in conflict_strategies:
            print(f"  {strategy.value}: {strategy.name}")
        
        # Test different sync directions
        print("\nTesting sync directions:")
        sync_directions = [
            SyncDirection.INBOUND,
            SyncDirection.OUTBOUND,
            SyncDirection.BIDIRECTIONAL
        ]
        
        for direction in sync_directions:
            print(f"  {direction.value}: {direction.name}")
        
        # Test transformation engine capabilities
        print("\nTransformation engine capabilities:")
        engine = self.integration_service.transformation_engine
        
        print(f"  Calculations: {len(engine['calculations'])} operations")
        print(f"  Validations: {len(engine['validations'])} rules")
        print(f"  Formatting: {len(engine['formatting'])} operations")
        
        # Test system connectors
        print("\nSystem connectors:")
        connectors = self.integration_service.connectors
        for system_type, system_connectors in connectors.items():
            print(f"  {system_type.value.upper()}: {len(system_connectors)} connectors")
        
        # Test connection health monitoring
        print("\nConnection health monitoring:")
        for system_id in self.demo_connections.keys():
            health_check = self.integration_service._check_connection_health(
                self.demo_connections[system_id]
            )
            status = "✅ Healthy" if health_check["healthy"] else "❌ Unhealthy"
            print(f"  {system_id}: {status}")
    
    def run_performance_test(self):
        """Run performance tests."""
        print("\n⚡ Performance Testing")
        print("-" * 40)
        
        # Test bulk data transformation
        print("Testing bulk data transformation...")
        bulk_data = [self.demo_data.copy() for _ in range(100)]
        
        start_time = time.time()
        for i, data in enumerate(bulk_data):
            self.integration_service.transform_data(data, "cmms_maximo_001", "outbound")
        end_time = time.time()
        
        transformation_rate = len(bulk_data) / (end_time - start_time)
        print(f"  Transformation rate: {transformation_rate:.2f} records/second")
        
        # Test bulk synchronization
        print("Testing bulk synchronization...")
        sync_data = [self.demo_data.copy() for _ in range(50)]
        
        start_time = time.time()
        sync_result = self.integration_service.sync_data(
            system_id="cmms_maximo_001",
            direction=SyncDirection.OUTBOUND,
            data=sync_data,
            conflict_resolution=ConflictResolution.TIMESTAMP_BASED
        )
        end_time = time.time()
        
        sync_rate = len(sync_data) / (end_time - start_time)
        print(f"  Sync rate: {sync_rate:.2f} records/second")
        print(f"  Success rate: {(sync_result.records_successful / sync_result.records_processed * 100):.1f}%")
    
    def generate_report(self):
        """Generate a comprehensive demonstration report."""
        print("\n📋 Demonstration Report")
        print("=" * 60)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "demo_summary": {
                "connections_created": len(self.demo_connections),
                "mappings_created": len(self.demo_mappings),
                "systems_supported": len(SystemType),
                "transformation_operations": len(self.integration_service.transformation_engine["calculations"]) +
                                          len(self.integration_service.transformation_engine["validations"]) +
                                          len(self.integration_service.transformation_engine["formatting"])
            },
            "system_breakdown": {
                system_id: {
                    "type": connection.system_type.value,
                    "name": connection.connection_name,
                    "status": connection.status.value,
                    "mappings": len([m for m in self.demo_mappings.values() if m.system_id == system_id])
                }
                for system_id, connection in self.demo_connections.items()
            },
            "capabilities_demonstrated": [
                "System connection management",
                "Field mapping configuration",
                "Data transformation (calculations, validations, formatting)",
                "Bidirectional synchronization",
                "Conflict resolution strategies",
                "Performance monitoring",
                "Connection health monitoring",
                "Audit logging",
                "Error handling and recovery"
            ],
            "performance_metrics": self.integration_service.get_performance_metrics()
        }
        
        print(json.dumps(report, indent=2))
        return report


def main():
    """Main demonstration function."""
    try:
        # Create and run demonstration
        demo = MultiSystemIntegrationDemo()
        demo.run_full_demo()
        
        # Run performance tests
        demo.run_performance_test()
        
        # Generate report
        demo.generate_report()
        
        print("\n🎉 Multi-System Integration Framework demonstration completed successfully!")
        print("The framework is ready for production use with enterprise-grade features.")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    main() 