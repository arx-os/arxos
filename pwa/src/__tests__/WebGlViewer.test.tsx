import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("three", () => {
  class Dummy {
    add() {}
    clear() {}
    position = {
      copy() {}
    };
    lookAt() {}
    set() {}
  }

  class Scene extends Dummy {
    background: unknown;
  }

  class PerspectiveCamera extends Dummy {
    aspect = 1;
    updateProjectionMatrix() {}
  }

  class WebGLRenderer {
    domElement = document.createElement("canvas");
    setPixelRatio() {}
    setSize() {}
    render() {}
    dispose() {}
  }

  class AmbientLight extends Dummy {}
  class DirectionalLight extends Dummy {
    position = {
      set() {},
      copy() {}
    };
  }
  class Group extends Dummy {}
  class BufferGeometry extends Dummy {
    setAttribute() {}
    dispose() {}
  }
  class BufferAttribute {}
  class LineBasicMaterial {}
  class LineSegments extends Dummy {}
  class PointsMaterial extends Dummy {}
  class Points extends Dummy {}
  class Vector3 {
    constructor(public x = 0, public y = 0, public z = 0) {}
  }

  class Color {
    constructor(public value: number) {
      this.value = value;
    }
  }

  return {
    Scene,
    PerspectiveCamera,
    WebGLRenderer,
    AmbientLight,
    DirectionalLight,
    Group,
    BufferGeometry,
    BufferAttribute,
    LineBasicMaterial,
    LineSegments,
    PointsMaterial,
    Points,
    Vector3,
    Color
  };
});

import WebGlViewer from "../components/WebGlViewer";
import { useViewerStore } from "../state/viewer";

beforeEach(() => {
  useViewerStore.getState().reset();
});

describe("WebGlViewer", () => {
  it("renders placeholder before mesh loads", () => {
    render(<WebGlViewer />);
    expect(screen.getByText(/3D Scan Viewer/i)).toBeInTheDocument();
  });

  it("renders canvas container when mesh is provided", () => {
    useViewerStore.setState({
      mesh: {
        wallPositions: new Float32Array([0, 0, 0, 1, 0, 0]),
        equipmentPositions: new Float32Array([0.5, 0, 0.5]),
        pointCloudPositions: new Float32Array([0.5, 0, 0.5]),
        boundsMin: [0, 0, 0],
        boundsMax: [1, 1, 1]
      }
    });
    render(<WebGlViewer />);
    expect(screen.getByText(/3D Scan Viewer/i)).toBeInTheDocument();
  });
});
