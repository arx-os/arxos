# Vendor Integration Guide

ArxOS is designed to be hardware-agnostic. The `HardwareInterface` trait allows third-party vendors and community members to add support for new protocols and devices seamlessly.

## Hardware Interface Trait

All hardware drivers must implement the `HardwareInterface` trait defined in `src/agent/hardware/mod.rs`.

```rust
#[async_trait]
pub trait HardwareInterface: Send + Sync {
    /// Initialize the connection to the hardware
    async fn connect(&mut self) -> Result<()>;
    
    /// Read a value from a specific address/tag
    async fn read(&self, address: &str) -> Result<HardwareValue>;
    
    /// Write a value to a specific address/tag
    async fn write(&mut self, address: &str, value: HardwareValue) -> Result<()>;
    
    /// Disconnect and cleanup
    async fn disconnect(&mut self) -> Result<()>;
}
```

## Adding a New Protocol

1.  **Create Module**: Add a new file in `src/agent/hardware/` (e.g., `knx.rs`).
2.  **Implement Trait**: Implement `HardwareInterface` for your struct.
3.  **Register**: Add your module to `HardwareManager` in `src/agent/hardware/mod.rs`.

### Example: Dummy Protocol

```rust
pub struct DummyDriver;

#[async_trait]
impl HardwareInterface for DummyDriver {
    async fn connect(&mut self) -> Result<()> {
        println!("Dummy driver connected");
        Ok(())
    }

    async fn read(&self, address: &str) -> Result<HardwareValue> {
        Ok(HardwareValue::Float(42.0))
    }
    
    // ...
}
```

## Best Practices

1.  **Async/Await**: Use `async_trait` for all I/O operations to ensure the agent remains responsive.
2.  **Error Handling**: Return descriptive `anyhow::Result` errors.
3.  **Configuration**: Load protocol settings (IPs, baud rates) from the standard `agent.toml` or environment variables.
4.  **Reconnection**: Implement automatic reconnection logic within your `connect` or `read/write` methods if the connection drops.

## Supported Protocols

- **BACnet**: (In Progress) Building Automation and Control Networks.
- **Modbus**: (Planned) Serial and TCP industrial protocol.
- **MQTT**: (Planned) IoT messaging protocol.
