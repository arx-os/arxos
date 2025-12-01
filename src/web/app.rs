//! Main Leptos App component

use leptos::*;
use leptos_meta::*;
use leptos_router::*;

use crate::web::pages::{Home, Import, Buildings, BuildingDetail};

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
                    <Routes>
                        <Route path="/" view=Home/>
                        <Route path="/import" view=Import/>
                        <Route path="/buildings" view=Buildings/>
                        <Route path="/buildings/:id" view=BuildingDetail/>
                    </Routes>
                </main>
            </div>
        </Router>
    }
}

#[component]
fn Header() -> impl IntoView {
    view! {
        <header class="app-header">
            <div class="header-content">
                <h1 class="app-title">
                    <A href="/">"ArxOS"</A>
                </h1>
                <nav class="main-nav">
                    <A href="/" class="nav-link">"Home"</A>
                    <A href="/import" class="nav-link">"Import"</A>
                    <A href="/buildings" class="nav-link">"Buildings"</A>
                </nav>
            </div>
        </header>
    }
}
