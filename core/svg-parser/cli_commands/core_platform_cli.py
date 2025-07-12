"""
Core Platform CLI Commands

This module provides comprehensive command-line interface for core platform
functionality including service management, health monitoring, configuration,
caching, and system metrics.

Usage Examples:
    arx platform health
    arx platform services list
    arx platform services register --service-id test_service --name "Test Service"
    arx platform services status
    arx platform metrics
    arx platform cache set --key test_key --value test_value --ttl 3600
    arx platform cache get --key test_key
    arx platform config get
    arx platform config update --log-level DEBUG --cache-ttl 7200
"""

import click
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from services.core_platform import (
    CorePlatformService,
    ServiceType,
    ServiceStatus,
    HealthStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@click.group()
def platform():
    """Core Platform commands."""
    pass


@platform.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
@click.option('--output', type=click.Path(), help='Output file for health status')
def health(format: str, output: Optional[str]):
    """
    Get system health status.
    
    This command provides comprehensive health information including
    service status, uptime, and health percentages.
    
    Examples:
        arx platform health
        arx platform health --format json --output health.json
    """
    try:
        platform_service = CorePlatformService()
        
        logger.info("Getting system health status")
        health_status = platform_service.get_health_status()
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(health_status, f, indent=2, default=str)
            logger.info(f"Health status saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps(health_status, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("status,healthy_services,total_services,health_percentage,uptime")
            click.echo(f"{health_status['status']},{health_status['healthy_services']},{health_status['total_services']},{health_status['health_percentage']:.1f},{health_status['uptime']:.1f}")
        else:
            # Table format
            click.echo("System Health Status")
            click.echo("=" * 30)
            click.echo(f"Status: {health_status['status']}")
            click.echo(f"Healthy Services: {health_status['healthy_services']}")
            click.echo(f"Total Services: {health_status['total_services']}")
            click.echo(f"Health Percentage: {health_status['health_percentage']:.1f}%")
            click.echo(f"Uptime: {health_status['uptime']:.1f} seconds")
            click.echo(f"Last Check: {health_status['last_check']}")
            
            # Health indicator
            if health_status['status'] == 'healthy':
                click.echo("🟢 System is healthy")
            elif health_status['status'] == 'degraded':
                click.echo("🟡 System is degraded")
            else:
                click.echo("🔴 System is unhealthy")
        
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@platform.group()
def services():
    """Service management commands."""
    pass


@services.command()
@click.option('--service-type', help='Filter by service type')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
@click.option('--output', type=click.Path(), help='Output file for service list')
def list(service_type: Optional[str], format: str, output: Optional[str]):
    """
    List all registered services.
    
    This command provides information about all registered services
    with optional filtering by service type.
    
    Examples:
        arx platform services list
        arx platform services list --service-type api
        arx platform services list --format json
    """
    try:
        platform_service = CorePlatformService()
        
        logger.info("Getting list of registered services")
        
        # Convert service type string to enum if provided
        service_type_enum = None
        if service_type:
            try:
                service_type_enum = ServiceType(service_type)
            except ValueError:
                click.echo(f"Error: Invalid service type '{service_type}'", err=True)
                sys.exit(1)
        
        services = platform_service.list_services(service_type_enum)
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump([{
                    'service_id': s.service_id,
                    'name': s.name,
                    'service_type': s.service_type.value,
                    'status': s.status.value,
                    'version': s.version,
                    'host': s.host,
                    'port': s.port,
                    'health_endpoint': s.health_endpoint,
                    'metadata': s.metadata,
                    'last_heartbeat': s.last_heartbeat.isoformat() if s.last_heartbeat else None,
                    'created_at': s.created_at.isoformat()
                } for s in services], f, indent=2, default=str)
            logger.info(f"Service list saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps([{
                'service_id': s.service_id,
                'name': s.name,
                'service_type': s.service_type.value,
                'status': s.status.value,
                'version': s.version,
                'host': s.host,
                'port': s.port,
                'health_endpoint': s.health_endpoint,
                'metadata': s.metadata,
                'last_heartbeat': s.last_heartbeat.isoformat() if s.last_heartbeat else None,
                'created_at': s.created_at.isoformat()
            } for s in services], indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("service_id,name,service_type,status,version,host,port,health_endpoint,last_heartbeat,created_at")
            for service in services:
                click.echo(f"{service.service_id},{service.name},{service.service_type.value},{service.status.value},{service.version},{service.host},{service.port},{service.health_endpoint or ''},{service.last_heartbeat.isoformat() if service.last_heartbeat else ''},{service.created_at.isoformat()}")
        else:
            # Table format
            click.echo(f"Registered Services ({len(services)} total)")
            click.echo("=" * 50)
            
            if services:
                for service in services:
                    status_icon = "🟢" if service.status == ServiceStatus.RUNNING else "🔴" if service.status == ServiceStatus.ERROR else "🟡"
                    click.echo(f"{status_icon} {service.name} ({service.service_id})")
                    click.echo(f"    Type: {service.service_type.value}")
                    click.echo(f"    Status: {service.status.value}")
                    click.echo(f"    Version: {service.version}")
                    click.echo(f"    Host: {service.host}:{service.port}")
                    if service.health_endpoint:
                        click.echo(f"    Health: {service.health_endpoint}")
                    if service.last_heartbeat:
                        click.echo(f"    Last Heartbeat: {service.last_heartbeat.isoformat()}")
                    click.echo()
            else:
                click.echo("No services registered.")
        
    except Exception as e:
        logger.error(f"Failed to list services: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@services.command()
@click.option('--service-id', required=True, help='Unique service identifier')
@click.option('--name', required=True, help='Service name')
@click.option('--service-type', required=True, type=click.Choice(['core', 'api', 'worker', 'database', 'cache', 'external']), help='Service type')
@click.option('--version', default='1.0.0', help='Service version')
@click.option('--host', default='localhost', help='Service host')
@click.option('--port', default=8080, type=int, help='Service port')
@click.option('--health-endpoint', help='Health check endpoint')
@click.option('--metadata', help='Additional metadata (JSON)')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def register(service_id: str, name: str, service_type: str, version: str, host: str, port: int,
             health_endpoint: Optional[str], metadata: Optional[str], format: str):
    """
    Register a new service with the platform.
    
    This command allows services to register themselves with the platform
    for discovery and health monitoring.
    
    Examples:
        arx platform services register --service-id my_service --name "My Service" --service-type api
        arx platform services register --service-id db_service --name "Database Service" --service-type database --port 5432
    """
    try:
        platform_service = CorePlatformService()
        
        # Parse metadata if provided
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                click.echo("Error: Invalid JSON in metadata", err=True)
                sys.exit(1)
        
        # Create service info
        from services.core_platform import ServiceInfo
        service_info = ServiceInfo(
            service_id=service_id,
            name=name,
            service_type=ServiceType(service_type),
            status=ServiceStatus.RUNNING,
            version=version,
            host=host,
            port=port,
            health_endpoint=health_endpoint,
            metadata=metadata_dict,
            last_heartbeat=datetime.now(),
            created_at=datetime.now()
        )
        
        logger.info(f"Registering service: {service_id}")
        
        # Register service
        success = platform_service.register_service(service_info)
        
        if not success:
            click.echo("Error: Service registration failed", err=True)
            sys.exit(1)
        
        # Display results
        if format == 'json':
            click.echo(json.dumps({
                'service_id': service_id,
                'name': name,
                'service_type': service_type,
                'status': 'registered',
                'version': version,
                'host': host,
                'port': port,
                'health_endpoint': health_endpoint,
                'metadata': metadata_dict,
                'registered_at': datetime.now().isoformat()
            }, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("service_id,name,service_type,status,version,host,port,health_endpoint,registered_at")
            click.echo(f"{service_id},{name},{service_type},registered,{version},{host},{port},{health_endpoint or ''},{datetime.now().isoformat()}")
        else:
            # Table format
            click.echo(f"Service registered successfully!")
            click.echo("=" * 30)
            click.echo(f"Service ID: {service_id}")
            click.echo(f"Name: {name}")
            click.echo(f"Type: {service_type}")
            click.echo(f"Version: {version}")
            click.echo(f"Host: {host}:{port}")
            if health_endpoint:
                click.echo(f"Health Endpoint: {health_endpoint}")
            if metadata_dict:
                click.echo(f"Metadata: {json.dumps(metadata_dict, indent=2)}")
            click.echo(f"Registered At: {datetime.now().isoformat()}")
        
        logger.info(f"Service {service_id} registered successfully")
        
    except Exception as e:
        logger.error(f"Service registration failed for {service_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@services.command()
@click.option('--service-id', required=True, help='Service identifier')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def info(service_id: str, format: str):
    """
    Get information about a specific service.
    
    This command provides detailed information about a registered service
    including status, health, and metadata.
    
    Examples:
        arx platform services info --service-id my_service
        arx platform services info --service-id db_service --format json
    """
    try:
        platform_service = CorePlatformService()
        
        logger.info(f"Getting service information for {service_id}")
        
        service_info = platform_service.get_service_info(service_id)
        
        if not service_info:
            click.echo(f"Error: Service {service_id} not found", err=True)
            sys.exit(1)
        
        # Display results
        if format == 'json':
            click.echo(json.dumps({
                'service_id': service_info.service_id,
                'name': service_info.name,
                'service_type': service_info.service_type.value,
                'status': service_info.status.value,
                'version': service_info.version,
                'host': service_info.host,
                'port': service_info.port,
                'health_endpoint': service_info.health_endpoint,
                'metadata': service_info.metadata,
                'last_heartbeat': service_info.last_heartbeat.isoformat() if service_info.last_heartbeat else None,
                'created_at': service_info.created_at.isoformat()
            }, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("service_id,name,service_type,status,version,host,port,health_endpoint,last_heartbeat,created_at")
            click.echo(f"{service_info.service_id},{service_info.name},{service_info.service_type.value},{service_info.status.value},{service_info.version},{service_info.host},{service_info.port},{service_info.health_endpoint or ''},{service_info.last_heartbeat.isoformat() if service_info.last_heartbeat else ''},{service_info.created_at.isoformat()}")
        else:
            # Table format
            click.echo(f"Service Information: {service_id}")
            click.echo("=" * 40)
            click.echo(f"Name: {service_info.name}")
            click.echo(f"Type: {service_info.service_type.value}")
            click.echo(f"Status: {service_info.status.value}")
            click.echo(f"Version: {service_info.version}")
            click.echo(f"Host: {service_info.host}:{service_info.port}")
            if service_info.health_endpoint:
                click.echo(f"Health Endpoint: {service_info.health_endpoint}")
            if service_info.metadata:
                click.echo(f"Metadata: {json.dumps(service_info.metadata, indent=2)}")
            if service_info.last_heartbeat:
                click.echo(f"Last Heartbeat: {service_info.last_heartbeat.isoformat()}")
            click.echo(f"Created At: {service_info.created_at.isoformat()}")
        
    except Exception as e:
        logger.error(f"Failed to get service info for {service_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@services.command()
@click.option('--service-id', required=True, help='Service identifier')
def unregister(service_id: str):
    """
    Unregister a service from the platform.
    
    This command allows services to unregister themselves from the platform
    when they are shutting down or becoming unavailable.
    
    Examples:
        arx platform services unregister --service-id my_service
    """
    try:
        platform_service = CorePlatformService()
        
        logger.info(f"Unregistering service: {service_id}")
        
        success = platform_service.unregister_service(service_id)
        
        if not success:
            click.echo(f"Error: Service {service_id} not found", err=True)
            sys.exit(1)
        
        click.echo(f"Service {service_id} unregistered successfully!")
        click.echo(f"Unregistered At: {datetime.now().isoformat()}")
        
        logger.info(f"Service {service_id} unregistered successfully")
        
    except Exception as e:
        logger.error(f"Failed to unregister service {service_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@services.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def status(format: str):
    """
    Get status of all registered services.
    
    This command provides a summary of service status including
    counts by status and service type.
    
    Examples:
        arx platform services status
        arx platform services status --format json
    """
    try:
        platform_service = CorePlatformService()
        
        logger.info("Getting services status")
        
        services = platform_service.list_services()
        
        # Calculate status summary
        status_summary = {
            'total_services': len(services),
            'running_services': len([s for s in services if s.status == ServiceStatus.RUNNING]),
            'error_services': len([s for s in services if s.status == ServiceStatus.ERROR]),
            'degraded_services': len([s for s in services if s.status == ServiceStatus.DEGRADED]),
            'stopped_services': len([s for s in services if s.status == ServiceStatus.STOPPED]),
            'services_by_type': {},
            'services_by_status': {}
        }
        
        # Group by service type
        for service in services:
            service_type = service.service_type.value
            if service_type not in status_summary["services_by_type"]:
                status_summary["services_by_type"][service_type] = []
            status_summary["services_by_type"][service_type].append({
                'service_id': service.service_id,
                'name': service.name,
                'status': service.status.value
            })
        
        # Group by status
        for service in services:
            status = service.status.value
            if status not in status_summary["services_by_status"]:
                status_summary["services_by_status"][status] = []
            status_summary["services_by_status"][status].append({
                'service_id': service.service_id,
                'name': service.name,
                'service_type': service.service_type.value
            })
        
        # Display results
        if format == 'json':
            click.echo(json.dumps(status_summary, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("total_services,running_services,error_services,degraded_services,stopped_services")
            click.echo(f"{status_summary['total_services']},{status_summary['running_services']},{status_summary['error_services']},{status_summary['degraded_services']},{status_summary['stopped_services']}")
        else:
            # Table format
            click.echo("Services Status Summary")
            click.echo("=" * 30)
            click.echo(f"Total Services: {status_summary['total_services']}")
            click.echo(f"Running: {status_summary['running_services']}")
            click.echo(f"Error: {status_summary['error_services']}")
            click.echo(f"Degraded: {status_summary['degraded_services']}")
            click.echo(f"Stopped: {status_summary['stopped_services']}")
            
            if status_summary['services_by_type']:
                click.echo("\nServices by Type:")
                for service_type, services_list in status_summary['services_by_type'].items():
                    click.echo(f"  {service_type}: {len(services_list)}")
            
            if status_summary['services_by_status']:
                click.echo("\nServices by Status:")
                for status, services_list in status_summary['services_by_status'].items():
                    click.echo(f"  {status}: {len(services_list)}")
        
    except Exception as e:
        logger.error(f"Failed to get services status: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@platform.command()
@click.option('--limit', default=100, type=int, help='Maximum number of metrics to return')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
@click.option('--output', type=click.Path(), help='Output file for metrics')
def metrics(limit: int, format: str, output: Optional[str]):
    """
    Get system performance metrics.
    
    This command provides historical system performance metrics including
    CPU, memory, disk, and network usage.
    
    Examples:
        arx platform metrics
        arx platform metrics --limit 50 --format json
    """
    try:
        platform_service = CorePlatformService()
        
        if limit < 1 or limit > 1000:
            click.echo("Error: Limit must be between 1 and 1000", err=True)
            sys.exit(1)
        
        logger.info("Getting system metrics")
        metrics = platform_service.get_system_metrics(limit)
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump([{
                    'cpu_usage': m.cpu_usage,
                    'memory_usage': m.memory_usage,
                    'disk_usage': m.disk_usage,
                    'network_io': m.network_io,
                    'active_connections': m.active_connections,
                    'response_time': m.response_time,
                    'error_rate': m.error_rate,
                    'timestamp': m.timestamp.isoformat()
                } for m in metrics], f, indent=2, default=str)
            logger.info(f"Metrics saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps([{
                'cpu_usage': m.cpu_usage,
                'memory_usage': m.memory_usage,
                'disk_usage': m.disk_usage,
                'network_io': m.network_io,
                'active_connections': m.active_connections,
                'response_time': m.response_time,
                'error_rate': m.error_rate,
                'timestamp': m.timestamp.isoformat()
            } for m in metrics], indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("cpu_usage,memory_usage,disk_usage,active_connections,response_time,error_rate,timestamp")
            for metric in metrics:
                click.echo(f"{metric.cpu_usage},{metric.memory_usage},{metric.disk_usage},{metric.active_connections},{metric.response_time},{metric.error_rate},{metric.timestamp.isoformat()}")
        else:
            # Table format
            click.echo(f"System Metrics ({len(metrics)} records)")
            click.echo("=" * 40)
            
            if metrics:
                latest = metrics[-1]
                click.echo(f"Latest Metrics:")
                click.echo(f"  CPU Usage: {latest.cpu_usage:.1f}%")
                click.echo(f"  Memory Usage: {latest.memory_usage:.1f}%")
                click.echo(f"  Disk Usage: {latest.disk_usage:.1f}%")
                click.echo(f"  Active Connections: {latest.active_connections}")
                click.echo(f"  Response Time: {latest.response_time:.3f}s")
                click.echo(f"  Error Rate: {latest.error_rate:.2f}%")
                click.echo(f"  Timestamp: {latest.timestamp.isoformat()}")
                
                if len(metrics) > 1:
                    click.echo(f"\nHistorical Data: {len(metrics)} records available")
            else:
                click.echo("No metrics available.")
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@platform.group()
def cache():
    """Cache management commands."""
    pass


@cache.command()
@click.option('--key', required=True, help='Cache key')
@click.option('--value', required=True, help='Cache value')
@click.option('--ttl', type=int, help='Time to live in seconds')
def set(key: str, value: str, ttl: Optional[int]):
    """
    Set a value in the cache.
    
    This command allows setting values in the platform cache with
    optional time-to-live settings.
    
    Examples:
        arx platform cache set --key my_key --value my_value
        arx platform cache set --key temp_key --value temp_value --ttl 3600
    """
    try:
        platform_service = CorePlatformService()
        
        logger.info(f"Setting cache value for key: {key}")
        
        success = platform_service.cache_set(key, value, ttl)
        
        if not success:
            click.echo("Error: Cache set operation failed", err=True)
            sys.exit(1)
        
        click.echo(f"Cache value set successfully!")
        click.echo(f"Key: {key}")
        click.echo(f"Value: {value}")
        if ttl:
            click.echo(f"TTL: {ttl} seconds")
        click.echo(f"Set At: {datetime.now().isoformat()}")
        
    except Exception as e:
        logger.error(f"Failed to set cache value for key {key}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cache.command()
@click.option('--key', required=True, help='Cache key')
def get(key: str):
    """
    Get a value from the cache.
    
    This command retrieves values from the platform cache.
    
    Examples:
        arx platform cache get --key my_key
    """
    try:
        platform_service = CorePlatformService()
        
        logger.info(f"Getting cache value for key: {key}")
        
        value = platform_service.cache_get(key)
        
        if value is not None:
            click.echo(f"Cache value retrieved successfully!")
            click.echo(f"Key: {key}")
            click.echo(f"Value: {value}")
            click.echo(f"Retrieved At: {datetime.now().isoformat()}")
        else:
            click.echo(f"Cache key '{key}' not found")
        
    except Exception as e:
        logger.error(f"Failed to get cache value for key {key}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cache.command()
@click.option('--key', required=True, help='Cache key')
def delete(key: str):
    """
    Delete a value from the cache.
    
    This command removes values from the platform cache.
    
    Examples:
        arx platform cache delete --key my_key
    """
    try:
        platform_service = CorePlatformService()
        
        logger.info(f"Deleting cache value for key: {key}")
        
        success = platform_service.cache_delete(key)
        
        if not success:
            click.echo("Error: Cache delete operation failed", err=True)
            sys.exit(1)
        
        click.echo(f"Cache value deleted successfully!")
        click.echo(f"Key: {key}")
        click.echo(f"Deleted At: {datetime.now().isoformat()}")
        
    except Exception as e:
        logger.error(f"Failed to delete cache value for key {key}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cache.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def stats(format: str):
    """
    Get cache performance statistics.
    
    This command provides comprehensive cache performance metrics including
    hit rates, memory usage, and Redis availability.
    
    Examples:
        arx platform cache stats
        arx platform cache stats --format json
    """
    try:
        platform_service = CorePlatformService()
        
        logger.info("Getting cache statistics")
        cache_stats = platform_service.get_cache_stats()
        
        # Display results
        if format == 'json':
            click.echo(json.dumps(cache_stats, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("hits,misses,sets,deletes,hit_rate,memory_cache_size,redis_available")
            click.echo(f"{cache_stats['hits']},{cache_stats['misses']},{cache_stats['sets']},{cache_stats['deletes']},{cache_stats['hit_rate']},{cache_stats['memory_cache_size']},{cache_stats['redis_available']}")
        else:
            # Table format
            click.echo("Cache Performance Statistics")
            click.echo("=" * 30)
            click.echo(f"Hits: {cache_stats['hits']}")
            click.echo(f"Misses: {cache_stats['misses']}")
            click.echo(f"Sets: {cache_stats['sets']}")
            click.echo(f"Deletes: {cache_stats['deletes']}")
            click.echo(f"Hit Rate: {cache_stats['hit_rate']:.1f}%")
            click.echo(f"Memory Cache Size: {cache_stats['memory_cache_size']}")
            click.echo(f"Redis Available: {'Yes' if cache_stats['redis_available'] else 'No'}")
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@platform.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
@click.option('--output', type=click.Path(), help='Output file for configuration')
def get(format: str, output: Optional[str]):
    """
    Get current system configuration.
    
    This command provides the current platform configuration including
    environment settings, feature flags, and system parameters.
    
    Examples:
        arx platform config get
        arx platform config get --format json --output config.json
    """
    try:
        platform_service = CorePlatformService()
        
        logger.info("Getting system configuration")
        config = platform_service.get_configuration()
        
        config_dict = {
            'environment': config.environment,
            'debug_mode': config.debug_mode,
            'log_level': config.log_level,
            'database_url': config.database_url,
            'redis_url': config.redis_url,
            'api_host': config.api_host,
            'api_port': config.api_port,
            'max_workers': config.max_workers,
            'cache_ttl': config.cache_ttl,
            'health_check_interval': config.health_check_interval,
            'backup_interval': config.backup_interval,
            'security_settings': config.security_settings,
            'feature_flags': config.feature_flags
        }
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            logger.info(f"Configuration saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps(config_dict, indent=2, default=str))
        elif format == 'csv':
            # CSV output for main settings
            click.echo("setting,value")
            for key, value in config_dict.items():
                if not isinstance(value, (dict, list)):
                    click.echo(f"{key},{value}")
        else:
            # Table format
            click.echo("System Configuration")
            click.echo("=" * 30)
            click.echo(f"Environment: {config.environment}")
            click.echo(f"Debug Mode: {config.debug_mode}")
            click.echo(f"Log Level: {config.log_level}")
            click.echo(f"Database URL: {config.database_url}")
            click.echo(f"Redis URL: {config.redis_url}")
            click.echo(f"API Host: {config.api_host}")
            click.echo(f"API Port: {config.api_port}")
            click.echo(f"Max Workers: {config.max_workers}")
            click.echo(f"Cache TTL: {config.cache_ttl} seconds")
            click.echo(f"Health Check Interval: {config.health_check_interval} seconds")
            click.echo(f"Backup Interval: {config.backup_interval} seconds")
            
            if config.security_settings:
                click.echo(f"\nSecurity Settings:")
                for key, value in config.security_settings.items():
                    click.echo(f"  {key}: {value}")
            
            if config.feature_flags:
                click.echo(f"\nFeature Flags:")
                for key, value in config.feature_flags.items():
                    click.echo(f"  {key}: {value}")
        
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@config.command()
@click.option('--log-level', help='Log level (DEBUG, INFO, WARNING, ERROR)')
@click.option('--cache-ttl', type=int, help='Cache TTL in seconds')
@click.option('--debug-mode', type=bool, help='Debug mode (true/false)')
@click.option('--max-workers', type=int, help='Maximum workers')
@click.option('--health-check-interval', type=int, help='Health check interval in seconds')
@click.option('--backup-interval', type=int, help='Backup interval in seconds')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def update(log_level: Optional[str], cache_ttl: Optional[int], debug_mode: Optional[bool],
           max_workers: Optional[int], health_check_interval: Optional[int], backup_interval: Optional[int],
           format: str):
    """
    Update system configuration.
    
    This command allows updating platform configuration parameters
    with proper validation and persistence.
    
    Examples:
        arx platform config update --log-level DEBUG
        arx platform config update --cache-ttl 7200 --debug-mode true
    """
    try:
        platform_service = CorePlatformService()
        
        # Build updates dictionary
        updates = {}
        if log_level is not None:
            updates['log_level'] = log_level
        if cache_ttl is not None:
            updates['cache_ttl'] = cache_ttl
        if debug_mode is not None:
            updates['debug_mode'] = debug_mode
        if max_workers is not None:
            updates['max_workers'] = max_workers
        if health_check_interval is not None:
            updates['health_check_interval'] = health_check_interval
        if backup_interval is not None:
            updates['backup_interval'] = backup_interval
        
        if not updates:
            click.echo("Error: No configuration updates specified", err=True)
            sys.exit(1)
        
        logger.info("Updating system configuration")
        
        success = platform_service.update_configuration(updates)
        
        if not success:
            click.echo("Error: Configuration update failed", err=True)
            sys.exit(1)
        
        # Display results
        if format == 'json':
            click.echo(json.dumps({
                'status': 'updated',
                'updates': updates,
                'updated_at': datetime.now().isoformat()
            }, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("setting,new_value,updated_at")
            for key, value in updates.items():
                click.echo(f"{key},{value},{datetime.now().isoformat()}")
        else:
            # Table format
            click.echo("Configuration updated successfully!")
            click.echo("=" * 30)
            for key, value in updates.items():
                click.echo(f"{key}: {value}")
            click.echo(f"Updated At: {datetime.now().isoformat()}")
        
        logger.info("Configuration updated successfully")
        
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@platform.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
@click.option('--output', type=click.Path(), help='Output file for performance metrics')
def performance(format: str, output: Optional[str]):
    """
    Get comprehensive performance metrics.
    
    This command provides detailed performance metrics including
    uptime, request statistics, success rates, and system health.
    
    Examples:
        arx platform performance
        arx platform performance --format json --output performance.json
    """
    try:
        platform_service = CorePlatformService()
        
        logger.info("Getting performance metrics")
        metrics = platform_service.get_performance_metrics()
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
            logger.info(f"Performance metrics saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps(metrics, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("uptime_seconds,total_requests,successful_requests,failed_requests,success_rate,average_response_time,registered_services,health_status")
            click.echo(f"{metrics['uptime_seconds']},{metrics['total_requests']},{metrics['successful_requests']},{metrics['failed_requests']},{metrics['success_rate']},{metrics['average_response_time']},{metrics['registered_services']},{metrics['health_status']}")
        else:
            # Table format
            click.echo("Performance Metrics")
            click.echo("=" * 30)
            click.echo(f"Uptime: {metrics['uptime_seconds']:.1f} seconds")
            click.echo(f"Total Requests: {metrics['total_requests']}")
            click.echo(f"Successful Requests: {metrics['successful_requests']}")
            click.echo(f"Failed Requests: {metrics['failed_requests']}")
            click.echo(f"Success Rate: {metrics['success_rate']:.1f}%")
            click.echo(f"Average Response Time: {metrics['average_response_time']:.3f}s")
            click.echo(f"Registered Services: {metrics['registered_services']}")
            click.echo(f"Health Status: {metrics['health_status']}")
            
            # Cache stats
            if 'cache_stats' in metrics:
                click.echo(f"\nCache Statistics:")
                cache_stats = metrics['cache_stats']
                click.echo(f"  Hit Rate: {cache_stats.get('hit_rate', 0):.1f}%")
                click.echo(f"  Memory Cache Size: {cache_stats.get('memory_cache_size', 0)}")
                click.echo(f"  Redis Available: {'Yes' if cache_stats.get('redis_available', False) else 'No'}")
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    platform() 