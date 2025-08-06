"""
MCP-Engineering Bridge Module

Bridge service that orchestrates the integration between MCP intelligence and engineering engines.
"""

from .bridge_service import MCPEngineeringBridge, BridgeConfig

__all__ = ["MCPEngineeringBridge", "BridgeConfig"]
