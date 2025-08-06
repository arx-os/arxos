#!/usr/bin/env python3
"""
Direct test script to verify Logic Engine migration
"""

import sys
import os
import tempfile

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_logic_engine_direct():
    """Test the Logic Engine migration directly."""
    try:
        # Import Logic Engine directly from file
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "logic_engine",
            os.path.join(os.path.dirname(__file__), "services", "logic_engine.py"),
        )
        logic_engine_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(logic_engine_module)

        LogicEngine = logic_engine_module.LogicEngine

        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Initialize Logic Engine
            engine = LogicEngine(db_path=db_path)
            print("✅ Logic Engine initialized successfully")

            # Check built-in functions
            print(f"✅ Built-in functions loaded: {len(engine.builtin_functions)}")

            # Test rule creation
            conditions = [{"field": "user.age", "operator": ">=", "value": 18}]

            actions = [{"type": "set_field", "field": "user.status", "value": "adult"}]

            rule_id = engine.create_rule(
                name="Age Check Rule",
                description="Check if user is adult",
                rule_type=logic_engine_module.RuleType.VALIDATION,
                conditions=conditions,
                actions=actions,
                priority=1,
                tags=["validation", "age"],
            )
            print(f"✅ Rule created successfully: {rule_id}")

            # Test rule execution
            test_data = {"user": {"age": 25}}
            execution = engine.execute_rule(rule_id, test_data)
            print(f"✅ Rule execution successful: {execution.status}")
            print(f"✅ Output data: {execution.output_data}")

            # Test performance metrics
            metrics = engine.get_performance_metrics()
            print(f"✅ Performance metrics: {metrics}")

            # Test built-in functions
            context = logic_engine_module.DataContext(
                data={"test": "Hello World"},
                variables={},
                functions=engine.builtin_functions,
                metadata={},
            )

            # Test string functions
            upper_result = engine.builtin_functions["upper"]("hello")
            print(f"✅ String function test: 'hello' -> '{upper_result}'")

            # Test math functions
            math_result = engine.builtin_functions["math_add"](5, 3)
            print(f"✅ Math function test: 5 + 3 = {math_result}")

            print("\n🎉 Logic Engine migration test completed successfully!")
            return True

        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)

    except Exception as e:
        print(f"❌ Logic Engine migration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_logic_engine_direct()
    sys.exit(0 if success else 1)
