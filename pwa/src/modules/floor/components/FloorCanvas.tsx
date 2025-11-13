import { useEffect, useRef } from "react";
import type { Floor, Selection } from "../types";
import { Renderer } from "../renderer/Renderer";

interface FloorCanvasProps {
  floor: Floor | null;
  selection: Selection | null;
  onSelectionChange: (selection: Selection | null) => void;
  className?: string;
}

export function FloorCanvas({
  floor,
  selection,
  onSelectionChange,
  className = "",
}: FloorCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rendererRef = useRef<Renderer | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize renderer
  useEffect(() => {
    if (!canvasRef.current) return;

    const renderer = new Renderer(canvasRef.current);
    rendererRef.current = renderer;

    // Set initial size
    const updateSize = () => {
      if (!containerRef.current || !canvasRef.current) return;

      const { width, height } = containerRef.current.getBoundingClientRect();
      renderer.resize(width, height);
    };

    updateSize();

    // Handle window resize
    const resizeObserver = new ResizeObserver(updateSize);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      resizeObserver.disconnect();
      renderer.destroy();
      rendererRef.current = null;
    };
  }, []);

  // Update floor data
  useEffect(() => {
    if (rendererRef.current && floor) {
      rendererRef.current.setFloor(floor);
    }
  }, [floor]);

  // Update selection
  useEffect(() => {
    if (rendererRef.current) {
      rendererRef.current.setSelection(selection);
    }
  }, [selection]);

  // Handle mouse events
  useEffect(() => {
    if (!canvasRef.current || !rendererRef.current) return;

    const canvas = canvasRef.current;
    const renderer = rendererRef.current;
    const camera = renderer.getCamera();

    let isDragging = false;
    let dragButton = -1;

    const handleMouseDown = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      if (e.button === 0) {
        // Left click - select element
        const element = renderer.findElementAtPoint(x, y);
        onSelectionChange(element);
      } else if (e.button === 2 || e.button === 1) {
        // Right click or middle click - start drag
        isDragging = true;
        dragButton = e.button;
        camera.startDrag(x, y);
        e.preventDefault();
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      if (isDragging) {
        camera.drag(x, y);
        renderer.render();
      } else {
        // Update hover state
        const element = renderer.findElementAtPoint(x, y);
        renderer.setHoveredElement(element);
      }
    };

    const handleMouseUp = (e: MouseEvent) => {
      if (isDragging && e.button === dragButton) {
        camera.endDrag();
        isDragging = false;
        dragButton = -1;
      }
    };

    const handleMouseLeave = () => {
      if (isDragging) {
        camera.endDrag();
        isDragging = false;
        dragButton = -1;
      }
      renderer.setHoveredElement(null);
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();

      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Zoom delta based on wheel direction
      const delta = e.deltaY > 0 ? -0.1 : 0.1;
      camera.zoom(delta, x - canvas.width / 2, y - canvas.height / 2);
      renderer.render();
    };

    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault();
    };

    canvas.addEventListener("mousedown", handleMouseDown);
    canvas.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener("mouseup", handleMouseUp);
    canvas.addEventListener("mouseleave", handleMouseLeave);
    canvas.addEventListener("wheel", handleWheel, { passive: false });
    canvas.addEventListener("contextmenu", handleContextMenu);

    return () => {
      canvas.removeEventListener("mousedown", handleMouseDown);
      canvas.removeEventListener("mousemove", handleMouseMove);
      canvas.removeEventListener("mouseup", handleMouseUp);
      canvas.removeEventListener("mouseleave", handleMouseLeave);
      canvas.removeEventListener("wheel", handleWheel);
      canvas.removeEventListener("contextmenu", handleContextMenu);
    };
  }, [onSelectionChange]);

  return (
    <div ref={containerRef} className={`relative w-full h-full ${className}`}>
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-crosshair"
        style={{ display: "block" }}
      />
    </div>
  );
}
