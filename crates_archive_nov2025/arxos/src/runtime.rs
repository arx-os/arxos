#![allow(dead_code)]

use alloc::string::String;
use alloc::vec::Vec;

/// Lightweight registry used in `no_std` contexts to track peripheral drivers.
pub struct RuntimeRegistry {
    drivers: Vec<&'static str>,
    notes: Vec<String>,
}

impl RuntimeRegistry {
    /// Create an empty runtime registry.
    pub fn new() -> Self {
        Self {
            drivers: Vec::new(),
            notes: Vec::new(),
        }
    }

    /// Register a driver by symbolic name.
    pub fn register_driver(&mut self, name: &'static str) {
        if !self.drivers.contains(&name) {
            self.drivers.push(name);
        }
    }

    /// Attach a diagnostic note that can be surfaced to host tooling.
    pub fn push_note(&mut self, note: impl Into<String>) {
        self.notes.push(note.into());
    }

    /// Enumerate registered drivers.
    pub fn drivers(&self) -> impl Iterator<Item = &&'static str> {
        self.drivers.iter()
    }

    /// Enumerate diagnostic notes collected during boot or driver init.
    pub fn notes(&self) -> impl Iterator<Item = &String> {
        self.notes.iter()
    }
}

/// Initialise a runtime registry with the core firmware driver set.
pub fn init_runtime() -> RuntimeRegistry {
    let mut registry = RuntimeRegistry::new();
    registry.register_driver("core::scheduler");
    registry.register_driver("core::message_bus");
    registry.push_note("Runtime initialised with lightweight scheduler");
    registry
}
