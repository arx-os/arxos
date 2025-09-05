//! Mobile Offline transports abstraction (BLE/USB placeholders)
//!
//! Provides a trait `MobileTransport` for sending/receiving byte frames
//! to a connected mobile device over an offline medium.

#[derive(Debug)]
pub enum TransportError {
    Io,
    NotConnected,
}

/// Transport abstraction for mobile links (BLE, USB CDC, etc.)
pub trait MobileTransport {
    /// Send one frame (opaque bytes) to the mobile peer
    fn send(&mut self, frame: &[u8]) -> Result<(), TransportError>;
    /// Try to receive one frame; returns None if no data currently available
    fn try_receive(&mut self) -> Option<Vec<u8>>;
}

/// Simple in-memory queue transport for testing and local loopback scenarios.
/// Tests can inspect `sent_frames` and inject with `push_incoming`.
pub struct QueueTransport {
    pub sent_frames: Vec<Vec<u8>>,   // frames sent out (to inspect in tests)
    incoming: Vec<Vec<u8>>,          // frames queued to be received
}

impl QueueTransport {
    pub fn new() -> Self { Self { sent_frames: Vec::new(), incoming: Vec::new() } }
    pub fn push_incoming(&mut self, frame: Vec<u8>) { self.incoming.push(frame); }
}

impl MobileTransport for QueueTransport {
    fn send(&mut self, frame: &[u8]) -> Result<(), TransportError> {
        self.sent_frames.push(frame.to_vec());
        Ok(())
    }
    fn try_receive(&mut self) -> Option<Vec<u8>> {
        if self.incoming.is_empty() { None } else { Some(self.incoming.remove(0)) }
    }
}


