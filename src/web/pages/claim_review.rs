//! Owner Staging Review Dashboard Leptos Page Component.

use leptos::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingContributionDto {
    pub index: usize,
    pub summary: String,
    pub content: String,
}

#[component]
pub fn ClaimReview() -> impl IntoView {
    // 1. Reactive State Signals
    let (loading, set_loading) = signal(false);
    let (status_msg, set_status_msg) = signal(String::from("Ready to load staging contributions..."));
    
    let (building_id, _set_building_id) = signal(String::from("building-123"));
    let (grace_active, set_grace_active) = signal(true);
    let (grace_days, set_grace_days) = signal(14u32);
    let (claim_status, set_claim_status) = signal(String::from("WaitingForReview"));
    
    let (pending_list, set_pending_list) = signal(Vec::<PendingContributionDto>::new());
    let (selected_contrib, set_selected_contrib) = signal(None::<PendingContributionDto>);
    
    let (live_mode, set_live_mode) = signal(false);
    let (owner_address, set_owner_address) = signal(String::from("0x1234567890abcdef"));

    // 2. Initial Data Loading function
    let load_data = move || {
        if !crate::web::ws_client::is_connected() {
            set_status_msg.set("Agent offline — use header to connect.".into());
            return;
        }
        
        set_loading.set(true);
        set_status_msg.set("Fetching status and pending queue...".into());

        // A. Load Grace Window Status
        leptos::prelude::spawn_local(async move {
            match crate::web::ws_client::send_rpc(
                "claim.get_status",
                serde_json::json!({ "building_id": building_id.get() }),
            ).await {
                Ok(val) => {
                    if let Some(active) = val.get("grace_window_active").and_then(|v| v.as_bool()) {
                        set_grace_active.set(active);
                    }
                    if let Some(days) = val.get("claim_grace_period_days").and_then(|v| v.as_u64()) {
                        set_grace_days.set(days as u32);
                    }
                    if let Some(status) = val.get("status").and_then(|v| v.as_str()) {
                        set_claim_status.set(status.to_string());
                    }
                }
                Err(e) => {
                    set_status_msg.set(format!("Error loading status: {}", e));
                }
            }

            // B. Load Pending Contributions
            match crate::web::ws_client::send_rpc(
                "claim.list_pending",
                serde_json::json!({}),
            ).await {
                Ok(val) => {
                    if let Some(arr) = val.as_array() {
                        let parsed: Vec<PendingContributionDto> = arr.iter().map(|item| {
                            PendingContributionDto {
                                index: item.get("index").and_then(|v| v.as_u64()).unwrap_or(0) as usize,
                                summary: item.get("summary").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                                content: item.get("content").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                            }
                        }).collect();
                        
                        set_pending_list.set(parsed);
                        set_status_msg.set("Staging data loaded successfully.".into());
                    }
                    set_loading.set(false);
                }
                Err(e) => {
                    set_status_msg.set(format!("Error loading contributions: {}", e));
                    set_loading.set(false);
                }
            }
        });
    };

    // Trigger load on connection status changes
    Effect::new(move |_| {
        if crate::web::ws_client::is_connected() {
            load_data();
        }
    });

    // 3. Approve Action
    let on_approve = move |index: usize| {
        set_loading.set(true);
        set_status_msg.set(format!("Approving contribution {} and releasing rewards...", index));

        leptos::prelude::spawn_local(async move {
            match crate::web::ws_client::send_rpc(
                "claim.review",
                serde_json::json!({
                    "building_id": building_id.get(),
                    "index": index,
                    "approve": true,
                    "owner_address": owner_address.get(),
                    "live": live_mode.get(),
                }),
            ).await {
                Ok(val) => {
                    let receipt = val.get("receipt").and_then(|v| v.as_str()).unwrap_or("");
                    set_status_msg.set(format!("Approved index {}. Receipt:\n{}", index, receipt));
                    set_selected_contrib.set(None);
                    load_data(); // reload lists
                }
                Err(e) => {
                    set_status_msg.set(format!("Approval failed: {}", e));
                    set_loading.set(false);
                }
            }
        });
    };

    // 4. Reject Action
    let on_reject = move |index: usize| {
        set_loading.set(true);
        set_status_msg.set(format!("Rejecting contribution {}...", index));

        leptos::prelude::spawn_local(async move {
            match crate::web::ws_client::send_rpc(
                "claim.review",
                serde_json::json!({
                    "building_id": building_id.get(),
                    "index": index,
                    "approve": false,
                    "owner_address": owner_address.get(),
                    "live": live_mode.get(),
                }),
            ).await {
                Ok(_) => {
                    set_status_msg.set(format!("Rejected contribution index {}.", index));
                    set_selected_contrib.set(None);
                    load_data();
                }
                Err(e) => {
                    set_status_msg.set(format!("Rejection failed: {}", e));
                    set_loading.set(false);
                }
            }
        });
    };

    view! {
        <div class="owner-review-dashboard" style="color: #fff; font-family: sans-serif; padding: 16px;">
            // Dashboard Header
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 12px; margin-bottom: 20px;">
                <div>
                    <h2 style="margin: 0; font-size: 22px; color: #4caf50;">"Owner Staging Review Portal"</h2>
                    <span style="font-size: 11px; color: #aaa;">"Building Twin ID: " {building_id.get()}</span>
                </div>
                <button
                    on:click=move |_| load_data()
                    disabled=loading.get()
                    style="background: #2196f3; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; cursor: pointer;"
                >
                    {move || if loading.get() { "Loading..." } else { "Refresh List" }}
                </button>
            </div>

            // Operations Status Message Banner
            <div style="background: #222; border-left: 4px solid #2196f3; padding: 12px; margin-bottom: 20px; font-size: 13px; font-family: monospace; white-space: pre-wrap;">
                {status_msg.get()}
            </div>

            <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                // Left Column: Configuration and Pending Queue
                <div style="flex: 1; min-width: 320px; display: flex; flex-direction: column; gap: 20px;">
                    // Grace Window Information Card
                    <div style="background: #181818; border: 1px solid #333; border-radius: 8px; padding: 16px;">
                        <h3 style="margin-top: 0; font-size: 15px; border-bottom: 1px solid #333; padding-bottom: 6px;">
                            "Grace Window Configuration"
                        </h3>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
                            <span style="color: #aaa;">"Grace Window State:"</span>
                            <span style=format!("font-weight: bold; color: {};", if grace_active.get() { "#4caf50" } else { "#f44336" })>
                                {move || if grace_active.get() { "Active (Open)" } else { "Expired (Locked)" }}
                            </span>

                            <span style="color: #aaa;">"Grace Duration Config:"</span>
                            <span>{grace_days.get()} " Days"</span>

                            <span style="color: #aaa;">"Claim Status:"</span>
                            <span style="font-weight: bold; color: #2196f3;">{claim_status.get()}</span>
                        </div>
                    </div>

                    // Blockchain Rewards Distribution Configuration Card
                    <div style="background: #181818; border: 1px solid #333; border-radius: 8px; padding: 16px;">
                        <h3 style="margin-top: 0; font-size: 15px; border-bottom: 1px solid #333; padding-bottom: 6px;">
                            "Rewards Split Configuration"
                        </h3>
                        <div style="display: flex; flex-direction: column; gap: 10px; font-size: 12px;">
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input
                                    type="checkbox"
                                    checked=live_mode.get()
                                    on:change=move |ev| set_live_mode.set(event_target_checked(&ev))
                                />
                                <span>"Enable Live Phase Network Rewards (Dry-run if unchecked)"</span>
                            </label>
                            
                            <div>
                                <span style="color: #aaa;">"Owner Wallet Address (10% Split):"</span>
                                <input
                                    type="text"
                                    value=owner_address.get()
                                    on:input=move |ev| set_owner_address.set(event_target_value(&ev))
                                    style="width: 100%; background: #2b2b2b; color: #fff; border: 1px solid #444; padding: 6px; border-radius: 4px; font-size: 12px; margin-top: 4px; box-sizing: border-box;"
                                />
                            </div>
                        </div>
                    </div>

                    // Pending Contribution List Selection List
                    <div style="background: #181818; border: 1px solid #333; border-radius: 8px; padding: 16px; flex: 1;">
                        <h3 style="margin-top: 0; font-size: 15px; border-bottom: 1px solid #333; padding-bottom: 6px;">
                            "Pending Queue"
                        </h3>
                        {move || if pending_list.get().is_empty() {
                            view! {
                                <div style="color: #666; font-size: 13px; text-align: center; padding: 24px;">
                                    "No contributions currently pending review."
                                </div>
                            }.into_any()
                        } else {
                            view! {
                                <div style="display: flex; flex-direction: column; gap: 8px;">
                                    {pending_list.get().into_iter().map(|item| {
                                        let item_clone = item.clone();
                                        let is_selected = selected_contrib.get().map(|sc| sc.index == item.index).unwrap_or(false);
                                        
                                        view! {
                                            <div
                                                on:click=move |_| set_selected_contrib.set(Some(item_clone.clone()))
                                                style=format!(
                                                    "background: {}; border: 1px solid {}; border-radius: 4px; padding: 10px; cursor: pointer; transition: 0.1s;",
                                                    if is_selected { "#2b2b2b" } else { "#222" },
                                                    if is_selected { "#4caf50" } else { "#333" }
                                                )
                                            >
                                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                                    <span style="font-weight: bold; font-size: 13px;">"Index #" {item.index}</span>
                                                    <span style="font-size: 10px; color: #ffa726; background: rgba(255,167,38,0.15); padding: 2px 6px; border-radius: 10px;">
                                                        "Pending"
                                                    </span>
                                                </div>
                                                <div style="font-size: 11px; color: #ccc; margin-top: 4px;">{item.summary}</div>
                                            </div>
                                        }
                                    }).collect::<Vec<_>>()}
                                </div>
                            }.into_any()
                        }}
                    </div>
                </div>

                // Right Column: Contribution Detail Inspection View
                <div style="flex: 2; min-width: 400px; background: #181818; border: 1px solid #333; border-radius: 8px; padding: 16px; display: flex; flex-direction: column;">
                    {move || if let Some(contrib) = selected_contrib.get() {
                        let idx = contrib.index;
                        view! {
                            <div style="display: flex; flex-direction: column; height: 100%;">
                                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 16px;">
                                    <h3 style="margin: 0; font-size: 16px; color: #ffa726;">
                                        "Inspect Contribution Index #" {idx}
                                    </h3>
                                    <div style="font-size: 11px; color: #aaa;">"Staging update queue file details"</div>
                                </div>

                                // Payout Escrow Split Summary Banner
                                <div style="background: rgba(76,175,80,0.1); border: 1px solid rgba(76,175,80,0.3); padding: 12px; border-radius: 6px; font-size: 12px; color: #81c784; margin-bottom: 16px; line-height: 1.4;">
                                    <strong>"Escrow Reward Split Payout details on approval:"</strong>
                                    <ul style="margin: 6px 0 0 16px; padding: 0;">
                                        <li>"70% directly to Field Workers (Labor incentive)"</li>
                                        <li>"10% directly to Owner (Data rights, owner address below)"</li>
                                        <li>"20% retained in Maintainers pool"</li>
                                    </ul>
                                </div>

                                // YAML details codeviewer box
                                <div style="flex: 1; background: #000; border: 1px solid #333; border-radius: 4px; padding: 12px; font-family: monospace; font-size: 11px; overflow: auto; max-height: 300px; white-space: pre-wrap; margin-bottom: 20px;">
                                    {contrib.content}
                                </div>

                                // Action Buttons Panel
                                <div style="display: flex; gap: 12px; justify-content: flex-end;">
                                    <button
                                        on:click=move |_| on_reject(idx)
                                        disabled=loading.get()
                                        style="background: #f44336; color: #fff; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold; cursor: pointer;"
                                    >
                                        "Reject & Archive"
                                    </button>
                                    <button
                                        on:click=move |_| on_approve(idx)
                                        disabled=loading.get()
                                        style="background: #4caf50; color: #fff; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold; cursor: pointer;"
                                    >
                                        "Approve & Merge"
                                    </button>
                                </div>
                            </div>
                        }.into_any()
                    } else {
                        view! {
                            <div style="flex: 1; display: flex; align-items: center; justify-content: center; color: #666; font-size: 14px; text-align: center; min-height: 300px;">
                                "Select a pending contribution from the list to inspect its contents, run address promotion checks, and distribute incentives."
                            </div>
                        }.into_any()
                    }}
                </div>
            </div>
        </div>
    }
}
