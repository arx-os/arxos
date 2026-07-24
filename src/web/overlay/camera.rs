//! getUserMedia camera helper for Create New (room capture).
//!
//! Prefers `facingMode: "environment"` (rear camera) for room scanning.
//! Requires a **secure context**: HTTPS or localhost. See docs/create-new-camera.md.

use std::cell::RefCell;

use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;
use wasm_bindgen_futures::JsFuture;

const VIDEO_ID: &str = "arx-create-new-video";
const CANVAS_ID: &str = "arx-create-new-canvas";

thread_local! {
    static ACTIVE_STREAM: RefCell<Option<web_sys::MediaStream>> = const { RefCell::new(None) };
}

/// Camera management wrapper binding video elements to device streams.
#[derive(Default)]
pub struct CameraManager;

impl CameraManager {
    pub fn new() -> Self {
        Self
    }

    /// Default video element id used by the Capture page.
    pub fn video_element_id() -> &'static str {
        VIDEO_ID
    }

    pub fn canvas_element_id() -> &'static str {
        CANVAS_ID
    }

    /// Whether the page is a secure context (required for getUserMedia on most browsers).
    pub fn is_secure_context() -> bool {
        web_sys::window()
            .and_then(|w| js_sys::Reflect::get(&w, &JsValue::from_str("isSecureContext")).ok())
            .and_then(|v| v.as_bool())
            .unwrap_or(false)
    }

    /// Stop any active camera tracks and clear srcObject on the video element.
    pub fn stop_camera() {
        ACTIVE_STREAM.with(|cell| {
            if let Some(stream) = cell.borrow_mut().take() {
                let tracks = stream.get_tracks();
                for i in 0..tracks.length() {
                    if let Ok(track) = tracks.get(i).dyn_into::<web_sys::MediaStreamTrack>() {
                        track.stop();
                    }
                }
            }
        });
        if let Some(video) = document_video(VIDEO_ID) {
            video.set_src_object(None);
        }
    }

    /// Request rear-facing camera (fallback: any video), bind to `#arx-create-new-video`.
    pub async fn start_preview() -> Result<(), String> {
        Self::stop_camera();

        if !Self::is_secure_context() {
            return Err(
                "Camera requires a secure context (HTTPS or http://localhost). \
                 On a phone over LAN HTTP, getUserMedia is blocked. \
                 Serve the PWA over HTTPS — see docs/create-new-camera.md."
                    .into(),
            );
        }

        let window = web_sys::window().ok_or("No window")?;
        let navigator = window.navigator();
        let media_devices = navigator
            .media_devices()
            .map_err(|_| "MediaDevices API unavailable (insecure context or unsupported browser)".to_string())?;

        // Prefer environment (rear) camera for room scanning.
        let stream = match request_stream(&media_devices, true).await {
            Ok(s) => s,
            Err(env_err) => match request_stream(&media_devices, false).await {
                Ok(s) => s,
                Err(any_err) => {
                    return Err(format!(
                        "getUserMedia failed (environment: {}; any: {})",
                        env_err, any_err
                    ));
                }
            },
        };

        let video = document_video(VIDEO_ID)
            .ok_or_else(|| format!("Missing <video id=\"{}\">", VIDEO_ID))?;
        video.set_autoplay(true);
        video.set_muted(true);
        let _ = video.set_attribute("playsinline", "true");
        video.set_src_object(Some(&stream));
        let play_promise = video.play().map_err(|e| format!("video.play failed: {:?}", e))?;
        let _ = JsFuture::from(play_promise).await;

        ACTIVE_STREAM.with(|cell| *cell.borrow_mut() = Some(stream));
        Ok(())
    }

    /// Capture one JPEG frame (base64, no data-URL prefix) from the live preview.
    ///
    /// Scales down so the long edge is at most `max_edge` pixels (default 1280).
    pub fn capture_jpeg_base64(max_edge: u32) -> Result<String, String> {
        let video = document_video(VIDEO_ID).ok_or("Video element not found")?;
        let vw = video.video_width();
        let vh = video.video_height();
        if vw == 0 || vh == 0 {
            return Err("Camera not ready (video dimensions 0 — wait for preview)".into());
        }

        let max_edge = if max_edge == 0 { 1280 } else { max_edge };
        let (cw, ch) = scaled_size(vw, vh, max_edge);

        let canvas = document_canvas(CANVAS_ID).ok_or("Canvas element not found")?;
        canvas.set_width(cw);
        canvas.set_height(ch);

        let ctx = canvas
            .get_context("2d")
            .map_err(|e| format!("{:?}", e))?
            .ok_or("2d context unavailable")?
            .dyn_into::<web_sys::CanvasRenderingContext2d>()
            .map_err(|_| "Not a CanvasRenderingContext2d")?;

        ctx.draw_image_with_html_video_element_and_dw_and_dh(&video, 0.0, 0.0, cw as f64, ch as f64)
            .map_err(|e| format!("drawImage failed: {:?}", e))?;

        let data_url = canvas
            .to_data_url_with_type("image/jpeg")
            .map_err(|e| format!("toDataURL failed: {:?}", e))?;

        strip_data_url_base64(&data_url)
    }

    /// Capture `count` frames with a short delay between them (burst).
    pub async fn capture_burst(count: u32, max_edge: u32) -> Result<Vec<String>, String> {
        let n = count.clamp(1, 8);
        let mut frames = Vec::with_capacity(n as usize);
        for i in 0..n {
            if i > 0 {
                // ~180ms between burst frames
                sleep_ms(180).await;
            }
            frames.push(Self::capture_jpeg_base64(max_edge)?);
        }
        Ok(frames)
    }

    /// Backward-compatible fire-and-forget bind (legacy overlay).
    pub fn request_camera_stream(&self, video_element_id: &str) -> Result<(), String> {
        let id = video_element_id.to_string();
        wasm_bindgen_futures::spawn_local(async move {
            let _ = start_preview_on_id(&id).await;
        });
        Ok(())
    }
}

async fn start_preview_on_id(video_id: &str) -> Result<(), String> {
    if !CameraManager::is_secure_context() {
        return Err("Insecure context".into());
    }
    let window = web_sys::window().ok_or("No window")?;
    let media_devices = window
        .navigator()
        .media_devices()
        .map_err(|_| "MediaDevices unavailable".to_string())?;
    let stream = request_stream(&media_devices, true)
        .await
        .or(request_stream(&media_devices, false).await)?;
    if let Some(video) = document_video(video_id) {
        video.set_src_object(Some(&stream));
        let _ = video.play();
        ACTIVE_STREAM.with(|cell| *cell.borrow_mut() = Some(stream));
    }
    Ok(())
}

async fn request_stream(
    media_devices: &web_sys::MediaDevices,
    environment: bool,
) -> Result<web_sys::MediaStream, String> {
    let constraints = web_sys::MediaStreamConstraints::new();
    constraints.set_audio(&JsValue::FALSE);

    if environment {
        // facingMode ideal environment
        let video = js_sys::Object::new();
        let facing = js_sys::Object::new();
        let _ = js_sys::Reflect::set(
            &facing,
            &JsValue::from_str("ideal"),
            &JsValue::from_str("environment"),
        );
        let _ = js_sys::Reflect::set(&video, &JsValue::from_str("facingMode"), &facing);
        constraints.set_video(&video);
    } else {
        constraints.set_video(&JsValue::TRUE);
    }

    let promise = media_devices
        .get_user_media_with_constraints(&constraints)
        .map_err(|e| format!("{:?}", e))?;
    let stream_val = JsFuture::from(promise)
        .await
        .map_err(|e| format!("{:?}", e))?;
    stream_val
        .dyn_into::<web_sys::MediaStream>()
        .map_err(|_| "Result was not a MediaStream".to_string())
}

fn document_video(id: &str) -> Option<web_sys::HtmlVideoElement> {
    web_sys::window()?
        .document()?
        .get_element_by_id(id)?
        .dyn_into()
        .ok()
}

fn document_canvas(id: &str) -> Option<web_sys::HtmlCanvasElement> {
    web_sys::window()?
        .document()?
        .get_element_by_id(id)?
        .dyn_into()
        .ok()
}

fn scaled_size(w: u32, h: u32, max_edge: u32) -> (u32, u32) {
    let long = w.max(h);
    if long <= max_edge {
        return (w, h);
    }
    let scale = max_edge as f64 / long as f64;
    (
        ((w as f64) * scale).round().max(1.0) as u32,
        ((h as f64) * scale).round().max(1.0) as u32,
    )
}

fn strip_data_url_base64(data_url: &str) -> Result<String, String> {
    let idx = data_url
        .find("base64,")
        .ok_or_else(|| "toDataURL did not return base64".to_string())?;
    Ok(data_url[idx + "base64,".len()..].to_string())
}

async fn sleep_ms(ms: i32) {
    let promise = js_sys::Promise::new(&mut |resolve, _reject| {
        if let Some(window) = web_sys::window() {
            let _ = window.set_timeout_with_callback_and_timeout_and_arguments_0(&resolve, ms);
        } else {
            let _ = resolve.call0(&JsValue::NULL);
        }
    });
    let _ = JsFuture::from(promise).await;
}
