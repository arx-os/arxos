#!/usr/bin/env python3
"""
Command-line tool for testing Symbol Library Zoom Integration

This tool provides a comprehensive testing interface for the zoom integration system,
allowing users to validate symbols, test scaling, and generate reports.
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from services.symbol_zoom_integration import SymbolZoomIntegration


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('zoom_integration_test.log')
        ]
    )


def test_symbol_scaling(integration: SymbolZoomIntegration, symbol_id: str) -> Dict[str, Any]:
    """Test symbol scaling at different zoom levels."""
    print(f"\n🔍 Testing symbol scaling for: {symbol_id}")
    
    zoom_levels = [0.25, 0.5, 1.0, 2.0, 4.0]
    scale_data = integration.validate_symbol_consistency(symbol_id, zoom_levels)
    
    if not scale_data:
        print(f"❌ Symbol '{symbol_id}' not found in library")
        return {"error": f"Symbol '{symbol_id}' not found"}
    
    print(f"✅ Found {len(scale_data)} scale data points")
    
    # Display scaling results
    print("\n📊 Scaling Results:")
    print(f"{'Zoom Level':<12} {'Scale Factor':<12} {'Width':<8} {'Height':<8} {'Consistent':<10}")
    print("-" * 60)
    
    consistent_count = 0
    for data in scale_data:
        status = "✅" if data.is_consistent else "❌"
        print(f"{data.zoom_level:<12} {data.current_scale:<12.3f} {data.actual_width:<8.1f} {data.actual_height:<8.1f} {status:<10}")
        if data.is_consistent:
            consistent_count += 1
    
    print(f"\n📈 Consistency: {consistent_count}/{len(scale_data)} zoom levels ({consistent_count/len(scale_data)*100:.1f}%)")
    
    return {
        "symbol_id": symbol_id,
        "total_tests": len(scale_data),
        "consistent_tests": consistent_count,
        "consistency_percentage": consistent_count / len(scale_data) * 100,
        "scale_data": [vars(data) for data in scale_data]
    }


def test_symbol_placement(integration: SymbolZoomIntegration, symbol_id: str) -> Dict[str, Any]:
    """Test symbol placement at various positions and zoom levels."""
    print(f"\n📍 Testing symbol placement for: {symbol_id}")
    
    # Test positions in a grid pattern
    test_positions = [
        (100, 100), (200, 100), (300, 100),
        (100, 200), (200, 200), (300, 200),
        (100, 300), (200, 300), (300, 300)
    ]
    zoom_levels = [0.5, 1.0, 2.0]
    
    results = integration.test_symbol_placement(symbol_id, test_positions, zoom_levels)
    
    if "error" in results:
        print(f"❌ {results['error']}")
        return results
    
    metrics = results["performance_metrics"]
    print(f"✅ Placement tests completed:")
    print(f"   • Total tests: {metrics['total_tests']}")
    print(f"   • Successful placements: {metrics['successful_placements']}")
    print(f"   • Consistent scaling: {metrics['consistent_scaling']}")
    print(f"   • Average scale factor: {metrics['average_scale_factor']:.3f}")
    
    return results


def fix_symbol_issues(integration: SymbolZoomIntegration, symbol_id: str) -> Dict[str, Any]:
    """Fix scaling issues for a symbol."""
    print(f"\n🔧 Fixing issues for symbol: {symbol_id}")
    
    results = integration.fix_symbol_scaling_issues(symbol_id)
    
    if "error" in results:
        print(f"❌ {results['error']}")
        return results
    
    if results["issues_found"] == 0:
        print("✅ No issues found - symbol is properly configured")
        return results
    
    print(f"⚠️  Found {results['issues_found']} issues:")
    for issue in results["issues"]:
        print(f"   • {issue}")
    
    print(f"\n🔧 Suggested fixes:")
    for fix in results["fixes"]:
        print(f"   • {fix}")
    
    if results["fixed_data"]:
        print(f"\n📝 Fixed symbol data available")
    
    return results


def validate_library(integration: SymbolZoomIntegration) -> Dict[str, Any]:
    """Validate the entire symbol library."""
    print("\n📚 Validating symbol library...")
    
    results = integration.validate_symbol_library()
    
    print(f"📊 Library Validation Results:")
    print(f"   • Total symbols: {results['total_symbols']}")
    print(f"   • Valid symbols: {results['valid_symbols']}")
    print(f"   • Invalid symbols: {results['invalid_symbols']}")
    
    if results["invalid_symbols"] > 0:
        print(f"\n⚠️  Issues found in {len(results['symbol_issues'])} symbols:")
        for symbol_id, issues in results["symbol_issues"].items():
            print(f"   • {symbol_id}: {len(issues)} issues")
    
    if results["recommendations"]:
        print(f"\n💡 Recommendations:")
        for recommendation in results["recommendations"]:
            print(f"   • {recommendation}")
    
    return results


def generate_report(integration: SymbolZoomIntegration, output_file: str = None) -> str:
    """Generate a comprehensive test report."""
    print("\n📄 Generating zoom integration test report...")
    
    report = integration.generate_zoom_test_report()
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Report saved to: {output_file}")
    else:
        print("✅ Report generated (use --output to save to file)")
    
    return report


def list_symbols(integration: SymbolZoomIntegration) -> List[str]:
    """List all available symbols in the library."""
    symbols = integration.load_symbol_library()
    
    print(f"\n📋 Available symbols ({len(symbols)} total):")
    print("-" * 50)
    
    symbol_list = []
    for symbol_id, symbol_data in symbols.items():
        system = symbol_data.get('system', 'unknown')
        display_name = symbol_data.get('display_name', symbol_id)
        print(f"• {symbol_id:<20} ({system:<12}) - {display_name}")
        symbol_list.append(symbol_id)
    
    return symbol_list


def run_comprehensive_test(integration: SymbolZoomIntegration, symbol_ids: List[str] = None) -> Dict[str, Any]:
    """Run comprehensive tests on specified symbols or all symbols."""
    print("\n🚀 Running comprehensive zoom integration tests...")
    
    if not symbol_ids:
        symbols = integration.load_symbol_library()
        symbol_ids = list(symbols.keys())
    
    results = {
        "total_symbols": len(symbol_ids),
        "tested_symbols": 0,
        "passed_symbols": 0,
        "failed_symbols": 0,
        "symbol_results": {},
        "library_validation": None,
        "overall_score": 0.0
    }
    
    # Test each symbol
    for symbol_id in symbol_ids:
        print(f"\n{'='*60}")
        print(f"Testing: {symbol_id}")
        print(f"{'='*60}")
        
        try:
            # Test scaling
            scaling_result = test_symbol_scaling(integration, symbol_id)
            
            # Test placement
            placement_result = test_symbol_placement(integration, symbol_id)
            
            # Fix issues
            fix_result = fix_symbol_issues(integration, symbol_id)
            
            # Determine if symbol passed
            passed = True
            if "error" in scaling_result or "error" in placement_result:
                passed = False
            elif fix_result.get("issues_found", 0) > 0:
                passed = False
            
            results["symbol_results"][symbol_id] = {
                "scaling": scaling_result,
                "placement": placement_result,
                "fixes": fix_result,
                "passed": passed
            }
            
            results["tested_symbols"] += 1
            if passed:
                results["passed_symbols"] += 1
                print(f"✅ {symbol_id}: PASSED")
            else:
                results["failed_symbols"] += 1
                print(f"❌ {symbol_id}: FAILED")
                
        except Exception as e:
            print(f"❌ Error testing {symbol_id}: {e}")
            results["symbol_results"][symbol_id] = {"error": str(e), "passed": False}
            results["tested_symbols"] += 1
            results["failed_symbols"] += 1
    
    # Validate entire library
    print(f"\n{'='*60}")
    print("Library Validation")
    print(f"{'='*60}")
    results["library_validation"] = validate_library(integration)
    
    # Calculate overall score
    if results["tested_symbols"] > 0:
        results["overall_score"] = (results["passed_symbols"] / results["tested_symbols"]) * 100
    
    # Print summary
    print(f"\n{'='*60}")
    print("COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total symbols tested: {results['tested_symbols']}")
    print(f"Passed: {results['passed_symbols']}")
    print(f"Failed: {results['failed_symbols']}")
    print(f"Overall score: {results['overall_score']:.1f}%")
    
    if results["overall_score"] >= 90:
        print("🎉 Excellent! Symbol library is well-integrated with zoom system")
    elif results["overall_score"] >= 75:
        print("👍 Good! Minor issues detected")
    elif results["overall_score"] >= 50:
        print("⚠️  Fair! Several issues need attention")
    else:
        print("❌ Poor! Significant issues detected")
    
    return results


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Test Symbol Library Zoom Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all symbols comprehensively
  python test_zoom_integration.py --comprehensive
  
  # Test specific symbols
  python test_zoom_integration.py --symbol ahu --symbol receptacle
  
  # Generate report
  python test_zoom_integration.py --report --output report.html
  
  # List all symbols
  python test_zoom_integration.py --list
  
  # Fix issues for a symbol
  python test_zoom_integration.py --fix ahu
        """
    )
    
    parser.add_argument(
        "--symbol", "-s",
        action="append",
        help="Test specific symbol(s)"
    )
    
    parser.add_argument(
        "--comprehensive", "-c",
        action="store_true",
        help="Run comprehensive tests on all symbols"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available symbols"
    )
    
    parser.add_argument(
        "--fix", "-f",
        help="Fix issues for a specific symbol"
    )
    
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Validate entire symbol library"
    )
    
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="Generate test report"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file for report"
    )
    
    parser.add_argument(
        "--library-path",
        default="arx-symbol-library",
        help="Path to symbol library (default: arx-symbol-library)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Initialize integration service
    try:
        integration = SymbolZoomIntegration(args.library_path)
    except Exception as e:
        print(f"❌ Failed to initialize integration service: {e}")
        sys.exit(1)
    
    # Execute requested actions
    if args.list:
        list_symbols(integration)
    
    elif args.fix:
        fix_symbol_issues(integration, args.fix)
    
    elif args.validate:
        validate_library(integration)
    
    elif args.report:
        generate_report(integration, args.output)
    
    elif args.comprehensive:
        run_comprehensive_test(integration, args.symbol)
    
    elif args.symbol:
        for symbol_id in args.symbol:
            test_symbol_scaling(integration, symbol_id)
            test_symbol_placement(integration, symbol_id)
            fix_symbol_issues(integration, symbol_id)
    
    else:
        # Default: run comprehensive test
        print("No specific action specified. Running comprehensive test...")
        run_comprehensive_test(integration)


if __name__ == "__main__":
    main() 