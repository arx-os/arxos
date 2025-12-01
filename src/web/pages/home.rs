//! Home page

use leptos::*;
use leptos_router::*;

#[component]
pub fn Home() -> impl IntoView {
    view! {
        <div class="page home-page">
            <div class="hero">
                <h1>"Welcome to ArxOS"</h1>
                <p class="subtitle">"Git for Buildings - Version control for building management data"</p>
                
                <div class="cta-buttons">
                    <A href="/import" class="btn btn-primary">
                        "Import IFC File"
                    </A>
                    <A href="/buildings" class="btn btn-secondary">
                        "View Buildings"
                    </A>
                </div>
            </div>

            <div class="features">
                <div class="feature-card">
                    <h3>"🏗️ IFC Import"</h3>
                    <p>"Import Industry Foundation Classes (IFC) files directly in your browser"</p>
                </div>
                <div class="feature-card">
                    <h3>"📊 Version Control"</h3>
                    <p>"Track changes to building data with Git-based version control"</p>
                </div>
                <div class="feature-card">
                    <h3>"🌐 Offline First"</h3>
                    <p>"Works offline as a Progressive Web App"</p>
                </div>
            </div>
        </div>
    }
}
