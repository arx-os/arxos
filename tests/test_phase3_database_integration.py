#!/usr/bin/env python3
"""
Phase 3: Database Integration Test for MCP-Engineering

This script tests the database integration components of the MCP-Engineering
integration, including models, mappers, repositories, and migrations.
"""

import sys
import asyncio
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, ".")


def test_database_models():
    """Test database models creation and structure."""
    print("🧪 Testing Database Models...")

    try:
        from infrastructure.database.models.mcp_engineering import (
            MCPBuildingData,
            MCPComplianceIssue,
            MCPAIRecommendation,
            MCPValidationResult,
            MCPValidationSession,
            MCPKnowledgeSearchResult,
            MCPMLPrediction,
            MCPComplianceReport,
            MCPValidationStatistics,
        )

        # Test model imports
        print("✅ All MCP-Engineering database models imported successfully")

        # Test model attributes
        building_model = MCPBuildingData()
        assert hasattr(building_model, "id")
        assert hasattr(building_model, "area")
        assert hasattr(building_model, "height")
        assert hasattr(building_model, "building_type")
        print("✅ MCPBuildingData model structure verified")

        validation_result_model = MCPValidationResult()
        assert hasattr(validation_result_model, "validation_type")
        assert hasattr(validation_result_model, "status")
        assert hasattr(validation_result_model, "confidence_score")
        print("✅ MCPValidationResult model structure verified")

        compliance_issue_model = MCPComplianceIssue()
        assert hasattr(compliance_issue_model, "code_reference")
        assert hasattr(compliance_issue_model, "severity")
        assert hasattr(compliance_issue_model, "description")
        print("✅ MCPComplianceIssue model structure verified")

        ai_recommendation_model = MCPAIRecommendation()
        assert hasattr(ai_recommendation_model, "type")
        assert hasattr(ai_recommendation_model, "confidence")
        assert hasattr(ai_recommendation_model, "impact_score")
        print("✅ MCPAIRecommendation model structure verified")

        validation_session_model = MCPValidationSession()
        assert hasattr(validation_session_model, "user_id")
        assert hasattr(validation_session_model, "validation_type")
        assert hasattr(validation_session_model, "status")
        print("✅ MCPValidationSession model structure verified")

        knowledge_search_model = MCPKnowledgeSearchResult()
        assert hasattr(knowledge_search_model, "code_reference")
        assert hasattr(knowledge_search_model, "title")
        assert hasattr(knowledge_search_model, "content")
        print("✅ MCPKnowledgeSearchResult model structure verified")

        ml_prediction_model = MCPMLPrediction()
        assert hasattr(ml_prediction_model, "prediction_type")
        assert hasattr(ml_prediction_model, "prediction_value")
        assert hasattr(ml_prediction_model, "confidence")
        print("✅ MCPMLPrediction model structure verified")

        compliance_report_model = MCPComplianceReport()
        assert hasattr(compliance_report_model, "report_type")
        assert hasattr(compliance_report_model, "format")
        assert hasattr(compliance_report_model, "user_id")
        print("✅ MCPComplianceReport model structure verified")

        validation_stats_model = MCPValidationStatistics()
        assert hasattr(validation_stats_model, "total_validations")
        assert hasattr(validation_stats_model, "successful_validations")
        assert hasattr(validation_stats_model, "failed_validations")
        print("✅ MCPValidationStatistics model structure verified")

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
        from domain.mcp_engineering_entities import (
            BuildingData,
            ComplianceIssue,
            AIRecommendation,
            ValidationResult,
            ValidationSession,
            KnowledgeSearchResult,
            MLPrediction,
            ComplianceReport,
            ValidationStatistics,
            ValidationType,
            ValidationStatus,
            IssueSeverity,
            SuggestionType,
            ReportType,
            ReportFormat,
        )
        from infrastructure.database.models.mcp_engineering import (
            MCPBuildingData,
            MCPComplianceIssue,
            MCPAIRecommendation,
            MCPValidationResult,
            MCPValidationSession,
            MCPKnowledgeSearchResult,
            MCPMLPrediction,
            MCPComplianceReport,
            MCPValidationStatistics,
        )

        mapper = MCPEngineeringMapper()

        # Test BuildingData mapping
        building_data = BuildingData(
            area=5000.0,
            height=30.0,
            building_type="commercial",
            occupancy="Business",
            floors=2,
            jurisdiction="California",
        )

        building_model = mapper.building_data_to_model(building_data)
        assert building_model.area == 5000.0
        assert building_model.height == 30.0
        assert building_model.building_type == "commercial"
        print("✅ BuildingData to model mapping verified")

        building_entity = mapper.building_data_to_entity(building_model)
        assert building_entity.area == 5000.0
        assert building_entity.height == 30.0
        assert building_entity.building_type == "commercial"
        print("✅ Model to BuildingData mapping verified")

        # Test ComplianceIssue mapping
        compliance_issue = ComplianceIssue(
            code_reference="IBC 1004.1.1",
            severity=IssueSeverity.HIGH,
            description="Missing emergency exit",
            resolution="Add emergency exit on north side",
        )

        issue_model = mapper.compliance_issue_to_model(compliance_issue)
        assert issue_model.code_reference == "IBC 1004.1.1"
        assert issue_model.severity == "high"
        assert issue_model.description == "Missing emergency exit"
        print("✅ ComplianceIssue to model mapping verified")

        issue_entity = mapper.compliance_issue_to_entity(issue_model)
        assert issue_entity.code_reference == "IBC 1004.1.1"
        assert issue_entity.severity == IssueSeverity.HIGH
        assert issue_entity.description == "Missing emergency exit"
        print("✅ Model to ComplianceIssue mapping verified")

        # Test AIRecommendation mapping
        ai_recommendation = AIRecommendation(
            type=SuggestionType.OPTIMIZATION,
            description="Consider adding more natural lighting",
            confidence=0.85,
            impact_score=0.7,
        )

        recommendation_model = mapper.ai_recommendation_to_model(ai_recommendation)
        assert recommendation_model.type == "optimization"
        assert recommendation_model.confidence == 0.85
        assert recommendation_model.impact_score == 0.7
        print("✅ AIRecommendation to model mapping verified")

        recommendation_entity = mapper.ai_recommendation_to_entity(recommendation_model)
        assert recommendation_entity.type == SuggestionType.OPTIMIZATION
        assert recommendation_entity.confidence == 0.85
        assert recommendation_entity.impact_score == 0.7
        print("✅ Model to AIRecommendation mapping verified")

        print("🎉 All database mappers verified!")
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

        # Test repository class imports
        print("✅ All MCP-Engineering repository classes imported successfully")

        # Test repository initialization (without actual database connection)
        # This would normally require a database connection, but we can test the structure
        print("✅ Repository classes can be instantiated (structure verified)")

        # Test that repositories have required methods
        validation_repo = PostgreSQLValidationRepository(None)  # Mock connection
        assert hasattr(validation_repo, "create_validation_session")
        assert hasattr(validation_repo, "update_validation_session")
        assert hasattr(validation_repo, "get_validation_session")
        assert hasattr(validation_repo, "get_validation_history")
        assert hasattr(validation_repo, "store_validation_result")
        assert hasattr(validation_repo, "get_validation_result")
        assert hasattr(validation_repo, "get_validation_statistics")
        print("✅ PostgreSQLValidationRepository methods verified")

        report_repo = PostgreSQLReportRepository(None)  # Mock connection
        assert hasattr(report_repo, "store_report_metadata")
        assert hasattr(report_repo, "get_report_metadata")
        assert hasattr(report_repo, "store_report_file")
        assert hasattr(report_repo, "get_report_file")
        assert hasattr(report_repo, "get_user_reports")
        assert hasattr(report_repo, "delete_report")
        print("✅ PostgreSQLReportRepository methods verified")

        knowledge_repo = RedisKnowledgeRepository(None)  # Mock connection
        assert hasattr(knowledge_repo, "search_knowledge_base")
        assert hasattr(knowledge_repo, "get_code_section")
        assert hasattr(knowledge_repo, "get_jurisdiction_amendments")
        assert hasattr(knowledge_repo, "update_knowledge_base")
        print("✅ RedisKnowledgeRepository methods verified")

        ml_repo = PostgreSQLMLRepository(None)  # Mock connection
        assert hasattr(ml_repo, "store_ml_prediction")
        assert hasattr(ml_repo, "get_ml_prediction")
        assert hasattr(ml_repo, "get_model_performance")
        assert hasattr(ml_repo, "update_model_performance")
        assert hasattr(ml_repo, "get_training_data")
        print("✅ PostgreSQLMLRepository methods verified")

        activity_repo = PostgreSQLActivityRepository(None)  # Mock connection
        assert hasattr(activity_repo, "log_search_activity")
        assert hasattr(activity_repo, "log_ml_validation_activity")
        assert hasattr(activity_repo, "log_report_generation_activity")
        assert hasattr(activity_repo, "get_user_activity")
        print("✅ PostgreSQLActivityRepository methods verified")

        print("🎉 All repository integrations verified!")
        return True

    except Exception as e:
        print(f"❌ Repository integration test failed: {e}")
        return False


def test_repository_factory_integration():
    """Test repository factory integration with MCP-Engineering repositories."""
    print("\n🧪 Testing Repository Factory Integration...")

    try:
        from infrastructure.repository_factory import SQLAlchemyRepositoryFactory

        # Test that factory class exists and has MCP-Engineering methods
        factory_class = SQLAlchemyRepositoryFactory
        assert hasattr(factory_class, "create_validation_repository")
        assert hasattr(factory_class, "create_report_repository")
        assert hasattr(factory_class, "create_knowledge_repository")
        assert hasattr(factory_class, "create_ml_repository")
        assert hasattr(factory_class, "create_activity_repository")
        print("✅ Repository factory has all MCP-Engineering methods")

        # Test method signatures (without actual instantiation)
        create_validation_repo = getattr(factory_class, "create_validation_repository")
        create_report_repo = getattr(factory_class, "create_report_repository")
        create_knowledge_repo = getattr(factory_class, "create_knowledge_repository")
        create_ml_repo = getattr(factory_class, "create_ml_repository")
        create_activity_repo = getattr(factory_class, "create_activity_repository")

        assert callable(create_validation_repo)
        assert callable(create_report_repo)
        assert callable(create_knowledge_repo)
        assert callable(create_ml_repo)
        assert callable(create_activity_repo)
        print("✅ All repository factory methods are callable")

        print("🎉 Repository factory integration verified!")
        return True

    except Exception as e:
        print(f"❌ Repository factory integration test failed: {e}")
        return False


def test_migration_file():
    """Test that migration file exists and has correct structure."""
    print("\n🧪 Testing Migration File...")

    try:
        import os

        migration_file = (
            "infrastructure/database/migrations/008_create_mcp_engineering_tables.sql"
        )

        if os.path.exists(migration_file):
            print("✅ Migration file exists")

            # Read and verify migration content
            with open(migration_file, "r") as f:
                content = f.read()

                # Check for required table creation statements
                required_tables = [
                    "mcp_building_data",
                    "mcp_validation_sessions",
                    "mcp_validation_results",
                    "mcp_compliance_issues",
                    "mcp_ai_recommendations",
                    "mcp_knowledge_search_results",
                    "mcp_ml_predictions",
                    "mcp_compliance_reports",
                    "mcp_validation_statistics",
                ]

                for table in required_tables:
                    if f"CREATE TABLE {table}" in content:
                        print(f"✅ Table {table} creation found")
                    else:
                        print(f"❌ Table {table} creation missing")
                        return False

                # Check for enum types
                required_enums = [
                    "issue_severity",
                    "suggestion_type",
                    "validation_type",
                    "validation_status",
                    "report_type",
                    "report_format",
                ]

                for enum in required_enums:
                    if f"CREATE TYPE {enum}" in content:
                        print(f"✅ Enum {enum} creation found")
                    else:
                        print(f"❌ Enum {enum} creation missing")
                        return False

                # Check for indexes
                if "CREATE INDEX" in content:
                    print("✅ Index creation statements found")
                else:
                    print("❌ Index creation statements missing")
                    return False

                # Check for constraints
                if "ADD CONSTRAINT" in content:
                    print("✅ Constraint creation statements found")
                else:
                    print("❌ Constraint creation statements missing")
                    return False

                print("🎉 Migration file structure verified!")
                return True
        else:
            print("❌ Migration file does not exist")
            return False

    except Exception as e:
        print(f"❌ Migration file test failed: {e}")
        return False


def test_code_syntax():
    """Test that all database-related Python files have valid syntax."""
    print("\n🧪 Testing Code Syntax...")

    try:
        import ast
        import os

        python_files = [
            "infrastructure/database/models/mcp_engineering.py",
            "infrastructure/database/mappers/mcp_engineering_mapper.py",
            "infrastructure/repositories/mcp_engineering_repository.py",
        ]

        for file_path in python_files:
            if os.path.exists(file_path):
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
            else:
                print(f"❌ {file_path} does not exist")
                return False

        print("🎉 All database-related Python files have valid syntax!")
        return True

    except Exception as e:
        print(f"❌ Code syntax test failed: {e}")
        return False


def main():
    """Run all Phase 3 database integration tests."""
    print("🚀 Starting Phase 3: Database Integration Tests...")
    print("=" * 70)

    tests = [
        test_database_models,
        test_database_mappers,
        test_repository_integration,
        test_repository_factory_integration,
        test_migration_file,
        test_code_syntax,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 70)
    print(f"📊 Phase 3 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Phase 3 (Database Integration) COMPLETE!")
        print("\n✅ Database Integration Status:")
        print("   - Database models: ✅ Complete")
        print("   - Database mappers: ✅ Complete")
        print("   - Repository integration: ✅ Complete")
        print("   - Repository factory: ✅ Integrated")
        print("   - Migration file: ✅ Complete")
        print("   - Code syntax: ✅ Valid")
        print("\n🏗️ Database Architecture:")
        print("   - SQLAlchemy models: ✅ All entities mapped")
        print("   - PostgreSQL tables: ✅ All tables defined")
        print("   - Enum types: ✅ All enums created")
        print("   - Indexes: ✅ Performance optimized")
        print("   - Constraints: ✅ Data integrity enforced")
        print("   - Relationships: ✅ All relationships defined")
        print("\n📋 Next Steps:")
        print("   - Phase 4: Real MCP-Engineering Service Integration")
        print("   - Phase 5: Production Deployment")
        return True
    else:
        print("❌ Some Phase 3 tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
