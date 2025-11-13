import { useState, useEffect } from "react";
import { Building2, ChevronDown } from "lucide-react";
import type { BuildingSummary, Building, Floor } from "../../../lib/wasm/geometry";
import { getBuildings, getBuilding } from "../../../lib/wasm/geometry";

interface FloorSelectorProps {
  onFloorSelect: (floor: Floor, buildingPath: string) => void;
  selectedFloorId: string | null;
}

export function FloorSelector({ onFloorSelect, selectedFloorId }: FloorSelectorProps) {
  const [buildings, setBuildings] = useState<BuildingSummary[]>([]);
  const [selectedBuilding, setSelectedBuilding] = useState<Building | null>(null);
  const [isLoadingBuildings, setIsLoadingBuildings] = useState(true);
  const [isLoadingFloors, setIsLoadingFloors] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isBuildingDropdownOpen, setIsBuildingDropdownOpen] = useState(false);
  const [isFloorDropdownOpen, setIsFloorDropdownOpen] = useState(false);

  // Load buildings on mount
  useEffect(() => {
    const loadBuildings = async () => {
      try {
        setIsLoadingBuildings(true);
        setError(null);
        const buildingList = await getBuildings();
        setBuildings(buildingList);

        // Auto-select first building
        if (buildingList.length > 0) {
          await loadBuilding(buildingList[0].path);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load buildings");
      } finally {
        setIsLoadingBuildings(false);
      }
    };

    loadBuildings();
  }, []);

  const loadBuilding = async (path: string) => {
    try {
      setIsLoadingFloors(true);
      setError(null);
      const building = await getBuilding(path);
      setSelectedBuilding(building);

      // Auto-select first floor
      if (building.floors.length > 0) {
        onFloorSelect(building.floors[0], building.path);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load building");
    } finally {
      setIsLoadingFloors(false);
    }
  };

  const handleBuildingSelect = async (buildingSummary: BuildingSummary) => {
    setIsBuildingDropdownOpen(false);
    await loadBuilding(buildingSummary.path);
  };

  const handleFloorSelect = (floor: Floor) => {
    setIsFloorDropdownOpen(false);
    if (selectedBuilding) {
      onFloorSelect(floor, selectedBuilding.path);
    }
  };

  if (isLoadingBuildings) {
    return (
      <div className="absolute top-4 left-4 bg-slate-800 border border-slate-700 rounded-lg shadow-lg p-4">
        <div className="flex items-center gap-2 text-slate-300">
          <Building2 size={18} />
          <span>Loading buildings...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="absolute top-4 left-4 bg-slate-800 border border-red-700 rounded-lg shadow-lg p-4">
        <div className="flex items-center gap-2 text-red-400">
          <Building2 size={18} />
          <span>Error: {error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="absolute top-4 left-4 flex gap-2">
      {/* Building selector */}
      <div className="relative">
        <button
          onClick={() => setIsBuildingDropdownOpen(!isBuildingDropdownOpen)}
          className="bg-slate-800 border border-slate-700 rounded-lg shadow-lg px-4 py-2 flex items-center gap-2 hover:bg-slate-700 transition-colors"
        >
          <Building2 size={18} className="text-slate-300" />
          <span className="text-slate-200">
            {selectedBuilding?.name || "Select Building"}
          </span>
          <ChevronDown size={16} className="text-slate-400" />
        </button>

        {isBuildingDropdownOpen && (
          <div className="absolute top-full mt-2 w-64 bg-slate-800 border border-slate-700 rounded-lg shadow-lg overflow-hidden z-10">
            {buildings.map((building) => (
              <button
                key={building.path}
                onClick={() => handleBuildingSelect(building)}
                className="w-full px-4 py-3 text-left hover:bg-slate-700 transition-colors border-b border-slate-700 last:border-b-0"
              >
                <div className="text-slate-200 font-medium">{building.name}</div>
                <div className="text-slate-400 text-sm">
                  {building.floor_count} floor{building.floor_count !== 1 ? "s" : ""}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Floor selector */}
      {selectedBuilding && (
        <div className="relative">
          <button
            onClick={() => setIsFloorDropdownOpen(!isFloorDropdownOpen)}
            className="bg-slate-800 border border-slate-700 rounded-lg shadow-lg px-4 py-2 flex items-center gap-2 hover:bg-slate-700 transition-colors"
            disabled={isLoadingFloors}
          >
            <span className="text-slate-200">
              {selectedBuilding.floors.find((f) => f.id === selectedFloorId)?.name ||
                "Select Floor"}
            </span>
            <ChevronDown size={16} className="text-slate-400" />
          </button>

          {isFloorDropdownOpen && (
            <div className="absolute top-full mt-2 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-lg overflow-hidden z-10">
              {selectedBuilding.floors.map((floor) => (
                <button
                  key={floor.id}
                  onClick={() => handleFloorSelect(floor)}
                  className={`w-full px-4 py-3 text-left hover:bg-slate-700 transition-colors border-b border-slate-700 last:border-b-0 ${
                    floor.id === selectedFloorId ? "bg-slate-700" : ""
                  }`}
                >
                  <div className="text-slate-200 font-medium">{floor.name}</div>
                  <div className="text-slate-400 text-sm">
                    Level {floor.level} • {floor.rooms.length} room
                    {floor.rooms.length !== 1 ? "s" : ""}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
