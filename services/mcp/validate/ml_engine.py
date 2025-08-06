"""
Machine Learning Rules Engine for MCP Rule Validation

This module provides ML-based rule capabilities:
- Predictive compliance analysis
- Machine learning model integration
- Feature extraction and prediction
- ML-based rule recommendations
- Computer vision for plan analysis (lightweight)
- NLP for building code interpretation (lightweight)
"""

import logging
import pickle
import os
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
import json

# Try to import optional dependencies, but don't fail if they're missing
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: numpy not available, using fallback calculations")

try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    import joblib

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available, using fallback ML")

try:
    import cv2

    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("Warning: opencv-python not available, using fallback CV")

try:
    import tensorflow as tf

    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: tensorflow not available, using fallback models")

try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    import torch

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available, using fallback NLP")

from models.mcp_models import (
    BuildingModel,
    BuildingObject,
    MCPFile,
    MCPRule,
    RuleCondition,
    RuleAction,
    ValidationViolation,
    RuleCategory,
)
from validate.rule_engine import MCPRuleEngine, RuleExecutionContext


@dataclass
class MLFeature:
    """Machine learning feature definition"""

    name: str
    feature_type: str  # 'numeric', 'categorical', 'boolean'
    source: str  # 'property', 'location', 'calculated'
    property_name: Optional[str] = None
    calculation: Optional[str] = None
    default_value: Any = None


@dataclass
class MLPrediction:
    """Machine learning prediction result"""

    rule_id: str
    prediction: Union[bool, float]
    confidence: float
    features_used: List[str]
    feature_values: Dict[str, Any]
    model_type: str


@dataclass
class ComputerVisionResult:
    """Computer vision analysis result"""

    image_path: str
    violations_detected: List[Dict[str, Any]]
    compliance_score: float
    confidence: float
    analysis_type: str


@dataclass
class NLPResult:
    """Natural language processing result"""

    text_content: str
    extracted_rules: List[Dict[str, Any]]
    compliance_analysis: Dict[str, Any]
    confidence: float
    language: str


class ComputerVisionEngine:
    """Computer vision engine for plan analysis and validation (lightweight)"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # CV settings
        self.model_directory = self.config.get("cv_model_directory", "./ml_models/cv")
        self.min_confidence = self.config.get("cv_min_confidence", 0.7)
        self.enable_gpu = self.config.get(
            "cv_enable_gpu", False
        )  # Disabled for lightweight version

        # Create model directory
        os.makedirs(self.model_directory, exist_ok=True)

        self.logger.info("Computer Vision Engine initialized (lightweight mode)")

    def analyze_building_plan(self, image_path: str) -> ComputerVisionResult:
        """Analyze building plan for compliance violations (lightweight)"""
        try:
            # Check if image exists
            if not os.path.exists(image_path):
                return ComputerVisionResult(
                    image_path=image_path,
                    violations_detected=[],
                    compliance_score=0.0,
                    confidence=0.0,
                    analysis_type="building_plan",
                )

            # Lightweight analysis (placeholder)
            violations = []
            compliance_score = 0.85  # Placeholder score

            return ComputerVisionResult(
                image_path=image_path,
                violations_detected=violations,
                compliance_score=compliance_score,
                confidence=0.85,
                analysis_type="building_plan",
            )

        except Exception as e:
            self.logger.error(f"Error analyzing building plan: {e}")
            return ComputerVisionResult(
                image_path=image_path,
                violations_detected=[],
                compliance_score=0.0,
                confidence=0.0,
                analysis_type="building_plan",
            )

    def extract_text_from_plans(self, image_path: str) -> List[str]:
        """Extract text from building plans using OCR (lightweight)"""
        try:
            if not os.path.exists(image_path):
                return []

            # Placeholder text extraction
            extracted_text = ["Sample text from plan", "Building code reference"]

            return extracted_text

        except Exception as e:
            self.logger.error(f"Error extracting text from plans: {e}")
            return []

    def detect_spatial_violations(self, image_path: str) -> List[Dict[str, Any]]:
        """Detect spatial violations in building plans (lightweight)"""
        try:
            if not os.path.exists(image_path):
                return []

            # Placeholder spatial violation detection
            violations = []

            return violations

        except Exception as e:
            self.logger.error(f"Error detecting spatial violations: {e}")
            return []


class NLPEngine:
    """Natural language processing engine for building code interpretation (lightweight)"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # NLP settings
        self.model_directory = self.config.get("nlp_model_directory", "./ml_models/nlp")
        self.min_confidence = self.config.get("nlp_min_confidence", 0.7)
        self.supported_languages = self.config.get(
            "supported_languages", ["en", "de", "fr"]
        )

        # Create model directory
        os.makedirs(self.model_directory, exist_ok=True)

        self.logger.info("NLP Engine initialized (lightweight mode)")

    def interpret_building_code(
        self, text_content: str, language: str = "en"
    ) -> NLPResult:
        """Interpret building code text and extract rules (lightweight)"""
        try:
            # Simple rule extraction using regex
            extracted_rules = self._extract_rules_from_text(text_content, language)

            # Simple compliance analysis
            compliance_analysis = self._analyze_compliance(
                text_content, extracted_rules
            )

            return NLPResult(
                text_content=text_content,
                extracted_rules=extracted_rules,
                compliance_analysis=compliance_analysis,
                confidence=0.8,
                language=language,
            )

        except Exception as e:
            self.logger.error(f"Error interpreting building code: {e}")
            return NLPResult(
                text_content=text_content,
                extracted_rules=[],
                compliance_analysis={},
                confidence=0.0,
                language=language,
            )

    def extract_requirements(self, regulation_text: str) -> List[Dict[str, Any]]:
        """Extract requirements from regulation text (lightweight)"""
        try:
            requirements = []

            # Extract numerical requirements using regex
            numerical_reqs = self._extract_numerical_requirements(regulation_text)
            requirements.extend(numerical_reqs)

            # Extract categorical requirements
            categorical_reqs = self._extract_categorical_requirements(regulation_text)
            requirements.extend(categorical_reqs)

            return requirements

        except Exception as e:
            self.logger.error(f"Error extracting requirements: {e}")
            return []

    def analyze_compliance_text(self, text_content: str) -> Dict[str, Any]:
        """Analyze compliance from text content (lightweight)"""
        try:
            analysis = {
                "compliance_score": 0.0,
                "violations_detected": [],
                "recommendations": [],
                "confidence": 0.0,
            }

            # Simple compliance analysis
            compliance_indicators = self._analyze_compliance_indicators(text_content)
            analysis["compliance_score"] = self._calculate_text_compliance_score(
                compliance_indicators
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing compliance text: {e}")
            return {
                "compliance_score": 0.0,
                "violations_detected": [],
                "recommendations": [],
                "confidence": 0.0,
            }

    def _extract_rules_from_text(
        self, text: str, language: str
    ) -> List[Dict[str, Any]]:
        """Extract rules from text content using regex"""
        rules = []

        # Simple regex-based rule extraction
        rule_patterns = [
            r"EN\s+\d{4}-\d+\.\d+\.\d+",
            r"Section\s+\d+\.\d+",
            r"Article\s+\d+",
            r"Clause\s+\d+",
        ]

        for pattern in rule_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                rules.append(
                    {"rule_id": match, "type": "structural", "confidence": 0.8}
                )

        return rules

    def _analyze_compliance(
        self, text: str, rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze compliance based on text and extracted rules"""
        analysis = {
            "compliance_score": 0.8,  # Placeholder
            "rule_coverage": len(rules) / 10.0,  # Placeholder
            "violation_count": 0,
        }

        return analysis

    def _extract_numerical_requirements(self, text: str) -> List[Dict[str, Any]]:
        """Extract numerical requirements from text using regex"""
        requirements = []

        # Extract numbers followed by units
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(kN|m²|mm|cm|m|kg)",
            r"minimum\s+(\d+(?:\.\d+)?)",
            r"maximum\s+(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*years?",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    value, unit = match
                else:
                    value = match
                    unit = "units"

                requirements.append(
                    {
                        "type": "numerical",
                        "value": float(value),
                        "unit": unit,
                        "confidence": 0.8,
                    }
                )

        return requirements

    def _extract_categorical_requirements(self, text: str) -> List[Dict[str, Any]]:
        """Extract categorical requirements from text"""
        requirements = []

        # Simple keyword-based extraction
        keywords = ["required", "shall", "must", "should", "prohibited"]

        for keyword in keywords:
            if keyword.lower() in text.lower():
                requirements.append(
                    {"type": "categorical", "requirement": keyword, "confidence": 0.7}
                )

        return requirements

    def _analyze_compliance_indicators(self, text: str) -> Dict[str, Any]:
        """Analyze compliance indicators in text"""
        indicators = {
            "positive_indicators": 0,
            "negative_indicators": 0,
            "neutral_indicators": 0,
        }

        # Simple keyword analysis
        positive_words = ["compliance", "approved", "acceptable", "adequate"]
        negative_words = ["violation", "non-compliant", "inadequate", "prohibited"]

        text_lower = text.lower()

        for word in positive_words:
            if word in text_lower:
                indicators["positive_indicators"] += 1

        for word in negative_words:
            if word in text_lower:
                indicators["negative_indicators"] += 1

        return indicators

    def _calculate_text_compliance_score(self, indicators: Dict[str, Any]) -> float:
        """Calculate compliance score from text indicators"""
        total = sum(indicators.values())
        if total == 0:
            return 0.5

        positive = indicators.get("positive_indicators", 0)
        negative = indicators.get("negative_indicators", 0)

        return max(0.0, min(1.0, (positive - negative) / total + 0.5))


class MLRuleEngine:
    """
    Machine learning rules engine for predictive validation (lightweight)

    Features:
    - Predictive compliance analysis
    - Feature extraction from building models
    - ML model training and prediction (basic)
    - Computer vision integration (lightweight)
    - NLP integration (lightweight)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ML rules engine

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # ML settings
        self.model_directory = self.config.get("model_directory", "./ml_models")
        self.min_confidence = self.config.get("min_confidence", 0.7)
        self.feature_scaling = self.config.get(
            "feature_scaling", False
        )  # Disabled for lightweight

        # Initialize base engine
        self.base_engine = MCPRuleEngine(config)

        # Initialize specialized engines
        self.cv_engine = ComputerVisionEngine(config)
        self.nlp_engine = NLPEngine(config)

        # ML models and features (basic implementation)
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        self.label_encoders: Dict[str, Any] = {}
        self.feature_definitions: Dict[str, List[MLFeature]] = {}

        # Create model directory
        os.makedirs(self.model_directory, exist_ok=True)

        self.logger.info("ML Rule Engine initialized (lightweight mode)")

    def analyze_building_plan_cv(self, image_path: str) -> ComputerVisionResult:
        """Analyze building plan using computer vision"""
        return self.cv_engine.analyze_building_plan(image_path)

    def interpret_building_code_nlp(
        self, text_content: str, language: str = "en"
    ) -> NLPResult:
        """Interpret building code using NLP"""
        return self.nlp_engine.interpret_building_code(text_content, language)

    def extract_requirements_nlp(self, regulation_text: str) -> List[Dict[str, Any]]:
        """Extract requirements from regulation text using NLP"""
        return self.nlp_engine.extract_requirements(regulation_text)

    def analyze_compliance_text_nlp(self, text_content: str) -> Dict[str, Any]:
        """Analyze compliance from text content using NLP"""
        return self.nlp_engine.analyze_compliance_text(text_content)

    def detect_spatial_violations_cv(self, image_path: str) -> List[Dict[str, Any]]:
        """Detect spatial violations using computer vision"""
        return self.cv_engine.detect_spatial_violations(image_path)

    def extract_text_from_plans_cv(self, image_path: str) -> List[str]:
        """Extract text from building plans using OCR"""
        return self.cv_engine.extract_text_from_plans(image_path)

    def define_features(self, rule_id: str, features: List[MLFeature]):
        """Define features for a specific rule"""
        self.feature_definitions[rule_id] = features
        self.logger.info(f"Defined {len(features)} features for rule {rule_id}")

    def extract_features(
        self, building_model: BuildingModel, rule_id: str
    ) -> Dict[str, Any]:
        """
        Extract features from building model for ML prediction

        Args:
            building_model: Building model to analyze
            rule_id: Rule ID for feature extraction

        Returns:
            Dictionary of extracted features
        """
        features = {}

        if rule_id not in self.feature_definitions:
            self.logger.warning(f"No feature definitions found for rule {rule_id}")
            return features

        for feature_def in self.feature_definitions[rule_id]:
            try:
                if feature_def.source == "property":
                    value = self._extract_property_feature(building_model, feature_def)
                elif feature_def.source == "location":
                    value = self._extract_location_feature(building_model, feature_def)
                elif feature_def.source == "calculated":
                    value = self._extract_calculated_feature(
                        building_model, feature_def
                    )
                else:
                    value = feature_def.default_value

                features[feature_def.name] = value

            except Exception as e:
                self.logger.error(f"Error extracting feature {feature_def.name}: {e}")
                features[feature_def.name] = feature_def.default_value

        return features

    def _extract_property_feature(
        self, building_model: BuildingModel, feature_def: MLFeature
    ) -> Any:
        """Extract property-based feature from building model"""
        if not feature_def.property_name:
            return feature_def.default_value

        # Extract property from building objects
        values = []
        for obj in building_model.objects:
            if feature_def.property_name in obj.properties:
                values.append(obj.properties[feature_def.property_name])

        if not values:
            return feature_def.default_value

        # Return appropriate value based on feature type
        if feature_def.feature_type == "numeric":
            return float(sum(values)) if values else 0.0
        elif feature_def.feature_type == "categorical":
            return values[0] if values else feature_def.default_value
        elif feature_def.feature_type == "boolean":
            return any(values) if values else False
        else:
            return values[0] if values else feature_def.default_value

    def _extract_location_feature(
        self, building_model: BuildingModel, feature_def: MLFeature
    ) -> Any:
        """Extract location-based feature from building model"""
        if not feature_def.property_name:
            return feature_def.default_value

        # Extract location-based features
        values = []
        for obj in building_model.objects:
            if obj.location and feature_def.property_name in obj.location:
                values.append(obj.location[feature_def.property_name])

        if not values:
            return feature_def.default_value

        # Return appropriate value based on feature type
        if feature_def.feature_type == "numeric":
            return float(sum(values)) if values else 0.0
        elif feature_def.feature_type == "categorical":
            return values[0] if values else feature_def.default_value
        elif feature_def.feature_type == "boolean":
            return any(values) if values else False
        else:
            return values[0] if values else feature_def.default_value

    def _extract_calculated_feature(
        self, building_model: BuildingModel, feature_def: MLFeature
    ) -> Any:
        """Extract calculated feature from building model"""
        if not feature_def.calculation:
            return feature_def.default_value

        try:
            # Simple calculation evaluation
            calculation = feature_def.calculation

            # Extract variables from building model
            variables = {}
            for obj in building_model.objects:
                for key, value in obj.properties.items():
                    if key not in variables:
                        variables[key] = []
                    variables[key].append(value)

            # Calculate feature value
            if feature_def.feature_type == "numeric":
                return float(len(building_model.objects))  # Placeholder calculation
            elif feature_def.feature_type == "categorical":
                return "default"  # Placeholder
            elif feature_def.feature_type == "boolean":
                return len(building_model.objects) > 0  # Placeholder
            else:
                return feature_def.default_value

        except Exception as e:
            self.logger.error(f"Error calculating feature {feature_def.name}: {e}")
            return feature_def.default_value

    def predict_compliance(
        self, building_model: BuildingModel, rule_id: str
    ) -> MLPrediction:
        """
        Predict compliance for building model using ML (basic implementation)

        Args:
            building_model: Building model to analyze
            rule_id: Rule ID for prediction

        Returns:
            ML prediction result
        """
        try:
            # Extract features
            features = self.extract_features(building_model, rule_id)

            # Basic prediction logic (placeholder for ML)
            prediction = True  # Placeholder
            confidence = 0.8  # Placeholder

            return MLPrediction(
                rule_id=rule_id,
                prediction=prediction,
                confidence=confidence,
                features_used=list(features.keys()),
                feature_values=features,
                model_type="basic",
            )

        except Exception as e:
            self.logger.error(f"Error predicting compliance for rule {rule_id}: {e}")
            return MLPrediction(
                rule_id=rule_id,
                prediction=False,
                confidence=0.0,
                features_used=[],
                feature_values={},
                model_type="unknown",
            )

    def create_ml_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        features: List[MLFeature],
        actions: List[RuleAction],
        model_type: str = "classifier",
    ) -> MCPRule:
        """
        Create ML-based rule

        Args:
            rule_id: Unique rule identifier
            name: Rule name
            description: Rule description
            features: List of ML features
            actions: List of rule actions
            model_type: Type of ML model

        Returns:
            Created MCP rule
        """
        # Define features for the rule
        self.define_features(rule_id, features)

        # Create rule
        rule = MCPRule(
            rule_id=rule_id,
            name=name,
            description=description,
            category=RuleCategory.STRUCTURAL_SAFETY,
            severity="error",
            enabled=True,
            conditions=[],  # ML rules don't have traditional conditions
            actions=actions,
            metadata={
                "ml_model_type": model_type,
                "feature_count": len(features),
                "is_ml_rule": True,
            },
        )

        return rule

    def validate_building_model_ml(
        self, building_model: BuildingModel, mcp_files: List[str]
    ) -> Dict[str, Any]:
        """
        Validate building model using ML predictions (basic implementation)

        Args:
            building_model: Building model to validate
            mcp_files: List of MCP file paths

        Returns:
            ML validation results
        """
        try:
            results = {
                "ml_predictions": [],
                "cv_analysis": None,
                "nlp_analysis": None,
                "overall_compliance_score": 0.0,
                "confidence": 0.0,
            }

            # Load MCP files and find ML rules
            ml_rules = []
            for mcp_file_path in mcp_files:
                try:
                    mcp_file = self.base_engine.load_mcp_file(mcp_file_path)
                    for rule in mcp_file.rules:
                        if self._is_ml_rule(rule):
                            ml_rules.append(rule)
                except Exception as e:
                    self.logger.error(f"Error loading MCP file {mcp_file_path}: {e}")
                    continue

            # Make ML predictions for each rule
            for rule in ml_rules:
                prediction = self.predict_compliance(building_model, rule.rule_id)
                results["ml_predictions"].append(prediction)

                # Execute ML rule actions
                rule_results = self._execute_ml_rule(rule, building_model, prediction)
                results.update(rule_results)

            # Calculate overall compliance score
            if results["ml_predictions"]:
                compliance_scores = [p.confidence for p in results["ml_predictions"]]
                results["overall_compliance_score"] = sum(compliance_scores) / len(
                    compliance_scores
                )
                results["confidence"] = min(compliance_scores)

            return results

        except Exception as e:
            self.logger.error(f"Error in ML validation: {e}")
            return {
                "ml_predictions": [],
                "cv_analysis": None,
                "nlp_analysis": None,
                "overall_compliance_score": 0.0,
                "confidence": 0.0,
            }

    def _is_ml_rule(self, rule: MCPRule) -> bool:
        """Check if rule is an ML-based rule"""
        return rule.metadata and rule.metadata.get("is_ml_rule", False)

    def _execute_ml_rule(
        self, rule: MCPRule, building_model: BuildingModel, prediction: MLPrediction
    ) -> Dict[str, Any]:
        """Execute ML rule and return results"""
        results = {}

        try:
            # Execute actions based on prediction
            for action in rule.actions:
                if action.type == ActionType.VALIDATION:
                    if prediction.prediction == False:  # Violation predicted
                        results["violations"] = results.get("violations", [])
                        results["violations"].append(
                            {
                                "rule_id": rule.rule_id,
                                "rule_name": rule.name,
                                "prediction_confidence": prediction.confidence,
                                "message": action.message,
                            }
                        )

                elif action.type == ActionType.CALCULATION:
                    results["calculations"] = results.get("calculations", {})
                    results["calculations"][rule.rule_id] = {
                        "prediction": prediction.prediction,
                        "confidence": prediction.confidence,
                        "features_used": prediction.features_used,
                    }

        except Exception as e:
            self.logger.error(f"Error executing ML rule {rule.rule_id}: {e}")

        return results
