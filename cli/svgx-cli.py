#!/usr/bin/env python3
"""
SVGX Engine CLI Tool

A comprehensive command-line interface for managing the SVGX Engine system,
including user management, canvas operations, and system monitoring.
"""

import argparse
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

# Configure rich console
console = Console()

class SVGXCLI:
    """SVGX Engine CLI client."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the SVGX CLI.

        Args:
            base_url: Base URL for the SVGX Engine

        Returns:
            None

        Raises:
            None
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None

        # Load token from environment or file
        self.token = os.getenv('SVGX_TOKEN') or self._load_token()
        if self.token:
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})

    def _load_token(self) -> Optional[str]:
        """Load token from config file."""
        config_file = os.path.expanduser('~/.svgx/config.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('token')
            except Exception:
                pass
        return None

    def _save_token(self, token: str):
        """Save token to config file."""
        config_dir = os.path.expanduser('~/.svgx')
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, 'config.json')

        config = {'token': token, 'updated_at': datetime.now().isoformat()}
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def login(self, username: str, password: str) -> bool:
        """Login to SVGX Engine."""
        try:
            response = self.session.post(f"{self.base_url}/auth/login", json={
                'username': username,
                'password': password
            })

            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                self._save_token(self.token)
                return True
            else:
                console.print(f"[red]Login failed: {response.text}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]Login error: {e}[/red]")
            return False

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""
        try:
            response = self.session.get(f"{self.base_url}/health/summary/")
            return response.json()
        except Exception as e:
            return {'error': str(e)}

    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        try:
            response = self.session.get(f"{self.base_url}/metrics/")
            return response.json()
        except Exception as e:
            return {'error': str(e)}

    def list_canvases(self) -> List[Dict[str, Any]]:
        """List all canvases."""
        try:
            response = self.session.get(f"{self.base_url}/runtime/canvases/")
            return response.json().get('canvases', [])
        except Exception as e:
            console.print(f"[red]Error listing canvases: {e}[/red]")
            return []

    def create_canvas(self, name: str, description: str = "") -> Optional[Dict[str, Any]]:
        """Create a new canvas."""
        try:
            response = self.session.post(f"{self.base_url}/runtime/canvases/", json={
                'name': name,
                'description': description
            })

            if response.status_code == 201:
                return response.json()
            else:
                console.print(f"[red]Failed to create canvas: {response.text}[/red]")
                return None

        except Exception as e:
            console.print(f"[red]Error creating canvas: {e}[/red]")
            return None

    def delete_canvas(self, canvas_id: str) -> bool:
        """Delete a canvas."""
        try:
            response = self.session.delete(f"{self.base_url}/runtime/canvases/{canvas_id}")
            return response.status_code == 204
        except Exception as e:
            console.print(f"[red]Error deleting canvas: {e}[/red]")
            return False

    def get_canvas(self, canvas_id: str) -> Optional[Dict[str, Any]]:
        """Get canvas details."""
        try:
            response = self.session.get(f"{self.base_url}/runtime/canvases/{canvas_id}")
            return response.json()
        except Exception as e:
            console.print(f"[red]Error getting canvas: {e}[/red]")
            return None

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users (admin only)."""
        try:
            response = self.session.get(f"{self.base_url}/admin/users/")
            return response.json().get('users', [])
        except Exception as e:
            console.print(f"[red]Error listing users: {e}[/red]")
            return []

    def create_user(self, username: str, email: str, password: str, role: str = "viewer") -> Optional[Dict[str, Any]]:
        """Create a new user (admin only)."""
        try:
            response = self.session.post(f"{self.base_url}/admin/users/", json={
                'username': username,
                'email': email,
                'password': password,
                'role': role
            })

            if response.status_code == 201:
                return response.json()
            else:
                console.print(f"[red]Failed to create user: {response.text}[/red]")
                return None

        except Exception as e:
            console.print(f"[red]Error creating user: {e}[/red]")
            return None

    def get_backups(self) -> List[Dict[str, Any]]:
        """List system backups."""
        try:
            response = self.session.get(f"{self.base_url}/state/backups/")
            return response.json().get('backups', [])
        except Exception as e:
            console.print(f"[red]Error listing backups: {e}[/red]")
            return []

    def create_backup(self, backup_type: str = "full") -> Optional[Dict[str, Any]]:
        """Create a system backup."""
        try:
            response = self.session.post(f"{self.base_url}/state/backup/", json={
                'backup_type': backup_type
            })

            if response.status_code == 200:
                return response.json()
            else:
                console.print(f"[red]Failed to create backup: {response.text}[/red]")
                return None

        except Exception as e:
            console.print(f"[red]Error creating backup: {e}[/red]")
            return None

    def get_instances(self) -> List[Dict[str, Any]]:
        """List all instances."""
        try:
            response = self.session.get(f"{self.base_url}/scaling/instances/")
            return response.json().get('instances', [])
        except Exception as e:
            console.print(f"[red]Error listing instances: {e}[/red]")
            return []

    def get_alerts(self) -> List[Dict[str, Any]]:
        """List active alerts."""
        try:
            response = self.session.get(f"{self.base_url}/health/alerts/")
            return response.json().get('alerts', [])
        except Exception as e:
            console.print(f"[red]Error listing alerts: {e}[/red]")
            return []


@click.group()
@click.option('--url', default='http://localhost:8000', help='SVGX Engine API URL')
@click.pass_context
def cli(ctx, url):
    """SVGX Engine CLI Tool"""
    ctx.ensure_object(dict)
    ctx.obj['cli'] = SVGXCLI(url)


@cli.command()
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, help='Password')
@click.pass_context
def login(ctx, username, password):
    """Login to SVGX Engine"""
    cli_client = ctx.obj['cli']

    with console.status("[bold green]Logging in..."):
        if cli_client.login(username, password):
            console.print("[green]Login successful![/green]")
        else:
            console.print("[red]Login failed![/red]")
            sys.exit(1)


@cli.command()
@click.pass_context
def health(ctx):
    """Show system health status"""
    cli_client = ctx.obj['cli']

    with console.status("[bold green]Checking system health..."):
        health_data = cli_client.get_system_health()

    if 'error' in health_data:
        console.print(f"[red]Error: {health_data['error']}[/red]")
        return

    # Create health table
    table = Table(title="System Health")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    for key, value in health_data.items():
        if key != 'metrics':
            table.add_row(key.replace('_', ' ').title(), str(value))

    console.print(table)

    # Show metrics if available
    if 'metrics' in health_data:
        metrics = health_data['metrics']
        if metrics:
            metrics_table = Table(title="System Metrics")
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="yellow")

            for key, value in metrics.items():
                metrics_table.add_row(key.replace('_', ' ').title(), str(value))

            console.print(metrics_table)


@cli.command()
@click.pass_context
def metrics(ctx):
    """Show system metrics"""
    cli_client = ctx.obj['cli']

    with console.status("[bold green]Fetching metrics..."):
        metrics_data = cli_client.get_metrics()

    if 'error' in metrics_data:
        console.print(f"[red]Error: {metrics_data['error']}[/red]")
        return

    # Create metrics table
    table = Table(title="System Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    for key, value in metrics_data.items():
        table.add_row(key.replace('_', ' ').title(), str(value))

    console.print(table)


@cli.group()
def canvas(ctx):
    """Canvas management commands"""
    pass


@canvas.command('list')
@click.pass_context
def list_canvases(ctx):
    """List all canvases"""
    cli_client = ctx.obj['cli']

    with console.status("[bold green]Fetching canvases..."):
        canvases = cli_client.list_canvases()

    if not canvases:
        console.print("[yellow]No canvases found[/yellow]")
        return

    # Create canvas table
    table = Table(title="Canvases")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Created", style="yellow")
    table.add_column("Updated", style="yellow")
    table.add_column("Objects", style="blue")

    for canvas in canvases:
        table.add_row(
            canvas.get('id', 'N/A'),
            canvas.get('name', 'N/A'),
            canvas.get('created_at', 'N/A')[:19],
            canvas.get('updated_at', 'N/A')[:19],
            str(len(canvas.get('objects', [])))
        )

    console.print(table)


@canvas.command('create')
@click.option('--name', prompt=True, help='Canvas name')
@click.option('--description', help='Canvas description')
@click.pass_context
def create_canvas(ctx, name, description):
    """Create a new canvas"""
    cli_client = ctx.obj['cli']

    with console.status("[bold green]Creating canvas..."):
        canvas = cli_client.create_canvas(name, description or "")

    if canvas:
        console.print(f"[green]Canvas created successfully![/green]")
        console.print(f"ID: {canvas.get('id')}")
        console.print(f"Name: {canvas.get('name')}")
    else:
        console.print("[red]Failed to create canvas[/red]")


@canvas.command('delete')
@click.argument('canvas_id')
@click.pass_context
def delete_canvas(ctx, canvas_id):
    """Delete a canvas"""
    cli_client = ctx.obj['cli']

    with console.status("[bold green]Deleting canvas..."):
        success = cli_client.delete_canvas(canvas_id)

    if success:
        console.print(f"[green]Canvas {canvas_id} deleted successfully![/green]")
    else:
        console.print(f"[red]Failed to delete canvas {canvas_id}[/red]")


@canvas.command('show')
@click.argument('canvas_id')
@click.pass_context
def show_canvas(ctx, canvas_id):
    """Show canvas details"""
    cli_client = ctx.obj['cli']

    with console.status("[bold green]Fetching canvas details..."):
        canvas = cli_client.get_canvas(canvas_id)

    if not canvas:
        console.print(f"[red]Canvas {canvas_id} not found[/red]")
        return

    # Create canvas details table
    table = Table(title=f"Canvas: {canvas.get('name', 'N/A')}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    for key, value in canvas.items():
        if key != 'objects':
            table.add_row(key.replace('_', ' ').title(), str(value))

    console.print(table)

    # Show objects count
    objects = canvas.get('objects', [])
    console.print(f"\n[bold]Objects: {len(objects)}[/bold]")


@cli.group()
def user(ctx):
    """User management commands (admin only)"""
    pass


@user.command('list')
@click.pass_context
def list_users(ctx):
    """List all users"""
    cli_client = ctx.obj['cli']

    with console.status("[bold green]Fetching users..."):
        users = cli_client.list_users()

    if not users:
        console.print("[yellow]No users found[/yellow]")
        return

    # Create users table
    table = Table(title="Users")
    table.add_column("ID", style="cyan")
    table.add_column("Username", style="green")
    table.add_column("Email", style="yellow")
    table.add_column("Role", style="blue")
    table.add_column("Created", style="magenta")

    for user in users:
        table.add_row(
            user.get('user_id', 'N/A'),
            user.get('username', 'N/A'),
            user.get('email', 'N/A'),
            user.get('role', 'N/A'),
            user.get('created_at', 'N/A')[:19]
        )

    console.print(table)


@user.command('create')
@click.option('--username', prompt=True, help='Username')
@click.option('--email', prompt=True, help='Email')
@click.option('--password', prompt=True, hide_input=True, help='Password')
@click.option('--role', default='viewer', type=click.Choice(['admin', 'editor', 'viewer']), help='User role')
@click.pass_context
def create_user(ctx, username, email, password, role):
    """Create a new user"""
    cli_client = ctx.obj['cli']

    with console.status("[bold green]Creating user..."):
        user = cli_client.create_user(username, email, password, role)

    if user:
        console.print(f"[green]User created successfully![/green]")
        console.print(f"Username: {user.get('username')}")
        console.print(f"Email: {user.get('email')}")
        console.print(f"Role: {user.get('role')}")
    else:
        console.print("[red]Failed to create user[/red]")


@cli.group()
def backup(ctx):
    """Backup management commands"""
    pass


@backup.command('list')
@click.pass_context
def list_backups(ctx):
    """List system backups"""
    cli_client = ctx.obj['cli']

    with console.status("[bold green]Fetching backups..."):
        backups = cli_client.get_backups()

    if not backups:
        console.print("[yellow]No backups found[/yellow]")
        return

    # Create backups table
    table = Table(title="System Backups")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Created", style="yellow")
    table.add_column("Size", style="blue")
    table.add_column("Objects", style="magenta")

    for backup in backups:
        size_mb = backup.get('size_bytes', 0) / (1024 * 1024)
        table.add_row(
            backup.get('backup_id', 'N/A'),
            backup.get('state_type', 'N/A'),
            backup.get('timestamp', 'N/A')[:19],
            f"{size_mb:.2f} MB",
            str(backup.get('entry_count', 0))
        )

    console.print(table)


@backup.command('create')
@click.option('--type', default='full', type=click.Choice(['full', 'incremental', 'differential']), help='Backup type')
@click.pass_context
def create_backup(ctx, type):
    """Create a system backup"""
    cli_client = ctx.obj['cli']

    with console.status("[bold green]Creating backup..."):
        backup = cli_client.create_backup(type)

    if backup:
        console.print(f"[green]Backup created successfully![/green]")
        console.print(f"ID: {backup.get('backup_id')}")
        console.print(f"Type: {backup.get('state_type')}")
        console.print(f"Objects: {backup.get('entry_count')}")
        console.print(f"Size: {backup.get('size_bytes', 0) / (1024 * 1024):.2f} MB")
    else:
        console.print("[red]Failed to create backup[/red]")


@cli.group()
def system(ctx):
    """System management commands"""
    pass


@system.command('instances')
@click.pass_context
def list_instances(ctx):
    """List all instances"""
    cli_client = ctx.obj['cli']

    with console.status("[bold green]Fetching instances..."):
        instances = cli_client.get_instances()

    if not instances:
        console.print("[yellow]No instances found[/yellow]")
        return

    # Create instances table
    table = Table(title="System Instances")
    table.add_column("ID", style="cyan")
    table.add_column("Host", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Connections", style="blue")
    table.add_column("CPU", style="magenta")
    table.add_column("Memory", style="red")

    for instance in instances:
        status_color = "green" if instance.get('status') == 'healthy' else "red"
        table.add_row(
            instance.get('instance_id', 'N/A'),
            f"{instance.get('host', 'N/A')}:{instance.get('port', 'N/A')}",
            f"[{status_color}]{instance.get('status', 'N/A')}[/{status_color}]",
            f"{instance.get('current_connections', 0)}/{instance.get('max_connections', 0)}",
            f"{instance.get('cpu_usage', 0):.1f}%",
            f"{instance.get('memory_usage', 0):.1f}%"
        )

    console.print(table)


@system.command('alerts')
@click.pass_context
def list_alerts(ctx):
    """List active alerts"""
    cli_client = ctx.obj['cli']

    with console.status("[bold green]Fetching alerts..."):
        alerts = cli_client.get_alerts()

    if not alerts:
        console.print("[green]No active alerts[/green]")
        return

    # Create alerts table
    table = Table(title="Active Alerts")
    table.add_column("ID", style="cyan")
    table.add_column("Level", style="red")
    table.add_column("Message", style="green")
    table.add_column("Metric", style="yellow")
    table.add_column("Value", style="blue")
    table.add_column("Time", style="magenta")

    for alert in alerts:
        level_color = "red" if alert.get('level') == 'critical' else "yellow"
        table.add_row(
            alert.get('alert_id', 'N/A'),
            f"[{level_color}]{alert.get('level', 'N/A')}[/{level_color}]",
            alert.get('message', 'N/A'),
            alert.get('metric_name', 'N/A'),
            str(alert.get('current_value', 'N/A')),
            alert.get('timestamp', 'N/A')[:19]
        )

    console.print(table)


if __name__ == '__main__':
    cli()
