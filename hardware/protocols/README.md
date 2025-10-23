# ArxOS Hardware Protocols

This directory contains communication protocol implementations for hardware integration.

## 📁 Structure

```
protocols/
├── src/
│   ├── lib.rs          # Main library file
│   ├── github_api.rs   # GitHub API integration
│   ├── mqtt.rs         # MQTT broker integration
│   ├── webhook.rs      # Webhook endpoint integration
│   └── common.rs       # Common protocol utilities
├── Cargo.toml          # Dependencies
└── README.md           # This file
```

## 🦀 Protocol Implementations

### GitHub API Integration
- `GitHubAPIClient` for direct repository integration
- YAML data format support
- Git commit integration
- Rate limiting handling

### MQTT Broker Integration
- `MQTTClient` for real-time messaging
- JSON data format support
- Topic management
- Connection handling

### Webhook Endpoint Integration
- `WebhookClient` for HTTP POST integration
- JSON data format support
- Retry logic
- Error handling

### Common Utilities
- `DataSerializer` for data serialization
- `ConnectionManager` for connection management
- `RetryLogic` for retry handling
- `ErrorRecovery` for error recovery

## 📚 Usage

```rust
use arxos_hardware_protocols::{GitHubAPIClient, MQTTClient, WebhookClient};

// GitHub API client
let mut github = GitHubAPIClient::new(token, owner, repo)?;
github.post_sensor_data(&sensor_data).await?;

// MQTT client
let mut mqtt = MQTTClient::new(broker, port, user, password)?;
mqtt.connect().await?;
mqtt.publish_sensor_data(&sensor_data).await?;

// Webhook client
let mut webhook = WebhookClient::new(url, port)?;
webhook.post_sensor_data(&sensor_data).await?;
```

## 🔧 Dependencies

- `reqwest` for HTTP client
- `serde_json` for JSON serialization
- `tokio` for async runtime
- `mqtt` for MQTT client
- `arxos_hardware_core` for core types
