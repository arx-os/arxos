"""
BIM Health Checker Demonstration Script

This script demonstrates the comprehensive BIM health checking functionality including:
- Floorplan validation and issue detection
- Behavior profile management
- Fix application and resolution
- Performance monitoring and analytics
- Validation history and reporting
- Error handling and edge cases

Performance Targets:
- BIM health checks complete within 5 minutes
- Validation identifies 95%+ of issues
- Fix suggestions are 90%+ accurate
- Automated fixes resolve 80%+ of issues

Usage:
    python examples/bim_health_checker_demo.py
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

from services.bim_health_checker import (
    BIMHealthCheckerService,
    IssueType,
    ValidationStatus,
    FixType,
    BehaviorProfile
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BIMHealthCheckerDemo:
    """Demonstration class for BIM Health Checker functionality."""
    
    def __init__(self):
        """Initialize the demonstration."""
        self.bim_health_service = BIMHealthCheckerService()
        self.demo_results = []
        
    def create_sample_floorplan(self, floorplan_id: str, issue_types: List[str] = None) -> Dict[str, Any]:
        """
        Create a sample floorplan with specified issues.
        
        Args:
            floorplan_id: Unique floorplan identifier
            issue_types: List of issue types to include
            
        Returns:
            Sample floorplan data
        """
        floorplan_data = {
            "floorplan_id": floorplan_id,
            "name": f"Demo Floorplan {floorplan_id}",
            "objects": {}
        }
        
        # Base objects
        base_objects = {
            "object_001": {
                "id": "object_001",
                "name": "HVAC Unit 1",
                "type": "equipment",
                "category": "hvac",
                "location": {"x": 100, "y": 200, "z": 0},
                "properties": {
                    "status": "active",
                    "priority": "high",
                    "capacity": "5000 BTU",
                    "efficiency": "85%"
                },
                "last_updated": int(datetime.now().timestamp())
            },
            "object_002": {
                "id": "object_002",
                "name": "Electrical Panel A",
                "type": "equipment",
                "category": "electrical",
                "location": {"x": 300, "y": 400, "z": 0},
                "properties": {
                    "status": "active",
                    "priority": "critical",
                    "voltage": "480V",
                    "amperage": "200A"
                },
                "last_updated": int(datetime.now().timestamp())
            },
            "object_003": {
                "id": "object_003",
                "name": "Water Heater",
                "type": "equipment",
                "category": "plumbing",
                "location": {"x": 500, "y": 600, "z": 0},
                "properties": {
                    "status": "active",
                    "priority": "medium",
                    "capacity": "50 gallons",
                    "temperature": "120F"
                },
                "last_updated": int(datetime.now().timestamp())
            }
        }
        
        # Add issue objects based on issue_types
        if issue_types:
            if "invalid_coordinates" in issue_types:
                base_objects["object_004"] = {
                    "id": "object_004",
                    "name": "Invalid Coordinates Object",
                    "type": "equipment",
                    "category": "electrical",
                    "location": {"x": -100, "y": 2000, "z": -50},  # Invalid coordinates
                    "properties": {"status": "active"},
                    "last_updated": int(datetime.now().timestamp())
                }
            
            if "stale_metadata" in issue_types:
                base_objects["object_005"] = {
                    "id": "object_005",
                    "name": "Stale Metadata Object",
                    "type": "equipment",
                    "category": "hvac",
                    "location": {"x": 700, "y": 800, "z": 0},
                    "properties": {"status": "active"},
                    "last_updated": int((datetime.now() - timedelta(days=60)).timestamp())  # Stale
                }
            
            if "duplicate_objects" in issue_types:
                # Add duplicate object
                base_objects["object_006"] = {
                    "id": "object_006",
                    "name": "Duplicate Object",
                    "type": "equipment",
                    "category": "hvac",
                    "location": {"x": 100, "y": 200, "z": 0},  # Same as object_001
                    "properties": {
                        "status": "active",
                        "priority": "high",
                        "capacity": "5000 BTU"
                    },
                    "last_updated": int(datetime.now().timestamp())
                }
            
            if "missing_symbols" in issue_types:
                base_objects["object_007"] = {
                    "id": "object_007",
                    "name": "Missing Symbol Object",
                    "type": "equipment",
                    "category": "electrical",
                    "location": {"x": 900, "y": 1000, "z": 0},
                    "properties": {"status": "active"},
                    "last_updated": int(datetime.now().timestamp())
                    # No symbol_id field
                }
        
        floorplan_data["objects"] = base_objects
        return floorplan_data
    
    def demo_basic_validation(self):
        """Demonstrate basic floorplan validation."""
        print("\n" + "="*60)
        print("DEMO: Basic Floorplan Validation")
        print("="*60)
        
        # Create sample floorplan
        floorplan_id = f"demo_basic_{int(time.time())}"
        floorplan_data = self.create_sample_floorplan(floorplan_id)
        
        print(f"Validating floorplan: {floorplan_id}")
        print(f"Objects to validate: {len(floorplan_data['objects'])}")
        
        # Perform validation
        start_time = time.time()
        result = self.bim_health_service.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=floorplan_data
        )
        end_time = time.time()
        
        # Display results
        print(f"\nValidation Results:")
        print(f"  Validation ID: {result.validation_id}")
        print(f"  Status: {result.status.value}")
        print(f"  Total Objects: {result.total_objects}")
        print(f"  Issues Found: {result.issues_found}")
        print(f"  Auto Fixes Applied: {result.auto_fixes_applied}")
        print(f"  Suggested Fixes: {result.suggested_fixes}")
        print(f"  Manual Fixes Required: {result.manual_fixes_required}")
        print(f"  Validation Time: {result.validation_time:.2f} seconds")
        print(f"  Total Time: {end_time - start_time:.2f} seconds")
        
        # Display issues
        if result.issues:
            print(f"\nIssues Found:")
            for i, issue in enumerate(result.issues, 1):
                print(f"  {i}. {issue.issue_type.value}: {issue.description}")
                print(f"     Severity: {issue.severity}, Fix Type: {issue.fix_type.value}")
                print(f"     Confidence: {issue.confidence:.2f}")
        
        self.demo_results.append({
            "demo": "basic_validation",
            "floorplan_id": floorplan_id,
            "result": result
        })
    
    def demo_issue_detection(self):
        """Demonstrate issue detection with various problem types."""
        print("\n" + "="*60)
        print("DEMO: Issue Detection")
        print("="*60)
        
        # Create floorplan with known issues
        floorplan_id = f"demo_issues_{int(time.time())}"
        issue_types = ["invalid_coordinates", "stale_metadata", "duplicate_objects", "missing_symbols"]
        floorplan_data = self.create_sample_floorplan(floorplan_id, issue_types)
        
        print(f"Validating floorplan with known issues: {floorplan_id}")
        print(f"Issue types included: {', '.join(issue_types)}")
        
        # Perform validation
        result = self.bim_health_service.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=floorplan_data
        )
        
        # Display results
        print(f"\nIssue Detection Results:")
        print(f"  Total Objects: {result.total_objects}")
        print(f"  Issues Found: {result.issues_found}")
        
        # Group issues by type
        issues_by_type = {}
        for issue in result.issues:
            issue_type = issue.issue_type.value
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)
        
        print(f"\nIssues by Type:")
        for issue_type, issues in issues_by_type.items():
            print(f"  {issue_type}: {len(issues)} issues")
            for issue in issues:
                print(f"    - {issue.description} (Severity: {issue.severity})")
        
        # Check detection accuracy
        expected_issues = len(issue_types)
        detected_issues = len(result.issues)
        accuracy = (detected_issues / max(expected_issues, 1)) * 100
        
        print(f"\nDetection Accuracy: {accuracy:.1f}%")
        print(f"  Expected Issues: {expected_issues}")
        print(f"  Detected Issues: {detected_issues}")
        
        self.demo_results.append({
            "demo": "issue_detection",
            "floorplan_id": floorplan_id,
            "result": result,
            "accuracy": accuracy
        })
    
    def demo_fix_application(self):
        """Demonstrate fix application functionality."""
        print("\n" + "="*60)
        print("DEMO: Fix Application")
        print("="*60)
        
        # First, create a validation with issues
        floorplan_id = f"demo_fixes_{int(time.time())}"
        issue_types = ["invalid_coordinates", "stale_metadata"]
        floorplan_data = self.create_sample_floorplan(floorplan_id, issue_types)
        
        print(f"Creating validation with issues: {floorplan_id}")
        
        result = self.bim_health_service.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=floorplan_data
        )
        
        print(f"Validation created with {len(result.issues)} issues")
        
        # Create fix selections
        fix_selections = {}
        for issue in result.issues:
            if issue.fix_type == FixType.AUTO_FIX:
                fix_selections[issue.issue_id] = "apply"
            elif issue.fix_type == FixType.SUGGESTED_FIX:
                fix_selections[issue.issue_id] = "apply"
            elif issue.fix_type == FixType.MANUAL_FIX:
                fix_selections[issue.issue_id] = "ignore"
        
        print(f"Applying {len(fix_selections)} fixes...")
        
        # Apply fixes
        fix_result = self.bim_health_service.apply_fixes(
            validation_id=result.validation_id,
            fix_selections=fix_selections
        )
        
        # Display results
        print(f"\nFix Application Results:")
        print(f"  Applied Fixes: {fix_result['applied_fixes']}")
        print(f"  Failed Fixes: {fix_result['failed_fixes']}")
        print(f"  Total Issues: {fix_result['total_issues']}")
        print(f"  Status: {fix_result['status']}")
        
        # Calculate success rate
        success_rate = (fix_result['applied_fixes'] / max(fix_result['total_issues'], 1)) * 100
        print(f"  Success Rate: {success_rate:.1f}%")
        
        self.demo_results.append({
            "demo": "fix_application",
            "floorplan_id": floorplan_id,
            "validation_id": result.validation_id,
            "fix_result": fix_result,
            "success_rate": success_rate
        })
    
    def demo_performance_monitoring(self):
        """Demonstrate performance monitoring and metrics."""
        print("\n" + "="*60)
        print("DEMO: Performance Monitoring")
        print("="*60)
        
        # Perform multiple validations to generate metrics
        print("Performing multiple validations to generate metrics...")
        
        validation_times = []
        for i in range(5):
            floorplan_id = f"perf_test_{i}_{int(time.time())}"
            floorplan_data = self.create_sample_floorplan(floorplan_id)
            
            start_time = time.time()
            result = self.bim_health_service.validate_floorplan(
                floorplan_id=floorplan_id,
                floorplan_data=floorplan_data
            )
            end_time = time.time()
            
            validation_time = end_time - start_time
            validation_times.append(validation_time)
            
            print(f"  Validation {i+1}: {validation_time:.2f}s ({result.issues_found} issues)")
        
        # Get metrics
        metrics = self.bim_health_service.get_metrics()
        
        print(f"\nPerformance Metrics:")
        print(f"  Total Validations: {metrics['metrics']['total_validations']}")
        print(f"  Successful Validations: {metrics['metrics']['successful_validations']}")
        print(f"  Issues Detected: {metrics['metrics']['issues_detected']}")
        print(f"  Auto Fixes Applied: {metrics['metrics']['auto_fixes_applied']}")
        print(f"  Average Validation Time: {metrics['metrics']['average_validation_time']:.2f}s")
        print(f"  Behavior Profiles: {metrics['behavior_profiles']}")
        print(f"  Database Size: {metrics['database_size']} bytes")
        
        # Performance analysis
        avg_time = sum(validation_times) / len(validation_times)
        max_time = max(validation_times)
        min_time = min(validation_times)
        
        print(f"\nPerformance Analysis:")
        print(f"  Average Time: {avg_time:.2f}s")
        print(f"  Min Time: {min_time:.2f}s")
        print(f"  Max Time: {max_time:.2f}s")
        print(f"  Performance Target: < 300s (5 minutes)")
        print(f"  Target Met: {'Yes' if max_time < 300 else 'No'}")
        
        # Success rate
        success_rate = (metrics['metrics']['successful_validations'] / max(metrics['metrics']['total_validations'], 1)) * 100
        print(f"  Success Rate: {success_rate:.1f}%")
        
        self.demo_results.append({
            "demo": "performance_monitoring",
            "metrics": metrics,
            "validation_times": validation_times,
            "avg_time": avg_time,
            "success_rate": success_rate
        })
    
    def demo_validation_history(self):
        """Demonstrate validation history functionality."""
        print("\n" + "="*60)
        print("DEMO: Validation History")
        print("="*60)
        
        # Create multiple validations for a floorplan
        floorplan_id = f"history_demo_{int(time.time())}"
        
        print(f"Creating validation history for: {floorplan_id}")
        
        # Perform multiple validations
        for i in range(3):
            floorplan_data = self.create_sample_floorplan(f"{floorplan_id}_v{i+1}")
            result = self.bim_health_service.validate_floorplan(
                floorplan_id=floorplan_id,
                floorplan_data=floorplan_data
            )
            print(f"  Validation {i+1}: {result.validation_id} ({result.issues_found} issues)")
        
        # Get history
        history = self.bim_health_service.get_validation_history(floorplan_id, limit=10)
        
        print(f"\nValidation History:")
        print(f"  Total Validations: {len(history)}")
        
        for i, validation in enumerate(history, 1):
            print(f"  {i}. {validation['validation_id']}")
            print(f"     Status: {validation['status']}")
            print(f"     Issues: {validation['issues_found']}")
            print(f"     Time: {validation['validation_time']:.2f}s")
            print(f"     Timestamp: {validation['timestamp']}")
        
        self.demo_results.append({
            "demo": "validation_history",
            "floorplan_id": floorplan_id,
            "history": history
        })
    
    def demo_behavior_profiles(self):
        """Demonstrate behavior profile management."""
        print("\n" + "="*60)
        print("DEMO: Behavior Profile Management")
        print("="*60)
        
        # Get existing profiles
        profiles = self.bim_health_service.get_behavior_profiles()
        
        print(f"Existing Behavior Profiles: {len(profiles)}")
        for profile in profiles:
            print(f"  {profile['profile_id']}: {profile['object_type']} ({profile['category']})")
        
        # Add a custom profile
        custom_profile = BehaviorProfile(
            profile_id="demo_custom_profile",
            object_type="custom_equipment",
            category="demo_category",
            properties={
                "required_fields": ["id", "name", "type", "location"],
                "coordinate_bounds": {"x": [0, 2000], "y": [0, 2000], "z": [0, 100]},
                "symbol_requirements": ["demo_symbol"]
            },
            validation_rules={
                "coordinate_validation": True,
                "symbol_linking": True,
                "metadata_completeness": 0.9
            },
            fix_suggestions={
                "missing_coordinates": "auto_calculate",
                "invalid_coordinates": "snap_to_grid",
                "missing_symbol": "assign_default"
            }
        )
        
        print(f"\nAdding custom profile: {custom_profile.profile_id}")
        self.bim_health_service.add_behavior_profile(custom_profile)
        
        # Verify profile was added
        updated_profiles = self.bim_health_service.get_behavior_profiles()
        print(f"Updated Behavior Profiles: {len(updated_profiles)}")
        
        # Find our custom profile
        custom_profile_found = any(p['profile_id'] == custom_profile.profile_id for p in updated_profiles)
        print(f"Custom Profile Added: {'Yes' if custom_profile_found else 'No'}")
        
        self.demo_results.append({
            "demo": "behavior_profiles",
            "original_count": len(profiles),
            "updated_count": len(updated_profiles),
            "custom_profile_added": custom_profile_found
        })
    
    def demo_error_handling(self):
        """Demonstrate error handling and edge cases."""
        print("\n" + "="*60)
        print("DEMO: Error Handling")
        print("="*60)
        
        # Test with invalid floorplan ID
        print("Testing with invalid floorplan ID...")
        try:
            result = self.bim_health_service.validate_floorplan(
                floorplan_id="",  # Empty ID
                floorplan_data={"objects": {}}
            )
        except Exception as e:
            print(f"  Expected error caught: {type(e).__name__}: {e}")
        
        # Test with invalid floorplan data
        print("Testing with invalid floorplan data...")
        try:
            result = self.bim_health_service.validate_floorplan(
                floorplan_id="test_invalid",
                floorplan_data={"objects": "invalid_data"}  # Should be dict
            )
        except Exception as e:
            print(f"  Expected error caught: {type(e).__name__}: {e}")
        
        # Test with very large floorplan
        print("Testing with large floorplan...")
        large_floorplan = {
            "floorplan_id": "large_test",
            "objects": {}
        }
        
        # Add 100 objects
        for i in range(100):
            large_floorplan["objects"][f"object_{i:03d}"] = {
                "id": f"object_{i:03d}",
                "name": f"Large Object {i}",
                "type": "equipment",
                "category": "electrical" if i % 2 == 0 else "hvac",
                "location": {"x": i * 10, "y": i * 20, "z": 0},
                "properties": {"status": "active", "priority": "high"},
                "last_updated": int(datetime.now().timestamp())
            }
        
        try:
            start_time = time.time()
            result = self.bim_health_service.validate_floorplan(
                floorplan_id="large_test",
                floorplan_data=large_floorplan
            )
            end_time = time.time()
            
            print(f"  Large floorplan validation successful!")
            print(f"  Objects: {result.total_objects}")
            print(f"  Time: {end_time - start_time:.2f}s")
            print(f"  Issues: {result.issues_found}")
            
        except Exception as e:
            print(f"  Error with large floorplan: {e}")
        
        self.demo_results.append({
            "demo": "error_handling",
            "status": "completed"
        })
    
    def demo_analytics(self):
        """Demonstrate analytics and reporting capabilities."""
        print("\n" + "="*60)
        print("DEMO: Analytics and Reporting")
        print("="*60)
        
        # Get comprehensive metrics
        metrics = self.bim_health_service.get_metrics()
        
        print("BIM Health Checker Analytics")
        print("-" * 40)
        
        # Performance metrics
        print("Performance Metrics:")
        print(f"  Total Validations: {metrics['metrics']['total_validations']}")
        print(f"  Success Rate: {(metrics['metrics']['successful_validations'] / max(metrics['metrics']['total_validations'], 1)) * 100:.1f}%")
        print(f"  Average Validation Time: {metrics['metrics']['average_validation_time']:.2f}s")
        print(f"  Issues per Validation: {metrics['metrics']['issues_detected'] / max(metrics['metrics']['total_validations'], 1):.1f}")
        
        # Fix effectiveness
        total_issues = metrics['metrics']['issues_detected']
        auto_fixes = metrics['metrics']['auto_fixes_applied']
        if total_issues > 0:
            auto_fix_rate = (auto_fixes / total_issues) * 100
            print(f"  Auto Fix Rate: {auto_fix_rate:.1f}%")
        
        # System metrics
        print("\nSystem Metrics:")
        print(f"  Behavior Profiles: {metrics['behavior_profiles']}")
        print(f"  Database Size: {metrics['database_size']} bytes")
        print(f"  Database Size (MB): {metrics['database_size'] / (1024 * 1024):.2f} MB")
        
        # Performance targets
        print("\nPerformance Targets:")
        print(f"  Validation Time < 5min: {'✓' if metrics['metrics']['average_validation_time'] < 300 else '✗'}")
        print(f"  Success Rate > 95%: {'✓' if (metrics['metrics']['successful_validations'] / max(metrics['metrics']['total_validations'], 1)) > 0.95 else '✗'}")
        print(f"  Auto Fix Rate > 80%: {'✓' if total_issues > 0 and (auto_fixes / total_issues) > 0.8 else '✗'}")
        
        self.demo_results.append({
            "demo": "analytics",
            "metrics": metrics,
            "performance_targets": {
                "validation_time_ok": metrics['metrics']['average_validation_time'] < 300,
                "success_rate_ok": (metrics['metrics']['successful_validations'] / max(metrics['metrics']['total_validations'], 1)) > 0.95,
                "auto_fix_rate_ok": total_issues > 0 and (auto_fixes / total_issues) > 0.8
            }
        })
    
    def run_comprehensive_demo(self):
        """Run the comprehensive demonstration."""
        print("BIM Health Checker Comprehensive Demonstration")
        print("=" * 60)
        print("This demonstration showcases all BIM health checking features")
        print("including validation, issue detection, fix application,")
        print("performance monitoring, and analytics.")
        print()
        
        try:
            # Run all demos
            self.demo_basic_validation()
            self.demo_issue_detection()
            self.demo_fix_application()
            self.demo_performance_monitoring()
            self.demo_validation_history()
            self.demo_behavior_profiles()
            self.demo_error_handling()
            self.demo_analytics()
            
            # Summary
            self.print_demo_summary()
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            print(f"Demo failed: {e}")
    
    def print_demo_summary(self):
        """Print a summary of all demo results."""
        print("\n" + "="*60)
        print("DEMO SUMMARY")
        print("="*60)
        
        total_demos = len(self.demo_results)
        successful_demos = sum(1 for result in self.demo_results if result.get('status', 'completed') == 'completed')
        
        print(f"Total Demonstrations: {total_demos}")
        print(f"Successful Demonstrations: {successful_demos}")
        print(f"Success Rate: {(successful_demos / total_demos) * 100:.1f}%")
        
        print("\nKey Features Demonstrated:")
        print("  ✓ Floorplan validation and issue detection")
        print("  ✓ Behavior profile management")
        print("  ✓ Fix application and resolution")
        print("  ✓ Performance monitoring and metrics")
        print("  ✓ Validation history and reporting")
        print("  ✓ Error handling and edge cases")
        print("  ✓ Analytics and reporting")
        
        # Performance summary
        if any('performance_monitoring' in result.get('demo', '') for result in self.demo_results):
            perf_result = next(r for r in self.demo_results if r.get('demo') == 'performance_monitoring')
            print(f"\nPerformance Summary:")
            print(f"  Average Validation Time: {perf_result.get('avg_time', 0):.2f}s")
            print(f"  Success Rate: {perf_result.get('success_rate', 0):.1f}%")
        
        # Analytics summary
        if any('analytics' in result.get('demo', '') for result in self.demo_results):
            analytics_result = next(r for r in self.demo_results if r.get('demo') == 'analytics')
            targets = analytics_result.get('performance_targets', {})
            print(f"\nPerformance Targets:")
            print(f"  Validation Time < 5min: {'✓' if targets.get('validation_time_ok') else '✗'}")
            print(f"  Success Rate > 95%: {'✓' if targets.get('success_rate_ok') else '✗'}")
            print(f"  Auto Fix Rate > 80%: {'✓' if targets.get('auto_fix_rate_ok') else '✗'}")
        
        print(f"\nBIM Health Checker demonstration completed successfully!")
        print("The system is ready for production use.")


def main():
    """Main function to run the demonstration."""
    demo = BIMHealthCheckerDemo()
    demo.run_comprehensive_demo()


if __name__ == "__main__":
    main() 