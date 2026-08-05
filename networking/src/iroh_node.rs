//! Iroh QUIC transport for the Arxos sync protocol.

use std::path::{Path, PathBuf};
use std::str::FromStr;
use std::sync::Arc;

use iroh::endpoint::presets;
use iroh::{Endpoint, EndpointAddr, EndpointId, SecretKey};
use tokio::io::AsyncReadExt;
use tokio::sync::RwLock;

use crate::error::{NetError, Result};
use crate::protocol::{
    decode_message, encode_message, BuildingHeadAd, Message, ObjectBlob, ARXOS_ALPN,
    PROTOCOL_VERSION,
};
use crate::sync::{
    building_ads_from_store, serve_get_object, serve_root_closure_with_options,
};
use crate::transport::{BoxFuture, ObjectTransport, PeerId};

/// Running Iroh node bound to a local object store.
pub struct IrohNode {
    endpoint: Endpoint,
    store_path: PathBuf,
    peer_id: PeerId,
    buildings: Arc<RwLock<Vec<BuildingHeadAd>>>,
}

impl IrohNode {
    /// Bind a new endpoint serving `store_path`.
    pub async fn bind(store_path: impl AsRef<Path>) -> Result<Self> {
        let store_path = store_path.as_ref().to_path_buf();
        let secret = SecretKey::generate();
        let endpoint = Endpoint::builder(presets::N0)
            .secret_key(secret)
            .alpns(vec![ARXOS_ALPN.to_vec()])
            .bind()
            .await
            .map_err(|e| NetError::Transport(format!("iroh bind: {e}")))?;

        let peer_id = endpoint.id().to_string();
        let buildings = building_ads_from_store(&store_path).unwrap_or_default();

        Ok(Self {
            endpoint,
            store_path,
            peer_id,
            buildings: Arc::new(RwLock::new(buildings)),
        })
    }

    /// Bind with an explicit 32-byte seed (deterministic peer id for tests).
    pub async fn bind_with_seed(store_path: impl AsRef<Path>, seed: [u8; 32]) -> Result<Self> {
        let store_path = store_path.as_ref().to_path_buf();
        let secret = SecretKey::from_bytes(&seed);
        let endpoint = Endpoint::builder(presets::N0)
            .secret_key(secret)
            .alpns(vec![ARXOS_ALPN.to_vec()])
            .bind()
            .await
            .map_err(|e| NetError::Transport(format!("iroh bind: {e}")))?;

        let peer_id = endpoint.id().to_string();
        let buildings = building_ads_from_store(&store_path).unwrap_or_default();

        Ok(Self {
            endpoint,
            store_path,
            peer_id,
            buildings: Arc::new(RwLock::new(buildings)),
        })
    }

    pub fn peer_id(&self) -> &PeerId {
        &self.peer_id
    }

    pub fn endpoint_id(&self) -> EndpointId {
        self.endpoint.id()
    }

    pub fn store_path(&self) -> &Path {
        &self.store_path
    }

    /// Endpoint address for dialing (includes home relay when available).
    pub async fn endpoint_addr(&self) -> EndpointAddr {
        self.endpoint.addr()
    }

    /// Human-readable ticket: endpoint id + serialized addr JSON (base64 not required).
    pub async fn ticket(&self) -> Result<String> {
        let addr = self.endpoint_addr().await;
        let json = serde_json::to_string(&addr)
            .map_err(|e| NetError::Serialization(e.to_string()))?;
        Ok(json)
    }

    pub async fn refresh_buildings(&self) -> Result<()> {
        let ads = building_ads_from_store(&self.store_path)?;
        *self.buildings.write().await = ads;
        Ok(())
    }

    pub async fn set_buildings(&self, ads: Vec<BuildingHeadAd>) {
        *self.buildings.write().await = ads;
    }

    /// Accept loop — spawn and cancel via dropping the task / closing endpoint.
    pub async fn accept_loop(self: Arc<Self>) -> Result<()> {
        loop {
            let incoming = self
                .endpoint
                .accept()
                .await
                .ok_or_else(|| NetError::Transport("endpoint closed".into()))?;
            let connecting = incoming
                .await
                .map_err(|e| NetError::Transport(format!("accept: {e}")))?;
            let node = Arc::clone(&self);
            tokio::spawn(async move {
                if let Err(e) = node.handle_connection(connecting).await {
                    tracing::warn!("connection handler error: {e}");
                }
            });
        }
    }

    async fn handle_connection(&self, conn: iroh::endpoint::Connection) -> Result<()> {
        loop {
            let (mut send, mut recv) = match conn.accept_bi().await {
                Ok(s) => s,
                Err(_) => break, // connection closed
            };
            let req = read_message(&mut recv).await?;
            let resp = self.handle_message(req).await;
            let enc = encode_message(&resp).map_err(NetError::Protocol)?;
            send.write_all(&enc)
                .await
                .map_err(|e| NetError::Transport(e.to_string()))?;
            send.finish()
                .map_err(|e| NetError::Transport(e.to_string()))?;
        }
        Ok(())
    }

    async fn handle_message(&self, msg: Message) -> Message {
        match msg {
            Message::Hello { .. } => Message::Hello {
                protocol_version: PROTOCOL_VERSION,
                peer_id: self.peer_id.clone(),
                buildings: self.buildings.read().await.clone(),
            },
            Message::GetObject { cid } => match serve_get_object(&self.store_path, &cid) {
                Ok(Some(bytes)) => Message::GetObjectOk { cid, bytes },
                Ok(None) => Message::GetObjectMissing { cid },
                Err(e) => Message::Error {
                    message: e.to_string(),
                },
            },
            Message::GetRootClosure {
                root_cid,
                include_blobs,
            } => match serve_root_closure_with_options(
                &self.store_path,
                &root_cid,
                include_blobs,
            ) {
                Ok(objects) => Message::RootClosure { root_cid, objects },
                Err(e) => Message::Error {
                    message: e.to_string(),
                },
            },
            Message::AnnounceRoot {
                building_id,
                root_cid,
                object_count,
                ..
            } => {
                let mut ads = self.buildings.write().await;
                if let Some(ad) = ads.iter_mut().find(|a| a.building_id == building_id) {
                    ad.root_cid = root_cid;
                    ad.object_count = object_count;
                } else {
                    ads.push(BuildingHeadAd {
                        building_id,
                        root_cid,
                        name: None,
                        object_count,
                    });
                }
                Message::Ok {
                    detail: Some("announced".into()),
                }
            }
            other => Message::Error {
                message: format!("unexpected request: {other:?}"),
            },
        }
    }

    async fn request(&self, addr: EndpointAddr, msg: Message) -> Result<Message> {
        let conn = self
            .endpoint
            .connect(addr, ARXOS_ALPN)
            .await
            .map_err(|e| NetError::Transport(format!("connect: {e}")))?;
        let (mut send, mut recv) = conn
            .open_bi()
            .await
            .map_err(|e| NetError::Transport(format!("open_bi: {e}")))?;
        let enc = encode_message(&msg).map_err(NetError::Protocol)?;
        // Must write before remote accept_bi returns.
        send.write_all(&enc)
            .await
            .map_err(|e| NetError::Transport(e.to_string()))?;
        send.finish()
            .map_err(|e| NetError::Transport(e.to_string()))?;
        let resp = read_message(&mut recv).await?;
        conn.close(0u32.into(), b"done");
        Ok(resp)
    }

    /// Parse a ticket (JSON EndpointAddr) produced by [`Self::ticket`].
    pub fn parse_ticket(ticket: &str) -> Result<EndpointAddr> {
        serde_json::from_str(ticket).map_err(|e| NetError::Protocol(format!("bad ticket: {e}")))
    }

    /// Fetch object from peer ticket.
    pub async fn fetch_object_ticket(
        &self,
        ticket: &str,
        cid: &str,
    ) -> Result<Option<Vec<u8>>> {
        let addr = Self::parse_ticket(ticket)?;
        match self
            .request(
                addr,
                Message::GetObject {
                    cid: cid.to_string(),
                },
            )
            .await?
        {
            Message::GetObjectOk { bytes, .. } => Ok(Some(bytes)),
            Message::GetObjectMissing { .. } => Ok(None),
            Message::Error { message } => Err(NetError::Transport(message)),
            other => Err(NetError::Protocol(format!("unexpected: {other:?}"))),
        }
    }

    pub async fn fetch_root_closure_ticket(
        &self,
        ticket: &str,
        root_cid: &str,
    ) -> Result<Vec<ObjectBlob>> {
        self.fetch_root_closure_ticket_with_options(ticket, root_cid, true)
            .await
    }

    pub async fn fetch_root_closure_ticket_with_options(
        &self,
        ticket: &str,
        root_cid: &str,
        include_blobs: bool,
    ) -> Result<Vec<ObjectBlob>> {
        let addr = Self::parse_ticket(ticket)?;
        match self
            .request(
                addr,
                Message::GetRootClosure {
                    root_cid: root_cid.to_string(),
                    include_blobs,
                },
            )
            .await?
        {
            Message::RootClosure { objects, .. } => Ok(objects),
            Message::Error { message } => Err(NetError::Transport(message)),
            other => Err(NetError::Protocol(format!("unexpected: {other:?}"))),
        }
    }

    pub async fn hello_ticket(&self, ticket: &str) -> Result<Message> {
        let addr = Self::parse_ticket(ticket)?;
        self.request(
            addr,
            Message::Hello {
                protocol_version: PROTOCOL_VERSION,
                peer_id: self.peer_id.clone(),
                buildings: self.buildings.read().await.clone(),
            },
        )
        .await
    }

    /// Gracefully close the endpoint.
    pub async fn close(&self) {
        self.endpoint.close().await;
    }
}

async fn read_message<R: AsyncReadExt + Unpin>(reader: &mut R) -> Result<Message> {
    let mut len_buf = [0u8; 4];
    reader
        .read_exact(&mut len_buf)
        .await
        .map_err(|e| NetError::Transport(format!("read len: {e}")))?;
    let len = u32::from_be_bytes(len_buf);
    if len > crate::protocol::MAX_MESSAGE_BYTES {
        return Err(NetError::Protocol(format!("message too large: {len}")));
    }
    let mut body = vec![0u8; len as usize];
    reader
        .read_exact(&mut body)
        .await
        .map_err(|e| NetError::Transport(format!("read body: {e}")))?;
    let mut framed = Vec::with_capacity(4 + body.len());
    framed.extend_from_slice(&len_buf);
    framed.extend_from_slice(&body);
    match decode_message(&framed).map_err(NetError::Protocol)? {
        Some((msg, _)) => Ok(msg),
        None => Err(NetError::Protocol("incomplete message".into())),
    }
}

/// Transport adapter: peer id is an EndpointAddr JSON ticket.
impl ObjectTransport for IrohNode {
    fn local_peer_id(&self) -> PeerId {
        self.peer_id.clone()
    }

    fn advertise_buildings(&self) -> BoxFuture<'_, Result<Vec<BuildingHeadAd>>> {
        Box::pin(async move { Ok(self.buildings.read().await.clone()) })
    }

    fn fetch_object<'a>(
        &'a self,
        peer: &'a PeerId,
        cid: &'a str,
    ) -> BoxFuture<'a, Result<Option<Vec<u8>>>> {
        Box::pin(async move { self.fetch_object_ticket(peer, cid).await })
    }

    fn fetch_root_closure_with_options<'a>(
        &'a self,
        peer: &'a PeerId,
        root_cid: &'a str,
        include_blobs: bool,
    ) -> BoxFuture<'a, Result<Vec<ObjectBlob>>> {
        Box::pin(async move {
            self.fetch_root_closure_ticket_with_options(peer, root_cid, include_blobs)
                .await
        })
    }

    fn announce_root<'a>(
        &'a self,
        peer: &'a PeerId,
        building_id: &'a str,
        root_cid: &'a str,
        object_count: u64,
        message: Option<String>,
    ) -> BoxFuture<'a, Result<()>> {
        Box::pin(async move {
            let addr = Self::parse_ticket(peer)?;
            let resp = self
                .request(
                    addr,
                    Message::AnnounceRoot {
                        building_id: building_id.to_string(),
                        root_cid: root_cid.to_string(),
                        object_count,
                        message,
                    },
                )
                .await?;
            match resp {
                Message::Ok { .. } => Ok(()),
                Message::Error { message } => Err(NetError::Transport(message)),
                other => Err(NetError::Protocol(format!("unexpected: {other:?}"))),
            }
        })
    }
}

/// Parse EndpointId from hex/string if needed.
#[allow(dead_code)]
pub fn parse_endpoint_id(s: &str) -> Result<EndpointId> {
    EndpointId::from_str(s).map_err(|e| NetError::Protocol(format!("endpoint id: {e}")))
}
