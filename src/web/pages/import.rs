//! Import page for IFC file upload

use leptos::*;
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;
use web_sys::Event;

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
                    set_parsing.set(true);
                    set_result.set(None);
                    
                    let file_name_clone = file.name();
                    let file_reader = web_sys::FileReader::new().unwrap();
                    let file_reader_clone = file_reader.clone();
                    
                    let onload = Closure::wrap(Box::new(move |_event: Event| {
                        let text = file_reader_clone.result().unwrap().as_string().unwrap();
                        
                        match crate::web::wasm_bridge::parse_ifc_data(&text) {
                            Ok(json) => {
                                // TODO: Store the building data (e.g. in local storage)
                                // For now, we just show success
                                set_result.set(Some(format!("Successfully parsed: {} ({} bytes)", file_name_clone, text.len())));
                                
                                // Save to local storage for the Buildings page
                                if let Some(window) = web_sys::window() {
                                    if let Ok(Some(storage)) = window.local_storage() {
                                        let _ = storage.set_item("last_imported_building", &json);
                                    }
                                }
                            },
                            Err(e) => {
                                set_result.set(Some(format!("Error parsing IFC: {:?}", e)));
                            }
                        }
                        set_parsing.set(false);
                    }) as Box<dyn FnMut(_)>);
                    
                    file_reader.set_onload(Some(onload.as_ref().unchecked_ref()));
                    file_reader.read_as_text(&file).unwrap();
                    onload.forget();
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
