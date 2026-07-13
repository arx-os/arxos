//! Main Leptos App component

use leptos::prelude::*;
use leptos::*;
use leptos_meta::*;
use leptos_router::components::{Route, Router, Routes, A};
use leptos_router::path;

use crate::web::pages::{BuildingDetail, Buildings, Home, Import};
use wasm_bindgen_futures::spawn_local;

#[component]
pub fn App() -> impl IntoView {
    // Provide metadata for the app
    provide_meta_context();

    view! {
        <Stylesheet id="leptos" href="/pkg/arxos.css"/>
        <Title text="ArxOS - Git for Buildings"/>
        <Meta name="description" content="Version control for building management data"/>
        <Meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>

        <Router>
            <div class="app-container" style="min-height: 100vh; font-family: system-ui, -apple-system, sans-serif;">
                <Header/>
                <main class="main-content" style="padding: 12px; max-width: 960px; margin: 0 auto;">
                    <Routes fallback=|| "Not Found">
                        <Route path=path!("/") view=Home/>
                        <Route path=path!("/import") view=Import/>
                        <Route path=path!("/buildings") view=Buildings/>
                        <Route path=path!("/buildings/:id") view=BuildingDetail/>
                    </Routes>
                </main>
            </div>
        </Router>
    }
}

/// Sticky mobile-friendly agent connection strip (Batch A: P0.1–P0.4).
#[component]
fn Header() -> impl IntoView {
    let (connected, set_connected) = create_signal(crate::web::ws_client::is_connected());
    let (host_input, set_host_input) =
        create_signal(crate::web::ws_client::get_saved_agent_host());
    let (token_input, set_token_input) =
        create_signal(crate::web::ws_client::get_saved_token().unwrap_or_default());
    let (status_msg, set_status_msg) = create_signal(String::new());

    // Attempt auto-connect on mount (saved host + token)
    create_effect(move |_| {
        let saved_token = crate::web::ws_client::get_saved_token().unwrap_or_default();
        let saved_host = crate::web::ws_client::get_saved_agent_host();
        if !saved_token.is_empty() && !connected.get() {
            set_status_msg.set(format!("Connecting to {}…", saved_host));
            spawn_local(async move {
                match crate::web::ws_client::connect_to_agent_at(&saved_host, &saved_token).await {
                    Ok(()) => {
                        set_connected.set(true);
                        set_status_msg.set(format!(
                            "Online → {}",
                            crate::web::ws_client::current_agent_host()
                        ));
                    }
                    Err(e) => {
                        set_connected.set(false);
                        set_status_msg.set(format!("Auto-connect failed: {}", e));
                    }
                }
            });
        }
    });

    let connect_action = move |ev: web_sys::SubmitEvent| {
        ev.prevent_default();
        let host = host_input.get();
        let token = token_input.get();
        let host_disp = crate::web::ws_client::normalize_agent_host(&host);
        set_status_msg.set(format!("Connecting to {}…", host_disp));
        spawn_local(async move {
            match crate::web::ws_client::connect_to_agent_at(&host, &token).await {
                Ok(()) => {
                    set_connected.set(true);
                    set_host_input.set(crate::web::ws_client::current_agent_host());
                    set_status_msg.set(format!(
                        "Connected → {}",
                        crate::web::ws_client::current_agent_host()
                    ));
                }
                Err(e) => {
                    set_connected.set(false);
                    set_status_msg.set(format!("Connection failed: {}", e));
                }
            }
        });
    };

    view! {
        <header class="app-header" style="position: sticky; top: 0; z-index: 50; background: #0f172a; color: #f8fafc; padding: 10px 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
            <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; max-width: 960px; margin: 0 auto;">
                <h1 class="app-title" style="margin: 0; font-size: 1.15rem; font-weight: 700;">
                    <A href="/" attr:style="color: #f8fafc; text-decoration: none;">"ArxOS"</A>
                </h1>
                <nav class="main-nav" style="display: flex; flex-wrap: wrap; gap: 8px;">
                    <A href="/" attr:style="color: #cbd5e1; text-decoration: none; padding: 8px 10px; min-height: 44px; display: inline-flex; align-items: center;">"Home"</A>
                    <A href="/import" attr:style="color: #cbd5e1; text-decoration: none; padding: 8px 10px; min-height: 44px; display: inline-flex; align-items: center;">"Import"</A>
                    <A href="/buildings" attr:style="color: #cbd5e1; text-decoration: none; padding: 8px 10px; min-height: 44px; display: inline-flex; align-items: center;">"Buildings"</A>
                </nav>
            </div>

            <form
                on:submit=connect_action
                class="connection-form"
                style="max-width: 960px; margin: 10px auto 0; display: flex; flex-direction: column; gap: 8px;"
            >
                <label style="font-size: 12px; color: #94a3b8;">
                    "Agent host (laptop LAN IP:port — not 127.0.0.1 on iPhone)"
                    <input
                        type="text"
                        inputmode="url"
                        autocomplete="off"
                        autocapitalize="none"
                        placeholder="192.168.x.x:8787"
                        prop:value=host_input
                        on:input=move |ev| set_host_input.set(event_target_value(&ev))
                        style="display: block; width: 100%; box-sizing: border-box; margin-top: 4px; min-height: 44px; padding: 10px 12px; border: 1px solid #334155; border-radius: 8px; font-size: 16px; background: #1e293b; color: #f8fafc;"
                    />
                </label>
                <label style="font-size: 12px; color: #94a3b8;">
                    "Agent token (from laptop agent console)"
                    <input
                        type="text"
                        autocomplete="off"
                        autocapitalize="none"
                        placeholder="did:key:…"
                        prop:value=token_input
                        on:input=move |ev| set_token_input.set(event_target_value(&ev))
                        style="display: block; width: 100%; box-sizing: border-box; margin-top: 4px; min-height: 44px; padding: 10px 12px; border: 1px solid #334155; border-radius: 8px; font-size: 16px; background: #1e293b; color: #f8fafc;"
                    />
                </label>
                <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px;">
                    <button
                        type="submit"
                        style="min-height: 44px; min-width: 120px; padding: 10px 16px; border: none; border-radius: 8px; background: #2563eb; color: white; font-size: 16px; font-weight: 600; cursor: pointer;"
                    >
                        {move || if connected.get() { "Reconnect" } else { "Connect" }}
                    </button>
                    <span style=move || {
                        if connected.get() {
                            "color: #4ade80; font-weight: 700; font-size: 15px;"
                        } else {
                            "color: #f87171; font-weight: 700; font-size: 15px;"
                        }
                    }>
                        {move || if connected.get() { "● Online" } else { "● Offline" }}
                    </span>
                </div>
                <p style="margin: 0; font-size: 13px; color: #94a3b8; word-break: break-word;">
                    {move || status_msg.get()}
                </p>
            </form>
        </header>
    }
}
