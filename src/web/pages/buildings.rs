use leptos::*;
use leptos::prelude::*;
use leptos_router::components::A;
use crate::core::Building;

#[component]
pub fn Buildings() -> impl IntoView {
    let (buildings, set_buildings) = create_signal(Vec::<Building>::new());

    create_effect(move |_| {
        // Prefer canonical sync envelope; fall back to legacy bare Building JSON
        if let Ok(envelope_json) = crate::web::wasm_bridge::load_active_building() {
            if let Ok(building_json) =
                crate::web::wasm_bridge::building_json_from_envelope(&envelope_json)
            {
                if let Ok(building) = serde_json::from_str::<Building>(&building_json) {
                    set_buildings.set(vec![building]);
                    return;
                }
            }
        }
        if let Some(window) = web_sys::window() {
            if let Ok(Some(storage)) = window.local_storage() {
                if let Ok(Some(json)) = storage.get_item("last_imported_building") {
                    if let Ok(building) = serde_json::from_str::<Building>(&json) {
                        set_buildings.set(vec![building]);
                    }
                }
            }
        }
    });

    view! {
        <div class="page buildings-page">
            <h1>"Buildings"</h1>
            <p>"Manage your building data"</p>

            <div class="buildings-list">
                {move || buildings.get().into_iter().map(|building| {
                    view! {
                        <div class="building-card">
                            <h3>{building.name}</h3>
                            <p class="building-id">"ID: " {building.id.clone()}</p>
                            <A href=format!("/buildings/{}", building.id) attr:class="btn btn-sm">
                                "View Details"
                            </A>
                        </div>
                    }
                }).collect_view()}
                
                {move || if buildings.get().is_empty() {
                    view! { 
                        <div class="empty-state">
                            <p>"No buildings found."</p>
                            <A href="/import" attr:class="btn btn-primary">"Import a Building"</A>
                        </div>
                    }.into_any()
                } else {
                    view! { <></> }.into_any()
                }}
            </div>
        </div>
    }
}
