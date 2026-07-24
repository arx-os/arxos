//! Capture page: **Create New** opens the device camera (getUserMedia).
//!
//! Primary path: live preview → capture frame(s) → agent `capture.from_camera`
//! → proposed room on Building hierarchy.
//! Secondary: file upload (LiDAR/IFC) and structure-only bedroom shortcut.
//!
//! Camera requires a secure context (HTTPS or localhost). See docs/create-new-camera.md.

use leptos::prelude::*;
use leptos::*;
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;
use wasm_bindgen_futures::spawn_local;
use web_sys::Event;

use crate::web::overlay::camera::CameraManager;

fn store_report_lines(lines: &[String]) {
    let joined = lines.join("\n");
    if let Some(window) = web_sys::window() {
        if let Ok(Some(storage)) = window.local_storage() {
            let _ = storage.set_item("arx_last_loss_report", &joined);
        }
    }
}

fn read_data_url_base64(data_url: &str) -> Result<String, String> {
    let idx = data_url
        .find("base64,")
        .ok_or_else(|| "FileReader did not return base64 data URL".to_string())?;
    Ok(data_url[idx + "base64,".len()..].to_string())
}

#[component]
pub fn Capture() -> impl IntoView {
    let (status, set_status) = create_signal(String::from(
        "Connect agent, then Create New to open the camera.",
    ));
    let (busy, set_busy) = create_signal(false);
    let (camera_on, set_camera_on) = create_signal(false);
    let (burst, set_burst) = create_signal(false);
    let (room_name, set_room_name) = create_signal(String::new());
    let (report_lines, set_report_lines) = create_signal(Vec::<String>::new());
    let (produced, set_produced) = create_signal(Vec::<String>::new());
    let (file_name, set_file_name) = create_signal(String::new());
    let (meta, set_meta) = create_signal(String::new());
    let (last_room, set_last_room) = create_signal(String::new());

    let push_report = move |lines: Vec<String>| {
        store_report_lines(&lines);
        set_report_lines.set(lines);
    };

    let open_camera = move |_| {
        set_busy.set(true);
        set_status.set("Requesting camera (facingMode: environment)…".into());
        set_produced.set(Vec::new());
        spawn_local(async move {
            match CameraManager::start_preview().await {
                Ok(()) => {
                    set_camera_on.set(true);
                    set_status.set(
                        "Camera live — frame the room, then Capture. Agent must be Online to save."
                            .into(),
                    );
                    set_busy.set(false);
                }
                Err(e) => {
                    set_camera_on.set(false);
                    set_status.set(format!("Camera failed: {}", e));
                    set_busy.set(false);
                }
            }
        });
    };

    let stop_camera = move |_| {
        CameraManager::stop_camera();
        set_camera_on.set(false);
        set_status.set("Camera stopped.".into());
    };

    let capture_and_send = move |_| {
        if !crate::web::ws_client::is_connected() {
            set_status.set("Agent offline — connect in header first.".into());
            return;
        }
        if !camera_on.get() {
            set_status.set("Open the camera first (Create New).".into());
            return;
        }
        set_busy.set(true);
        set_status.set("Capturing frame(s)…".into());
        set_produced.set(Vec::new());
        let use_burst = burst.get();
        let name = room_name.get();
        spawn_local(async move {
            let frames = if use_burst {
                CameraManager::capture_burst(3, 1280).await
            } else {
                CameraManager::capture_jpeg_base64(1280).map(|f| vec![f])
            };
            let frames = match frames {
                Ok(f) => f,
                Err(e) => {
                    set_status.set(format!("Capture failed: {}", e));
                    set_busy.set(false);
                    return;
                }
            };

            set_status.set(format!(
                "Sending {} frame(s) to agent (capture.from_camera)…",
                frames.len()
            ));

            let mut params = serde_json::json!({
                "frames": frames,
            });
            if !name.trim().is_empty() {
                params["room_name"] = serde_json::json!(name.trim());
            }

            match crate::web::ws_client::send_rpc("capture.from_camera", params).await {
                Ok(val) => {
                    let lines: Vec<String> = val
                        .get("report_summary")
                        .and_then(|a| a.as_array())
                        .map(|a| {
                            a.iter()
                                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                        .unwrap_or_default();
                    push_report(lines);

                    let prod: Vec<String> = val
                        .get("produced")
                        .and_then(|a| a.as_array())
                        .map(|a| {
                            a.iter()
                                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                        .unwrap_or_default();
                    set_produced.set(prod);

                    let rn = val
                        .get("room_name")
                        .and_then(|v| v.as_str())
                        .unwrap_or("?")
                        .to_string();
                    set_last_room.set(rn.clone());
                    set_meta.set(format!(
                        "Building: {} · room: {} · frames={} · rooms={}",
                        val.get("building_name")
                            .and_then(|v| v.as_str())
                            .unwrap_or("?"),
                        rn,
                        val.get("frame_count").and_then(|v| v.as_u64()).unwrap_or(0),
                        val.get("rooms").and_then(|v| v.as_u64()).unwrap_or(0),
                    ));
                    set_status.set(format!(
                        "Created proposed room \"{}\". Open Review hierarchy or Label next.",
                        rn
                    ));
                    set_busy.set(false);
                }
                Err(e) => {
                    set_status.set(format!("capture.from_camera failed: {}", e));
                    set_busy.set(false);
                }
            }
        });
    };

    let ensure_bedroom = move |_| {
        if !crate::web::ws_client::is_connected() {
            set_status.set("Agent offline — connect in header first.".into());
            return;
        }
        set_busy.set(true);
        set_status.set("Creating Bedroom room via edit.apply…".into());
        spawn_local(async move {
            let script = r#"
add room Bedroom floor="Ground Floor" type=bedroom
"#;
            match crate::web::ws_client::send_rpc(
                "edit.apply",
                serde_json::json!({ "script": script }),
            )
            .await
            {
                Ok(val) => {
                    let lines: Vec<String> = val
                        .get("report_summary")
                        .and_then(|a| a.as_array())
                        .map(|a| {
                            a.iter()
                                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                        .unwrap_or_default();
                    push_report(lines);
                    let rooms = val.get("rooms").and_then(|v| v.as_u64()).unwrap_or(0);
                    set_meta.set(format!(
                        "Building: {} · rooms={}",
                        val.get("building_name")
                            .and_then(|v| v.as_str())
                            .unwrap_or("?"),
                        rooms
                    ));
                    set_last_room.set("Bedroom".into());
                    set_status.set(
                        "Bedroom room ensured (or already existed). Next: Label ceiling fan + light switch."
                            .into(),
                    );
                    set_busy.set(false);
                }
                Err(e) => {
                    let msg = e.to_string();
                    if msg.contains("already exists") {
                        set_status.set("Bedroom already exists — proceed to Label.".into());
                        set_last_room.set("Bedroom".into());
                    } else {
                        set_status.set(format!("edit.apply failed: {}", msg));
                    }
                    set_busy.set(false);
                }
            }
        });
    };

    let on_file_change = move |ev: Event| {
        if !crate::web::ws_client::is_connected() {
            set_status.set("Agent offline — connect in header first.".into());
            return;
        }
        let input = match ev
            .target()
            .and_then(|t| t.dyn_into::<web_sys::HtmlInputElement>().ok())
        {
            Some(i) => i,
            None => return,
        };
        let files = match input.files() {
            Some(f) if f.length() > 0 => f,
            _ => return,
        };
        let file = match files.get(0) {
            Some(f) => f,
            None => return,
        };
        let name = file.name();
        set_file_name.set(name.clone());
        set_busy.set(true);
        set_status.set(format!("Reading {}…", name));
        set_report_lines.set(Vec::new());

        let reader = web_sys::FileReader::new().unwrap();
        let reader_c = reader.clone();
        let name_c = name.clone();

        let onload = Closure::wrap(Box::new(move |_e: Event| {
            let data_url = match reader_c.result().ok().and_then(|r| r.as_string()) {
                Some(s) => s,
                None => {
                    set_status.set("Failed to read file as data URL".into());
                    set_busy.set(false);
                    return;
                }
            };
            let b64 = match read_data_url_base64(&data_url) {
                Ok(b) => b,
                Err(e) => {
                    set_status.set(e);
                    set_busy.set(false);
                    return;
                }
            };

            let fname = name_c.clone();
            let lower = fname.to_ascii_lowercase();
            let is_ifc = lower.ends_with(".ifc");
            let method = if is_ifc {
                "ifc.import".to_string()
            } else {
                "lidar.import".to_string()
            };
            set_status.set(format!("Uploading to agent ({})…", method));

            spawn_local(async move {
                let params = if is_ifc {
                    serde_json::json!({
                        "filename": fname,
                        "data": b64,
                    })
                } else {
                    serde_json::json!({
                        "filename": fname,
                        "data": b64,
                        "merge": true,
                        "light_mode": true,
                        "voxel_size": 0.05,
                    })
                };

                match crate::web::ws_client::send_rpc(&method, params).await {
                    Ok(val) => {
                        let lines: Vec<String> = val
                            .get("report_summary")
                            .and_then(|a| a.as_array())
                            .map(|a| {
                                a.iter()
                                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                                    .collect()
                            })
                            .unwrap_or_default();
                        let n = lines.len();
                        push_report(lines);
                        let floors = val.get("floors").and_then(|v| v.as_u64()).unwrap_or(0);
                        let rooms = val.get("rooms").and_then(|v| v.as_u64()).unwrap_or(0);
                        let equip = val.get("equipment").and_then(|v| v.as_u64()).unwrap_or(0);
                        set_meta.set(format!(
                            "{} · {} floors · {} rooms · {} equip",
                            val.get("building_name")
                                .and_then(|v| v.as_str())
                                .unwrap_or("?"),
                            floors,
                            rooms,
                            equip
                        ));
                        set_status.set(format!(
                            "Import OK via {} — read LossReport below ({} lines). Then Label.",
                            method, n
                        ));
                        set_busy.set(false);
                    }
                    Err(e) => {
                        set_status.set(format!("{} failed: {}", method, e));
                        set_busy.set(false);
                    }
                }
            });
        }) as Box<dyn FnMut(_)>);

        reader.set_onload(Some(onload.as_ref().unchecked_ref()));
        let _ = reader.read_as_data_url(&file);
        onload.forget();
    };

    // Cleanup camera when leaving is best-effort on stop button; no unmount hook required for pilot.

    view! {
        <div class="page capture-page" style="padding-bottom: 24px;">
            <h1 style="font-size: 1.35rem; margin: 0 0 6px;">"Create New"</h1>
            <p style="color: #64748b; font-size: 14px; margin: 0 0 12px;">
                "Primary: open the "
                <strong>"device camera"</strong>
                ", capture the room, send frames to the laptop agent → proposed room in hierarchy. "
                "No ARKit/RoomPlan in pure browser — JPEG frames + placeholder room only."
            </p>

            <div style=move || {
                let online = crate::web::ws_client::is_connected();
                if online {
                    "border-radius: 12px; padding: 12px 14px; margin-bottom: 12px; background: #dcfce7; color: #166534; font-size: 14px;".to_string()
                } else {
                    "border-radius: 12px; padding: 12px 14px; margin-bottom: 12px; background: #fee2e2; color: #991b1b; font-size: 14px;".to_string()
                }
            }>
                {move || {
                    if crate::web::ws_client::is_connected() {
                        format!("● Online → {}", crate::web::ws_client::current_agent_host())
                    } else {
                        "● Offline — connect in header first".into()
                    }
                }}
            </div>

            <p style="font-size: 13px; color: #475569; margin: 0 0 12px; word-break: break-word;">
                {move || status.get()}
            </p>
            {move || {
                let m = meta.get();
                if m.is_empty() {
                    view! { <></> }.into_any()
                } else {
                    view! {
                        <p style="font-size: 13px; font-weight: 600; color: #0f172a; margin: 0 0 12px;">{m}</p>
                    }.into_any()
                }
            }}

            // —— 1. Camera Create New (primary) ——
            <section style="margin-bottom: 16px; padding: 14px; border-radius: 12px; border: 2px solid #2563eb; background: #eff6ff;">
                <h2 style="font-size: 1.05rem; margin: 0 0 8px; color: #1e3a8a;">"1. Create New (camera)"</h2>
                <p style="font-size: 13px; color: #1e40af; margin: 0 0 10px;">
                    "getUserMedia · facingMode environment preferred · secure context required (HTTPS or localhost)."
                </p>

                <label style="display: block; font-size: 13px; color: #334155; margin-bottom: 10px;">
                    "Room name (optional — default Room-YYYYMMDD-HHMMSS)"
                    <input
                        type="text"
                        placeholder="e.g. Living Room"
                        prop:value=room_name
                        on:input=move |ev| set_room_name.set(event_target_value(&ev))
                        prop:disabled=move || busy.get()
                        style="display: block; width: 100%; box-sizing: border-box; margin-top: 4px; min-height: 44px; padding: 10px 12px; border: 1px solid #93c5fd; border-radius: 8px; font-size: 16px;"
                    />
                </label>

                <label style="display: flex; align-items: center; gap: 8px; font-size: 14px; color: #334155; margin-bottom: 12px; min-height: 44px;">
                    <input
                        type="checkbox"
                        prop:checked=burst
                        on:change=move |ev| {
                            let t = ev.target().and_then(|t| t.dyn_into::<web_sys::HtmlInputElement>().ok());
                            if let Some(el) = t {
                                set_burst.set(el.checked());
                            }
                        }
                    />
                    "Burst: 3 frames (~180ms apart)"
                </label>

                <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px;">
                    <button
                        type="button"
                        on:click=open_camera
                        prop:disabled=move || busy.get()
                        style="min-height: 52px; width: 100%; border: none; border-radius: 10px; background: #2563eb; color: white; font-size: 17px; font-weight: 700; cursor: pointer;"
                    >
                        {move || {
                            if busy.get() && !camera_on.get() {
                                "Opening camera…"
                            } else if camera_on.get() {
                                "Re-open camera"
                            } else {
                                "Create New — Open camera"
                            }
                        }}
                    </button>
                    {move || {
                        if camera_on.get() {
                            view! {
                                <div style="display: flex; flex-direction: column; gap: 8px;">
                                    <button
                                        type="button"
                                        on:click=capture_and_send
                                        prop:disabled=move || busy.get()
                                        style="min-height: 52px; width: 100%; border: none; border-radius: 10px; background: #0f172a; color: #f8fafc; font-size: 17px; font-weight: 700; cursor: pointer;"
                                    >
                                        {move || if busy.get() { "Working…" } else { "Capture & send to agent" }}
                                    </button>
                                    <button
                                        type="button"
                                        on:click=stop_camera
                                        prop:disabled=move || busy.get()
                                        style="min-height: 44px; width: 100%; border: 1px solid #94a3b8; border-radius: 10px; background: #fff; color: #334155; font-size: 15px; font-weight: 600; cursor: pointer;"
                                    >
                                        "Stop camera"
                                    </button>
                                </div>
                            }.into_any()
                        } else {
                            view! { <></> }.into_any()
                        }
                    }}
                </div>

                <div style="position: relative; background: #0f172a; border-radius: 12px; overflow: hidden; min-height: 200px;">
                    <video
                        id="arx-create-new-video"
                        autoplay
                        muted
                        playsinline
                        style="display: block; width: 100%; max-height: 70vh; object-fit: contain; background: #000;"
                    ></video>
                    <canvas
                        id="arx-create-new-canvas"
                        style="display: none;"
                        width="1"
                        height="1"
                    ></canvas>
                    {move || {
                        if !camera_on.get() {
                            view! {
                                <p style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 14px; margin: 0; padding: 16px; text-align: center; pointer-events: none;">
                                    "Camera preview appears here after Open camera"
                                </p>
                            }.into_any()
                        } else {
                            view! { <></> }.into_any()
                        }
                    }}
                </div>
            </section>

            {move || {
                let p = produced.get();
                if p.is_empty() {
                    view! { <></> }.into_any()
                } else {
                    view! {
                        <section style="margin-bottom: 16px; padding: 14px; border-radius: 12px; background: #f0fdf4; border: 1px solid #86efac;">
                            <h2 style="font-size: 0.95rem; margin: 0 0 8px; color: #14532d;">"What this capture produced"</h2>
                            <ul style="margin: 0; padding-left: 1.1rem; font-size: 13px; color: #166534;">
                                {p.into_iter().map(|l| view! { <li style="margin-bottom: 4px;">{l}</li> }).collect_view()}
                            </ul>
                        </section>
                    }.into_any()
                }
            }}

            // —— 2. Structure-only shortcut ——
            <section style="margin-bottom: 16px; padding: 14px; border-radius: 12px; border: 1px solid #e2e8f0; background: #fff;">
                <h2 style="font-size: 1rem; margin: 0 0 8px;">"2. Structure only (no camera)"</h2>
                <p style="font-size: 13px; color: #64748b; margin: 0 0 10px;">
                    "Ensures room Bedroom on Ground Floor (edit.apply → validate → building.yaml). Use when camera is unavailable."
                </p>
                <button
                    type="button"
                    on:click=ensure_bedroom
                    prop:disabled=move || busy.get()
                    style="min-height: 48px; width: 100%; border: none; border-radius: 10px; background: #64748b; color: white; font-size: 16px; font-weight: 600; cursor: pointer;"
                >
                    {move || if busy.get() { "Working…" } else { "Create / ensure Bedroom room" }}
                </button>
            </section>

            // —— 3. File capture (secondary) ——
            <section style="margin-bottom: 16px; padding: 14px; border-radius: 12px; border: 1px solid #e2e8f0; background: #fff;">
                <h2 style="font-size: 1rem; margin: 0 0 8px;">"3. File capture (secondary)"</h2>
                <p style="font-size: 13px; color: #64748b; margin: 0 0 10px;">
                    "Not the primary Create New path. Upload .ply / .las / .xyz / .csv (LiDAR) or .ifc — agent import spine + LossReport."
                </p>
                <label
                    for="capture-upload"
                    style="display: block; text-align: center; min-height: 48px; line-height: 48px; background: #334155; color: #f8fafc; border-radius: 10px; font-weight: 600; font-size: 16px; cursor: pointer;"
                >
                    {move || if busy.get() { "Uploading…" } else { "Choose scan or IFC file" }}
                </label>
                <input
                    type="file"
                    id="capture-upload"
                    accept=".ply,.las,.laz,.xyz,.csv,.ifc"
                    on:change=on_file_change
                    prop:disabled=move || busy.get()
                    style="display: none;"
                />
                {move || {
                    let n = file_name.get();
                    if n.is_empty() {
                        view! { <></> }.into_any()
                    } else {
                        view! {
                            <p style="font-size: 13px; color: #475569; margin: 8px 0 0;">"Selected: " {n}</p>
                        }.into_any()
                    }
                }}
            </section>

            <section style="padding: 14px; border-radius: 12px; background: #fffbeb; border: 1px solid #fcd34d;">
                <h2 style="font-size: 0.95rem; margin: 0 0 8px;">"LossReport / ingest summary"</h2>
                {move || {
                    let lines = report_lines.get();
                    if lines.is_empty() {
                        view! {
                            <p style="margin: 0; font-size: 13px; color: #78350f;">
                                "No report yet — Create New (camera) or structure/file to see honesty lines."
                            </p>
                        }.into_any()
                    } else {
                        view! {
                            <ul style="margin: 0; padding-left: 1.1rem; font-size: 12px; font-family: ui-monospace, monospace; color: #78350f;">
                                {lines.into_iter().map(|l| view! { <li style="margin-bottom: 4px;">{l}</li> }).collect_view()}
                            </ul>
                        }.into_any()
                    }
                }}
            </section>

            <p style="margin-top: 16px; font-size: 14px; display: flex; flex-wrap: wrap; gap: 12px;">
                <a href="/label" style="color: #2563eb; font-weight: 600;">"Next → Label objects"</a>
                <a href="/review" style="color: #166534; font-weight: 600;">
                    {move || {
                        let r = last_room.get();
                        if r.is_empty() {
                            "Open Review hierarchy".to_string()
                        } else {
                            format!("Review hierarchy (look for {})", r)
                        }
                    }}
                </a>
            </p>
        </div>
    }
}
