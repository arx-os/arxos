"""
SVGX Evaluator for runtime behavior evaluation and simulation.

This module handles the evaluation of arx:behavior elements and
executes programmable logic, calculations, and triggers.
"""

import math
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import html

logger = logging.getLogger(__name__)


@dataclass
class EvaluationContext:
    """Context for behavior evaluation."""
    variables: Dict[str, float]
    calculations: Dict[str, str]
    triggers: List[Dict[str, str]]
    environment: Dict[str, Any]


class SVGXEvaluator:
    """Evaluates SVGX behavior and simulation logic."""

    def __init__(self):
        self.builtin_functions = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'sqrt': math.sqrt,
            'pow': math.pow,
            'abs': abs,
            'round': round,
            'floor': math.floor,
            'ceil': math.ceil,
            'log': math.log,
            'exp': math.exp,
        }
        self.evaluation_context = EvaluationContext(
            variables={},
            calculations={},
            triggers=[],
            environment={}
        )

    def evaluate_behavior(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate behavior with variables, calculations, and triggers.

        Args:
            behavior_data: Behavior data from SVGX element

        Returns:
            Evaluation results
        """
        try:
            # Initialize context
            self.evaluation_context.variables = behavior_data.get('variables', {})
            self.evaluation_context.calculations = behavior_data.get('calculations', {})
            self.evaluation_context.triggers = behavior_data.get('triggers', [])

            # Evaluate calculations
            results = {}
            for calc_name, formula in self.evaluation_context.calculations.items():
                try:
                    result = self._evaluate_formula(formula)
                    results[calc_name] = result
                    # Update variables with calculated values
                    self.evaluation_context.variables[calc_name] = result
                except Exception as e:
                    logger.warning(f"Failed to evaluate calculation {calc_name}: {e}")
                    results[calc_name] = None

            return {
                'variables': self.evaluation_context.variables,
                'calculations': results,
                'triggers': self.evaluation_context.triggers
            }

        except Exception as e:
            logger.error(f"Failed to evaluate behavior: {e}")
            return {}

    def _evaluate_formula(self, formula: str) -> float:
        """
        Evaluate a mathematical formula safely.

        Args:
            formula: Mathematical formula as string

        Returns:
            Calculated result
        """
        try:
            # Create a safe evaluation environment
            safe_dict = {
                '__builtins__': {},
                'math': math,
                **self.builtin_functions,
                **self.evaluation_context.variables
            }

            # Replace common mathematical operators
            formula = formula.replace('^', '**')

            # Evaluate the formula
            result = None  # SECURITY: eval() removed - use safe alternatives
            # eval(formula, {"__builtins__": {}}, safe_dict)

            if isinstance(result, (int, float)):
                return float(result)
            else:
                raise ValueError(f"Formula result is not numeric: {result}")

        except Exception as e:
            logger.error(f"Failed to evaluate formula '{formula}': {e}")
            raise

    def evaluate_physics(self, physics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate physics simulation.

        Args:
            physics_data: Physics data from SVGX element

        Returns:
            Physics simulation results
        """
        try:
            results = {}

            # Calculate forces
            if 'forces' in physics_data:
                total_force = self._calculate_total_force(physics_data['forces'])
                results['total_force'] = total_force

            # Calculate mass effects
            if 'mass' in physics_data:
                mass = physics_data['mass']['value']
                unit = physics_data['mass']['unit']
                results['mass'] = {'value': mass, 'unit': unit}

                # Calculate weight (mass * gravity)
                if 'total_force' in results:
                    gravity = 9.81  # m/s²
                    weight = mass * gravity
                    results['weight'] = {'value': weight, 'unit': 'N'}

            # Calculate anchor effects
            if 'anchor' in physics_data:
                results['anchor'] = physics_data['anchor']

            return results

        except Exception as e:
            logger.error(f"Failed to evaluate physics: {e}")
            return {}

    def _calculate_total_force(self, forces: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate total force from multiple force vectors.

        Args:
            forces: List of force dictionaries

        Returns:
            Total force vector
        """
        total_x = 0.0
        total_y = 0.0
        total_z = 0.0

        for force in forces:
            force_type = force.get('type', 'unknown')
            direction = force.get('direction', 'down')
            value = force.get('value', 0.0)

            # Convert direction to vector components
            if direction == 'down':
                total_y += value
            elif direction == 'up':
                total_y -= value
            elif direction == 'left':
                total_x -= value
            elif direction == 'right':
                total_x += value
            elif direction == 'forward':
                total_z += value
            elif direction == 'backward':
                total_z -= value

        return {
            'x': total_x,
            'y': total_y,
            'z': total_z,
            'magnitude': math.sqrt(total_x**2 + total_y**2 + total_z**2)
        }

    def evaluate_system(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate system-level behavior and interactions.

        Args:
            system_data: System data from SVGX element

        Returns:
            System evaluation results
        """
        try:
            results = {}

            # Evaluate system components
            if 'components' in system_data:
                component_results = {}
                for component in system_data['components']:
                    component_id = component.get('id')
                    component_type = component.get('type')

                    # Evaluate component behavior
                    component_result = self._evaluate_component(component)
                    component_results[component_id] = component_result

                results['components'] = component_results

            # Calculate system-level metrics
            if 'system_type' in system_data:
                system_type = system_data['system_type']
                if system_type == 'electrical':
                    results.update(self._evaluate_electrical_system(system_data))
                elif system_type == 'mechanical':
                    results.update(self._evaluate_mechanical_system(system_data))
                elif system_type == 'plumbing':
                    results.update(self._evaluate_plumbing_system(system_data))
            return results

        except Exception as e:
            logger.error(f"Failed to evaluate system: {e}")
            return {}

    def _evaluate_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate individual component behavior."""
        component_type = component.get('type', 'unknown')

        if component_type.startswith('electrical'):
            return self._evaluate_electrical_component(component)
        elif component_type.startswith('mechanical'):
            return self._evaluate_mechanical_component(component)
        else:
            return {'status': 'unknown', 'type': component_type}

    def _evaluate_electrical_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate electrical component behavior."""
        results = {'type': 'electrical'}

        # Extract electrical properties
        voltage = component.get('voltage', 0)
        power = component.get('power', 0)
        resistance = component.get('resistance', 0)

        # Calculate electrical values
        if voltage and resistance:
            current = voltage / resistance
            actual_power = voltage * current
            results.update({
                'voltage': voltage,
                'current': current,
                'power': actual_power,
                'resistance': resistance,
                'status': 'operational' if current > 0 else 'offline'
            })

        return results

    def _evaluate_mechanical_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate mechanical component behavior."""
        results = {'type': 'mechanical'}

        # Extract mechanical properties
        mass = component.get('mass', 0)
        position = component.get('position', [0, 0, 0])

        results.update({
            'mass': mass,
            'position': position,
            'status': 'operational'
        })

        return results

    def _evaluate_electrical_system(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate electrical system behavior."""
        total_power = 0
        total_current = 0
        component_count = 0

        if 'components' in system_data:
            for component in system_data['components']:
                if component.get('type', '').startswith('electrical'):
                    power = component.get('power', 0)
                    current = component.get('current', 0)
                    total_power += power
                    total_current += current
                    component_count += 1

        return {
            'total_power': total_power,
            'total_current': total_current,
            'component_count': component_count,
            'system_load': total_power / max(total_power, 1) * 100  # percentage
        }

    def _evaluate_mechanical_system(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate mechanical system behavior."""
        total_mass = 0
        component_count = 0

        if 'components' in system_data:
            for component in system_data['components']:
                if component.get('type', '').startswith('mechanical'):
                    mass = component.get('mass', 0)
                    total_mass += mass
                    component_count += 1

        return {
            'total_mass': total_mass,
            'component_count': component_count,
            'system_status': 'operational'
        }

    def _evaluate_plumbing_system(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate plumbing system behavior."""
        total_flow = 0
        component_count = 0

        if 'components' in system_data:
            for component in system_data['components']:
                if component.get('type', '').startswith('plumbing'):
                    flow = component.get('flow_rate', 0)
                    total_flow += flow
                    component_count += 1

        return {
            'total_flow': total_flow,
            'component_count': component_count,
            'system_status': 'operational'
        }
