use crate::core::Building;
use leptos::prelude::*;
use leptos::*;
use leptos_router::hooks::use_params_map;
use serde_json::Value;
use wasm_bindgen_futures::spawn_local;

#[component]
pub fn BuildingDetail() -> impl IntoView {
    let params = use_params_map();
    let id = move || params.with(|p| p.get("id").unwrap_or_default());

    // Signals for local building data
    let (building, set_building) = create_signal(Option::<Building>::None);

    // Signals for agent state
    let (git_status, set_git_status) = create_signal(Option::<Value>::None);
    let (commit_message, set_commit_message) = create_signal(String::new());
    let (action_message, set_action_message) = create_signal(String::new());

    // Load building data from sync envelope (or legacy localStorage) on mount
    create_effect(move |_| {
        let want_id = id();
        if let Ok(envelope_json) = crate::web::wasm_bridge::load_active_building() {
            if let Ok(building_json) =
                crate::web::wasm_bridge::building_json_from_envelope(&envelope_json)
            {
                if let Ok(b) = serde_json::from_str::<Building>(&building_json) {
                    if b.id == want_id || want_id.is_empty() {
                        set_building.set(Some(b));
                        return;
                    }
                }
            }
        }
        if let Some(window) = web_sys::window() {
            if let Ok(Some(storage)) = window.local_storage() {
                if let Ok(Some(json)) = storage.get_item("last_imported_building") {
                    if let Ok(b) = serde_json::from_str::<Building>(&json) {
                        if b.id == want_id {
                            set_building.set(Some(b));
                        }
                    }
                }
            }
        }
    });

    // Helper to fetch Git status from local agent
    let fetch_git_status = move || {
        spawn_local(async move {
            if crate::web::ws_client::is_connected() {
                match crate::web::ws_client::send_rpc("git.status", serde_json::json!({})).await {
                    Ok(status) => {
                        set_git_status.set(Some(status));
                    }
                    Err(e) => {
                        set_action_message.set(format!("Failed to fetch Git status: {}", e));
                    }
                }
            } else {
                set_git_status.set(None);
            }
        });
    };

    // Trigger initial Git status load
    create_effect(move |_| {
        fetch_git_status();
    });

    // Commit action handler
    let commit_action = move |ev: web_sys::SubmitEvent| {
        ev.prevent_default();
        let message = commit_message.get();
        if message.is_empty() {
            set_action_message.set("Commit message cannot be empty".to_string());
            return;
        }

        set_action_message.set("Committing changes...".to_string());
        spawn_local(async move {
            match crate::web::ws_client::send_rpc(
                "git.commit",
                serde_json::json!({
                    "message": message,
                    "stageAll": true
                }),
            )
            .await
            {
                Ok(result) => {
                    set_action_message.set(format!("Committed: {}", result));
                    set_commit_message.set(String::new());
                    fetch_git_status(); // Refresh Git status
                }
                Err(e) => {
                    set_action_message.set(format!("Commit failed: {}", e));
                }
            }
        });
    };

    // Compute stats from local building representation
    let floors_count = move || building.get().map(|b| b.floors.len()).unwrap_or(0);

    let rooms_count = move || building.get().map(|b| b.get_all_rooms().len()).unwrap_or(0);

    /// Count all equipment across the full hierarchy:
    /// floor common areas + wing-level equipment + room-level equipment.
    let equipment_count = move || {
        building
            .get()
            .map(|b| {
                b.floors
                    .iter()
                    .flat_map(|f| {
                        // Floor-level common-area equipment
                        let floor_eq = f.equipment.len();
                        // Wing-level equipment + room-level equipment
                        let wing_and_room_eq: usize = f
                            .wings
                            .iter()
                            .map(|w| {
                                w.equipment.len()
                                    + w.rooms.iter().map(|r| r.equipment.len()).sum::<usize>()
                            })
                            .sum();
                        std::iter::once(floor_eq + wing_and_room_eq)
                    })
                    .sum::<usize>()
            })
            .unwrap_or(0)
    };

    /// Render an ASCII 3D view of the building using the WASM binding.
    let ascii_view = move || {
        building.get().and_then(|b| {
            serde_json::to_string(&b)
                .ok()
                .map(|json| crate::web::wasm_bridge::render_building_ascii(&json, 78, 20))
        })
    };

    view! {
        <div class="page building-detail-page" style="padding: 20px; max-width: 1000px; margin: 0 auto; font-family: sans-serif;">
            <h1 style="border-bottom: 2px solid #eaeaea; padding-bottom: 10px;">"Building Details"</h1>
            <p style="color: #666; font-size: 14px;">"ID: " {id}
                {move || building.get().map(|b| view! {
                    <span style="margin-left: 8px; color: #333; font-weight: bold;">" — " {b.name.clone()}</span>
                }.into_any()).unwrap_or_else(|| view! { <></> }.into_any())}
            </p>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                // Building Details (Cached)
                <div class="building-info" style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; background-color: #fcfcfc;">
                    <h2 style="margin-top: 0;">"Building Information (Client Cache)"</h2>
                    {move || match building.get() {
                        Some(b) => view! {
                            <div>
                                <p><strong>"Name: "</strong> {b.name.clone()}</p>
                                <p><strong>"Floors: "</strong> {floors_count()}</p>
                                <p><strong>"Rooms: "</strong> {rooms_count()}</p>
                                <p><strong>"Equipment: "</strong> {equipment_count()}</p>
                            </div>
                        }.into_any(),
                        None => view! {
                            <p style="color: #e07a5f;">"No cached building data matches this ID. Please import it first."</p>
                        }.into_any()
                    }}
                </div>

                // Git status & actions from Agent daemon
                <div class="agent-workspace" style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; background-color: #fcfcfc;">
                    <h2 style="margin-top: 0;">"Git Workspace Status (Local Agent)"</h2>

                    {move || if crate::web::ws_client::is_connected() {
                        view! {
                            <div>
                                <button on:click=move |_| fetch_git_status() class="btn btn-sm" style="margin-bottom: 10px; padding: 4px 8px; cursor: pointer;">
                                    "Refresh Status"
                                </button>

                                {move || match git_status.get() {
                                    Some(status) => {
                                        let modified = status.get("modified").and_then(|v| v.as_array()).map(|a| a.len()).unwrap_or(0);
                                        let staged = status.get("staged").and_then(|v| v.as_array()).map(|a| a.len()).unwrap_or(0);
                                        let untracked = status.get("untracked").and_then(|v| v.as_array()).map(|a| a.len()).unwrap_or(0);

                                        view! {
                                            <div style="font-size: 14px; line-height: 1.6;">
                                                <p><strong>"Staged Files: "</strong> {staged}</p>
                                                <p><strong>"Modified Files: "</strong> {modified}</p>
                                                <p><strong>"Untracked Files: "</strong> {untracked}</p>

                                                {move || if modified > 0 || untracked > 0 || staged > 0 {
                                                    view! {
                                                        <form on:submit=commit_action style="margin-top: 15px; border-top: 1px solid #eee; padding-top: 15px;">
                                                            <div style="display: flex; flex-direction: column; gap: 8px;">
                                                                <label style="font-weight: bold; font-size: 12px;">"Commit Message"</label>
                                                                <input
                                                                    type="text"
                                                                    placeholder="e.g. Added scanner logs for Floor 1"
                                                                    prop:value=commit_message
                                                                    on:input=move |ev| set_commit_message.set(event_target_value(&ev))
                                                                    style="padding: 6px 10px; border: 1px solid #ccc; border-radius: 4px;"
                                                                />
                                                                <button type="submit" class="btn btn-primary" style="padding: 6px 12px; cursor: pointer; align-self: flex-start;">
                                                                    "Stage & Commit Changes"
                                                                </button>
                                                            </div>
                                                        </form>
                                                    }.into_any()
                                                } else {
                                                    view! {
                                                        <p style="color: #4f772d; font-weight: bold;">"✓ Workspace is clean (no changes)"</p>
                                                    }.into_any()
                                                }}
                                            </div>
                                        }.into_any()
                                    }
                                    None => view! { <p style="color: #888;">"Loading workspace status..."</p> }.into_any()
                                }}
                            </div>
                        }.into_any()
                    } else {
                        view! {
                            <div style="color: #888; text-align: center; padding: 20px 0;">
                                <p>"⚠️ Agent offline or disconnected."</p>
                                <p style="font-size: 12px; line-height: 1.4;">"Please paste your DID token in the header and click Connect to access Git history, commits, and sensor streams."</p>
                            </div>
                        }.into_any()
                    }}
                </div>
            </div>

            // 3D ASCII View panel — visible only when building data is loaded
            {move || ascii_view().map(|view_str| view! {
                <div style="margin-top: 20px; border: 1px solid #ddd; border-radius: 8px; padding: 16px; background: #1a1a2e;">
                    <h2 style="margin-top: 0; color: #e2eafc; font-size: 14px; font-family: monospace;">"🏢 3D ASCII Building View"</h2>
                    <pre id="building-ascii-view" style="
                        font-family: 'Courier New', Courier, monospace;
                        font-size: 11px;
                        color: #a8d8ea;
                        background: #0d0d1a;
                        padding: 12px;
                        border-radius: 4px;
                        overflow-x: auto;
                        white-space: pre;
                        line-height: 1.3;
                        margin: 0;
                    ">{view_str}</pre>
                </div>
            }.into_any())}

            // Action status notification bar
            {move || if !action_message.get().is_empty() {
                view! {
                    <div style="margin-top: 20px; padding: 12px; border-radius: 6px; background-color: #e2eafc; border: 1px solid #b5c99a; font-size: 13px; display: flex; justify-content: space-between; align-items: center;">
                        <span>{action_message.get()}</span>
                        <button on:click=move |_| set_action_message.set(String::new()) style="border: none; background: none; font-weight: bold; cursor: pointer;">"✕"</button>
                    </div>
                }.into_any()
            } else {
                view! { <></> }.into_any()
            }}
        </div>
    }
}
