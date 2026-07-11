use std::net::UdpSocket;
use std::sync::{Arc, Mutex, OnceLock};
use std::thread;
use std::time::{Duration, Instant};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PeerInfo {
    pub peer_id: String,
    pub endpoint: String,
    #[serde(skip)]
    pub last_seen: Option<Instant>,
}

static PEERS: OnceLock<Arc<Mutex<Vec<PeerInfo>>>> = OnceLock::new();

/// Retrieve the dynamic list of discovered local peers
pub fn get_peers() -> Arc<Mutex<Vec<PeerInfo>>> {
    PEERS.get_or_init(|| Arc::new(Mutex::new(Vec::new()))).clone()
}

/// Start background UDP broadcast and listener tasks for local network node discovery
pub fn start_discovery(peer_id: String, port: u16) {
    let peer_id_clone = peer_id.clone();
    
    // 1. Spawner thread for Broadcasting our node endpoint
    thread::spawn(move || {
        let broadcast_addr = "255.255.255.255:8788";
        let payload = serde_json::to_string(&PeerInfo {
            peer_id: peer_id_clone,
            endpoint: format!("http://127.0.0.1:{}", port),
            last_seen: None,
        }).unwrap_or_default();

        // Bind sender socket to any free ephemeral port
        if let Ok(socket) = UdpSocket::bind("0.0.0.0:0") {
            let _ = socket.set_broadcast(true);
            loop {
                let _ = socket.send_to(payload.as_bytes(), broadcast_addr);
                thread::sleep(Duration::from_secs(5));
            }
        }
    });

    // 2. Spawner thread for Listening for broadcasts from other nodes
    thread::spawn(move || {
        if let Ok(socket) = UdpSocket::bind("0.0.0.0:8788") {
            let mut buf = [0u8; 1024];
            loop {
                if let Ok((amt, src)) = socket.recv_from(&mut buf) {
                    if let Ok(mut peer) = serde_json::from_slice::<PeerInfo>(&buf[..amt]) {
                        // Avoid adding self to peers list
                        if peer.peer_id == peer_id {
                            continue;
                        }

                        // Replace localhost IP with actual sender's IP so we can query them
                        if peer.endpoint.contains("127.0.0.1") || peer.endpoint.contains("localhost") {
                            let ip = src.ip().to_string();
                            peer.endpoint = peer.endpoint.replace("127.0.0.1", &ip).replace("localhost", &ip);
                        }
                        
                        peer.last_seen = Some(Instant::now());
                        
                        let peers_list = get_peers();
                        let mut guard = peers_list.lock().unwrap();
                        
                        // Avoid duplicates, keep most recent seen timestamp
                        if let Some(existing) = guard.iter_mut().find(|p| p.peer_id == peer.peer_id) {
                            existing.endpoint = peer.endpoint.clone();
                            existing.last_seen = peer.last_seen;
                        } else {
                            guard.push(peer);
                        }

                        // Prune stale peers (inactive for >15s)
                        let now = Instant::now();
                        guard.retain(|p| {
                            p.last_seen.map(|t| now.duration_since(t) < Duration::from_secs(15)).unwrap_or(false)
                        });
                    }
                }
            }
        }
    });
}
