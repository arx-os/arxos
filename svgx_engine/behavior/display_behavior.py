"""
Display Behavior Profile for Audiovisual System

This module defines the behavior patterns and logic for AV display devices
including LED displays, LCD panels, and video walls.
"""

import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class DisplayState:
    """Represents the current state of a display device"""

    power_state: str = "off"  # off, on, standby
    input_source: str = "none"
    brightness: int = 50  # 0-100
    volume: int = 50  # 0-100
    resolution: str = "1920x1080"
    refresh_rate: int = 60
    temperature: float = 25.0
    uptime_hours: float = 0.0
    error_count: int = 0
    last_maintenance: Optional[str] = None


class DisplayBehavior:
    """
    Behavior profile for AV display devices

    Handles power management, input switching, calibration,
    and performance monitoring for display devices.
    """

    def __init__(self, display_id: str, properties: Dict[str, Any]):
        """
        Initialize display behavior

        Args:
            display_id: Unique identifier for the display
            properties: Display properties from schema
        """
        self.display_id = display_id
        self.properties = properties
        self.state = DisplayState()
        self.input_sources = ["HDMI1", "HDMI2", "DisplayPort", "VGA", "USB-C"]
        self.valid_resolutions = ["1920x1080", "3840x2160", "1280x720"]
        self.max_brightness = properties.get("brightness", 400)
        self.contrast_ratio = properties.get("contrast_ratio", "3000:1")
        self.refresh_rate = properties.get("refresh_rate", 60)

        # Performance tracking
        self.start_time = time.time()
        self.operation_log = []

    def power_on(self) -> Dict[str, Any]:
        """
        Power on the display device

        Returns:
            Dict containing operation result and new state
        """
        try:
            if self.state.power_state == "off":
                self.state.power_state = "on"
                self.state.uptime_hours = 0.0
                self.log_operation("power_on", "success")

                return {
                    "success": True,
                    "operation": "power_on",
                    "state": "on",
                    "message": f"Display {self.display_id} powered on successfully",
                    "timestamp": time.time(),
                }
            else:
                return {
                    "success": False,
                    "operation": "power_on",
                    "message": f"Display {self.display_id} is already {self.state.power_state}",
                    "timestamp": time.time(),
                }
        except Exception as e:
            self.log_operation("power_on", "error", str(e))
            return {
                "success": False,
                "operation": "power_on",
                "error": str(e),
                "timestamp": time.time(),
            }

    def power_off(self) -> Dict[str, Any]:
        """
        Power off the display device

        Returns:
            Dict containing operation result and new state
        """
        try:
            if self.state.power_state == "on":
                self.state.power_state = "off"
                self.log_operation("power_off", "success")

                return {
                    "success": True,
                    "operation": "power_off",
                    "state": "off",
                    "message": f"Display {self.display_id} powered off successfully",
                    "timestamp": time.time(),
                }
            else:
                return {
                    "success": False,
                    "operation": "power_off",
                    "message": f"Display {self.display_id} is already {self.state.power_state}",
                    "timestamp": time.time(),
                }
        except Exception as e:
            self.log_operation("power_off", "error", str(e))
            return {
                "success": False,
                "operation": "power_off",
                "error": str(e),
                "timestamp": time.time(),
            }

    def set_input_source(self, input_source: str) -> Dict[str, Any]:
        """
        Switch to specified input source

        Args:
            input_source: Name of input source to switch to

        Returns:
            Dict containing operation result and new state
        """
        try:
            if input_source not in self.input_sources:
                return {
                    "success": False,
                    "operation": "set_input_source",
                    "message": f"Invalid input source: {input_source}",
                    "valid_sources": self.input_sources,
                    "timestamp": time.time(),
                }

            if self.state.power_state != "on":
                return {
                    "success": False,
                    "operation": "set_input_source",
                    "message": "Display must be powered on to change input source",
                    "timestamp": time.time(),
                }

            self.state.input_source = input_source
            self.log_operation("set_input_source", "success", input_source)

            return {
                "success": True,
                "operation": "set_input_source",
                "input_source": input_source,
                "message": f"Display {self.display_id} switched to {input_source}",
                "timestamp": time.time(),
            }
        except Exception as e:
            self.log_operation("set_input_source", "error", str(e))
            return {
                "success": False,
                "operation": "set_input_source",
                "error": str(e),
                "timestamp": time.time(),
            }

    def set_brightness(self, brightness: int) -> Dict[str, Any]:
        """
        Set display brightness

        Args:
            brightness: Brightness level (0-100)

        Returns:
            Dict containing operation result and new state
        """
        try:
            if not 0 <= brightness <= 100:
                return {
                    "success": False,
                    "operation": "set_brightness",
                    "message": f"Brightness must be between 0 and 100, got {brightness}",
                    "timestamp": time.time(),
                }

            if self.state.power_state != "on":
                return {
                    "success": False,
                    "operation": "set_brightness",
                    "message": "Display must be powered on to adjust brightness",
                    "timestamp": time.time(),
                }

            self.state.brightness = brightness
            self.log_operation("set_brightness", "success", str(brightness))

            return {
                "success": True,
                "operation": "set_brightness",
                "brightness": brightness,
                "message": f"Display {self.display_id} brightness set to {brightness}%",
                "timestamp": time.time(),
            }
        except Exception as e:
            self.log_operation("set_brightness", "error", str(e))
            return {
                "success": False,
                "operation": "set_brightness",
                "error": str(e),
                "timestamp": time.time(),
            }

    def set_volume(self, volume: int) -> Dict[str, Any]:
        """
        Set display volume (if applicable)

        Args:
            volume: Volume level (0-100)

        Returns:
            Dict containing operation result and new state
        """
        try:
            if not 0 <= volume <= 100:
                return {
                    "success": False,
                    "operation": "set_volume",
                    "message": f"Volume must be between 0 and 100, got {volume}",
                    "timestamp": time.time(),
                }

            if self.state.power_state != "on":
                return {
                    "success": False,
                    "operation": "set_volume",
                    "message": "Display must be powered on to adjust volume",
                    "timestamp": time.time(),
                }

            self.state.volume = volume
            self.log_operation("set_volume", "success", str(volume))

            return {
                "success": True,
                "operation": "set_volume",
                "volume": volume,
                "message": f"Display {self.display_id} volume set to {volume}%",
                "timestamp": time.time(),
            }
        except Exception as e:
            self.log_operation("set_volume", "error", str(e))
            return {
                "success": False,
                "operation": "set_volume",
                "error": str(e),
                "timestamp": time.time(),
            }

    def calibrate_display(self) -> Dict[str, Any]:
        """
        Run display calibration

        Returns:
            Dict containing calibration result
        """
        try:
            if self.state.power_state != "on":
                return {
                    "success": False,
                    "operation": "calibrate_display",
                    "message": "Display must be powered on for calibration",
                    "timestamp": time.time(),
                }

            # Simulate calibration process
            time.sleep(0.1)  # Simulate calibration time

            self.log_operation("calibrate_display", "success")

            return {
                "success": True,
                "operation": "calibrate_display",
                "message": f"Display {self.display_id} calibration completed",
                "calibration_data": {
                    "brightness": self.state.brightness,
                    "contrast": 50,
                    "color_temperature": 6500,
                    "gamma": 2.2,
                },
                "timestamp": time.time(),
            }
        except Exception as e:
            self.log_operation("calibrate_display", "error", str(e))
            return {
                "success": False,
                "operation": "calibrate_display",
                "error": str(e),
                "timestamp": time.time(),
            }

    def get_status(self) -> Dict[str, Any]:
        """
        Get current display status

        Returns:
            Dict containing current status information
        """
        try:
            # Update uptime
            if self.state.power_state == "on":
                self.state.uptime_hours = (time.time() - self.start_time) / 3600

            return {
                "success": True,
                "operation": "get_status",
                "display_id": self.display_id,
                "state": {
                    "power_state": self.state.power_state,
                    "input_source": self.state.input_source,
                    "brightness": self.state.brightness,
                    "volume": self.state.volume,
                    "resolution": self.state.resolution,
                    "refresh_rate": self.state.refresh_rate,
                    "temperature": self.state.temperature,
                    "uptime_hours": self.state.uptime_hours,
                    "error_count": self.state.error_count,
                },
                "properties": self.properties,
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "operation": "get_status",
                "error": str(e),
                "timestamp": time.time(),
            }

    def validate_connections(self, connections: List[str]) -> Dict[str, Any]:
        """
        Validate display connections

        Args:
            connections: List of connected devices

        Returns:
            Dict containing validation result
        """
        try:
            required_connections = ["power", "control"]
            optional_connections = ["video", "audio", "network"]

            missing_required = [
                conn for conn in required_connections if conn not in connections
            ]
            present_optional = [
                conn for conn in optional_connections if conn in connections
            ]

            is_valid = len(missing_required) == 0

            return {
                "success": is_valid,
                "operation": "validate_connections",
                "valid": is_valid,
                "missing_required": missing_required,
                "present_optional": present_optional,
                "message": f"Display {self.display_id} connections validated",
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "operation": "validate_connections",
                "error": str(e),
                "timestamp": time.time(),
            }

    def log_operation(self, operation: str, status: str, details: str = ""):
        """Log an operation for tracking purposes"""
        log_entry = {
            "timestamp": time.time(),
            "operation": operation,
            "status": status,
            "details": details,
            "display_id": self.display_id,
        }
        self.operation_log.append(log_entry)

    def get_operation_log(self) -> List[Dict[str, Any]]:
        """Get the operation log"""
        return self.operation_log

    def reset_operation_log(self):
        """Reset the operation log"""
        self.operation_log = []

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the display

        Returns:
            Dict containing performance metrics
        """
        try:
            uptime_hours = self.state.uptime_hours
            error_rate = self.state.error_count / max(uptime_hours, 1) * 100

            return {
                "success": True,
                "operation": "get_performance_metrics",
                "metrics": {
                    "uptime_hours": uptime_hours,
                    "error_count": self.state.error_count,
                    "error_rate_per_hour": error_rate,
                    "temperature": self.state.temperature,
                    "brightness_level": self.state.brightness,
                    "power_state": self.state.power_state,
                    "input_source": self.state.input_source,
                },
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "operation": "get_performance_metrics",
                "error": str(e),
                "timestamp": time.time(),
            }


def create_display_behavior(
    display_id: str, properties: Dict[str, Any]
) -> DisplayBehavior:
    """
    Factory function to create a display behavior instance

    Args:
        display_id: Unique identifier for the display
        properties: Display properties from schema

    Returns:
        DisplayBehavior instance
    """
    return DisplayBehavior(display_id, properties)
