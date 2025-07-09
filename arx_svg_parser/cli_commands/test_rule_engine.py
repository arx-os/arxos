"""
Comprehensive testing utility for building code rule engine.

This tool provides:
- Rule validation testing
- Test data generation
- Performance benchmarking
- Coverage analysis
- Regression testing
"""

import argparse
import json
import sys
import os
import time
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

from ..services.rule_engine import EnhancedRuleEngine, RuleDefinition


class RuleEngineTester:
    """Comprehensive testing utility for rule engine"""
    
    def __init__(self):
        self.rule_engine = EnhancedRuleEngine()
        self.test_results = []
        self.performance_metrics = {}
    
    def load_test_rules(self, rules_directory: str) -> List[RuleDefinition]:
        """Load all test rules from directory"""
        try:
            rules = self.rule_engine.load_rules_from_directory(rules_directory)
            print(f"Loaded {len(rules)} test rules from {rules_directory}")
            return rules
        except Exception as e:
            print(f"Error loading test rules: {e}")
            return []
    
    def generate_test_data(self, rule_type: str, scenario: str = "normal") -> Dict[str, Any]:
        """Generate test data for different scenarios"""
        if rule_type == "structural":
            return self._generate_structural_test_data(scenario)
        elif rule_type == "fire_safety":
            return self._generate_fire_safety_test_data(scenario)
        elif rule_type == "accessibility":
            return self._generate_accessibility_test_data(scenario)
        elif rule_type == "energy":
            return self._generate_energy_test_data(scenario)
        else:
            return self._generate_general_test_data(scenario)
    
    def _generate_structural_test_data(self, scenario: str) -> Dict[str, Any]:
        """Generate structural test data"""
        if scenario == "passing":
            return {
                "structural": {
                    "loads": {
                        "dead_load": 100,
                        "live_load": 60,
                        "snow_load": 40
                    },
                    "materials": {
                        "concrete": {
                            "strength": 4000,
                            "density": 150
                        },
                        "steel": {
                            "yield_strength": 50000,
                            "tensile_strength": 65000
                        }
                    }
                }
            }
        elif scenario == "failing":
            return {
                "structural": {
                    "loads": {
                        "dead_load": 50,
                        "live_load": 30,
                        "snow_load": 20
                    },
                    "materials": {
                        "concrete": {
                            "strength": 2000,
                            "density": 120
                        },
                        "steel": {
                            "yield_strength": 30000,
                            "tensile_strength": 45000
                        }
                    }
                }
            }
        else:  # normal
            return {
                "structural": {
                    "loads": {
                        "dead_load": 80,
                        "live_load": 50,
                        "snow_load": 30
                    },
                    "materials": {
                        "concrete": {
                            "strength": 3000,
                            "density": 145
                        },
                        "steel": {
                            "yield_strength": 36000,
                            "tensile_strength": 58000
                        }
                    }
                }
            }
    
    def _generate_fire_safety_test_data(self, scenario: str) -> Dict[str, Any]:
        """Generate fire safety test data"""
        if scenario == "passing":
            return {
                "fire_safety": {
                    "fire_ratings": {
                        "walls": 3,
                        "doors": 2,
                        "floors": 2
                    },
                    "egress": {
                        "exit_width": 42,
                        "exit_distance": 150,
                        "exit_count": 4
                    },
                    "sprinklers": True,
                    "alarms": True
                }
            }
        elif scenario == "failing":
            return {
                "fire_safety": {
                    "fire_ratings": {
                        "walls": 1,
                        "doors": 0,
                        "floors": 1
                    },
                    "egress": {
                        "exit_width": 30,
                        "exit_distance": 250,
                        "exit_count": 2
                    },
                    "sprinklers": False,
                    "alarms": False
                }
            }
        else:  # normal
            return {
                "fire_safety": {
                    "fire_ratings": {
                        "walls": 2,
                        "doors": 1,
                        "floors": 2
                    },
                    "egress": {
                        "exit_width": 36,
                        "exit_distance": 200,
                        "exit_count": 3
                    },
                    "sprinklers": True,
                    "alarms": True
                }
            }
    
    def _generate_accessibility_test_data(self, scenario: str) -> Dict[str, Any]:
        """Generate accessibility test data"""
        if scenario == "passing":
            return {
                "accessibility": {
                    "clear_width": 48,
                    "doors": {
                        "entrance": {
                            "width": 42,
                            "threshold": 0.25
                        },
                        "interior": {
                            "width": 36,
                            "threshold": 0.5
                        }
                    },
                    "ramp": {
                        "slope": 1.0,
                        "handrails": True,
                        "landing": True
                    }
                }
            }
        elif scenario == "failing":
            return {
                "accessibility": {
                    "clear_width": 32,
                    "doors": {
                        "entrance": {
                            "width": 30,
                            "threshold": 1.0
                        },
                        "interior": {
                            "width": 28,
                            "threshold": 1.5
                        }
                    },
                    "ramp": {
                        "slope": 2.0,
                        "handrails": False,
                        "landing": False
                    }
                }
            }
        else:  # normal
            return {
                "accessibility": {
                    "clear_width": 42,
                    "doors": {
                        "entrance": {
                            "width": 36,
                            "threshold": 0.5
                        },
                        "interior": {
                            "width": 32,
                            "threshold": 0.75
                        }
                    },
                    "ramp": {
                        "slope": 1.5,
                        "handrails": True,
                        "landing": True
                    }
                }
            }
    
    def _generate_energy_test_data(self, scenario: str) -> Dict[str, Any]:
        """Generate energy test data"""
        if scenario == "passing":
            return {
                "energy": {
                    "insulation": {
                        "walls": 30,
                        "roof": 40,
                        "floor": 25
                    },
                    "windows": {
                        "u_factor": 0.25,
                        "shgc": 0.15,
                        "air_leakage": 0.1
                    },
                    "hvac": {
                        "efficiency": 0.95,
                        "duct_sealing": True
                    }
                }
            }
        elif scenario == "failing":
            return {
                "energy": {
                    "insulation": {
                        "walls": 10,
                        "roof": 15,
                        "floor": 8
                    },
                    "windows": {
                        "u_factor": 0.50,
                        "shgc": 0.40,
                        "air_leakage": 0.5
                    },
                    "hvac": {
                        "efficiency": 0.70,
                        "duct_sealing": False
                    }
                }
            }
        else:  # normal
            return {
                "energy": {
                    "insulation": {
                        "walls": 25,
                        "roof": 35,
                        "floor": 20
                    },
                    "windows": {
                        "u_factor": 0.30,
                        "shgc": 0.20,
                        "air_leakage": 0.2
                    },
                    "hvac": {
                        "efficiency": 0.85,
                        "duct_sealing": True
                    }
                }
            }
    
    def _generate_general_test_data(self, scenario: str) -> Dict[str, Any]:
        """Generate general test data"""
        if scenario == "passing":
            return {
                "building_type": "commercial",
                "floors": 5,
                "occupancy": "office",
                "area": 50000,
                "height": 60
            }
        elif scenario == "failing":
            return {
                "building_type": "residential",
                "floors": 2,
                "occupancy": "single_family",
                "area": 2000,
                "height": 20
            }
        else:  # normal
            return {
                "building_type": "mixed_use",
                "floors": 3,
                "occupancy": "retail",
                "area": 15000,
                "height": 35
            }
    
    def run_single_rule_test(self, rule: RuleDefinition, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single rule test"""
        start_time = time.time()
        
        try:
            result = self.rule_engine.test_rule(rule, test_data)
            execution_time = time.time() - start_time
            
            result['execution_time'] = execution_time
            result['rule_name'] = rule.rule_name
            result['rule_type'] = rule.rule_type
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'rule_name': rule.rule_name,
                'rule_type': rule.rule_type,
                'passed': False,
                'message': f"Test execution error: {str(e)}",
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
    
    def run_comprehensive_test(self, rules: List[RuleDefinition], scenarios: List[str] = None) -> Dict[str, Any]:
        """Run comprehensive testing across all rules and scenarios"""
        if scenarios is None:
            scenarios = ["passing", "failing", "normal"]
        
        print(f"Running comprehensive test with {len(rules)} rules and {len(scenarios)} scenarios...")
        
        results = {
            'summary': {
                'total_rules': len(rules),
                'total_tests': len(rules) * len(scenarios),
                'passed_tests': 0,
                'failed_tests': 0,
                'error_tests': 0,
                'total_execution_time': 0
            },
            'rule_results': {},
            'scenario_results': {},
            'performance_metrics': {}
        }
        
        # Test each rule against each scenario
        for rule in rules:
            rule_results = []
            
            for scenario in scenarios:
                test_data = self.generate_test_data(rule.rule_type, scenario)
                test_result = self.run_single_rule_test(rule, test_data)
                
                rule_results.append(test_result)
                results['summary']['total_execution_time'] += test_result.get('execution_time', 0)
                
                # Update summary counts
                if test_result.get('passed', False):
                    results['summary']['passed_tests'] += 1
                elif 'error' in test_result.get('message', '').lower():
                    results['summary']['error_tests'] += 1
                else:
                    results['summary']['failed_tests'] += 1
            
            results['rule_results'][rule.rule_name] = rule_results
        
        # Calculate scenario results
        for scenario in scenarios:
            scenario_passed = 0
            scenario_failed = 0
            
            for rule_name, rule_results in results['rule_results'].items():
                for result in rule_results:
                    if result.get('passed', False):
                        scenario_passed += 1
                    else:
                        scenario_failed += 1
            
            results['scenario_results'][scenario] = {
                'passed': scenario_passed,
                'failed': scenario_failed,
                'total': scenario_passed + scenario_failed
            }
        
        # Calculate performance metrics
        avg_execution_time = results['summary']['total_execution_time'] / results['summary']['total_tests']
        results['performance_metrics'] = {
            'average_execution_time': avg_execution_time,
            'total_execution_time': results['summary']['total_execution_time'],
            'tests_per_second': results['summary']['total_tests'] / results['summary']['total_execution_time'] if results['summary']['total_execution_time'] > 0 else 0
        }
        
        return results
    
    def run_performance_benchmark(self, rules: List[RuleDefinition], iterations: int = 100) -> Dict[str, Any]:
        """Run performance benchmarking"""
        print(f"Running performance benchmark with {len(rules)} rules, {iterations} iterations...")
        
        benchmark_results = {
            'total_iterations': iterations,
            'total_rules': len(rules),
            'execution_times': [],
            'rule_performance': {}
        }
        
        # Generate test data once
        test_data_cache = {}
        for rule in rules:
            test_data_cache[rule.rule_name] = self.generate_test_data(rule.rule_type, "normal")
        
        # Benchmark each rule
        for rule in rules:
            rule_times = []
            
            for i in range(iterations):
                start_time = time.time()
                self.rule_engine.execute_rule(rule, test_data_cache[rule.rule_name])
                execution_time = time.time() - start_time
                rule_times.append(execution_time)
            
            # Calculate statistics
            avg_time = sum(rule_times) / len(rule_times)
            min_time = min(rule_times)
            max_time = max(rule_times)
            
            benchmark_results['rule_performance'][rule.rule_name] = {
                'average_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'total_time': sum(rule_times),
                'iterations_per_second': iterations / sum(rule_times)
            }
            
            benchmark_results['execution_times'].extend(rule_times)
        
        # Overall statistics
        all_times = benchmark_results['execution_times']
        benchmark_results['overall'] = {
            'total_execution_time': sum(all_times),
            'average_execution_time': sum(all_times) / len(all_times),
            'min_execution_time': min(all_times),
            'max_execution_time': max(all_times),
            'total_operations': len(all_times),
            'operations_per_second': len(all_times) / sum(all_times)
        }
        
        return benchmark_results
    
    def generate_test_report(self, test_results: Dict[str, Any], output_file: str = None) -> str:
        """Generate a comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("BUILDING CODE RULE ENGINE TEST REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        summary = test_results['summary']
        report.append("SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Rules Tested: {summary['total_rules']}")
        report.append(f"Total Tests: {summary['total_tests']}")
        report.append(f"Passed: {summary['passed_tests']}")
        report.append(f"Failed: {summary['failed_tests']}")
        report.append(f"Errors: {summary['error_tests']}")
        report.append(f"Success Rate: {(summary['passed_tests'] / summary['total_tests'] * 100):.1f}%")
        report.append(f"Total Execution Time: {summary['total_execution_time']:.3f}s")
        report.append("")
        
        # Performance metrics
        if 'performance_metrics' in test_results:
            perf = test_results['performance_metrics']
            report.append("PERFORMANCE METRICS")
            report.append("-" * 40)
            report.append(f"Average Execution Time: {perf['average_execution_time']:.6f}s")
            report.append(f"Tests per Second: {perf['tests_per_second']:.1f}")
            report.append("")
        
        # Rule results
        report.append("RULE RESULTS")
        report.append("-" * 40)
        for rule_name, rule_results in test_results['rule_results'].items():
            passed_count = sum(1 for r in rule_results if r.get('passed', False))
            total_count = len(rule_results)
            success_rate = (passed_count / total_count * 100) if total_count > 0 else 0
            
            report.append(f"{rule_name}:")
            report.append(f"  Success Rate: {success_rate:.1f}% ({passed_count}/{total_count})")
            
            # Show failures
            failures = [r for r in rule_results if not r.get('passed', False)]
            if failures:
                report.append("  Failures:")
                for failure in failures:
                    report.append(f"    - {failure.get('message', 'Unknown error')}")
            report.append("")
        
        # Scenario results
        if 'scenario_results' in test_results:
            report.append("SCENARIO RESULTS")
            report.append("-" * 40)
            for scenario, scenario_data in test_results['scenario_results'].items():
                total = scenario_data['total']
                passed = scenario_data['passed']
                success_rate = (passed / total * 100) if total > 0 else 0
                report.append(f"{scenario.capitalize()}: {success_rate:.1f}% ({passed}/{total})")
            report.append("")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"Test report saved to: {output_file}")
        
        return report_text
    
    def run_regression_test(self, baseline_file: str, current_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run regression testing against baseline"""
        try:
            with open(baseline_file, 'r') as f:
                baseline_results = json.load(f)
            
            regression_results = {
                'baseline_file': baseline_file,
                'comparison_date': datetime.now().isoformat(),
                'changes': {},
                'performance_changes': {}
            }
            
            # Compare test results
            baseline_summary = baseline_results.get('summary', {})
            current_summary = current_results.get('summary', {})
            
            for key in ['passed_tests', 'failed_tests', 'error_tests']:
                baseline_val = baseline_summary.get(key, 0)
                current_val = current_summary.get(key, 0)
                change = current_val - baseline_val
                
                regression_results['changes'][key] = {
                    'baseline': baseline_val,
                    'current': current_val,
                    'change': change,
                    'percentage_change': (change / baseline_val * 100) if baseline_val > 0 else 0
                }
            
            # Compare performance
            baseline_perf = baseline_results.get('performance_metrics', {})
            current_perf = current_results.get('performance_metrics', {})
            
            for key in ['average_execution_time', 'tests_per_second']:
                if key in baseline_perf and key in current_perf:
                    baseline_val = baseline_perf[key]
                    current_val = current_perf[key]
                    change = current_val - baseline_val
                    
                    regression_results['performance_changes'][key] = {
                        'baseline': baseline_val,
                        'current': current_val,
                        'change': change,
                        'percentage_change': (change / baseline_val * 100) if baseline_val > 0 else 0
                    }
            
            return regression_results
            
        except Exception as e:
            return {
                'error': f"Regression test failed: {str(e)}",
                'baseline_file': baseline_file
            }


def main():
    parser = argparse.ArgumentParser(description="Comprehensive testing utility for building code rule engine")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Comprehensive test command
    test_parser = subparsers.add_parser('test', help='Run comprehensive testing')
    test_parser.add_argument('rules_dir', help='Directory containing rule files')
    test_parser.add_argument('--scenarios', nargs='+', default=['passing', 'failing', 'normal'], 
                           help='Test scenarios to run')
    test_parser.add_argument('--output', help='Output file for test report')
    test_parser.add_argument('--format', choices=['text', 'json'], default='text', 
                           help='Output format')
    
    # Performance benchmark command
    benchmark_parser = subparsers.add_parser('benchmark', help='Run performance benchmarking')
    benchmark_parser.add_argument('rules_dir', help='Directory containing rule files')
    benchmark_parser.add_argument('--iterations', type=int, default=100, 
                                help='Number of iterations for benchmarking')
    benchmark_parser.add_argument('--output', help='Output file for benchmark results')
    
    # Regression test command
    regression_parser = subparsers.add_parser('regression', help='Run regression testing')
    regression_parser.add_argument('rules_dir', help='Directory containing rule files')
    regression_parser.add_argument('baseline_file', help='Baseline results file')
    regression_parser.add_argument('--output', help='Output file for regression results')
    
    # Generate test data command
    data_parser = subparsers.add_parser('generate-data', help='Generate test data')
    data_parser.add_argument('rule_type', help='Type of rule (structural, fire_safety, etc.)')
    data_parser.add_argument('scenario', help='Test scenario (passing, failing, normal)')
    data_parser.add_argument('--output', help='Output file for test data')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    tester = RuleEngineTester()
    
    try:
        if args.command == 'test':
            # Load rules
            rules = tester.load_test_rules(args.rules_dir)
            if not rules:
                print("No rules loaded. Exiting.")
                return
            
            # Run comprehensive test
            results = tester.run_comprehensive_test(rules, args.scenarios)
            
            # Generate report
            if args.format == 'json':
                report_data = {
                    'test_results': results,
                    'generated_at': datetime.now().isoformat()
                }
                report_text = json.dumps(report_data, indent=2)
            else:
                report_text = tester.generate_test_report(results, args.output)
            
            if not args.output:
                print(report_text)
            
        elif args.command == 'benchmark':
            # Load rules
            rules = tester.load_test_rules(args.rules_dir)
            if not rules:
                print("No rules loaded. Exiting.")
                return
            
            # Run benchmark
            benchmark_results = tester.run_performance_benchmark(rules, args.iterations)
            
            # Output results
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(benchmark_results, f, indent=2)
                print(f"Benchmark results saved to: {args.output}")
            else:
                print(json.dumps(benchmark_results, indent=2))
            
        elif args.command == 'regression':
            # Load rules
            rules = tester.load_test_rules(args.rules_dir)
            if not rules:
                print("No rules loaded. Exiting.")
                return
            
            # Run current tests
            current_results = tester.run_comprehensive_test(rules)
            
            # Run regression test
            regression_results = tester.run_regression_test(args.baseline_file, current_results)
            
            # Output results
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(regression_results, f, indent=2)
                print(f"Regression results saved to: {args.output}")
            else:
                print(json.dumps(regression_results, indent=2))
            
        elif args.command == 'generate-data':
            # Generate test data
            test_data = tester.generate_test_data(args.rule_type, args.scenario)
            
            # Output data
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(test_data, f, indent=2)
                print(f"Test data saved to: {args.output}")
            else:
                print(json.dumps(test_data, indent=2))
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main() 