# Arxos Mobile App Architecture
**Version:** 1.0  
**Date:** August 31, 2025  
**Platform:** iOS and Android Native

## Overview

The Arxos mobile app provides a unified interface for building intelligence access through multiple air-gapped communication methods. Built with Rust core and native UI, it automatically selects the best available connection method while maintaining complete offline operation.

## Architecture Philosophy

### Core Principles
1. **Rust Core, Native UI**: Business logic in Rust, platform UI in Swift/Kotlin
2. **Offline First**: Full functionality without internet
3. **Progressive Enhancement**: Better features with better hardware
4. **Zero Configuration**: Automatic discovery and connection
5. **Privacy by Design**: No analytics, no cloud, no tracking

## Application Structure

### Layer Architecture

```
┌─────────────────────────────────────────────────┐
│                Native UI Layer                  │
│         iOS (SwiftUI) | Android (Compose)       │
├─────────────────────────────────────────────────┤
│              Platform Bridge Layer              │
│        Swift/Kotlin ←→ Rust FFI Bindings        │
├─────────────────────────────────────────────────┤
│               Rust Core Library                 │
│    Business Logic | Data Models | Protocols     │
├─────────────────────────────────────────────────┤
│            Transport Abstraction Layer          │
│     LoRa USB | Bluetooth | SMS | Future...      │
├─────────────────────────────────────────────────┤
│              Platform Services                  │
│    iOS/Android USB | BLE | SMS | Storage        │
└─────────────────────────────────────────────────┘
```

### Directory Structure

```
arxos-mobile/
├── rust-core/                 # Shared Rust library
│   ├── src/
│   │   ├── lib.rs            # FFI exports
│   │   ├── models/           # ArxObject, Building, etc.
│   │   ├── protocols/        # ArxQL, compression
│   │   ├── transport/        # Connection managers
│   │   ├── cache/            # Offline storage
│   │   └── security/         # Crypto, auth
│   └── Cargo.toml
│
├── ios/                       # iOS app
│   ├── ArxosApp/
│   │   ├── App.swift         # Main app entry
│   │   ├── Views/            # SwiftUI views
│   │   ├── ViewModels/       # MVVM view models
│   │   ├── Services/         # Platform services
│   │   ├── Bridge/           # Rust FFI bridge
│   │   └── Resources/        # Assets, Info.plist
│   └── ArxosApp.xcodeproj
│
├── android/                   # Android app
│   ├── app/
│   │   ├── src/
│   │   │   ├── main/
│   │   │   │   ├── java/com/arxos/
│   │   │   │   │   ├── MainActivity.kt
│   │   │   │   │   ├── ui/          # Compose UI
│   │   │   │   │   ├── viewmodels/  # ViewModels
│   │   │   │   │   ├── services/    # Platform services
│   │   │   │   │   └── bridge/      # Rust JNI bridge
│   │   │   │   └── res/             # Resources
│   │   └── build.gradle
│   └── settings.gradle
│
└── shared/                    # Shared resources
    ├── assets/               # Icons, images
    ├── schemas/              # Data schemas
    └── tests/                # Integration tests
```

## Rust Core Library

### FFI Interface

```rust
// rust-core/src/lib.rs

use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int};

/// Initialize the Arxos library
#[no_mangle]
pub extern "C" fn arxos_init() -> c_int {
    android_logger::init_once(
        android_logger::Config::default()
            .with_min_level(log::Level::Debug)
    );
    
    match initialize_core() {
        Ok(_) => 0,
        Err(_) => -1,
    }
}

/// Connect to building using best available method
#[no_mangle]
pub extern "C" fn arxos_connect(building_id: *const c_char) -> c_int {
    let building = unsafe {
        CStr::from_ptr(building_id).to_string_lossy().to_string()
    };
    
    match connect_to_building(&building) {
        Ok(connection_id) => connection_id as c_int,
        Err(_) => -1,
    }
}

/// Execute ArxQL query
#[no_mangle]
pub extern "C" fn arxos_query(
    connection_id: c_int,
    query: *const c_char,
    callback: extern "C" fn(*const c_char)
) {
    let query_str = unsafe {
        CStr::from_ptr(query).to_string_lossy().to_string()
    };
    
    std::thread::spawn(move || {
        match execute_query(connection_id as u32, &query_str) {
            Ok(result) => {
                let json = serde_json::to_string(&result).unwrap();
                let c_str = CString::new(json).unwrap();
                callback(c_str.as_ptr());
            }
            Err(e) => {
                let error = format!("{{\"error\":\"{}\"}}", e);
                let c_str = CString::new(error).unwrap();
                callback(c_str.as_ptr());
            }
        }
    });
}

/// Transport layer abstraction
pub struct TransportManager {
    lora: Option<LoRaTransport>,
    bluetooth: Option<BluetoothTransport>,
    sms: Option<SMSTransport>,
    active: Option<Box<dyn Transport>>,
}

impl TransportManager {
    pub fn new() -> Self {
        Self {
            lora: LoRaTransport::detect(),
            bluetooth: BluetoothTransport::new(),
            sms: SMSTransport::new(),
            active: None,
        }
    }
    
    pub fn auto_connect(&mut self, building_id: &str) -> Result<(), Error> {
        // Try transports in priority order
        
        // 1. LoRa dongle (best range and bandwidth)
        if let Some(ref mut lora) = self.lora {
            if lora.connect(building_id).is_ok() {
                self.active = Some(Box::new(lora.clone()));
                return Ok(());
            }
        }
        
        // 2. Bluetooth (no hardware needed)
        if let Some(ref mut ble) = self.bluetooth {
            if ble.scan_and_connect(building_id).is_ok() {
                self.active = Some(Box::new(ble.clone()));
                return Ok(());
            }
        }
        
        // 3. SMS (emergency fallback)
        if let Some(ref mut sms) = self.sms {
            if sms.configure(building_id).is_ok() {
                self.active = Some(Box::new(sms.clone()));
                return Ok(());
            }
        }
        
        Err(Error::NoTransportAvailable)
    }
}
```

### Data Models

```rust
// rust-core/src/models/mod.rs

use serde::{Serialize, Deserialize};
use crate::arxobject::ArxObject;

#[derive(Serialize, Deserialize, Clone)]
pub struct Building {
    pub id: String,
    pub name: String,
    pub address: String,
    pub floors: Vec<Floor>,
    pub last_sync: Option<DateTime<Utc>>,
    pub connection_method: Option<ConnectionMethod>,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct Floor {
    pub number: i8,
    pub name: String,
    pub rooms: Vec<Room>,
    pub arxobjects: Vec<ArxObject>,
    pub ascii_map: Option<String>,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct Room {
    pub number: String,
    pub name: String,
    pub area_sqm: f32,
    pub occupancy: Option<OccupancyStatus>,
    pub equipment_count: u32,
}

#[derive(Serialize, Deserialize, Clone)]
pub enum ConnectionMethod {
    LoRaDongle { frequency: u32, rssi: i16 },
    Bluetooth { device_name: String, rssi: i8 },
    SMS { phone_number: String },
}

#[derive(Serialize, Deserialize, Clone)]
pub enum OccupancyStatus {
    Vacant,
    Occupied { count: Option<u8> },
    Unknown,
}
```

## iOS Application

### SwiftUI Main App

```swift
// ios/ArxosApp/App.swift

import SwiftUI

@main
struct ArxosApp: App {
    @StateObject private var appState = AppState()
    @StateObject private var connectionManager = ConnectionManager()
    
    init() {
        // Initialize Rust core
        arxos_init()
        
        // Configure app appearance
        configureAppearance()
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appState)
                .environmentObject(connectionManager)
                .onAppear {
                    connectionManager.startAutoDiscovery()
                }
        }
    }
    
    private func configureAppearance() {
        // Terminal-inspired theme
        UINavigationBar.appearance().backgroundColor = .black
        UINavigationBar.appearance().titleTextAttributes = [
            .foregroundColor: UIColor.green,
            .font: UIFont.monospacedSystemFont(ofSize: 18, weight: .medium)
        ]
    }
}
```

### Connection Manager

```swift
// ios/ArxosApp/Services/ConnectionManager.swift

import Foundation
import ExternalAccessory
import CoreBluetooth
import Combine

class ConnectionManager: NSObject, ObservableObject {
    @Published var connectionStatus: ConnectionStatus = .disconnected
    @Published var availableTransports: [TransportType] = []
    @Published var currentBuilding: Building?
    
    private var loraManager: LoRaDongleManager?
    private var bluetoothManager: BluetoothManager?
    private var smsManager: SMSManager?
    
    override init() {
        super.init()
        setupTransports()
    }
    
    private func setupTransports() {
        // Check for LoRa dongle
        if LoRaDongleManager.isDongleConnected() {
            loraManager = LoRaDongleManager()
            availableTransports.append(.lora)
        }
        
        // Bluetooth is always available
        bluetoothManager = BluetoothManager()
        availableTransports.append(.bluetooth)
        
        // SMS if configured
        if SMSManager.isConfigured() {
            smsManager = SMSManager()
            availableTransports.append(.sms)
        }
    }
    
    func connectToBuilding(_ buildingId: String) {
        connectionStatus = .connecting
        
        // Call Rust core for auto-connection
        let result = arxos_connect(buildingId)
        
        if result >= 0 {
            connectionStatus = .connected(connectionId: Int(result))
            loadBuildingData(buildingId)
        } else {
            connectionStatus = .failed(error: "No transport available")
        }
    }
    
    func query(_ arxql: String) async throws -> QueryResult {
        guard case .connected(let connectionId) = connectionStatus else {
            throw ConnectionError.notConnected
        }
        
        return try await withCheckedThrowingContinuation { continuation in
            arxos_query(Int32(connectionId), arxql) { resultPtr in
                guard let resultPtr = resultPtr else {
                    continuation.resume(throwing: ConnectionError.queryFailed)
                    return
                }
                
                let json = String(cString: resultPtr)
                
                do {
                    let result = try JSONDecoder().decode(QueryResult.self, 
                                                         from: json.data(using: .utf8)!)
                    continuation.resume(returning: result)
                } catch {
                    continuation.resume(throwing: error)
                }
            }
        }
    }
}
```

### Terminal View

```swift
// ios/ArxosApp/Views/TerminalView.swift

import SwiftUI

struct TerminalView: View {
    @State private var commandHistory: [String] = []
    @State private var currentCommand: String = ""
    @State private var output: [TerminalLine] = []
    @EnvironmentObject var connectionManager: ConnectionManager
    
    var body: some View {
        VStack(spacing: 0) {
            // Output area
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: 2) {
                        ForEach(output) { line in
                            Text(line.text)
                                .font(.custom("Menlo", size: 12))
                                .foregroundColor(line.color)
                                .id(line.id)
                        }
                    }
                    .padding(8)
                }
                .background(Color.black)
                .onChange(of: output.count) { _ in
                    withAnimation {
                        proxy.scrollTo(output.last?.id)
                    }
                }
            }
            
            // Input area
            HStack {
                Text("arxos>")
                    .font(.custom("Menlo", size: 14))
                    .foregroundColor(.green)
                
                TextField("", text: $currentCommand)
                    .font(.custom("Menlo", size: 14))
                    .foregroundColor(.white)
                    .autocapitalization(.none)
                    .disableAutocorrection(true)
                    .onSubmit {
                        executeCommand()
                    }
            }
            .padding(8)
            .background(Color.black.opacity(0.9))
        }
        .background(Color.black)
        .onAppear {
            output.append(TerminalLine(
                text: "Arxos Terminal v1.0",
                color: .green
            ))
            output.append(TerminalLine(
                text: "Type 'help' for commands",
                color: .gray
            ))
        }
    }
    
    private func executeCommand() {
        guard !currentCommand.isEmpty else { return }
        
        // Add to history
        commandHistory.append(currentCommand)
        output.append(TerminalLine(
            text: "arxos> \(currentCommand)",
            color: .white
        ))
        
        // Process command
        Task {
            do {
                let result = try await connectionManager.query(currentCommand)
                displayResult(result)
            } catch {
                output.append(TerminalLine(
                    text: "Error: \(error.localizedDescription)",
                    color: .red
                ))
            }
        }
        
        currentCommand = ""
    }
    
    private func displayResult(_ result: QueryResult) {
        // Format result based on type
        switch result {
        case .objects(let arxObjects):
            for obj in arxObjects {
                output.append(TerminalLine(
                    text: formatArxObject(obj),
                    color: .cyan
                ))
            }
            
        case .floorPlan(let ascii):
            for line in ascii.split(separator: "\n") {
                output.append(TerminalLine(
                    text: String(line),
                    color: .yellow
                ))
            }
            
        case .status(let message):
            output.append(TerminalLine(
                text: message,
                color: .green
            ))
        }
    }
}
```

## Android Application

### Main Activity

```kotlin
// android/app/src/main/java/com/arxos/MainActivity.kt

package com.arxos

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.lifecycle.viewmodel.compose.viewModel
import com.arxos.ui.theme.ArxosTheme
import com.arxos.ui.screens.MainScreen
import com.arxos.services.ConnectionManager
import com.arxos.bridge.RustBridge

class MainActivity : ComponentActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Initialize Rust core
        RustBridge.init()
        
        // Initialize connection manager
        ConnectionManager.initialize(this)
        
        setContent {
            ArxosTheme {
                MainScreen()
            }
        }
    }
    
    override fun onResume() {
        super.onResume()
        ConnectionManager.checkForUsbDevices()
    }
}
```

### Rust JNI Bridge

```kotlin
// android/app/src/main/java/com/arxos/bridge/RustBridge.kt

package com.arxos.bridge

import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

object RustBridge {
    init {
        System.loadLibrary("arxos_core")
    }
    
    // Native methods
    external fun arxosInit(): Int
    external fun arxosConnect(buildingId: String): Int
    external fun arxosQuery(
        connectionId: Int,
        query: String,
        callback: (String) -> Unit
    )
    
    fun init() {
        val result = arxosInit()
        if (result != 0) {
            throw RuntimeException("Failed to initialize Arxos core")
        }
    }
    
    suspend fun connect(buildingId: String): Int {
        return suspendCancellableCoroutine { cont ->
            val result = arxosConnect(buildingId)
            if (result >= 0) {
                cont.resume(result)
            } else {
                cont.resumeWithException(
                    Exception("Connection failed")
                )
            }
        }
    }
    
    suspend fun query(connectionId: Int, arxql: String): QueryResult {
        return suspendCancellableCoroutine { cont ->
            arxosQuery(connectionId, arxql) { json ->
                try {
                    val result = Json.decodeFromString<QueryResult>(json)
                    cont.resume(result)
                } catch (e: Exception) {
                    cont.resumeWithException(e)
                }
            }
        }
    }
}
```

### Compose UI

```kotlin
// android/app/src/main/java/com/arxos/ui/screens/TerminalScreen.kt

package com.arxos.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.arxos.viewmodels.TerminalViewModel

@Composable
fun TerminalScreen(
    viewModel: TerminalViewModel = viewModel()
) {
    val terminalLines by viewModel.output.collectAsState()
    var currentCommand by remember { mutableStateOf("") }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
    ) {
        // Output area
        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(8.dp),
            reverseLayout = false
        ) {
            items(terminalLines) { line ->
                Text(
                    text = line.text,
                    color = line.color,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
        }
        
        // Input area
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color.Black.copy(alpha = 0.9f))
                .padding(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "arxos> ",
                color = Color.Green,
                fontSize = 14.sp,
                fontFamily = FontFamily.Monospace
            )
            
            TextField(
                value = currentCommand,
                onValueChange = { currentCommand = it },
                modifier = Modifier.fillMaxWidth(),
                textStyle = LocalTextStyle.current.copy(
                    color = Color.White,
                    fontSize = 14.sp,
                    fontFamily = FontFamily.Monospace
                ),
                keyboardOptions = KeyboardOptions(
                    imeAction = ImeAction.Send
                ),
                keyboardActions = KeyboardActions(
                    onSend = {
                        viewModel.executeCommand(currentCommand)
                        currentCommand = ""
                    }
                ),
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = Color.Transparent,
                    unfocusedContainerColor = Color.Transparent,
                    cursorColor = Color.Green
                )
            )
        }
    }
}
```

## Offline Capabilities

### Local Cache Database

```rust
// rust-core/src/cache/mod.rs

use rusqlite::{Connection, Result};
use serde::{Serialize, Deserialize};

pub struct OfflineCache {
    conn: Connection,
}

impl OfflineCache {
    pub fn new() -> Result<Self> {
        let conn = Connection::open("arxos_cache.db")?;
        
        // Create tables
        conn.execute(
            "CREATE TABLE IF NOT EXISTS buildings (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                data BLOB NOT NULL,
                last_sync INTEGER NOT NULL
            )",
            [],
        )?;
        
        conn.execute(
            "CREATE TABLE IF NOT EXISTS query_cache (
                query TEXT PRIMARY KEY,
                result BLOB NOT NULL,
                timestamp INTEGER NOT NULL,
                ttl INTEGER NOT NULL
            )",
            [],
        )?;
        
        Ok(Self { conn })
    }
    
    pub fn cache_query(&self, query: &str, result: &QueryResult, ttl: Duration) -> Result<()> {
        let data = bincode::serialize(result).unwrap();
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        self.conn.execute(
            "INSERT OR REPLACE INTO query_cache (query, result, timestamp, ttl) 
             VALUES (?1, ?2, ?3, ?4)",
            params![query, data, timestamp, ttl.as_secs()],
        )?;
        
        Ok(())
    }
    
    pub fn get_cached_query(&self, query: &str) -> Option<QueryResult> {
        let result = self.conn.query_row(
            "SELECT result, timestamp, ttl FROM query_cache WHERE query = ?1",
            params![query],
            |row| {
                let data: Vec<u8> = row.get(0)?;
                let timestamp: u64 = row.get(1)?;
                let ttl: u64 = row.get(2)?;
                Ok((data, timestamp, ttl))
            },
        ).ok()?;
        
        // Check if cache is still valid
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        if now - result.1 > result.2 {
            // Cache expired
            return None;
        }
        
        bincode::deserialize(&result.0).ok()
    }
}
```

### Sync Strategy

```rust
// rust-core/src/sync/mod.rs

pub struct SyncManager {
    cache: OfflineCache,
    transport: Box<dyn Transport>,
}

impl SyncManager {
    pub async fn sync_building(&mut self, building_id: &str) -> Result<(), Error> {
        // Progressive sync strategy
        
        // 1. Critical data (emergency exits, fire systems)
        self.sync_emergency_data(building_id).await?;
        
        // 2. Current floor data
        self.sync_current_floor(building_id).await?;
        
        // 3. Frequently accessed rooms
        self.sync_frequent_rooms(building_id).await?;
        
        // 4. Full building data (background)
        tokio::spawn(async move {
            self.sync_full_building(building_id).await
        });
        
        Ok(())
    }
    
    async fn sync_emergency_data(&mut self, building_id: &str) -> Result<(), Error> {
        let emergency_queries = [
            "type:emergency_exit",
            "type:fire_alarm",
            "type:aed",
            "type:sprinkler",
        ];
        
        for query in emergency_queries {
            let result = self.transport.query(query).await?;
            self.cache.cache_query(
                query,
                &result,
                Duration::from_secs(86400), // 24 hour cache
            )?;
        }
        
        Ok(())
    }
}
```

## Performance Optimization

### Battery Management

```swift
// ios/ArxosApp/Services/BatteryManager.swift

class BatteryManager: ObservableObject {
    @Published var batteryLevel: Float = 1.0
    @Published var isLowPowerMode: Bool = false
    
    func optimizeForBattery() {
        if batteryLevel < 0.2 || isLowPowerMode {
            // Reduce query frequency
            ConnectionManager.shared.queryInterval = 60 // seconds
            
            // Disable auto-discovery
            ConnectionManager.shared.stopAutoDiscovery()
            
            // Use cached data more aggressively
            CacheManager.shared.ttlMultiplier = 5.0
            
            // Reduce Bluetooth scan rate
            BluetoothManager.shared.scanInterval = 30 // seconds
        }
    }
}
```

### Memory Management

```rust
// rust-core/src/memory/mod.rs

pub struct MemoryManager {
    max_cache_size: usize,
    current_size: AtomicUsize,
}

impl MemoryManager {
    pub fn new(max_size: usize) -> Self {
        Self {
            max_cache_size: max_size,
            current_size: AtomicUsize::new(0),
        }
    }
    
    pub fn should_evict(&self) -> bool {
        self.current_size.load(Ordering::Relaxed) > self.max_cache_size * 90 / 100
    }
    
    pub fn evict_lru(&self) {
        // Evict least recently used cache entries
        // Priority order:
        // 1. Old query results
        // 2. Non-emergency floor plans
        // 3. Historical data
        // Never evict: Emergency data, current floor
    }
}
```

## Testing Framework

### Unit Tests

```rust
// rust-core/src/tests/mod.rs

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_transport_selection() {
        let mut manager = TransportManager::new();
        
        // Mock available transports
        manager.lora = Some(MockLoRaTransport::new());
        manager.bluetooth = Some(MockBluetoothTransport::new());
        
        // Should prefer LoRa when available
        manager.auto_connect("building-1").unwrap();
        assert!(matches!(manager.active, Some(ref t) if t.name() == "LoRa"));
    }
    
    #[test]
    fn test_offline_cache() {
        let cache = OfflineCache::new().unwrap();
        
        let query = "room:127";
        let result = QueryResult::Status("Room 127: OK".to_string());
        
        cache.cache_query(query, &result, Duration::from_secs(60)).unwrap();
        
        let cached = cache.get_cached_query(query).unwrap();
        assert_eq!(cached, result);
    }
}
```

### UI Tests (iOS)

```swift
// ios/ArxosAppTests/TerminalTests.swift

import XCTest
@testable import ArxosApp

class TerminalTests: XCTestCase {
    func testCommandExecution() async {
        let viewModel = TerminalViewModel()
        
        await viewModel.executeCommand("HELP")
        
        XCTAssertFalse(viewModel.output.isEmpty)
        XCTAssertTrue(viewModel.output.last?.text.contains("Available commands"))
    }
    
    func testAutoCompletion() {
        let viewModel = TerminalViewModel()
        
        let suggestions = viewModel.autocomplete("STA")
        
        XCTAssertTrue(suggestions.contains("STATUS"))
    }
}
```

## App Store Deployment

### iOS App Store Requirements

```yaml
# ios/ArxosApp/Info.plist requirements
Required Device Capabilities:
  - external-accessory  # For LoRa dongle
  - bluetooth-le        # For BLE connections
  
Background Modes:
  - external-accessory-wireless-configuration
  - bluetooth-central
  
Usage Descriptions:
  NSBluetoothAlwaysUsageDescription: "Arxos uses Bluetooth to connect to building networks"
  NSLocationWhenInUseUsageDescription: "Arxos uses location to find nearby buildings"
  UISupportedExternalAccessoryProtocols:
    - com.arxos.lora
```

### Google Play Requirements

```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<uses-permission android:name="android.permission.BLUETOOTH" />
<uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
<uses-permission android:name="android.permission.BLUETOOTH_SCAN" />
<uses-permission android:name="android.permission.USB_PERMISSION" />
<uses-permission android:name="android.permission.SEND_SMS" />
<uses-permission android:name="android.permission.RECEIVE_SMS" />

<uses-feature android:name="android.hardware.usb.host" />
<uses-feature android:name="android.hardware.bluetooth_le" />
```

## Conclusion

The Arxos mobile app provides a seamless interface to building intelligence through multiple air-gapped communication methods. By using Rust for the core logic and native UI frameworks, the app delivers excellent performance while maintaining the flexibility to support various transport methods.

The offline-first architecture ensures the app remains functional even without any connectivity, while the progressive sync strategy optimizes for both performance and battery life. The terminal-inspired interface maintains consistency with the Arxos philosophy while providing modern mobile UX when appropriate.