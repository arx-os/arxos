//! Replay protection window to prevent acceptance of old frames.
//! Maintains a sliding window of recently seen nonces per sender.

use std::collections::{HashMap, VecDeque};

/// Replay window per sender (by u16 sender id)
pub struct ReplayWindow {
    /// Max entries to keep per sender
    capacity: usize,
    /// Map of sender -> queue of seen nonces (u32 timestamp + u16 counter packed optional)
    seen: HashMap<u16, VecDeque<u64>>, // store combined nonce tokens
}

impl ReplayWindow {
    pub fn new(capacity: usize) -> Self {
        Self { capacity, seen: HashMap::new() }
    }

    /// Check if `token` for `sender` is new. If new, record and return true; else false.
    pub fn accept(&mut self, sender: u16, token: u64) -> bool {
        let q = self.seen.entry(sender).or_insert_with(VecDeque::new);
        if q.contains(&token) {
            return false;
        }
        q.push_back(token);
        while q.len() > self.capacity { q.pop_front(); }
        true
    }
}


