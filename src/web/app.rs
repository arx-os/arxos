//! Main Leptos App component

use leptos::*;
use leptos::prelude::*;
use leptos_meta::*;
use leptos_router::*;
use leptos_router::components::{A, Router, Routes, Route};
use leptos_router::path;

use crate::web::pages::{Home, Import, Buildings, BuildingDetail};
use wasm_bindgen_futures::spawn_local;

#[component]
pub fn App() -> impl IntoView {
    // Provide metadata for the app
    provide_meta_context();

    view! {
        <Stylesheet id="leptos" href="/pkg/arxos.css"/>
        <Title text="ArxOS - Git for Buildings"/>
        <Meta name="description" content="Version control for building management data"/>
        
        <Router>
            <div class="app-container">
                <Header/>
                <main class="main-content">
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

#[component]
fn Header() -> impl IntoView {
    let (connected, set_connected) = create_signal(crate::web::ws_client::is_connected());
    let (token_input, set_token_input) = create_signal(crate::web::ws_client::get_saved_token().unwrap_or_default());
    let (status_msg, set_status_msg) = create_signal(String::new());

    // Attempt auto-connect on mount
    create_effect(move |_| {
        let saved = crate::web::ws_client::get_saved_token().unwrap_or_default();
        if !saved.is_empty() && !connected.get() {
            set_status_msg.set("Connecting...".to_string());
            spawn_local(async move {
                match crate::web::ws_client::connect_to_agent_async(&saved).await {
                    Ok(()) => {
                        set_connected.set(true);
                        set_status_msg.set("Connected".to_string());
                    }
                    Err(e) => {
                        set_status_msg.set(format!("Auto-connect failed: {}", e));
                    }
                }
            });
        }
    });

    let connect_action = move |ev: web_sys::SubmitEvent| {
        ev.prevent_default();
        let token = token_input.get();
        set_status_msg.set("Connecting...".to_string());
        spawn_local(async move {
            match crate::web::ws_client::connect_to_agent_async(&token).await {
                Ok(()) => {
                    set_connected.set(true);
                    set_status_msg.set("Connected to Agent".to_string());
                }
                Err(e) => {
                    set_connected.set(false);
                    set_status_msg.set(format!("Connection failed: {}", e));
                }
            }
        });
    };

    view! {
        <header class="app-header">
            <div class="header-content">
                <h1 class="app-title">
                    <A href="/">"ArxOS"</A>
                </h1>
                <nav class="main-nav">
                    <A href="/" attr:class="nav-link">"Home"</A>
                    <A href="/import" attr:class="nav-link">"Import"</A>
                    <A href="/buildings" attr:class="nav-link">"Buildings"</A>
                </nav>
                <div class="agent-connection-panel" style="display: flex; align-items: center; gap: 10px; margin-left: auto;">
                    <form on:submit=connect_action class="connection-form" style="display: flex; gap: 5px;">
                        <input
                            type="text"
                            placeholder="Agent Token..."
                            prop:value=token_input
                            on:input=move |ev| set_token_input.set(event_target_value(&ev))
                            class="token-input-field"
                            style="padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 12px; width: 150px;"
                        />
                        <button type="submit" class="btn btn-sm btn-primary" style="padding: 4px 8px; font-size: 12px; cursor: pointer;">
                            {move || if connected.get() { "Reconnect" } else { "Connect" }}
                        </button>
                    </form>
                    <span class=move || if connected.get() { "status-badge connected" } else { "status-badge disconnected" }
                          style=move || if connected.get() { "color: green; font-weight: bold; font-size: 12px;" } else { "color: red; font-weight: bold; font-size: 12px;" }>
                        {move || if connected.get() { "● Online" } else { "● Offline" }}
                    </span>
                    <span class="status-message" style="font-size: 11px; color: #666;">{move || status_msg.get()}</span>
                </div>
            </div>
        </header>
    }
}
