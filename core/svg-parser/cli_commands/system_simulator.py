#!/usr/bin/env python3
"""
System Simulator CLI Tool

This tool provides a command-line interface for system simulation operations, including power flow, HVAC, plumbing, fire suppression, comprehensive simulation, and sample data generation.

Usage examples:
  python -m arx_svg_parser.cmd.system_simulator power --input power.json
  python -m arx_svg_parser.cmd.system_simulator hvac --input hvac.json --duration 120
  python -m arx_svg_parser.cmd.system_simulator fire --input fire.json --fire-scenario scenario.json
  python -m arx_svg_parser.cmd.system_simulator comprehensive --input building.json --format text
  python -m arx_svg_parser.cmd.system_simulator generate-sample --system all --output sample.json

Options can also be set via environment variables or config files if config support is added.
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Use relative imports for package context
from core.services.system_simulation

try:
    import yaml
except ImportError:
    yaml = None

def load_config(args) -> dict:
    config = {}
    config_file = getattr(args, 'config', None) or os.environ.get('ARXOS_SYSTEM_SIMULATOR_CONFIG')
    if config_file:
        ext = Path(config_file).suffix.lower()
        try:
            with open(config_file, 'r') as f:
                if ext in ['.yaml', '.yml'] and yaml:
                    config = yaml.safe_load(f)
                elif ext == '.json':
                    config = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}", file=sys.stderr)
    else:
        for default in [Path.cwd() / 'arxos_cli_config.yaml', Path.home() / 'arxos_cli_config.yaml']:
            if default.exists() and yaml:
                with open(default, 'r') as f:
                    config = yaml.safe_load(f)
                break
    for key, value in os.environ.items():
        if key.startswith('ARXOS_SYSTEM_SIMULATOR_'):
            config[key[len('ARXOS_SYSTEM_SIMULATOR_'):].lower()] = value
    for k, v in vars(args).items():
        if v is not None:
            config[k] = v
    return config


def main():
    parser = argparse.ArgumentParser(description="System behavior simulation CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Power flow simulation
    power_parser = subparsers.add_parser('power', help='Simulate electrical power flow')
    power_parser.add_argument('--input', required=True, help='Input JSON file with electrical system data')
    power_parser.add_argument('--output', help='Output file for simulation results')
    
    # HVAC simulation
    hvac_parser = subparsers.add_parser('hvac', help='Simulate HVAC system behavior')
    hvac_parser.add_argument('--input', required=True, help='Input JSON file with HVAC system data')
    hvac_parser.add_argument('--output', help='Output file for simulation results')
    hvac_parser.add_argument('--duration', type=int, default=60, help='Simulation duration in minutes')
    
    # Plumbing simulation
    plumbing_parser = subparsers.add_parser('plumbing', help='Simulate plumbing system behavior')
    plumbing_parser.add_argument('--input', required=True, help='Input JSON file with plumbing system data')
    plumbing_parser.add_argument('--output', help='Output file for simulation results')
    
    # Fire suppression simulation
    fire_parser = subparsers.add_parser('fire', help='Simulate fire suppression system')
    fire_parser.add_argument('--input', required=True, help='Input JSON file with fire suppression system data')
    fire_parser.add_argument('--output', help='Output file for simulation results')
    fire_parser.add_argument('--fire-scenario', help='JSON file with fire scenario data')
    
    # Comprehensive simulation
    comprehensive_parser = subparsers.add_parser('comprehensive', help='Run comprehensive simulation of all systems')
    comprehensive_parser.add_argument('--input', required=True, help='Input JSON file with all system data')
    comprehensive_parser.add_argument('--output', help='Output file for simulation results')
    comprehensive_parser.add_argument('--format', choices=['json', 'text'], default='json', help='Output format')
    
    # Generate sample data
    sample_parser = subparsers.add_parser('generate-sample', help='Generate sample system data')
    sample_parser.add_argument('--system', choices=['power', 'hvac', 'plumbing', 'fire', 'all'], 
                              default='all', help='System type to generate')
    sample_parser.add_argument('--output', default='sample_system_data.json', help='Output file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        config = load_config(args)
        if args.command == 'power':
            simulate_power_flow(args)
        elif args.command == 'hvac':
            simulate_hvac(args)
        elif args.command == 'plumbing':
            simulate_plumbing(args)
        elif args.command == 'fire':
            simulate_fire_suppression(args)
        elif args.command == 'comprehensive':
            run_comprehensive_simulation(args)
        elif args.command == 'generate-sample':
            generate_sample_data(args)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def simulate_power_flow(args):
    """Run power flow simulation"""
    # Load input data
    with open(args.input, 'r') as f:
        electrical_data = json.load(f)
    
    # Create simulation engine
    engine = SystemSimulationService()
    
    # Setup and run simulation
    engine._setup_power_simulation(electrical_data)
    result = engine.power_simulator.simulate()
    
    # Output results
    output_results(result, args.output, 'power_flow')


def simulate_hvac(args):
    """Run HVAC simulation"""
    # Load input data
    with open(args.input, 'r') as f:
        hvac_data = json.load(f)
    
    # Create simulation engine
    engine = SystemSimulationService()
    
    # Setup and run simulation
    engine._setup_hvac_simulation(hvac_data)
    result = engine.hvac_simulator.simulate(args.duration)
    
    # Output results
    output_results(result, args.output, 'hvac')


def simulate_plumbing(args):
    """Run plumbing simulation"""
    # Load input data
    with open(args.input, 'r') as f:
        plumbing_data = json.load(f)
    
    # Create simulation engine
    engine = SystemSimulationService()
    
    # Setup and run simulation
    engine._setup_plumbing_simulation(plumbing_data)
    result = engine.plumbing_simulator.simulate()
    
    # Output results
    output_results(result, args.output, 'plumbing')


def simulate_fire_suppression(args):
    """Run fire suppression simulation"""
    # Load input data
    with open(args.input, 'r') as f:
        fire_data = json.load(f)
    
    # Load fire scenario if provided
    fire_scenario = None
    if args.fire_scenario:
        with open(args.fire_scenario, 'r') as f:
            fire_scenario = json.load(f)
    
    # Create simulation engine
    engine = SystemSimulationService()
    
    # Setup and run simulation
    engine._setup_fire_suppression_simulation(fire_data)
    result = engine.fire_suppression_simulator.simulate(fire_scenario)
    
    # Output results
    output_results(result, args.output, 'fire_suppression')


def run_comprehensive_simulation(args):
    """Run comprehensive simulation of all systems"""
    # Load input data
    with open(args.input, 'r') as f:
        building_data = json.load(f)
    
    # Create simulation engine
    engine = SystemSimulationService()
    
    # Run comprehensive simulation
    results = engine.run_comprehensive_simulation(building_data)
    
    # Output results
    if args.output:
        if args.format == 'json':
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        else:
            with open(args.output, 'w') as f:
                f.write(format_comprehensive_results_text(results))
        print(f"Comprehensive simulation results saved to: {args.output}")
    else:
        if args.format == 'json':
            print(json.dumps(results, indent=2, default=str))
        else:
            print(format_comprehensive_results_text(results))


def generate_sample_data(args):
    """Generate sample system data"""
    sample_data = {}
    
    if args.system in ['power', 'all']:
        sample_data['electrical'] = generate_sample_power_data()
    
    if args.system in ['hvac', 'all']:
        sample_data['hvac'] = generate_sample_hvac_data()
    
    if args.system in ['plumbing', 'all']:
        sample_data['plumbing'] = generate_sample_plumbing_data()
    
    if args.system in ['fire', 'all']:
        sample_data['fire_suppression'] = generate_sample_fire_data()
    
    # Save sample data
    with open(args.output, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"Sample system data saved to: {args.output}")


def output_results(result: Dict, output_file: str, system_type: str):
    """Output simulation results"""
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"{system_type} simulation results saved to: {output_file}")
    else:
        print(f"\n{system_type.upper()} SIMULATION RESULTS")
        print("=" * 50)
        print(f"Status: {result['status']}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Alerts: {len(result['alerts'])}")
        print(f"Recommendations: {len(result['recommendations'])}")
        
        if result['alerts']:
            print("\nAlerts:")
            for alert in result['alerts']:
                print(f"  - {alert}")
        
        if result['recommendations']:
            print("\nRecommendations:")
            for rec in result['recommendations']:
                print(f"  - {rec}")
        
        print(f"\nMetrics:")
        for key, value in result['metrics'].items():
            print(f"  {key}: {value}")


def format_comprehensive_results_text(results: Dict[str, Dict]) -> str:
    """Format comprehensive results as text"""
    output = []
    output.append("COMPREHENSIVE SYSTEM SIMULATION RESULTS")
    output.append("=" * 60)
    
    for system_type, result in results.items():
        output.append(f"\n{system_type.upper()} SYSTEM")
        output.append("-" * 30)
        output.append(f"Status: {result['status']}")
        output.append(f"Alerts: {len(result['alerts'])}")
        output.append(f"Recommendations: {len(result['recommendations'])}")
        
        if result['alerts']:
            output.append("Alerts:")
            for alert in result['alerts']:
                output.append(f"  - {alert}")
        
        if result['recommendations']:
            output.append("Recommendations:")
            for rec in result['recommendations']:
                output.append(f"  - {rec}")
    
    return "\n".join(output)


def generate_sample_power_data() -> Dict[str, Any]:
    """Generate sample electrical system data"""
    return {
        "nodes": [
            {
                "id": "main_bus",
                "voltage": 120.0,
                "power_demand": 0.0,
                "power_supply": 10000.0,
                "is_generator": True,
                "is_load": False,
                "is_bus": True
            },
            {
                "id": "panel_1",
                "voltage": 120.0,
                "power_demand": 2000.0,
                "power_supply": 0.0,
                "is_generator": False,
                "is_load": True,
                "is_bus": False
            },
            {
                "id": "panel_2",
                "voltage": 120.0,
                "power_demand": 1500.0,
                "power_supply": 0.0,
                "is_generator": False,
                "is_load": True,
                "is_bus": False
            }
        ],
        "connections": [
            {
                "from_node": "main_bus",
                "to_node": "panel_1",
                "resistance": 0.1,
                "reactance": 0.05,
                "max_current": 100.0
            },
            {
                "from_node": "main_bus",
                "to_node": "panel_2",
                "resistance": 0.1,
                "reactance": 0.05,
                "max_current": 100.0
            }
        ]
    }


def generate_sample_hvac_data() -> Dict[str, Any]:
    """Generate sample HVAC system data"""
    return {
        "zones": [
            {
                "id": "zone_1",
                "temperature": 22.0,
                "humidity": 50.0,
                "air_flow_rate": 500.0,
                "heat_load": 5000.0,
                "cooling_load": 3000.0,
                "volume": 5000.0
            },
            {
                "id": "zone_2",
                "temperature": 24.0,
                "humidity": 45.0,
                "air_flow_rate": 400.0,
                "heat_load": 3000.0,
                "cooling_load": 4000.0,
                "volume": 4000.0
            }
        ],
        "equipment": [
            {
                "id": "ahu_1",
                "type": "ahu",
                "capacity": 10000.0,
                "efficiency": 0.85,
                "power_consumption": 2000.0
            },
            {
                "id": "chiller_1",
                "type": "chiller",
                "capacity": 15000.0,
                "efficiency": 0.90,
                "power_consumption": 3000.0
            }
        ]
    }


def generate_sample_plumbing_data() -> Dict[str, Any]:
    """Generate sample plumbing system data"""
    return {
        "nodes": [
            {
                "id": "main_supply",
                "pressure": 80.0,
                "flow_rate": 0.0,
                "demand": 0.0,
                "supply": 500.0,
                "elevation": 0.0
            },
            {
                "id": "floor_1",
                "pressure": 60.0,
                "flow_rate": 0.0,
                "demand": 100.0,
                "supply": 0.0,
                "elevation": 10.0
            },
            {
                "id": "floor_2",
                "pressure": 40.0,
                "flow_rate": 0.0,
                "demand": 80.0,
                "supply": 0.0,
                "elevation": 20.0
            }
        ],
        "connections": [
            {
                "from_node": "main_supply",
                "to_node": "floor_1",
                "diameter": 2.0,
                "length": 50.0,
                "roughness": 0.01,
                "max_flow": 200.0
            },
            {
                "from_node": "floor_1",
                "to_node": "floor_2",
                "diameter": 1.5,
                "length": 30.0,
                "roughness": 0.01,
                "max_flow": 150.0
            }
        ]
    }


def generate_sample_fire_data() -> Dict[str, Any]:
    """Generate sample fire suppression system data"""
    return {
        "zones": [
            {
                "id": "zone_1",
                "area": 2000.0,
                "sprinkler_count": 20,
                "sprinkler_spacing": 12.0,
                "water_demand": 200.0,
                "pressure_required": 30.0
            },
            {
                "id": "zone_2",
                "area": 1500.0,
                "sprinkler_count": 15,
                "sprinkler_spacing": 12.0,
                "water_demand": 150.0,
                "pressure_required": 30.0
            }
        ]
    }


if __name__ == '__main__':
    main() 