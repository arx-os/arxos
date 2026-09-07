//! Local-network discovery via mDNS (site use).
//!
//! Service type: `_arxos._udp.local.`
//! TXT keys: `peer`, `building`, `root`, `name`, `objects`
//! (no dial ticket — Iroh tickets do not fit in DNS TXT).

use std::collections::HashMap;
use std::net::IpAddr;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use crate::error::{NetError, Result};
use crate::protocol::BuildingHeadAd;

/// DNS-SD service type for Arxos nodes on the LAN.
pub const SERVICE_TYPE: &str = "_arxos._udp.local.";

/// A discovered peer advertisement.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiscoveredPeer {
    pub instance_name: String,
    pub peer_id: String,
    /// Optional dial ticket / endpoint addr JSON when published.
    pub ticket: Option<String>,
    pub host: Option<String>,
    pub port: u16,
    pub addresses: Vec<IpAddr>,
    pub buildings: Vec<BuildingHeadAd>,
}

/// mDNS announcer + browser (feature `mdns`).
#[cfg(feature = "mdns")]
pub struct MdnsDiscovery {
    daemon: mdns_sd::ServiceDaemon,
    discovered: Arc<Mutex<HashMap<String, DiscoveredPeer>>>,
}

#[cfg(feature = "mdns")]
impl MdnsDiscovery {
    pub fn new() -> Result<Self> {
        let daemon = mdns_sd::ServiceDaemon::new()
            .map_err(|e| NetError::Discovery(format!("mdns daemon: {e}")))?;
        Ok(Self {
            daemon,
            discovered: Arc::new(Mutex::new(HashMap::new())),
        })
    }

    /// Advertise this node. `port` is informational (QUIC uses iroh ports).
    pub fn announce(
        &self,
        instance: &str,
        peer_id: &str,
        port: u16,
        ticket: Option<&str>,
        buildings: &[BuildingHeadAd],
    ) -> Result<()> {
        let _ = ticket; // Iroh tickets do not fit in DNS TXT; copy from serve stdout.
        let props = txt_properties(peer_id, buildings);

        let host_name = format!("{instance}.local.");
        let service = mdns_sd::ServiceInfo::new(
            SERVICE_TYPE,
            instance,
            &host_name,
            "", // let mdns-sd fill addresses
            port,
            Some(props),
        )
        .map_err(|e| NetError::Discovery(format!("service info: {e}")))?
        .enable_addr_auto();

        self.daemon
            .register(service)
            .map_err(|e| NetError::Discovery(format!("register: {e}")))?;
        Ok(())
    }

    /// Browse for peers; updates internal cache. Call repeatedly or spawn.
    pub fn start_browse(&self) -> Result<()> {
        let receiver = self
            .daemon
            .browse(SERVICE_TYPE)
            .map_err(|e| NetError::Discovery(format!("browse: {e}")))?;
        let cache = Arc::clone(&self.discovered);
        std::thread::Builder::new()
            .name("arxos-mdns".into())
            .spawn(move || {
                while let Ok(event) = receiver.recv() {
                    match event {
                        mdns_sd::ServiceEvent::ServiceResolved(info) => {
                            let peer = peer_from_info(&info);
                            if let Ok(mut guard) = cache.lock() {
                                guard.insert(peer.instance_name.clone(), peer);
                            }
                        }
                        mdns_sd::ServiceEvent::ServiceRemoved(_, fullname) => {
                            if let Ok(mut guard) = cache.lock() {
                                guard.retain(|_, p| p.instance_name != fullname);
                            }
                        }
                        _ => {}
                    }
                }
            })
            .map_err(|e| NetError::Discovery(format!("spawn browse: {e}")))?;
        Ok(())
    }

    /// Snapshot of currently discovered peers.
    pub fn peers(&self) -> Vec<DiscoveredPeer> {
        self.discovered
            .lock()
            .map(|g| g.values().cloned().collect())
            .unwrap_or_default()
    }

    /// Wait up to `timeout` for at least one peer (or return current set).
    pub fn wait_for_peers(&self, timeout: Duration) -> Vec<DiscoveredPeer> {
        let start = std::time::Instant::now();
        loop {
            let peers = self.peers();
            if !peers.is_empty() || start.elapsed() >= timeout {
                return peers;
            }
            std::thread::sleep(Duration::from_millis(100));
        }
    }

    pub fn shutdown(&self) -> Result<()> {
        let _ = self.daemon.shutdown();
        Ok(())
    }
}

/// TXT records for LAN discovery. Peer id + advertised heads only — not dial tickets.
pub fn txt_properties(peer_id: &str, buildings: &[BuildingHeadAd]) -> HashMap<String, String> {
    let mut props = HashMap::new();
    props.insert("peer".into(), peer_id.to_string());
    if let Some(b) = buildings.first() {
        props.insert("building".into(), b.building_id.clone());
        props.insert("root".into(), b.root_cid.clone());
        if let Some(n) = &b.name {
            props.insert("name".into(), n.clone());
        }
        props.insert("objects".into(), b.object_count.to_string());
    }
    for (i, b) in buildings.iter().skip(1).take(4).enumerate() {
        props.insert(format!("building{}", i + 2), b.building_id.clone());
        props.insert(format!("root{}", i + 2), b.root_cid.clone());
    }
    props
}

#[cfg(feature = "mdns")]
fn peer_from_info(info: &mdns_sd::ServiceInfo) -> DiscoveredPeer {
    let props = info.get_properties();
    let peer_id = props
        .get_property_val_str("peer")
        .unwrap_or("")
        .to_string();
    let ticket = props
        .get_property_val_str("ticket")
        .map(|s| s.to_string())
        .filter(|s| !s.is_empty() && !s.ends_with('…'));

    let mut buildings = Vec::new();
    if let (Some(b), Some(r)) = (
        props.get_property_val_str("building"),
        props.get_property_val_str("root"),
    ) {
        let objects = props
            .get_property_val_str("objects")
            .and_then(|s| s.parse().ok())
            .unwrap_or(0);
        buildings.push(BuildingHeadAd {
            building_id: b.to_string(),
            root_cid: r.to_string(),
            name: props.get_property_val_str("name").map(|s| s.to_string()),
            object_count: objects,
        });
    }
    for i in 2..=5 {
        let bk = format!("building{i}");
        let rk = format!("root{i}");
        if let (Some(b), Some(r)) = (
            props.get_property_val_str(&bk),
            props.get_property_val_str(&rk),
        ) {
            buildings.push(BuildingHeadAd {
                building_id: b.to_string(),
                root_cid: r.to_string(),
                name: None,
                object_count: 0,
            });
        }
    }

    DiscoveredPeer {
        instance_name: info.get_fullname().to_string(),
        peer_id,
        ticket,
        host: Some(info.get_hostname().to_string()),
        port: info.get_port(),
        addresses: info.get_addresses().iter().copied().collect(),
        buildings,
    }
}

/// Stub when mdns feature is off.
#[cfg(not(feature = "mdns"))]
pub struct MdnsDiscovery;

#[cfg(not(feature = "mdns"))]
impl MdnsDiscovery {
    pub fn new() -> Result<Self> {
        Err(NetError::Discovery(
            "mdns feature not enabled; rebuild with arxos-networking/mdns".into(),
        ))
    }

    pub fn announce(
        &self,
        _instance: &str,
        _peer_id: &str,
        _port: u16,
        _ticket: Option<&str>,
        _buildings: &[BuildingHeadAd],
    ) -> Result<()> {
        Err(NetError::Discovery("mdns disabled".into()))
    }

    pub fn start_browse(&self) -> Result<()> {
        Err(NetError::Discovery("mdns disabled".into()))
    }

    pub fn peers(&self) -> Vec<DiscoveredPeer> {
        Vec::new()
    }

    pub fn wait_for_peers(&self, _timeout: Duration) -> Vec<DiscoveredPeer> {
        Vec::new()
    }

    pub fn shutdown(&self) -> Result<()> {
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn txt_properties_omit_dial_ticket() {
        let ads = vec![BuildingHeadAd {
            building_id: "bid".into(),
            root_cid: "b3:aa".into(),
            name: Some("Hall".into()),
            object_count: 3,
        }];
        let p = txt_properties("peer-1", &ads);
        assert!(!p.contains_key("ticket"));
        assert_eq!(p.get("peer").map(String::as_str), Some("peer-1"));
        assert_eq!(p.get("building").map(String::as_str), Some("bid"));
        assert_eq!(p.get("root").map(String::as_str), Some("b3:aa"));
    }
}
