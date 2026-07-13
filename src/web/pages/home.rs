//! Home page — field status strip (Batch A P0.4)

use leptos::prelude::*;
use leptos::*;
use leptos_router::components::A;

#[component]
pub fn Home() -> impl IntoView {
    let (tick, set_tick) = create_signal(0u32);

    // Light refresh of connection status when navigating home
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
                        "Ready for Batch B review actions once agent RPCs land. Export spine stays on capture node.".to_string()
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
                "iPhone + laptop agent — connect strip above. Capture node holds building.yaml."
            </p>

            {status_block}

            <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px;">
                <A href="/import" attr:style="display: block; text-align: center; min-height: 48px; line-height: 48px; background: #2563eb; color: white; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 16px;">
                    "Import IFC (browser)"
                </A>
                <A href="/buildings" attr:style="display: block; text-align: center; min-height: 48px; line-height: 48px; background: #e2e8f0; color: #0f172a; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 16px;">
                    "View buildings"
                </A>
            </div>

            <section style="font-size: 14px; color: #475569; line-height: 1.45;">
                <h2 style="font-size: 1rem; color: #0f172a;">"Pass A checklist"</h2>
                <ul style="padding-left: 1.2rem; margin: 8px 0;">
                    <li>"Same Wi-Fi/hotspot as laptop"</li>
                    <li>"Agent host = laptop LAN IP:8787 (not 127.0.0.1)"</li>
                    <li>"Token from agent console"</li>
                    <li>"Header shows ● Online"</li>
                </ul>
                <p style="margin: 8px 0 0;">
                    "Docs: " <code>"docs/iphone-field-loop.md"</code>
                </p>
            </section>
        </div>
    }
}
