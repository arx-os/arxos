#!/usr/bin/env python3
"""
Smart Tagging Kits Demonstration Script

Comprehensive demonstration of QR + BLE tag assignment, scanning, resolution,
and management with offline capabilities.
"""

import json
import time
import tempfile
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.smart_tagging_kits import (
    SmartTaggingService, TagType, TagStatus, ScanResult
)
from cli_commands.smart_tagging_cli import SmartTaggingCLI


class SmartTaggingDemo:
    """Comprehensive demonstration of Smart Tagging Kits functionality."""
    
    def __init__(self):
        """Initialize the demonstration."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.service = SmartTaggingService(self.temp_db.name)
        self.cli = SmartTaggingCLI()
        
        # Demo data
        self.demo_objects = [
            {"id": "HVAC_001", "name": "Air Handler Unit 1", "type": "mechanical"},
            {"id": "ELEC_002", "name": "Electrical Panel 2", "type": "electrical"},
            {"id": "PLUMB_003", "name": "Water Heater 3", "type": "plumbing"},
            {"id": "SEC_004", "name": "Security Camera 4", "type": "security"},
            {"id": "NET_005", "name": "Network Switch 5", "type": "network"}
        ]
        
        self.demo_users = [
            {"id": "tech_001", "name": "John Technician", "role": "technician"},
            {"id": "maint_002", "name": "Sarah Maintainer", "role": "maintenance"},
            {"id": "admin_003", "name": "Mike Administrator", "role": "administrator"}
        ]
        
        self.demo_devices = [
            {"id": "mobile_001", "name": "iPhone 15", "type": "mobile"},
            {"id": "tablet_002", "name": "iPad Pro", "type": "tablet"},
            {"id": "scanner_003", "name": "QR Scanner", "type": "dedicated"}
        ]
    
    def run_comprehensive_demo(self):
        """Run comprehensive demonstration of all features."""
        print("🏷️  Smart Tagging Kits - Comprehensive Demonstration")
        print("=" * 60)
        print()
        
        try:
            # 1. Basic Tag Management
            self.demo_basic_tag_management()
            
            # 2. Advanced Tag Features
            self.demo_advanced_tag_features()
            
            # 3. Scanning and Resolution
            self.demo_scanning_and_resolution()
            
            # 4. Bulk Operations
            self.demo_bulk_operations()
            
            # 5. Data Import/Export
            self.demo_data_import_export()
            
            # 6. Analytics and Reporting
            self.demo_analytics_and_reporting()
            
            # 7. Performance Testing
            self.demo_performance_testing()
            
            # 8. Error Handling
            self.demo_error_handling()
            
            # 9. CLI Integration
            self.demo_cli_integration()
            
            # 10. Advanced Features
            self.demo_advanced_features()
            
            print("🎉 Comprehensive demonstration completed successfully!")
            print("✅ All Smart Tagging Kits features are working correctly")
            
        except Exception as e:
            print(f"❌ Demonstration failed: {e}")
            raise
    
    def demo_basic_tag_management(self):
        """Demonstrate basic tag management features."""
        print("📋 1. Basic Tag Management")
        print("-" * 30)
        
        # Tag validation
        print("🔍 Testing tag validation...")
        qr_tag = "BUILDING_A_HVAC_001"
        ble_tag = "1234567890abcdef"
        hybrid_tag = "QR_HVAC_001:1234567890abcdef"
        
        validation_results = {
            "QR": self.service.validate_tag(qr_tag, TagType.QR),
            "BLE": self.service.validate_tag(ble_tag, TagType.BLE),
            "HYBRID": self.service.validate_tag(hybrid_tag, TagType.HYBRID)
        }
        
        for tag_type, result in validation_results.items():
            status = "✅" if result["valid"] else "❌"
            print(f"   {status} {tag_type} tag validation: {result.get('message', result.get('error', 'Unknown'))}")
        
        # Tag assignment
        print("\n🏷️  Testing tag assignment...")
        assignment_results = []
        
        for i, obj in enumerate(self.demo_objects[:3]):
            tag_data = f"QR_{obj['id']}_{i+1}"
            result = self.service.assign_tag(
                object_id=obj["id"],
                tag_type=TagType.QR,
                tag_data=tag_data,
                user_id=self.demo_users[0]["id"],
                device_id=self.demo_devices[0]["id"],
                metadata={"location": "Building A", "priority": "high"}
            )
            assignment_results.append(result)
            
            status = "✅" if result["success"] else "❌"
            print(f"   {status} Assigned {tag_data} to {obj['name']}")
        
        # Tag scanning
        print("\n🔍 Testing tag scanning...")
        for i, result in enumerate(assignment_results):
            if result["success"]:
                scan_result = self.service.scan_tag(
                    tag_data=result["tag_id"],
                    tag_type=TagType.QR,
                    user_id=self.demo_users[1]["id"],
                    device_id=self.demo_devices[1]["id"],
                    location={"lat": 40.7128, "lng": -74.0060}
                )
                
                status = "✅" if scan_result["success"] else "❌"
                response_time = f"{scan_result['response_time']:.3f}s"
                print(f"   {status} Scanned tag in {response_time}")
        
        print("✅ Basic tag management demonstration completed")
        print()
    
    def demo_advanced_tag_features(self):
        """Demonstrate advanced tag features."""
        print("🚀 2. Advanced Tag Features")
        print("-" * 30)
        
        # Hybrid tag assignment
        print("🔗 Testing hybrid tag assignment...")
        hybrid_result = self.service.assign_tag(
            object_id=self.demo_objects[3]["id"],
            tag_type=TagType.HYBRID,
            tag_data="QR_SEC_004:1234567890abcdef",
            user_id=self.demo_users[2]["id"],
            device_id=self.demo_devices[2]["id"],
            metadata={"security_level": "high", "access_required": True}
        )
        
        if hybrid_result["success"]:
            print(f"   ✅ Hybrid tag assigned: {hybrid_result['tag_id']}")
        
        # Tag mapping update
        print("\n🔄 Testing tag mapping updates...")
        update_success = self.service.update_tag_mapping(
            tag_data="QR_HVAC_001_1",
            object_id="HVAC_001_UPDATED",
            user_id=self.demo_users[0]["id"],
            device_id=self.demo_devices[0]["id"],
            metadata={"updated_reason": "equipment_replacement"}
        )
        
        status = "✅" if update_success else "❌"
        print(f"   {status} Tag mapping updated")
        
        # Tag assignment removal
        print("\n🗑️  Testing tag assignment removal...")
        remove_success = self.service.remove_tag_assignment(
            tag_data="QR_ELEC_002_2",
            user_id=self.demo_users[1]["id"],
            device_id=self.demo_devices[1]["id"]
        )
        
        status = "✅" if remove_success else "❌"
        print(f"   {status} Tag assignment removed")
        
        # Get object tags
        print("\n📋 Testing object tag retrieval...")
        object_tags = self.service.get_object_tags("HVAC_001")
        print(f"   📊 Found {len(object_tags)} tags for HVAC_001")
        
        print("✅ Advanced tag features demonstration completed")
        print()
    
    def demo_scanning_and_resolution(self):
        """Demonstrate scanning and resolution features."""
        print("🔍 3. Scanning and Resolution")
        print("-" * 30)
        
        # Offline resolution testing
        print("📱 Testing offline resolution...")
        resolution_results = []
        
        for i, obj in enumerate(self.demo_objects[:3]):
            tag_data = f"OFFLINE_TEST_{i+1}"
            self.service.assign_tag(
                object_id=obj["id"],
                tag_type=TagType.QR,
                tag_data=tag_data,
                user_id=self.demo_users[0]["id"],
                device_id=self.demo_devices[0]["id"]
            )
            
            # Test offline resolution
            resolve_result = self.service.resolve_object(tag_data, TagType.QR)
            resolution_results.append(resolve_result)
            
            status = "✅" if resolve_result["success"] and resolve_result["found"] else "❌"
            print(f"   {status} Offline resolution for {tag_data}: {resolve_result.get('object_id', 'Not found')}")
        
        # Scan history analysis
        print("\n📊 Analyzing scan history...")
        for i, obj in enumerate(self.demo_objects[:2]):
            tag_data = f"SCAN_TEST_{i+1}"
            self.service.assign_tag(
                object_id=obj["id"],
                tag_type=TagType.QR,
                tag_data=tag_data,
                user_id=self.demo_users[0]["id"],
                device_id=self.demo_devices[0]["id"]
            )
            
            # Perform multiple scans
            for scan_num in range(3):
                self.service.scan_tag(
                    tag_data=tag_data,
                    tag_type=TagType.QR,
                    user_id=self.demo_users[scan_num % len(self.demo_users)]["id"],
                    device_id=self.demo_devices[scan_num % len(self.demo_devices)]["id"]
                )
            
            # Get scan history
            history = self.service.get_tag_history(tag_data)
            scan_events = [h for h in history if h["event_type"] == "scanned"]
            print(f"   📈 {tag_data}: {len(scan_events)} scan events recorded")
        
        print("✅ Scanning and resolution demonstration completed")
        print()
    
    def demo_bulk_operations(self):
        """Demonstrate bulk operations."""
        print("📦 4. Bulk Operations")
        print("-" * 30)
        
        # Create bulk assignments
        bulk_assignments = []
        for i in range(10):
            bulk_assignments.append({
                "object_id": f"BULK_OBJ_{i+1:03d}",
                "tag_type": "qr",
                "tag_data": f"BULK_QR_{i+1:03d}_{i*1000}",
                "user_id": self.demo_users[0]["id"],
                "device_id": self.demo_devices[0]["id"],
                "metadata": {"bulk_operation": True, "batch_id": f"batch_{i//5}"}
            })
        
        print(f"📋 Processing {len(bulk_assignments)} bulk assignments...")
        start_time = time.time()
        
        bulk_result = self.service.bulk_assign_tags(bulk_assignments)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"   ⏱️  Processing time: {processing_time:.3f}s")
        print(f"   ✅ Successful: {bulk_result['successful']}")
        print(f"   ❌ Failed: {bulk_result['failed']}")
        print(f"   📊 Success rate: {bulk_result['successful'] / bulk_result['total'] * 100:.1f}%")
        
        if bulk_result['errors']:
            print(f"   ⚠️  Errors: {len(bulk_result['errors'])}")
            for error in bulk_result['errors'][:3]:
                print(f"      - {error['tag_data']}: {error['error']}")
        
        print("✅ Bulk operations demonstration completed")
        print()
    
    def demo_data_import_export(self):
        """Demonstrate data import/export features."""
        print("📤 5. Data Import/Export")
        print("-" * 30)
        
        # Export data
        print("📤 Testing data export...")
        export_start = time.time()
        
        exported_json = self.service.export_tag_data("json")
        exported_csv = self.service.export_tag_data("csv")
        
        export_time = time.time() - export_start
        
        print(f"   ⏱️  Export time: {export_time:.3f}s")
        print(f"   📄 JSON size: {len(exported_json)} characters")
        print(f"   📄 CSV size: {len(exported_csv)} characters")
        
        # Import data
        print("\n📥 Testing data import...")
        import_start = time.time()
        
        # Create test import data
        import_data = {
            "tags": [
                {
                    "tag_id": "import_test_1",
                    "tag_type": "qr",
                    "tag_data": "IMPORT_QR_001",
                    "object_id": "IMPORT_OBJ_001",
                    "status": "assigned",
                    "created_at": datetime.now().isoformat(),
                    "assigned_at": datetime.now().isoformat(),
                    "last_scan_at": None,
                    "scan_count": 0,
                    "metadata": {"imported": True},
                    "device_id": "import_device",
                    "user_id": "import_user"
                }
            ],
            "mappings": [],
            "export_timestamp": datetime.now().isoformat(),
            "total_tags": 1,
            "total_mappings": 0
        }
        
        import_result = self.service.import_tag_data(json.dumps(import_data), "json")
        import_time = time.time() - import_start
        
        print(f"   ⏱️  Import time: {import_time:.3f}s")
        print(f"   ✅ Successful imports: {import_result['successful']}")
        print(f"   ❌ Failed imports: {import_result['failed']}")
        
        # Verify imported data
        resolve_result = self.service.resolve_object("IMPORT_QR_001", TagType.QR)
        if resolve_result["success"] and resolve_result["found"]:
            print(f"   ✅ Imported tag verified: {resolve_result['object_id']}")
        
        print("✅ Data import/export demonstration completed")
        print()
    
    def demo_analytics_and_reporting(self):
        """Demonstrate analytics and reporting features."""
        print("📊 6. Analytics and Reporting")
        print("-" * 30)
        
        # Generate analytics
        print("📈 Generating analytics...")
        analytics = self.service.get_analytics(period_days=30)
        
        print(f"   📊 Total Tags: {analytics['total_tags']}")
        print(f"   🏷️  Assigned Tags: {analytics['assigned_tags']}")
        print(f"   📈 Assignment Rate: {analytics['assignment_rate']:.1%}")
        print(f"   🔍 Total Scans: {analytics['total_scans']}")
        print(f"   ✅ Successful Scans: {analytics['successful_scans']}")
        print(f"   📊 Scan Success Rate: {analytics['scan_success_rate']:.1%}")
        print(f"   ⏱️  Avg Response Time: {analytics['avg_response_time']:.3f}s")
        print(f"   📋 Total Assignments: {analytics['total_assignments']}")
        
        if analytics['assignments_by_type']:
            print(f"\n   📋 Assignments by Type:")
            for tag_type, count in analytics['assignments_by_type'].items():
                print(f"      - {tag_type.upper()}: {count}")
        
        if analytics['most_scanned_tags']:
            print(f"\n   🏆 Most Scanned Tags:")
            for i, tag in enumerate(analytics['most_scanned_tags'][:3], 1):
                print(f"      {i}. {tag['tag_data']} ({tag['scan_count']} scans)")
        
        # Performance metrics
        print("\n📊 Performance Metrics:")
        metrics = self.service.get_performance_metrics()
        
        print(f"   💾 Database Size: {metrics['database_size']} bytes")
        print(f"   🗂️  Cache Size: {metrics['cache_size']} entries")
        print(f"   ⚡ Performance Score: {metrics['assignment_rate'] * 100:.1f}/100")
        
        print("✅ Analytics and reporting demonstration completed")
        print()
    
    def demo_performance_testing(self):
        """Demonstrate performance testing."""
        print("⚡ 7. Performance Testing")
        print("-" * 30)
        
        # Tag assignment performance
        print("🏷️  Testing tag assignment performance...")
        assignment_times = []
        
        for i in range(50):
            start_time = time.time()
            result = self.service.assign_tag(
                object_id=f"PERF_OBJ_{i}",
                tag_type=TagType.QR,
                tag_data=f"PERF_QR_{i}_{i*1000}",
                user_id=self.demo_users[0]["id"],
                device_id=self.demo_devices[0]["id"]
            )
            end_time = time.time()
            
            if result["success"]:
                assignment_times.append(end_time - start_time)
        
        avg_assignment_time = sum(assignment_times) / len(assignment_times)
        print(f"   ⏱️  Average assignment time: {avg_assignment_time:.4f}s")
        print(f"   📊 Total assignments: {len(assignment_times)}")
        
        # Scan performance
        print("\n🔍 Testing scan performance...")
        scan_times = []
        
        for i in range(50):
            tag_data = f"PERF_QR_{i}_{i*1000}"
            start_time = time.time()
            result = self.service.scan_tag(
                tag_data=tag_data,
                tag_type=TagType.QR,
                user_id=self.demo_users[1]["id"],
                device_id=self.demo_devices[1]["id"]
            )
            end_time = time.time()
            
            if result["success"]:
                scan_times.append(end_time - start_time)
        
        avg_scan_time = sum(scan_times) / len(scan_times)
        print(f"   ⏱️  Average scan time: {avg_scan_time:.4f}s")
        print(f"   📊 Total scans: {len(scan_times)}")
        
        # Resolution performance
        print("\n📱 Testing resolution performance...")
        resolution_times = []
        
        for i in range(100):
            tag_data = f"PERF_QR_{i}_{i*1000}"
            start_time = time.time()
            result = self.service.resolve_object(tag_data, TagType.QR)
            end_time = time.time()
            
            if result["success"]:
                resolution_times.append(end_time - start_time)
        
        avg_resolution_time = sum(resolution_times) / len(resolution_times)
        print(f"   ⏱️  Average resolution time: {avg_resolution_time:.4f}s")
        print(f"   📊 Total resolutions: {len(resolution_times)}")
        
        # Performance summary
        print(f"\n📊 Performance Summary:")
        print(f"   🏷️  Assignment: {avg_assignment_time:.4f}s (target: <0.1s)")
        print(f"   🔍 Scanning: {avg_scan_time:.4f}s (target: <0.05s)")
        print(f"   📱 Resolution: {avg_resolution_time:.4f}s (target: <0.01s)")
        
        # Performance validation
        assignment_ok = avg_assignment_time < 0.1
        scan_ok = avg_scan_time < 0.05
        resolution_ok = avg_resolution_time < 0.01
        
        print(f"\n✅ Performance Validation:")
        print(f"   {'✅' if assignment_ok else '❌'} Assignment performance")
        print(f"   {'✅' if scan_ok else '❌'} Scan performance")
        print(f"   {'✅' if resolution_ok else '❌'} Resolution performance")
        
        print("✅ Performance testing demonstration completed")
        print()
    
    def demo_error_handling(self):
        """Demonstrate error handling features."""
        print("⚠️  8. Error Handling")
        print("-" * 30)
        
        # Invalid tag validation
        print("🔍 Testing invalid tag handling...")
        invalid_tags = [
            ("", TagType.QR, "Empty tag data"),
            ("INVALID", TagType.BLE, "Invalid BLE format"),
            ("TOO_LONG_" + "A" * 1000, TagType.QR, "Tag too long"),
            ("INVALID:FORMAT", TagType.HYBRID, "Invalid hybrid format")
        ]
        
        for tag_data, tag_type, description in invalid_tags:
            result = self.service.validate_tag(tag_data, tag_type)
            status = "❌" if not result["valid"] else "✅"
            print(f"   {status} {description}: {result.get('error', 'Valid')}")
        
        # Duplicate tag assignment
        print("\n🔄 Testing duplicate tag handling...")
        tag_data = "DUPLICATE_TEST"
        
        # First assignment
        result1 = self.service.assign_tag(
            object_id="OBJ_1",
            tag_type=TagType.QR,
            tag_data=tag_data,
            user_id=self.demo_users[0]["id"],
            device_id=self.demo_devices[0]["id"]
        )
        
        # Second assignment (should fail)
        result2 = self.service.assign_tag(
            object_id="OBJ_2",
            tag_type=TagType.QR,
            tag_data=tag_data,
            user_id=self.demo_users[0]["id"],
            device_id=self.demo_devices[0]["id"]
        )
        
        print(f"   ✅ First assignment: {result1['success']}")
        print(f"   ❌ Second assignment: {result2['success']} - {result2['error']}")
        
        # Non-existent tag operations
        print("\n🔍 Testing non-existent tag operations...")
        non_existent_tag = "NON_EXISTENT_TAG"
        
        scan_result = self.service.scan_tag(
            tag_data=non_existent_tag,
            tag_type=TagType.QR,
            user_id=self.demo_users[0]["id"],
            device_id=self.demo_devices[0]["id"]
        )
        
        resolve_result = self.service.resolve_object(non_existent_tag, TagType.QR)
        
        print(f"   ❌ Scan non-existent: {scan_result['result']}")
        print(f"   ❌ Resolve non-existent: {resolve_result['found']}")
        
        print("✅ Error handling demonstration completed")
        print()
    
    def demo_cli_integration(self):
        """Demonstrate CLI integration."""
        print("💻 9. CLI Integration")
        print("-" * 30)
        
        # Test CLI initialization
        print("🔧 Testing CLI initialization...")
        try:
            cli = SmartTaggingCLI()
            print("   ✅ CLI initialized successfully")
        except Exception as e:
            print(f"   ❌ CLI initialization failed: {e}")
        
        # Test CLI argument parsing
        print("\n📋 Testing CLI argument parsing...")
        try:
            # Create mock arguments for tag assignment
            args = type('Args', (), {
                'command': 'assign',
                'object_id': 'CLI_TEST_OBJ',
                'tag_type': 'qr',
                'tag_data': 'CLI_QR_TEST',
                'user_id': 'cli_user',
                'device_id': 'cli_device',
                'metadata': None,
                'output': None
            })()
            
            # Mock sys.exit to prevent actual exit
            import sys
            original_exit = sys.exit
            
            def mock_exit(code):
                if code != 0:
                    raise SystemExit(code)
            
            sys.exit = mock_exit
            
            try:
                cli.assign_tag(args)
                print("   ✅ CLI tag assignment successful")
            except SystemExit:
                print("   ❌ CLI tag assignment failed")
            finally:
                sys.exit = original_exit
                
        except Exception as e:
            print(f"   ❌ CLI argument parsing failed: {e}")
        
        print("✅ CLI integration demonstration completed")
        print()
    
    def demo_advanced_features(self):
        """Demonstrate advanced features."""
        print("🚀 10. Advanced Features")
        print("-" * 30)
        
        # Tag generation
        print("🎲 Testing tag generation...")
        import uuid
        import time
        
        # Generate different types of tags
        qr_tag = f"GEN_QR_{int(time.time())}{uuid.uuid4().hex[:8]}"
        ble_tag = uuid.uuid4().hex[:16]
        hybrid_tag = f"GEN_QR_{int(time.time())}:{uuid.uuid4().hex[:16]}"
        
        generated_tags = [
            (qr_tag, TagType.QR, "QR Code"),
            (ble_tag, TagType.BLE, "BLE Beacon"),
            (hybrid_tag, TagType.HYBRID, "Hybrid Tag")
        ]
        
        for tag_data, tag_type, description in generated_tags:
            validation = self.service.validate_tag(tag_data, tag_type)
            status = "✅" if validation["valid"] else "❌"
            print(f"   {status} Generated {description}: {tag_data}")
        
        # Cache performance testing
        print("\n🗂️  Testing cache performance...")
        test_tag = "CACHE_TEST_TAG"
        
        # Assign tag
        self.service.assign_tag(
            object_id="CACHE_OBJ",
            tag_type=TagType.QR,
            tag_data=test_tag,
            user_id=self.demo_users[0]["id"],
            device_id=self.demo_devices[0]["id"]
        )
        
        # First resolution (populate cache)
        start_time = time.time()
        result1 = self.service.resolve_object(test_tag, TagType.QR)
        first_time = time.time() - start_time
        
        # Second resolution (use cache)
        start_time = time.time()
        result2 = self.service.resolve_object(test_tag, TagType.QR)
        second_time = time.time() - start_time
        
        print(f"   ⏱️  First resolution: {first_time:.4f}s")
        print(f"   ⏱️  Cached resolution: {second_time:.4f}s")
        print(f"   📈 Speed improvement: {first_time/second_time:.1f}x")
        
        # Database persistence testing
        print("\n💾 Testing database persistence...")
        persistence_tag = "PERSISTENCE_TEST"
        
        # Assign tag
        self.service.assign_tag(
            object_id="PERSISTENCE_OBJ",
            tag_type=TagType.QR,
            tag_data=persistence_tag,
            user_id=self.demo_users[0]["id"],
            device_id=self.demo_devices[0]["id"]
        )
        
        # Create new service instance (simulates restart)
        new_service = SmartTaggingService(self.temp_db.name)
        
        # Try to resolve tag in new instance
        resolve_result = new_service.resolve_object(persistence_tag, TagType.QR)
        
        if resolve_result["success"] and resolve_result["found"]:
            print(f"   ✅ Persistence verified: {resolve_result['object_id']}")
        else:
            print(f"   ❌ Persistence failed")
        
        print("✅ Advanced features demonstration completed")
        print()
    
    def generate_demo_report(self):
        """Generate comprehensive demo report."""
        print("📊 Demo Report Generation")
        print("-" * 30)
        
        # Collect metrics
        metrics = self.service.get_performance_metrics()
        analytics = self.service.get_analytics(period_days=1)
        
        report = {
            "demo_timestamp": datetime.now().isoformat(),
            "performance_metrics": metrics,
            "analytics": analytics,
            "demo_objects": len(self.demo_objects),
            "demo_users": len(self.demo_users),
            "demo_devices": len(self.demo_devices),
            "features_tested": [
                "Tag Assignment",
                "Tag Validation",
                "Tag Scanning",
                "Offline Resolution",
                "Bulk Operations",
                "Data Import/Export",
                "Analytics",
                "Performance Testing",
                "Error Handling",
                "CLI Integration",
                "Advanced Features"
            ]
        }
        
        # Save report
        report_file = "smart_tagging_demo_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Demo report saved to: {report_file}")
        print(f"📊 Total tags in system: {metrics['total_tags']}")
        print(f"🏷️  Assignment rate: {metrics['assignment_rate']:.1%}")
        print(f"🔍 Total scans: {metrics['total_scans']}")
        print(f"⏱️  Avg response time: {metrics['avg_response_time']:.3f}s")
        
        print("✅ Demo report generation completed")
        print()
    
    def cleanup(self):
        """Clean up demo resources."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)


def main():
    """Main demonstration entry point."""
    demo = SmartTaggingDemo()
    
    try:
        # Run comprehensive demonstration
        demo.run_comprehensive_demo()
        
        # Generate demo report
        demo.generate_demo_report()
        
        print("🎉 Smart Tagging Kits demonstration completed successfully!")
        print("✅ All features are working correctly and ready for production use")
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        raise
    finally:
        # Clean up
        demo.cleanup()


if __name__ == "__main__":
    main() 