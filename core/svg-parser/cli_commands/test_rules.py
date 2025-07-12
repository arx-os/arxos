"""
CLI tool for testing building code rules with comprehensive scenarios and reporting.
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from ..services.rule_engine import EnhancedRuleEngine
from ..utils.test_data_generator import TestDataGenerator, TestScenario


def main():
    parser = argparse.ArgumentParser(description="Test building code rules with comprehensive scenarios")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test single rule command
    single_parser = subparsers.add_parser('test-rule', help='Test a single rule')
    single_parser.add_argument('rule_name', help='Name of the rule to test')
    single_parser.add_argument('--rules-dir', required=True, help='Directory containing rule files')
    single_parser.add_argument('--scenarios', nargs='+', default=['passing', 'failing', 'normal'],
                              help='Test scenarios to run')
    single_parser.add_argument('--output', help='Output file for test results')
    
    # Test all rules command
    all_parser = subparsers.add_parser('test-all', help='Test all rules in a directory')
    all_parser.add_argument('--rules-dir', required=True, help='Directory containing rule files')
    all_parser.add_argument('--scenarios', nargs='+', default=['passing', 'failing', 'normal'],
                           help='Test scenarios to run')
    all_parser.add_argument('--output', help='Output file for test results')
    all_parser.add_argument('--format', choices=['text', 'json', 'html'], default='text',
                           help='Output format')
    
    # Generate test data command
    data_parser = subparsers.add_parser('generate-data', help='Generate test data for rules')
    data_parser.add_argument('--rule-types', nargs='+', 
                            choices=['structural', 'fire_safety', 'accessibility', 'energy'],
                            default=['structural', 'fire_safety', 'accessibility', 'energy'],
                            help='Rule types to generate data for')
    data_parser.add_argument('--output', default='test_data.json',
                            help='Output file for test data')
    
    # Validate rules command
    validate_parser = subparsers.add_parser('validate', help='Validate rule definitions')
    validate_parser.add_argument('--rules-dir', required=True, help='Directory containing rule files')
    validate_parser.add_argument('--output', help='Output file for validation results')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'test-rule':
            test_single_rule(args)
        elif args.command == 'test-all':
            test_all_rules(args)
        elif args.command == 'generate-data':
            generate_test_data(args)
        elif args.command == 'validate':
            validate_rules(args)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def test_single_rule(args):
    """Test a single rule with various scenarios"""
    rule_engine = EnhancedRuleEngine()
    data_generator = TestDataGenerator()
    
    # Load rules
    rules = rule_engine.load_rules_from_directory(args.rules_dir)
    rule = rule_engine.get_rule(args.rule_name)
    
    if not rule:
        print(f"Rule '{args.rule_name}' not found")
        return
    
    print(f"Testing rule: {args.rule_name}")
    print(f"Rule type: {rule.rule_type}")
    print(f"Scenarios: {', '.join(args.scenarios)}")
    print("-" * 50)
    
    results = {
        'rule_name': args.rule_name,
        'rule_type': rule.rule_type,
        'test_scenarios': {},
        'summary': {
            'total_tests': len(args.scenarios),
            'passed': 0,
            'failed': 0,
            'errors': 0
        }
    }
    
    for scenario in args.scenarios:
        print(f"\nScenario: {scenario}")
        
        # Generate test data
        test_data = data_generator.generate_test_data(rule.rule_type, scenario)
        
        # Test the rule
        test_result = rule_engine.test_rule(rule, test_data)
        
        # Store results
        results['test_scenarios'][scenario] = {
            'test_data': test_data,
            'result': test_result
        }
        
        # Update summary
        if test_result.get('passed', False):
            results['summary']['passed'] += 1
            print(f"  ✓ PASSED")
        else:
            if 'error' in test_result.get('message', '').lower():
                results['summary']['errors'] += 1
                print(f"  ✗ ERROR: {test_result.get('message', 'Unknown error')}")
            else:
                results['summary']['failed'] += 1
                print(f"  ✗ FAILED: {test_result.get('message', 'Unknown failure')}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Total tests: {results['summary']['total_tests']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Errors: {results['summary']['errors']}")
    success_rate = (results['summary']['passed'] / results['summary']['total_tests'] * 100) if results['summary']['total_tests'] > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")


def test_all_rules(args):
    """Test all rules in a directory"""
    rule_engine = EnhancedRuleEngine()
    data_generator = TestDataGenerator()
    
    # Load rules
    rules = rule_engine.load_rules_from_directory(args.rules_dir)
    
    if not rules:
        print("No rules found in directory")
        return
    
    print(f"Testing {len(rules)} rules")
    print(f"Scenarios: {', '.join(args.scenarios)}")
    print("=" * 60)
    
    results = {
        'metadata': {
            'test_date': datetime.now().isoformat(),
            'rules_directory': args.rules_dir,
            'scenarios': args.scenarios,
            'total_rules': len(rules)
        },
        'rule_results': {},
        'summary': {
            'total_tests': len(rules) * len(args.scenarios),
            'passed': 0,
            'failed': 0,
            'errors': 0
        },
        'rule_type_summary': {}
    }
    
    # Test each rule
    for rule in rules:
        print(f"\nTesting rule: {rule.rule_name}")
        
        rule_results = {
            'rule_name': rule.rule_name,
            'rule_type': rule.rule_type,
            'scenarios': {},
            'summary': {
                'passed': 0,
                'failed': 0,
                'errors': 0
            }
        }
        
        for scenario in args.scenarios:
            # Generate test data
            test_data = data_generator.generate_test_data(rule.rule_type, scenario)
            
            # Test the rule
            test_result = rule_engine.test_rule(rule, test_data)
            
            # Store scenario result
            rule_results['scenarios'][scenario] = {
                'test_data': test_data,
                'result': test_result
            }
            
            # Update rule summary
            if test_result.get('passed', False):
                rule_results['summary']['passed'] += 1
                results['summary']['passed'] += 1
            else:
                if 'error' in test_result.get('message', '').lower():
                    rule_results['summary']['errors'] += 1
                    results['summary']['errors'] += 1
                else:
                    rule_results['summary']['failed'] += 1
                    results['summary']['failed'] += 1
        
        # Store rule results
        results['rule_results'][rule.rule_name] = rule_results
        
        # Print rule summary
        total_scenarios = len(args.scenarios)
        rule_success_rate = (rule_results['summary']['passed'] / total_scenarios * 100) if total_scenarios > 0 else 0
        print(f"  Success rate: {rule_success_rate:.1f}% ({rule_results['summary']['passed']}/{total_scenarios})")
    
    # Calculate rule type summary
    for rule_name, rule_result in results['rule_results'].items():
        rule_type = rule_result['rule_type']
        if rule_type not in results['rule_type_summary']:
            results['rule_type_summary'][rule_type] = {
                'total_rules': 0,
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0
            }
        
        rule_type_summary = results['rule_type_summary'][rule_type]
        rule_type_summary['total_rules'] += 1
        rule_type_summary['total_tests'] += len(args.scenarios)
        rule_type_summary['passed'] += rule_result['summary']['passed']
        rule_type_summary['failed'] += rule_result['summary']['failed']
        rule_type_summary['errors'] += rule_result['summary']['errors']
    
    # Print overall summary
    print("\n" + "=" * 60)
    print("OVERALL TEST SUMMARY")
    print("=" * 60)
    print(f"Total rules tested: {len(rules)}")
    print(f"Total tests: {results['summary']['total_tests']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Errors: {results['summary']['errors']}")
    overall_success_rate = (results['summary']['passed'] / results['summary']['total_tests'] * 100) if results['summary']['total_tests'] > 0 else 0
    print(f"Overall success rate: {overall_success_rate:.1f}%")
    
    # Print rule type summary
    print("\nRULE TYPE SUMMARY")
    print("-" * 40)
    for rule_type, summary in results['rule_type_summary'].items():
        type_success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        print(f"{rule_type}: {type_success_rate:.1f}% ({summary['passed']}/{summary['total_tests']}) - {summary['total_rules']} rules")
    
    # Save results
    if args.output:
        if args.format == 'json':
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
        elif args.format == 'html':
            html_content = generate_html_report(results)
            with open(args.output, 'w') as f:
                f.write(html_content)
        else:  # text format
            with open(args.output, 'w') as f:
                f.write(generate_text_report(results))
        
        print(f"\nResults saved to: {args.output}")


def generate_test_data(args):
    """Generate test data for rules"""
    data_generator = TestDataGenerator()
    
    print(f"Generating test data for rule types: {', '.join(args.rule_types)}")
    
    test_suite = data_generator.generate_comprehensive_test_suite(args.rule_types)
    data_generator.save_test_suite(test_suite, args.output)
    
    print(f"Generated {test_suite['metadata']['total_scenarios']} test scenarios")


def validate_rules(args):
    """Validate rule definitions"""
    rule_engine = EnhancedRuleEngine()
    
    print(f"Validating rules in directory: {args.rules_dir}")
    
    # Load rules
    rules = rule_engine.load_rules_from_directory(args.rules_dir)
    
    validation_results = {
        'metadata': {
            'validation_date': datetime.now().isoformat(),
            'rules_directory': args.rules_dir,
            'total_rules': len(rules)
        },
        'validation_results': {},
        'summary': {
            'valid': 0,
            'invalid': 0,
            'total_errors': 0
        }
    }
    
    for rule in rules:
        print(f"\nValidating rule: {rule.rule_name}")
        
        # Validate rule definition
        rule_data = {
            'rule_name': rule.rule_name,
            'rule_type': rule.rule_type,
            'version': rule.version,
            'description': rule.description,
            'severity': rule.severity,
            'priority': rule.priority,
            'conditions': rule.conditions,
            'actions': rule.actions,
            'enabled': rule.enabled
        }
        
        errors = rule_engine.validate_rule_definition(rule_data)
        
        validation_result = {
            'rule_name': rule.rule_name,
            'rule_type': rule.rule_type,
            'valid': len(errors) == 0,
            'errors': errors,
            'error_count': len(errors)
        }
        
        validation_results['validation_results'][rule.rule_name] = validation_result
        
        if len(errors) == 0:
            validation_results['summary']['valid'] += 1
            print(f"  ✓ VALID")
        else:
            validation_results['summary']['invalid'] += 1
            validation_results['summary']['total_errors'] += len(errors)
            print(f"  ✗ INVALID ({len(errors)} errors)")
            for error in errors:
                print(f"    - {error}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Total rules: {validation_results['summary']['valid'] + validation_results['summary']['invalid']}")
    print(f"Valid: {validation_results['summary']['valid']}")
    print(f"Invalid: {validation_results['summary']['invalid']}")
    print(f"Total errors: {validation_results['summary']['total_errors']}")
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(validation_results, f, indent=2)
        print(f"\nValidation results saved to: {args.output}")


def generate_html_report(results: Dict[str, Any]) -> str:
    """Generate HTML report from test results"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Building Code Rule Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .rule-type {{ background-color: #f8f8f8; padding: 10px; margin: 10px 0; border-radius: 3px; }}
        .rule {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ddd; }}
        .rule.passed {{ border-left-color: #4caf50; }}
        .rule.failed {{ border-left-color: #f44336; }}
        .scenario {{ margin: 5px 0; padding: 5px; }}
        .scenario.passed {{ color: #4caf50; }}
        .scenario.failed {{ color: #f44336; }}
        .scenario.error {{ color: #ff9800; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Building Code Rule Test Report</h1>
        <p>Generated: {results['metadata']['test_date']}</p>
        <p>Rules Directory: {results['metadata']['rules_directory']}</p>
        <p>Total Rules: {results['metadata']['total_rules']}</p>
    </div>
    
    <div class="summary">
        <h2>Overall Summary</h2>
        <p>Total Tests: {results['summary']['total_tests']}</p>
        <p>Passed: {results['summary']['passed']}</p>
        <p>Failed: {results['summary']['failed']}</p>
        <p>Errors: {results['summary']['errors']}</p>
        <p>Success Rate: {(results['summary']['passed'] / results['summary']['total_tests'] * 100):.1f}%</p>
    </div>
"""
    
    # Add rule type summary
    html += "<h2>Rule Type Summary</h2>"
    for rule_type, summary in results['rule_type_summary'].items():
        success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        html += f"""
        <div class="rule-type">
            <h3>{rule_type}</h3>
            <p>Success Rate: {success_rate:.1f}% ({summary['passed']}/{summary['total_tests']}) - {summary['total_rules']} rules</p>
        </div>
        """
    
    # Add detailed rule results
    html += "<h2>Detailed Results</h2>"
    for rule_name, rule_result in results['rule_results'].items():
        total_scenarios = len(rule_result['scenarios'])
        success_rate = (rule_result['summary']['passed'] / total_scenarios * 100) if total_scenarios > 0 else 0
        status_class = "passed" if success_rate == 100 else "failed"
        
        html += f"""
        <div class="rule {status_class}">
            <h3>{rule_name} ({rule_result['rule_type']})</h3>
            <p>Success Rate: {success_rate:.1f}% ({rule_result['summary']['passed']}/{total_scenarios})</p>
        """
        
        for scenario_name, scenario_result in rule_result['scenarios'].items():
            result = scenario_result['result']
            scenario_class = "passed" if result.get('passed', False) else "failed"
            if 'error' in result.get('message', '').lower():
                scenario_class = "error"
            
            html += f"""
            <div class="scenario {scenario_class}">
                <strong>{scenario_name}:</strong> {result.get('message', 'No message')}
            </div>
            """
        
        html += "</div>"
    
    html += """
</body>
</html>
"""
    return html


def generate_text_report(results: Dict[str, Any]) -> str:
    """Generate text report from test results"""
    report = []
    report.append("BUILDING CODE RULE TEST REPORT")
    report.append("=" * 60)
    report.append(f"Generated: {results['metadata']['test_date']}")
    report.append(f"Rules Directory: {results['metadata']['rules_directory']}")
    report.append(f"Total Rules: {results['metadata']['total_rules']}")
    report.append("")
    
    # Overall summary
    report.append("OVERALL SUMMARY")
    report.append("-" * 40)
    report.append(f"Total Tests: {results['summary']['total_tests']}")
    report.append(f"Passed: {results['summary']['passed']}")
    report.append(f"Failed: {results['summary']['failed']}")
    report.append(f"Errors: {results['summary']['errors']}")
    success_rate = (results['summary']['passed'] / results['summary']['total_tests'] * 100) if results['summary']['total_tests'] > 0 else 0
    report.append(f"Success Rate: {success_rate:.1f}%")
    report.append("")
    
    # Rule type summary
    report.append("RULE TYPE SUMMARY")
    report.append("-" * 40)
    for rule_type, summary in results['rule_type_summary'].items():
        type_success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        report.append(f"{rule_type}: {type_success_rate:.1f}% ({summary['passed']}/{summary['total_tests']}) - {summary['total_rules']} rules")
    report.append("")
    
    # Detailed results
    report.append("DETAILED RESULTS")
    report.append("-" * 40)
    for rule_name, rule_result in results['rule_results'].items():
        total_scenarios = len(rule_result['scenarios'])
        success_rate = (rule_result['summary']['passed'] / total_scenarios * 100) if total_scenarios > 0 else 0
        
        report.append(f"{rule_name} ({rule_result['rule_type']}): {success_rate:.1f}% ({rule_result['summary']['passed']}/{total_scenarios})")
        
        for scenario_name, scenario_result in rule_result['scenarios'].items():
            result = scenario_result['result']
            status = "PASS" if result.get('passed', False) else "FAIL"
            if 'error' in result.get('message', '').lower():
                status = "ERROR"
            
            report.append(f"  {scenario_name}: {status} - {result.get('message', 'No message')}")
        
        report.append("")
    
    return "\n".join(report)


if __name__ == '__main__':
    main() 