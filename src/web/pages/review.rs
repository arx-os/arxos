//! Agent-backed Review page (Batch B2–B3): load building.get, hierarchy + proposed badges.

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

#[component]
pub fn Review() -> impl IntoView {
    let (status_msg, set_status_msg) = create_signal(String::from("Tap Refresh to load from agent."));
    let (loading, set_loading) = create_signal(false);
    let (building_name, set_building_name) = create_signal(String::new());
    let (meta, set_meta) = create_signal(String::new());
    let (rows, set_rows) = create_signal(Vec::<HierarchyRow>::new());
    let (warnings, set_warnings) = create_signal(Vec::<String>::new());
    let (proposed_only, set_proposed_only) = create_signal(false);
    let (load_gen, set_load_gen) = create_signal(0u32);

    let (claims_processed, set_claims_processed) = create_signal(0usize);
    let (claims_approved, set_claims_approved) = create_signal(0usize);
    let (claims_rejected, set_claims_rejected) = create_signal(0usize);
    let (rewards_axd, set_rewards_axd) = create_signal(0.0f64);

    let do_load = move || {
        if !crate::web::ws_client::is_connected() {
            set_status_msg.set(
                "Agent offline — use header Connect (LAN host + token).".into(),
            );
            return;
        }
        set_loading.set(true);
        set_status_msg.set("Loading building.get…".into());

        // Fetch queue stats from /api/claims/status
        let host = crate::web::ws_client::current_agent_host();
        let token = crate::web::ws_client::get_saved_token().unwrap_or_default();
        let status_url = format!("http://{}/api/claims/status?token={}", host, token);
        spawn_local(async move {
            if let Ok(res) = gloo_net::http::Request::get(&status_url).send().await {
                if let Ok(stats) = res.json::<serde_json::Value>().await {
                    if let Some(processed) = stats.get("claims_processed").and_then(|v| v.as_u64()) {
                        set_claims_processed.set(processed as usize);
                    }
                    if let Some(approved) = stats.get("claims_approved").and_then(|v| v.as_u64()) {
                        set_claims_approved.set(approved as usize);
                    }
                    if let Some(rejected) = stats.get("claims_rejected").and_then(|v| v.as_u64()) {
                        set_claims_rejected.set(rejected as usize);
                    }
                    if let Some(axd) = stats.get("rewards_distributed_axd").and_then(|v| v.as_f64()) {
                        set_rewards_axd.set(axd);
                    }
                }
            }
        });

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

    // Auto-load once when Online on mount
    create_effect(move |_| {
        if crate::web::ws_client::is_connected() && load_gen.get() == 0 && !loading.get() {
            do_load();
        }
    });

    view! {
        <div class="page review-page" style="padding-bottom: 88px;">
            <h1 style="font-size: 1.35rem; margin: 0 0 6px;">"Review"</h1>
            <p style="color: #64748b; font-size: 14px; margin: 0 0 12px;">
                "Live model from laptop agent (building.get). Read-only until Batch B4–B5."
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

            <p style="font-size: 13px; color: #475569; margin: 0 0 10px; word-break: break-word;">
                {move || status_msg.get()}
            </p>

            {move || {
                let name = building_name.get();
                if name.is_empty() {
                    view! { <></> }.into_any()
                } else {
                    view! {
                        <div style="margin-bottom: 12px;">
                            <div style="font-weight: 700; font-size: 1.1rem;">{name}</div>
                            <div style="font-size: 13px; color: #64748b;">{meta.get()}</div>
                            <div style="margin-top: 6px; display: flex; flex-wrap: wrap; gap: 6px; font-size: 11px;">
                                <span style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px; color: #475569; font-weight: 600;">
                                    "Processed: " {move || claims_processed.get()}
                                </span>
                                <span style="background: #dcfce7; padding: 2px 6px; border-radius: 4px; color: #166534; font-weight: 600;">
                                    "Approved: " {move || claims_approved.get()}
                                </span>
                                <span style="background: #fee2e2; padding: 2px 6px; border-radius: 4px; color: #991b1b; font-weight: 600;">
                                    "Rejected: " {move || claims_rejected.get()}
                                </span>
                                <span style="background: #e0f2fe; padding: 2px 6px; border-radius: 4px; color: #0369a1; font-weight: 600;">
                                    "Distributed: " {move || format!("{:.1} AXD", rewards_axd.get())}
                                </span>
                            </div>
                        </div>
                    }.into_any()
                }
            }}

            <label style="display: flex; align-items: center; gap: 10px; min-height: 48px; margin-bottom: 10px; font-size: 15px;">
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

            <div style="display: flex; flex-direction: column; gap: 8px;">
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
                            view! {
                                <div style=format!(
                                    "min-height: 48px; display: flex; flex-direction: column; justify-content: center; padding: 10px 12px; border-radius: 10px; border: 1px solid #e2e8f0; background: #fff;"
                                )>
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
                        <section style="margin-top: 16px; padding: 12px; border-radius: 10px; background: #fffbeb; border: 1px solid #fcd34d;">
                            <h2 style="font-size: 0.95rem; margin: 0 0 8px;">"Review warnings"</h2>
                            <ul style="margin: 0; padding-left: 1.1rem; font-size: 12px; color: #78350f;">
                                {w.into_iter().map(|line| view! { <li style="margin-bottom: 4px;">{line}</li> }).collect_view()}
                            </ul>
                        </section>
                    }.into_any()
                }
            }}

            // Sticky bottom bar (B3 polish; Export reserved for B7)
            <div style="position: fixed; left: 0; right: 0; bottom: 0; z-index: 40; background: #0f172a; color: #f8fafc; padding: 10px 12px; box-shadow: 0 -2px 12px rgba(0,0,0,0.2);">
                <div style="max-width: 960px; margin: 0 auto; display: flex; gap: 10px;">
                    <button
                        type="button"
                        on:click=move |_| do_load()
                        prop:disabled=move || loading.get()
                        style="flex: 1; min-height: 48px; border: none; border-radius: 10px; background: #2563eb; color: white; font-size: 16px; font-weight: 600; cursor: pointer;"
                    >
                        {move || if loading.get() { "Loading…" } else { "Refresh" }}
                    </button>
                    <button
                        type="button"
                        disabled=true
                        title="Batch B7"
                        style="flex: 1; min-height: 48px; border: none; border-radius: 10px; background: #334155; color: #94a3b8; font-size: 14px; font-weight: 600;"
                    >
                        "Export (soon)"
                    </button>
                </div>
            </div>
        </div>
    }
}
