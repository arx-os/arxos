//! Pilot-oriented import resource limits (R6).
//!
//! Hard-fail with actionable messages instead of silent OOM/hang on edge hardware.
//! Override with env vars when a capture node is intentionally provisioned larger.
//!
//! See `docs/resource-limits.md`.

use anyhow::{bail, Context, Result};
use std::path::Path;

/// Default max IFC file size (matches agent upload ceiling).
pub const DEFAULT_MAX_IFC_BYTES: u64 = 50 * 1024 * 1024;

/// Default max LiDAR file size before parse (raw on disk).
pub const DEFAULT_MAX_LIDAR_BYTES: u64 = 512 * 1024 * 1024;

/// Default max input points counted during voxel filter (before downsampled output).
/// Light mode already bounds voxel map capacity; this caps stream length.
pub const DEFAULT_MAX_LIDAR_INPUT_POINTS: usize = 20_000_000;

fn env_u64(key: &str, default: u64) -> u64 {
    std::env::var(key)
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(default)
}

fn env_usize(key: &str, default: usize) -> usize {
    std::env::var(key)
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(default)
}

/// `ARX_MAX_IFC_BYTES` or [`DEFAULT_MAX_IFC_BYTES`].
pub fn max_ifc_bytes() -> u64 {
    env_u64("ARX_MAX_IFC_BYTES", DEFAULT_MAX_IFC_BYTES)
}

/// `ARX_MAX_LIDAR_BYTES` or [`DEFAULT_MAX_LIDAR_BYTES`].
pub fn max_lidar_bytes() -> u64 {
    env_u64("ARX_MAX_LIDAR_BYTES", DEFAULT_MAX_LIDAR_BYTES)
}

/// `ARX_MAX_LIDAR_INPUT_POINTS` or [`DEFAULT_MAX_LIDAR_INPUT_POINTS`].
pub fn max_lidar_input_points() -> usize {
    env_usize("ARX_MAX_LIDAR_INPUT_POINTS", DEFAULT_MAX_LIDAR_INPUT_POINTS)
}

/// Refuse oversized files before expensive parse.
pub fn check_file_size(path: &Path, max_bytes: u64, kind: &str) -> Result<()> {
    let meta = std::fs::metadata(path)
        .with_context(|| format!("stat {} for size check", path.display()))?;
    let len = meta.len();
    if len > max_bytes {
        bail!(
            "{kind} file too large for pilot defaults: {} ({} bytes) exceeds limit {} bytes. \
             Re-export a lighter model, use a capture node with more RAM, or raise the limit via \
             env (ARX_MAX_IFC_BYTES / ARX_MAX_LIDAR_BYTES). See docs/resource-limits.md.",
            path.display(),
            len,
            max_bytes
        );
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    #[test]
    fn accepts_small_file() {
        let mut f = NamedTempFile::new().unwrap();
        writeln!(f, "ok").unwrap();
        check_file_size(f.path(), 1024, "test").unwrap();
    }

    #[test]
    fn rejects_oversize() {
        let mut f = NamedTempFile::new().unwrap();
        f.write_all(&[0u8; 100]).unwrap();
        let err = check_file_size(f.path(), 10, "test").unwrap_err();
        assert!(err.to_string().contains("too large"));
    }
}
