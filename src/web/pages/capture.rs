//! Capture page: agent-backed IFC / LiDAR file upload + LossReport panel.
//!
//! Pure WASM has no ARKit/RoomPlan access — capture is file picker → agent spine.
//! Also offers "Create Bedroom room" structure shortcut for the bedroom loop.

use leptos::prelude::*;
use leptos::*;
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;
use wasm_bindgen_futures::spawn_local;
use web_sys::Event;

fn store_report_lines(lines: &[String]) {
    let joined = lines.join("\n");
    if let Some(window) = web_sys::window() {
        if let Ok(Some(storage)) = window.local_storage() {
            let _ = storage.set_item("arx_last_loss_report", &joined);
        }
    }
}

fn read_data_url_base64(data_url: &str) -> Result<String, String> {
    // data:[<mediatype>][;base64],<data>
    let idx = data_url
        .find("base64,")
        .ok_or_else(|| "FileReader did not return base64 data URL".to_string())?;
    Ok(data_url[idx + "base64,".len()..].to_string())
}

#[component]
pub fn Capture() -> impl IntoView {
    let (status, set_status) = create_signal(String::from(
        "Connect agent, then upload a scan/IFC or create Bedroom structure.",
    ));
    let (busy, set_busy) = create_signal(false);
    let (report_lines, set_report_lines) = create_signal(Vec::<String>::new());
    let (file_name, set_file_name) = create_signal(String::new());
    let (meta, set_meta) = create_signal(String::new());

    let push_report = move |lines: Vec<String>| {
        store_report_lines(&lines);
        set_report_lines.set(lines);
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
                    set_status.set(
                        "Bedroom room ensured (or already existed). Next: Label ceiling fan + light switch."
                            .into(),
                    );
                    set_busy.set(false);
                }
                Err(e) => {
                    // Room may already exist — still ok for loop
                    let msg = e.to_string();
                    if msg.contains("already exists") {
                        set_status.set("Bedroom already exists — proceed to Label.".into());
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

    view! {
        <div class="page capture-page" style="padding-bottom: 24px;">
            <h1 style="font-size: 1.35rem; margin: 0 0 6px;">"Capture"</h1>
            <p style="color: #64748b; font-size: 14px; margin: 0 0 12px;">
                "Terminal-style capture: upload scan/IFC to the laptop agent (spine). "
                "iOS ARKit/RoomPlan not in this build — use Files app share or Create Bedroom."
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

            <section style="margin-bottom: 16px; padding: 14px; border-radius: 12px; border: 1px solid #e2e8f0; background: #fff;">
                <h2 style="font-size: 1rem; margin: 0 0 8px;">"1. Structure (bedroom)"</h2>
                <p style="font-size: 13px; color: #64748b; margin: 0 0 10px;">
                    "Ensures room Bedroom on Ground Floor (edit.apply → validate → building.yaml)."
                </p>
                <button
                    type="button"
                    on:click=ensure_bedroom
                    prop:disabled=move || busy.get()
                    style="min-height: 48px; width: 100%; border: none; border-radius: 10px; background: #2563eb; color: white; font-size: 16px; font-weight: 600; cursor: pointer;"
                >
                    {move || if busy.get() { "Working…" } else { "Create / ensure Bedroom room" }}
                </button>
            </section>

            <section style="margin-bottom: 16px; padding: 14px; border-radius: 12px; border: 1px solid #e2e8f0; background: #fff;">
                <h2 style="font-size: 1rem; margin: 0 0 8px;">"2. File capture (optional)"</h2>
                <p style="font-size: 13px; color: #64748b; margin: 0 0 10px;">
                    "Upload .ply / .las / .xyz / .csv (LiDAR) or .ifc — agent runs import spine + LossReport."
                </p>
                <label
                    for="capture-upload"
                    style="display: block; text-align: center; min-height: 48px; line-height: 48px; background: #0f172a; color: #f8fafc; border-radius: 10px; font-weight: 600; font-size: 16px; cursor: pointer;"
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
                                "No report yet — import or create structure to see honesty lines."
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

            <p style="margin-top: 16px; font-size: 14px;">
                <a href="/label" style="color: #2563eb; font-weight: 600;">"Next → Label objects"</a>
            </p>
        </div>
    }
}
