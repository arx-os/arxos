"""
MCP-Engineering Integration Service

Integration service that connects MCP intelligence layer with engineering logic engines.
Provides real-time engineering validation, code compliance checking, and intelligent suggestions.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

from .bridge.bridge_service import MCPEngineeringBridge, BridgeConfig

__all__ = ["MCPEngineeringBridge", "BridgeConfig"]
