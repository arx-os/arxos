import { X, Box, Circle } from "lucide-react";
import type { Selection, Floor, Room, Equipment } from "../types";

interface SelectionPanelProps {
  selection: Selection;
  floor: Floor;
  onClose: () => void;
}

export function SelectionPanel({ selection, floor, onClose }: SelectionPanelProps) {
  const getSelectedElement = (): Room | Equipment | null => {
    if (selection.type === "room") {
      return floor.rooms.find((r) => r.id === selection.id) || null;
    } else if (selection.type === "equipment") {
      for (const room of floor.rooms) {
        const equipment = room.equipment.find((e) => e.id === selection.id);
        if (equipment) return equipment;
      }
    }
    return null;
  };

  const element = getSelectedElement();

  if (!element) return null;

  const isRoom = selection.type === "room";
  const room = isRoom ? (element as Room) : null;
  const equipment = !isRoom ? (element as Equipment) : null;

  return (
    <div className="absolute bottom-4 left-4 w-80 bg-slate-800 border border-slate-700 rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-700 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isRoom ? (
            <Box size={18} className="text-cyan-400" />
          ) : (
            <Circle size={18} className="text-cyan-400" />
          )}
          <h3 className="text-slate-200 font-medium">
            {isRoom ? "Room" : "Equipment"} Details
          </h3>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-200 transition-colors"
        >
          <X size={18} />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-3">
        {isRoom && room ? (
          <>
            <div>
              <label className="text-slate-400 text-sm">Name</label>
              <div className="text-slate-200 font-medium">{room.name}</div>
            </div>
            <div>
              <label className="text-slate-400 text-sm">Type</label>
              <div className="text-slate-200">{room.room_type}</div>
            </div>
            <div>
              <label className="text-slate-400 text-sm">Equipment Count</label>
              <div className="text-slate-200">{room.equipment.length}</div>
            </div>
            <div>
              <label className="text-slate-400 text-sm">Bounds</label>
              <div className="text-slate-200 text-sm font-mono">
                <div>
                  Min: ({room.bounds.min.x.toFixed(2)}, {room.bounds.min.y.toFixed(2)})
                </div>
                <div>
                  Max: ({room.bounds.max.x.toFixed(2)}, {room.bounds.max.y.toFixed(2)})
                </div>
              </div>
            </div>
            {room.polygon && room.polygon.length > 0 && (
              <div>
                <label className="text-slate-400 text-sm">Polygon Points</label>
                <div className="text-slate-200 text-sm">{room.polygon.length} vertices</div>
              </div>
            )}
          </>
        ) : equipment ? (
          <>
            <div>
              <label className="text-slate-400 text-sm">Name</label>
              <div className="text-slate-200 font-medium">{equipment.name}</div>
            </div>
            <div>
              <label className="text-slate-400 text-sm">Type</label>
              <div className="text-slate-200">{equipment.equipment_type}</div>
            </div>
            <div>
              <label className="text-slate-400 text-sm">Position</label>
              <div className="text-slate-200 text-sm font-mono">
                ({equipment.position.x.toFixed(2)}, {equipment.position.y.toFixed(2)}
                {equipment.position.z !== undefined && `, ${equipment.position.z.toFixed(2)}`})
              </div>
            </div>
            {equipment.properties && Object.keys(equipment.properties).length > 0 && (
              <div>
                <label className="text-slate-400 text-sm">Properties</label>
                <div className="mt-1 space-y-1">
                  {Object.entries(equipment.properties).map(([key, value]) => (
                    <div key={key} className="text-sm">
                      <span className="text-slate-400">{key}:</span>{" "}
                      <span className="text-slate-200">
                        {typeof value === "object"
                          ? JSON.stringify(value)
                          : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}
