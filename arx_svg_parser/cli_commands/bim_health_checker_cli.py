"""
BIM Health Checker CLI Commands

This module provides comprehensive command-line interface for BIM health checking
and validation operations including:
- Floorplan validation and issue detection
- Fix application and resolution
- Validation history and reporting
- Performance metrics and analytics
- Behavior profile management

Usage Examples:
    arx bim-health validate --floorplan-id floorplan_001 --floorplan-data data.json
    arx bim-health status --floorplan-id floorplan_001
    arx bim-health history --floorplan-id floorplan_001 --limit 10
    arx bim-health apply-fixes --validation-id val_123 --fixes fixes.json
    arx bim-health metrics
    arx bim-health profiles
"""

import click
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
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


@click.group()
def bim_health():
    """BIM Health Checker commands."""
    pass


@bim_health.command()
@click.option('--floorplan-id', required=True, help='Unique floorplan identifier')
@click.option('--floorplan-data', type=click.Path(exists=True), help='Path to floorplan data JSON file')
@click.option('--auto-apply-fixes', is_flag=True, help='Automatically apply safe fixes')
@click.option('--output', type=click.Path(), help='Output file for validation results')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def validate(floorplan_id: str, floorplan_data: Optional[str], auto_apply_fixes: bool,
             output: Optional[str], format: str, verbose: bool):
    """
    Validate a floorplan for BIM health issues.
    
    This command performs comprehensive BIM validation including:
    - Missing behavior profile detection
    - Invalid coordinate validation and correction
    - Unlinked symbol detection and linking
    - Stale object metadata identification
    - Context-aware fix suggestions
    
    Examples:
        arx bim-health validate --floorplan-id floorplan_001 --floorplan-data data.json
        arx bim-health validate --floorplan-id floorplan_002 --auto-apply-fixes --verbose
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize BIM health service
        bim_health_service = BIMHealthCheckerService()
        
        # Load floorplan data
        if floorplan_data:
            with open(floorplan_data, 'r') as f:
                floorplan_data_dict = json.load(f)
            logger.info(f"Loaded floorplan data from {floorplan_data}")
        else:
            # Create sample data for testing
            floorplan_data_dict = {
                "floorplan_id": floorplan_id,
                "name": f"Test Floorplan {floorplan_id}",
                "objects": {
                    "object_001": {
                        "id": "object_001",
                        "name": "Test Object 1",
                        "type": "equipment",
                        "category": "electrical",
                        "location": {"x": 100, "y": 200, "z": 0},
                        "properties": {"status": "active", "priority": "high"},
                        "last_updated": int(datetime.now().timestamp())
                    },
                    "object_002": {
                        "id": "object_002",
                        "name": "Test Object 2",
                        "type": "equipment",
                        "category": "hvac",
                        "location": {"x": 300, "y": 400, "z": 0},
                        "properties": {"status": "active", "priority": "medium"},
                        "last_updated": int(datetime.now().timestamp())
                    }
                }
            }
            logger.info("Using sample floorplan data for validation")
        
        # Validate request data
        if not floorplan_id:
            raise click.BadParameter("Floorplan ID is required")
        
        if not floorplan_data_dict:
            raise click.BadParameter("Floorplan data is required")
        
        # Perform validation
        logger.info(f"Starting BIM validation for floorplan {floorplan_id}")
        
        result = bim_health_service.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=floorplan_data_dict
        )
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump({
                    'validation_id': result.validation_id,
                    'floorplan_id': result.floorplan_id,
                    'status': result.status.value,
                    'total_objects': result.total_objects,
                    'issues_found': result.issues_found,
                    'auto_fixes_applied': result.auto_fixes_applied,
                    'suggested_fixes': result.suggested_fixes,
                    'manual_fixes_required': result.manual_fixes_required,
                    'validation_time': result.validation_time,
                    'timestamp': result.timestamp.isoformat(),
                    'summary': result.summary,
                    'issues': [
                        {
                            'issue_id': issue.issue_id,
                            'issue_type': issue.issue_type.value,
                            'object_id': issue.object_id,
                            'severity': issue.severity,
                            'description': issue.description,
                            'fix_type': issue.fix_type.value,
                            'confidence': issue.confidence
                        }
                        for issue in result.issues
                    ]
                }, f, indent=2, default=str)
            logger.info(f"Validation results saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps({
                'validation_id': result.validation_id,
                'floorplan_id': result.floorplan_id,
                'status': result.status.value,
                'total_objects': result.total_objects,
                'issues_found': result.issues_found,
                'auto_fixes_applied': result.auto_fixes_applied,
                'suggested_fixes': result.suggested_fixes,
                'manual_fixes_required': result.manual_fixes_required,
                'validation_time': result.validation_time,
                'summary': result.summary
            }, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("validation_id,floorplan_id,status,total_objects,issues_found,auto_fixes_applied,suggested_fixes,manual_fixes_required,validation_time")
            click.echo(f"{result.validation_id},{result.floorplan_id},{result.status.value},{result.total_objects},{result.auto_fixes_applied},{result.suggested_fixes},{result.manual_fixes_required},{result.validation_time}")
        else:
            # Table format
            click.echo(f"BIM Validation Results for {floorplan_id}")
            click.echo("=" * 50)
            click.echo(f"Validation ID: {result.validation_id}")
            click.echo(f"Status: {result.status.value}")
            click.echo(f"Total Objects: {result.total_objects}")
            click.echo(f"Issues Found: {result.issues_found}")
            click.echo(f"Auto Fixes Applied: {result.auto_fixes_applied}")
            click.echo(f"Suggested Fixes: {result.suggested_fixes}")
            click.echo(f"Manual Fixes Required: {result.manual_fixes_required}")
            click.echo(f"Validation Time: {result.validation_time:.2f} seconds")
            
            if result.issues:
                click.echo("\nIssues Found:")
                click.echo("-" * 30)
                for issue in result.issues:
                    click.echo(f"  {issue.issue_type.value}: {issue.description} (Severity: {issue.severity})")
        
        logger.info(f"BIM validation completed for {floorplan_id}: {result.issues_found} issues found")
        
    except Exception as e:
        logger.error(f"BIM validation failed for floorplan {floorplan_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@bim_health.command()
@click.option('--validation-id', required=True, help='Validation result identifier')
@click.option('--fixes', type=click.Path(exists=True), help='Path to fixes JSON file')
@click.option('--output', type=click.Path(), help='Output file for fix results')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
def apply_fixes(validation_id: str, fixes: Optional[str], output: Optional[str], format: str):
    """
    Apply selected fixes to a validation result.
    
    This command allows applying fixes to validation issues including:
    - Auto fixes (applied automatically during validation)
    - Suggested fixes (user-approved fixes)
    - Manual fixes (requiring user intervention)
    
    Examples:
        arx bim-health apply-fixes --validation-id val_123 --fixes fixes.json
        arx bim-health apply-fixes --validation-id val_456 --fixes fixes.json --output results.json
    """
    try:
        bim_health_service = BIMHealthCheckerService()
        
        # Load fix selections
        if fixes:
            with open(fixes, 'r') as f:
                fix_selections = json.load(f)
            logger.info(f"Loaded fix selections from {fixes}")
        else:
            click.echo("No fixes file provided. Please specify --fixes option.", err=True)
            sys.exit(1)
        
        # Validate request data
        if not validation_id:
            raise click.BadParameter("Validation ID is required")
        
        if not fix_selections:
            raise click.BadParameter("Fix selections are required")
        
        # Apply fixes
        logger.info(f"Applying fixes for validation {validation_id}")
        
        result = bim_health_service.apply_fixes(
            validation_id=validation_id,
            fix_selections=fix_selections
        )
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            logger.info(f"Fix application results saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps(result, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("validation_id,applied_fixes,failed_fixes,total_issues,status")
            click.echo(f"{result['validation_id']},{result['applied_fixes']},{result['failed_fixes']},{result['total_issues']},{result['status']}")
        else:
            # Table format
            click.echo(f"Fix Application Results for {validation_id}")
            click.echo("=" * 40)
            click.echo(f"Applied Fixes: {result['applied_fixes']}")
            click.echo(f"Failed Fixes: {result['failed_fixes']}")
            click.echo(f"Total Issues: {result['total_issues']}")
            click.echo(f"Status: {result['status']}")
        
        logger.info(f"Fix application completed for {validation_id}: {result['applied_fixes']} fixes applied")
        
    except ValueError as e:
        logger.error(f"Fix application failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fix application failed for {validation_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@bim_health.command()
@click.option('--floorplan-id', required=True, help='Floorplan identifier')
@click.option('--limit', default=50, type=int, help='Maximum number of results to return')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--output', type=click.Path(), help='Output file for history results')
def history(floorplan_id: str, limit: int, format: str, output: Optional[str]):
    """
    Get validation history for a floorplan.
    
    This command provides detailed history of BIM validations including:
    - Validation timestamps and status
    - Issue counts and fix statistics
    - Performance metrics and validation scores
    
    Examples:
        arx bim-health history --floorplan-id floorplan_001
        arx bim-health history --floorplan-id floorplan_002 --limit 10 --format json
    """
    try:
        bim_health_service = BIMHealthCheckerService()
        
        if limit < 1 or limit > 1000:
            raise click.BadParameter("Limit must be between 1 and 1000")
        
        logger.info(f"Getting validation history for floorplan {floorplan_id}")
        
        history = bim_health_service.get_validation_history(floorplan_id, limit)
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump({
                    'floorplan_id': floorplan_id,
                    'validations': history,
                    'total_validations': len(history)
                }, f, indent=2, default=str)
            logger.info(f"Validation history saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps({
                'floorplan_id': floorplan_id,
                'validations': history,
                'total_validations': len(history)
            }, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("validation_id,floorplan_id,status,total_objects,issues_found,validation_time,timestamp")
            for validation in history:
                click.echo(f"{validation['validation_id']},{validation['floorplan_id']},{validation['status']},{validation['total_objects']},{validation['issues_found']},{validation['validation_time']},{validation['timestamp']}")
        else:
            # Table format
            click.echo(f"Validation History for {floorplan_id}")
            click.echo("=" * 50)
            click.echo(f"Total Validations: {len(history)}")
            
            if history:
                click.echo("\nRecent Validations:")
                click.echo("-" * 30)
                for validation in history[:10]:  # Show last 10
                    click.echo(f"  {validation['validation_id']}: {validation['status']} ({validation['issues_found']} issues)")
            else:
                click.echo("No validation history found.")
        
    except Exception as e:
        logger.error(f"Failed to get validation history for {floorplan_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@bim_health.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--output', type=click.Path(), help='Output file for metrics')
def metrics(format: str, output: Optional[str]):
    """
    Get BIM health checker performance metrics.
    
    This command provides comprehensive performance metrics including:
    - Total validations and success rates
    - Issues detected and fix application statistics
    - Average validation times and system resource usage
    - Behavior profile statistics
    
    Examples:
        arx bim-health metrics
        arx bim-health metrics --format json --output metrics.json
    """
    try:
        bim_health_service = BIMHealthCheckerService()
        
        logger.info("Getting BIM health checker metrics")
        
        metrics_data = bim_health_service.get_metrics()
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            logger.info(f"Metrics saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps(metrics_data, indent=2, default=str))
        elif format == 'csv':
            # CSV output for metrics
            click.echo("metric,value")
            for key, value in metrics_data['metrics'].items():
                click.echo(f"{key},{value}")
            click.echo(f"behavior_profiles,{metrics_data['behavior_profiles']}")
            click.echo(f"database_size,{metrics_data['database_size']}")
        else:
            # Table format
            click.echo("BIM Health Checker Performance Metrics")
            click.echo("=" * 40)
            click.echo(f"Total Validations: {metrics_data['metrics']['total_validations']}")
            click.echo(f"Successful Validations: {metrics_data['metrics']['successful_validations']}")
            click.echo(f"Issues Detected: {metrics_data['metrics']['issues_detected']}")
            click.echo(f"Auto Fixes Applied: {metrics_data['metrics']['auto_fixes_applied']}")
            click.echo(f"Average Validation Time: {metrics_data['metrics']['average_validation_time']:.2f} seconds")
            click.echo(f"Behavior Profiles: {metrics_data['behavior_profiles']}")
            click.echo(f"Database Size: {metrics_data['database_size']} bytes")
            
            # Calculate success rate
            total_validations = metrics_data['metrics']['total_validations']
            successful_validations = metrics_data['metrics']['successful_validations']
            if total_validations > 0:
                success_rate = (successful_validations / total_validations) * 100
                click.echo(f"Success Rate: {success_rate:.1f}%")
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@bim_health.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--output', type=click.Path(), help='Output file for profiles')
def profiles(format: str, output: Optional[str]):
    """
    Get all behavior profiles.
    
    This command provides access to all behavior profiles used for
    BIM validation including validation rules and fix suggestions.
    
    Examples:
        arx bim-health profiles
        arx bim-health profiles --format json --output profiles.json
    """
    try:
        bim_health_service = BIMHealthCheckerService()
        
        logger.info("Getting behavior profiles")
        
        profiles = bim_health_service.get_behavior_profiles()
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(profiles, f, indent=2, default=str)
            logger.info(f"Behavior profiles saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps(profiles, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("profile_id,object_type,category")
            for profile in profiles:
                click.echo(f"{profile['profile_id']},{profile['object_type']},{profile['category']}")
        else:
            # Table format
            click.echo("Behavior Profiles")
            click.echo("=" * 30)
            click.echo(f"Total Profiles: {len(profiles)}")
            
            for profile in profiles:
                click.echo(f"\nProfile: {profile['profile_id']}")
                click.echo(f"  Object Type: {profile['object_type']}")
                click.echo(f"  Category: {profile['category']}")
                click.echo(f"  Validation Rules: {len(profile['validation_rules'])} rules")
                click.echo(f"  Fix Suggestions: {len(profile['fix_suggestions'])} suggestions")
        
    except Exception as e:
        logger.error(f"Failed to get behavior profiles: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@bim_health.command()
@click.option('--profile-id', required=True, help='Unique profile identifier')
@click.option('--object-type', required=True, help='Object type')
@click.option('--category', required=True, help='Object category')
@click.option('--properties', type=click.Path(exists=True), help='Path to properties JSON file')
@click.option('--validation-rules', type=click.Path(exists=True), help='Path to validation rules JSON file')
@click.option('--fix-suggestions', type=click.Path(exists=True), help='Path to fix suggestions JSON file')
@click.option('--output', type=click.Path(), help='Output file for profile')
def add_profile(profile_id: str, object_type: str, category: str, properties: Optional[str],
                validation_rules: Optional[str], fix_suggestions: Optional[str], output: Optional[str]):
    """
    Add a new behavior profile.
    
    This command allows adding custom behavior profiles for BIM validation
    including validation rules and fix suggestions.
    
    Examples:
        arx bim-health add-profile --profile-id custom_profile --object-type equipment --category custom
        arx bim-health add-profile --profile-id test_profile --object-type fixture --category plumbing --properties props.json
    """
    try:
        bim_health_service = BIMHealthCheckerService()
        
        # Load JSON files if provided
        properties_dict = {}
        if properties:
            with open(properties, 'r') as f:
                properties_dict = json.load(f)
        
        validation_rules_dict = {}
        if validation_rules:
            with open(validation_rules, 'r') as f:
                validation_rules_dict = json.load(f)
        
        fix_suggestions_dict = {}
        if fix_suggestions:
            with open(fix_suggestions, 'r') as f:
                fix_suggestions_dict = json.load(f)
        
        # Create behavior profile
        profile = BehaviorProfile(
            profile_id=profile_id,
            object_type=object_type,
            category=category,
            properties=properties_dict,
            validation_rules=validation_rules_dict,
            fix_suggestions=fix_suggestions_dict
        )
        
        # Add profile
        bim_health_service.add_behavior_profile(profile)
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump({
                    'profile_id': profile_id,
                    'object_type': object_type,
                    'category': category,
                    'properties': properties_dict,
                    'validation_rules': validation_rules_dict,
                    'fix_suggestions': fix_suggestions_dict
                }, f, indent=2, default=str)
            logger.info(f"Profile saved to {output}")
        
        # Display results
        click.echo(f"Behavior profile '{profile_id}' added successfully!")
        click.echo(f"  Object Type: {object_type}")
        click.echo(f"  Category: {category}")
        click.echo(f"  Properties: {len(properties_dict)} properties")
        click.echo(f"  Validation Rules: {len(validation_rules_dict)} rules")
        click.echo(f"  Fix Suggestions: {len(fix_suggestions_dict)} suggestions")
        
        logger.info(f"Behavior profile {profile_id} added successfully")
        
    except Exception as e:
        logger.error(f"Failed to add behavior profile {profile_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@bim_health.command()
@click.option('--floorplan-id', help='Floorplan identifier to test')
@click.option('--floorplan-data', type=click.Path(exists=True), help='Path to floorplan data file')
@click.option('--output', type=click.Path(), help='Output file for test results')
def test(floorplan_id: Optional[str], floorplan_data: Optional[str], output: Optional[str]):
    """
    Test BIM health checker functionality.
    
    This command provides a way to test BIM health checker functionality
    using sample data or provided files.
    
    Examples:
        arx bim-health test
        arx bim-health test --floorplan-id test_floorplan --floorplan-data data.json
    """
    try:
        bim_health_service = BIMHealthCheckerService()
        
        # Use provided floorplan ID or generate one
        test_floorplan_id = floorplan_id or f"test_floorplan_{int(datetime.now().timestamp())}"
        
        # Load floorplan data or create sample data
        if floorplan_data:
            with open(floorplan_data, 'r') as f:
                floorplan_data_dict = json.load(f)
            logger.info(f"Loaded floorplan data from {floorplan_data}")
        else:
            # Create sample data for testing
            floorplan_data_dict = {
                "floorplan_id": test_floorplan_id,
                "name": f"Test Floorplan {test_floorplan_id}",
                "objects": {
                    "object_001": {
                        "id": "object_001",
                        "name": "Test Object 1",
                        "type": "equipment",
                        "category": "electrical",
                        "location": {"x": 100, "y": 200, "z": 0},
                        "properties": {"status": "active", "priority": "high"},
                        "last_updated": int(datetime.now().timestamp())
                    },
                    "object_002": {
                        "id": "object_002",
                        "name": "Test Object 2",
                        "type": "equipment",
                        "category": "hvac",
                        "location": {"x": 300, "y": 400, "z": 0},
                        "properties": {"status": "active", "priority": "medium"},
                        "last_updated": int(datetime.now().timestamp())
                    }
                }
            }
            logger.info("Using sample floorplan data for testing")
        
        # Perform test validation
        click.echo(f"Testing BIM health checker for floorplan: {test_floorplan_id}")
        click.echo(f"Objects to validate: {len(floorplan_data_dict.get('objects', {}))}")
        
        result = bim_health_service.validate_floorplan(
            floorplan_id=test_floorplan_id,
            floorplan_data=floorplan_data_dict
        )
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump({
                    'validation_id': result.validation_id,
                    'floorplan_id': result.floorplan_id,
                    'status': result.status.value,
                    'total_objects': result.total_objects,
                    'issues_found': result.issues_found,
                    'validation_time': result.validation_time,
                    'summary': result.summary
                }, f, indent=2, default=str)
            logger.info(f"Test results saved to {output}")
        
        # Display results
        click.echo(f"Test completed successfully!")
        click.echo(f"  Validation ID: {result.validation_id}")
        click.echo(f"  Status: {result.status.value}")
        click.echo(f"  Total Objects: {result.total_objects}")
        click.echo(f"  Issues Found: {result.issues_found}")
        click.echo(f"  Validation Time: {result.validation_time:.2f} seconds")
        
        # Check status
        history = bim_health_service.get_validation_history(test_floorplan_id, limit=1)
        if history:
            click.echo(f"  Floorplan Status: Validated")
        else:
            click.echo(f"  Floorplan Status: Not found")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@bim_health.command()
def health():
    """
    Check BIM health checker service health.
    
    This command provides a health check for the BIM health checker service
    including database connectivity and basic functionality.
    
    Examples:
        arx bim-health health
    """
    try:
        bim_health_service = BIMHealthCheckerService()
        
        # Get metrics as a health check
        metrics = bim_health_service.get_metrics()
        
        click.echo("BIM Health Checker Service Health Check")
        click.echo("=" * 40)
        click.echo(f"Status: Healthy")
        click.echo(f"Database accessible: Yes")
        click.echo(f"Behavior profiles: {metrics['behavior_profiles']}")
        click.echo(f"Database size: {metrics['database_size']} bytes")
        click.echo(f"Total validations: {metrics['metrics']['total_validations']}")
        
        # Test basic functionality
        test_floorplan_id = f"health_check_{int(datetime.now().timestamp())}"
        history = bim_health_service.get_validation_history(test_floorplan_id, limit=1)
        
        if len(history) == 0:
            click.echo("Basic functionality: OK")
        else:
            click.echo("Basic functionality: Warning (unexpected history)")
        
        click.echo("Health check completed successfully!")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        click.echo(f"Health check failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    bim_health() 