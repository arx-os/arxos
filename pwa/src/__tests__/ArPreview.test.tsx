import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import ArPreview from "../components/ArPreview";

type MockSession = {
  addEventListener: ReturnType<typeof vi.fn>;
  end: ReturnType<typeof vi.fn>;
};

describe("ArPreview", () => {
  const originalXR = (navigator as Navigator & { xr?: XRSystem }).xr;
  let mockSession: MockSession;

  beforeAll(() => {
    Object.defineProperty(navigator, "xr", {
      configurable: true,
      value: undefined
    });
  });

  beforeEach(() => {
    mockSession = {
      addEventListener: vi.fn(),
      end: vi.fn().mockResolvedValue(undefined)
    };
  });

  afterAll(() => {
    Object.defineProperty(navigator, "xr", {
      configurable: true,
      value: originalXR
    });
  });

  it("shows unsupported state when WebXR is not available", async () => {
    render(<ArPreview />);

    await waitFor(() => {
      expect(screen.getByText("Unsupported")).toBeInTheDocument();
    });
  });

  it("starts a session and loads demo overlay when WebXR is supported", async () => {
    Object.defineProperty(navigator, "xr", {
      configurable: true,
      value: {
        isSessionSupported: vi.fn().mockResolvedValue(true),
        requestSession: vi.fn().mockResolvedValue(mockSession)
      }
    });

    vi.spyOn(window, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ anchors: [], metadata: "demo" })
    } as Response);

    render(<ArPreview />);

    await waitFor(() => {
      expect(screen.getByText("WebXR Ready")).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /load demo overlay/i }));
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /start ar session/i }));
    });

    const xr = (navigator as Navigator & { xr?: XRSystem }).xr;
    expect(xr?.requestSession).toHaveBeenCalledWith("immersive-ar", {
      requiredFeatures: [],
      optionalFeatures: ["dom-overlay"],
      domOverlay: { root: document.body }
    });
    expect(mockSession.addEventListener).toHaveBeenCalledWith("end", expect.any(Function), {
      once: true
    });

    vi.mocked(window.fetch).mockRestore();
  });
});
