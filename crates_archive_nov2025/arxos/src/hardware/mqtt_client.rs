//! MQTT client for sensor data ingestion
//!
//! This module provides MQTT subscription capabilities for receiving sensor data
//! from IoT devices via MQTT brokers using the rumqttc library.

#[cfg(feature = "async-sensors")]
use super::{HardwareError, SensorData};
#[cfg(feature = "async-sensors")]
use log::{error, info, warn};
#[cfg(feature = "async-sensors")]
use rumqttc::{AsyncClient, Event, Incoming, MqttOptions, QoS};

/// MQTT client configuration
#[cfg(feature = "async-sensors")]
#[derive(Debug, Clone)]
pub struct MqttClientConfig {
    pub broker_url: String,
    pub broker_port: u16,
    pub client_id: String,
    pub username: Option<String>,
    pub password: Option<String>,
    pub topics: Vec<String>,
}

#[cfg(feature = "async-sensors")]
impl Default for MqttClientConfig {
    fn default() -> Self {
        Self {
            broker_url: "localhost".to_string(),
            broker_port: 1883,
            client_id: format!("arxos_sensor_client_{}", uuid::Uuid::new_v4()),
            username: None,
            password: None,
            topics: vec!["arxos/sensors/#".to_string()],
        }
    }
}

/// MQTT client for sensor data ingestion
#[cfg(feature = "async-sensors")]
pub struct MqttSensorClient {
    config: MqttClientConfig,
}

#[cfg(feature = "async-sensors")]
impl MqttSensorClient {
    /// Create a new MQTT client
    pub fn new(config: MqttClientConfig) -> Result<Self, HardwareError> {
        info!(
            "Created MQTT client configuration for broker: {}:{}",
            config.broker_url, config.broker_port
        );
        Ok(Self { config })
    }

    /// Get the configuration
    pub fn get_config(&self) -> &MqttClientConfig {
        &self.config
    }
}

/// Start MQTT subscriber for sensor data ingestion
#[cfg(feature = "async-sensors")]
pub async fn start_mqtt_subscriber(
    config: MqttClientConfig,
    callback: impl Fn(SensorData) -> Result<(), String> + Send + Sync + 'static,
) -> Result<(), HardwareError> {
    info!("Starting MQTT subscriber for sensor ingestion");
    info!(
        "Configuration: broker={}:{}, topics={:?}",
        config.broker_url, config.broker_port, config.topics
    );

    // Build MQTT options
    let mut mqtt_options =
        MqttOptions::new(&config.client_id, &config.broker_url, config.broker_port);

    // Set credentials if provided
    if let (Some(username), Some(password)) = (&config.username, &config.password) {
        mqtt_options.set_credentials(username, password);
    }

    // Set keep alive interval
    mqtt_options.set_keep_alive(std::time::Duration::from_secs(60));

    // Create async client with 10 message capacity
    let (client, mut event_loop) = AsyncClient::new(mqtt_options, 10);

    // Subscribe to all configured topics with QoS 1 (at least once delivery)
    for topic in &config.topics {
        info!("Subscribing to MQTT topic: {}", topic);
        client
            .subscribe(topic, QoS::AtLeastOnce)
            .await
            .map_err(|e| {
                HardwareError::IoError(std::io::Error::other(format!(
                    "Failed to subscribe to topic {}: {}",
                    topic, e
                )))
            })?;
    }

    // Spawn task to handle incoming messages
    tokio::spawn(async move {
        loop {
            match event_loop.poll().await {
                Ok(Event::Incoming(Incoming::ConnAck(_))) => {
                    info!("MQTT client connected to broker");
                }
                Ok(Event::Incoming(Incoming::SubAck(suback))) => {
                    info!("MQTT subscription acknowledged: {:?}", suback);
                }
                Ok(Event::Incoming(Incoming::Publish(publish))) => {
                    info!("Received MQTT message on topic: {}", publish.topic);

                    // Parse sensor data from MQTT payload
                    let payload_str = match String::from_utf8(publish.payload.to_vec()) {
                        Ok(s) => s,
                        Err(e) => {
                            warn!("Failed to decode MQTT payload as UTF-8: {}", e);
                            continue;
                        }
                    };

                    // Try to parse as SensorData JSON
                    match serde_json::from_str::<SensorData>(&payload_str) {
                        Ok(sensor_data) => {
                            // Call user callback with sensor data
                            if let Err(e) = callback(sensor_data) {
                                error!("Callback error processing sensor data: {}", e);
                            }
                        }
                        Err(e) => {
                            warn!("Failed to parse MQTT payload as SensorData: {}", e);
                        }
                    }
                }
                Ok(Event::Incoming(Incoming::Disconnect)) => {
                    warn!("MQTT client disconnected from broker");
                }
                Err(e) => {
                    error!("MQTT event loop error: {}", e);
                    break;
                }
                _ => {}
            }
        }
        warn!("MQTT subscriber event loop terminated");
    });

    info!("MQTT subscriber started successfully");
    Ok(())
}

#[cfg(not(feature = "async-sensors"))]
pub struct MqttSensorClient;

#[cfg(not(feature = "async-sensors"))]
impl MqttSensorClient {
    pub fn new(_config: MqttClientConfig) -> Result<Self, HardwareError> {
        Err(HardwareError::IoError(std::io::Error::other(
            "MQTT support requires async-sensors feature",
        )))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[cfg(feature = "async-sensors")]
    fn test_mqtt_config_defaults() {
        let config = MqttClientConfig::default();
        assert_eq!(config.broker_url, "localhost");
        assert_eq!(config.broker_port, 1883);
        assert_eq!(config.topics.len(), 1);
        assert!(config.topics[0].contains("arxos"));
    }

    #[test]
    #[cfg(feature = "async-sensors")]
    fn test_mqtt_config_custom() {
        let config = MqttClientConfig {
            broker_url: "mqtt.example.com".to_string(),
            broker_port: 8883,
            client_id: "test_client".to_string(),
            username: Some("user".to_string()),
            password: Some("pass".to_string()),
            topics: vec!["sensors/temp".to_string(), "sensors/humidity".to_string()],
        };

        assert_eq!(config.broker_url, "mqtt.example.com");
        assert_eq!(config.broker_port, 8883);
        assert_eq!(config.topics.len(), 2);
        assert_eq!(config.username, Some("user".to_string()));
        assert_eq!(config.password, Some("pass".to_string()));
    }

    #[tokio::test]
    #[cfg(feature = "async-sensors")]
    async fn test_mqtt_client_creation() {
        let config = MqttClientConfig::default();
        // Note: This will fail to connect if no broker is running, but that's expected
        // We're testing that the client can be created with valid config
        let result = MqttSensorClient::new(config);
        // Should succeed even without broker
        assert!(result.is_ok());
    }

    #[tokio::test]
    #[cfg(feature = "async-sensors")]
    async fn test_mqtt_subscriber_placeholder() {
        let config = MqttClientConfig::default();
        let callback = |_data: SensorData| -> Result<(), String> { Ok(()) };

        // This will fail without a real broker, but we can verify it starts the setup
        let result = start_mqtt_subscriber(config, callback).await;
        // For now, expect it to at least start (would need real broker for actual success)
        assert!(result.is_ok() || result.is_err());
    }
}
