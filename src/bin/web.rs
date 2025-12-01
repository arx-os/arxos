use leptos::*;
use arxos::web::App;

fn main() {
    // Initialize panic hook for better error messages in browser console
    console_error_panic_hook::set_once();
    
    // Mount the Leptos app
    mount_to_body(|| view! { <App/> })
}
