import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import jsonschema

class SymbolSchemaValidator:
    """
    Validates symbol data against the Arxos symbol JSON schema.
    Loads the schema from arx-symbol-library/schemas/symbol.schema.json.
    """
    def __init__(self, schema_path: Optional[Union[str, Path]] = None):
        if schema_path is None:
            # Default path relative to this file
            base = Path(__file__).parent.parent.parent
            schema_path = base / "arx-symbol-library" / "schemas" / "symbol.schema.json"
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        self.validator = jsonschema.Draft7Validator(self.schema)

    def _load_schema(self) -> Dict[str, Any]:
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def validate_symbol(self, symbol: Union[Dict[str, Any], str, Path]) -> (bool, List[str]):
        """
        Validate a single symbol dict or JSON file.
        Returns (is_valid, error_list)
        """
        if isinstance(symbol, (str, Path)):
            with open(symbol, 'r', encoding='utf-8') as f:
                symbol = json.load(f)
        errors = sorted(self.validator.iter_errors(symbol), key=lambda e: e.path)
        if not errors:
            return True, []
        error_msgs = [self._format_error(e) for e in errors]
        return False, error_msgs

    def validate_symbols(self, symbols: Union[List[Dict[str, Any]], str, Path]) -> List[Dict[str, Any]]:
        """
        Validate a list of symbols (or a file containing a list).
        Returns a list of dicts: {"index": i, "valid": bool, "errors": [str]}
        """
        if isinstance(symbols, (str, Path)):
            with open(symbols, 'r', encoding='utf-8') as f:
                symbols = json.load(f)
        results = []
        for i, symbol in enumerate(symbols):
            valid, errors = self.validate_symbol(symbol)
            results.append({"index": i, "valid": valid, "errors": errors})
        return results

    def _format_error(self, error: jsonschema.ValidationError) -> str:
        path = ".".join([str(p) for p in error.path])
        if path:
            return f"{path}: {error.message}"
        return error.message 