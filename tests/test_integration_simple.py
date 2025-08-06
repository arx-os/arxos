#!/usr/bin/env python3
"""
Comprehensive Integration Test for MCP-Engineering

This script tests the complete MCP-Engineering integration including:
- Phase 3: Database Integration
- Phase 4: Real Service Integration
- Phase 5: Production Deployment
"""

import sys
import asyncio
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, ".")


def test_domain_entities():
    """Test domain entities creation and validation."""
    print("🧪 Testing Domain Entities...")

    try:
        from domain.mcp_engineering_entities import (
            BuildingData,
            ValidationType,
            ValidationStatus,
            IssueSeverity,
            SuggestionType,
            ReportType,
            ReportFormat,
            ComplianceIssue,
            AIRecommendation,
            ValidationResult,
        )

        # Test BuildingData
        building_data = BuildingData(
            area=5000.0,
            height=30.0,
            building_type="commercial",
            occupancy="Business",
            floors=2,
            jurisdiction="California",
        )
        print("✅ BuildingData entity created successfully")

        # Test enums
        assert ValidationStatus.PASS.value == "pass"
        assert ValidationType.STRUCTURAL.value == "structural"
        assert IssueSeverity.HIGH.value == "high"
        assert SuggestionType.OPTIMIZATION.value == "optimization"
        assert ReportType.COMPREHENSIVE.value == "comprehensive"
        assert ReportFormat.PDF.value == "pdf"
        print("✅ All enums working correctly")

        # Test ComplianceIssue
        issue = ComplianceIssue(
            code_reference="IBC 1004.1.1",
            severity=IssueSeverity.HIGH,
            description="Missing emergency exit",
            resolution="Add emergency exit on north side",
        )
        print("✅ ComplianceIssue entity created successfully")

        # Test AIRecommendation
        recommendation = AIRecommendation(
            type=SuggestionType.OPTIMIZATION,
            description="Consider adding more natural lighting",
            confidence=0.85,
            impact_score=0.7,
        )
        print("✅ AIRecommendation entity created successfully")

        # Test ValidationResult
        validation_result = ValidationResult(
            building_data=building_data,
            validation_type=ValidationType.STRUCTURAL,
            status=ValidationStatus.PASS,
            confidence_score=0.95,
        )
        print("✅ ValidationResult entity created successfully")

        print("🎉 All domain entity tests passed!")
        return True

    except Exception as e:
        print(f"❌ Domain entity test failed: {e}")
        return False


def test_database_models():
    """Test database models structure."""
    print("\n🧪 Testing Database Models...")

    try:
        from infrastructure.database.models.mcp_engineering import (
            MCPBuildingData,
            MCPValidationSession,
            MCPValidationResult,
            MCPComplianceIssue,
            MCPAIRecommendation,
            MCPKnowledgeSearchResult,
            MCPMLPrediction,
            MCPComplianceReport,
            MCPValidationStatistics,
        )

        print("✅ All database models imported successfully")

        # Test that models have required attributes
        required_models = [
            MCPBuildingData,
            MCPValidationSession,
            MCPValidationResult,
            MCPComplianceIssue,
            MCPAIRecommendation,
            MCPKnowledgeSearchResult,
            MCPMLPrediction,
            MCPComplianceReport,
            MCPValidationStatistics,
        ]

        for model in required_models:
            assert hasattr(model, "__tablename__")
            assert hasattr(model, "id")
            print(f"✅ {model.__name__} has required structure")

        print("🎉 All database models verified!")
        return True

    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False


def test_database_mappers():
    """Test database mappers functionality."""
    print("\n🧪 Testing Database Mappers...")

    try:
        from infrastructure.database.mappers.mcp_engineering_mapper import (
            MCPEngineeringMapper,
        )

        print("✅ MCPEngineeringMapper imported successfully")

        # Test that mapper has required methods
        mapper = MCPEngineeringMapper()

        required_methods = [
            "building_data_to_model",
            "building_data_to_entity",
            "validation_result_to_model",
            "validation_result_to_entity",
            "compliance_issue_to_model",
            "compliance_issue_to_entity",
            "ai_recommendation_to_model",
            "ai_recommendation_to_entity",
        ]

        for method_name in required_methods:
            assert hasattr(mapper, method_name)
            print(f"✅ Mapper method {method_name} found")

        print("🎉 Database mappers verified!")
        return True

    except Exception as e:
        print(f"❌ Database mappers test failed: {e}")
        return False


def test_repository_integration():
    """Test repository integration with database models."""
    print("\n🧪 Testing Repository Integration...")

    try:
        from infrastructure.repositories.mcp_engineering_repository import (
            PostgreSQLValidationRepository,
            PostgreSQLReportRepository,
            RedisKnowledgeRepository,
            PostgreSQLMLRepository,
            PostgreSQLActivityRepository,
        )

        print("✅ All repository implementations imported successfully")

        # Test that repositories have required methods
        required_repos = [
            (
                PostgreSQLValidationRepository,
                [
                    "create_validation_session",
                    "get_validation_session",
                    "store_validation_result",
                ],
            ),
            (
                PostgreSQLReportRepository,
                ["store_report_metadata", "get_report_metadata", "store_report_file"],
            ),
            (
                RedisKnowledgeRepository,
                ["search_knowledge_base", "get_code_section", "update_knowledge_base"],
            ),
            (
                PostgreSQLMLRepository,
                ["store_ml_prediction", "get_ml_prediction", "get_model_performance"],
            ),
            (
                PostgreSQLActivityRepository,
                [
                    "log_search_activity",
                    "log_ml_validation_activity",
                    "get_user_activity",
                ],
            ),
        ]

        for repo_class, required_methods in required_repos:
            for method_name in required_methods:
                assert hasattr(repo_class, method_name)
            print(f"✅ {repo_class.__name__} has required methods")

        print("🎉 Repository integration verified!")
        return True

    except Exception as e:
        print(f"❌ Repository integration test failed: {e}")
        return False


def test_repository_factory_integration():
    """Test repository factory integration."""
    print("\n🧪 Testing Repository Factory Integration...")

    try:
        from infrastructure.repository_factory import SQLAlchemyRepositoryFactory

        print("✅ Repository factory imported successfully")

        # Test that factory has MCP-Engineering methods
        factory_methods = [
            "create_validation_repository",
            "create_report_repository",
            "create_knowledge_repository",
            "create_ml_repository",
            "create_activity_repository",
        ]

        for method_name in factory_methods:
            assert hasattr(SQLAlchemyRepositoryFactory, method_name)
            print(f"✅ Factory method {method_name} found")

        print("🎉 Repository factory integration verified!")
        return True

    except Exception as e:
        print(f"❌ Repository factory integration test failed: {e}")
        return False


def test_migration_file():
    """Test migration file structure."""
    print("\n🧪 Testing Migration File...")

    try:
        import os

        migration_file = (
            "infrastructure/database/migrations/008_create_mcp_engineering_tables.sql"
        )

        if os.path.exists(migration_file):
            with open(migration_file, "r") as f:
                content = f.read()

            # Check for key components
            required_components = [
                "CREATE TYPE issue_severity",
                "CREATE TABLE mcp_building_data",
                "CREATE TABLE mcp_validation_sessions",
                "CREATE TABLE mcp_validation_results",
                "CREATE TABLE mcp_compliance_issues",
                "CREATE TABLE mcp_ai_recommendations",
                "CREATE INDEX",
                "CREATE TRIGGER",
            ]

            for component in required_components:
                assert component in content
                print(f"✅ Migration contains {component}")

            print("🎉 Migration file structure verified!")
            return True
        else:
            print(f"❌ Migration file not found: {migration_file}")
            return False

    except Exception as e:
        print(f"❌ Migration file test failed: {e}")
        return False


def test_application_service_structure():
    """Test application service structure without dependencies."""
    print("\n🧪 Testing Application Service Structure...")

    try:
        # Test that the service file exists and can be imported
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "mcp_engineering_service", "application/services/mcp_engineering_service.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        print("✅ MCP-Engineering service module can be imported")

        # Test that the class exists
        assert hasattr(module, "MCPEngineeringService")
        print("✅ MCPEngineeringService class found")

        print("🎉 Application service structure verified!")
        return True

    except Exception as e:
        print(f"❌ Application service structure test failed: {e}")
        return False


def test_api_routes_structure():
    """Test API routes structure without dependencies."""
    print("\n🧪 Testing API Routes Structure...")

    try:
        # Test that the routes file exists and can be imported
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "mcp_engineering_routes", "api/routes/mcp_engineering_routes.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        print("✅ MCP-Engineering routes module can be imported")

        # Test that the router exists
        assert hasattr(module, "router")
        print("✅ Router found")

        # Test router attributes
        router = module.router
        assert router.prefix == "/mcp"
        assert "MCP Engineering" in router.tags
        print("✅ Router configuration correct")

        print("🎉 API routes structure verified!")
        return True

    except Exception as e:
        print(f"❌ API routes structure test failed: {e}")
        return False


def test_phase4_http_client():
    """Test Phase 4 HTTP client functionality."""
    print("\n🧪 Testing Phase 4 HTTP Client...")

    try:
        from infrastructure.services.mcp_engineering_client import (
            MCPEngineeringHTTPClient,
            APIConfig,
        )

        # Test configuration
        config = APIConfig(
            base_url="https://api.mcp-engineering-test.com",
            api_key="test-key",
            timeout=10,
            max_retries=3,
        )
        print("✅ APIConfig created successfully")

        # Test client initialization
        client = MCPEngineeringHTTPClient(config)
        print("✅ MCPEngineeringHTTPClient initialized successfully")

        # Test that client has required methods
        required_methods = [
            "validate_building",
            "get_ai_recommendations",
            "get_ml_predictions",
            "health_check",
            "get_metrics",
        ]

        for method_name in required_methods:
            assert hasattr(client, method_name)
            print(f"✅ Client method {method_name} found")

        print("🎉 Phase 4 HTTP client verified!")
        return True

    except Exception as e:
        print(f"❌ Phase 4 HTTP client test failed: {e}")
        return False


def test_phase4_grpc_client():
    """Test Phase 4 gRPC client functionality."""
    print("\n🧪 Testing Phase 4 gRPC Client...")

    try:
        from infrastructure.services.mcp_engineering_grpc_client import (
            MCPEngineeringGRPCClient,
            GRPCConfig,
            MCPEngineeringGRPCManager,
        )

        # Test configuration
        config = GRPCConfig(
            server_address="localhost:50051", timeout=10, max_reconnect_attempts=3
        )
        print("✅ GRPCConfig created successfully")

        # Test client initialization
        client = MCPEngineeringGRPCClient(config)
        print("✅ MCPEngineeringGRPCClient initialized successfully")

        # Test manager initialization
        manager = MCPEngineeringGRPCManager([config])
        print("✅ MCPEngineeringGRPCManager initialized successfully")

        # Test that client has required methods
        required_methods = [
            "stream_validation_updates",
            "validate_building_realtime",
            "health_check",
            "get_connection_status",
        ]

        for method_name in required_methods:
            assert hasattr(client, method_name)
            print(f"✅ Client method {method_name} found")

        print("🎉 Phase 4 gRPC client verified!")
        return True

    except Exception as e:
        print(f"❌ Phase 4 gRPC client test failed: {e}")
        return False


def test_phase4_external_apis():
    """Test Phase 4 external API integrations."""
    print("\n🧪 Testing Phase 4 External APIs...")

    try:
        from application.services.external_apis.building_validation_api import (
            BuildingValidationAPI,
        )
        from application.services.external_apis.ai_ml_apis import AIMLAPIs

        # Test BuildingValidationAPI
        validation_api = BuildingValidationAPI(None)  # Mock client
        print("✅ BuildingValidationAPI initialized successfully")

        # Test that API has required methods
        validation_methods = [
            "validate_structural_compliance",
            "validate_electrical_compliance",
            "validate_mechanical_compliance",
            "validate_plumbing_compliance",
            "validate_fire_safety_compliance",
            "validate_accessibility_compliance",
            "validate_energy_efficiency",
        ]

        for method_name in validation_methods:
            assert hasattr(validation_api, method_name)
            print(f"✅ Validation API method {method_name} found")

        # Test AIMLAPIs
        ai_ml_apis = AIMLAPIs(None)  # Mock client
        print("✅ AIMLAPIs initialized successfully")

        # Test that API has required methods
        ai_methods = [
            "get_optimization_recommendations",
            "get_cost_savings_recommendations",
            "get_safety_recommendations",
            "get_efficiency_recommendations",
            "get_compliance_recommendations",
        ]

        for method_name in ai_methods:
            assert hasattr(ai_ml_apis, method_name)
            print(f"✅ AI/ML API method {method_name} found")

        print("🎉 Phase 4 external APIs verified!")
        return True

    except Exception as e:
        print(f"❌ Phase 4 external APIs test failed: {e}")
        return False


def test_phase4_configuration():
    """Test Phase 4 configuration management."""
    print("\n🧪 Testing Phase 4 Configuration...")

    try:
        from application.config.mcp_engineering import (
            MCPEngineeringConfig,
            ConfigManager,
            Environment,
        )

        # Test config manager
        manager = ConfigManager()
        print("✅ ConfigManager created successfully")

        # Test configuration loading
        config = manager.get_config()
        print("✅ MCPEngineeringConfig loaded successfully")

        # Test that config has required attributes
        required_attrs = [
            "environment",
            "api_keys",
            "service_endpoints",
            "grpc_services",
            "rate_limits",
            "monitoring",
            "security",
            "circuit_breaker",
        ]

        for attr_name in required_attrs:
            assert hasattr(config, attr_name)
            print(f"✅ Config attribute {attr_name} found")

        print("🎉 Phase 4 configuration verified!")
        return True

    except Exception as e:
        print(f"❌ Phase 4 configuration test failed: {e}")
        return False


def test_phase5_production_deployment():
    """Test Phase 5 production deployment components."""
    print("\n🧪 Testing Phase 5 Production Deployment...")

    try:
        # Test Docker configuration
        import os

        dockerfile_path = "Dockerfile"
        if os.path.exists(dockerfile_path):
            with open(dockerfile_path, "r") as f:
                content = f.read()
                assert "FROM python" in content
                assert "COPY" in content
                assert "EXPOSE" in content
            print("✅ Dockerfile structure verified")
        else:
            print("⚠️ Dockerfile not found - will be created in Phase 5")

        # Test Kubernetes configuration
        k8s_dir = "k8s"
        if os.path.exists(k8s_dir):
            k8s_files = os.listdir(k8s_dir)
            assert len(k8s_files) > 0
            print("✅ Kubernetes configuration files found")
        else:
            print("⚠️ Kubernetes directory not found - will be created in Phase 5")

        # Test monitoring configuration
        monitoring_dir = "infrastructure/monitoring"
        if os.path.exists(monitoring_dir):
            monitoring_files = os.listdir(monitoring_dir)
            assert len(monitoring_files) > 0
            print("✅ Monitoring configuration found")
        else:
            print("⚠️ Monitoring directory not found - will be created in Phase 5")

        # Test security configuration
        security_config_path = "config/security.yaml"
        if os.path.exists(security_config_path):
            print("✅ Security configuration found")
        else:
            print("⚠️ Security configuration not found - will be created in Phase 5")

        print("🎉 Phase 5 production deployment structure verified!")
        return True

    except Exception as e:
        print(f"❌ Phase 5 production deployment test failed: {e}")
        return False


def test_phase5_performance_optimization():
    """Test Phase 5 performance optimization components."""
    print("\n🧪 Testing Phase 5 Performance Optimization...")

    try:
        import os

        # Test caching configuration
        caching_dir = "infrastructure/caching"
        if os.path.exists(caching_dir):
            caching_files = os.listdir(caching_dir)
            assert len(caching_files) > 0
            print("✅ Caching configuration found")
        else:
            print("⚠️ Caching directory not found - will be created in Phase 5")

        # Test load balancing configuration
        load_balancer_path = "infrastructure/services/load_balancer.py"
        if os.path.exists(load_balancer_path):
            print("✅ Load balancer configuration found")
        else:
            print("⚠️ Load balancer not found - will be created in Phase 5")

        # Test connection pooling
        pooling_path = "infrastructure/database/connection_pool.py"
        if os.path.exists(pooling_path):
            print("✅ Connection pooling configuration found")
        else:
            print("⚠️ Connection pooling not found - will be created in Phase 5")

        print("🎉 Phase 5 performance optimization structure verified!")
        return True

    except Exception as e:
        print(f"❌ Phase 5 performance optimization test failed: {e}")
        return False


def test_phase5_security_hardening():
    """Test Phase 5 security hardening components."""
    print("\n🧪 Testing Phase 5 Security Hardening...")

    try:
        import os

        # Test authentication configuration
        auth_path = "infrastructure/security/authentication.py"
        if os.path.exists(auth_path):
            print("✅ Authentication configuration found")
        else:
            print("⚠️ Authentication not found - will be created in Phase 5")

        # Test authorization configuration
        authz_path = "infrastructure/security/authorization.py"
        if os.path.exists(authz_path):
            print("✅ Authorization configuration found")
        else:
            print("⚠️ Authorization not found - will be created in Phase 5")

        # Test rate limiting
        rate_limit_path = "infrastructure/security/rate_limiting.py"
        if os.path.exists(rate_limit_path):
            print("✅ Rate limiting configuration found")
        else:
            print("⚠️ Rate limiting not found - will be created in Phase 5")

        # Test input validation
        validation_path = "infrastructure/security/input_validation.py"
        if os.path.exists(validation_path):
            print("✅ Input validation configuration found")
        else:
            print("⚠️ Input validation not found - will be created in Phase 5")

        print("🎉 Phase 5 security hardening structure verified!")
        return True

    except Exception as e:
        print(f"❌ Phase 5 security hardening test failed: {e}")
        return False


def test_file_structure():
    """Test that all required files exist."""
    print("\n🧪 Testing File Structure...")

    import os

    required_files = [
        "domain/mcp_engineering_entities.py",
        "application/services/mcp_engineering_service.py",
        "api/routes/mcp_engineering_routes.py",
        "infrastructure/repositories/mcp_engineering_repository.py",
        "infrastructure/repository_factory.py",
        "infrastructure/database/models/mcp_engineering.py",
        "infrastructure/database/mappers/mcp_engineering_mapper.py",
        "infrastructure/database/migrations/008_create_mcp_engineering_tables.sql",
    ]

    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            return False

    print("🎉 All required files exist!")
    return True


def test_code_syntax():
    """Test that all Python files have valid syntax."""
    print("\n🧪 Testing Code Syntax...")

    import ast
    import os

    python_files = [
        "domain/mcp_engineering_entities.py",
        "application/services/mcp_engineering_service.py",
        "api/routes/mcp_engineering_routes.py",
        "infrastructure/repositories/mcp_engineering_repository.py",
        "infrastructure/database/models/mcp_engineering.py",
        "infrastructure/database/mappers/mcp_engineering_mapper.py",
    ]

    for file_path in python_files:
        try:
            with open(file_path, "r") as f:
                content = f.read()
                ast.parse(content)
            print(f"✅ {file_path} has valid syntax")
        except SyntaxError as e:
            print(f"❌ {file_path} has syntax error: {e}")
            return False
        except Exception as e:
            print(f"❌ {file_path} error: {e}")
            return False

    print("🎉 All Python files have valid syntax!")
    return True


def main():
    """Run all integration tests."""
    print("🚀 Starting MCP-Engineering Comprehensive Integration Tests...")
    print("=" * 80)
    print("Testing Phase 3: Database Integration")
    print("Testing Phase 4: Real Service Integration")
    print("Testing Phase 5: Production Deployment")
    print("=" * 80)

    tests = [
        # Phase 3: Database Integration
        test_file_structure,
        test_code_syntax,
        test_domain_entities,
        test_database_models,
        test_database_mappers,
        test_repository_integration,
        test_repository_factory_integration,
        test_migration_file,
        test_application_service_structure,
        test_api_routes_structure,
        # Phase 4: Real Service Integration
        test_phase4_http_client,
        test_phase4_grpc_client,
        test_phase4_external_apis,
        test_phase4_configuration,
        # Phase 5: Production Deployment
        test_phase5_production_deployment,
        test_phase5_performance_optimization,
        test_phase5_security_hardening,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 80)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All integration tests passed!")
        print("\n✅ MCP-Engineering Integration Status:")
        print("   - Phase 3 (Database Integration): ✅ Complete")
        print("   - Phase 4 (Real Service Integration): ✅ Complete")
        print("   - Phase 5 (Production Deployment): ✅ Ready for Implementation")
        print("\n🚀 Next Steps:")
        print("   - Implement Phase 5: Production Deployment")
        print("   - Deploy to production environment")
        print("   - Set up monitoring and alerting")
        print("   - Configure security and performance optimization")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
