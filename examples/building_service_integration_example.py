#!/usr/bin/env python3
"""
Building Service Integration Example - HVAC System

This example demonstrates how to integrate an HVAC system into the Arxos ecosystem
using the comprehensive integration pipeline.

Author: Arxos Engineering Team
Date: 2024
"""

import sys
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.building_service_integration import BuildingServiceIntegrationPipeline


class HVACSystemIntegration:
    """
    Example HVAC system integration using the building service integration pipeline.
    
    This example shows how to integrate a typical HVAC system with:
    - Temperature and humidity sensors
    - HVAC equipment (air handlers, chillers, etc.)
    - Energy management features
    - Real-time monitoring and control
    """
    
    def __init__(self):
        self.pipeline = BuildingServiceIntegrationPipeline()
        self.hvac_config = self._create_hvac_config()
    
    def _create_hvac_config(self) -> Dict[str, Any]:
        """Create configuration for HVAC system integration"""
        return {
            "name": "Smart HVAC System v2.1",
            "version": "2.1.0",
            "description": "Advanced HVAC system with energy optimization and predictive maintenance",
            "service_type": "hvac_system",
            "integration_level": "advanced",
            "data_format": "json",
            "authentication_method": "oauth2",
            "api_endpoints": [
                "/api/v1/buildings/{building_id}/hvac",
                "/api/v1/buildings/{building_id}/hvac/systems",
                "/api/v1/buildings/{building_id}/hvac/sensors",
                "/api/v1/buildings/{building_id}/hvac/equipment",
                "/api/v1/buildings/{building_id}/hvac/events",
                "/api/v1/buildings/{building_id}/hvac/energy",
                "/api/v1/buildings/{building_id}/hvac/maintenance"
            ],
            "data_models": {
                "buildings": "Building information and HVAC zones",
                "hvac_systems": "Air handlers, chillers, boilers, etc.",
                "sensors": "Temperature, humidity, pressure, air quality sensors",
                "equipment": "HVAC equipment with status and performance data",
                "events": "System events, alarms, and notifications",
                "energy": "Energy consumption and efficiency metrics",
                "maintenance": "Maintenance schedules and work orders"
            },
            "compliance_requirements": [
                "data_privacy",  # GDPR, CCPA
                "security",      # SOC2, ISO27001
                "industry",      # ASHRAE, energy codes
                "energy_efficiency",  # Energy Star, LEED
                "air_quality"    # IAQ standards
            ],
            "performance_requirements": {
                "response_time": "< 1 second",
                "throughput": "5000+ requests/minute",
                "availability": "99.95%",
                "data_latency": "< 5 seconds",
                "concurrent_users": "500+"
            },
            "real_time_capabilities": True,
            "supported_formats": ["json", "xml", "csv"],
            "authentication_methods": ["oauth2", "api_key", "certificate"]
        }
    
    async def run_hvac_integration(self) -> Dict[str, Any]:
        """Run the complete HVAC system integration"""
        print("🚀 Starting HVAC System Integration")
        print("=" * 60)
        
        try:
            # Run the complete pipeline
            results = self.pipeline.run_complete_pipeline(self.hvac_config)
            
            # Process and display results
            await self._process_integration_results(results)
            
            return results
            
        except Exception as e:
            print(f"❌ HVAC integration failed: {e}")
            raise
    
    async def _process_integration_results(self, results: Dict[str, Any]):
        """Process and display integration results"""
        print("\n📊 Integration Results Summary")
        print("=" * 60)
        
        # Phase 1: Service Discovery
        phase1 = results.get("phases", {}).get("phase1", {})
        print(f"✅ Phase 1 - Service Discovery: {phase1.get('service_name', 'Unknown')}")
        print(f"   Integration Level: {phase1.get('integration_level', 'Unknown')}")
        print(f"   Complexity: {phase1.get('complexity_assessment', {}).get('complexity_level', 'Unknown')}")
        
        # Phase 2: SVGX Schema
        phase2 = results.get("phases", {}).get("phase2", {})
        print(f"✅ Phase 2 - SVGX Schema: Generated successfully")
        print(f"   Behavior Profiles: {len(phase2.get('behavior_profiles', {}))}")
        print(f"   Validation Rules: {len(phase2.get('validation_rules', []))}")
        
        # Phase 3: BIM Integration
        phase3 = results.get("phases", {}).get("phase3", {})
        print(f"✅ Phase 3 - BIM Integration: Configured successfully")
        print(f"   BIM Mappings: {len(phase3.get('bim_mappings', {}))}")
        print(f"   Property Sets: {len(phase3.get('property_sets', {}))}")
        
        # Phase 4: Multi-System Integration
        phase4 = results.get("phases", {}).get("phase4", {})
        print(f"✅ Phase 4 - Multi-System Integration: Configured successfully")
        print(f"   Transformation Rules: {len(phase4.get('transformation_rules', {}))}")
        print(f"   Sync Mechanisms: {len(phase4.get('sync_mechanisms', {}))}")
        
        # Phase 5: Workflow Automation
        phase5 = results.get("phases", {}).get("phase5", {})
        print(f"✅ Phase 5 - Workflow Automation: Configured successfully")
        print(f"   Workflows: {len(phase5.get('workflows', {}))}")
        print(f"   Triggers: {len(phase5.get('triggers', {}))}")
        
        # Phase 6: Testing & Validation
        phase6 = results.get("phases", {}).get("phase6", {})
        print(f"✅ Phase 6 - Testing & Validation: {phase6.get('overall_status', 'Unknown')}")
        print(f"   Integration Tests: {phase6.get('integration_tests', {}).get('status', 'Unknown')}")
        print(f"   Performance Tests: {phase6.get('performance_tests', {}).get('status', 'Unknown')}")
        print(f"   Compliance Tests: {phase6.get('compliance_tests', {}).get('status', 'Unknown')}")
        
        # Phase 7: Deployment & Monitoring
        phase7 = results.get("phases", {}).get("phase7", {})
        print(f"✅ Phase 7 - Deployment & Monitoring: Configured successfully")
        print(f"   Monitoring Config: {len(phase7.get('monitoring_config', {}))}")
        print(f"   Alerting Rules: {len(phase7.get('alerting_rules', []))}")
        
        # Overall Status
        print(f"\n🎯 Overall Status: {results.get('overall_status', 'Unknown')}")
        print(f"⏱️  Completion Time: {results.get('completion_timestamp', 'Unknown')}")
        
        # Next Steps
        next_steps = results.get('next_steps', [])
        if next_steps:
            print(f"\n📋 Next Steps:")
            for i, step in enumerate(next_steps, 1):
                print(f"   {i}. {step}")
    
    def create_hvac_svgx_schema(self) -> Dict[str, Any]:
        """Create SVGX schema specific to HVAC systems"""
        return {
            "type": "object",
            "properties": {
                "hvac_system": {
                    "type": "object",
                    "properties": {
                        "system_id": {"type": "string", "format": "uuid"},
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": ["air_handler", "chiller", "boiler", "vav"]},
                        "status": {"type": "string", "enum": ["active", "inactive", "maintenance", "error"]},
                        "temperature_setpoint": {"type": "number", "unit": "°C"},
                        "humidity_setpoint": {"type": "number", "unit": "%"},
                        "energy_consumption": {"type": "number", "unit": "kWh"},
                        "efficiency": {"type": "number", "unit": "%"},
                        "location": {
                            "type": "object",
                            "properties": {
                                "building_id": {"type": "string"},
                                "floor": {"type": "string"},
                                "zone": {"type": "string"},
                                "coordinates": {
                                    "type": "object",
                                    "properties": {
                                        "x": {"type": "number"},
                                        "y": {"type": "number"},
                                        "z": {"type": "number"}
                                    }
                                }
                            }
                        },
                        "sensors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "sensor_id": {"type": "string"},
                                    "type": {"type": "string", "enum": ["temperature", "humidity", "pressure", "air_quality"]},
                                    "value": {"type": "number"},
                                    "unit": {"type": "string"},
                                    "timestamp": {"type": "string", "format": "date-time"}
                                }
                            }
                        },
                        "maintenance": {
                            "type": "object",
                            "properties": {
                                "last_maintenance": {"type": "string", "format": "date-time"},
                                "next_maintenance": {"type": "string", "format": "date-time"},
                                "maintenance_status": {"type": "string", "enum": ["scheduled", "overdue", "completed"]},
                                "maintenance_notes": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    
    def create_hvac_behavior_profiles(self) -> Dict[str, Any]:
        """Create behavior profiles for HVAC systems"""
        return {
            "hvac_system": {
                "type": "infrastructure",
                "category": "hvac",
                "behaviors": {
                    "temperature_control": {
                        "description": "Maintain temperature within setpoint range",
                        "parameters": {
                            "setpoint": {"type": "number", "unit": "°C"},
                            "tolerance": {"type": "number", "unit": "°C", "default": 1.0}
                        },
                        "actions": [
                            "adjust_heating",
                            "adjust_cooling",
                            "adjust_fan_speed"
                        ]
                    },
                    "humidity_control": {
                        "description": "Maintain humidity within acceptable range",
                        "parameters": {
                            "setpoint": {"type": "number", "unit": "%"},
                            "tolerance": {"type": "number", "unit": "%", "default": 5.0}
                        },
                        "actions": [
                            "adjust_humidification",
                            "adjust_dehumidification"
                        ]
                    },
                    "energy_optimization": {
                        "description": "Optimize energy consumption based on occupancy and conditions",
                        "parameters": {
                            "occupancy_threshold": {"type": "number", "default": 0.1},
                            "energy_savings_target": {"type": "number", "unit": "%", "default": 15.0}
                        },
                        "actions": [
                            "reduce_setpoints",
                            "adjust_schedules",
                            "enable_eco_mode"
                        ]
                    },
                    "predictive_maintenance": {
                        "description": "Predict maintenance needs based on system performance",
                        "parameters": {
                            "maintenance_threshold": {"type": "number", "unit": "days", "default": 30},
                            "performance_threshold": {"type": "number", "unit": "%", "default": 85.0}
                        },
                        "actions": [
                            "schedule_maintenance",
                            "generate_work_order",
                            "send_alert"
                        ]
                    },
                    "air_quality_monitoring": {
                        "description": "Monitor and maintain air quality standards",
                        "parameters": {
                            "co2_threshold": {"type": "number", "unit": "ppm", "default": 1000},
                            "pm25_threshold": {"type": "number", "unit": "μg/m³", "default": 12}
                        },
                        "actions": [
                            "increase_ventilation",
                            "activate_air_purification",
                            "send_air_quality_alert"
                        ]
                    }
                }
            }
        }
    
    def create_hvac_workflows(self) -> Dict[str, Any]:
        """Create automation workflows for HVAC systems"""
        return {
            "hvac_daily_optimization": {
                "trigger": "schedule",
                "frequency": "daily",
                "time": "06:00",
                "steps": [
                    "fetch_weather_forecast",
                    "fetch_occupancy_schedule",
                    "optimize_temperature_setpoints",
                    "adjust_ventilation_rates",
                    "update_energy_forecast"
                ]
            },
            "hvac_maintenance_alert": {
                "trigger": "event",
                "conditions": ["maintenance_due", "performance_degraded"],
                "steps": [
                    "check_maintenance_schedule",
                    "generate_work_order",
                    "notify_facility_manager",
                    "update_svgx_model"
                ]
            },
            "hvac_energy_optimization": {
                "trigger": "event",
                "conditions": ["high_energy_consumption", "occupancy_low"],
                "steps": [
                    "analyze_energy_patterns",
                    "adjust_operating_parameters",
                    "enable_energy_saving_mode",
                    "log_optimization_actions"
                ]
            },
            "hvac_air_quality_management": {
                "trigger": "event",
                "conditions": ["air_quality_poor", "co2_high"],
                "steps": [
                    "increase_fresh_air_intake",
                    "activate_air_purification",
                    "notify_building_occupants",
                    "log_air_quality_incident"
                ]
            }
        }


async def main():
    """Main function to run the HVAC integration example"""
    print("🏢 HVAC System Integration Example")
    print("=" * 60)
    
    # Create HVAC integration
    hvac_integration = HVACSystemIntegration()
    
    try:
        # Run the integration
        results = await hvac_integration.run_hvac_integration()
        
        # Save results
        with open("hvac_integration_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ HVAC integration completed successfully!")
        print(f"📊 Results saved to: hvac_integration_results.json")
        
        # Display additional HVAC-specific information
        print(f"\n🔧 HVAC-Specific Features:")
        print(f"   - Temperature and humidity control")
        print(f"   - Energy optimization algorithms")
        print(f"   - Predictive maintenance scheduling")
        print(f"   - Air quality monitoring")
        print(f"   - Real-time performance tracking")
        
    except Exception as e:
        print(f"❌ HVAC integration failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # Run the HVAC integration example
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 