"""
Behavior Profiles with Variables and Calculations
Define YAML-based behavior profile format to attach physics and functional logic to ArxObjects
"""

import os
import yaml
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime
import re
import math

logger = logging.getLogger(__name__)


class VariableType(Enum):
    """Variable types for behavior profiles"""
    SCALAR = "scalar"         # Single numeric value
    VECTOR = "vector"         # Array of numeric values
    STRING = "string"         # Text value
    BOOLEAN = "boolean"       # True/false value
    OBJECT = "object"         # Complex object
    ARRAY = "array"          # Array of any type


class CalculationType(Enum):
    """Calculation types for behavior profiles"""
    ARITHMETIC = "arithmetic"     # Basic math operations
    PHYSICS = "physics"          # Physics calculations
    LOGIC = "logic"             # Logical operations
    CONDITIONAL = "conditional"  # Conditional calculations
    LOOKUP = "lookup"           # Table lookups
    CUSTOM = "custom"           # Custom functions


class UnitType(Enum):
    """Unit types for physical quantities"""
    VOLTAGE = "voltage"         # Volts (V)
    CURRENT = "current"         # Amperes (A)
    POWER = "power"            # Watts (W)
    RESISTANCE = "resistance"   # Ohms (Ω)
    FREQUENCY = "frequency"     # Hertz (Hz)
    TEMPERATURE = "temperature" # Celsius (°C)
    PRESSURE = "pressure"      # Pascals (Pa)
    FLOW_RATE = "flow_rate"    # Liters per second (L/s)
    LENGTH = "length"          # Meters (m)
    AREA = "area"             # Square meters (m²)
    VOLUME = "volume"         # Cubic meters (m³)
    TIME = "time"             # Seconds (s)
    ANGLE = "angle"           # Radians (rad)
    VELOCITY = "velocity"     # Meters per second (m/s)
    ACCELERATION = "acceleration"  # Meters per second squared (m/s²)
    FORCE = "force"           # Newtons (N)
    ENERGY = "energy"         # Joules (J)
    MASS = "mass"            # Kilograms (kg)
    DENSITY = "density"      # Kilograms per cubic meter (kg/m³)


@dataclass
class Variable:
    """Variable definition in behavior profile"""
    name: str
    type: VariableType
    value: Any
    unit: Optional[str]
    description: str
    min_value: Optional[float]
    max_value: Optional[float]
    default_value: Any
    is_required: bool
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Calculation:
    """Calculation definition in behavior profile"""
    name: str
    type: CalculationType
    expression: str
    input_variables: List[str]
    output_variable: str
    description: str
    conditions: List[Dict[str, Any]]
    error_handling: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.input_variables is None:
            self.input_variables = []
        if self.conditions is None:
            self.conditions = []
        if self.error_handling is None:
            self.error_handling = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BehaviorProfile:
    """Complete behavior profile for an ArxObject"""
    profile_id: str
    object_id: str
    name: str
    description: str
    version: str
    author: str
    created_at: str
    modified_at: str
    variables: Dict[str, Variable]
    calculations: Dict[str, Calculation]
    dependencies: List[str]
    metadata: Dict[str, Any]
    is_active: bool
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if self.calculations is None:
            self.calculations = {}
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


class BehaviorLoader:
    """Loader for YAML-based behavior profiles"""
    
    def __init__(self, profiles_path: str = "behavior/profiles"):
        self.profiles_path = profiles_path
        self.profiles: Dict[str, BehaviorProfile] = {}
        self.variable_cache: Dict[str, Any] = {}
        self.calculation_cache: Dict[str, Any] = {}
        
        self.logger = logging.getLogger(__name__)
        
        self._load_profiles()
    
    def _load_profiles(self):
        """Load all behavior profiles from the profiles directory"""
        
        try:
            if not os.path.exists(self.profiles_path):
                os.makedirs(self.profiles_path, exist_ok=True)
                self.logger.info(f"Created profiles directory: {self.profiles_path}")
                return
            
            for filename in os.listdir(self.profiles_path):
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    file_path = os.path.join(self.profiles_path, filename)
                    self._load_profile_from_file(file_path)
                    
        except Exception as e:
            self.logger.error(f"Failed to load behavior profiles: {e}")
    
    def _load_profile_from_file(self, file_path: str) -> Optional[BehaviorProfile]:
        """Load a single behavior profile from YAML file"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return None
            
            # Parse variables
            variables = {}
            for var_name, var_data in data.get('variables', {}).items():
                variables[var_name] = self._parse_variable(var_name, var_data)
            
            # Parse calculations
            calculations = {}
            for calc_name, calc_data in data.get('calculations', {}).items():
                calculations[calc_name] = self._parse_calculation(calc_name, calc_data)
            
            # Create behavior profile
            profile = BehaviorProfile(
                profile_id=data.get('profile_id', ''),
                object_id=data.get('object_id', ''),
                name=data.get('name', ''),
                description=data.get('description', ''),
                version=data.get('version', '1.0'),
                author=data.get('author', ''),
                created_at=data.get('created_at', datetime.utcnow().isoformat()),
                modified_at=data.get('modified_at', datetime.utcnow().isoformat()),
                variables=variables,
                calculations=calculations,
                dependencies=data.get('dependencies', []),
                metadata=data.get('metadata', {}),
                is_active=data.get('is_active', True)
            )
            
            self.profiles[profile.profile_id] = profile
            self.logger.info(f"Loaded behavior profile: {profile.profile_id}")
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Failed to load profile from {file_path}: {e}")
            return None
    
    def _parse_variable(self, name: str, data: Dict) -> Variable:
        """Parse variable from YAML data"""
        
        return Variable(
            name=name,
            type=VariableType(data.get('type', 'scalar')),
            value=data.get('value'),
            unit=data.get('unit'),
            description=data.get('description', ''),
            min_value=data.get('min_value'),
            max_value=data.get('max_value'),
            default_value=data.get('default_value'),
            is_required=data.get('is_required', False),
            metadata=data.get('metadata', {})
        )
    
    def _parse_calculation(self, name: str, data: Dict) -> Calculation:
        """Parse calculation from YAML data"""
        
        return Calculation(
            name=name,
            type=CalculationType(data.get('type', 'arithmetic')),
            expression=data.get('expression', ''),
            input_variables=data.get('input_variables', []),
            output_variable=data.get('output_variable', ''),
            description=data.get('description', ''),
            conditions=data.get('conditions', []),
            error_handling=data.get('error_handling', {}),
            metadata=data.get('metadata', {})
        )
    
    def get_profile(self, profile_id: str) -> Optional[BehaviorProfile]:
        """Get a behavior profile by ID"""
        
        return self.profiles.get(profile_id)
    
    def get_profiles_by_object(self, object_id: str) -> List[BehaviorProfile]:
        """Get all behavior profiles for an object"""
        
        return [profile for profile in self.profiles.values() 
                if profile.object_id == object_id and profile.is_active]
    
    def get_profiles_by_type(self, calculation_type: CalculationType) -> List[BehaviorProfile]:
        """Get behavior profiles by calculation type"""
        
        matching_profiles = []
        for profile in self.profiles.values():
            for calculation in profile.calculations.values():
                if calculation.type == calculation_type:
                    matching_profiles.append(profile)
                    break
        
        return matching_profiles
    
    def create_profile(self, profile_data: Dict) -> str:
        """Create a new behavior profile"""
        
        profile_id = profile_data.get('profile_id')
        if not profile_id:
            raise ValueError("Profile ID is required")
        
        if profile_id in self.profiles:
            raise ValueError(f"Profile {profile_id} already exists")
        
        # Create profile
        profile = self._create_profile_from_data(profile_data)
        self.profiles[profile_id] = profile
        
        # Save to file
        self._save_profile_to_file(profile)
        
        self.logger.info(f"Created behavior profile: {profile_id}")
        return profile_id
    
    def _create_profile_from_data(self, data: Dict) -> BehaviorProfile:
        """Create behavior profile from data"""
        
        # Parse variables
        variables = {}
        for var_name, var_data in data.get('variables', {}).items():
            variables[var_name] = self._parse_variable(var_name, var_data)
        
        # Parse calculations
        calculations = {}
        for calc_name, calc_data in data.get('calculations', {}).items():
            calculations[calc_name] = self._parse_calculation(calc_name, calc_data)
        
        return BehaviorProfile(
            profile_id=data.get('profile_id', ''),
            object_id=data.get('object_id', ''),
            name=data.get('name', ''),
            description=data.get('description', ''),
            version=data.get('version', '1.0'),
            author=data.get('author', ''),
            created_at=datetime.utcnow().isoformat(),
            modified_at=datetime.utcnow().isoformat(),
            variables=variables,
            calculations=calculations,
            dependencies=data.get('dependencies', []),
            metadata=data.get('metadata', {}),
            is_active=data.get('is_active', True)
        )
    
    def _save_profile_to_file(self, profile: BehaviorProfile):
        """Save behavior profile to YAML file"""
        
        try:
            os.makedirs(self.profiles_path, exist_ok=True)
            
            file_path = os.path.join(self.profiles_path, f"{profile.profile_id}.yaml")
            
            data = {
                'profile_id': profile.profile_id,
                'object_id': profile.object_id,
                'name': profile.name,
                'description': profile.description,
                'version': profile.version,
                'author': profile.author,
                'created_at': profile.created_at,
                'modified_at': profile.modified_at,
                'dependencies': profile.dependencies,
                'metadata': profile.metadata,
                'is_active': profile.is_active,
                'variables': {},
                'calculations': {}
            }
            
            # Add variables
            for var_name, variable in profile.variables.items():
                data['variables'][var_name] = asdict(variable)
            
            # Add calculations
            for calc_name, calculation in profile.calculations.items():
                data['calculations'][calc_name] = asdict(calculation)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Saved behavior profile to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save behavior profile: {e}")
    
    def update_profile(self, profile_id: str, updates: Dict) -> bool:
        """Update an existing behavior profile"""
        
        if profile_id not in self.profiles:
            return False
        
        profile = self.profiles[profile_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.modified_at = datetime.utcnow().isoformat()
        
        # Save to file
        self._save_profile_to_file(profile)
        
        self.logger.info(f"Updated behavior profile: {profile_id}")
        return True
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete a behavior profile"""
        
        if profile_id not in self.profiles:
            return False
        
        # Remove from profiles
        del self.profiles[profile_id]
        
        # Delete file
        file_path = os.path.join(self.profiles_path, f"{profile_id}.yaml")
        if os.path.exists(file_path):
            os.remove(file_path)
        
        self.logger.info(f"Deleted behavior profile: {profile_id}")
        return True
    
    def validate_profile(self, profile_id: str) -> List[str]:
        """Validate a behavior profile"""
        
        errors = []
        
        if profile_id not in self.profiles:
            errors.append(f"Profile {profile_id} not found")
            return errors
        
        profile = self.profiles[profile_id]
        
        # Validate variables
        for var_name, variable in profile.variables.items():
            if variable.is_required and variable.value is None:
                errors.append(f"Required variable {var_name} has no value")
            
            if variable.min_value is not None and variable.value is not None:
                if variable.value < variable.min_value:
                    errors.append(f"Variable {var_name} value {variable.value} is below minimum {variable.min_value}")
            
            if variable.max_value is not None and variable.value is not None:
                if variable.value > variable.max_value:
                    errors.append(f"Variable {var_name} value {variable.value} is above maximum {variable.max_value}")
        
        # Validate calculations
        for calc_name, calculation in profile.calculations.items():
            # Check if input variables exist
            for input_var in calculation.input_variables:
                if input_var not in profile.variables:
                    errors.append(f"Calculation {calc_name} references non-existent variable {input_var}")
            
            # Check if output variable exists
            if calculation.output_variable not in profile.variables:
                errors.append(f"Calculation {calc_name} output variable {calculation.output_variable} not found")
        
        return errors
    
    def get_profile_statistics(self) -> Dict[str, Any]:
        """Get statistics about behavior profiles"""
        
        total_profiles = len(self.profiles)
        active_profiles = len([p for p in self.profiles.values() if p.is_active])
        
        total_variables = sum(len(p.variables) for p in self.profiles.values())
        total_calculations = sum(len(p.calculations) for p in self.profiles.values())
        
        calculation_types = {}
        for profile in self.profiles.values():
            for calculation in profile.calculations.values():
                calc_type = calculation.type.value
                calculation_types[calc_type] = calculation_types.get(calc_type, 0) + 1
        
        variable_types = {}
        for profile in self.profiles.values():
            for variable in profile.variables.values():
                var_type = variable.type.value
                variable_types[var_type] = variable_types.get(var_type, 0) + 1
        
        return {
            'total_profiles': total_profiles,
            'active_profiles': active_profiles,
            'inactive_profiles': total_profiles - active_profiles,
            'total_variables': total_variables,
            'total_calculations': total_calculations,
            'calculation_types': calculation_types,
            'variable_types': variable_types,
            'average_variables_per_profile': total_variables / total_profiles if total_profiles > 0 else 0,
            'average_calculations_per_profile': total_calculations / total_profiles if total_profiles > 0 else 0
        }
    
    def export_profile_report(self) -> Dict[str, Any]:
        """Export behavior profile report"""
        
        report = {
            'profiles': {},
            'statistics': self.get_profile_statistics()
        }
        
        for profile_id, profile in self.profiles.items():
            report['profiles'][profile_id] = {
                'name': profile.name,
                'object_id': profile.object_id,
                'version': profile.version,
                'is_active': profile.is_active,
                'variable_count': len(profile.variables),
                'calculation_count': len(profile.calculations),
                'dependencies': profile.dependencies
            }
        
        return report


# Global behavior loader instance
behavior_loader = BehaviorLoader() 