//! Buildings list page

use leptos::*;
use leptos_router::*;

#[component]
pub fn Buildings() -> impl IntoView {
    // TODO: Load buildings from local storage or agent
    let buildings = vec![
        ("building-1", "Sample Building"),
        ("building-2", "Office Complex"),
    ];

    view! {
        <div class="page buildings-page">
            <h1>"Buildings"</h1>
            <p>"Manage your building data"</p>

            <div class="buildings-list">
                {buildings.into_iter().map(|(id, name)| {
                    view! {
                        <div class="building-card">
                            <h3>{name}</h3>
                            <A href=format!("/buildings/{}", id) class="btn btn-sm">
                                "View Details"
                            </A>
                        </div>
                    }
                }).collect_view()}
            </div>
        </div>
    }
}
