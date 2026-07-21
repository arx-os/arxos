//! Home page — field status + bedroom loop entry

use leptos::prelude::*;
use leptos::{component, view, IntoView};
use leptos_router::components::A;

#[component]
pub fn Home() -> impl IntoView {
    let (tick, set_tick) = create_signal(0u32);

    create_effect(move |_| {
        set_tick.update(|n| *n += 1);
    });

    let status_block = move || {
        let _ = tick.get();
        let online = crate::web::ws_client::is_connected();
        let host = crate::web::ws_client::current_agent_host();
        let err = crate::web::ws_client::last_connection_error();
        let badge = if online {
            ("● Online", "#166534", "#dcfce7")
        } else {
            ("● Offline", "#991b1b", "#fee2e2")
        };
        view! {
            <div style=format!(
                "border-radius: 12px; padding: 14px 16px; margin-bottom: 16px; background: {}; color: {}; border: 1px solid currentColor;",
                badge.2, badge.1
            )>
                <div style="font-weight: 700; font-size: 1.05rem;">{badge.0}</div>
                <div style="margin-top: 6px; font-size: 14px;">
                    "Agent host: " <strong>{host}</strong>
                </div>
                <div style="margin-top: 4px; font-size: 13px; opacity: 0.9;">
                    {if online {
                        "Connected — run bedroom loop: Capture → Label → Review → Export.".to_string()
                    } else if let Some(e) = err {
                        format!("Last error: {}", e)
                    } else {
                        "Enter laptop LAN IP:8787 + token in the header, then Connect. Use http:// PWA (not https) for ws://.".to_string()
                    }}
                </div>
            </div>
        }
    };

    view! {
        <div class="page home-page">
            <h1 style="font-size: 1.4rem; margin: 0 0 8px;">"ArxOS field"</h1>
            <p style="color: #64748b; margin: 0 0 16px; font-size: 15px;">
                "Terminal-style PWA + laptop agent. Capture node holds building.yaml."
            </p>

            {status_block}

            <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px;">
                <A href="/capture" attr:style="display: block; text-align: center; min-height: 48px; line-height: 48px; background: #2563eb; color: white; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 16px;">
                    "1. Capture"
                </A>
                <A href="/label" attr:style="display: block; text-align: center; min-height: 48px; line-height: 48px; background: #0f172a; color: white; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 16px;">
                    "2. Label (fan + switch)"
                </A>
                <A href="/review" attr:style="display: block; text-align: center; min-height: 48px; line-height: 48px; background: #166534; color: white; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 16px;">
                    "3. Review / Validate / Export"
                </A>
            </div>

            <section style="font-size: 14px; color: #475569; line-height: 1.45;">
                <h2 style="font-size: 1rem; color: #0f172a;">"Bedroom loop (≈15 min)"</h2>
                <ol style="padding-left: 1.2rem; margin: 8px 0;">
                    <li>"Laptop: arx init + arx agent in pilot dir"</li>
                    <li>"Phone/browser: Connect (LAN IP + token)"</li>
                    <li>"Capture: Create Bedroom (optional scan upload)"</li>
                    <li>"Label: Ceiling Fan + Light Switch → Accept"</li>
                    <li>"Review: Validate + Export approved_only IFC"</li>
                    <li>"Laptop: confirm building.yaml has both equipment"</li>
                </ol>
                <p style="margin: 8px 0 0;">
                    "Runbook: " <code>"docs/bedroom-loop.md"</code>
                </p>
            </section>
        </div>
    }
}
