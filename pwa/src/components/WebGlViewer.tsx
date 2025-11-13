import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { useViewerStore } from "../state/viewer";

const WALL_COLOR = 0x42a5f5;
const EQUIPMENT_COLOR = 0xffc107;
const POINT_CLOUD_COLOR = 0xffffff;

function computeCameraPosition(boundsMin: [number, number, number], boundsMax: [number, number, number]) {
  const center = new THREE.Vector3(
    (boundsMin[0] + boundsMax[0]) / 2,
    (boundsMin[1] + boundsMax[1]) / 2,
    (boundsMin[2] + boundsMax[2]) / 2
  );
  const spanX = boundsMax[0] - boundsMin[0];
  const spanY = boundsMax[1] - boundsMin[1];
  const spanZ = boundsMax[2] - boundsMin[2];
  const maxSpan = Math.max(spanX, spanY, spanZ, 1);
  const distance = maxSpan * 1.8;
  return { center, position: new THREE.Vector3(center.x + distance, center.y + distance, center.z + distance) };
}

type AutomationWindow = Window & { __ARXOS_DISABLE_WEBGL__?: boolean };

export default function WebGlViewer() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const { mesh, loading, error, clearError } = useViewerStore((state) => ({
    mesh: state.mesh,
    loading: state.loading,
    error: state.error,
    clearError: state.clearError
  }));
  const [context, setContext] = useState<{
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    renderer: THREE.WebGLRenderer;
    frameId?: number;
    group: THREE.Group;
  } | null>(null);
  const [initError, setInitError] = useState<string | null>(null);
  const disableFlag =
    typeof window !== "undefined" && (window as AutomationWindow).__ARXOS_DISABLE_WEBGL__ === true;
  const envDisabled = import.meta.env.VITE_DISABLE_WEBGL === "1";
  const skipRenderer =
    envDisabled ||
    disableFlag ||
    (typeof navigator !== "undefined" && (navigator.webdriver || /HeadlessChrome/i.test(navigator.userAgent)));

  useEffect(() => {
    if (skipRenderer || !containerRef.current || !canvasRef.current || context) {
      return;
    }

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f172a);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        canvas: canvasRef.current ?? undefined
      });
    } catch (initializationError) {
      console.warn("WebGL renderer initialization failed", initializationError);
      setInitError("WebGL renderer unavailable in this environment.");
      return;
    }

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);

    const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 2000);

    const ambient = new THREE.AmbientLight(0xffffff, 0.6);
    const directional = new THREE.DirectionalLight(0xffffff, 0.6);
    directional.position.set(10, 20, 10);
    scene.add(ambient, directional);

    const group = new THREE.Group();
    scene.add(group);

    const updateSize = () => {
      if (!containerRef.current) {
        return;
      }
      const { clientWidth, clientHeight } = containerRef.current;
      renderer.setSize(clientWidth, clientHeight);
      camera.aspect = clientWidth / Math.max(clientHeight, 1);
      camera.updateProjectionMatrix();
    };

    updateSize();
    window.addEventListener("resize", updateSize);

    let frameId = 0;
    const animate = () => {
      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    };

    animate();

    setContext({ scene, camera, renderer, group, frameId });

    return () => {
      window.removeEventListener("resize", updateSize);
      cancelAnimationFrame(frameId);
      renderer.dispose();
    };
  }, [context, skipRenderer]);

  useEffect(() => {
    if (skipRenderer || !context || !mesh) {
      return;
    }

    context.group.clear();

    const { center, position } = computeCameraPosition(mesh.boundsMin, mesh.boundsMax);
    context.camera.position.copy(position);
    context.camera.lookAt(center);

    if (mesh.wallPositions.length >= 6) {
      const wallGeometry = new THREE.BufferGeometry();
      wallGeometry.setAttribute("position", new THREE.BufferAttribute(mesh.wallPositions, 3));
      const wallMaterial = new THREE.LineBasicMaterial({ color: WALL_COLOR });
      const walls = new THREE.LineSegments(wallGeometry, wallMaterial);
      context.group.add(walls);
    }

    if (mesh.equipmentPositions.length >= 3) {
      const equipmentGeometry = new THREE.BufferGeometry();
      equipmentGeometry.setAttribute(
        "position",
        new THREE.BufferAttribute(mesh.equipmentPositions, 3)
      );
      const equipmentMaterial = new THREE.PointsMaterial({
        color: EQUIPMENT_COLOR,
        size: 0.2,
        sizeAttenuation: true
      });
      const points = new THREE.Points(equipmentGeometry, equipmentMaterial);
      context.group.add(points);
    }

    if (mesh.pointCloudPositions.length >= 3) {
      const cloudGeometry = new THREE.BufferGeometry();
      cloudGeometry.setAttribute(
        "position",
        new THREE.BufferAttribute(mesh.pointCloudPositions, 3)
      );
      const cloudMaterial = new THREE.PointsMaterial({
        color: POINT_CLOUD_COLOR,
        size: 0.08,
        opacity: 0.4,
        transparent: true,
        sizeAttenuation: true
      });
      const cloud = new THREE.Points(cloudGeometry, cloudMaterial);
      context.group.add(cloud);
    }
  }, [context, mesh, skipRenderer]);

  if (skipRenderer) {
    return (
      <section
        className="rounded-xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg shadow-slate-900/40"
        data-testid="panel-webgl"
      >
        <header className="mb-3 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-100">3D Scan Viewer</h2>
            <p className="text-xs text-slate-400">
              WebGL rendering is disabled in this environment. Mesh data is still available via WASM.
            </p>
          </div>
        </header>
        <div className="relative h-[360px] w-full overflow-hidden rounded-lg border border-slate-800 bg-slate-950">
          <div className="absolute inset-0 flex items-center justify-center text-xs text-slate-300">
            WebGL viewer disabled for automation.
          </div>
        </div>
      </section>
    );
  }

  return (
    <section
      className="rounded-xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg shadow-slate-900/40"
      data-testid="panel-webgl"
    >
      <header className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-100">3D Scan Viewer</h2>
          <p className="text-xs text-slate-400">
            Visualize room boundaries, equipment detections, and point-cloud overlays using WebGL.
          </p>
        </div>
        {error && (
          <button
            type="button"
            onClick={() => clearError()}
            className="rounded-md border border-slate-700 bg-red-500/20 px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-red-200"
          >
            Clear Error
          </button>
        )}
      </header>
      <div
        ref={containerRef}
        className="relative h-[360px] w-full overflow-hidden rounded-lg border border-slate-800 bg-slate-950"
      >
        <canvas ref={canvasRef} className="h-full w-full" />
        {!mesh && !loading && (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-slate-400">
            Awaiting AR scan data…
          </div>
        )}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-slate-300">
            Generating mesh buffers…
          </div>
        )}
        {initError && (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-amber-300">
            {initError}
          </div>
        )}
        {error && (
          <div className="absolute inset-x-0 bottom-2 mx-auto w-5/6 rounded-md border border-red-500/50 bg-red-900/30 px-3 py-2 text-[11px] text-red-200">
            {error}
          </div>
        )}
      </div>
    </section>
  );
}
