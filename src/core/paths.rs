//! Cross-platform paths for ArxOS data storage
//!
//! - Windows: %PROGRAMDATA%\ArxOS
//! - macOS: /Library/Application Support/ArxOS
//! - Linux/Unix: /var/lib/arxos

#[cfg(feature = "std")]
use std::path::PathBuf;

#[cfg(feature = "std")]
pub fn data_dir() -> PathBuf {
    if cfg!(target_os = "windows") {
        if let Some(base) = std::env::var_os("PROGRAMDATA") {
            let mut p = PathBuf::from(base);
            p.push("ArxOS");
            p
        } else {
            PathBuf::from(r"C:\\ProgramData\\ArxOS")
        }
    } else if cfg!(target_os = "macos") {
        PathBuf::from("/Library/Application Support/ArxOS")
    } else {
        PathBuf::from("/var/lib/arxos")
    }
}

#[cfg(feature = "std")]
pub fn workspace_db_path(workspace_id: u16) -> PathBuf {
    let mut p = data_dir();
    p.push(format!("vbs_{}.db", workspace_id));
    p
}


