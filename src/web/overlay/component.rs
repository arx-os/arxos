//! Leptos component rendering camera background and HTML label overlays.

use leptos::prelude::*;
use crate::core::Position;
use crate::web::cache::{WarmCache, SyncQueue};
use crate::web::discovery::DiscoveryManager;
use crate::web::cache::warming::PredictiveWarming;
use super::camera::CameraManager;
use super::label::{LabelProjector, ScreenLabel};

#[component]
pub fn ArOverlayScreen() -> impl IntoView {
    // 1. Core State Signals
    let (labels, set_labels) = signal(Vec::<ScreenLabel>::new());
    let (provisional_mode, set_provisional_mode) = signal(true);
    let (heading, set_heading) = signal(90.0f64); // raw compass reading
    let (smoothed_heading, set_smoothed_heading) = signal(90.0f64); // low-pass smoothed compass
    let (sensor_confidence, set_sensor_confidence) = signal(0.85f64); // sensor quality indicator

    // 2. Initial camera request
    Effect::new(move |_| {
        let camera = CameraManager::new();
        let _ = camera.request_camera_stream("ar-camera-feed");
    });

    // 3. Compass heading smoothing (low-pass filter effect)
    Effect::new(move |_| {
        let raw = heading.get();
        let prev = smoothed_heading.get();
        // Simple low-pass filter: 80% previous + 20% raw input
        let smoothed = 0.8 * prev + 0.2 * raw;
        set_smoothed_heading.set(smoothed);
    });

    // 4. Throttled Proximity Label Query Loop (Runs every 300ms)
    Effect::new(move |_| {
        let mut warm_cache = WarmCache::new();
        let mut manager = DiscoveryManager::new();
        let warmer = PredictiveWarming;

        // Mock current position
        let current_pos = Position {
            x: 0.0,
            y: 0.0,
            z: 0.0,
            coordinate_system: "local".to_string(),
        };

        // Populate mock subtree in warm cache
        let floor_addr = crate::core::domain::ArxAddress::from_path("/building/hq/floor-1").unwrap();
        let mut anchor1 = crate::core::Anchor::new(
            "Main Distribution Panel".to_string(),
            Position { x: 2.0, y: 0.5, z: 0.2, coordinate_system: "local".to_string() },
            0.75, // low saturation/confidence
        );
        anchor1.properties.insert("circuit_id".to_string(), "MDP-A1".to_string());
        anchor1.address = Some(floor_addr.clone());

        let envelope = crate::web::cache::warm::BuildingSyncEnvelope {
            base_address: floor_addr.clone(),
            anchors: vec![anchor1],
            payload: "mock metadata".to_string(),
            fetched_at_timestamp: 1000,
        };
        warm_cache.insert_subtree(envelope);

        // Update position inside manager
        let loc_ctx = crate::web::discovery::LocationContext {
            current_address: floor_addr,
            coordinates: crate::core::spatial::Point3D::new(0.0, 0.0, 0.0),
            confidence: sensor_confidence.get(),
        };
        manager.update_position(loc_ctx, &mut warm_cache, &warmer);

        set_provisional_mode.set(manager.is_provisional());

        // Read active anchors, project coordinates using the average camera FOV profile (e.g. 60 deg)
        let visible = manager.get_visible_anchors(&warm_cache);
        let projected = LabelProjector::project_labels(&visible, &current_pos, smoothed_heading.get(), Some(60.0));
        set_labels.set(projected);
    });

    // Trigger action handler (recalibrate anchor)
    let on_recalibrate_click = move |anchor_id: String| {
        let mut sync_queue = SyncQueue::new();
        crate::web::discovery::TaskResolver::recalibrate_anchor(
            &anchor_id,
            Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "local".to_string() },
            0.98, // updated high confidence calibration
            &mut sync_queue,
        );
        let _ = sync_queue.sync_with_agent();
    };

    view! {
        <div class="ar-overlay-container" style="position: relative; width: 100vw; height: 100vh; overflow: hidden; background: #000;">
            // Live Video Feed from Camera
            <video
                id="ar-camera-feed"
                autoplay=true
                playsinline=true
                style="width: 100%; height: 100%; object-fit: cover; pointer-events: none;"
            ></video>

            // Toggle simulation button to demonstrate sensor quality degradation
            <button
                on:click=move |_| {
                    if sensor_confidence.get() > 0.5 {
                        set_sensor_confidence.set(0.30);
                    } else {
                        set_sensor_confidence.set(0.85);
                    }
                }
                style="position: absolute; top: 16px; right: 16px; background: rgba(0,0,0,0.6); color: #fff; border: 1px solid #fff; padding: 6px 12px; border-radius: 4px; font-size: 11px; z-index: 10; cursor: pointer;"
            >
                {move || format!("Simulate Sensors ({})", if sensor_confidence.get() < 0.5 { "Poor" } else { "Good" })}
            </button>

            // Show active AR labels overlay only when sensor confidence is healthy (>= 0.5)
            <div
                class="labels-overlay-layer"
                style=format!(
                    "position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; display: {};",
                    if sensor_confidence.get() < 0.5 { "none" } else { "block" }
                )
            >
                {move || labels.get().into_iter().map(|label| {
                    let anchor_id = label.anchor.id.clone();
                    let click_handler = move |_| on_recalibrate_click(anchor_id.clone());
                    
                    view! {
                        <div
                            class="ar-text-tag"
                            style=format!(
                                "position: absolute; left: {}%; top: {}%; transform: translate(-50%, -50%); background: rgba(18, 18, 18, 0.85); color: #fff; padding: 12px 16px; border-radius: 8px; border: 1px solid {}; font-family: sans-serif; pointer-events: auto; max-width: 250px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);",
                                label.x_percent,
                                label.y_percent,
                                if label.is_provisional { "#ff9800" } else { "#4caf50" }
                            )
                        >
                            <div style="font-size: 14px; font-weight: bold; margin-bottom: 4px;">{label.title}</div>
                            <div style="font-size: 11px; color: #ccc; margin-bottom: 6px;">{label.subtitle}</div>
                            
                            <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                                <span style="font-size: 10px; color: #aaa;">{format!("{:.1}m away", label.distance_m)}</span>
                                <button
                                    on:click=click_handler
                                    style="background: #2196f3; color: #fff; border: none; padding: 4px 8px; border-radius: 4px; font-size: 10px; cursor: pointer; font-weight: bold;"
                                >
                                    "Recalibrate"
                                </button>
                            </div>
                        </div>
                    }
                }).collect::<Vec<_>>()}
            </div>

            // Fallback List View Card: rendered when sensor data is poor or unavailable (< 0.5)
            <div
                class="sensor-fallback-list"
                style=format!(
                    "position: absolute; top: 16px; left: 16px; max-width: 320px; background: rgba(18, 18, 18, 0.95); color: #fff; border-radius: 8px; border: 1px solid #f44336; padding: 16px; font-family: sans-serif; box-shadow: 0 4px 16px rgba(0,0,0,0.6); display: {};",
                    if sensor_confidence.get() < 0.5 { "block" } else { "none" }
                )
            >
                <div style="font-size: 13px; font-weight: bold; color: #f44336; margin-bottom: 4px;">
                    "⚠️ Sensor Precision Degraded"
                </div>
                <div style="font-size: 11px; color: #bbb; margin-bottom: 12px;">
                    "Camera overlays disabled. Displaying closest anchors in proximity list:"
                </div>
                <div style="max-height: 180px; overflow-y: auto;">
                    {move || labels.get().into_iter().map(|label| {
                        let anchor_id = label.anchor.id.clone();
                        let click_handler = move |_| on_recalibrate_click(anchor_id.clone());
                        view! {
                            <div style="padding: 8px 0; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                                <div>
                                    <div style="font-size: 12px; font-weight: bold;">{label.title}</div>
                                    <div style="font-size: 10px; color: #aaa;">{format!("{:.1}m away", label.distance_m)}</div>
                                </div>
                                <button
                                    on:click=click_handler
                                    style="background: #2196f3; color: #fff; border: none; padding: 4px 6px; border-radius: 4px; font-size: 9px; cursor: pointer;"
                                >
                                    "Calibrate"
                                </button>
                            </div>
                        }
                    }).collect::<Vec<_>>()}
                </div>
            </div>

            // Bottom control banner (indicates branch status: provisional vs main verified)
            <div
                class="ar-status-banner"
                style=format!(
                    "position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%); padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: bold; color: #fff; background: {}; pointer-events: none;",
                    if provisional_mode.get() { "rgba(255, 152, 0, 0.9)" } else { "rgba(76, 175, 80, 0.9)" }
                )
            >
                {move || if provisional_mode.get() {
                    "Stage Mode (/building) - Unverified Data"
                } else {
                    "Authoritative Mode (/main) - Property Owner Twin"
                }}
            </div>
        </div>
    }
}
