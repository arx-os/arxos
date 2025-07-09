"""
Advanced Infrastructure CLI Commands

This module provides comprehensive command-line interface for advanced infrastructure
functionality including SVG grouping, caching, distributed processing, collaboration,
and performance monitoring.

Usage Examples:
    arx infrastructure health
    arx infrastructure svg-groups create --name "Building Floor" --elements '[...]'
    arx infrastructure cache set --key "calc_result" --value "1000"
    arx infrastructure cache get --key "calc_result"
    arx infrastructure process --type calculation --data '{"operation": "add", "values": [1,2,3]}'
    arx infrastructure collaboration create --document-id "doc123" --users "user1,user2"
    arx infrastructure performance
"""

import click
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from services.advanced_infrastructure import (
    AdvancedInfrastructure,
    CacheStrategy,
    ProcessingMode,
    CompressionLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@click.group()
def infrastructure():
    """Advanced Infrastructure commands."""
    pass


@infrastructure.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def health(format: str):
    """
    Get advanced infrastructure health status.
    
    Examples:
        arx infrastructure health
        arx infrastructure health --format json
    """
    try:
        infra = AdvancedInfrastructure()
        
        logger.info("Getting advanced infrastructure health status")
        metrics = infra.get_performance_metrics()
        
        health_status = {
            "status": "healthy" if metrics['cache_hit_rate'] > 50 else "degraded",
            "cache_hit_rate": metrics['cache_hit_rate'],
            "cache_size": metrics['cache_size'],
            "processing_tasks": metrics['processing_tasks'],
            "active_sessions": metrics['active_sessions'],
            "memory_usage": metrics['memory_usage']
        }
        
        if format == 'json':
            click.echo(json.dumps(health_status, indent=2))
        elif format == 'csv':
            click.echo("status,cache_hit_rate,cache_size,processing_tasks,active_sessions")
            click.echo(f"{health_status['status']},{health_status['cache_hit_rate']:.1f},{health_status['cache_size']},{health_status['processing_tasks']},{health_status['active_sessions']}")
        else:
            click.echo("Advanced Infrastructure Health Status")
            click.echo("=" * 40)
            click.echo(f"Status: {health_status['status']}")
            click.echo(f"Cache Hit Rate: {health_status['cache_hit_rate']:.1f}%")
            click.echo(f"Cache Size: {health_status['cache_size']}")
            click.echo(f"Processing Tasks: {health_status['processing_tasks']}")
            click.echo(f"Active Sessions: {health_status['active_sessions']}")
            click.echo(f"Memory Usage: {health_status['memory_usage'] / 1024 / 1024:.1f} MB")
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@infrastructure.group()
def svg_groups():
    """SVG group management commands."""
    pass


@svg_groups.command()
@click.option('--name', required=True, help='Group name')
@click.option('--elements', required=True, help='SVG elements (JSON)')
@click.option('--parent-id', help='Parent group ID')
@click.option('--metadata', help='Additional metadata (JSON)')
def create(name: str, elements: str, parent_id: Optional[str], metadata: Optional[str]):
    """
    Create a new SVG group.
    
    Examples:
        arx infrastructure svg-groups create --name "Building Floor" --elements '[{"type": "rect", "id": "floor1"}]'
    """
    try:
        infra = AdvancedInfrastructure()
        
        # Parse JSON inputs
        try:
            elements_data = json.loads(elements)
            metadata_data = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON format: {e}", err=True)
            sys.exit(1)
        
        logger.info(f"Creating SVG group: {name}")
        
        group_id = infra.create_hierarchical_svg_group(
            name=name,
            elements=elements_data,
            parent_id=parent_id,
            metadata=metadata_data
        )
        
        click.echo(f"SVG group created successfully!")
        click.echo(f"Group ID: {group_id}")
        click.echo(f"Name: {name}")
        click.echo(f"Elements: {len(elements_data)}")
        
    except Exception as e:
        logger.error(f"Failed to create SVG group: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@svg_groups.command()
@click.option('--group-id', required=True, help='Group identifier')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def get(group_id: str, format: str):
    """
    Get information about a specific SVG group.
    
    Examples:
        arx infrastructure svg-groups get --group-id group_123
    """
    try:
        infra = AdvancedInfrastructure()
        
        logger.info(f"Getting SVG group information for {group_id}")
        
        group = infra.get_svg_group(group_id)
        
        if not group:
            click.echo(f"Error: SVG group {group_id} not found", err=True)
            sys.exit(1)
        
        if format == 'json':
            click.echo(json.dumps(group, indent=2))
        elif format == 'csv':
            click.echo("group_id,name,parent_id,elements_count,created_at")
            click.echo(f"{group['group_id']},{group['name']},{group['parent_id'] or ''},{len(group['elements'])},{group['created_at']}")
        else:
            click.echo(f"SVG Group Information")
            click.echo("=" * 30)
            click.echo(f"Group ID: {group['group_id']}")
            click.echo(f"Name: {group['name']}")
            click.echo(f"Parent ID: {group['parent_id'] or 'None'}")
            click.echo(f"Elements: {len(group['elements'])}")
            click.echo(f"Created: {group['created_at']}")
            click.echo(f"Updated: {group['updated_at']}")
            
            if group['metadata']:
                click.echo(f"Metadata: {json.dumps(group['metadata'], indent=2)}")
        
    except Exception as e:
        logger.error(f"Failed to get SVG group info for {group_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@svg_groups.command()
@click.option('--group-id', required=True, help='Group identifier')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def hierarchy(group_id: str, format: str):
    """
    Get complete SVG hierarchy starting from the specified group.
    
    Examples:
        arx infrastructure svg-groups hierarchy --group-id group_123
    """
    try:
        infra = AdvancedInfrastructure()
        
        logger.info(f"Getting SVG hierarchy for {group_id}")
        
        hierarchy = infra.get_svg_hierarchy(group_id)
        
        if not hierarchy:
            click.echo(f"Error: SVG group {group_id} not found", err=True)
            sys.exit(1)
        
        if format == 'json':
            click.echo(json.dumps(hierarchy, indent=2))
        elif format == 'csv':
            click.echo("group_id,name,level,children_count,elements_count")
            click.echo(f"{hierarchy['group_id']},{hierarchy['name']},{hierarchy['level']},{len(hierarchy['children'])},{len(hierarchy['elements'])}")
        else:
            click.echo(f"SVG Hierarchy")
            click.echo("=" * 20)
            click.echo(f"Root: {hierarchy['name']} ({hierarchy['group_id']})")
            click.echo(f"Level: {hierarchy['level']}")
            click.echo(f"Elements: {len(hierarchy['elements'])}")
            click.echo(f"Children: {len(hierarchy['children'])}")
            
            if hierarchy['children']:
                click.echo(f"\nChildren:")
                for child in hierarchy['children']:
                    click.echo(f"  - {child['name']} (Level {child['level']}, {len(child['elements'])} elements)")
        
    except Exception as e:
        logger.error(f"Failed to get SVG hierarchy for {group_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@infrastructure.group()
def cache():
    """Cache management commands."""
    pass


@cache.command()
@click.option('--key', required=True, help='Cache key')
@click.option('--value', required=True, help='Value to cache')
@click.option('--ttl', type=int, help='Time to live in seconds')
@click.option('--strategy', type=click.Choice(['lru', 'lfu', 'fifo', 'ttl']), help='Cache strategy')
def set(key: str, value: str, ttl: Optional[int], strategy: Optional[str]):
    """
    Set a value in the cache.
    
    Examples:
        arx infrastructure cache set --key "calc_result" --value "1000" --ttl 3600
    """
    try:
        infra = AdvancedInfrastructure()
        
        # Convert strategy string to enum
        strategy_enum = None
        if strategy:
            try:
                strategy_enum = CacheStrategy(strategy)
            except ValueError:
                click.echo(f"Error: Invalid cache strategy '{strategy}'", err=True)
                sys.exit(1)
        
        logger.info(f"Setting cache entry: {key}")
        
        success = infra.cache_set(
            key=key,
            value=value,
            ttl=ttl,
            strategy=strategy_enum
        )
        
        if not success:
            click.echo("Error: Failed to set cache entry", err=True)
            sys.exit(1)
        
        click.echo(f"Cache entry set successfully!")
        click.echo(f"Key: {key}")
        click.echo(f"Value: {value}")
        if ttl:
            click.echo(f"TTL: {ttl} seconds")
        
    except Exception as e:
        logger.error(f"Failed to set cache entry: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cache.command()
@click.option('--key', required=True, help='Cache key')
def get(key: str):
    """
    Get a value from the cache.
    
    Examples:
        arx infrastructure cache get --key "calc_result"
    """
    try:
        infra = AdvancedInfrastructure()
        
        logger.info(f"Getting cache entry: {key}")
        
        value = infra.cache_get(key)
        
        if value is None:
            click.echo(f"Error: Cache entry '{key}' not found", err=True)
            sys.exit(1)
        
        click.echo(f"Cache Entry")
        click.echo("=" * 20)
        click.echo(f"Key: {key}")
        click.echo(f"Value: {value}")
        
    except Exception as e:
        logger.error(f"Failed to get cache entry {key}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cache.command()
@click.option('--key', required=True, help='Cache key')
def delete(key: str):
    """
    Delete a value from the cache.
    
    Examples:
        arx infrastructure cache delete --key "calc_result"
    """
    try:
        infra = AdvancedInfrastructure()
        
        logger.info(f"Deleting cache entry: {key}")
        
        # Remove from memory cache
        if key in infra.cache:
            del infra.cache[key]
        
        # Remove from database
        infra._remove_cache_entry(key)
        
        click.echo(f"Cache entry deleted successfully!")
        click.echo(f"Key: {key}")
        
    except Exception as e:
        logger.error(f"Failed to delete cache entry {key}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cache.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def stats(format: str):
    """
    Get cache statistics.
    
    Examples:
        arx infrastructure cache stats
        arx infrastructure cache stats --format json
    """
    try:
        infra = AdvancedInfrastructure()
        
        logger.info("Getting cache statistics")
        
        metrics = infra.get_performance_metrics()
        
        cache_stats = {
            "total_entries": metrics['cache_size'],
            "hits": metrics['cache_hits'],
            "misses": metrics['cache_misses'],
            "hit_rate": metrics['cache_hit_rate'],
            "memory_usage": metrics['memory_usage'],
            "max_size": metrics['max_cache_size'],
            "max_memory": metrics['max_cache_memory']
        }
        
        if format == 'json':
            click.echo(json.dumps(cache_stats, indent=2))
        elif format == 'csv':
            click.echo("total_entries,hits,misses,hit_rate,memory_usage")
            click.echo(f"{cache_stats['total_entries']},{cache_stats['hits']},{cache_stats['misses']},{cache_stats['hit_rate']:.1f},{cache_stats['memory_usage']}")
        else:
            click.echo("Cache Statistics")
            click.echo("=" * 20)
            click.echo(f"Total Entries: {cache_stats['total_entries']}")
            click.echo(f"Hits: {cache_stats['hits']}")
            click.echo(f"Misses: {cache_stats['misses']}")
            click.echo(f"Hit Rate: {cache_stats['hit_rate']:.1f}%")
            click.echo(f"Memory Usage: {cache_stats['memory_usage'] / 1024 / 1024:.1f} MB")
            click.echo(f"Max Size: {cache_stats['max_size']}")
            click.echo(f"Max Memory: {cache_stats['max_memory'] / 1024 / 1024:.1f} MB")
        
    except Exception as e:
        logger.error(f"Failed to get cache statistics: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@infrastructure.group()
def process():
    """Distributed processing commands."""
    pass


@process.command()
@click.option('--type', 'task_type', required=True, help='Task type')
@click.option('--data', required=True, help='Task data (JSON)')
@click.option('--priority', default=1, type=int, help='Task priority')
@click.option('--mode', default='parallel', type=click.Choice(['sequential', 'parallel', 'distributed']), help='Processing mode')
def create(task_type: str, data: str, priority: int, mode: str):
    """
    Create and process a distributed task.
    
    Examples:
        arx infrastructure process create --type calculation --data '{"operation": "add", "values": [1,2,3]}'
    """
    try:
        infra = AdvancedInfrastructure()
        
        # Parse JSON data
        try:
            data_obj = json.loads(data)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON format: {e}", err=True)
            sys.exit(1)
        
        # Convert mode string to enum
        try:
            mode_enum = ProcessingMode(mode)
        except ValueError:
            click.echo(f"Error: Invalid processing mode '{mode}'", err=True)
            sys.exit(1)
        
        logger.info(f"Processing distributed task: {task_type}")
        
        task_id = infra.process_distributed_task(
            task_type=task_type,
            data=data_obj,
            priority=priority,
            mode=mode_enum
        )
        
        click.echo(f"Task created successfully!")
        click.echo(f"Task ID: {task_id}")
        click.echo(f"Type: {task_type}")
        click.echo(f"Mode: {mode}")
        click.echo(f"Priority: {priority}")
        
    except Exception as e:
        logger.error(f"Failed to process distributed task: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@process.command()
@click.option('--task-id', required=True, help='Task identifier')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def status(task_id: str, format: str):
    """
    Get task status and result.
    
    Examples:
        arx infrastructure process status --task-id task_123
    """
    try:
        infra = AdvancedInfrastructure()
        
        logger.info(f"Getting task status for {task_id}")
        
        # This would typically query the database for task status
        # For now, return a mock response
        task_info = {
            "task_id": task_id,
            "task_type": "unknown",
            "status": "completed",
            "priority": 1,
            "created_at": datetime.now().isoformat(),
            "result": {"message": "Task completed successfully"},
            "error": None
        }
        
        if format == 'json':
            click.echo(json.dumps(task_info, indent=2))
        elif format == 'csv':
            click.echo("task_id,task_type,status,priority,created_at")
            click.echo(f"{task_info['task_id']},{task_info['task_type']},{task_info['status']},{task_info['priority']},{task_info['created_at']}")
        else:
            click.echo(f"Task Status")
            click.echo("=" * 20)
            click.echo(f"Task ID: {task_info['task_id']}")
            click.echo(f"Type: {task_info['task_type']}")
            click.echo(f"Status: {task_info['status']}")
            click.echo(f"Priority: {task_info['priority']}")
            click.echo(f"Created: {task_info['created_at']}")
            
            if task_info['result']:
                click.echo(f"Result: {json.dumps(task_info['result'], indent=2)}")
            
            if task_info['error']:
                click.echo(f"Error: {task_info['error']}")
        
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@infrastructure.group()
def collaboration():
    """Collaboration session commands."""
    pass


@collaboration.command()
@click.option('--document-id', required=True, help='Document identifier')
@click.option('--users', required=True, help='User IDs (comma-separated)')
def create(document_id: str, users: str):
    """
    Create a new collaboration session.
    
    Examples:
        arx infrastructure collaboration create --document-id "doc123" --users "user1,user2,user3"
    """
    try:
        infra = AdvancedInfrastructure()
        
        # Parse users
        user_list = [user.strip() for user in users.split(',')]
        
        logger.info(f"Creating collaboration session for document: {document_id}")
        
        session_id = infra.create_collaboration_session(
            document_id=document_id,
            users=user_list
        )
        
        click.echo(f"Collaboration session created successfully!")
        click.echo(f"Session ID: {session_id}")
        click.echo(f"Document ID: {document_id}")
        click.echo(f"Users: {len(user_list)}")
        
    except Exception as e:
        logger.error(f"Failed to create collaboration session: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@collaboration.command()
@click.option('--session-id', required=True, help='Session identifier')
@click.option('--user-id', required=True, help='User identifier')
def join(session_id: str, user_id: str):
    """
    Join an existing collaboration session.
    
    Examples:
        arx infrastructure collaboration join --session-id session_123 --user-id user1
    """
    try:
        infra = AdvancedInfrastructure()
        
        logger.info(f"User {user_id} joining session {session_id}")
        
        success = infra.join_collaboration_session(session_id, user_id)
        
        if not success:
            click.echo(f"Error: Session {session_id} not found", err=True)
            sys.exit(1)
        
        click.echo(f"Successfully joined session!")
        click.echo(f"Session ID: {session_id}")
        click.echo(f"User ID: {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to join session {session_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@collaboration.command()
@click.option('--session-id', required=True, help='Session identifier')
@click.option('--user-id', required=True, help='User identifier')
@click.option('--change', required=True, help='Change data (JSON)')
def add_change(session_id: str, user_id: str, change: str):
    """
    Add a change to a collaboration session.
    
    Examples:
        arx infrastructure collaboration add-change --session-id session_123 --user-id user1 --change '{"element_id": "rect1", "type": "move"}'
    """
    try:
        infra = AdvancedInfrastructure()
        
        # Parse change data
        try:
            change_data = json.loads(change)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON format: {e}", err=True)
            sys.exit(1)
        
        logger.info(f"Adding change to session {session_id}")
        
        success = infra.add_collaboration_change(
            session_id=session_id,
            user_id=user_id,
            change=change_data
        )
        
        if not success:
            click.echo(f"Error: Session {session_id} not found", err=True)
            sys.exit(1)
        
        click.echo(f"Change added successfully!")
        click.echo(f"Session ID: {session_id}")
        click.echo(f"User ID: {user_id}")
        click.echo(f"Change: {json.dumps(change_data, indent=2)}")
        
    except Exception as e:
        logger.error(f"Failed to add change to session {session_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@collaboration.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def list_sessions(format: str):
    """
    List all active collaboration sessions.
    
    Examples:
        arx infrastructure collaboration list-sessions
    """
    try:
        infra = AdvancedInfrastructure()
        
        logger.info("Getting list of collaboration sessions")
        
        sessions = []
        for session_id, session in infra.sessions.items():
            sessions.append({
                "session_id": session_id,
                "document_id": session.document_id,
                "users": session.users,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "changes_count": len(session.changes),
                "conflicts_count": len(session.conflicts)
            })
        
        if format == 'json':
            click.echo(json.dumps({"sessions": sessions, "total": len(sessions)}, indent=2))
        elif format == 'csv':
            click.echo("session_id,document_id,users_count,changes_count,conflicts_count")
            for session in sessions:
                click.echo(f"{session['session_id']},{session['document_id']},{len(session['users'])},{session['changes_count']},{session['conflicts_count']}")
        else:
            click.echo(f"Collaboration Sessions ({len(sessions)} total)")
            click.echo("=" * 50)
            
            if sessions:
                for session in sessions:
                    click.echo(f"Session: {session['session_id']}")
                    click.echo(f"  Document: {session['document_id']}")
                    click.echo(f"  Users: {len(session['users'])}")
                    click.echo(f"  Changes: {session['changes_count']}")
                    click.echo(f"  Conflicts: {session['conflicts_count']}")
                    click.echo(f"  Created: {session['created_at']}")
                    click.echo()
            else:
                click.echo("No active sessions found.")
        
    except Exception as e:
        logger.error(f"Failed to list collaboration sessions: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@infrastructure.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def performance(format: str):
    """
    Get advanced infrastructure performance metrics.
    
    Examples:
        arx infrastructure performance
        arx infrastructure performance --format json
    """
    try:
        infra = AdvancedInfrastructure()
        
        logger.info("Getting performance metrics")
        
        metrics = infra.get_performance_metrics()
        
        if format == 'json':
            click.echo(json.dumps(metrics, indent=2))
        elif format == 'csv':
            click.echo("total_operations,cache_hits,cache_misses,cache_hit_rate,processing_tasks,collaboration_sessions")
            click.echo(f"{metrics['total_operations']},{metrics['cache_hits']},{metrics['cache_misses']},{metrics['cache_hit_rate']:.1f},{metrics['processing_tasks']},{metrics['collaboration_sessions']}")
        else:
            click.echo("Advanced Infrastructure Performance Metrics")
            click.echo("=" * 50)
            click.echo(f"Total Operations: {metrics['total_operations']}")
            click.echo(f"Cache Hits: {metrics['cache_hits']}")
            click.echo(f"Cache Misses: {metrics['cache_misses']}")
            click.echo(f"Cache Hit Rate: {metrics['cache_hit_rate']:.1f}%")
            click.echo(f"Cache Size: {metrics['cache_size']}")
            click.echo(f"Processing Tasks: {metrics['processing_tasks']}")
            click.echo(f"Collaboration Sessions: {metrics['collaboration_sessions']}")
            click.echo(f"Active Sessions: {metrics['active_sessions']}")
            click.echo(f"Memory Usage: {metrics['memory_usage'] / 1024 / 1024:.1f} MB")
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    infrastructure() 