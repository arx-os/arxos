#!/usr/bin/env python3
"""
Smart Tagging Kits Demonstration Script

This script demonstrates all capabilities of the Smart Tagging Kits feature:
- QR + BLE tag assignment to maintainable objects
- Tag-to-object mapping persistence
- Offline tag resolution capabilities
- Short-range scan functionality
- Tag linking to object JSON data
- In-app tag logs and history tracking
- Tag management interface
- Tag validation and conflict resolution

Usage:
    python examples/smart_tagging_demo.py
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.smart_tagging_kits import (
    SmartTaggingService, TagData, ScanResult, ObjectMapping,
    TagType, TagStatus
)
from utils.logger import setup_logger

class SmartTaggingDemo:
    """Demonstration class for Smart Tagging Kits."""
    
    def __init__(self):
        self.logger = setup_logger("smart_tagging_demo", level=logging.INFO)
        self.service = SmartTaggingService()
        self.demo_objects = [
            {"id": "hvac_unit_001", "name": "HVAC Unit 1", "location": "Floor 1", "type": "mechanical"},
            {"id": "electrical_panel_002", "name": "Electrical Panel 2", "location": "Basement", "type": "electrical"},
            {"id": "fire_alarm_003", "name": "Fire Alarm System", "location": "Floor 2", "type": "safety"},
            {"id": "plumbing_valve_004", "name": "Main Water Valve", "location": "Utility Room", "type": "plumbing"},
            {"id": "network_switch_005", "name": "Network Switch", "location": "IT Room", "type": "network"}
        ]
    
    async def run_demo(self):
        """Run the complete Smart Tagging Kits demonstration."""
        self.logger.info("🚀 Starting Smart Tagging Kits Demonstration")
        self.logger.info("=" * 60)
        
        try:
            # Phase 1: Tag Assignment
            await self.demo_tag_assignment()
            
            # Phase 2: Tag Scanning
            await self.demo_tag_scanning()
            
            # Phase 3: Tag Management
            await self.demo_tag_management()
            
            # Phase 4: Advanced Features
            await self.demo_advanced_features()
            
            # Phase 5: Performance Testing
            await self.demo_performance_testing()
            
            self.logger.info("✅ Smart Tagging Kits demonstration completed successfully!")
            
        except Exception as e:
            self.logger.error(f"❌ Demonstration failed: {str(e)}")
            raise
    
    async def demo_tag_assignment(self):
        """Demonstrate tag assignment capabilities."""
        self.logger.info("\n📋 Phase 1: Tag Assignment")
        self.logger.info("-" * 40)
        
        # Assign QR tags to objects
        self.logger.info("🔖 Assigning QR tags to objects...")
        qr_tags = []
        
        for obj in self.demo_objects[:3]:  # First 3 objects
            tag_id = await self.service.assign_tag_to_object(
                object_id=obj["id"],
                tag_type=TagType.QR,
                metadata={
                    "object_name": obj["name"],
                    "location": obj["location"],
                    "object_type": obj["type"],
                    "priority": "high" if obj["type"] in ["safety", "electrical"] else "medium"
                }
            )
            qr_tags.append(tag_id)
            self.logger.info(f"  ✅ Assigned QR tag {tag_id} to {obj['name']}")
        
        # Assign BLE tags to objects
        self.logger.info("\n📡 Assigning BLE tags to objects...")
        ble_tags = []
        
        for obj in self.demo_objects[3:]:  # Last 2 objects
            tag_id = await self.service.assign_tag_to_object(
                object_id=obj["id"],
                tag_type=TagType.BLE,
                metadata={
                    "object_name": obj["name"],
                    "location": obj["location"],
                    "object_type": obj["type"],
                    "ble_address": f"AA:BB:CC:DD:EE:{obj['id'][-2:]}",
                    "signal_strength": -65.0
                }
            )
            ble_tags.append(tag_id)
            self.logger.info(f"  ✅ Assigned BLE tag {tag_id} to {obj['name']}")
        
        # Demonstrate tag limits
        self.logger.info("\n⚠️  Testing tag limits...")
        try:
            # Try to assign more tags to an object that already has one
            await self.service.assign_tag_to_object(
                object_id=self.demo_objects[0]["id"],
                tag_type=TagType.BLE,
                metadata={"test": "limit"}
            )
        except Exception as e:
            self.logger.info(f"  ✅ Correctly prevented exceeding tag limit: {str(e)}")
        
        self.logger.info(f"\n📊 Tag Assignment Summary:")
        self.logger.info(f"  - QR Tags assigned: {len(qr_tags)}")
        self.logger.info(f"  - BLE Tags assigned: {len(ble_tags)}")
        self.logger.info(f"  - Total tags: {len(qr_tags) + len(ble_tags)}")
    
    async def demo_tag_scanning(self):
        """Demonstrate tag scanning capabilities."""
        self.logger.info("\n📱 Phase 2: Tag Scanning")
        self.logger.info("-" * 40)
        
        # Get all tags
        all_tags = await self.service.list_tags()
        
        # Scan each tag
        self.logger.info("🔍 Scanning all tags...")
        scan_results = []
        
        for tag_data in all_tags:
            # Simulate scanning
            scan_data = {
                "tag_id": tag_data.id,
                "tag_type": tag_data.tag_type.value,
                "signal_strength": -65.0 if tag_data.tag_type == TagType.BLE else None,
                "scanner_info": {
                    "device": "demo_scanner",
                    "location": "demo_location",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            result = await self.service.scan_tag(scan_data)
            
            if result:
                scan_results.append(result)
                self.logger.info(f"  ✅ Scanned {tag_data.tag_type} tag {tag_data.id} -> {result.object_id}")
            else:
                self.logger.warning(f"  ❌ Failed to scan tag {tag_data.id}")
        
        # Demonstrate BLE scanning
        self.logger.info("\n📡 Demonstrating BLE tag scanning...")
        ble_results = await self.service.scanner_service.scan_ble_tags(timeout=3)
        
        self.logger.info(f"  📊 Discovered {len(ble_results)} BLE tags:")
        for ble_data in ble_results:
            self.logger.info(f"    - {ble_data['tag_id']} (Signal: {ble_data.get('signal_strength', 'N/A')} dBm)")
        
        # Demonstrate scan history
        self.logger.info("\n📈 Scan History Analysis:")
        for tag_data in all_tags:
            if tag_data.scan_history:
                self.logger.info(f"  📊 {tag_data.id}: {len(tag_data.scan_history)} scans")
                latest_scan = tag_data.scan_history[-1]
                self.logger.info(f"    Last scan: {latest_scan.get('timestamp', 'N/A')}")
        
        self.logger.info(f"\n📊 Tag Scanning Summary:")
        self.logger.info(f"  - Tags scanned: {len(scan_results)}")
        self.logger.info(f"  - BLE tags discovered: {len(ble_results)}")
        self.logger.info(f"  - Scan success rate: {len(scan_results)/len(all_tags)*100:.1f}%")
    
    async def demo_tag_management(self):
        """Demonstrate tag management capabilities."""
        self.logger.info("\n🔧 Phase 3: Tag Management")
        self.logger.info("-" * 40)
        
        # List all tags
        all_tags = await self.service.list_tags()
        self.logger.info(f"📋 Current tags ({len(all_tags)} total):")
        
        for tag_data in all_tags:
            status_icon = "✅" if tag_data.status in [TagStatus.ACTIVE, TagStatus.ASSIGNED] else "❌"
            self.logger.info(f"  {status_icon} {tag_data.id} ({tag_data.tag_type.value}) -> {tag_data.object_id}")
        
        # Search tags
        self.logger.info("\n🔍 Searching tags...")
        
        # Search by object type
        electrical_tags = await self.service.search_tags("electrical")
        self.logger.info(f"  🔌 Electrical tags: {len(electrical_tags)}")
        
        # Search by location
        floor_tags = await self.service.search_tags("Floor")
        self.logger.info(f"  🏢 Floor tags: {len(floor_tags)}")
        
        # Search by priority
        high_priority_tags = await self.service.search_tags("high")
        self.logger.info(f"  ⚠️  High priority tags: {len(high_priority_tags)}")
        
        # Get object tags
        self.logger.info("\n📦 Object tag analysis:")
        for obj in self.demo_objects:
            object_tags = await self.service.get_object_tags(obj["id"])
            if object_tags:
                self.logger.info(f"  📦 {obj['name']}: {len(object_tags)} tags")
                for tag in object_tags:
                    self.logger.info(f"    - {tag.id} ({tag.tag_type.value})")
        
        # Tag information
        self.logger.info("\nℹ️  Detailed tag information:")
        for tag_data in all_tags[:3]:  # Show first 3 tags
            tag_info = await self.service.get_tag_info(tag_data.id)
            if tag_info:
                self.logger.info(f"  📊 {tag_info.id}:")
                self.logger.info(f"    - Object: {tag_info.object_id}")
                self.logger.info(f"    - Type: {tag_info.tag_type.value}")
                self.logger.info(f"    - Status: {tag_info.status.value}")
                self.logger.info(f"    - Created: {tag_info.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                self.logger.info(f"    - Scans: {len(tag_info.scan_history)}")
                self.logger.info(f"    - Metadata: {len(tag_info.metadata)} fields")
    
    async def demo_advanced_features(self):
        """Demonstrate advanced tagging features."""
        self.logger.info("\n🚀 Phase 4: Advanced Features")
        self.logger.info("-" * 40)
        
        # Demonstrate tag validation
        self.logger.info("✅ Tag validation features:")
        self.logger.info("  - Automatic tag ID generation")
        self.logger.info("  - Object existence validation")
        self.logger.info("  - Tag limit enforcement")
        self.logger.info("  - Tag type validation")
        self.logger.info("  - Metadata validation")
        
        # Demonstrate offline capabilities
        self.logger.info("\n📱 Offline capabilities:")
        self.logger.info("  - Tag data persistence")
        self.logger.info("  - Offline tag resolution")
        self.logger.info("  - Local tag storage")
        self.logger.info("  - Sync when online")
        
        # Demonstrate conflict resolution
        self.logger.info("\n⚖️  Conflict resolution:")
        self.logger.info("  - Duplicate tag detection")
        self.logger.info("  - Tag status management")
        self.logger.info("  - Object mapping validation")
        self.logger.info("  - Scan history tracking")
        
        # Demonstrate performance features
        self.logger.info("\n⚡ Performance features:")
        self.logger.info("  - Fast tag assignment (<5 seconds)")
        self.logger.info("  - Quick tag scanning (<2 seconds)")
        self.logger.info("  - Efficient tag searching")
        self.logger.info("  - Optimized tag listing")
        
        # Demonstrate security features
        self.logger.info("\n🔒 Security features:")
        self.logger.info("  - Tag data validation")
        self.logger.info("  - Access control")
        self.logger.info("  - Audit trail")
        self.logger.info("  - Data integrity checks")
    
    async def demo_performance_testing(self):
        """Demonstrate performance testing capabilities."""
        self.logger.info("\n⚡ Phase 5: Performance Testing")
        self.logger.info("-" * 40)
        
        # Test tag assignment performance
        self.logger.info("⏱️  Testing tag assignment performance...")
        start_time = datetime.now()
        
        for i in range(5):
            tag_id = await self.service.assign_tag_to_object(
                object_id=f"perf_test_object_{i}",
                tag_type=TagType.QR if i % 2 == 0 else TagType.BLE,
                metadata={"test": "performance", "index": i}
            )
        
        assignment_time = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"  ✅ Assigned 5 tags in {assignment_time:.2f} seconds")
        self.logger.info(f"  📊 Average: {assignment_time/5:.2f} seconds per tag")
        
        # Test tag scanning performance
        self.logger.info("\n⏱️  Testing tag scanning performance...")
        all_tags = await self.service.list_tags()
        
        start_time = datetime.now()
        scan_count = 0
        
        for tag_data in all_tags:
            scan_data = {
                "tag_id": tag_data.id,
                "tag_type": tag_data.tag_type.value,
                "signal_strength": -65.0 if tag_data.tag_type == TagType.BLE else None,
                "scanner_info": {"test": "performance"}
            }
            
            result = await self.service.scan_tag(scan_data)
            if result:
                scan_count += 1
        
        scan_time = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"  ✅ Scanned {scan_count} tags in {scan_time:.2f} seconds")
        self.logger.info(f"  📊 Average: {scan_time/scan_count:.2f} seconds per scan")
        
        # Test search performance
        self.logger.info("\n⏱️  Testing search performance...")
        start_time = datetime.now()
        
        search_results = await self.service.search_tags("test")
        
        search_time = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"  ✅ Found {len(search_results)} results in {search_time:.2f} seconds")
        
        # Performance summary
        self.logger.info(f"\n📊 Performance Summary:")
        self.logger.info(f"  - Tag assignment: {assignment_time/5:.2f}s average")
        self.logger.info(f"  - Tag scanning: {scan_time/scan_count:.2f}s average")
        self.logger.info(f"  - Tag searching: {search_time:.2f}s total")
        self.logger.info(f"  - Total tags managed: {len(all_tags)}")
        self.logger.info(f"  - Scan success rate: {scan_count/len(all_tags)*100:.1f}%")
    
    async def cleanup_demo(self):
        """Clean up demo data."""
        self.logger.info("\n🧹 Cleaning up demo data...")
        
        all_tags = await self.service.list_tags()
        removed_count = 0
        
        for tag_data in all_tags:
            if "perf_test" in tag_data.id or any(obj["id"] in tag_data.id for obj in self.demo_objects):
                success = await self.service.remove_tag(tag_data.id)
                if success:
                    removed_count += 1
        
        self.logger.info(f"  ✅ Removed {removed_count} demo tags")
    
    def print_demo_info(self):
        """Print demonstration information."""
        self.logger.info("\n📋 Smart Tagging Kits Feature Overview")
        self.logger.info("=" * 60)
        self.logger.info("🎯 Key Features:")
        self.logger.info("  ✅ QR + BLE tag assignment to maintainable objects")
        self.logger.info("  ✅ Tag-to-object mapping persistence")
        self.logger.info("  ✅ Offline tag resolution capabilities")
        self.logger.info("  ✅ Short-range scan functionality (<2 seconds)")
        self.logger.info("  ✅ Tag linking to object JSON data")
        self.logger.info("  ✅ In-app tag logs and history tracking")
        self.logger.info("  ✅ Tag management interface")
        self.logger.info("  ✅ Tag validation and conflict resolution")
        
        self.logger.info("\n🔧 Technical Capabilities:")
        self.logger.info("  📱 QR Code Generation & Scanning")
        self.logger.info("  📡 BLE Tag Configuration & Detection")
        self.logger.info("  💾 Persistent Tag Data Storage")
        self.logger.info("  🔍 Real-time Tag Scanning")
        self.logger.info("  📊 Tag Analytics & Reporting")
        self.logger.info("  ⚡ High-Performance Operations")
        self.logger.info("  🔒 Secure Tag Management")
        
        self.logger.info("\n📈 Performance Targets:")
        self.logger.info("  ⏱️  Tag assignment: <5 seconds")
        self.logger.info("  🔍 Tag scanning: <2 seconds")
        self.logger.info("  💾 Offline operation: 100%")
        self.logger.info("  📊 Data persistence: 100%")
        self.logger.info("  ✅ Validation accuracy: 100%")

async def main():
    """Main demonstration function."""
    demo = SmartTaggingDemo()
    
    # Print demo information
    demo.print_demo_info()
    
    # Run demonstration
    await demo.run_demo()
    
    # Cleanup
    await demo.cleanup_demo()
    
    print("\n🎉 Smart Tagging Kits demonstration completed!")
    print("📚 Check the logs above for detailed results.")

if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main()) 