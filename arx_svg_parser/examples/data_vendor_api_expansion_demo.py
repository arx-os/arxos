#!/usr/bin/env python3
"""
Data Vendor API Expansion Demo

Demonstrates advanced analytics, data masking, encryption, compliance checking,
audit logging, and data export capabilities for vendor data APIs.
"""

import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from services.data_vendor_api_expansion import (
    data_vendor_api_expansion,
    DataMaskingLevel,
    ComplianceType
)


class DataVendorAPIExpansionDemo:
    """Demonstration class for Data Vendor API Expansion features."""
    
    def __init__(self):
        self.service = data_vendor_api_expansion
        self.demo_data = self._create_demo_data()
    
    def _create_demo_data(self) -> Dict[str, Any]:
        """Create comprehensive demo data for testing."""
        return {
            "vendor_id": "demo_vendor_001",
            "name": "Demo Vendor Corporation",
            "email": "contact@demovendor.com",
            "phone": "555-987-6543",
            "address": "456 Business Avenue, Tech City, USA",
            "ssn": "987-65-4321",
            "credit_card": "5555-4444-3333-2222",
            "ip_address": "10.0.0.100",
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "financial_data": {
                "revenue": 2500000,
                "profit": 350000,
                "tax_id": "98-7654321",
                "bank_account": "1234567890"
            },
            "medical_record": {
                "patient_id": "P98765",
                "diagnosis": "Type 2 Diabetes",
                "treatment": "Metformin 500mg twice daily",
                "blood_pressure": "140/90"
            },
            "personal_info": {
                "date_of_birth": "1985-03-15",
                "driver_license": "DL123456789",
                "passport": "P123456789"
            }
        }
    
    def run_comprehensive_demo(self):
        """Run comprehensive demonstration of all features."""
        print("=" * 80)
        print("DATA VENDOR API EXPANSION - COMPREHENSIVE DEMONSTRATION")
        print("=" * 80)
        
        try:
            # 1. Analytics Demo
            self._demo_analytics()
            
            # 2. Data Masking Demo
            self._demo_data_masking()
            
            # 3. Encryption Demo
            self._demo_encryption()
            
            # 4. Compliance Demo
            self._demo_compliance()
            
            # 5. Audit Logging Demo
            self._demo_audit_logging()
            
            # 6. Data Export Demo
            self._demo_data_export()
            
            # 7. Performance Demo
            self._demo_performance()
            
            # 8. Integration Demo
            self._demo_integration_workflow()
            
            print("\n" + "=" * 80)
            print("DEMONSTRATION COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")
            raise
    
    def _demo_analytics(self):
        """Demonstrate analytics capabilities."""
        print("\n📊 ANALYTICS DEMONSTRATION")
        print("-" * 40)
        
        # Get analytics for demo vendor
        analytics = self.service.get_analytics(
            vendor_id="demo_vendor_001",
            time_range="30d",
            metrics=["total_records", "data_quality", "compliance"]
        )
        
        print(f"📈 Analytics Results:")
        print(f"   • Total Records: {analytics.total_records:,}")
        print(f"   • Unique Vendors: {analytics.unique_vendors}")
        print(f"   • Data Quality Score: {analytics.data_quality_score:.2%}")
        print(f"   • Compliance Score: {analytics.compliance_score:.2%}")
        print(f"   • Last Updated: {analytics.last_updated}")
        
        # Show trends
        if analytics.trends.get("data_growth"):
            print(f"   • Data Growth Trend: {len(analytics.trends['data_growth'])} data points")
        
        # Show predictions
        if analytics.predictions.get("data_growth_forecast"):
            forecast = analytics.predictions["data_growth_forecast"]
            print(f"   • Growth Forecast: {len(forecast)} days predicted")
            print(f"   • Quality Prediction: {analytics.predictions.get('quality_prediction', 0):.2%}")
            print(f"   • Compliance Risk: {analytics.predictions.get('compliance_risk', 'unknown')}")
        
        print("✅ Analytics demonstration completed")
    
    def _demo_data_masking(self):
        """Demonstrate data masking capabilities."""
        print("\n🔒 DATA MASKING DEMONSTRATION")
        print("-" * 40)
        
        print("Original Data (sensitive fields):")
        sensitive_fields = ["email", "phone", "ssn", "credit_card", "address"]
        for field in sensitive_fields:
            if field in self.demo_data:
                print(f"   {field}: {self.demo_data[field]}")
        
        # Test partial masking
        print("\n📝 Partial Masking Results:")
        partial_masked = self.service.mask_sensitive_data(
            self.demo_data,
            masking_level=DataMaskingLevel.PARTIAL
        )
        
        for field in sensitive_fields:
            if field in partial_masked:
                print(f"   {field}: {partial_masked[field]}")
        
        # Test full masking
        print("\n🔐 Full Masking Results:")
        full_masked = self.service.mask_sensitive_data(
            self.demo_data,
            masking_level=DataMaskingLevel.FULL
        )
        
        for field in sensitive_fields:
            if field in full_masked:
                print(f"   {field}: {full_masked[field]}")
        
        # Test custom masking
        print("\n🎨 Custom Masking Results:")
        custom_rules = {
            "email": self.service.masking_rules["email"],
            "phone": self.service.masking_rules["phone"]
        }
        custom_rules["email"].replacement_char = "#"
        custom_rules["phone"].replacement_char = "X"
        
        custom_masked = self.service.mask_sensitive_data(
            self.demo_data,
            masking_level=DataMaskingLevel.CUSTOM,
            custom_rules=custom_rules
        )
        
        for field in ["email", "phone"]:
            if field in custom_masked:
                print(f"   {field}: {custom_masked[field]}")
        
        print("✅ Data masking demonstration completed")
    
    def _demo_encryption(self):
        """Demonstrate encryption capabilities."""
        print("\n🔐 ENCRYPTION DEMONSTRATION")
        print("-" * 40)
        
        print("Original Sensitive Data:")
        sensitive_fields = ["email", "phone", "ssn", "credit_card"]
        for field in sensitive_fields:
            if field in self.demo_data:
                print(f"   {field}: {self.demo_data[field]}")
        
        # Encrypt data
        print("\n🔒 Encrypted Data:")
        encrypted_data = self.service.encrypt_sensitive_data(self.demo_data)
        
        for field in sensitive_fields:
            if field in encrypted_data:
                print(f"   {field}: {encrypted_data[field][:20]}...")
        
        # Decrypt data
        print("\n🔓 Decrypted Data:")
        decrypted_data = self.service.decrypt_sensitive_data(encrypted_data)
        
        for field in sensitive_fields:
            if field in decrypted_data:
                print(f"   {field}: {decrypted_data[field]}")
        
        # Verify decryption
        print("\n✅ Verification:")
        for field in sensitive_fields:
            if field in self.demo_data and field in decrypted_data:
                is_correct = self.demo_data[field] == decrypted_data[field]
                print(f"   {field}: {'✅' if is_correct else '❌'}")
        
        print("✅ Encryption demonstration completed")
    
    def _demo_compliance(self):
        """Demonstrate compliance checking capabilities."""
        print("\n📋 COMPLIANCE DEMONSTRATION")
        print("-" * 40)
        
        compliance_types = [
            ComplianceType.GDPR,
            ComplianceType.HIPAA,
            ComplianceType.CCPA,
            ComplianceType.SOX
        ]
        
        for compliance_type in compliance_types:
            print(f"\n🔍 {compliance_type.value.upper()} Compliance Check:")
            
            results = self.service.check_compliance(
                self.demo_data,
                compliance_type
            )
            
            print(f"   Status: {'✅ Compliant' if results['compliant'] else '❌ Non-compliant'}")
            
            if results['errors']:
                print(f"   Errors: {len(results['errors'])}")
                for error in results['errors'][:2]:  # Show first 2 errors
                    print(f"     • {error}")
            
            if results['warnings']:
                print(f"   Warnings: {len(results['warnings'])}")
                for warning in results['warnings'][:2]:  # Show first 2 warnings
                    print(f"     • {warning}")
            
            if results['recommendations']:
                print(f"   Recommendations: {len(results['recommendations'])}")
                for rec in results['recommendations'][:2]:  # Show first 2 recommendations
                    print(f"     • {rec}")
        
        print("✅ Compliance demonstration completed")
    
    def _demo_audit_logging(self):
        """Demonstrate audit logging capabilities."""
        print("\n📝 AUDIT LOGGING DEMONSTRATION")
        print("-" * 40)
        
        # Generate some audit events
        events = [
            ("analytics_access", {"vendor_id": "demo_vendor_001", "time_range": "30d"}),
            ("data_masking", {"fields_masked": ["email", "phone"], "level": "partial"}),
            ("data_encryption", {"fields_encrypted": ["ssn", "credit_card"]}),
            ("compliance_check", {"compliance_type": "gdpr", "compliant": True}),
            ("data_export", {"format": "json", "size_bytes": 2048})
        ]
        
        print("📊 Generating audit events:")
        for event_type, event_data in events:
            self.service._log_audit_event(event_type, event_data)
            print(f"   • {event_type}: {event_data}")
        
        # Get audit log
        print("\n📋 Audit Log Entries:")
        audit_entries = self.service.get_audit_log()
        
        for entry in audit_entries[-5:]:  # Show last 5 entries
            print(f"   • {entry['timestamp']} - {entry['event_type']}")
            print(f"     Data: {entry['event_data']}")
        
        # Test filtering
        print("\n🔍 Filtered Audit Log (analytics_access events):")
        filtered_entries = self.service.get_audit_log(event_type="analytics_access")
        print(f"   Found {len(filtered_entries)} analytics access events")
        
        print("✅ Audit logging demonstration completed")
    
    def _demo_data_export(self):
        """Demonstrate data export capabilities."""
        print("\n📤 DATA EXPORT DEMONSTRATION")
        print("-" * 40)
        
        export_formats = ["json", "csv", "xml", "yaml"]
        
        for format_type in export_formats:
            print(f"\n📄 {format_type.upper()} Export:")
            
            try:
                exported_data = self.service.export_data(
                    self.demo_data,
                    export_format=format_type,
                    include_analytics=True,
                    mask_sensitive=True
                )
                
                print(f"   Size: {len(exported_data)} characters")
                print(f"   Preview: {exported_data[:100]}...")
                
            except Exception as e:
                print(f"   ❌ Export failed: {e}")
        
        print("✅ Data export demonstration completed")
    
    def _demo_performance(self):
        """Demonstrate performance capabilities."""
        print("\n⚡ PERFORMANCE DEMONSTRATION")
        print("-" * 40)
        
        # Get performance metrics
        metrics = self.service.get_performance_metrics()
        
        print("📊 Performance Metrics:")
        print(f"   • Analytics Cache Size: {metrics['analytics_cache_size']}")
        print(f"   • Masking Rules Count: {metrics['masking_rules_count']}")
        print(f"   • Compliance Configs Count: {metrics['compliance_configs_count']}")
        print(f"   • Audit Log Entries: {metrics['audit_log_entries']}")
        print(f"   • Encryption Enabled: {'✅' if metrics['encryption_enabled'] else '❌'}")
        print(f"   • Service Uptime: {metrics['service_uptime']:.2f} seconds")
        
        # Performance benchmark
        print("\n🏃 Performance Benchmark:")
        
        # Analytics performance
        start_time = time.time()
        for i in range(10):
            self.service.get_analytics(vendor_id=f"benchmark_vendor_{i}")
        analytics_time = time.time() - start_time
        print(f"   • Analytics (10 calls): {analytics_time:.3f}s ({analytics_time/10:.3f}s per call)")
        
        # Masking performance
        start_time = time.time()
        for i in range(100):
            self.service.mask_sensitive_data(self.demo_data)
        masking_time = time.time() - start_time
        print(f"   • Data Masking (100 calls): {masking_time:.3f}s ({masking_time/100:.3f}s per call)")
        
        # Encryption performance
        start_time = time.time()
        for i in range(50):
            self.service.encrypt_sensitive_data(self.demo_data)
        encryption_time = time.time() - start_time
        print(f"   • Encryption (50 calls): {encryption_time:.3f}s ({encryption_time/50:.3f}s per call)")
        
        print("✅ Performance demonstration completed")
    
    def _demo_integration_workflow(self):
        """Demonstrate complete integration workflow."""
        print("\n🔄 INTEGRATION WORKFLOW DEMONSTRATION")
        print("-" * 40)
        
        print("🔄 Simulating complete vendor data processing workflow:")
        
        # Step 1: Get analytics
        print("\n1️⃣ Getting vendor analytics...")
        analytics = self.service.get_analytics(vendor_id="workflow_vendor")
        print(f"   ✅ Analytics retrieved: {analytics.total_records} records")
        
        # Step 2: Mask sensitive data
        print("\n2️⃣ Masking sensitive data...")
        masked_data = self.service.mask_sensitive_data(
            self.demo_data,
            masking_level=DataMaskingLevel.PARTIAL
        )
        print(f"   ✅ Data masked: {len(masked_data)} fields processed")
        
        # Step 3: Check compliance
        print("\n3️⃣ Checking compliance...")
        compliance_results = self.service.check_compliance(
            self.demo_data,
            ComplianceType.GDPR
        )
        print(f"   ✅ Compliance checked: {'Compliant' if compliance_results['compliant'] else 'Non-compliant'}")
        
        # Step 4: Export data
        print("\n4️⃣ Exporting data...")
        exported_data = self.service.export_data(
            masked_data,
            export_format="json",
            include_analytics=True,
            mask_sensitive=False  # Already masked
        )
        print(f"   ✅ Data exported: {len(exported_data)} characters")
        
        # Step 5: Get audit log
        print("\n5️⃣ Retrieving audit log...")
        audit_entries = self.service.get_audit_log()
        recent_entries = [e for e in audit_entries if "workflow" in str(e.get('event_data', ''))]
        print(f"   ✅ Audit log retrieved: {len(recent_entries)} workflow events")
        
        print("\n🎉 Integration workflow completed successfully!")
        print("✅ Integration demonstration completed")


def run_demo():
    """Run the comprehensive demonstration."""
    try:
        demo = DataVendorAPIExpansionDemo()
        demo.run_comprehensive_demo()
        
        print("\n" + "=" * 80)
        print("DEMONSTRATION SUMMARY")
        print("=" * 80)
        print("✅ Analytics Engine: Real-time data processing and insights")
        print("✅ Data Masking: Sensitive data protection with multiple levels")
        print("✅ Encryption: AES-256 encryption for data at rest and in transit")
        print("✅ Compliance: GDPR, HIPAA, CCPA, and SOX compliance checking")
        print("✅ Audit Logging: Comprehensive activity tracking")
        print("✅ Data Export: Multiple format support (JSON, CSV, XML, YAML)")
        print("✅ Performance: Optimized for high-throughput operations")
        print("✅ Integration: Seamless workflow integration")
        
        print("\n🚀 Data Vendor API Expansion is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    run_demo() 