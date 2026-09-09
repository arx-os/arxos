//! Local serve control channel (Unix domain socket).
//!
//! Path: `$STORE/meta/serve.sock` (mode 0600). **Not** on Iroh. The serve
//! process binds this after taking `store.lock`. Clients (`inbox apply`) send
//! JSON lines; the lock holder runs [`BuildingRepository::inbox_apply`].
//!
//! Windows: no socket; CLI uses in-process `--local` apply.

use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Error, Result};
use crate::object::BuildingId;
use crate::repository::BuildingRepository;

/// Relative path of the control socket under the store root.
pub const SERVE_SOCK_REL: &str = "meta/serve.sock";

/// `$STORE/meta/serve.sock`
pub fn serve_sock_path(store_root: impl AsRef<Path>) -> PathBuf {
    store_root.as_ref().join(SERVE_SOCK_REL)
}

/// One control request (JSON line).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CtlRequest {
    pub op: String,
    #[serde(default)]
    pub building_id: Option<String>,
    #[serde(default)]
    pub cids: Option<Vec<String>>,
}

/// Reply to a control request.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CtlReply {
    pub ok: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub root_cid: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub object_count: Option<u64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub applied: Option<u64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pending: Option<u64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub rejected: Option<u64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub buildings: Option<Vec<CtlBuildingStatus>>,
}

/// Per-building snapshot for `op=status`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CtlBuildingStatus {
    pub building_id: String,
    pub pending: u64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub head_root: Option<String>,
}

impl CtlReply {
    fn err(msg: impl Into<String>) -> Self {
        Self {
            ok: false,
            error: Some(msg.into()),
            root_cid: None,
            object_count: None,
            applied: None,
            pending: None,
            rejected: None,
            buildings: None,
        }
    }

    fn ok() -> Self {
        Self {
            ok: true,
            error: None,
            root_cid: None,
            object_count: None,
            applied: None,
            pending: None,
            rejected: None,
            buildings: None,
        }
    }
}

/// Run a control op against `store_root`. Caller must already hold `store.lock`.
pub fn handle_ctl(store_root: impl AsRef<Path>, req: &CtlRequest) -> CtlReply {
    match req.op.as_str() {
        "status" => status_reply(store_root.as_ref()),
        "inbox_list" => match req.building_id.as_deref() {
            Some(id) => inbox_list_reply(store_root.as_ref(), id),
            None => CtlReply::err("building_id required"),
        },
        "inbox_apply" => match req.building_id.as_deref() {
            Some(id) => inbox_apply_reply(store_root.as_ref(), id, req.cids.as_deref()),
            None => CtlReply::err("building_id required"),
        },
        "inbox_reject" => match req.building_id.as_deref() {
            Some(id) => inbox_reject_reply(store_root.as_ref(), id, req.cids.as_deref()),
            None => CtlReply::err("building_id required"),
        },
        other => CtlReply::err(format!("unknown op: {other}")),
    }
}

fn parse_bid(id: &str) -> Result<BuildingId> {
    BuildingId::from_str_ok(id)
}

trait BidParse {
    fn from_str_ok(s: &str) -> Result<BuildingId>;
}

impl BidParse for BuildingId {
    fn from_str_ok(s: &str) -> Result<BuildingId> {
        use std::str::FromStr;
        BuildingId::from_str(s)
    }
}

fn status_reply(store_root: &Path) -> CtlReply {
    let list = match BuildingRepository::list_buildings(store_root) {
        Ok(v) => v,
        Err(e) => return CtlReply::err(e.to_string()),
    };
    let mut buildings = Vec::new();
    for rec in list {
        let pending = crate::inbox::load_inbox(store_root, &rec.building_id)
            .map(|f| f.pending.len() as u64)
            .unwrap_or(0);
        buildings.push(CtlBuildingStatus {
            building_id: rec.building_id.to_string(),
            pending,
            head_root: rec.head_root.map(|c| c.to_string()),
        });
    }
    let mut r = CtlReply::ok();
    r.buildings = Some(buildings);
    r
}

fn inbox_list_reply(store_root: &Path, building_id: &str) -> CtlReply {
    let bid = match parse_bid(building_id) {
        Ok(b) => b,
        Err(e) => return CtlReply::err(e.to_string()),
    };
    match crate::inbox::load_inbox(store_root, &bid) {
        Ok(f) => {
            let mut r = CtlReply::ok();
            r.pending = Some(f.pending.len() as u64);
            r
        }
        Err(e) => CtlReply::err(e.to_string()),
    }
}

fn inbox_apply_reply(store_root: &Path, building_id: &str, cids: Option<&[String]>) -> CtlReply {
    let bid = match parse_bid(building_id) {
        Ok(b) => b,
        Err(e) => return CtlReply::err(e.to_string()),
    };
    let mut repo = match BuildingRepository::open_assuming_exclusive(store_root, &bid) {
        Ok(r) => r,
        Err(e) => return CtlReply::err(e.to_string()),
    };
    let only = match parse_cids(cids) {
        Ok(v) => v,
        Err(e) => return CtlReply::err(e),
    };
    match repo.inbox_apply(only.as_ref()) {
        Ok(res) => {
            let mut r = CtlReply::ok();
            r.root_cid = Some(res.commit.root_cid.to_string());
            r.object_count = Some(res.commit.object_count);
            r.applied = Some(res.applied.len() as u64);
            r
        }
        Err(e) => CtlReply::err(e.to_string()),
    }
}

fn inbox_reject_reply(store_root: &Path, building_id: &str, cids: Option<&[String]>) -> CtlReply {
    let bid = match parse_bid(building_id) {
        Ok(b) => b,
        Err(e) => return CtlReply::err(e.to_string()),
    };
    let repo = match BuildingRepository::open_assuming_exclusive(store_root, &bid) {
        Ok(r) => r,
        Err(e) => return CtlReply::err(e.to_string()),
    };
    let Some(set) = (match parse_cids(cids) {
        Ok(v) => v,
        Err(e) => return CtlReply::err(e),
    }) else {
        return CtlReply::err("cids required for inbox_reject");
    };
    match repo.inbox_reject(&set) {
        Ok(n) => {
            let mut r = CtlReply::ok();
            r.rejected = Some(n);
            r
        }
        Err(e) => CtlReply::err(e.to_string()),
    }
}

fn parse_cids(
    cids: Option<&[String]>,
) -> std::result::Result<Option<std::collections::BTreeSet<crate::cid::Cid>>, String> {
    use std::str::FromStr;
    let Some(list) = cids else {
        return Ok(None);
    };
    if list.is_empty() {
        return Ok(None);
    }
    let mut set = std::collections::BTreeSet::new();
    for s in list {
        set.insert(crate::cid::Cid::from_str(s).map_err(|e| e.to_string())?);
    }
    Ok(Some(set))
}

/// Bind the control socket, spawn the accept loop, unlink on drop of the guard.
///
/// Caller must already hold `store.lock`.
#[cfg(unix)]
pub fn spawn_serve_ctl(
    store_root: impl AsRef<Path>,
) -> Result<(
    ServeSockGuard,
    std::sync::Arc<std::sync::atomic::AtomicBool>,
    std::thread::JoinHandle<()>,
)> {
    let root = store_root.as_ref().to_path_buf();
    let listener = bind_serve_ctl(&root)?;
    let stop = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
    let stop2 = std::sync::Arc::clone(&stop);
    let root2 = root.clone();
    let handle = std::thread::Builder::new()
        .name("arxos-ctl".into())
        .spawn(move || serve_ctl_loop(root2, listener, stop2))
        .map_err(|e| Error::Store(format!("spawn serve ctl: {e}")))?;
    Ok((ServeSockGuard::new(&root), stop, handle))
}

#[cfg(not(unix))]
pub fn spawn_serve_ctl(
    _store_root: impl AsRef<Path>,
) -> Result<(
    ServeSockGuard,
    std::sync::Arc<std::sync::atomic::AtomicBool>,
    std::thread::JoinHandle<()>,
)> {
    Err(Error::Store(
        "serve control socket is unix-only".into(),
    ))
}

/// Bind `$STORE/meta/serve.sock`. Caller must already hold `store.lock`.
/// Unlinks a stale socket first. Mode 0600.
#[cfg(unix)]
pub fn bind_serve_ctl(store_root: impl AsRef<Path>) -> Result<std::os::unix::net::UnixListener> {
    use std::os::unix::fs::PermissionsExt;
    use std::os::unix::net::UnixListener;

    let path = serve_sock_path(store_root);
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    if path.exists() {
        std::fs::remove_file(&path)?;
    }
    let listener = UnixListener::bind(&path).map_err(|e| {
        Error::Store(format!("bind serve ctl {}: {e}", path.display()))
    })?;
    std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o600))?;
    Ok(listener)
}

/// Guard that unlinks the control socket on drop.
pub struct ServeSockGuard {
    path: PathBuf,
}

impl ServeSockGuard {
    pub fn new(store_root: impl AsRef<Path>) -> Self {
        Self {
            path: serve_sock_path(store_root),
        }
    }
}

impl Drop for ServeSockGuard {
    fn drop(&mut self) {
        let _ = std::fs::remove_file(&self.path);
    }
}

/// Accept loop: one request per connection, applies serialized on `gate`.
#[cfg(unix)]
pub fn serve_ctl_loop(
    store_root: PathBuf,
    listener: std::os::unix::net::UnixListener,
    stop: std::sync::Arc<std::sync::atomic::AtomicBool>,
) {
    use std::sync::Mutex;

    let gate = Mutex::new(());
    let _ = listener.set_nonblocking(false);
    while !stop.load(std::sync::atomic::Ordering::Relaxed) {
        match listener.accept() {
            Ok((stream, _)) => {
                if stop.load(std::sync::atomic::Ordering::Relaxed) {
                    break;
                }
                let _busy = gate.lock();
                handle_connection(&store_root, stream);
            }
            Err(_) => {
                if stop.load(std::sync::atomic::Ordering::Relaxed) {
                    break;
                }
            }
        }
    }
}

#[cfg(unix)]
fn handle_connection(store_root: &Path, stream: std::os::unix::net::UnixStream) {
    let Ok(writer) = stream.try_clone() else {
        return;
    };
    let mut reader = BufReader::new(stream);
    let mut line = String::new();
    if reader.read_line(&mut line).is_err() {
        return;
    }
    let reply = match serde_json::from_str::<CtlRequest>(line.trim()) {
        Ok(req) => handle_ctl(store_root, &req),
        Err(e) => CtlReply::err(format!("bad json: {e}")),
    };
    let mut writer = writer;
    if let Ok(body) = serde_json::to_string(&reply) {
        let _ = writeln!(writer, "{body}");
        let _ = writer.flush();
    }
}

/// True when a control socket path exists (serve may be up, or a stale sock).
pub fn serve_ctl_path_exists(store_root: impl AsRef<Path>) -> bool {
    serve_sock_path(store_root).exists()
}

/// Send one request. Connect failure means serve is down or the sock is stale.
#[cfg(unix)]
pub fn ctl_send(store_root: impl AsRef<Path>, req: &CtlRequest) -> Result<CtlReply> {
    use std::os::unix::net::UnixStream;

    let path = serve_sock_path(store_root);
    let stream = UnixStream::connect(&path).map_err(|e| {
        Error::Store(format!("connect serve ctl {}: {e}", path.display()))
    })?;
    let mut stream = stream;
    let body = serde_json::to_string(req)
        .map_err(|e| Error::Serialization(format!("ctl request: {e}")))?;
    writeln!(stream, "{body}")?;
    stream.flush()?;
    let mut reader = BufReader::new(stream);
    let mut line = String::new();
    reader.read_line(&mut line)?;
    serde_json::from_str(line.trim())
        .map_err(|e| Error::Deserialization(format!("ctl reply: {e}")))
}

#[cfg(not(unix))]
pub fn ctl_send(_store_root: impl AsRef<Path>, _req: &CtlRequest) -> Result<CtlReply> {
    Err(Error::Store(
        "serve control socket is unix-only; use --local apply".into(),
    ))
}

/// Wake a blocking accept so [`serve_ctl_loop`] can exit.
#[cfg(unix)]
pub fn wake_ctl(store_root: impl AsRef<Path>) {
    use std::os::unix::net::UnixStream;
    let _ = UnixStream::connect(serve_sock_path(store_root));
}

#[cfg(not(unix))]
pub fn wake_ctl(_store_root: impl AsRef<Path>) {}
