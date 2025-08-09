#!/usr/bin/env python3
"""
Deployment report generator for Arxos platform.
Generates comprehensive deployment reports for CI/CD pipelines.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class DeploymentReportGenerator:
    """Generate comprehensive deployment reports."""

    def __init__(self):
        self.report_data = {
            "timestamp": datetime.now().isoformat(),
            "platform": "Arxos",
            "deployment_type": "enterprise",
            "status": "success",
            "environment": os.getenv("DEPLOYMENT_ENV", "staging"),
            "version": os.getenv("DEPLOYMENT_VERSION", "latest"),
            "commit_sha": os.getenv("GITHUB_SHA", "unknown"),
            "branch": os.getenv("GITHUB_REF", "unknown")
        }

    def add_security_scan_results(self, results: Dict[str, Any]):
        """Add security scan results to the report."""
        self.report_data["security_scan"] = {
            "status": results.get("status", "unknown"),
            "vulnerabilities_found": results.get("vulnerabilities", 0),
            "critical_issues": results.get("critical", 0),
            "high_issues": results.get("high", 0),
            "medium_issues": results.get("medium", 0),
            "low_issues": results.get("low", 0),
            "scan_tools": results.get("tools", ["trivy", "bandit", "safety"])
        }

    def add_code_quality_results(self, results: Dict[str, Any]):
        """Add code quality results to the report."""
        self.report_data["code_quality"] = {
            "status": results.get("status", "unknown"),
            "test_coverage": results.get("coverage", 0),
            "code_complexity": results.get("complexity", "low"),
            "duplication_rate": results.get("duplication", 0),
            "maintainability_index": results.get("maintainability", 0),
            "quality_gate": results.get("quality_gate", "passed")
        }

    def add_test_results(self, results: Dict[str, Any]):
        """Add test results to the report."""
        self.report_data["test_results"] = {
            "unit_tests": {
                "total": results.get("unit_total", 0),
                "passed": results.get("unit_passed", 0),
                "failed": results.get("unit_failed", 0),
                "coverage": results.get("unit_coverage", 0)
            },
            "integration_tests": {
                "total": results.get("integration_total", 0),
                "passed": results.get("integration_passed", 0),
                "failed": results.get("integration_failed", 0)
            },
            "performance_tests": {
                "status": results.get("performance_status", "unknown"),
                "avg_response_time": results.get("avg_response_time", 0),
                "throughput": results.get("throughput", 0),
                "error_rate": results.get("error_rate", 0)
            }
        }

    def add_deployment_info(self, deployment_data: Dict[str, Any]):
        """Add deployment information to the report."""
        self.report_data["deployment"] = {
            "method": deployment_data.get("method", "kubernetes"),
            "cluster": deployment_data.get("cluster", "production"),
            "namespace": deployment_data.get("namespace", "arxos"),
            "replicas": deployment_data.get("replicas", 3),
            "resources": deployment_data.get("resources", {
                "cpu": "1000m",
                "memory": "2Gi"
            }),
            "services": deployment_data.get("services", [
                "api-service",
                "ai-service",
                "realtime-service",
                "auth-service"
            ])
        }

    def add_monitoring_info(self, monitoring_data: Dict[str, Any]):
        """Add monitoring information to the report."""
        self.report_data["monitoring"] = {
            "health_checks": monitoring_data.get("health_checks", "passing"),
            "metrics_collection": monitoring_data.get("metrics", "enabled"),
            "logging": monitoring_data.get("logging", "enabled"),
            "alerting": monitoring_data.get("alerting", "enabled"),
            "dashboard_url": monitoring_data.get("dashboard_url", "")
        }

    def generate_html_report(self) -> str:
        """Generate HTML deployment report."""
        html_template = """<!DOCTYPE html>"
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arxos Deployment Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { margin: 0; font-size: 2.5em; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .content { padding: 30px; }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            background: #f8f9fa;
        }
        .section h2 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #28a745;
        }
        .card.failed { border-left-color: #dc3545; }
        .card.warning { border-left-color: #ffc107; }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }
        .metric:last-child { border-bottom: none; }
        .metric-label { font-weight: 600; color: #495057; }
        .metric-value {
            font-weight: bold;
            color: #2c3e50;
        }
        .status-success { color: #28a745; }
        .status-failed { color: #dc3545; }
        .status-warning { color: #ffc107; }
        .status-unknown { color: #6c757d; }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Arxos Deployment Report</h1>
            <p>Deployment completed successfully at {timestamp}</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>📊 Deployment Summary</h2>
                <div class="grid">
                    <div class="card">
                        <h3>Environment</h3>
                        <div class="metric">
                            <span class="metric-label">Environment:</span>
                            <span class="metric-value">{environment}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Version:</span>
                            <span class="metric-value">{version}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Branch:</span>
                            <span class="metric-value">{branch}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Commit:</span>
                            <span class="metric-value">{commit_sha[:8]}</span>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Security Scan</h3>
                        <div class="metric">
                            <span class="metric-label">Status:</span>
                            <span class="metric-value status-{security_status}">{security_status}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Vulnerabilities:</span>
                            <span class="metric-value">{vulnerabilities}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Critical Issues:</span>
                            <span class="metric-value">{critical_issues}</span>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Code Quality</h3>
                        <div class="metric">
                            <span class="metric-label">Quality Gate:</span>
                            <span class="metric-value status-{quality_status}">{quality_status}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Test Coverage:</span>
                            <span class="metric-value">{coverage}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {coverage}%"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🧪 Test Results</h2>
                <div class="grid">
                    <div class="card">
                        <h3>Unit Tests</h3>
                        <div class="metric">
                            <span class="metric-label">Total:</span>
                            <span class="metric-value">{unit_total}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Passed:</span>
                            <span class="metric-value status-success">{unit_passed}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Failed:</span>
                            <span class="metric-value status-failed">{unit_failed}</span>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Integration Tests</h3>
                        <div class="metric">
                            <span class="metric-label">Total:</span>
                            <span class="metric-value">{integration_total}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Passed:</span>
                            <span class="metric-value status-success">{integration_passed}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Failed:</span>
                            <span class="metric-value status-failed">{integration_failed}</span>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Performance Tests</h3>
                        <div class="metric">
                            <span class="metric-label">Status:</span>
                            <span class="metric-value status-{performance_status}">{performance_status}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Avg Response:</span>
                            <span class="metric-value">{avg_response_time}ms</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Throughput:</span>
                            <span class="metric-value">{throughput} req/s</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>⚙️ Deployment Configuration</h2>
                <div class="grid">
                    <div class="card">
                        <h3>Infrastructure</h3>
                        <div class="metric">
                            <span class="metric-label">Method:</span>
                            <span class="metric-value">{deployment_method}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Cluster:</span>
                            <span class="metric-value">{cluster}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Namespace:</span>
                            <span class="metric-value">{namespace}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Replicas:</span>
                            <span class="metric-value">{replicas}</span>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Services Deployed</h3>
                        {services_html}
                    </div>

                    <div class="card">
                        <h3>Monitoring</h3>
                        <div class="metric">
                            <span class="metric-label">Health Checks:</span>
                            <span class="metric-value status-{health_status}">{health_status}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Metrics:</span>
                            <span class="metric-value">{metrics_status}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Logging:</span>
                            <span class="metric-value">{logging_status}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Generated by Arxos CI/CD Pipeline | {timestamp}</p>
        </div>
    </div>
</body>
</html>
        """

        # Prepare data for template
        template_data = {
            "timestamp": self.report_data["timestamp"],
            "environment": self.report_data["environment"],
            "version": self.report_data["version"],
            "branch": self.report_data["branch"].replace("refs/heads/", ""),
            "commit_sha": self.report_data["commit_sha"],
            "security_status": self.report_data.get("security_scan", {}).get("status", "unknown"),
            "vulnerabilities": self.report_data.get("security_scan", {}).get("vulnerabilities_found", 0),
            "critical_issues": self.report_data.get("security_scan", {}).get("critical_issues", 0),
            "quality_status": self.report_data.get("code_quality", {}).get("quality_gate", "unknown"),
            "coverage": self.report_data.get("code_quality", {}).get("test_coverage", 0),
            "unit_total": self.report_data.get("test_results", {}).get("unit_tests", {}).get("total", 0),
            "unit_passed": self.report_data.get("test_results", {}).get("unit_tests", {}).get("passed", 0),
            "unit_failed": self.report_data.get("test_results", {}).get("unit_tests", {}).get("failed", 0),
            "integration_total": self.report_data.get("test_results", {}).get("integration_tests", {}).get("total", 0),
            "integration_passed": self.report_data.get("test_results", {}).get("integration_tests", {}).get("passed", 0),
            "integration_failed": self.report_data.get("test_results", {}).get("integration_tests", {}).get("failed", 0),
            "performance_status": self.report_data.get("test_results", {}).get("performance_tests", {}).get("status", "unknown"),
            "avg_response_time": self.report_data.get("test_results", {}).get("performance_tests", {}).get("avg_response_time", 0),
            "throughput": self.report_data.get("test_results", {}).get("performance_tests", {}).get("throughput", 0),
            "deployment_method": self.report_data.get("deployment", {}).get("method", "unknown"),
            "cluster": self.report_data.get("deployment", {}).get("cluster", "unknown"),
            "namespace": self.report_data.get("deployment", {}).get("namespace", "unknown"),
            "replicas": self.report_data.get("deployment", {}).get("replicas", 0),
            "health_status": self.report_data.get("monitoring", {}).get("health_checks", "unknown"),
            "metrics_status": self.report_data.get("monitoring", {}).get("metrics_collection", "unknown"),
            "logging_status": self.report_data.get("monitoring", {}).get("logging", "unknown")
        }

        # Generate services HTML
        services = self.report_data.get("deployment", {}).get("services", [])
        services_html = ""
        for service in services:
            services_html += f'<div class="metric"><span class="metric-label">•</span><span class="metric-value">{service}</span></div>'

        template_data["services_html"] = services_html

        return html_template.format(**template_data)

    def generate_report(self) -> bool:
        """Generate the deployment report."""
        try:
            # Create reports directory
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)

            # Generate HTML report
            html_content = self.generate_html_report()
            html_path = reports_dir / "deployment_report.html"

            with open(html_path, "w") as f:
                f.write(html_content)

            # Generate JSON report
            json_path = reports_dir / "deployment_report.json"
            with open(json_path, "w") as f:
                json.dump(self.report_data, f, indent=2)

            print(f"Deployment reports generated:")
            print(f"  - {html_path}")
            print(f"  - {json_path}")

            return True

        except Exception as e:
            print(f"Error generating deployment report: {e}")
            return False


def main():
    """Main function to generate deployment report."""
    generator = DeploymentReportGenerator()

    # Add sample data (in real deployment, this would come from CI/CD pipeline)
    generator.add_security_scan_results({
        "status": "passed",
        "vulnerabilities": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    })

    generator.add_code_quality_results({
        "status": "passed",
        "coverage": 85,
        "complexity": "low",
        "duplication": 2.5,
        "maintainability": 95,
        "quality_gate": "passed"
    })

    generator.add_test_results({
        "unit_total": 150,
        "unit_passed": 148,
        "unit_failed": 2,
        "unit_coverage": 85,
        "integration_total": 25,
        "integration_passed": 25,
        "integration_failed": 0,
        "performance_status": "passed",
        "avg_response_time": 150,
        "throughput": 50,
        "error_rate": 0.01
    })

    generator.add_deployment_info({
        "method": "kubernetes",
        "cluster": "production",
        "namespace": "arxos",
        "replicas": 3,
        "services": ["api-service", "ai-service", "realtime-service", "auth-service"]
    })

    generator.add_monitoring_info({
        "health_checks": "passing",
        "metrics": "enabled",
        "logging": "enabled",
        "alerting": "enabled",
        "dashboard_url": "https://monitoring.arxos.com"
    })

    success = generator.generate_report()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
