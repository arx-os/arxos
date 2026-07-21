//! Agent-backed Review: hierarchy, accept/reject, validate, approved IFC export.

use crate::core::review::{equipment_review_status, room_review_status, ReviewStatus};
use crate::core::Building;
use leptos::prelude::*;
use leptos::*;
use wasm_bindgen_futures::spawn_local;

#[derive(Clone, Debug)]
struct HierarchyRow {
    kind: &'static str,
    path: String,
    name: String,
    status: Option<ReviewStatus>,
}

fn status_label(s: Option<ReviewStatus>) -> (&'static str, &'static str, &'static str) {
    match s {
        Some(ReviewStatus::Proposed) => ("proposed", "#92400e", "#fef3c7"),
        Some(ReviewStatus::Accepted) => ("accepted", "#166534", "#dcfce7"),
        Some(ReviewStatus::Rejected) => ("rejected", "#374151", "#e5e7eb"),
        None => ("—", "#64748b", "#f1f5f9"),
    }
}

fn build_rows(building: &Building) -> Vec<HierarchyRow> {
    let mut rows = Vec::new();
    for floor in &building.floors {
        for eq in &floor.equipment {
            rows.push(HierarchyRow {
                kind: "equip",
                path: format!("{} / (floor)", floor.name),
                name: eq.name.clone(),
                status: equipment_review_status(eq),
            });
        }
        for wing in &floor.wings {
            for eq in &wing.equipment {
                rows.push(HierarchyRow {
                    kind: "equip",
                    path: format!("{} / {}", floor.name, wing.name),
                    name: eq.name.clone(),
                    status: equipment_review_status(eq),
                });
            }
            for room in &wing.rooms {
                rows.push(HierarchyRow {
                    kind: "room",
                    path: format!("{} / {}", floor.name, wing.name),
                    name: room.name.clone(),
                    status: room_review_status(room),
                });
                for eq in &room.equipment {
                    rows.push(HierarchyRow {
                        kind: "equip",
                        path: format!("{} / {} / {}", floor.name, wing.name, room.name),
                        name: eq.name.clone(),
                        status: equipment_review_status(eq),
                    });
                }
            }
        }
    }
    rows
}

fn quote_name(name: &str) -> String {
    if name.contains(' ') || name.contains('"') {
        format!("\"{}\"", name.replace('"', ""))
    } else {
        name.to_string()
    }
}

#[component]
pub fn Review() -> impl IntoView {
    let (status_msg, set_status_msg) =
        create_signal(String::from("Tap Refresh to load from agent."));
    let (loading, set_loading) = create_signal(false);
    let (building_name, set_building_name) = create_signal(String::new());
    let (meta, set_meta) = create_signal(String::new());
    let (rows, set_rows) = create_signal(Vec::<HierarchyRow>::new());
    let (warnings, set_warnings) = create_signal(Vec::<String>::new());
    let (validate_lines, set_validate_lines) = create_signal(Vec::<String>::new());
    let (export_msg, set_export_msg) = create_signal(String::new());
    let (proposed_only, set_proposed_only) = create_signal(false);
    let (load_gen, set_load_gen) = create_signal(0u32);
    let (approved_only, set_approved_only) = create_signal(true);

    let do_load = move || {
        if !crate::web::ws_client::is_connected() {
            set_status_msg.set("Agent offline — use header Connect (LAN host + token).".into());
            return;
        }
        set_loading.set(true);
        set_status_msg.set("Loading building.get…".into());

        spawn_local(async move {
            match crate::web::ws_client::send_rpc("building.get", serde_json::json!({})).await {
                Ok(val) => {
                    let name = val
                        .get("building")
                        .and_then(|b| b.get("name"))
                        .and_then(|n| n.as_str())
                        .unwrap_or("(unnamed)")
                        .to_string();
                    let floors = val.get("floors").and_then(|v| v.as_u64()).unwrap_or(0);
                    let rooms = val.get("rooms").and_then(|v| v.as_u64()).unwrap_or(0);
                    let equip = val.get("equipment").and_then(|v| v.as_u64()).unwrap_or(0);
                    let pr = val
                        .get("proposed_rooms")
                        .and_then(|v| v.as_u64())
                        .unwrap_or(0);
                    let pe = val
                        .get("proposed_equipment")
                        .and_then(|v| v.as_u64())
                        .unwrap_or(0);
                    let warns: Vec<String> = val
                        .get("review_warnings")
                        .and_then(|v| v.as_array())
                        .map(|a| {
                            a.iter()
                                .filter_map(|x| x.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                        .unwrap_or_default();

                    let hierarchy = match val.get("building").cloned() {
                        Some(bjson) => match serde_json::from_value::<Building>(bjson) {
                            Ok(b) => build_rows(&b),
                            Err(e) => {
                                set_status_msg.set(format!("Parse building failed: {}", e));
                                set_loading.set(false);
                                return;
                            }
                        },
                        None => {
                            set_status_msg.set("building.get missing building field".into());
                            set_loading.set(false);
                            return;
                        }
                    };

                    set_building_name.set(name);
                    set_meta.set(format!(
                        "{} floors · {} rooms · {} equip · proposed R{} / E{}",
                        floors, rooms, equip, pr, pe
                    ));
                    set_rows.set(hierarchy);
                    set_warnings.set(warns);
                    set_status_msg.set(format!(
                        "Loaded from agent ({})",
                        crate::web::ws_client::current_agent_host()
                    ));
                    set_load_gen.update(|n| *n += 1);
                    set_loading.set(false);
                }
                Err(e) => {
                    set_status_msg.set(format!("building.get failed: {}", e));
                    set_loading.set(false);
                }
            }
        });
    };

    let set_status_for = move |kind: &str, name: String, status: String| {
        if !crate::web::ws_client::is_connected() {
            set_status_msg.set("Agent offline.".into());
            return;
        }
        let qn = quote_name(&name);
        let script = if kind == "room" {
            format!("set room {qn} review_status={status}\n")
        } else {
            format!("set equipment {qn} review_status={status}\n")
        };
        set_loading.set(true);
        set_status_msg.set(format!("Setting {} → {}…", name, status));
        let status_done = status.clone();
        spawn_local(async move {
            match crate::web::ws_client::send_rpc(
                "edit.apply",
                serde_json::json!({ "script": script }),
            )
            .await
            {
                Ok(_) => {
                    set_status_msg.set(format!("{} → {}", name, status_done));
                    set_loading.set(false);
                    // reload hierarchy
                    if crate::web::ws_client::is_connected() {
                        match crate::web::ws_client::send_rpc("building.get", serde_json::json!({}))
                            .await
                        {
                            Ok(val) => {
                                if let Some(bjson) = val.get("building").cloned() {
                                    if let Ok(b) = serde_json::from_value::<Building>(bjson) {
                                        set_rows.set(build_rows(&b));
                                        let floors =
                                            val.get("floors").and_then(|v| v.as_u64()).unwrap_or(0);
                                        let rooms =
                                            val.get("rooms").and_then(|v| v.as_u64()).unwrap_or(0);
                                        let equip = val
                                            .get("equipment")
                                            .and_then(|v| v.as_u64())
                                            .unwrap_or(0);
                                        let pr = val
                                            .get("proposed_rooms")
                                            .and_then(|v| v.as_u64())
                                            .unwrap_or(0);
                                        let pe = val
                                            .get("proposed_equipment")
                                            .and_then(|v| v.as_u64())
                                            .unwrap_or(0);
                                        set_meta.set(format!(
                                            "{} floors · {} rooms · {} equip · proposed R{} / E{}",
                                            floors, rooms, equip, pr, pe
                                        ));
                                    }
                                }
                            }
                            Err(e) => set_status_msg.set(format!("Reload failed: {}", e)),
                        }
                    }
                }
                Err(e) => {
                    set_status_msg.set(format!("edit.apply failed: {}", e));
                    set_loading.set(false);
                }
            }
        });
    };

    let do_validate = move |_| {
        if !crate::web::ws_client::is_connected() {
            set_status_msg.set("Agent offline.".into());
            return;
        }
        set_loading.set(true);
        set_status_msg.set("Validating…".into());
        spawn_local(async move {
            match crate::web::ws_client::send_rpc("building.validate", serde_json::json!({})).await
            {
                Ok(val) => {
                    let ok = val.get("ok").and_then(|v| v.as_bool()).unwrap_or(false);
                    let lines: Vec<String> = val
                        .get("summary_lines")
                        .and_then(|a| a.as_array())
                        .map(|a| {
                            a.iter()
                                .filter_map(|x| x.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                        .unwrap_or_default();
                    let review: Vec<String> = val
                        .get("review_warnings")
                        .and_then(|a| a.as_array())
                        .map(|a| {
                            a.iter()
                                .filter_map(|x| x.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                        .unwrap_or_default();
                    set_validate_lines.set(lines.clone());
                    set_warnings.set(review);
                    set_status_msg.set(if ok {
                        "Validation OK (see summary). Note: OK ≠ complete BIM.".into()
                    } else {
                        "Validation FAILED — fix errors before official export.".into()
                    });
                    set_loading.set(false);
                }
                Err(e) => {
                    set_status_msg.set(format!("building.validate failed: {}", e));
                    set_loading.set(false);
                }
            }
        });
    };

    let do_export = move |_| {
        if !crate::web::ws_client::is_connected() {
            set_status_msg.set("Agent offline.".into());
            return;
        }
        let approved = approved_only.get();
        set_loading.set(true);
        set_export_msg.set(String::new());
        set_status_msg.set(if approved {
            "Exporting IFC (approved_only)…".into()
        } else {
            "Exporting full IFC…".into()
        });
        spawn_local(async move {
            match crate::web::ws_client::send_rpc(
                "ifc.export",
                serde_json::json!({
                    "approved_only": approved,
                    "filename": if approved { "bedroom-approved.ifc" } else { "bedroom-full.ifc" },
                }),
            )
            .await
            {
                Ok(val) => {
                    let path = val
                        .get("filename")
                        .and_then(|v| v.as_str())
                        .unwrap_or("exports/*.ifc");
                    let size = val.get("size_bytes").and_then(|v| v.as_u64()).unwrap_or(0);
                    set_export_msg.set(format!(
                        "Exported {} ({} bytes) on capture node. Official spine = same as `arx export --format ifc`.",
                        path, size
                    ));
                    set_status_msg.set(format!("Export OK → {}", path));
                    set_loading.set(false);
                }
                Err(e) => {
                    set_status_msg.set(format!("ifc.export failed: {}", e));
                    set_loading.set(false);
                }
            }
        });
    };

    create_effect(move |_| {
        if crate::web::ws_client::is_connected() && load_gen.get() == 0 && !loading.get() {
            do_load();
        }
    });

    view! {
        <div class="page review-page" style="padding-bottom: 100px;">
            <h1 style="font-size: 1.35rem; margin: 0 0 6px;">"Review"</h1>
            <p style="color: #64748b; font-size: 14px; margin: 0 0 12px;">
                "Hierarchy + review_status + validate + IFC export (agent bridge → real spine)."
            </p>

            <div style=move || {
                if crate::web::ws_client::is_connected() {
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

            <p style="font-size: 13px; color: #475569; margin: 0 0 10px; word-break: break-word;">
                {move || status_msg.get()}
            </p>
            {move || {
                let m = export_msg.get();
                if m.is_empty() {
                    view! { <></> }.into_any()
                } else {
                    view! {
                        <p style="font-size: 13px; color: #166534; background: #dcfce7; padding: 10px; border-radius: 8px; margin: 0 0 10px;">{m}</p>
                    }.into_any()
                }
            }}

            {move || {
                let name = building_name.get();
                if name.is_empty() {
                    view! { <></> }.into_any()
                } else {
                    view! {
                        <div style="margin-bottom: 12px;">
                            <div style="font-weight: 700; font-size: 1.1rem;">{name}</div>
                            <div style="font-size: 13px; color: #64748b;">{meta.get()}</div>
                        </div>
                    }.into_any()
                }
            }}

            <label style="display: flex; align-items: center; gap: 10px; min-height: 44px; margin-bottom: 10px; font-size: 15px;">
                <input
                    type="checkbox"
                    prop:checked=move || proposed_only.get()
                    on:change=move |ev| {
                        let el: web_sys::HtmlInputElement = event_target(&ev);
                        set_proposed_only.set(el.checked());
                    }
                    style="width: 20px; height: 20px;"
                />
                "Proposed only"
            </label>

            <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px;">
                {move || {
                    let only = proposed_only.get();
                    rows.get()
                        .into_iter()
                        .filter(|r| !only || r.status == Some(ReviewStatus::Proposed))
                        .map(|r| {
                            let (label, fg, bg) = status_label(r.status);
                            let kind = r.kind;
                            let path = r.path.clone();
                            let name = r.name.clone();
                            let name_a = name.clone();
                            let name_r = name.clone();
                            let kind_a = kind;
                            let kind_r = kind;
                            view! {
                                <div style="min-height: 48px; display: flex; flex-direction: column; justify-content: center; padding: 10px 12px; border-radius: 10px; border: 1px solid #e2e8f0; background: #fff;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                                        <span style="font-weight: 600; font-size: 15px;">
                                            {format!("[{}] {}", kind, name)}
                                        </span>
                                        <span style=format!(
                                            "font-size: 12px; font-weight: 700; padding: 4px 8px; border-radius: 999px; color: {}; background: {}; white-space: nowrap;",
                                            fg, bg
                                        )>
                                            {label}
                                        </span>
                                    </div>
                                    <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">{path}</div>
                                    <div style="display: flex; gap: 8px; margin-top: 8px;">
                                        <button
                                            type="button"
                                            on:click=move |_| set_status_for(kind_a, name_a.clone(), "accepted".into())
                                            style="flex:1; min-height: 40px; border: none; border-radius: 8px; background: #166534; color: white; font-weight: 600; font-size: 13px;"
                                        >
                                            "Accept"
                                        </button>
                                        <button
                                            type="button"
                                            on:click=move |_| set_status_for(kind_r, name_r.clone(), "rejected".into())
                                            style="flex:1; min-height: 40px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f8fafc; color: #374151; font-weight: 600; font-size: 13px;"
                                        >
                                            "Reject"
                                        </button>
                                    </div>
                                </div>
                            }
                        })
                        .collect_view()
                }}
            </div>

            {move || {
                let w = warnings.get();
                if w.is_empty() {
                    view! { <></> }.into_any()
                } else {
                    view! {
                        <section style="margin-bottom: 12px; padding: 12px; border-radius: 10px; background: #fffbeb; border: 1px solid #fcd34d;">
                            <h2 style="font-size: 0.95rem; margin: 0 0 8px;">"Review warnings"</h2>
                            <ul style="margin: 0; padding-left: 1.1rem; font-size: 12px; color: #78350f;">
                                {w.into_iter().map(|line| view! { <li style="margin-bottom: 4px;">{line}</li> }).collect_view()}
                            </ul>
                        </section>
                    }.into_any()
                }
            }}

            {move || {
                let lines = validate_lines.get();
                if lines.is_empty() {
                    view! { <></> }.into_any()
                } else {
                    view! {
                        <section style="margin-bottom: 12px; padding: 12px; border-radius: 10px; background: #f1f5f9; border: 1px solid #e2e8f0;">
                            <h2 style="font-size: 0.95rem; margin: 0 0 8px;">"Validation / LossReport"</h2>
                            <ul style="margin: 0; padding-left: 1.1rem; font-size: 12px; font-family: ui-monospace, monospace;">
                                {lines.into_iter().map(|line| view! { <li>{line}</li> }).collect_view()}
                            </ul>
                        </section>
                    }.into_any()
                }
            }}

            <label style="display: flex; align-items: center; gap: 10px; min-height: 44px; margin-bottom: 8px; font-size: 14px;">
                <input
                    type="checkbox"
                    prop:checked=move || approved_only.get()
                    on:change=move |ev| {
                        let el: web_sys::HtmlInputElement = event_target(&ev);
                        set_approved_only.set(el.checked());
                    }
                    style="width: 20px; height: 20px;"
                />
                "Export approved_only (drop proposed/rejected)"
            </label>

            <div style="position: fixed; left: 0; right: 0; bottom: 0; z-index: 40; background: #0f172a; color: #f8fafc; padding: 10px 12px; box-shadow: 0 -2px 12px rgba(0,0,0,0.2);">
                <div style="max-width: 960px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px;">
                    <button
                        type="button"
                        on:click=move |_| do_load()
                        prop:disabled=move || loading.get()
                        style="min-height: 48px; border: none; border-radius: 10px; background: #334155; color: white; font-size: 14px; font-weight: 600; cursor: pointer;"
                    >
                        {move || if loading.get() { "…" } else { "Refresh" }}
                    </button>
                    <button
                        type="button"
                        on:click=do_validate
                        prop:disabled=move || loading.get()
                        style="min-height: 48px; border: none; border-radius: 10px; background: #0369a1; color: white; font-size: 14px; font-weight: 600; cursor: pointer;"
                    >
                        "Validate"
                    </button>
                    <button
                        type="button"
                        on:click=do_export
                        prop:disabled=move || loading.get()
                        style="min-height: 48px; border: none; border-radius: 10px; background: #2563eb; color: white; font-size: 14px; font-weight: 600; cursor: pointer;"
                    >
                        "Export IFC"
                    </button>
                </div>
            </div>
        </div>
    }
}
