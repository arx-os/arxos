//! Label page: form-based equipment labels (no hand-written text scripts).
//!
//! Bedroom loop presets: Ceiling Fan + Light Switch as proposed, then Accept.

use leptos::prelude::*;
use leptos::*;
use wasm_bindgen_futures::spawn_local;

fn store_report_lines(lines: &[String]) {
    let joined = lines.join("\n");
    if let Some(window) = web_sys::window() {
        if let Ok(Some(storage)) = window.local_storage() {
            let _ = storage.set_item("arx_last_loss_report", &joined);
        }
    }
}

#[component]
pub fn Label() -> impl IntoView {
    let (room, set_room) = create_signal(String::from("Bedroom"));
    let (status, set_status) = create_signal(String::from(
        "Label ceiling fan and light switch, then accept for export.",
    ));
    let (busy, set_busy) = create_signal(false);
    let (report_lines, set_report_lines) = create_signal(Vec::<String>::new());
    let (meta, set_meta) = create_signal(String::new());

    let run_script = move |script: String, ok_msg: String| {
        if !crate::web::ws_client::is_connected() {
            set_status.set("Agent offline — connect in header first.".into());
            return;
        }
        set_busy.set(true);
        set_status.set("Applying labels via edit.apply…".into());
        spawn_local(async move {
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
                    store_report_lines(&lines);
                    set_report_lines.set(lines);
                    set_meta.set(format!(
                        "{} · rooms={} · equip={}",
                        val.get("building_name")
                            .and_then(|v| v.as_str())
                            .unwrap_or("?"),
                        val.get("rooms").and_then(|v| v.as_u64()).unwrap_or(0),
                        val.get("equipment").and_then(|v| v.as_u64()).unwrap_or(0)
                    ));
                    set_status.set(ok_msg);
                    set_busy.set(false);
                }
                Err(e) => {
                    set_status.set(format!("edit.apply failed: {}", e));
                    set_busy.set(false);
                }
            }
        });
    };

    let add_fan = move |_| {
        let r = room.get();
        let script = format!(
            r#"
add equipment "Ceiling Fan" room="{r}" type=electrical
set equipment "Ceiling Fan" review_status=proposed
"#
        );
        run_script(
            script,
            "Ceiling Fan added as proposed. Accept when ready.".into(),
        );
    };

    let add_switch = move |_| {
        let r = room.get();
        let script = format!(
            r#"
add equipment "Light Switch" room="{r}" type=electrical
set equipment "Light Switch" review_status=proposed
"#
        );
        run_script(
            script,
            "Light Switch added as proposed. Accept when ready.".into(),
        );
    };

    let add_both = move |_| {
        let r = room.get();
        if !crate::web::ws_client::is_connected() {
            set_status.set("Agent offline — connect in header first.".into());
            return;
        }
        set_busy.set(true);
        set_status.set("Labeling fan + switch…".into());
        spawn_local(async move {
            // Ensure room (ignore already exists)
            let ensure = format!(r#"add room {r} floor="Ground Floor" type=bedroom"#);
            let _ = crate::web::ws_client::send_rpc(
                "edit.apply",
                serde_json::json!({ "script": ensure }),
            )
            .await;

            let equip_script = format!(
                r#"
add equipment "Ceiling Fan" room="{r}" type=electrical
set equipment "Ceiling Fan" review_status=proposed
add equipment "Light Switch" room="{r}" type=electrical
set equipment "Light Switch" review_status=proposed
"#
            );
            match crate::web::ws_client::send_rpc(
                "edit.apply",
                serde_json::json!({ "script": equip_script }),
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
                    store_report_lines(&lines);
                    set_report_lines.set(lines);
                    set_meta.set(format!(
                        "{} · rooms={} · equip={}",
                        val.get("building_name")
                            .and_then(|v| v.as_str())
                            .unwrap_or("?"),
                        val.get("rooms").and_then(|v| v.as_u64()).unwrap_or(0),
                        val.get("equipment").and_then(|v| v.as_u64()).unwrap_or(0)
                    ));
                    set_status.set(
                        "Ceiling Fan + Light Switch labeled as proposed. Open Review to accept & export."
                            .into(),
                    );
                    set_busy.set(false);
                }
                Err(e) => {
                    set_status.set(format!(
                        "Label failed (one may already exist): {}. Try individual buttons or Review.",
                        e
                    ));
                    set_busy.set(false);
                }
            }
        });
    };

    let accept_both = move |_| {
        let script = r#"
set equipment "Ceiling Fan" review_status=accepted
set equipment "Light Switch" review_status=accepted
"#
        .to_string();
        run_script(
            script,
            "Both objects accepted. Validate + Export from Review.".into(),
        );
    };

    view! {
        <div class="page label-page" style="padding-bottom: 24px;">
            <h1 style="font-size: 1.35rem; margin: 0 0 6px;">"Label"</h1>
            <p style="color: #64748b; font-size: 14px; margin: 0 0 12px;">
                "Form labels → agent edit.apply (text DSL under the hood). No hand-written scripts required."
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

            <p style="font-size: 13px; color: #475569; margin: 0 0 12px; word-break: break-word;">
                {move || status.get()}
            </p>
            {move || {
                let m = meta.get();
                if m.is_empty() {
                    view! { <></> }.into_any()
                } else {
                    view! {
                        <p style="font-size: 13px; font-weight: 600; margin: 0 0 12px;">{m}</p>
                    }.into_any()
                }
            }}

            <label style="display: block; font-size: 13px; color: #64748b; margin-bottom: 12px;">
                "Target room"
                <input
                    type="text"
                    prop:value=move || room.get()
                    on:input=move |ev| set_room.set(event_target_value(&ev))
                    style="display: block; width: 100%; box-sizing: border-box; margin-top: 4px; min-height: 48px; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 10px; font-size: 16px;"
                />
            </label>

            <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px;">
                <button
                    type="button"
                    on:click=add_both
                    prop:disabled=move || busy.get()
                    style="min-height: 48px; border: none; border-radius: 10px; background: #2563eb; color: white; font-size: 16px; font-weight: 600; cursor: pointer;"
                >
                    "Add Ceiling Fan + Light Switch (proposed)"
                </button>
                <button
                    type="button"
                    on:click=add_fan
                    prop:disabled=move || busy.get()
                    style="min-height: 48px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; color: #0f172a; font-size: 15px; font-weight: 600; cursor: pointer;"
                >
                    "Add Ceiling Fan only"
                </button>
                <button
                    type="button"
                    on:click=add_switch
                    prop:disabled=move || busy.get()
                    style="min-height: 48px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; color: #0f172a; font-size: 15px; font-weight: 600; cursor: pointer;"
                >
                    "Add Light Switch only"
                </button>
                <button
                    type="button"
                    on:click=accept_both
                    prop:disabled=move || busy.get()
                    style="min-height: 48px; border: none; border-radius: 10px; background: #166534; color: white; font-size: 16px; font-weight: 600; cursor: pointer;"
                >
                    "Accept both (review_status=accepted)"
                </button>
            </div>

            <section style="padding: 14px; border-radius: 12px; background: #f1f5f9; border: 1px solid #e2e8f0;">
                <h2 style="font-size: 0.95rem; margin: 0 0 8px;">"Last edit report"</h2>
                {move || {
                    let lines = report_lines.get();
                    if lines.is_empty() {
                        view! {
                            <p style="margin: 0; font-size: 13px; color: #64748b;">"No edits yet."</p>
                        }.into_any()
                    } else {
                        view! {
                            <ul style="margin: 0; padding-left: 1.1rem; font-size: 12px; font-family: ui-monospace, monospace;">
                                {lines.into_iter().map(|l| view! { <li>{l}</li> }).collect_view()}
                            </ul>
                        }.into_any()
                    }
                }}
            </section>

            <p style="margin-top: 16px; font-size: 14px;">
                <a href="/review" style="color: #2563eb; font-weight: 600;">"Next → Review hierarchy / Validate / Export"</a>
            </p>
        </div>
    }
}
