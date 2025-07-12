"""
Database utilities for BIM model persistence.
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path

from models.bim import BIMModel


class BIMDatabase:
    """Database interface for BIM model persistence."""
    
    def __init__(self, db_path: str = "bim_models.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
    
    def save_model(self, model: BIMModel) -> bool:
        """Save BIM model to database."""
        try:
            # Implementation for real persistence logic
            model_data = {
                "id": model.id,
                "name": model.name,
                "description": model.description,
                "model_metadata": model.model_metadata,
                "created_at": model.created_at.isoformat() if model.created_at else None,
                "updated_at": model.updated_at.isoformat() if model.updated_at else None,
                "created_by": model.created_by,
                "project_id": model.project_id,
                "version": model.version,
                "is_active": model.is_active
            }
            
            with open(self.db_path, 'w') as f:
                json.dump(model_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self, model_id: str) -> Optional[BIMModel]:
        """Load BIM model from database."""
        try:
            # Implementation for real loading logic
            if not self.db_path.exists():
                return None
            
            with open(self.db_path, 'r') as f:
                data = json.load(f)
            
            model = BIMModel(
                id=data["id"],
                name=data["name"],
                description=data.get("description"),
                model_metadata=data.get("model_metadata", {})
            )
            return model
        except Exception as e:
            print(f"Error loading model: {e}")
            return None 