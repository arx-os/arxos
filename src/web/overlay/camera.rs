//! Web-sys wrapper for accessing mobile device camera feeds.

/// Camera management wrapper binding video elements to device streams.
pub struct CameraManager;

impl CameraManager {
    pub fn new() -> Self {
        Self
    }

    /// Requests camera stream access and binds it to a local HTMLVideoElement by ID.
    pub fn request_camera_stream(&self, _video_element_id: &str) -> Result<(), String> {
        #[cfg(target_arch = "wasm32")]
        {
            use wasm_bindgen::JsCast;
            
            let window = web_sys::window().ok_or("No global window found")?;
            let navigator = window.navigator();
            let media_devices = navigator.media_devices().map_err(|_| "Media devices unsupported")?;

            // Setup camera constraints (rear facing camera preferred)
            let mut constraints = web_sys::MediaStreamConstraints::new();
            constraints.video(&wasm_bindgen::JsValue::from_str("{\"facingMode\": \"environment\"}"));
            constraints.audio(&wasm_bindgen::JsValue::from_bool(false));

            let promise = media_devices.get_user_media_with_constraints(&constraints)
                .map_err(|_| "Camera request failed")?;

            let video_id = _video_element_id.to_string();
            let future = wasm_bindgen_futures::JsFuture::from(promise);
            wasm_bindgen_futures::spawn_local(async move {
                if let Ok(stream_val) = future.await {
                    let document = web_sys::window().unwrap().document().unwrap();
                    if let Some(el) = document.get_element_by_id(&video_id) {
                        if let Ok(video_el) = el.dyn_into::<web_sys::HtmlVideoElement>() {
                            let stream: web_sys::MediaStream = stream_val.unchecked_into();
                            video_el.set_src_object(Some(&stream));
                            let _ = video_el.play();
                        }
                    }
                }
            });
        }
        Ok(())
    }
}
