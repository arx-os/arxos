//! Import page for IFC file upload — stores shared BuildingSyncEnvelope.

use leptos::*;
use leptos::prelude::*;
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;
use web_sys::Event;

#[component]
pub fn Import() -> impl IntoView {
    let (file_name, set_file_name) = create_signal(String::new());
    let (parsing, set_parsing) = create_signal(false);
    let (result, set_result) = create_signal(Option::<String>::None);
    let (report_lines, set_report_lines) = create_signal(Vec::<String>::new());

    let on_file_change = move |ev: Event| {
        let input = ev.target().unwrap();
        let input = input.dyn_into::<web_sys::HtmlInputElement>().unwrap();

        if let Some(files) = input.files() {
            if files.length() > 0 {
                if let Some(file) = files.get(0) {
                    set_file_name.set(file.name());
                    set_parsing.set(true);
                    set_result.set(None);
                    set_report_lines.set(Vec::new());

                    let file_name_clone = file.name();
                    let file_reader = web_sys::FileReader::new().unwrap();
                    let file_reader_clone = file_reader.clone();

                    let onload = Closure::wrap(Box::new(move |_event: Event| {
                        let text = file_reader_clone.result().unwrap().as_string().unwrap();

                        match crate::web::wasm_bridge::parse_ifc_data_with_report(&text) {
                            Ok(envelope_json) => {
                                if let Err(e) =
                                    crate::web::wasm_bridge::store_active_building(&envelope_json)
                                {
                                    set_result.set(Some(format!(
                                        "Parsed but failed to store: {:?}",
                                        e
                                    )));
                                } else {
                                    // Surface report lines if present
                                    if let Ok(val) =
                                        serde_json::from_str::<serde_json::Value>(&envelope_json)
                                    {
                                        if let Some(arr) = val.get("report").and_then(|r| r.as_array())
                                        {
                                            let lines: Vec<String> = arr
                                                .iter()
                                                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                                                .collect();
                                            set_report_lines.set(lines);
                                        }
                                        let name = val
                                            .get("building")
                                            .and_then(|b| b.get("name"))
                                            .and_then(|n| n.as_str())
                                            .unwrap_or("building");
                                        set_result.set(Some(format!(
                                            "Imported '{}' from {} ({} bytes) — stored as active building",
                                            name,
                                            file_name_clone,
                                            text.len()
                                        )));
                                    } else {
                                        set_result.set(Some(format!(
                                            "Successfully parsed: {} ({} bytes)",
                                            file_name_clone,
                                            text.len()
                                        )));
                                    }
                                }
                            }
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
            <p>"Upload an Industry Foundation Classes (IFC) file — uses the same native pipeline as the CLI."</p>

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
                    }.into_any()
                } else {
                    view! { <p class="hint">"No file selected"</p> }.into_any()
                }}

                {move || if parsing.get() {
                    view! { <p class="status">"Parsing (native pipeline)..."</p> }.into_any()
                } else {
                    view! { <></> }.into_any()
                }}

                {move || if let Some(msg) = result.get() {
                    view! { <p class="result success">{msg}</p> }.into_any()
                } else {
                    view! { <></> }.into_any()
                }}

                {move || {
                    let lines = report_lines.get();
                    if lines.is_empty() {
                        view! { <></> }.into_any()
                    } else {
                        view! {
                            <div class="report" style="margin-top: 1rem; font-family: monospace; font-size: 12px;">
                                <h3>"Ingest report"</h3>
                                <ul>
                                    {lines.into_iter().map(|l| view! { <li>{l}</li> }).collect_view()}
                                </ul>
                            </div>
                        }.into_any()
                    }
                }}
            </div>
        </div>
    }
}
