#!/usr/bin/env python3
"""
MCP Grafana Dashboard Configurations

This module provides Grafana dashboard configurations specifically for MCP service monitoring,
including performance metrics, validation statistics, and business intelligence.
"""

import json
from typing import Dict, List, Any
from datetime import datetime


class MCPDashboardGenerator:
    """Generates Grafana dashboard configurations for MCP service monitoring"""

    def __init__(self):
        self.dashboard_templates = {
            "mcp_performance": self._create_performance_dashboard,
            "mcp_validation": self._create_validation_dashboard,
            "mcp_business": self._create_business_dashboard,
            "mcp_system": self._create_system_dashboard,
        }

    def _create_performance_dashboard(self) -> Dict[str, Any]:
        """Create MCP Performance Dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "MCP Performance Dashboard",
                "tags": ["mcp", "performance", "monitoring"],
                "style": "dark",
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "API Response Time",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(mcp_api_request_duration_seconds_bucket[5m]))",
                                "legendFormat": "95th Percentile",
                            },
                            {
                                "expr": "histogram_quantile(0.50, rate(mcp_api_request_duration_seconds_bucket[5m]))",
                                "legendFormat": "50th Percentile",
                            },
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "s",
                                "min": 0,
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    },
                    {
                        "id": 2,
                        "title": "API Request Rate",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "rate(mcp_api_requests_total[5m])",
                                "legendFormat": "Requests/sec",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "reqps",
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    },
                    {
                        "id": 3,
                        "title": "Validation Duration",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(mcp_validation_duration_seconds_bucket[5m]))",
                                "legendFormat": "95th Percentile",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "s",
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    },
                    {
                        "id": 4,
                        "title": "Cache Hit Ratio",
                        "type": "gauge",
                        "targets": [
                            {"expr": "mcp_cache_hit_ratio", "legendFormat": "Hit Ratio"}
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "unit": "percent",
                                "min": 0,
                                "max": 100,
                                "thresholds": {
                                    "steps": [
                                        {"color": "red", "value": None},
                                        {"color": "yellow", "value": 70},
                                        {"color": "green", "value": 90},
                                    ]
                                },
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    },
                ],
            }
        }

    def _create_validation_dashboard(self) -> Dict[str, Any]:
        """Create MCP Validation Dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "MCP Validation Dashboard",
                "tags": ["mcp", "validation", "compliance"],
                "style": "dark",
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Validation Requests",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "rate(mcp_validation_requests_total[5m])",
                                "legendFormat": "Requests/sec",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "reqps",
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    },
                    {
                        "id": 2,
                        "title": "Violations Found",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "rate(mcp_violations_found_total[5m])",
                                "legendFormat": "Violations/sec",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "short",
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    },
                    {
                        "id": 3,
                        "title": "Compliance Scores",
                        "type": "heatmap",
                        "targets": [
                            {
                                "expr": "mcp_compliance_scores",
                                "legendFormat": "Compliance Score",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "percent",
                                "min": 0,
                                "max": 100,
                            }
                        },
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
                    },
                    {
                        "id": 4,
                        "title": "Rules Checked",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(rate(mcp_rules_checked_total[5m]))",
                                "legendFormat": "Rules/sec",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "short",
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                    },
                    {
                        "id": 5,
                        "title": "Warnings Found",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "rate(mcp_warnings_found_total[5m])",
                                "legendFormat": "Warnings/sec",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "short",
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                    },
                ],
            }
        }

    def _create_business_dashboard(self) -> Dict[str, Any]:
        """Create MCP Business Intelligence Dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "MCP Business Intelligence",
                "tags": ["mcp", "business", "analytics"],
                "style": "dark",
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Active Users",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(mcp_active_users)",
                                "legendFormat": "Active Users",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "short",
                            }
                        },
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                    },
                    {
                        "id": 2,
                        "title": "Login Success Rate",
                        "type": "gauge",
                        "targets": [
                            {
                                "expr": 'rate(mcp_login_attempts_total{result="success"}[5m]) / rate(mcp_login_attempts_total[5m]) * 100',
                                "legendFormat": "Success Rate",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "unit": "percent",
                                "min": 0,
                                "max": 100,
                                "thresholds": {
                                    "steps": [
                                        {"color": "red", "value": None},
                                        {"color": "yellow", "value": 80},
                                        {"color": "green", "value": 95},
                                    ]
                                },
                            }
                        },
                        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                    },
                    {
                        "id": 3,
                        "title": "Jurisdiction Matches",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "rate(mcp_jurisdiction_matches_total[5m])",
                                "legendFormat": "Matches/sec",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "short",
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    },
                    {
                        "id": 4,
                        "title": "MCP Files Loaded",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "rate(mcp_files_loaded_total[5m])",
                                "legendFormat": "Files/sec",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "short",
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    },
                ],
            }
        }

    def _create_system_dashboard(self) -> Dict[str, Any]:
        """Create MCP System Health Dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "MCP System Health",
                "tags": ["mcp", "system", "health"],
                "style": "dark",
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "System Uptime",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "mcp_system_uptime_seconds",
                                "legendFormat": "Uptime",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "s",
                            }
                        },
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                    },
                    {
                        "id": 2,
                        "title": "Memory Usage",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "mcp_system_memory_bytes",
                                "legendFormat": "Memory Usage",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "bytes",
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 6, "y": 0},
                    },
                    {
                        "id": 3,
                        "title": "CPU Usage",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "mcp_system_cpu_percent",
                                "legendFormat": "CPU Usage",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "percent",
                            }
                        },
                        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
                    },
                    {
                        "id": 4,
                        "title": "Error Rate",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "rate(mcp_errors_total[5m])",
                                "legendFormat": "Errors/sec",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "short",
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    },
                    {
                        "id": 5,
                        "title": "WebSocket Connections",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "rate(mcp_websocket_connections_total[5m])",
                                "legendFormat": "Connections/sec",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "unit": "short",
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    },
                ],
            }
        }

    def generate_all_dashboards(self) -> Dict[str, Any]:
        """Generate all MCP dashboards"""
        dashboards = {}
        for name, generator in self.dashboard_templates.items():
            dashboards[name] = generator()
        return dashboards

    def save_dashboards(self, output_file: str = "mcp_grafana_dashboards.json"):
        """Save all dashboards to a JSON file"""
        dashboards = self.generate_all_dashboards()

        with open(output_file, "w") as f:
            json.dump(dashboards, f, indent=2)

        print(f"✅ MCP Grafana dashboards saved to {output_file}")
        return dashboards


def main():
    """Generate MCP Grafana dashboards"""
    generator = MCPDashboardGenerator()
    dashboards = generator.save_dashboards()

    print(f"📊 Generated {len(dashboards)} MCP dashboards:")
    for name in dashboards.keys():
        print(f"  - {name}")

    print("\n🎯 Dashboard types:")
    print("  - Performance: API response times, request rates, cache performance")
    print("  - Validation: Compliance scores, violations, rules checked")
    print("  - Business: User activity, jurisdiction matches, file operations")
    print("  - System: Uptime, memory, CPU, error rates")


if __name__ == "__main__":
    main()
