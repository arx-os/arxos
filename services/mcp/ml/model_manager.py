"""
Model Manager for ML Integration

Handles model versioning, loading, management, and lifecycle operations
for machine learning models in the MCP service.
"""

import os
import json
import pickle
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import shutil

from .models import ModelInfo, ModelStatus, TrainingResult


logger = logging.getLogger(__name__)


class ModelManager:
    """Manages machine learning models for the MCP service"""

    def __init__(self, models_dir: str = "ml_models"):
        """
        Initialize the model manager

        Args:
            models_dir: Directory containing model files
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

        # Model registry - maps model_id to ModelInfo
        self.model_registry: Dict[str, ModelInfo] = {}

        # Active models cache
        self.active_models: Dict[str, Any] = {}

        # Load existing models
        self._load_model_registry()
        self._load_active_models()

        logger.info(f"ModelManager initialized with {len(self.model_registry)} models")

    def _load_model_registry(self) -> None:
        """Load the model registry from disk"""
        registry_file = self.models_dir / "model_registry.json"

        if registry_file.exists():
            try:
                with open(registry_file, "r") as f:
                    registry_data = json.load(f)

                for model_data in registry_data.values():
                    # Convert string dates back to datetime
                    if model_data.get("training_date"):
                        model_data["training_date"] = datetime.fromisoformat(
                            model_data["training_date"]
                        )

                    model_info = ModelInfo(**model_data)
                    self.model_registry[model_info.model_id] = model_info

                logger.info(f"Loaded {len(self.model_registry)} models from registry")

            except Exception as e:
                logger.error(f"Failed to load model registry: {e}")
                self.model_registry = {}
        else:
            logger.info("No existing model registry found, starting fresh")

    def _save_model_registry(self) -> None:
        """Save the model registry to disk"""
        registry_file = self.models_dir / "model_registry.json"

        try:
            registry_data = {}
            for model_id, model_info in self.model_registry.items():
                model_dict = model_info.dict()
                # Convert datetime to string for JSON serialization
                if model_dict.get("training_date"):
                    model_dict["training_date"] = model_dict[
                        "training_date"
                    ].isoformat()
                registry_data[model_id] = model_dict

            with open(registry_file, "w") as f:
                json.dump(registry_data, f, indent=2)

            logger.debug("Model registry saved successfully")

        except Exception as e:
            logger.error(f"Failed to save model registry: {e}")

    def _load_active_models(self) -> None:
        """Load active models into memory"""
        for model_id, model_info in self.model_registry.items():
            if model_info.status == ModelStatus.ACTIVE:
                try:
                    self._load_model(model_id)
                    logger.info(f"Loaded active model: {model_info.model_name}")
                except Exception as e:
                    logger.error(f"Failed to load active model {model_id}: {e}")
                    # Mark as error
                    model_info.status = ModelStatus.ERROR
                    self._save_model_registry()

    def _load_model(self, model_id: str) -> Any:
        """Load a specific model into memory"""
        if model_id not in self.model_registry:
            raise ValueError(f"Model {model_id} not found in registry")

        model_info = self.model_registry[model_id]
        model_path = Path(model_info.file_path)

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        try:
            with open(model_path, "rb") as f:
                model = pickle.load(f)

            self.active_models[model_id] = model
            logger.debug(f"Model {model_id} loaded successfully")
            return model

        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            raise

    def _generate_model_id(self, model_name: str, version: str) -> str:
        """Generate a unique model ID"""
        timestamp = datetime.utcnow().isoformat()
        unique_string = f"{model_name}_{version}_{timestamp}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def register_model(
        self,
        model_file: str,
        model_name: str,
        model_type: str,
        version: str,
        description: Optional[str] = None,
    ) -> str:
        """
        Register a new model in the registry

        Args:
            model_file: Path to the model file
            model_name: Human-readable model name
            model_type: Type of model (classification, regression, etc.)
            version: Model version
            description: Optional model description

        Returns:
            Model ID of the registered model
        """
        model_path = Path(model_file)

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}")

        # Generate unique model ID
        model_id = self._generate_model_id(model_name, version)

        # Copy model file to models directory
        dest_path = self.models_dir / f"{model_id}.pkl"
        shutil.copy2(model_path, dest_path)

        # Calculate file size and hash
        file_size = dest_path.stat().st_size
        file_hash = self._calculate_file_hash(dest_path)

        # Create model info
        model_info = ModelInfo(
            model_id=model_id,
            model_name=model_name,
            model_type=model_type,
            version=version,
            status=ModelStatus.INACTIVE,
            file_path=str(dest_path),
            file_size=file_size,
            description=description,
            training_date=datetime.utcnow(),
        )

        # Add to registry
        self.model_registry[model_id] = model_info
        self._save_model_registry()

        logger.info(f"Registered model: {model_name} (ID: {model_id})")
        return model_id

    def activate_model(self, model_id: str) -> bool:
        """
        Activate a model (load it into memory)

        Args:
            model_id: ID of the model to activate

        Returns:
            True if successful, False otherwise
        """
        if model_id not in self.model_registry:
            logger.error(f"Model {model_id} not found in registry")
            return False

        model_info = self.model_registry[model_id]

        try:
            # Load the model
            self._load_model(model_id)

            # Update status
            model_info.status = ModelStatus.ACTIVE
            self._save_model_registry()

            logger.info(f"Activated model: {model_info.model_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to activate model {model_id}: {e}")
            model_info.status = ModelStatus.ERROR
            self._save_model_registry()
            return False

    def deactivate_model(self, model_id: str) -> bool:
        """
        Deactivate a model (remove from memory)

        Args:
            model_id: ID of the model to deactivate

        Returns:
            True if successful, False otherwise
        """
        if model_id not in self.model_registry:
            logger.error(f"Model {model_id} not found in registry")
            return False

        model_info = self.model_registry[model_id]

        # Remove from active models
        if model_id in self.active_models:
            del self.active_models[model_id]

        # Update status
        model_info.status = ModelStatus.INACTIVE
        self._save_model_registry()

        logger.info(f"Deactivated model: {model_info.model_name}")
        return True

    def get_model(self, model_id: str) -> Optional[Any]:
        """
        Get a model by ID (load if not active)

        Args:
            model_id: ID of the model to get

        Returns:
            The model object or None if not found
        """
        if model_id not in self.model_registry:
            logger.error(f"Model {model_id} not found in registry")
            return None

        # If not in active models, load it
        if model_id not in self.active_models:
            try:
                self._load_model(model_id)
            except Exception as e:
                logger.error(f"Failed to load model {model_id}: {e}")
                return None

        return self.active_models.get(model_id)

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get model information

        Args:
            model_id: ID of the model

        Returns:
            ModelInfo object or None if not found
        """
        return self.model_registry.get(model_id)

    def list_models(self, status: Optional[ModelStatus] = None) -> List[ModelInfo]:
        """
        List all models, optionally filtered by status

        Args:
            status: Optional status filter

        Returns:
            List of ModelInfo objects
        """
        models = list(self.model_registry.values())

        if status:
            models = [m for m in models if m.status == status]

        return models

    def delete_model(self, model_id: str) -> bool:
        """
        Delete a model from the registry

        Args:
            model_id: ID of the model to delete

        Returns:
            True if successful, False otherwise
        """
        if model_id not in self.model_registry:
            logger.error(f"Model {model_id} not found in registry")
            return False

        model_info = self.model_registry[model_id]

        try:
            # Remove from active models
            if model_id in self.active_models:
                del self.active_models[model_id]

            # Delete model file
            model_path = Path(model_info.file_path)
            if model_path.exists():
                model_path.unlink()

            # Remove from registry
            del self.model_registry[model_id]
            self._save_model_registry()

            logger.info(f"Deleted model: {model_info.model_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete model {model_id}: {e}")
            return False

    def update_model_accuracy(self, model_id: str, accuracy: float) -> bool:
        """
        Update model accuracy

        Args:
            model_id: ID of the model
            accuracy: New accuracy value

        Returns:
            True if successful, False otherwise
        """
        if model_id not in self.model_registry:
            logger.error(f"Model {model_id} not found in registry")
            return False

        model_info = self.model_registry[model_id]
        model_info.accuracy = accuracy
        self._save_model_registry()

        logger.info(f"Updated accuracy for model {model_id}: {accuracy}")
        return True

    def get_active_models_count(self) -> int:
        """Get the number of active models"""
        return len(
            [m for m in self.model_registry.values() if m.status == ModelStatus.ACTIVE]
        )

    def get_total_models_count(self) -> int:
        """Get the total number of models"""
        return len(self.model_registry)

    def get_model_statistics(self) -> Dict[str, Any]:
        """Get statistics about all models"""
        total_models = len(self.model_registry)
        active_models = len(
            [m for m in self.model_registry.values() if m.status == ModelStatus.ACTIVE]
        )
        inactive_models = len(
            [
                m
                for m in self.model_registry.values()
                if m.status == ModelStatus.INACTIVE
            ]
        )
        error_models = len(
            [m for m in self.model_registry.values() if m.status == ModelStatus.ERROR]
        )

        # Calculate average accuracy
        accuracies = [
            m.accuracy for m in self.model_registry.values() if m.accuracy is not None
        ]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0

        # Calculate total file size
        total_size = sum(m.file_size or 0 for m in self.model_registry.values())

        return {
            "total_models": total_models,
            "active_models": active_models,
            "inactive_models": inactive_models,
            "error_models": error_models,
            "average_accuracy": avg_accuracy,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
        }
