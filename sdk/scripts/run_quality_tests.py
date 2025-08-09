#!/usr/bin/env python3
"""
Quality test runner for SDKs
Executes all quality tests and generates comprehensive reports
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import argparse
import sys

class QualityTestRunner:
    """Quality test runner for SDKs"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or "sdk/generator/config/quality.yaml"
        self.results = {}
        self.start_time = time.time()

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all quality tests"""
        print("🚀 Starting Quality Test Suite")
        print("=" * 50)

        # Test categories
        test_categories = [
            ("unit", "Unit Tests"),
            ("integration", "Integration Tests"),
            ("performance", "Performance Tests"),
            ("quality", "Code Quality Tests"),
            ("coverage", "Coverage Tests")
        ]

        for category, description in test_categories:
            print(f"\n📋 Running {description}")
            print("-" * 30)

            self.results[category] = self.run_category_tests(category)

        # Generate summary report
        self.generate_summary_report()

        return self.results

    def run_category_tests(self, category: str) -> Dict[str, Any]:
        """Run tests for a specific category"""
        category_results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0,
            "duration": 0,
            "details": []
        }

        # Find test files for category
        test_dir = Path(f"sdk/tests/{category}")
        if not test_dir.exists():
            print(f"  ⚠️  No tests found for category: {category}")
            return category_results

        test_files = list(test_dir.rglob("test_*.py"))

        if not test_files:
            print(f"  ⚠️  No test files found in {test_dir}")
            return category_results

        print(f"  📁 Found {len(test_files)} test files")

        for test_file in test_files:
            result = self.run_test_file(test_file, category)
            category_results["details"].append(result)

            if result["status"] == "passed":
                category_results["passed"] += 1
            elif result["status"] == "failed":
                category_results["failed"] += 1
            else:
                category_results["skipped"] += 1

            category_results["total"] += 1
            category_results["duration"] += result["duration"]

        # Print category summary
        print(f"  ✅ Passed: {category_results['passed']}")
        print(f"  ❌ Failed: {category_results['failed']}")
        print(f"  ⏭️  Skipped: {category_results['skipped']}")
        print(f"  ⏱️  Duration: {category_results['duration']:.2f}s")

        return category_results

    def run_test_file(self, test_file: Path, category: str) -> Dict[str, Any]:
        """Run a single test file"""
        result = {
            "file": str(test_file),
            "category": category,
            "status": "unknown",
            "duration": 0,
            "output": "",
            "error": ""
        }

        start_time = time.time()

        try:
            # Run pytest on the test file
            cmd = [
                "python", "-m", "pytest", str(test_file),
                "-v", "--tb=short", "--json-report"
            ]

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            end_time = time.time()
            result["duration"] = end_time - start_time
            result["output"] = process.stdout
            result["error"] = process.stderr

            if process.returncode == 0:
                result["status"] = "passed"
                print(f"    ✅ {test_file.name}")
            else:
                result["status"] = "failed"
                print(f"    ❌ {test_file.name}")

        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["error"] = "Test timed out after 5 minutes"
            print(f"    ⏰ {test_file.name} (timeout)")

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"    💥 {test_file.name} (error)")

        return result

    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "=" * 50)
        print("📊 Quality Test Summary Report")
        print("=" * 50)

        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_duration = 0

        for category, results in self.results.items():
            total_passed += results["passed"]
            total_failed += results["failed"]
            total_skipped += results["skipped"]
            total_duration += results["duration"]

            print(f"\n📋 {category.upper()} TESTS:")
            print(f"  ✅ Passed: {results['passed']}")
            print(f"  ❌ Failed: {results['failed']}")
            print(f"  ⏭️  Skipped: {results['skipped']}")
            print(f"  ⏱️  Duration: {results['duration']:.2f}s")

            # Show failed tests
            failed_tests = [r for r in results["details"] if r["status"] == "failed"]
            if failed_tests:
                print("  ❌ Failed Tests:")
                for test in failed_tests:
                    print(f"    - {test['file']}")
                    if test["error"]:
                        print(f"      Error: {test['error'][:100]}...")

        total_tests = total_passed + total_failed + total_skipped
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        print(f"\n🎯 OVERALL SUMMARY:")
        print(f"  ✅ Total Passed: {total_passed}")
        print(f"  ❌ Total Failed: {total_failed}")
        print(f"  ⏭️  Total Skipped: {total_skipped}")
        print(f"  📊 Success Rate: {success_rate:.1f}%")
        print(f"  ⏱️  Total Duration: {total_duration:.2f}s")

        # Quality gates
        self.check_quality_gates()

        # Save detailed report
        self.save_detailed_report()

        # Exit with appropriate code
        if total_failed > 0:
            print(f"\n❌ Quality tests failed: {total_failed} failures")
            sys.exit(1)
        else:
            print(f"\n✅ All quality tests passed!")
            sys.exit(0)

    def check_quality_gates(self):
        """Check quality gates"""
        print(f"\n🚦 QUALITY GATES:")

        gates = {
            "Success Rate": self.get_success_rate() >= 90,
            "No Critical Failures": self.get_critical_failures() == 0,
            "Performance Tests Pass": self.check_performance_gates(),
            "Coverage Threshold": self.check_coverage_gates(),
            "Code Quality": self.check_code_quality_gates()
        }

        all_passed = True
        for gate_name, passed in gates.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {gate_name}: {status}")
            if not passed:
                all_passed = False

        if all_passed:
            print("  🎉 All quality gates passed!")
        else:
            print("  ⚠️  Some quality gates failed")

    def get_success_rate(self) -> float:
        """Calculate overall success rate"""
        total_passed = sum(r["passed"] for r in self.results.values())
        total_tests = sum(r["total"] for r in self.results.values())
        return (total_passed / total_tests * 100) if total_tests > 0 else 0

    def get_critical_failures(self) -> int:
        """Count critical failures"""
        critical_failures = 0
        for category, results in self.results.items():
            for test in results["details"]:
                if test["status"] == "failed" and "critical" in test["file"].lower():
                    critical_failures += 1
        return critical_failures

    def check_performance_gates(self) -> bool:
        """Check performance test gates"""
        if "performance" not in self.results:
            return True

        perf_results = self.results["performance"]
        return perf_results["failed"] == 0

    def check_coverage_gates(self) -> bool:
        """Check coverage test gates"""
        if "coverage" not in self.results:
            return True

        coverage_results = self.results["coverage"]
        return coverage_results["failed"] == 0

    def check_code_quality_gates(self) -> bool:
        """Check code quality test gates"""
        if "quality" not in self.results:
            return True

        quality_results = self.results["quality"]
        return quality_results["failed"] == 0

    def save_detailed_report(self):
        """Save detailed report to file"""
        report_data = {
            "timestamp": time.time(),
            "duration": time.time() - self.start_time,
            "results": self.results,
            "summary": {
                "total_passed": sum(r["passed"] for r in self.results.values()),
                "total_failed": sum(r["failed"] for r in self.results.values()),
                "total_skipped": sum(r["skipped"] for r in self.results.values()),
                "success_rate": self.get_success_rate()
            }
        }

        report_path = Path("sdk/quality_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_path}")

    def run_specific_tests(self, test_patterns: List[str]):
        """Run specific tests based on patterns"""
        print(f"🎯 Running specific tests: {test_patterns}")

        for pattern in test_patterns:
            test_files = list(Path("sdk/tests").rglob(f"*{pattern}*.py"))

            if not test_files:
                print(f"  ⚠️  No tests found matching pattern: {pattern}")
                continue

            print(f"  📁 Found {len(test_files)} test files for pattern: {pattern}")

            for test_file in test_files:
                result = self.run_test_file(test_file, "specific")
                print(f"    {'✅' if result['status'] == 'passed' else '❌'} {test_file.name}")

    def run_language_specific_tests(self, language: str):
        """Run tests for a specific language"""
        print(f"🔤 Running tests for language: {language}")

        # Find language-specific tests
        test_patterns = [
            f"test_{language}_sdk.py",
            f"test_{language}_*.py",
            f"*{language}*.py"
        ]

        found_tests = []
        for pattern in test_patterns:
            test_files = list(Path("sdk/tests").rglob(pattern))
            found_tests.extend(test_files)

        if not found_tests:
            print(f"  ⚠️  No tests found for language: {language}")
            return

        print(f"  📁 Found {len(found_tests)} test files")

        for test_file in found_tests:
            result = self.run_test_file(test_file, f"{language}_specific")
            print(f"    {'✅' if result['status'] == 'passed' else '❌'} {test_file.name}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Quality Test Runner for SDKs")
    parser.add_argument("--config", help="Path to quality config file")
    parser.add_argument("--tests", nargs="+", help="Run specific test patterns")
    parser.add_argument("--language", help="Run tests for specific language")
    parser.add_argument("--category", help="Run tests for specific category")

    args = parser.parse_args()

    runner = QualityTestRunner(args.config)

    if args.tests:
        runner.run_specific_tests(args.tests)
    elif args.language:
        runner.run_language_specific_tests(args.language)
    elif args.category:
        # Run specific category
        runner.results[args.category] = runner.run_category_tests(args.category)
        runner.generate_summary_report()
    else:
        # Run all tests
        runner.run_all_tests()

if __name__ == "__main__":
    main()
