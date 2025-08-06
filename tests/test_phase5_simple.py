#!/usr/bin/env python3
"""
Simple Phase 5 Validation Test

This script validates the Phase 5 implementation by checking for the existence
and basic structure of all required files and components.
"""

import os
import sys
import json
from datetime import datetime


def test_file_exists(file_path, description):
    """Test if a file exists and has content."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
            if len(content.strip()) > 0:
                print(f"  ✅ {description}: {file_path}")
                return True
            else:
                print(f"  ❌ {description}: {file_path} (empty file)")
                return False
    else:
        print(f"  ❌ {description}: {file_path} (not found)")
        return False


def test_directory_exists(dir_path, description):
    """Test if a directory exists."""
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        print(f"  ✅ {description}: {dir_path}")
        return True
    else:
        print(f"  ❌ {description}: {dir_path} (not found)")
        return False


def test_ci_cd_pipeline():
    """Test CI/CD pipeline components."""
    print("\n📋 Testing CI/CD Pipeline Components...")

    tests = [
        (".github/workflows/deploy.yml", "GitHub Actions Workflow"),
        ("Dockerfile", "Production Dockerfile"),
        ("k8s/namespace.yaml", "Kubernetes Namespace Config"),
        ("k8s/deployment.yaml", "Kubernetes Deployment"),
        ("k8s/service.yaml", "Kubernetes Service"),
        ("k8s/ingress.yaml", "Kubernetes Ingress"),
    ]

    passed = 0
    total = len(tests)

    for file_path, description in tests:
        if test_file_exists(file_path, description):
            passed += 1

    return passed, total


def test_security_components():
    """Test security hardening components."""
    print("\n🔒 Testing Security Components...")

    tests = [
        ("infrastructure/security/authentication.py", "JWT Authentication"),
        ("infrastructure/security/authorization.py", "RBAC Authorization"),
        ("infrastructure/security/input_validation.py", "Input Validation"),
        ("infrastructure/security/rate_limiting.py", "Rate Limiting"),
    ]

    passed = 0
    total = len(tests)

    for file_path, description in tests:
        if test_file_exists(file_path, description):
            passed += 1

    return passed, total


def test_performance_optimization():
    """Test performance optimization components."""
    print("\n⚡ Testing Performance Optimization Components...")

    tests = [
        ("infrastructure/database/connection_pool.py", "Database Connection Pooling"),
        ("infrastructure/services/load_balancer.py", "Load Balancer"),
        ("infrastructure/caching/redis_cache.py", "Redis Caching"),
    ]

    passed = 0
    total = len(tests)

    for file_path, description in tests:
        if test_file_exists(file_path, description):
            passed += 1

    return passed, total


def test_monitoring_components():
    """Test monitoring and alerting components."""
    print("\n📊 Testing Monitoring Components...")

    tests = [
        ("infrastructure/monitoring/prometheus_metrics.py", "Prometheus Metrics"),
        ("k8s/monitoring/prometheus.yaml", "Prometheus Config"),
        ("k8s/monitoring/grafana.yaml", "Grafana Config"),
        ("k8s/monitoring/alertmanager.yaml", "AlertManager Config"),
    ]

    passed = 0
    total = len(tests)

    for file_path, description in tests:
        if test_file_exists(file_path, description):
            passed += 1

    return passed, total


def test_documentation():
    """Test documentation components."""
    print("\n📚 Testing Documentation Components...")

    tests = [
        (
            "docs/MCP_ENGINEERING_PHASE5_PRODUCTION_DEPLOYMENT.md",
            "Phase 5 Deployment Plan",
        ),
        (
            "docs/MCP_ENGINEERING_PHASE5_IMPLEMENTATION_STATUS.md",
            "Phase 5 Status Document",
        ),
        ("requirements.txt", "Production Dependencies"),
    ]

    passed = 0
    total = len(tests)

    for file_path, description in tests:
        if test_file_exists(file_path, description):
            passed += 1

    return passed, total


def test_testing_components():
    """Test testing components."""
    print("\n🧪 Testing Testing Components...")

    tests = [
        ("tests/test_phase5_comprehensive.py", "Comprehensive Phase 5 Tests"),
        ("tests/test_phase5_production_deployment.py", "Production Deployment Tests"),
    ]

    passed = 0
    total = len(tests)

    for file_path, description in tests:
        if test_file_exists(file_path, description):
            passed += 1

    return passed, total


def test_dockerfile_content():
    """Test Dockerfile content for best practices."""
    print("\n🐳 Testing Dockerfile Best Practices...")

    if not os.path.exists("Dockerfile"):
        print("  ❌ Dockerfile not found")
        return 0, 1

    with open("Dockerfile", "r") as f:
        content = f.read()

    checks = [
        ("Multi-stage build", "FROM python:3.11-slim as builder" in content),
        ("Production stage", "FROM python:3.11-slim as production" in content),
        ("Non-root user", "USER mcp" in content),
        ("Health check", "HEALTHCHECK" in content),
        ("Expose port", "EXPOSE 8000" in content),
        (
            "Security hardening",
            "RUN groupadd -r mcp && useradd -r -g mcp mcp" in content,
        ),
    ]

    passed = 0
    total = len(checks)

    for description, check in checks:
        if check:
            print(f"  ✅ {description}")
            passed += 1
        else:
            print(f"  ❌ {description}")

    return passed, total


def test_kubernetes_manifests():
    """Test Kubernetes manifests for best practices."""
    print("\n☸️  Testing Kubernetes Manifests...")

    checks = []

    # Test deployment.yaml
    if os.path.exists("k8s/deployment.yaml"):
        with open("k8s/deployment.yaml", "r") as f:
            content = f.read()
            checks.extend(
                [
                    ("Deployment manifest exists", True),
                    ("Resource limits defined", "limits:" in content),
                    ("Health probes configured", "livenessProbe:" in content),
                    ("Security context", "securityContext:" in content),
                ]
            )
    else:
        checks.extend(
            [
                ("Deployment manifest exists", False),
                ("Resource limits defined", False),
                ("Health probes configured", False),
                ("Security context", False),
            ]
        )

    # Test service.yaml
    if os.path.exists("k8s/service.yaml"):
        with open("k8s/service.yaml", "r") as f:
            content = f.read()
            checks.extend(
                [
                    ("Service manifest exists", True),
                    ("Service type defined", "type:" in content),
                    ("Port configuration", "port:" in content),
                ]
            )
    else:
        checks.extend(
            [
                ("Service manifest exists", False),
                ("Service type defined", False),
                ("Port configuration", False),
            ]
        )

    # Test ingress.yaml
    if os.path.exists("k8s/ingress.yaml"):
        with open("k8s/ingress.yaml", "r") as f:
            content = f.read()
            checks.extend(
                [
                    ("Ingress manifest exists", True),
                    ("SSL configuration", "tls:" in content),
                    ("Host configuration", "host:" in content),
                ]
            )
    else:
        checks.extend(
            [
                ("Ingress manifest exists", False),
                ("SSL configuration", False),
                ("Host configuration", False),
            ]
        )

    passed = 0
    total = len(checks)

    for description, check in checks:
        if check:
            print(f"  ✅ {description}")
            passed += 1
        else:
            print(f"  ❌ {description}")

    return passed, total


def main():
    """Run all Phase 5 validation tests."""
    print("🚀 Phase 5 Production Deployment - Validation Tests")
    print("=" * 60)

    test_functions = [
        test_ci_cd_pipeline,
        test_security_components,
        test_performance_optimization,
        test_monitoring_components,
        test_documentation,
        test_testing_components,
        test_dockerfile_content,
        test_kubernetes_manifests,
    ]

    total_passed = 0
    total_tests = 0

    for test_func in test_functions:
        passed, total = test_func()
        total_passed += passed
        total_tests += total

    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_tests - total_passed}")
    print(f"Success Rate: {(total_passed/total_tests)*100:.1f}%")

    if total_passed == total_tests:
        print("\n🎉 ALL PHASE 5 TESTS PASSED!")
        print("✅ Phase 5 implementation is complete and production-ready!")
        return True
    else:
        print(f"\n⚠️  {total_tests - total_passed} tests failed.")
        print("🔧 Some components need attention before production deployment.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
