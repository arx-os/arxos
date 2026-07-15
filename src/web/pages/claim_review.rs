//! Owner Staging Review Dashboard Leptos Page Component.

use leptos::prelude::*;
use serde::{Deserialize, Serialize};
use std::cell::RefCell;
use wasm_bindgen_futures::spawn_local;
use crate::web::cache::WarmCache;
use crate::web::cache::warm::BuildingSyncEnvelope;
use crate::core::domain::ArxAddress;

thread_local! {
    static CLAIM_WARM_CACHE: RefCell<WarmCache> = RefCell::new(WarmCache::new());
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PendingContributionDto {
    pub index: usize,
    pub building_id: String,
    pub address: String,
    pub contributor: String,
    pub summary: String,
    pub estimated_reward: String,
    pub timestamp: u64,
    pub status: String,
    pub content: String,
}

fn format_age(timestamp: u64) -> String {
    let now = chrono::Utc::now().timestamp() as u64;
    if now < timestamp {
        return "Just now".to_string();
    }
    let diff = now - timestamp;
    if diff < 60 {
        format!("{}s ago", diff)
    } else if diff < 3600 {
        format!("{}m ago", diff / 60)
    } else if diff < 86400 {
        format!("{}h ago", diff / 3600)
    } else {
        format!("{}d ago", diff / 86400)
    }
}

fn format_short_address(addr: &str) -> String {
    if addr.len() > 12 {
        format!("{}...{}", &addr[0..6], &addr[addr.len()-4..addr.len()])
    } else {
        addr.to_string()
    }
}

#[component]
pub fn ClaimReview() -> impl IntoView {
    // 1. Reactive State Signals
    let (loading, set_loading) = signal(false);
    let (status_msg, set_status_msg) = signal(String::from("Ready to load staging contributions..."));
    let (last_updated, set_last_updated) = signal(None::<u64>);
    
    let (building_id, _set_building_id) = signal(String::from("building-123"));
    let (grace_active, set_grace_active) = signal(true);
    let (grace_days, set_grace_days) = signal(14u32);
    let (claim_status, set_claim_status) = signal(String::from("WaitingForReview"));
    
    let (pending_list, set_pending_list) = signal(Vec::<PendingContributionDto>::new());
    let (selected_contrib, set_selected_contrib) = signal(None::<PendingContributionDto>);
    
    let (live_mode, set_live_mode) = signal(false);
    let (owner_address, set_owner_address) = signal(String::from("0x1234567890abcdef"));

    // Load from local Warm Cache on init
    let load_from_cache = move || {
        if let Ok(addr) = ArxAddress::from_path("/owner/staging") {
            if let Some(envelope) = CLAIM_WARM_CACHE.with(|cache| cache.borrow_mut().get_subtree(&addr).cloned()) {
                if let Ok(cached_list) = serde_json::from_str::<Vec<PendingContributionDto>>(&envelope.payload) {
                    set_pending_list.set(cached_list);
                    set_last_updated.set(Some(envelope.fetched_at_timestamp));
                    set_status_msg.set("Loaded pending list from local cache.".into());
                }
            }
        }
    };

    // 2. Initial Data Loading function
    let load_data = move || {
        load_from_cache();

        if !crate::web::ws_client::is_connected() {
            set_status_msg.set("Agent offline — use header to connect.".into());
            return;
        }
        
        set_loading.set(true);
        set_status_msg.set("Fetching status and pending queue...".into());

        // A. Load Grace Window Status
        spawn_local(async move {
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
                                building_id: item.get("building_id").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                                address: item.get("address").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                                contributor: item.get("contributor").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                                summary: item.get("summary").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                                estimated_reward: item.get("estimated_reward").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                                timestamp: item.get("timestamp").and_then(|v| v.as_u64()).unwrap_or(0),
                                status: item.get("status").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                                content: item.get("content").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                            }
                        }).collect();
                        
                        set_pending_list.set(parsed.clone());
                        set_status_msg.set("Staging data loaded successfully.".into());
                        
                        // Cache in Warm Cache
                        if let Ok(addr) = ArxAddress::from_path("/owner/staging") {
                            let ts = chrono::Utc::now().timestamp() as u64;
                            let envelope = BuildingSyncEnvelope {
                                base_address: addr,
                                anchors: vec![],
                                payload: serde_json::to_string(&parsed).unwrap_or_default(),
                                fetched_at_timestamp: ts,
                            };
                            CLAIM_WARM_CACHE.with(|cache| cache.borrow_mut().insert_subtree(envelope));
                            set_last_updated.set(Some(ts));
                        }
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
        } else {
            load_from_cache();
        }
    });

    // 3. Approve Action
    let on_approve = move |index: usize| {
        set_loading.set(true);
        set_status_msg.set(format!("Approving contribution {} and releasing rewards...", index));

        spawn_local(async move {
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

        spawn_local(async move {
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
        <div class="owner-review-dashboard" style="color: #f1f5f9; font-family: system-ui, sans-serif; padding: 20px; background: #0f172a; min-height: 100vh; display: flex; flex-direction: column; gap: 20px;">
            // Dashboard Header
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 16px; flex-wrap: wrap; gap: 12px;">
                <div>
                    <h2 style="margin: 0; font-size: 24px; font-weight: 700; color: #10b981; letter-spacing: -0.025em;">"Owner Staging Review Dashboard"</h2>
                    <div style="font-size: 13px; color: #94a3b8; margin-top: 4px; display: flex; align-items: center; gap: 8px;">
                        <span>"Building Twin ID: " <strong>{building_id.get()}</strong></span>
                        {move || last_updated.get().map(|ts| {
                            let formatted = chrono::DateTime::from_timestamp(ts as i64, 0)
                                .map(|dt| dt.format("%Y-%m-%d %H:%M:%S UTC").to_string())
                                .unwrap_or_else(|| "Unknown".to_string());
                            view! {
                                <span style="color: #64748b;">"• Last Updated: " {formatted}</span>
                            }
                        })}
                    </div>
                </div>
                <button
                    on:click=move |_| load_data()
                    disabled=loading.get()
                    style="background: #2563eb; color: #ffffff; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 14px; min-height: 44px; transition: background 0.2s;"
                    onmouseover="this.style.background='#1d4ed8'"
                    onmouseout="this.style.background='#2563eb'"
                >
                    {move || if loading.get() { "Loading..." } else { "Refresh List" }}
                </button>
            </div>

            // Operations Status Message Banner
            <div style="background: #1e293b; border-left: 4px solid #3b82f6; border-radius: 6px; padding: 12px 16px; font-size: 13px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; white-space: pre-wrap; color: #cbd5e1; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                {status_msg.get()}
            </div>

            <div style="display: flex; gap: 24px; flex-wrap: wrap;">
                // Left Column: Configuration and Pending Queue
                <div style="flex: 1; min-width: 340px; display: flex; flex-direction: column; gap: 20px;">
                    // Grace Window Information Card
                    <div style="background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 18px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                        <h3 style="margin-top: 0; font-size: 16px; font-weight: 600; border-bottom: 1px solid #334155; padding-bottom: 8px; color: #f8fafc;">
                            "Grace Window Configuration"
                        </h3>
                        <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 10px; font-size: 13px; margin-top: 12px;">
                            <span style="color: #94a3b8;">"Grace Window State:"</span>
                            <span style=format!("font-weight: 700; color: {};", if grace_active.get() { "#10b981" } else { "#ef4444" })>
                                {move || if grace_active.get() { "Active (Open)" } else { "Expired (Locked)" }}
                            </span>

                            <span style="color: #94a3b8;">"Grace Duration Config:"</span>
                            <span style="color: #f8fafc; font-weight: 500;">{grace_days.get()} " Days"</span>

                            <span style="color: #94a3b8;">"Claim Status:"</span>
                            <span style="font-weight: 700; color: #3b82f6;">{claim_status.get()}</span>
                        </div>
                    </div>

                    // Blockchain Rewards Distribution Configuration Card
                    <div style="background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 18px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                        <h3 style="margin-top: 0; font-size: 16px; font-weight: 600; border-bottom: 1px solid #334155; padding-bottom: 8px; color: #f8fafc;">
                            "Rewards Split Configuration"
                        </h3>
                        <div style="display: flex; flex-direction: column; gap: 14px; font-size: 13px; margin-top: 12px;">
                            <label style="display: flex; align-items: center; gap: 10px; cursor: pointer; color: #cbd5e1; user-select: none;">
                                <input
                                    type="checkbox"
                                    checked=live_mode.get()
                                    on:change=move |ev| set_live_mode.set(event_target_checked(&ev))
                                    style="width: 16px; height: 16px; border-radius: 4px; accent-color: #2563eb;"
                                />
                                <span>"Enable Live Phase Network Rewards (Dry-run if unchecked)"</span>
                            </label>
                            
                            <div>
                                <span style="color: #94a3b8; font-weight: 500;">"Owner Wallet Address (10% Split):"</span>
                                <input
                                    type="text"
                                    value=owner_address.get()
                                    on:input=move |ev| set_owner_address.set(event_target_value(&ev))
                                    style="width: 100%; background: #0f172a; color: #f8fafc; border: 1px solid #334155; padding: 8px 12px; border-radius: 6px; font-size: 13px; margin-top: 6px; box-sizing: border-box; font-family: ui-monospace, monospace;"
                                />
                            </div>
                        </div>
                    </div>

                    // Pending Contribution Queue
                    <div style="background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 18px; flex: 1; display: flex; flex-direction: column; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                        <h3 style="margin-top: 0; font-size: 16px; font-weight: 600; border-bottom: 1px solid #334155; padding-bottom: 8px; color: #f8fafc; margin-bottom: 12px;">
                            "Pending Queue"
                        </h3>
                        {move || if pending_list.get().is_empty() {
                            view! {
                                <div style="color: #64748b; font-size: 14px; text-align: center; padding: 32px 16px; display: flex; flex-direction: column; gap: 8px;">
                                    <span style="font-size: 24px;">"📦"</span>
                                    <span>"No contributions currently pending review."</span>
                                </div>
                            }.into_any()
                        } else {
                            view! {
                                <div style="display: flex; flex-direction: column; gap: 12px; overflow-y: auto; max-height: 480px;">
                                    {pending_list.get().into_iter().map(|item| {
                                        let item_clone = item.clone();
                                        let is_selected = selected_contrib.get().map(|sc| sc.index == item.index).unwrap_or(false);
                                        
                                        view! {
                                            <div
                                                on:click=move |_| set_selected_contrib.set(Some(item_clone.clone()))
                                                style=format!(
                                                    "background: {}; border: 1px solid {}; border-radius: 8px; padding: 14px; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                                                    if is_selected { "#334155" } else { "#1e293b" },
                                                    if is_selected { "#10b981" } else { "#334155" }
                                                )
                                                onmouseover="this.style.transform='translateY(-1px)'"
                                                onmouseout="this.style.transform='none'"
                                            >
                                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                                    <span style="font-weight: 700; font-size: 14px; color: #f8fafc;">"Index #" {item.index}</span>
                                                    <span style="font-size: 11px; font-weight: 600; color: #f59e0b; background: rgba(245, 158, 11, 0.1); padding: 2px 8px; border-radius: 12px;">
                                                        "Staged"
                                                    </span>
                                                </div>
                                                <div style="font-size: 12px; color: #cbd5e1; font-weight: 500; font-family: ui-monospace, monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 4px;">
                                                    {item.address.clone()}
                                                </div>
                                                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #94a3b8; margin-top: 8px;">
                                                    <span>"By: " {format_short_address(&item.contributor)}</span>
                                                    <span>{format_age(item.timestamp)}</span>
                                                </div>
                                            </div>
                                        }
                                    }).collect::<Vec<_>>()}
                                </div>
                            }.into_any()
                        }}
                    </div>
                </div>

                // Right Column: Contribution Detail Inspection View
                <div style="flex: 2; min-width: 420px; background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 18px; display: flex; flex-direction: column; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    {move || if let Some(contrib) = selected_contrib.get() {
                        let idx = contrib.index;
                        let item_age = format_age(contrib.timestamp);
                        view! {
                            <div style="display: flex; flex-direction: column; height: 100%; gap: 16px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 12px;">
                                    <h3 style="margin: 0; font-size: 18px; font-weight: 700; color: #f59e0b;">
                                        "Inspect Contribution Index #" {idx}
                                    </h3>
                                    <div style="font-size: 12px; color: #94a3b8;">"Submitted " {item_age}</div>
                                </div>

                                // Rich Card Metadata details
                                <div style="background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 14px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px 12px; font-size: 13px;">
                                    <span style="color: #94a3b8;">"Building ArxAddress:"</span>
                                    <span style="color: #f8fafc; font-family: ui-monospace, monospace; font-weight: 600; text-align: right;">{contrib.address.clone()}</span>

                                    <span style="color: #94a3b8;">"Contributor Identity:"</span>
                                    <span style="color: #cbd5e1; font-family: ui-monospace, monospace; text-align: right;" title=contrib.contributor.clone()>{format_short_address(&contrib.contributor)}</span>

                                    <span style="color: #94a3b8;">"Change Summary:"</span>
                                    <span style="color: #cbd5e1; font-weight: 500; text-align: right;">{contrib.summary.clone()}</span>

                                    <span style="color: #94a3b8;">"Estimated Reward Bounty:"</span>
                                    <span style="color: #10b981; font-weight: 700; text-align: right;">{contrib.estimated_reward.clone()}</span>
                                </div>

                                // Payout Escrow Split Summary Banner
                                <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2); padding: 12px 16px; border-radius: 8px; font-size: 12px; color: #a7f3d0; line-height: 1.5;">
                                    <strong>"Escrow Reward Split Payout details on approval:"</strong>
                                    <ul style="margin: 6px 0 0 16px; padding: 0;">
                                        <li>"70% directly to Field Workers (Labor incentive)"</li>
                                        <li>"10% directly to Owner (Data rights, owner address below)"</li>
                                        <li>"20% retained in Maintainers pool"</li>
                                    </ul>
                                </div>

                                // YAML details codeviewer box
                                <div style="display: flex; flex-direction: column; gap: 6px;">
                                    <span style="font-size: 12px; font-weight: 600; color: #94a3b8;">"Provisional Building YAML Content"</span>
                                    <div style="background: #090d16; border: 1px solid #1e293b; border-radius: 8px; padding: 14px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 12px; overflow: auto; max-height: 280px; white-space: pre-wrap; color: #38bdf8; line-height: 1.4;">
                                        {contrib.content}
                                    </div>
                                </div>

                                // Action Buttons Panel
                                <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: auto; padding-top: 12px; border-top: 1px solid #334155;">
                                    <button
                                        on:click=move |_| on_reject(idx)
                                        disabled=loading.get()
                                        style="background: #ef4444; color: #ffffff; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; min-height: 44px; display: inline-flex; align-items: center; justify-content: center; font-size: 14px; transition: background 0.2s;"
                                        onmouseover="this.style.background='#dc2626'"
                                        onmouseout="this.style.background='#ef4444'"
                                    >
                                        "Reject & Archive"
                                    </button>
                                    <button
                                        on:click=move |_| on_approve(idx)
                                        disabled=loading.get()
                                        style="background: #10b981; color: #ffffff; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; min-height: 44px; display: inline-flex; align-items: center; justify-content: center; font-size: 14px; transition: background 0.2s;"
                                        onmouseover="this.style.background='#059669'"
                                        onmouseout="this.style.background='#10b981'"
                                    >
                                        "Approve & Merge"
                                    </button>
                                </div>
                            </div>
                        }.into_any()
                    } else {
                        view! {
                            <div style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #64748b; font-size: 14px; text-align: center; min-height: 360px; gap: 12px;">
                                <span style="font-size: 36px;">"🔍"</span>
                                <span style="max-width: 280px; line-height: 1.5;">"Select a pending contribution from the list to inspect its contents, run address promotion checks, and distribute incentives."</span>
                            </div>
                        }.into_any()
                    }}
                </div>
            </div>
        </div>
    }
}
