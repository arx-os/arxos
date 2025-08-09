
# Example of Proper Python Syntax

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ExampleClass:
    """Example class with proper syntax"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the class"""
        self.config = config or {}
        self.logger = logger

    async def example_function(self, param: str) -> Dict[str, Any]:
        """Example async function with proper syntax"""
        try:
            result = {
                "status": "success",
                "param": param,
                "config": self.config
            }
            return result
        except Exception as e:
            self.logger.error(f"Error in example_function: {e}")
            raise

    def validate_syntax(self, content: str) -> bool:
        """Validate Python syntax"""
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False

# Usage example
if __name__ == "__main__":
    example = ExampleClass({"test": "value"})
    result = await example.example_function("test_param")
    print(result)
