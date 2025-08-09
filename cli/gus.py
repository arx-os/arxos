#!/usr/bin/env python3
"""
GUS (General Utility Script) - Command line interface for Arxos Platform utilities.

This script provides command-line access to common utility functions
from the import the
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
import click
import structlog

from core.shared.config import get_settings

logger = structlog.get_logger()


class GUSCLI:
    """CLI interface for GUS agent"""

    def __init__(self):
        """
        Initialize the GUS CLI.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self.settings = get_settings()
        self.gus_api_url = self.settings.gus_api_url or "http://localhost:9001"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def query(self, query: str, user_id: str = "cli_user") -> Dict[str, Any]:
        """Send a query to GUS agent"""
        try:
            response = await self.client.post(
                f"{self.gus_api_url}/api/v1/query",
                json={
                    "query": query,
                    "user_id": user_id,
                    "context": {"source": "cli"}
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logger.error(f"Error querying GUS: {e}")
            return {"error": str(e)}

    async def get_knowledge(self, topic: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Query knowledge base"""
        try:
            response = await self.client.post(
                f"{self.gus_api_url}/api/v1/knowledge",
                json={
                    "topic": topic,
                    "context": context or {}
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logger.error(f"Error querying knowledge: {e}")
            return {"error": str(e)}

    async def execute_task(self, task: str, parameters: Dict[str, Any], user_id: str = "cli_user") -> Dict[str, Any]:
        """Execute a specific task"""
        try:
            response = await self.client.post(
                f"{self.gus_api_url}/api/v1/task",
                json={
                    "task": task,
                    "parameters": parameters,
                    "user_id": user_id
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Check GUS service health"""
        try:
            response = await self.client.get(f"{self.gus_api_url}/health")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logger.error(f"Error checking health: {e}")
            return {"error": str(e)}

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--api-url', default=None, help='GUS API URL')
@click.pass_context
def gus(ctx, debug: bool, api_url: Optional[str]):
    """GUS (General User Support) Agent CLI"

    Interact with the GUS AI agent for CAD assistance and knowledge queries.
    """
    # Configure logging
    if debug:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    # Initialize GUS CLI
    ctx.obj = GUSCLI()
    if api_url:
        ctx.obj.gus_api_url = api_url


@gus.command()
@click.argument('query', nargs=-1)
@click.option('--user-id', default='cli_user', help='User ID for the query')
@click.option('--format', 'output_format', default='text',
              type=click.Choice(['text', 'json']), help='Output format')
@click.pass_obj
def query(gus_cli: GUSCLI, query: tuple, user_id: str, output_format: str):
    """Send a natural language query to GUS agent"""
    if not query:
        click.echo("Error: Query is required", err=True)
        sys.exit(1)

    query_text = " ".join(query)

    async def run_query():
        result = await gus_cli.query(query_text, user_id)
        await gus_cli.close()
        return result

    result = asyncio.run(run_query())

    if "error" in result:
        click.echo(f"Error: {result['error']}", err=True)
        sys.exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Response: {result.get('message', 'No response')}")
        if result.get('confidence'):
            click.echo(f"Confidence: {result['confidence']:.2f}")
        if result.get('intent'):
            click.echo(f"Intent: {result['intent']}")


@gus.command()
@click.argument('topic')
@click.option('--format', 'output_format', default='text',
              type=click.Choice(['text', 'json']), help='Output format')
@click.pass_obj
def knowledge(gus_cli: GUSCLI, topic: str, output_format: str):
    """Query the knowledge base for a specific topic"""

    async def run_knowledge_query():
        result = await gus_cli.get_knowledge(topic)
        await gus_cli.close()
        return result

    result = asyncio.run(run_knowledge_query())

    if "error" in result:
        click.echo(f"Error: {result['error']}", err=True)
        sys.exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Knowledge: {result.get('message', 'No information found')}")
        if result.get('confidence'):
            click.echo(f"Confidence: {result['confidence']:.2f}")


@gus.command()
@click.argument('task')
@click.option('--parameters', '-p', multiple=True, help='Task parameters (key=value)')
@click.option('--user-id', default='cli_user', help='User ID for the task')
@click.option('--format', 'output_format', default='text',
              type=click.Choice(['text', 'json']), help='Output format')
@click.pass_obj
def task(gus_cli: GUSCLI, task: str, parameters: tuple, user_id: str, output_format: str):
    """Execute a specific task"""

    # Parse parameters
    task_params = {}
    for param in parameters:
        if '=' in param:
            key, value = param.split('=', 1)
            task_params[key] = value
        else:
            task_params[param] = True

    async def run_task():
        result = await gus_cli.execute_task(task, task_params, user_id)
        await gus_cli.close()
        return result

    result = asyncio.run(run_task())

    if "error" in result:
        click.echo(f"Error: {result['error']}", err=True)
        sys.exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Task Result: {result.get('message', 'No result')}")
        if result.get('actions'):
            click.echo(f"Actions: {len(result['actions'])} performed")


@gus.command()
@click.option('--format', 'output_format', default='text',
              type=click.Choice(['text', 'json']), help='Output format')
@click.pass_obj
def health(gus_cli: GUSCLI, output_format: str):
    """Check GUS service health"""

    async def run_health_check():
        result = await gus_cli.health_check()
        await gus_cli.close()
        return result

    result = asyncio.run(run_health_check())

    if "error" in result:
        click.echo(f"Error: {result['error']}", err=True)
        sys.exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Status: {result.get('status', 'unknown')}")
        click.echo(f"Service: {result.get('service', 'unknown')}")
        click.echo(f"Version: {result.get('version', 'unknown')}")


@gus.command()
@click.pass_obj
def help_topics(gus_cli: GUSCLI):
    """Show available help topics"""
    topics = [
        "electrical_outlets",
        "structural_requirements",
        "architectural_requirements",
        "electrical_systems",
        "hvac_energy",
        "life_safety",
        "accessibility"
    ]

    click.echo("Available knowledge topics:")
    for topic in topics:
        click.echo(f"  - {topic}")

    click.echo("\nUse 'arx gus knowledge <topic>' to query specific topics.")


if __name__ == "__main__":
    gus()
