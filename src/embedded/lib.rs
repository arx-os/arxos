//! Arxos Embedded Library
//! 
//! For running on ESP32, STM32, and other microcontrollers

#![no_std]

use arxos_core::ArxObject;
use heapless::Vec;

/// Cache for storing ArxObjects in no_std environment
pub struct ArxCache {
    objects: Vec<ArxObject, 100>,
}

impl ArxCache {
    pub fn new() -> Self {
        Self {
            objects: Vec::new(),
        }
    }

    pub fn insert(&mut self, obj: ArxObject) -> Result<(), ArxObject> {
        self.objects.push(obj).map_err(|e| e)
    }

    pub fn get(&self, id: u16) -> Option<&ArxObject> {
        self.objects.iter().find(|obj| obj.id == id)
    }

    pub fn clear(&mut self) {
        self.objects.clear();
    }
}