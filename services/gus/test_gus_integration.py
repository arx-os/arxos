"""
GUS Integration Test

Simple test to verify GUS agent integration with all components.
"""

import asyncio
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import GUS components
try:
    from core.agent import GUSAgent
    from core.nlp import NLPProcessor
    from core.knowledge import KnowledgeManager
    from core.decision import DecisionEngine
    from core.learning import LearningSystem
except ImportError as e:
    logger.error(f"Failed to import GUS components: {e}")
    raise


def create_gus_config() -> Dict[str, Any]:
    """Create configuration for GUS agent"""
    return {
        "nlp": {
            "model_path": "models/nlp",
            "confidence_threshold": 0.5
        },
        "knowledge": {
            "knowledge_db_path": "test_gus_knowledge.db",
            "vector_db_path": "test_gus_vectors.npz"
        },
        "decision": {
            "retraining_threshold": 0.8,
            "min_training_samples": 50
        },
        "learning": {
            "learning_db_path": "test_gus_learning.db",
            "retraining_threshold": 0.8,
            "min_training_samples": 50
        }
    }


async def test_gus_basic_functionality():
    """Test basic GUS functionality"""
    logger.info("Testing GUS basic functionality...")
    
    try:
        # Initialize GUS agent
        config = create_gus_config()
        gus = GUSAgent(config)
        
        # Test basic query processing
        test_queries = [
            "Hello, how can you help me?",
            "I want to create a new drawing",
            "How do I export my drawing to SVG?",
            "What is BILT token?",
            "Help me with building codes"
        ]
        
        for i, query in enumerate(test_queries):
            logger.info(f"Testing query {i+1}: {query}")
            
            response = await gus.process_query(query, f"test_user_{i}")
            
            logger.info(f"Response: {response.message}")
            logger.info(f"Confidence: {response.confidence}")
            logger.info(f"Intent: {response.intent}")
            logger.info(f"Actions: {response.actions}")
            logger.info("---")
        
        # Test knowledge query
        logger.info("Testing knowledge query...")
        knowledge_response = await gus.get_knowledge("building codes")
        logger.info(f"Knowledge response: {knowledge_response.message}")
        
        # Test task execution
        logger.info("Testing task execution...")
        task_response = await gus.execute_task(
            "create_drawing", 
            {"system_type": "mechanical", "precision": "high"}, 
            "test_user"
        )
        logger.info(f"Task response: {task_response.message}")
        
        # Shutdown
        await gus.shutdown()
        
        logger.info("✅ GUS basic functionality test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ GUS basic functionality test failed: {e}")
        return False


async def test_gus_components():
    """Test individual GUS components"""
    logger.info("Testing GUS components...")
    
    try:
        config = create_gus_config()
        
        # Test NLP processor
        logger.info("Testing NLP processor...")
        nlp = NLPProcessor(config["nlp"])
        nlp_result = await nlp.process("Create a new drawing", {})
        logger.info(f"NLP result - Intent: {nlp_result.intent.value}, Confidence: {nlp_result.confidence}")
        
        # Test Knowledge manager
        logger.info("Testing Knowledge manager...")
        knowledge = KnowledgeManager(config["knowledge"])
        knowledge_result = await knowledge.query("building codes", [], {})
        logger.info(f"Knowledge result - Items: {len(knowledge_result.items)}")
        
        # Test Decision engine
        logger.info("Testing Decision engine...")
        decision = DecisionEngine(config["decision"])
        decision_result = await decision.decide(nlp_result, knowledge_result, {})
        logger.info(f"Decision result - Type: {decision_result.decision_type.value}, Confidence: {decision_result.confidence}")
        
        # Test Learning system
        logger.info("Testing Learning system...")
        learning = LearningSystem(config["learning"])
        success = await learning.record_learning_event(
            "Create a new drawing",
            "create_drawing",
            confidence=0.8,
            success=True
        )
        logger.info(f"Learning event recorded: {success}")
        
        # Shutdown components
        await nlp.shutdown()
        await knowledge.shutdown()
        await decision.shutdown()
        await learning.shutdown()
        
        logger.info("✅ GUS components test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ GUS components test failed: {e}")
        return False


async def test_gus_error_handling():
    """Test GUS error handling"""
    logger.info("Testing GUS error handling...")
    
    try:
        config = create_gus_config()
        gus = GUSAgent(config)
        
        # Test with empty query
        response = await gus.process_query("", "test_user")
        logger.info(f"Empty query response: {response.message}")
        
        # Test with very long query
        long_query = "This is a very long query " * 100
        response = await gus.process_query(long_query, "test_user")
        logger.info(f"Long query response: {response.message}")
        
        # Test with special characters
        special_query = "Create drawing with @#$%^&*() symbols"
        response = await gus.process_query(special_query, "test_user")
        logger.info(f"Special chars response: {response.message}")
        
        await gus.shutdown()
        
        logger.info("✅ GUS error handling test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ GUS error handling test failed: {e}")
        return False


async def main():
    """Run all GUS tests"""
    logger.info("🚀 Starting GUS integration tests...")
    
    tests = [
        test_gus_basic_functionality,
        test_gus_components,
        test_gus_error_handling
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    logger.info(f"\n📊 Test Results:")
    logger.info(f"Passed: {passed}/{total}")
    logger.info(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 All GUS tests passed!")
    else:
        logger.error("❌ Some GUS tests failed!")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main()) 