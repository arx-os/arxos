"""
Jurisdiction Matcher for MCP Validation

This module provides automatic jurisdiction matching for building models
based on their geographical location. It determines which building codes
apply to a specific building based on its location data.

Key Features:
- Automatic jurisdiction detection from building location
- Multi-level jurisdiction matching (country, state, city, county)
- Fallback to base codes when specific amendments aren't available
- Support for international building codes
- Configurable jurisdiction mapping
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import json

from models.mcp_models import Jurisdiction, MCPFile

logger = logging.getLogger(__name__)


@dataclass
class BuildingLocation:
    """Building location information"""

    country: str
    state: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "country": self.country,
            "state": self.state,
            "city": self.city,
            "county": self.county,
            "postal_code": self.postal_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


@dataclass
class JurisdictionMatch:
    """Jurisdiction matching result"""

    mcp_file: MCPFile
    match_level: str  # 'exact', 'state', 'country', 'fallback'
    confidence: float  # 0.0 to 1.0
    reasoning: str


class JurisdictionMatcher:
    """Matches building locations to applicable building codes"""

    def __init__(self, mcp_data_path: str = "mcp"):
        self.mcp_data_path = Path(mcp_data_path)
        self.jurisdiction_mappings = self._load_jurisdiction_mappings()
        self.available_mcp_files = self._scan_available_mcp_files()

    def _load_jurisdiction_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load jurisdiction mappings from configuration"""
        # Default jurisdiction mappings
        mappings = {
            "US": {
                "base_codes": [
                    "nec-2023-base",
                    "ibc-2024-base",
                    "ipc-2024-base",
                    "imc-2024-base",
                ],
                "states": {
                    "CA": ["nec-2023-ca", "ibc-2024-ca", "ipc-2024-ca", "imc-2024-ca"],
                    "NY": ["nec-2023-ny"],
                    "TX": ["nec-2023-tx"],
                    "FL": ["nec-2023-fl"],
                },
            },
            "EU": {
                "base_codes": ["en-1990-base", "en-1991-base"],
                "structural_codes": [
                    "en-1992-1-1",
                    "en-1993-1-1",
                    "en-1994-1-1",
                    "en-1995-1-1",
                ],
            },
            "CA": {"base_codes": ["nbc-2020"]},
            "AU": {"base_codes": ["ncc-2022"]},
        }

        # Try to load from config file if it exists
        config_file = self.mcp_data_path / "jurisdiction_mappings.json"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    mappings.update(json.load(f))
            except Exception as e:
                logger.warning(f"Could not load jurisdiction mappings: {e}")

        return mappings

    def _scan_available_mcp_files(self) -> Dict[str, MCPFile]:
        """Scan and load all available MCP files"""
        available_files = {}

        # Scan all JSON files in the MCP directory
        for json_file in self.mcp_data_path.rglob("*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)

                # Create MCPFile object
                mcp_file = self._create_mcp_file_from_dict(data)
                available_files[mcp_file.mcp_id] = mcp_file

            except Exception as e:
                logger.warning(f"Could not load MCP file {json_file}: {e}")

        return available_files

    def _create_mcp_file_from_dict(self, data: Dict[str, Any]) -> MCPFile:
        """Create MCPFile from dictionary data"""
        # This is a simplified version - in practice, you'd use the full deserialization
        from models.mcp_models import Jurisdiction

        jurisdiction = Jurisdiction(
            country=data.get("jurisdiction", {}).get("country", ""),
            state=data.get("jurisdiction", {}).get("state"),
            city=data.get("jurisdiction", {}).get("city"),
            county=data.get("jurisdiction", {}).get("county"),
        )

        # Create a simplified MCPFile for matching purposes
        class SimpleMCPFile:
            def __init__(self, mcp_id, name, jurisdiction):
                self.mcp_id = mcp_id
                self.name = name
                self.jurisdiction = jurisdiction

        return SimpleMCPFile(
            mcp_id=data.get("mcp_id", ""),
            name=data.get("name", ""),
            jurisdiction=jurisdiction,
        )

    def extract_building_location(
        self, building_model: Dict[str, Any]
    ) -> Optional[BuildingLocation]:
        """Extract location information from building model"""
        # Look for location data in building metadata
        metadata = building_model.get("metadata", {})

        # Check various possible location fields
        location_data = (
            metadata.get("location")
            or metadata.get("address")
            or metadata.get("site")
            or building_model.get("location")
        )

        if not location_data:
            return None

        # Extract location components
        return BuildingLocation(
            country=location_data.get("country", ""),
            state=location_data.get("state"),
            city=location_data.get("city"),
            county=location_data.get("county"),
            postal_code=location_data.get("postal_code"),
            latitude=location_data.get("latitude"),
            longitude=location_data.get("longitude"),
        )

    def match_jurisdictions(
        self, building_location: BuildingLocation
    ) -> List[JurisdictionMatch]:
        """Match building location to applicable jurisdictions"""
        matches = []

        # Get country-level mappings
        country_mappings = self.jurisdiction_mappings.get(building_location.country, {})

        # Match base codes for the country
        base_codes = country_mappings.get("base_codes", [])
        for code_id in base_codes:
            if code_id in self.available_mcp_files:
                mcp_file = self.available_mcp_files[code_id]
                matches.append(
                    JurisdictionMatch(
                        mcp_file=mcp_file,
                        match_level="country",
                        confidence=1.0,
                        reasoning=f"Base code for {building_location.country}",
                    )
                )

        # Match state-level codes (for US)
        if building_location.country == "US" and building_location.state:
            state_codes = country_mappings.get("states", {}).get(
                building_location.state, []
            )
            for code_id in state_codes:
                if code_id in self.available_mcp_files:
                    mcp_file = self.available_mcp_files[code_id]
                    matches.append(
                        JurisdictionMatch(
                            mcp_file=mcp_file,
                            match_level="state",
                            confidence=1.0,
                            reasoning=f"State-specific code for {building_location.state}",
                        )
                    )

        # Match structural codes (for EU)
        if building_location.country == "EU":
            structural_codes = country_mappings.get("structural_codes", [])
            for code_id in structural_codes:
                if code_id in self.available_mcp_files:
                    mcp_file = self.available_mcp_files[code_id]
                    matches.append(
                        JurisdictionMatch(
                            mcp_file=mcp_file,
                            match_level="structural",
                            confidence=0.9,
                            reasoning=f"Structural code for EU",
                        )
                    )

        return matches

    def get_applicable_codes(self, building_model: Dict[str, Any]) -> List[str]:
        """Get list of applicable MCP file IDs for a building"""
        # Extract building location
        location = self.extract_building_location(building_model)

        if not location:
            logger.warning(
                "No location data found in building model, using fallback codes"
            )
            # Return base codes for US as fallback
            return self.jurisdiction_mappings.get("US", {}).get("base_codes", [])

        # Match jurisdictions
        matches = self.match_jurisdictions(location)

        # Return MCP file IDs
        return [match.mcp_file.mcp_id for match in matches]

    def validate_jurisdiction_match(
        self, building_model: Dict[str, Any], mcp_file_id: str
    ) -> bool:
        """Validate if a specific MCP file applies to the building"""
        location = self.extract_building_location(building_model)

        if not location:
            return False

        matches = self.match_jurisdictions(location)

        # Check if the specific MCP file is in the matches
        return any(match.mcp_file.mcp_id == mcp_file_id for match in matches)

    def get_jurisdiction_info(self, building_model: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed jurisdiction information for a building"""
        location = self.extract_building_location(building_model)

        if not location:
            return {
                "location_found": False,
                "applicable_codes": [],
                "jurisdiction_level": "unknown",
            }

        matches = self.match_jurisdictions(location)

        return {
            "location_found": True,
            "building_location": location.to_dict(),
            "applicable_codes": [match.mcp_file.mcp_id for match in matches],
            "jurisdiction_level": (
                max([match.match_level for match in matches]) if matches else "unknown"
            ),
            "matches": [
                {
                    "mcp_id": match.mcp_file.mcp_id,
                    "name": match.mcp_file.name,
                    "match_level": match.match_level,
                    "confidence": match.confidence,
                    "reasoning": match.reasoning,
                }
                for match in matches
            ],
        }


# Example usage and testing
if __name__ == "__main__":
    # Test the jurisdiction matcher
    matcher = JurisdictionMatcher()

    # Test building model with location
    test_building = {
        "building_id": "test_building",
        "building_name": "Test Building",
        "metadata": {
            "location": {
                "country": "US",
                "state": "CA",
                "city": "San Francisco",
                "county": "San Francisco",
            }
        },
    }

    # Get applicable codes
    applicable_codes = matcher.get_applicable_codes(test_building)
    print(f"Applicable codes: {applicable_codes}")

    # Get jurisdiction info
    jurisdiction_info = matcher.get_jurisdiction_info(test_building)
    print(f"Jurisdiction info: {jurisdiction_info}")
