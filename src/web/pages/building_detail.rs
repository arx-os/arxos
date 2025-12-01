//! Building detail page

use leptos::*;
use leptos_router::*;

#[component]
pub fn BuildingDetail() -> impl IntoView {
    let params = use_params_map();
    let id = move || params.with(|p| p.get("id").cloned().unwrap_or_default());

    view! {
        <div class="page building-detail-page">
            <h1>"Building Details"</h1>
            <p>"ID: " {id}</p>

            <div class="building-info">
                <h2>"Building Information"</h2>
                <p>"Name: Sample Building"</p>
                <p>"Floors: 3"</p>
                <p>"Rooms: 45"</p>
                <p>"Equipment: 120"</p>
            </div>

            <div class="actions">
                <button class="btn btn-primary">"Export"</button>
                <button class="btn btn-secondary">"3D View"</button>
            </div>
        </div>
    }
}
