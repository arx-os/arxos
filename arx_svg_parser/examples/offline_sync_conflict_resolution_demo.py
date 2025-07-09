"""
Offline Sync & Conflict Resolution Demo

This demonstration script showcases the comprehensive offline sync and conflict
resolution capabilities including:
- Two-way sync operations for mobile and CLI clients
- Conflict detection algorithms with intelligent resolution
- Safe merging strategies for data conflicts
- Rollback capabilities for failed syncs
- Unsynced change flagging and tracking
- Device sync logs with timestamps
- Last known remote state hash tracking
- Sync status monitoring and reporting
- Sync troubleshooting and recovery tools

Performance Targets:
- Two-way sync completes within 60 seconds
- Conflict detection identifies 95%+ of conflicts
- Safe merging resolves 90%+ of conflicts automatically
- Sync logs maintain complete history of operations
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the sync service
from services.offline_sync_conflict_resolution import (
    OfflineSyncConflictResolutionService,
    ConflictType,
    SyncStatus
)


class OfflineSyncDemo:
    """Demonstration class for offline sync and conflict resolution."""
    
    def __init__(self):
        """Initialize the demo with a sync service."""
        self.sync_service = OfflineSyncConflictResolutionService(db_path="demo_sync.db")
        self.device_ids = [
            "mobile_device_001",
            "mobile_device_002", 
            "cli_device_001",
            "cli_device_002",
            "tablet_device_001"
        ]
        
        # Sample building data
        self.sample_buildings = {
            "building_001": {
                "id": "building_001",
                "name": "Office Building A",
                "type": "commercial",
                "floors": 5,
                "systems": ["electrical", "hvac", "plumbing"],
                "last_modified": 1640995200,
                "last_sync_timestamp": 1640995200
            },
            "building_002": {
                "id": "building_002", 
                "name": "Residential Complex B",
                "type": "residential",
                "floors": 3,
                "systems": ["electrical", "hvac", "security"],
                "last_modified": 1640995300,
                "last_sync_timestamp": 1640995200
            }
        }
        
        # Sample equipment data
        self.sample_equipment = {
            "equipment_001": {
                "id": "equipment_001",
                "name": "HVAC Unit 1",
                "type": "hvac",
                "location": {"x": 100, "y": 200, "floor": 1},
                "properties": {
                    "status": "active",
                    "priority": "high",
                    "maintenance_schedule": "monthly"
                },
                "last_modified": 1640995400,
                "last_sync_timestamp": 1640995200
            },
            "equipment_002": {
                "id": "equipment_002",
                "name": "Electrical Panel A",
                "type": "electrical",
                "location": {"x": 300, "y": 400, "floor": 2},
                "properties": {
                    "status": "active",
                    "priority": "critical",
                    "voltage": "480V"
                },
                "last_modified": 1640995500,
                "last_sync_timestamp": 1640995200
            }
        }
    
    def generate_sample_changes(self, device_id: str, change_count: int = 5) -> List[Dict[str, Any]]:
        """Generate sample changes for a device."""
        changes = []
        
        for i in range(change_count):
            change_type = random.choice(["create", "update", "delete"])
            
            if change_type == "create":
                change = {
                    "id": f"new_object_{device_id}_{i}",
                    "name": f"New Object {i}",
                    "type": random.choice(["equipment", "system", "space"]),
                    "location": {
                        "x": random.randint(0, 1000),
                        "y": random.randint(0, 1000),
                        "floor": random.randint(1, 5)
                    },
                    "properties": {
                        "status": random.choice(["active", "inactive", "maintenance"]),
                        "priority": random.choice(["low", "medium", "high", "critical"])
                    },
                    "last_modified": int(time.time()) + i,
                    "last_sync_timestamp": 1640995200
                }
            elif change_type == "update":
                # Update existing equipment
                equipment_id = random.choice(list(self.sample_equipment.keys()))
                original = self.sample_equipment[equipment_id].copy()
                original["name"] = f"Updated {original['name']}"
                original["last_modified"] = int(time.time()) + i
                change = original
            else:  # delete
                equipment_id = random.choice(list(self.sample_equipment.keys()))
                change = {
                    "id": equipment_id,
                    "deleted": True,
                    "last_modified": int(time.time()) + i,
                    "last_sync_timestamp": 1640995200
                }
            
            changes.append(change)
        
        return changes
    
    def generate_remote_state(self) -> Dict[str, Any]:
        """Generate sample remote state."""
        return {
            "objects": {
                **self.sample_buildings,
                **self.sample_equipment
            },
            "last_updated": int(time.time()),
            "version": "1.0.0"
        }
    
    def demo_basic_sync_operations(self):
        """Demonstrate basic sync operations."""
        logger.info("=== Basic Sync Operations Demo ===")
        
        for device_id in self.device_ids[:3]:  # Test with first 3 devices
            logger.info(f"\n--- Testing device: {device_id} ---")
            
            # Generate local changes
            local_changes = self.generate_sample_changes(device_id, 3)
            remote_state = self.generate_remote_state()
            
            logger.info(f"Local changes: {len(local_changes)}")
            logger.info(f"Remote objects: {len(remote_state['objects'])}")
            
            # Perform sync
            start_time = time.time()
            result = self.sync_service.sync_data(
                device_id=device_id,
                local_changes=local_changes,
                remote_data=remote_state
            )
            end_time = time.time()
            
            logger.info(f"Sync completed in {end_time - start_time:.2f} seconds")
            logger.info(f"Result: {result}")
            
            # Check sync status
            status = self.sync_service.get_sync_status(device_id)
            logger.info(f"Sync status: {status}")
    
    def demo_conflict_detection_and_resolution(self):
        """Demonstrate conflict detection and resolution."""
        logger.info("\n=== Conflict Detection and Resolution Demo ===")
        
        device_id = "conflict_test_device"
        
        # Create conflicting changes
        conflicting_changes = [
            {
                "id": "equipment_001",
                "name": "HVAC Unit 1 - Local Update",
                "type": "hvac",
                "location": {"x": 150, "y": 250, "floor": 1},
                "properties": {
                    "status": "maintenance",
                    "priority": "high",
                    "maintenance_schedule": "weekly"
                },
                "last_modified": 1640995600,
                "last_sync_timestamp": 1640995200
            },
            {
                "id": "equipment_002",
                "name": "Electrical Panel A - Local Update",
                "type": "electrical",
                "location": {"x": 350, "y": 450, "floor": 2},
                "properties": {
                    "status": "active",
                    "priority": "critical",
                    "voltage": "600V"
                },
                "last_modified": 1640995700,
                "last_sync_timestamp": 1640995200
            }
        ]
        
        # Create remote state with conflicting modifications
        remote_state = {
            "objects": {
                "equipment_001": {
                    "id": "equipment_001",
                    "name": "HVAC Unit 1 - Remote Update",
                    "type": "hvac",
                    "location": {"x": 200, "y": 300, "floor": 1},
                    "properties": {
                        "status": "active",
                        "priority": "medium",
                        "maintenance_schedule": "monthly"
                    },
                    "last_modified": 1640995500,
                    "last_sync_timestamp": 1640995200
                },
                "equipment_002": {
                    "id": "equipment_002",
                    "name": "Electrical Panel A - Remote Update",
                    "type": "electrical",
                    "location": {"x": 400, "y": 500, "floor": 2},
                    "properties": {
                        "status": "inactive",
                        "priority": "critical",
                        "voltage": "480V"
                    },
                    "last_modified": 1640995400,
                    "last_sync_timestamp": 1640995200
                }
            },
            "last_updated": int(time.time())
        }
        
        logger.info(f"Testing conflict resolution for device: {device_id}")
        logger.info(f"Conflicting changes: {len(conflicting_changes)}")
        
        # Perform sync with conflicts
        result = self.sync_service.sync_data(
            device_id=device_id,
            local_changes=conflicting_changes,
            remote_data=remote_state
        )
        
        logger.info(f"Sync result: {result}")
        logger.info(f"Conflicts resolved: {result['conflicts_resolved']}")
        
        # Check sync history
        history = self.sync_service.get_sync_history(device_id, limit=10)
        logger.info(f"Sync history entries: {len(history)}")
    
    def demo_rollback_capabilities(self):
        """Demonstrate rollback capabilities."""
        logger.info("\n=== Rollback Capabilities Demo ===")
        
        device_id = "rollback_test_device"
        
        # Perform initial sync
        local_changes = self.generate_sample_changes(device_id, 2)
        remote_state = self.generate_remote_state()
        
        logger.info(f"Performing initial sync for device: {device_id}")
        result = self.sync_service.sync_data(
            device_id=device_id,
            local_changes=local_changes,
            remote_data=remote_state
        )
        
        operation_id = result["operation_id"]
        logger.info(f"Initial sync operation ID: {operation_id}")
        
        # Simulate a failed operation (in real scenario, this would be detected)
        logger.info("Simulating rollback scenario...")
        
        # Perform rollback
        rollback_result = self.sync_service.rollback_sync(device_id, operation_id)
        logger.info(f"Rollback result: {rollback_result}")
        
        # Check status after rollback
        status = self.sync_service.get_sync_status(device_id)
        logger.info(f"Status after rollback: {status}")
    
    def demo_performance_monitoring(self):
        """Demonstrate performance monitoring capabilities."""
        logger.info("\n=== Performance Monitoring Demo ===")
        
        # Perform multiple syncs to generate metrics
        for i in range(5):
            device_id = f"performance_device_{i:03d}"
            local_changes = self.generate_sample_changes(device_id, random.randint(1, 5))
            remote_state = self.generate_remote_state()
            
            self.sync_service.sync_data(
                device_id=device_id,
                local_changes=local_changes,
                remote_data=remote_state
            )
        
        # Get performance metrics
        metrics = self.sync_service.get_metrics()
        logger.info("Performance Metrics:")
        logger.info(f"  Total syncs: {metrics['metrics']['total_syncs']}")
        logger.info(f"  Successful syncs: {metrics['metrics']['successful_syncs']}")
        logger.info(f"  Conflicts resolved: {metrics['metrics']['conflicts_resolved']}")
        logger.info(f"  Rollbacks: {metrics['metrics']['rollbacks']}")
        logger.info(f"  Average sync time: {metrics['metrics']['average_sync_time']:.2f}ms")
        logger.info(f"  Total devices: {metrics['total_devices']}")
        logger.info(f"  Database size: {metrics['database_size']} bytes")
    
    def demo_concurrent_sync_operations(self):
        """Demonstrate concurrent sync operations."""
        logger.info("\n=== Concurrent Sync Operations Demo ===")
        
        import threading
        import time
        
        results = []
        errors = []
        
        def sync_worker(device_id):
            try:
                local_changes = self.generate_sample_changes(device_id, 3)
                remote_state = self.generate_remote_state()
                
                result = self.sync_service.sync_data(
                    device_id=device_id,
                    local_changes=local_changes,
                    remote_data=remote_state
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start concurrent syncs
        threads = []
        start_time = time.time()
        
        for i in range(10):
            device_id = f"concurrent_device_{i:03d}"
            thread = threading.Thread(target=sync_worker, args=(device_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        logger.info(f"Concurrent syncs completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Successful syncs: {len(results)}")
        logger.info(f"Errors: {len(errors)}")
        
        if errors:
            logger.error(f"Errors encountered: {errors}")
    
    def demo_conflict_resolution_strategies(self):
        """Demonstrate different conflict resolution strategies."""
        logger.info("\n=== Conflict Resolution Strategies Demo ===")
        
        # Create conflicting data
        local_data = {
            "id": "strategy_test_object",
            "name": "Local Version",
            "properties": {"status": "active", "priority": "high"},
            "last_modified": 1640995600
        }
        
        remote_data = {
            "id": "strategy_test_object",
            "name": "Remote Version",
            "properties": {"status": "inactive", "priority": "medium"},
            "last_modified": 1640995500
        }
        
        strategies = ["auto", "local", "remote", "manual"]
        
        for strategy in strategies:
            logger.info(f"\n--- Testing strategy: {strategy} ---")
            
            resolved_data = self.sync_service.resolve_conflict(
                conflict_type=ConflictType.MODIFICATION_CONFLICT,
                local_data=local_data,
                remote_data=remote_data,
                resolution_strategy=strategy
            )
            
            logger.info(f"Resolution strategy: {strategy}")
            logger.info(f"Resolved data name: {resolved_data.get('name', 'N/A')}")
            logger.info(f"Resolved data status: {resolved_data.get('properties', {}).get('status', 'N/A')}")
    
    def demo_sync_history_and_analytics(self):
        """Demonstrate sync history and analytics."""
        logger.info("\n=== Sync History and Analytics Demo ===")
        
        device_id = "history_test_device"
        
        # Perform multiple syncs to generate history
        for i in range(3):
            local_changes = self.generate_sample_changes(device_id, 2)
            remote_state = self.generate_remote_state()
            
            self.sync_service.sync_data(
                device_id=device_id,
                local_changes=local_changes,
                remote_data=remote_state
            )
        
        # Get sync history
        history = self.sync_service.get_sync_history(device_id, limit=10)
        logger.info(f"Sync history for device {device_id}:")
        
        for i, operation in enumerate(history):
            logger.info(f"  Operation {i+1}:")
            logger.info(f"    ID: {operation['operation_id']}")
            logger.info(f"    Type: {operation['operation_type']}")
            logger.info(f"    Status: {operation['status']}")
            logger.info(f"    Duration: {operation.get('duration_ms', 'N/A')}ms")
            logger.info(f"    Timestamp: {operation['timestamp']}")
    
    def demo_cleanup_operations(self):
        """Demonstrate cleanup operations."""
        logger.info("\n=== Cleanup Operations Demo ===")
        
        # Perform some syncs
        for i in range(3):
            device_id = f"cleanup_device_{i:03d}"
            local_changes = self.generate_sample_changes(device_id, 2)
            remote_state = self.generate_remote_state()
            
            self.sync_service.sync_data(
                device_id=device_id,
                local_changes=local_changes,
                remote_data=remote_state
            )
        
        # Get initial metrics
        initial_metrics = self.sync_service.get_metrics()
        logger.info(f"Initial total operations: {initial_metrics['metrics']['total_syncs']}")
        
        # Perform cleanup
        deleted_count = self.sync_service.cleanup_old_operations(days=1)
        logger.info(f"Cleanup deleted {deleted_count} operations")
        
        # Get final metrics
        final_metrics = self.sync_service.get_metrics()
        logger.info(f"Final total operations: {final_metrics['metrics']['total_syncs']}")
    
    def demo_error_handling_and_recovery(self):
        """Demonstrate error handling and recovery."""
        logger.info("\n=== Error Handling and Recovery Demo ===")
        
        device_id = "error_test_device"
        
        # Test with invalid data
        logger.info("Testing error handling with invalid data...")
        
        try:
            invalid_changes = [{"invalid": "data"}]
            invalid_remote = {"invalid": "structure"}
            
            result = self.sync_service.sync_data(
                device_id=device_id,
                local_changes=invalid_changes,
                remote_data=invalid_remote
            )
            logger.info("Unexpected success with invalid data")
        except Exception as e:
            logger.info(f"Expected error caught: {type(e).__name__}: {e}")
        
        # Test recovery with valid data
        logger.info("Testing recovery with valid data...")
        
        try:
            valid_changes = self.generate_sample_changes(device_id, 2)
            valid_remote = self.generate_remote_state()
            
            result = self.sync_service.sync_data(
                device_id=device_id,
                local_changes=valid_changes,
                remote_data=valid_remote
            )
            logger.info(f"Recovery successful: {result['status']}")
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
    
    def run_comprehensive_demo(self):
        """Run the comprehensive demonstration."""
        logger.info("Starting Offline Sync & Conflict Resolution Demo")
        logger.info("=" * 60)
        
        try:
            # Run all demo sections
            self.demo_basic_sync_operations()
            self.demo_conflict_detection_and_resolution()
            self.demo_rollback_capabilities()
            self.demo_performance_monitoring()
            self.demo_concurrent_sync_operations()
            self.demo_conflict_resolution_strategies()
            self.demo_sync_history_and_analytics()
            self.demo_cleanup_operations()
            self.demo_error_handling_and_recovery()
            
            logger.info("\n" + "=" * 60)
            logger.info("Demo completed successfully!")
            
            # Final metrics
            final_metrics = self.sync_service.get_metrics()
            logger.info("Final System Metrics:")
            logger.info(f"  Total syncs: {final_metrics['metrics']['total_syncs']}")
            logger.info(f"  Success rate: {final_metrics['metrics']['successful_syncs'] / max(final_metrics['metrics']['total_syncs'], 1) * 100:.1f}%")
            logger.info(f"  Conflicts resolved: {final_metrics['metrics']['conflicts_resolved']}")
            logger.info(f"  Total devices: {final_metrics['total_devices']}")
            
        except Exception as e:
            logger.error(f"Demo failed with error: {e}")
            raise


def main():
    """Main function to run the demo."""
    demo = OfflineSyncDemo()
    demo.run_comprehensive_demo()


if __name__ == "__main__":
    main() 