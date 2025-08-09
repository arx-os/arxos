
# Example of Proper Docstring Patterns

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ExampleClass:
    """
    Example class with proper docstring patterns.

    Attributes:
        config: Configuration dictionary

    Methods:
        process_data: Process input data
        validate_input: Validate input parameters
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the class.

        Args:
            config: Configuration dictionary

        Returns:
            None
        """
        self.config = config or {}
        self.logger = logger

    async def process_data(self, data: str) -> Dict[str, Any]:
        """
        Process input data asynchronously.

        Args:
            data: Input data to process

        Returns:
            Processed data dictionary

        Raises:
            ValueError: If data is invalid
        """
        try:
            result = {
                "status": "success",
                "data": data,
                "config": self.config
            }
            return result
        except Exception as e:
            self.logger.error(f"Error processing data: {e}")
            raise ValueError(f"Invalid data: {e}")

    def validate_input(self, input_data: str) -> bool:
        """
        Validate input parameters.

        Args:
            input_data: Input data to validate

        Returns:
            True if valid, False otherwise
        """
        return bool(input_data and input_data.strip()
# Usage example
if __name__ == "__main__":
    example = ExampleClass({"test": "value"})
    result = await example.process_data("test_data")
    print(result)
