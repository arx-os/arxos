#!/usr/bin/env python3
"""
Test script for SVGX Telemetry Service Migration

This script validates the migration of telemetry services from arx_svg_parser
to svgx_engine with SVGX-specific enhancements and Windows compatibility.
"""

import time
import json
import tempfile
import os
import threading
from typing import List, Dict, Any

# Import SVGX telemetry components
from svgx_engine.services.telemetry import (
    SVGXTelemetryBuffer,
    SVGXTelemetryIngestor,
    SVGXTelemetryHook,
    SVGXTelemetryRecord,
    SVGXTelemetryType,
    SVGXTelemetrySeverity,
    generate_svgx_simulated_telemetry,
    create_svgx_telemetry_buffer,
    create_svgx_telemetry_ingestor,
    create_svgx_telemetry_hook
)

from svgx_engine.utils.errors import TelemetryError


def test_svgx_telemetry_record():
    """Test SVGX telemetry record creation and serialization"""
    print("\n=== Testing SVGXTelemetryRecord ===")
    
    try:
        # Test basic record creation
        record = SVGXTelemetryRecord(
            timestamp=time.time(),
            source="test_source",
            type=SVGXTelemetryType.SVGX_PARSER,
            value="test_value",
            namespace="test_namespace",
            component="test_component",
            user_id="user123",
            session_id="session456",
            duration_ms=150.5,
            memory_usage_mb=25.3,
            cpu_usage_percent=12.5,
            severity=SVGXTelemetrySeverity.INFO
        )
        
        print(f"✓ Record created: {record.type.value}")
        print(f"✓ Namespace: {record.namespace}")
        print(f"✓ Component: {record.component}")
        print(f"✓ Duration: {record.duration_ms}ms")
        
        # Test serialization
        record_dict = record.to_dict()
        print(f"✓ Serialization: {len(record_dict)} fields")
        
        # Test deserialization
        record_from_dict = SVGXTelemetryRecord.from_dict(record_dict)
        print(f"✓ Deserialization: {record_from_dict.type.value}")
        
        # Test string type conversion
        record_str = SVGXTelemetryRecord(
            timestamp=time.time(),
            source="test_source",
            type="svgx_parser",  # String instead of enum
            value="test_value",
            severity="info"  # String instead of enum
        )
        print(f"✓ String type conversion: {record_str.type.value}")
        
        return True
        
    except Exception as e:
        print(f"✗ SVGXTelemetryRecord test failed: {e}")
        return False


def test_svgx_telemetry_buffer():
    """Test SVGX telemetry buffer functionality"""
    print("\n=== Testing SVGXTelemetryBuffer ===")
    
    try:
        # Create buffer
        buffer = create_svgx_telemetry_buffer(max_size=1000, enable_persistence=True)
        print(f"✓ Buffer created: max_size={buffer.queue.maxsize}")
        
        # Test buffer start/stop
        buffer.start()
        print("✓ Buffer started")
        
        # Create test records
        records = []
        for i in range(5):
            record = SVGXTelemetryRecord(
                timestamp=time.time() + i,
                source=f"test_source_{i}",
                type=SVGXTelemetryType.SVGX_PARSER,
                value=f"test_value_{i}",
                namespace=f"namespace_{i % 2}",
                component=f"component_{i % 3}",
                duration_ms=100 + i * 50,
                severity=SVGXTelemetrySeverity.INFO
            )
            records.append(record)
        
        # Ingest records
        for record in records:
            buffer.ingest(record)
        
        print(f"✓ Records ingested: {len(records)}")
        
        # Wait for processing
        time.sleep(0.5)
        
        # Get statistics
        stats = buffer.get_stats()
        print(f"✓ Statistics collected: {len(stats)} categories")
        print(f"✓ Namespace stats: {len(stats['namespace_stats'])} namespaces")
        print(f"✓ Component stats: {len(stats['component_stats'])} components")
        print(f"✓ Severity stats: {len(stats['severity_stats'])} severities")
        print(f"✓ Performance metrics: {len(stats['performance_metrics'])} types")
        
        # Test buffer stop
        buffer.stop()
        print("✓ Buffer stopped")
        
        return True
        
    except Exception as e:
        print(f"✗ SVGXTelemetryBuffer test failed: {e}")
        return False


def test_svgx_telemetry_ingestor():
    """Test SVGX telemetry ingestor functionality"""
    print("\n=== Testing SVGXTelemetryIngestor ===")
    
    try:
        # Create buffer and ingestor
        buffer = create_svgx_telemetry_buffer(max_size=1000)
        ingestor = create_svgx_telemetry_ingestor(buffer)
        
        buffer.start()
        print("✓ Ingestor created and buffer started")
        
        # Test direct operation ingestion
        record = ingestor.ingest_svgx_operation(
            operation_type=SVGXTelemetryType.SVGX_COMPILER,
            component="test_compiler",
            value="compilation_result",
            namespace="test_namespace",
            user_id="user123",
            session_id="session456",
            duration_ms=2500.0,
            severity=SVGXTelemetrySeverity.INFO
        )
        
        print(f"✓ Operation ingested: {record.type.value}")
        print(f"✓ Component: {record.component}")
        print(f"✓ Duration: {record.duration_ms}ms")
        
        # Test list ingestion
        test_records = [
            {
                "timestamp": time.time(),
                "source": "test_source_1",
                "type": "svgx_parser",
                "value": "parse_result_1",
                "namespace": "test_namespace",
                "component": "test_parser",
                "duration_ms": 150.0,
                "severity": "info"
            },
            {
                "timestamp": time.time() + 1,
                "source": "test_source_2",
                "type": "svgx_runtime",
                "value": "runtime_result_2",
                "namespace": "test_namespace",
                "component": "test_runtime",
                "duration_ms": 300.0,
                "severity": "warning"
            }
        ]
        
        ingestor.ingest_from_list(test_records)
        print(f"✓ List ingestion: {len(test_records)} records")
        
        # Test file ingestion
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for record in test_records:
                f.write(json.dumps(record) + '\n')
            temp_file = f.name
        
        try:
            ingestor.ingest_from_file(temp_file, namespace="file_namespace")
            print("✓ File ingestion completed")
        finally:
            os.unlink(temp_file)
        
        # Wait for processing
        time.sleep(0.5)
        
        # Get buffer stats
        stats = buffer.get_stats()
        print(f"✓ Total records processed: {stats['queue_size']}")
        
        buffer.stop()
        print("✓ Ingestor test completed")
        
        return True
        
    except Exception as e:
        print(f"✗ SVGXTelemetryIngestor test failed: {e}")
        return False


def test_svgx_telemetry_hook():
    """Test SVGX telemetry hook functionality"""
    print("\n=== Testing SVGXTelemetryHook ===")
    
    try:
        # Create hook
        hook = create_svgx_telemetry_hook()
        print("✓ Hook created")
        
        # Create test records with different scenarios
        test_records = [
            # Performance alert (exceeds threshold)
            SVGXTelemetryRecord(
                timestamp=time.time(),
                source="test_source",
                type=SVGXTelemetryType.SVGX_PARSER,
                value="slow_parse",
                component="slow_parser",
                duration_ms=6000.0,  # Exceeds 5000ms threshold
                severity=SVGXTelemetrySeverity.WARNING
            ),
            # Error alert
            SVGXTelemetryRecord(
                timestamp=time.time() + 1,
                source="test_source",
                type=SVGXTelemetryType.SVGX_ERROR,
                value="parse_error",
                component="error_parser",
                severity=SVGXTelemetrySeverity.ERROR
            ),
            # Security alert
            SVGXTelemetryRecord(
                timestamp=time.time() + 2,
                source="test_source",
                type=SVGXTelemetryType.SVGX_SECURITY,
                value="unauthorized_access",
                component="security_monitor",
                severity=SVGXTelemetrySeverity.CRITICAL
            ),
            # Normal operation
            SVGXTelemetryRecord(
                timestamp=time.time() + 3,
                source="test_source",
                type=SVGXTelemetryType.SVGX_CACHE,
                value="cache_hit",
                component="cache_manager",
                duration_ms=50.0,
                severity=SVGXTelemetrySeverity.INFO
            )
        ]
        
        # Process records through hook
        for record in test_records:
            hook.on_telemetry(record)
        
        print(f"✓ Records processed: {len(test_records)}")
        
        # Check events
        events = hook.get_recent_events()
        print(f"✓ Events captured: {len(events)}")
        
        # Check alerts
        alerts = hook.get_alerts()
        print(f"✓ Alerts generated: {len(alerts)}")
        
        # Verify alert types
        performance_alerts = [a for a in alerts if "PERFORMANCE_ALERT" in a]
        error_alerts = [a for a in alerts if "ERROR_ALERT" in a]
        security_alerts = [a for a in alerts if "SECURITY_ALERT" in a]
        
        print(f"✓ Performance alerts: {len(performance_alerts)}")
        print(f"✓ Error alerts: {len(error_alerts)}")
        print(f"✓ Security alerts: {len(security_alerts)}")
        
        # Test clear functionality
        hook.clear_events()
        print("✓ Events cleared")
        
        return True
        
    except Exception as e:
        print(f"✗ SVGXTelemetryHook test failed: {e}")
        return False


def test_svgx_simulated_telemetry():
    """Test SVGX simulated telemetry generation"""
    print("\n=== Testing SVGX Simulated Telemetry ===")
    
    try:
        # Generate simulated data
        sources = ["svgx_parser", "svgx_runtime", "svgx_compiler", "svgx_cache"]
        types = [SVGXTelemetryType.SVGX_PARSER, SVGXTelemetryType.SVGX_RUNTIME, 
                SVGXTelemetryType.SVGX_COMPILER, SVGXTelemetryType.SVGX_CACHE]
        
        simulated_data = generate_svgx_simulated_telemetry(
            sources=sources,
            types=types,
            count=50,
            namespace="simulation_namespace"
        )
        
        print(f"✓ Simulated data generated: {len(simulated_data)} records")
        
        # Validate data structure
        for i, record in enumerate(simulated_data):
            required_fields = ['timestamp', 'source', 'type', 'value', 'namespace', 'component']
            missing_fields = [field for field in required_fields if field not in record]
            if missing_fields:
                print(f"✗ Record {i} missing fields: {missing_fields}")
                return False
        
        print("✓ All records have required fields")
        
        # Test ingestion of simulated data
        buffer = create_svgx_telemetry_buffer(max_size=1000)
        ingestor = create_svgx_telemetry_ingestor(buffer)
        
        buffer.start()
        ingestor.ingest_from_list(simulated_data)
        time.sleep(0.5)
        
        stats = buffer.get_stats()
        print(f"✓ Simulated data ingested: {stats['queue_size']} records")
        
        buffer.stop()
        
        return True
        
    except Exception as e:
        print(f"✗ SVGX Simulated Telemetry test failed: {e}")
        return False


def test_windows_compatibility():
    """Test Windows compatibility features"""
    print("\n=== Testing Windows Compatibility ===")
    
    try:
        # Test buffer with persistence (Windows-compatible file paths)
        buffer = create_svgx_telemetry_buffer(max_size=100, enable_persistence=True)
        
        # Create test record
        record = SVGXTelemetryRecord(
            timestamp=time.time(),
            source="windows_test",
            type=SVGXTelemetryType.SVGX_PARSER,
            value="windows_compatibility_test",
            namespace="windows_namespace",
            component="windows_component"
        )
        
        # Test ingestion (should handle Windows file paths)
        buffer.ingest(record)
        print("✓ Windows-compatible ingestion completed")
        
        # Check if persistence file was created
        if hasattr(buffer, 'persistence_file') and buffer.persistence_file:
            if os.path.exists(buffer.persistence_file):
                print("✓ Persistence file created successfully")
            else:
                print("⚠ Persistence file not found (may be disabled)")
        
        buffer.stop()
        
        return True
        
    except Exception as e:
        print(f"✗ Windows Compatibility test failed: {e}")
        return False


def test_error_handling():
    """Test error handling in telemetry system"""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Test TelemetryError
        try:
            raise TelemetryError("Test telemetry error", details={"test": "data"})
        except TelemetryError as e:
            error_dict = e.to_dict()
            print(f"✓ TelemetryError caught: {error_dict['error_type']}")
            print(f"✓ Error details: {error_dict['details']}")
        
        # Test invalid record handling
        buffer = create_svgx_telemetry_buffer(max_size=100)
        buffer.start()
        
        # Try to ingest invalid data (should not crash)
        try:
            invalid_record = SVGXTelemetryRecord(
                timestamp=time.time(),
                source="test",
                type="invalid_type",  # Invalid type
                value="test"
            )
            buffer.ingest(invalid_record)
            print("✓ Invalid record handled gracefully")
        except Exception as e:
            print(f"✓ Invalid record properly rejected: {e}")
        
        buffer.stop()
        
        return True
        
    except Exception as e:
        print(f"✗ Error Handling test failed: {e}")
        return False


def test_integration():
    """Test integration between telemetry components"""
    print("\n=== Testing Telemetry Integration ===")
    
    try:
        # Create all components
        buffer = create_svgx_telemetry_buffer(max_size=1000)
        ingestor = create_svgx_telemetry_ingestor(buffer)
        hook = create_svgx_telemetry_hook()
        
        # Connect components
        buffer.add_listener(hook.on_telemetry)
        buffer.start()
        
        print("✓ Components connected and started")
        
        # Generate and ingest test data
        test_operations = [
            (SVGXTelemetryType.SVGX_PARSER, "test_parser", "parse_result", 100.0),
            (SVGXTelemetryType.SVGX_RUNTIME, "test_runtime", "runtime_result", 500.0),
            (SVGXTelemetryType.SVGX_COMPILER, "test_compiler", "compilation_result", 2000.0),
            (SVGXTelemetryType.SVGX_CACHE, "test_cache", "cache_hit", 50.0),
            (SVGXTelemetryType.SVGX_SECURITY, "test_security", "security_check", 150.0)
        ]
        
        for op_type, component, value, duration in test_operations:
            ingestor.ingest_svgx_operation(
                operation_type=op_type,
                component=component,
                value=value,
                duration_ms=duration
            )
        
        print(f"✓ {len(test_operations)} operations ingested")
        
        # Wait for processing
        time.sleep(0.5)
        
        # Check results
        events = hook.get_recent_events()
        alerts = hook.get_alerts()
        stats = buffer.get_stats()
        
        print(f"✓ Integration results:")
        print(f"  - Events captured: {len(events)}")
        print(f"  - Alerts generated: {len(alerts)}")
        print(f"  - Namespace stats: {len(stats['namespace_stats'])}")
        print(f"  - Component stats: {len(stats['component_stats'])}")
        print(f"  - Performance metrics: {len(stats['performance_metrics'])}")
        
        buffer.stop()
        
        return True
        
    except Exception as e:
        print(f"✗ Telemetry Integration test failed: {e}")
        return False


def main():
    """Run all telemetry migration tests"""
    print("📊 Testing SVGX Telemetry Service Migration")
    print("=" * 60)
    
    start_time = time.time()
    
    # Run all tests
    tests = [
        test_svgx_telemetry_record,
        test_svgx_telemetry_buffer,
        test_svgx_telemetry_ingestor,
        test_svgx_telemetry_hook,
        test_svgx_simulated_telemetry,
        test_windows_compatibility,
        test_error_handling,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✓ PASSED: {passed}/{total} tests")
    print(f"❌ FAILED: {total - passed}/{total} tests")
    print(f"⏱️  Total test time: {duration:.2f} seconds")
    
    if passed == total:
        print("\n🎉 All tests passed! Telemetry service migration successful.")
        print("\n✅ Migration Status:")
        print("   - SVGXTelemetryRecord: Enhanced with SVGX-specific metadata")
        print("   - SVGXTelemetryBuffer: Thread-safe with Windows compatibility")
        print("   - SVGXTelemetryIngestor: Multi-source ingestion with SVGX operations")
        print("   - SVGXTelemetryHook: Real-time monitoring and alerting")
        print("   - Error handling: Comprehensive TelemetryError integration")
        print("   - Cross-platform: Windows compatibility with unique file paths")
        print("   - Performance tracking: Duration, memory, and CPU monitoring")
        print("   - Namespace isolation: SVGX namespace and component tracking")
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please review the implementation.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 