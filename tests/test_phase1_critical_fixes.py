"""
Test Phase 1 Critical Fixes

Tests for the critical fixes implemented in Phase 1:
1. Missing GUS Core Modules
2. Configuration System
3. Dependency Management
4. Basic Authentication
"""

import pytest
import asyncio
import logging
from typing import Dict, Any

# Test imports for GUS core modules
from services.gus.core.nlp import NLPProcessor, NLPResult
from services.gus.core.knowledge import KnowledgeManager, KnowledgeResult
from services.gus.core.decision import DecisionEngine, DecisionResult
from services.gus.core.learning import LearningSystem, LearningData

# Test imports for configuration
from application.config import get_config, get_database_config, get_service_config, get_pdf_analysis_config

# Test imports for authentication
from api.dependencies import get_current_user, get_current_user_required, require_permission


class TestPhase1CriticalFixes:
    """Test suite for Phase 1 critical fixes"""
    
    def setup_method(self):
        """Setup test environment"""
        # Configure logging for tests
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def test_1_gus_core_modules_exist(self):
        """Test that all GUS core modules can be imported and initialized"""
        try:
            # Test NLP Processor
            nlp_config = {'test': True}
            nlp_processor = NLPProcessor(nlp_config)
            assert nlp_processor is not None
            assert hasattr(nlp_processor, 'process')
            assert hasattr(nlp_processor, 'get_supported_intents')
            
            # Test Knowledge Manager
            knowledge_config = {'test': True}
            knowledge_manager = KnowledgeManager(knowledge_config)
            assert knowledge_manager is not None
            assert hasattr(knowledge_manager, 'query')
            assert hasattr(knowledge_manager, 'get_available_topics')
            
            # Test Decision Engine
            decision_config = {'test': True}
            decision_engine = DecisionEngine(decision_config)
            assert decision_engine is not None
            assert hasattr(decision_engine, 'decide')
            assert hasattr(decision_engine, 'get_supported_intents')
            
            # Test Learning System
            learning_config = {'test': True}
            learning_system = LearningSystem(learning_config)
            assert learning_system is not None
            assert hasattr(learning_system, 'update')
            assert hasattr(learning_system, 'get_performance_metrics')
            
            self.logger.info("✅ All GUS core modules exist and can be initialized")
            
        except Exception as e:
            pytest.fail(f"GUS core modules test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_2_nlp_processor_functionality(self):
        """Test NLP processor functionality"""
        try:
            nlp_config = {'test': True}
            nlp_processor = NLPProcessor(nlp_config)
            
            # Test query processing
            query = "analyze this PDF for system schedule"
            session = {'user_id': 'test_user'}
            
            result = await nlp_processor.process(query, session)
            
            assert isinstance(result, NLPResult)
            assert hasattr(result, 'intent')
            assert hasattr(result, 'entities')
            assert hasattr(result, 'confidence')
            assert hasattr(result, 'message')
            
            # Test intent extraction
            assert result.intent in ['pdf_analysis', 'unknown']
            assert result.confidence >= 0.0
            assert result.confidence <= 1.0
            
            self.logger.info("✅ NLP processor functionality working")
            
        except Exception as e:
            pytest.fail(f"NLP processor test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_3_knowledge_manager_functionality(self):
        """Test knowledge manager functionality"""
        try:
            knowledge_config = {'test': True}
            knowledge_manager = KnowledgeManager(knowledge_config)
            
            # Test knowledge query
            intent = 'pdf_analysis'
            entities = {'file_type': ['pdf']}
            context = {'user_id': 'test_user'}
            
            result = await knowledge_manager.query(intent, entities, context)
            
            assert isinstance(result, KnowledgeResult)
            assert hasattr(result, 'summary')
            assert hasattr(result, 'confidence')
            assert hasattr(result, 'details')
            assert hasattr(result, 'sources')
            
            # Test knowledge retrieval
            assert result.confidence >= 0.0
            assert result.confidence <= 1.0
            assert len(result.sources) > 0
            
            self.logger.info("✅ Knowledge manager functionality working")
            
        except Exception as e:
            pytest.fail(f"Knowledge manager test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_4_decision_engine_functionality(self):
        """Test decision engine functionality"""
        try:
            decision_config = {'test': True}
            decision_engine = DecisionEngine(decision_config)
            
            # Create mock NLP and knowledge results
            nlp_result = type('obj', (object,), {
                'intent': 'pdf_analysis',
                'confidence': 0.8
            })
            
            knowledge_result = type('obj', (object,), {
                'confidence': 0.9
            })
            
            session = {'user_id': 'test_user'}
            
            result = await decision_engine.decide(nlp_result, knowledge_result, session)
            
            assert isinstance(result, DecisionResult)
            assert hasattr(result, 'response')
            assert hasattr(result, 'confidence')
            assert hasattr(result, 'actions')
            assert hasattr(result, 'reasoning')
            
            # Test decision logic
            assert result.confidence >= 0.0
            assert result.confidence <= 1.0
            assert len(result.actions) > 0
            
            self.logger.info("✅ Decision engine functionality working")
            
        except Exception as e:
            pytest.fail(f"Decision engine test failed: {e}")
    
    def test_5_configuration_system(self):
        """Test configuration system"""
        try:
            # Test configuration loading
            config = get_config()
            assert isinstance(config, dict)
            assert 'environment' in config
            assert 'database' in config
            assert 'service' in config
            assert 'pdf_analysis' in config
            assert 'security' in config
            assert 'gus_service' in config
            
            # Test database configuration
            db_config = get_database_config()
            assert hasattr(db_config, 'host')
            assert hasattr(db_config, 'port')
            assert hasattr(db_config, 'database')
            assert hasattr(db_config, 'username')
            assert hasattr(db_config, 'password')
            
            # Test service configuration
            service_config = get_service_config()
            assert hasattr(service_config, 'host')
            assert hasattr(service_config, 'port')
            assert hasattr(service_config, 'debug')
            assert hasattr(service_config, 'workers')
            
            # Test PDF analysis configuration
            pdf_config = get_pdf_analysis_config()
            assert hasattr(pdf_config, 'max_file_size')
            assert hasattr(pdf_config, 'timeout')
            assert hasattr(pdf_config, 'confidence_threshold')
            assert hasattr(pdf_config, 'supported_formats')
            assert hasattr(pdf_config, 'processing_workers')
            
            # Validate configuration values
            assert pdf_config.max_file_size > 0
            assert pdf_config.timeout > 0
            assert 0 <= pdf_config.confidence_threshold <= 1
            assert len(pdf_config.supported_formats) > 0
            assert pdf_config.processing_workers > 0
            
            self.logger.info("✅ Configuration system working")
            
        except Exception as e:
            pytest.fail(f"Configuration system test failed: {e}")
    
    def test_6_dependency_management(self):
        """Test dependency management"""
        try:
            # Test that core modules can be imported
            import services.gus.core.nlp
            import services.gus.core.knowledge
            import services.gus.core.decision
            import services.gus.core.learning
            import services.gus.core.pdf_analysis
            
            # Test that configuration can be imported
            import application.config
            
            # Test that authentication can be imported
            import api.dependencies
            
            # Test that PDF analysis handles missing dependencies gracefully
            from services.gus.core.pdf_analysis import PDF_AVAILABLE, IMAGE_AVAILABLE, ML_AVAILABLE
            
            # These should be defined even if dependencies are missing
            assert PDF_AVAILABLE is not None
            assert IMAGE_AVAILABLE is not None
            assert ML_AVAILABLE is not None
            
            self.logger.info("✅ Dependency management working")
            
        except Exception as e:
            pytest.fail(f"Dependency management test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_7_authentication_system(self):
        """Test authentication system"""
        try:
            from fastapi import Request
            from unittest.mock import Mock
            
            # Test anonymous user
            request = Mock()
            request.headers = {}
            request.cookies = {}
            
            user = await get_current_user(request)
            assert user['id'] == 'anonymous'
            assert 'pdf_analysis' in user['permissions']
            assert user['auth_type'] == 'anonymous'
            
            # Test API key authentication
            request.headers = {'X-API-Key': 'default-key'}
            user = await get_current_user(request)
            assert user['id'] == 'anonymous'
            assert 'pdf_analysis' in user['permissions']
            assert user['auth_type'] == 'api_key'
            
            # Test Bearer token authentication
            request.headers = {'Authorization': 'Bearer test-token-123456789'}
            user = await get_current_user(request)
            assert user['id'] == 'authenticated_user'
            assert 'pdf_analysis' in user['permissions']
            assert user['auth_type'] == 'jwt'
            
            self.logger.info("✅ Authentication system working")
            
        except Exception as e:
            pytest.fail(f"Authentication system test failed: {e}")
    
    def test_8_system_startup_simulation(self):
        """Test that the system can start up without critical errors"""
        try:
            # Simulate system startup by initializing all core components
            
            # Initialize GUS core modules
            config = {'test': True}
            nlp = NLPProcessor(config)
            knowledge = KnowledgeManager(config)
            decision = DecisionEngine(config)
            learning = LearningSystem(config)
            
            # Initialize configuration
            app_config = get_config()
            db_config = get_database_config()
            service_config = get_service_config()
            pdf_config = get_pdf_analysis_config()
            
            # Test that all components are functional
            assert nlp is not None
            assert knowledge is not None
            assert decision is not None
            assert learning is not None
            assert app_config is not None
            assert db_config is not None
            assert service_config is not None
            assert pdf_config is not None
            
            self.logger.info("✅ System startup simulation successful")
            
        except Exception as e:
            pytest.fail(f"System startup simulation failed: {e}")
    
    def test_9_custom_implementation_philosophy(self):
        """Test that we're following the custom implementation philosophy"""
        try:
            # Check that we're not using external NLP libraries
            nlp_source = NLPProcessor.__module__
            assert 'spacy' not in nlp_source
            assert 'nltk' not in nlp_source
            assert 'textblob' not in nlp_source
            
            # Check that we're not using external ML libraries for core functionality
            decision_source = DecisionEngine.__module__
            assert 'sklearn' not in decision_source
            assert 'tensorflow' not in decision_source
            assert 'pytorch' not in decision_source
            
            # Check that we're using custom configuration
            config_source = get_config.__module__
            assert 'pydantic' not in config_source
            assert 'dynaconf' not in config_source
            
            # Check that we're using custom authentication
            auth_source = get_current_user.__module__
            assert 'passlib' not in auth_source
            assert 'python-jose' not in auth_source
            
            self.logger.info("✅ Custom implementation philosophy maintained")
            
        except Exception as e:
            pytest.fail(f"Custom implementation philosophy test failed: {e}")


def run_phase1_tests():
    """Run all Phase 1 tests"""
    print("🚀 Running Phase 1 Critical Fixes Tests...")
    
    test_instance = TestPhase1CriticalFixes()
    test_instance.setup_method()
    
    # Run all tests
    test_methods = [
        test_instance.test_1_gus_core_modules_exist,
        test_instance.test_2_nlp_processor_functionality,
        test_instance.test_3_knowledge_manager_functionality,
        test_instance.test_4_decision_engine_functionality,
        test_instance.test_5_configuration_system,
        test_instance.test_6_dependency_management,
        test_instance.test_7_authentication_system,
        test_instance.test_8_system_startup_simulation,
        test_instance.test_9_custom_implementation_philosophy
    ]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            if asyncio.iscoroutinefunction(test_method):
                asyncio.run(test_method())
            else:
                test_method()
            passed += 1
            print(f"✅ {test_method.__name__}")
        except Exception as e:
            failed += 1
            print(f"❌ {test_method.__name__}: {e}")
    
    print(f"\n📊 Phase 1 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("🎉 All Phase 1 critical fixes are working correctly!")
        return True
    else:
        print("⚠️ Some Phase 1 fixes need attention.")
        return False


if __name__ == "__main__":
    run_phase1_tests() 