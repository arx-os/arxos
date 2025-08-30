# Embedded Rust for ESP32

## Building Firmware Without std

### no_std Setup

```rust
#![no_std]
#![no_main]

extern crate panic_halt;
use esp32_hal::prelude::*;
```

### Memory Management

```rust
// Static allocation only
use heapless::{Vec, String};

static mut CACHE: Vec<ArxObject, 100> = Vec::new();
```

### Interrupt Handling

```rust
#[interrupt]
fn LORA_IRQ() {
    // Handle LoRa packet received
    let packet = unsafe { LORA.read_packet() };
    PACKET_QUEUE.enqueue(packet);
}
```

### Power Management

```rust
// Deep sleep between transmissions
esp32_hal::sleep::deep_sleep(Duration::from_secs(30));
```

---

→ Next: [Testing](testing.md)