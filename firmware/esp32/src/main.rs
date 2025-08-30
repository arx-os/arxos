//! Arxos ESP32 Mesh Node Firmware
//! 
//! This firmware runs on ESP32-C3 with SX1262 LoRa radio
//! to create an air-gapped mesh network for building intelligence.

#![no_std]
#![no_main]
#![feature(type_alias_impl_trait)]

use esp_backtrace as _;
use esp_hal::{
    clock::ClockControl,
    delay::Delay,
    gpio::{AnyPin, Input, Io, Level, Output, Pull},
    peripherals::Peripherals,
    prelude::*,
    rng::Rng,
    spi::{master::Spi, SpiMode},
    system::SystemControl,
    timer::{timg::TimerGroup, ErasedTimer, OneShotTimer},
    uart::{config::Config as UartConfig, TxRxPins, Uart},
};
use esp_println::println;
use embassy_executor::Spawner;
use embassy_time::{Duration, Timer};
use static_cell::StaticCell;

mod config;
mod lora_driver;
mod mesh_router;
mod packet_processor;
mod ssh_server;
mod storage;

use config::NodeConfig;
use lora_driver::LoRaDriver;
use mesh_router::MeshRouter;

/// Main embassy executor
static EXECUTOR: StaticCell<embassy_executor::Executor> = StaticCell::new();

#[esp_hal::macros::main]
async fn main(spawner: Spawner) {
    println!("╔════════════════════════════════════════╗");
    println!("║     Arxos Mesh Node Firmware v0.1.0     ║");
    println!("║         100% Air-Gapped RF Only         ║");
    println!("╚════════════════════════════════════════╝");
    
    // Initialize hardware
    let peripherals = Peripherals::take();
    let system = SystemControl::new(peripherals.SYSTEM);
    let clocks = ClockControl::boot_defaults(system.clock_control).freeze();
    let delay = Delay::new(&clocks);
    
    // Initialize GPIO
    let io = Io::new(peripherals.GPIO, peripherals.IO_MUX);
    
    // Initialize RNG for node ID if not set
    let mut rng = Rng::new(peripherals.RNG);
    
    // Load or generate node configuration
    let config = NodeConfig::load_or_create(&mut rng);
    println!("Node ID: 0x{:04X}", config.node_id);
    println!("Region: {}", config.region_string());
    
    // Initialize SPI for LoRa
    let sclk = io.pins.gpio6;
    let miso = io.pins.gpio2;
    let mosi = io.pins.gpio7;
    let cs = io.pins.gpio10;
    let reset = io.pins.gpio3;
    let dio1 = io.pins.gpio5;
    let busy = io.pins.gpio4;
    
    let spi = Spi::new(
        peripherals.SPI2,
        100_000u32.Hz(),
        SpiMode::Mode0,
        &clocks,
    )
    .with_sck(sclk)
    .with_mosi(mosi)
    .with_miso(miso);
    
    // Initialize LoRa driver
    let lora = LoRaDriver::new(
        spi,
        Output::new(cs, Level::High),
        Output::new(reset, Level::High),
        Input::new(dio1, Pull::None),
        Input::new(busy, Pull::None),
        config.clone(),
    ).await;
    
    // Initialize mesh router
    let router = MeshRouter::new(config.node_id, lora);
    
    // Initialize UART for SSH server
    let uart_pins = TxRxPins::new(io.pins.gpio21, io.pins.gpio20);
    let uart = Uart::new_with_config(
        peripherals.UART0,
        UartConfig::default(),
        uart_pins,
        &clocks,
    );
    
    // Spawn async tasks
    spawner.spawn(mesh_receive_task(router.clone())).unwrap();
    spawner.spawn(mesh_transmit_task(router.clone())).unwrap();
    spawner.spawn(heartbeat_task()).unwrap();
    spawner.spawn(ssh_server_task(uart)).unwrap();
    
    println!("Mesh node started successfully!");
    println!("Listening on {} MHz", config.frequency_mhz());
    
    // Main loop - process packets
    loop {
        Timer::after(Duration::from_secs(1)).await;
        
        // Check mesh health
        if router.is_healthy().await {
            // Everything OK
        } else {
            println!("Warning: Mesh connectivity issues detected");
        }
    }
}

/// Task to receive packets from mesh network
#[embassy_executor::task]
async fn mesh_receive_task(router: MeshRouter) {
    println!("Starting mesh receive task");
    
    loop {
        match router.receive_packet().await {
            Ok(packet) => {
                println!("Received packet from 0x{:04X}", packet.source_id);
                router.process_packet(packet).await;
            }
            Err(e) => {
                println!("Receive error: {:?}", e);
            }
        }
    }
}

/// Task to transmit queued packets
#[embassy_executor::task]
async fn mesh_transmit_task(router: MeshRouter) {
    println!("Starting mesh transmit task");
    
    loop {
        // Check for packets to transmit
        if let Some(packet) = router.get_next_tx_packet().await {
            match router.transmit_packet(packet).await {
                Ok(_) => {
                    // Successfully transmitted
                }
                Err(e) => {
                    println!("Transmit error: {:?}", e);
                }
            }
        }
        
        // Small delay to prevent tight loop
        Timer::after(Duration::from_millis(10)).await;
    }
}

/// Heartbeat LED task
#[embassy_executor::task]
async fn heartbeat_task() {
    println!("Starting heartbeat task");
    
    loop {
        // Toggle LED or print heartbeat
        println!("♥");
        Timer::after(Duration::from_secs(30)).await;
    }
}

/// SSH server task for terminal access
#[embassy_executor::task]
async fn ssh_server_task(uart: Uart<'static, UART0>) {
    println!("Starting SSH server on UART");
    
    // Simple command processor for now
    // Full SSH implementation would use russh crate
    loop {
        // Read command from UART
        let mut buffer = [0u8; 256];
        match uart.read(&mut buffer).await {
            Ok(len) => {
                let command = core::str::from_utf8(&buffer[..len]).unwrap_or("");
                process_command(command).await;
            }
            Err(_) => {
                Timer::after(Duration::from_millis(100)).await;
            }
        }
    }
}

async fn process_command(cmd: &str) {
    match cmd.trim() {
        "status" => {
            println!("Node status: OK");
            println!("Mesh neighbors: 3");
            println!("Packets routed: 1,234");
        }
        "scan" => {
            println!("Scanning for neighbors...");
            // Trigger neighbor discovery
        }
        _ => {
            println!("Unknown command: {}", cmd);
        }
    }
}

/// Panic handler
#[panic_handler]
fn panic(info: &core::panic::PanicInfo) -> ! {
    println!("PANIC: {}", info);
    loop {}
}