//! Import page for IFC file upload

use leptos::*;
use web_sys::{Event, FileList};

#[component]
pub fn Import() -> impl IntoView {
    let (file_name, set_file_name) = create_signal(String::new());
    let (parsing, set_parsing) = create_signal(false);
    let (result, set_result) = create_signal(Option::<String>::None);

    let on_file_change = move |ev: Event| {
        let input = ev.target().unwrap();
        let input = input.dyn_into::<web_sys::HtmlInputElement>().unwrap();
        
        if let Some(files) = input.files() {
            if files.length() > 0 {
                if let Some(file) = files.get(0) {
                    set_file_name.set(file.name());
                    
                    // TODO: Read file and parse with BimParser
                    set_parsing.set(true);
                    
                    // Placeholder for actual parsing
                    set_timeout(
                        move || {
                            set_parsing.set(false);
                            set_result.set(Some(format!("Successfully parsed: {}", file.name())));
                        },
                        std::time::Duration::from_secs(1),
                    );
                }
            }
        }
    };

    view! {
        <div class="page import-page">
            <h1>"Import IFC File"</h1>
            <p>"Upload an Industry Foundation Classes (IFC) file to import building data"</p>

            <div class="upload-section">
                <label for="ifc-upload" class="upload-label">
                    "Choose IFC File"
                </label>
                <input
                    type="file"
                    id="ifc-upload"
                    accept=".ifc"
                    on:change=on_file_change
                    class="file-input"
                />
                
                {move || if !file_name.get().is_empty() {
                    view! {
                        <p class="file-name">"Selected: " {file_name.get()}</p>
                    }.into_view()
                } else {
                    view! { <p class="hint">"No file selected"</p> }.into_view()
                }}
                
                {move || if parsing.get() {
                    view! { <p class="status">"Parsing..."</p> }.into_view()
                } else {
                    view! { <></> }.into_view()
                }}
                
                {move || if let Some(msg) = result.get() {
                    view! { <p class="result success">{msg}</p> }.into_view()
                } else {
                    view! { <></> }.into_view()
                }}
            </div>
        </div>
    }
}
