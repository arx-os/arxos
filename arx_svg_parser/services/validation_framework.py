from typing import Any, Callable, Dict, List, Optional, Type
from pydantic import BaseModel, ValidationError

class ValidationResult:
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str):
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str):
        self.warnings.append(warning)

    def __bool__(self):
        return self.is_valid

class Validator:
    def __init__(self):
        self.field_validators: Dict[str, List[Callable[[Any], Optional[str]]]] = {}
        self.model_validators: List[Callable[[BaseModel], Optional[str]]] = []
        self.warning_validators: List[Callable[[BaseModel], Optional[str]]] = []

    def add_field_validator(self, field: str, func: Callable[[Any], Optional[str]]):
        self.field_validators.setdefault(field, []).append(func)

    def add_model_validator(self, func: Callable[[BaseModel], Optional[str]]):
        self.model_validators.append(func)

    def add_warning_validator(self, func: Callable[[BaseModel], Optional[str]]):
        self.warning_validators.append(func)

    def validate(self, model: BaseModel) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        # Field-level validation
        for field, validators in self.field_validators.items():
            value = getattr(model, field, None)
            for validator in validators:
                error = validator(value)
                if error:
                    result.add_error(f"{field}: {error}")
        # Model-level validation
        for validator in self.model_validators:
            error = validator(model)
            if error:
                result.add_error(error)
        # Warning-level validation
        for validator in self.warning_validators:
            warning = validator(model)
            if warning:
                result.add_warning(warning)
        return result

# Example usage:
#
# from pydantic import BaseModel
# class MyModel(BaseModel):
#     name: str
#     age: int
#
# validator = Validator()
# validator.add_field_validator('age', lambda v: "Must be >= 0" if v < 0 else None)
# validator.add_model_validator(lambda m: "Name cannot be empty" if not m.name else None)
#
# m = MyModel(name="", age=-1)
# result = validator.validate(m)
# print(result.is_valid, result.errors) 