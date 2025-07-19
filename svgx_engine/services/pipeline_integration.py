#!/usr/bin/env python3
"""
Arxos Pipeline Integration Service

This service acts as a bridge between the Go orchestration layer and the SVGX engine
for pipeline operations. It handles SVGX-specific operations like symbol validation,
behavior profile implementation, and compliance checking.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Add the svgx_engine to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from svgx_engine.services.symbol_manager import SymbolManager
from svgx_engine.services.behavior_engine import BehaviorEngine
from svgx_engine.services.validation_engine import ValidationEngine
from svgx_engine.utils.errors import PipelineError, ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineIntegrationService:
    """Service for integrating with the Go pipeline orchestration layer."""
    
    def __init__(self):
        self.symbol_manager = SymbolManager()
        self.behavior_engine = BehaviorEngine()
        self.validation_engine = ValidationEngine()
        
    def handle_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a pipeline operation and return the result."""
        try:
            logger.info(f"Handling operation: {operation} with params: {params}")
            
            if operation == "validate-schema":
                return self.validate_schema(params)
            elif operation == "validate-symbol":
                return self.validate_symbol(params)
            elif operation == "validate-behavior":
                return self.validate_behavior(params)
            elif operation == "add-symbols":
                return self.add_symbols(params)
            elif operation == "implement-behavior":
                return self.implement_behavior(params)
            elif operation == "compliance":
                return self.run_compliance_check(params)
            else:
                raise PipelineError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"Error in operation {operation}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
                "timestamp": time.time()
            }
    
    def validate_schema(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a system schema."""
        system = params.get("system")
        if not system:
            raise PipelineError("System parameter is required")
        
        # Check if schema file exists
        schema_file = Path(f"schemas/{system}/schema.json")
        if not schema_file.exists():
            return {
                "success": False,
                "error": f"Schema file not found: {schema_file}",
                "suggestion": "Run define-schema step first"
            }
        
        # Validate schema structure
        try:
            with open(schema_file, 'r') as f:
                schema = json.load(f)
            
            # Basic schema validation
            required_fields = ["system", "objects"]
            for field in required_fields:
                if field not in schema:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            return {
                "success": True,
                "message": f"Schema validation passed for system: {system}",
                "object_count": len(schema.get("objects", {})),
                "timestamp": time.time()
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in schema file: {str(e)}"
            }
    
    def validate_symbol(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a symbol."""
        symbol = params.get("symbol")
        if not symbol:
            raise PipelineError("Symbol parameter is required")
        
        try:
            # Validate symbol using symbol manager
            validation_result = self.symbol_manager.validate_symbol(symbol)
            
            return {
                "success": True,
                "message": f"Symbol validation passed: {symbol}",
                "validation_details": validation_result,
                "timestamp": time.time()
            }
            
        except ValidationError as e:
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }
    
    def validate_behavior(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate behavior profiles for a system."""
        system = params.get("system")
        if not system:
            raise PipelineError("System parameter is required")
        
        try:
            # Validate behavior profiles for the system
            validation_result = self.behavior_engine.validate_system_behavior(system)
            
            return {
                "success": True,
                "message": f"Behavior validation passed for system: {system}",
                "validation_details": validation_result,
                "timestamp": time.time()
            }
            
        except ValidationError as e:
            return {
                "success": False,
                "error": str(e),
                "system": system
            }
    
    def add_symbols(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add symbols for a system."""
        system = params.get("system")
        symbols = params.get("symbols", [])
        
        if not system:
            raise PipelineError("System parameter is required")
        
        if not symbols:
            # Create default symbol for the system
            symbols = [f"{system}_default"]
        
        created_symbols = []
        errors = []
        
        for symbol in symbols:
            try:
                # Create symbol using symbol manager
                symbol_path = self.symbol_manager.create_symbol(system, symbol)
                created_symbols.append({
                    "name": symbol,
                    "path": str(symbol_path),
                    "status": "created"
                })
                
            except Exception as e:
                errors.append({
                    "symbol": symbol,
                    "error": str(e)
                })
        
        return {
            "success": len(errors) == 0,
            "created_symbols": created_symbols,
            "errors": errors,
            "system": system,
            "timestamp": time.time()
        }
    
    def implement_behavior(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Implement behavior profiles for a system."""
        system = params.get("system")
        if not system:
            raise PipelineError("System parameter is required")
        
        try:
            # Create behavior profile for the system
            behavior_path = self.behavior_engine.create_system_behavior(system)
            
            return {
                "success": True,
                "message": f"Behavior profile created for system: {system}",
                "behavior_path": str(behavior_path),
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "system": system
            }
    
    def run_compliance_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run enterprise compliance validation."""
        system = params.get("system")
        if not system:
            raise PipelineError("System parameter is required")
        
        try:
            # Run compliance checks
            compliance_result = self.validation_engine.run_compliance_check(system)
            
            return {
                "success": True,
                "message": f"Compliance check completed for system: {system}",
                "compliance_details": compliance_result,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "system": system
            }


def main():
    """Main entry point for the pipeline integration service."""
    parser = argparse.ArgumentParser(description="Arxos Pipeline Integration Service")
    parser.add_argument("--operation", required=True, help="Operation to perform")
    parser.add_argument("--params", required=True, help="JSON parameters")
    
    args = parser.parse_args()
    
    try:
        # Parse parameters
        params = json.loads(args.params)
        
        # Create service and handle operation
        service = PipelineIntegrationService()
        result = service.handle_operation(args.operation, params)
        
        # Output result as JSON
        print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if result.get("success", False) else 1)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "operation": args.operation,
            "timestamp": time.time()
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main() 