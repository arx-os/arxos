"""
Projector Behavior Profile for Audiovisual System

This module defines the behavior patterns and logic for AV projector devices
including DLP, LCD, and laser projectors.
"""

import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ProjectorState:
    """Represents the current state of a projector device"""
    power_state: str = "off"  # off, on, standby, cooling
    input_source: str = "none"
    brightness: int = 100  # 0-100
    contrast: int = 50  # 0-100
    keystone: int = 0  # -30 to 30
    lens_shift_h: int = 0  # -10 to 10
    lens_shift_v: int = 0  # -10 to 10
    lamp_hours: float = 0.0
    temperature: float = 25.0
    uptime_hours: float = 0.0
    error_count: int = 0
    last_maintenance: Optional[str] = None


class ProjectorBehavior:
    """
    Behavior profile for AV projector devices
    
    Handles power management, image adjustment, lamp management,
    and performance monitoring for projector devices.
    """
    
    def __init__(self, projector_id: str, properties: Dict[str, Any]):
        """
        Initialize projector behavior
        
        Args:
            projector_id: Unique identifier for the projector
            properties: Projector properties from schema
        """
        self.projector_id = projector_id
        self.properties = properties
        self.state = ProjectorState()
        self.input_sources = ["HDMI1", "HDMI2", "VGA", "Component", "Composite"]
        self.valid_resolutions = ["1920x1080", "1280x720", "800x600"]
        self.max_brightness = properties.get("brightness", 3000)
        self.contrast_ratio = properties.get("contrast_ratio", "2000:1")
        self.throw_ratio = properties.get("throw_ratio", "1.2:1")
        self.lamp_life = properties.get("lamp_life", 4000)
        
        # Performance tracking
        self.start_time = time.time()
        self.operation_log = []
    
    def power_on(self) -> Dict[str, Any]:
        """
        Power on the projector device
        
        Returns:
            Dict containing operation result and new state
        """
        try:
            if self.state.power_state == "off":
                # Check lamp hours before powering on
                if self.state.lamp_hours > self.lamp_life * 0.9:
                    return {
                        "success": False,
                        "operation": "power_on",
                        "message": f"Projector {self.projector_id} lamp needs replacement",
                        "lamp_hours": self.state.lamp_hours,
                        "max_lamp_life": self.lamp_life,
                        "timestamp": time.time()
                    }
                
                self.state.power_state = "on"
                self.state.uptime_hours = 0.0
                self.log_operation("power_on", "success")
                
                return {
                    "success": True,
                    "operation": "power_on",
                    "state": "on",
                    "message": f"Projector {self.projector_id} powered on successfully",
                    "timestamp": time.time()
                }
            else:
                return {
                    "success": False,
                    "operation": "power_on",
                    "message": f"Projector {self.projector_id} is already {self.state.power_state}",
                    "timestamp": time.time()
                }
        except Exception as e:
            self.log_operation("power_on", "error", str(e))
            return {
                "success": False,
                "operation": "power_on",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def power_off(self) -> Dict[str, Any]:
        """
        Power off the projector device
        
        Returns:
            Dict containing operation result and new state
        """
        try:
            if self.state.power_state == "on":
                # Enter cooling mode first
                self.state.power_state = "cooling"
                time.sleep(0.1)  # Simulate cooling time
                
                self.state.power_state = "off"
                self.log_operation("power_off", "success")
                
                return {
                    "success": True,
                    "operation": "power_off",
                    "state": "off",
                    "message": f"Projector {self.projector_id} powered off successfully",
                    "timestamp": time.time()
                }
            else:
                return {
                    "success": False,
                    "operation": "power_off",
                    "message": f"Projector {self.projector_id} is already {self.state.power_state}",
                    "timestamp": time.time()
                }
        except Exception as e:
            self.log_operation("power_off", "error", str(e))
            return {
                "success": False,
                "operation": "power_off",
                "error": str(e),
                "timestamp": time.time()
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
                    "timestamp": time.time()
                }
            
            if self.state.power_state != "on":
                return {
                    "success": False,
                    "operation": "set_input_source",
                    "message": "Projector must be powered on to change input source",
                    "timestamp": time.time()
                }
            
            self.state.input_source = input_source
            self.log_operation("set_input_source", "success", input_source)
            
            return {
                "success": True,
                "operation": "set_input_source",
                "input_source": input_source,
                "message": f"Projector {self.projector_id} switched to {input_source}",
                "timestamp": time.time()
            }
        except Exception as e:
            self.log_operation("set_input_source", "error", str(e))
            return {
                "success": False,
                "operation": "set_input_source",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def adjust_keystone(self, keystone_value: int) -> Dict[str, Any]:
        """
        Adjust keystone correction
        
        Args:
            keystone_value: Keystone value (-30 to 30)
            
        Returns:
            Dict containing operation result and new state
        """
        try:
            if not -30 <= keystone_value <= 30:
                return {
                    "success": False,
                    "operation": "adjust_keystone",
                    "message": f"Keystone value must be between -30 and 30, got {keystone_value}",
                    "timestamp": time.time()
                }
            
            if self.state.power_state != "on":
                return {
                    "success": False,
                    "operation": "adjust_keystone",
                    "message": "Projector must be powered on to adjust keystone",
                    "timestamp": time.time()
                }
            
            self.state.keystone = keystone_value
            self.log_operation("adjust_keystone", "success", str(keystone_value))
            
            return {
                "success": True,
                "operation": "adjust_keystone",
                "keystone": keystone_value,
                "message": f"Projector {self.projector_id} keystone adjusted to {keystone_value}",
                "timestamp": time.time()
            }
        except Exception as e:
            self.log_operation("adjust_keystone", "error", str(e))
            return {
                "success": False,
                "operation": "adjust_keystone",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def adjust_lens_shift(self, horizontal: int, vertical: int) -> Dict[str, Any]:
        """
        Adjust lens shift
        
        Args:
            horizontal: Horizontal shift (-10 to 10)
            vertical: Vertical shift (-10 to 10)
            
        Returns:
            Dict containing operation result and new state
        """
        try:
            if not -10 <= horizontal <= 10:
                return {
                    "success": False,
                    "operation": "adjust_lens_shift",
                    "message": f"Horizontal shift must be between -10 and 10, got {horizontal}",
                    "timestamp": time.time()
                }
            
            if not -10 <= vertical <= 10:
                return {
                    "success": False,
                    "operation": "adjust_lens_shift",
                    "message": f"Vertical shift must be between -10 and 10, got {vertical}",
                    "timestamp": time.time()
                }
            
            if self.state.power_state != "on":
                return {
                    "success": False,
                    "operation": "adjust_lens_shift",
                    "message": "Projector must be powered on to adjust lens shift",
                    "timestamp": time.time()
                }
            
            self.state.lens_shift_h = horizontal
            self.state.lens_shift_v = vertical
            self.log_operation("adjust_lens_shift", "success", f"H:{horizontal}, V:{vertical}")
            
            return {
                "success": True,
                "operation": "adjust_lens_shift",
                "horizontal_shift": horizontal,
                "vertical_shift": vertical,
                "message": f"Projector {self.projector_id} lens shift adjusted",
                "timestamp": time.time()
            }
        except Exception as e:
            self.log_operation("adjust_lens_shift", "error", str(e))
            return {
                "success": False,
                "operation": "adjust_lens_shift",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def set_brightness(self, brightness: int) -> Dict[str, Any]:
        """
        Set projector brightness
        
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
                    "timestamp": time.time()
                }
            
            if self.state.power_state != "on":
                return {
                    "success": False,
                    "operation": "set_brightness",
                    "message": "Projector must be powered on to adjust brightness",
                    "timestamp": time.time()
                }
            
            self.state.brightness = brightness
            self.log_operation("set_brightness", "success", str(brightness))
            
            return {
                "success": True,
                "operation": "set_brightness",
                "brightness": brightness,
                "message": f"Projector {self.projector_id} brightness set to {brightness}%",
                "timestamp": time.time()
            }
        except Exception as e:
            self.log_operation("set_brightness", "error", str(e))
            return {
                "success": False,
                "operation": "set_brightness",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_lamp_status(self) -> Dict[str, Any]:
        """
        Get lamp status and hours
        
        Returns:
            Dict containing lamp status information
        """
        try:
            lamp_percentage = (self.state.lamp_hours / self.lamp_life) * 100
            lamp_status = "good" if lamp_percentage < 80 else "warning" if lamp_percentage < 90 else "replace"
            
            return {
                "success": True,
                "operation": "get_lamp_status",
                "lamp_hours": self.state.lamp_hours,
                "max_lamp_life": self.lamp_life,
                "lamp_percentage": lamp_percentage,
                "lamp_status": lamp_status,
                "message": f"Projector {self.projector_id} lamp status retrieved",
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "success": False,
                "operation": "get_lamp_status",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def calibrate_projector(self) -> Dict[str, Any]:
        """
        Run projector calibration
        
        Returns:
            Dict containing calibration result
        """
        try:
            if self.state.power_state != "on":
                return {
                    "success": False,
                    "operation": "calibrate_projector",
                    "message": "Projector must be powered on for calibration",
                    "timestamp": time.time()
                }
            
            # Simulate calibration process
            time.sleep(0.2)  # Simulate calibration time
            
            self.log_operation("calibrate_projector", "success")
            
            return {
                "success": True,
                "operation": "calibrate_projector",
                "message": f"Projector {self.projector_id} calibration completed",
                "calibration_data": {
                    "brightness": self.state.brightness,
                    "contrast": self.state.contrast,
                    "keystone": self.state.keystone,
                    "lens_shift_h": self.state.lens_shift_h,
                    "lens_shift_v": self.state.lens_shift_v,
                    "color_temperature": 6500,
                    "gamma": 2.2
                },
                "timestamp": time.time()
            }
        except Exception as e:
            self.log_operation("calibrate_projector", "error", str(e))
            return {
                "success": False,
                "operation": "calibrate_projector",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current projector status
        
        Returns:
            Dict containing current status information
        """
        try:
            # Update uptime and lamp hours
            if self.state.power_state == "on":
                self.state.uptime_hours = (time.time() - self.start_time) / 3600
                self.state.lamp_hours += 0.001  # Increment lamp hours slightly
            
            return {
                "success": True,
                "operation": "get_status",
                "projector_id": self.projector_id,
                "state": {
                    "power_state": self.state.power_state,
                    "input_source": self.state.input_source,
                    "brightness": self.state.brightness,
                    "contrast": self.state.contrast,
                    "keystone": self.state.keystone,
                    "lens_shift_h": self.state.lens_shift_h,
                    "lens_shift_v": self.state.lens_shift_v,
                    "lamp_hours": self.state.lamp_hours,
                    "temperature": self.state.temperature,
                    "uptime_hours": self.state.uptime_hours,
                    "error_count": self.state.error_count
                },
                "properties": self.properties,
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "success": False,
                "operation": "get_status",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def validate_connections(self, connections: List[str]) -> Dict[str, Any]:
        """
        Validate projector connections
        
        Args:
            connections: List of connected devices
            
        Returns:
            Dict containing validation result
        """
        try:
            required_connections = ["power", "control"]
            optional_connections = ["video", "audio", "network"]
            
            missing_required = [conn for conn in required_connections if conn not in connections]
            present_optional = [conn for conn in optional_connections if conn in connections]
            
            is_valid = len(missing_required) == 0
            
            return {
                "success": is_valid,
                "operation": "validate_connections",
                "valid": is_valid,
                "missing_required": missing_required,
                "present_optional": present_optional,
                "message": f"Projector {self.projector_id} connections validated",
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "success": False,
                "operation": "validate_connections",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def log_operation(self, operation: str, status: str, details: str = ""):
        """Log an operation for tracking purposes"""
        log_entry = {
            "timestamp": time.time(),
            "operation": operation,
            "status": status,
            "details": details,
            "projector_id": self.projector_id
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
        Get performance metrics for the projector
        
        Returns:
            Dict containing performance metrics
        """
        try:
            uptime_hours = self.state.uptime_hours
            error_rate = self.state.error_count / max(uptime_hours, 1) * 100
            lamp_percentage = (self.state.lamp_hours / self.lamp_life) * 100
            
            return {
                "success": True,
                "operation": "get_performance_metrics",
                "metrics": {
                    "uptime_hours": uptime_hours,
                    "error_count": self.state.error_count,
                    "error_rate_per_hour": error_rate,
                    "lamp_hours": self.state.lamp_hours,
                    "lamp_percentage": lamp_percentage,
                    "temperature": self.state.temperature,
                    "brightness_level": self.state.brightness,
                    "power_state": self.state.power_state,
                    "input_source": self.state.input_source
                },
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "success": False,
                "operation": "get_performance_metrics",
                "error": str(e),
                "timestamp": time.time()
            }


def create_projector_behavior(projector_id: str, properties: Dict[str, Any]) -> ProjectorBehavior:
    """
    Factory function to create a projector behavior instance
    
    Args:
        projector_id: Unique identifier for the projector
        properties: Projector properties from schema
        
    Returns:
        ProjectorBehavior instance
    """
    return ProjectorBehavior(projector_id, properties) 