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
    let (heading, _set_heading) = signal(90.0f64); // raw compass reading
    let (smoothed_heading, set_smoothed_heading) = signal(90.0f64); // low-pass smoothed compass
    let (sensor_confidence, set_sensor_confidence) = signal(0.85f64); // sensor quality indicator

    // 2. Settings Configuration Signals
    let (smoothing_factor, set_smoothing_factor) = signal(0.80f64); // Alpha factor (higher = more smoothed)
    let (cluster_threshold, set_cluster_threshold) = signal(15.0f64); // X% horizontal collision window
    let (fov_degrees, set_fov_degrees) = signal(60.0f64); // Camera FOV
    let (max_labels, set_max_labels) = signal(20usize); // Max displayed labels limit
    let (settings_open, set_settings_open) = signal(false); // Settings panel open flag

    // 3. Raw/Smoothed Position Signals
    let (raw_pos, _set_raw_pos) = signal(Position {
        x: 0.0,
        y: 0.0,
        z: 0.0,
        coordinate_system: "local".to_string(),
    });
    let (smoothed_pos, set_smoothed_pos) = signal(Position {
        x: 0.0,
        y: 0.0,
        z: 0.0,
        coordinate_system: "local".to_string(),
    });

    // 4. Initial camera request
    Effect::new(move |_| {
        let camera = CameraManager::new();
        let _ = camera.request_camera_stream("ar-camera-feed");
    });

    // 5. Circular Compass Heading Smoothing (sine/cosine exponential low-pass filter)
    Effect::new(move |_| {
        let raw_deg = heading.get();
        let raw_rad = raw_deg.to_radians();
        let prev_deg = smoothed_heading.get();
        let prev_rad = prev_deg.to_radians();
        let alpha = smoothing_factor.get();

        // Decompose raw and prev into unit vectors, smooth sin and cos separately, and reconstruct
        let sin_smoothed = alpha * prev_rad.sin() + (1.0 - alpha) * raw_rad.sin();
        let cos_smoothed = alpha * prev_rad.cos() + (1.0 - alpha) * raw_rad.cos();
        let smoothed_rad = sin_smoothed.atan2(cos_smoothed);
        
        let mut smoothed_deg = smoothed_rad.to_degrees();
        if smoothed_deg < 0.0 {
            smoothed_deg += 360.0;
        }
        set_smoothed_heading.set(smoothed_deg);
    });

    // 6. Position Exponential Smoothing
    Effect::new(move |_| {
        let raw = raw_pos.get();
        let mut prev = smoothed_pos.get();
        let alpha = smoothing_factor.get();

        prev.x = alpha * prev.x + (1.0 - alpha) * raw.x;
        prev.y = alpha * prev.y + (1.0 - alpha) * raw.y;
        prev.z = alpha * prev.z + (1.0 - alpha) * raw.z;
        set_smoothed_pos.set(prev);
    });

    // 7. Throttled Proximity Label Query Loop (Runs every 300ms)
    Effect::new(move |_| {
        let mut warm_cache = WarmCache::new();
        let mut manager = DiscoveryManager::new();
        let warmer = PredictiveWarming;

        let current_pos = smoothed_pos.get();

        // Populate multiple mock anchors to demonstrate stacking & clustering behavior
        let floor_addr = crate::core::domain::ArxAddress::from_path("/building/hq/floor-1").unwrap();
        
        // Anchor 1: Base Anchor (Main Distribution Panel)
        let mut anchor1 = crate::core::Anchor::new(
            "Main Distribution Panel".to_string(),
            Position { x: 2.0, y: 0.5, z: 0.2, coordinate_system: "local".to_string() },
            0.75,
        );
        anchor1.properties.insert("circuit_id".to_string(), "MDP-A1".to_string());
        anchor1.address = Some(floor_addr.clone());

        // Anchor 2: Directly overlapping horizontally and vertically (SP-B1)
        let mut anchor2 = crate::core::Anchor::new(
            "Sub Panel B".to_string(),
            Position { x: 2.1, y: 0.52, z: 0.0, coordinate_system: "local".to_string() },
            0.80,
        );
        anchor2.properties.insert("circuit_id".to_string(), "SP-B1".to_string());
        anchor2.address = Some(floor_addr.clone());

        // Anchor 3: Creating a stacking collision cascade (ATS-01)
        let mut anchor3 = crate::core::Anchor::new(
            "Transfer Switch".to_string(),
            Position { x: 1.95, y: 0.48, z: -0.2, coordinate_system: "local".to_string() },
            0.85,
        );
        anchor3.properties.insert("circuit_id".to_string(), "ATS-01".to_string());
        anchor3.address = Some(floor_addr.clone());

        let envelope = crate::web::cache::warm::BuildingSyncEnvelope {
            base_address: floor_addr.clone(),
            anchors: vec![anchor1, anchor2, anchor3],
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

        // Read active anchors, project coordinates with new collision & parameter configurations
        let visible = manager.get_visible_anchors(&warm_cache);
        let projected = LabelProjector::project_labels(
            &visible,
            &current_pos,
            smoothed_heading.get(),
            Some(fov_degrees.get()),
            Some(cluster_threshold.get()),
            Some(max_labels.get()),
        );
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
            <style>
                "
                @keyframes fadeInTag {
                    from { opacity: 0; transform: translate(-50%, -40%); }
                    to { opacity: 1; transform: translate(-50%, -50%); }
                }
                .ar-text-tag {
                    animation: fadeInTag 0.25s ease-out;
                }
                "
            </style>

            // Live Video Feed from Camera
            <video
                id="ar-camera-feed"
                autoplay=true
                playsinline=true
                style="width: 100%; height: 100%; object-fit: cover; pointer-events: none;"
            ></video>

            // Configuration settings button
            <button
                on:click=move |_| set_settings_open.update(|v| *v = !*v)
                style="position: absolute; top: 16px; right: 140px; background: rgba(18, 18, 18, 0.85); color: #fff; border: 1px solid #475569; padding: 6px 12px; border-radius: 4px; font-size: 11px; z-index: 10; cursor: pointer; font-weight: bold;"
            >
                "⚙️ Settings"
            </button>

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

            // Configurable Settings slide-out Drawer
            <div
                class="settings-drawer"
                style=move || format!(
                    "position: absolute; top: 0; right: 0; width: 280px; height: 100%; background: rgba(15, 23, 42, 0.95); border-left: 1px solid #334155; padding: 20px; color: #f8fafc; font-family: sans-serif; transition: transform 0.3s ease-in-out; transform: {}; z-index: 100; box-shadow: -4px 0 20px rgba(0,0,0,0.5);",
                    if settings_open.get() { "translateX(0)" } else { "translateX(100%)" }
                )
            >
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 10px; margin-bottom: 20px;">
                    <h3 style="margin: 0; font-size: 14px; font-weight: 600;">"AR HUD Settings"</h3>
                    <button
                        on:click=move |_| set_settings_open.set(false)
                        style="background: transparent; border: none; color: #94a3b8; font-size: 16px; cursor: pointer; font-weight: bold; width: 24px; height: 24px;"
                    >
                        "✕"
                    </button>
                </div>

                // FOV Slider
                <div style="margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 6px; color: #94a3b8;">
                        <span>"Field of View"</span>
                        <span style="color: #3b82f6; font-weight: bold;">{move || format!("{:.0}°", fov_degrees.get())}</span>
                    </div>
                    <input
                        type="range"
                        min="30"
                        max="120"
                        value=move || fov_degrees.get().to_string()
                        on:input=move |ev| {
                            let el: web_sys::HtmlInputElement = event_target(&ev);
                            if let Ok(v) = el.value().parse::<f64>() {
                                set_fov_degrees.set(v);
                            }
                        }
                        style="width: 100%; cursor: pointer;"
                    />
                </div>

                // Smoothing Slider
                <div style="margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 6px; color: #94a3b8;">
                        <span>"Smoothing Factor (Alpha)"</span>
                        <span style="color: #3b82f6; font-weight: bold;">{move || format!("{:.2}", smoothing_factor.get())}</span>
                    </div>
                    <input
                        type="range"
                        min="0.0"
                        max="0.99"
                        step="0.01"
                        value=move || smoothing_factor.get().to_string()
                        on:input=move |ev| {
                            let el: web_sys::HtmlInputElement = event_target(&ev);
                            if let Ok(v) = el.value().parse::<f64>() {
                                set_smoothing_factor.set(v);
                            }
                        }
                        style="width: 100%; cursor: pointer;"
                    />
                </div>

                // Stacking / Cluster Threshold Slider
                <div style="margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 6px; color: #94a3b8;">
                        <span>"Stack Threshold (X%)"</span>
                        <span style="color: #3b82f6; font-weight: bold;">{move || format!("{:.0}%", cluster_threshold.get())}</span>
                    </div>
                    <input
                        type="range"
                        min="5"
                        max="35"
                        value=move || cluster_threshold.get().to_string()
                        on:input=move |ev| {
                            let el: web_sys::HtmlInputElement = event_target(&ev);
                            if let Ok(v) = el.value().parse::<f64>() {
                                set_cluster_threshold.set(v);
                            }
                        }
                        style="width: 100%; cursor: pointer;"
                    />
                </div>

                // Max Labels Slider
                <div style="margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 6px; color: #94a3b8;">
                        <span>"Max Labels Limit"</span>
                        <span style="color: #3b82f6; font-weight: bold;">{move || max_labels.get().to_string()}</span>
                    </div>
                    <input
                        type="range"
                        min="5"
                        max="50"
                        value=move || max_labels.get().to_string()
                        on:input=move |ev| {
                            let el: web_sys::HtmlInputElement = event_target(&ev);
                            if let Ok(v) = el.value().parse::<usize>() {
                                set_max_labels.set(v);
                            }
                        }
                        style="width: 100%; cursor: pointer;"
                    />
                </div>

                <div style="font-size: 10px; color: #64748b; line-height: 1.4; margin-top: 30px; border-top: 1px solid #334155; padding-top: 15px;">
                    "Adjust sliders to tune camera heading smoothing, FOV limits, or vertical collision stacking on site."
                </div>
            </div>

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
                    
                    let cluster_badge = if label.cluster_count > 0 {
                        view! {
                            <span style="background: #3b82f6; color: #fff; font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 999px; margin-left: 6px; white-space: nowrap;">
                                {format!("+{}", label.cluster_count)}
                            </span>
                        }.into_any()
                    } else {
                        view! { <></> }.into_any()
                    };

                    view! {
                        <div
                            class="ar-text-tag"
                            style=format!(
                                "position: absolute; left: {}%; top: {}%; transform: translate(-50%, -50%); background: rgba(18, 18, 18, 0.85); color: #fff; padding: 12px 16px; border-radius: 8px; border: 1px solid {}; font-family: sans-serif; pointer-events: auto; min-width: 200px; max-width: 250px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); transition: left 0.25s ease-out, top 0.25s ease-out, opacity 0.3s ease-in;",
                                label.x_percent,
                                label.y_percent,
                                if label.is_provisional { "#ff9800" } else { "#4caf50" }
                            )
                        >
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                                <span style="font-size: 14px; font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 150px;">{label.title}</span>
                                {cluster_badge}
                            </div>
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
