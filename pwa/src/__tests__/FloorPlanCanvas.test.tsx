import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import FloorPlanCanvas from "../components/FloorPlanCanvas";

vi.mock("../lib/wasm", () => {
  const mockScan = {
    detectedEquipment: [
      {
        name: "Unit-1",
        type: "HVAC",
        position: { x: 5, y: 3, z: 0 },
        confidence: 0.92
      }
    ],
    roomBoundaries: {
      walls: [
        { startPoint: { x: 0, y: 0, z: 0 }, endPoint: { x: 10, y: 0, z: 0 }, height: 3, thickness: 0.2 },
        { startPoint: { x: 10, y: 0, z: 0 }, endPoint: { x: 10, y: 8, z: 0 }, height: 3, thickness: 0.2 },
        { startPoint: { x: 10, y: 8, z: 0 }, endPoint: { x: 0, y: 8, z: 0 }, height: 3, thickness: 0.2 },
        { startPoint: { x: 0, y: 8, z: 0 }, endPoint: { x: 0, y: 0, z: 0 }, height: 3, thickness: 0.2 }
      ],
      openings: []
    }
  };

  return {
    initWasm: vi.fn().mockResolvedValue({}),
    validateArScan: vi.fn().mockResolvedValue(true),
    parseArScan: vi.fn().mockResolvedValue(mockScan),
    extractEquipmentFromScan: vi.fn().mockResolvedValue([
      {
        id: "unit-1",
        name: "Unit-1",
        equipmentType: "HVAC",
        status: "Unknown",
        position: { x: 5, y: 3, z: 0 },
        properties: {},
        addressPath: ""
      }
    ])
  };
});

describe("FloorPlanCanvas", () => {
  it("renders sample scan status", async () => {
    render(<FloorPlanCanvas />);

    await waitFor(() => {
      expect(screen.getByText(/Rendered 1 equipment points/)).toBeInTheDocument();
    });
  });
});
