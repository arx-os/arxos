//! Mesh Bridge for Development
//! 
//! Bridges ESP32 UART to TCP/SSH for development and testing
//! This allows the terminal client to connect to real ESP32 hardware

use serialport::{SerialPort, SerialPortInfo};
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;
use clap::Parser;
use log::{debug, error, info, warn};

/// Mesh bridge command-line arguments
#[derive(Debug)]
struct Args {
    /// Serial port path (e.g., /dev/ttyUSB0)
    #[arg(short, long)]
    port: String,
    
    /// Serial baud rate
    #[arg(short, long, default_value_t = 115200)]
    baud: u32,
    
    /// TCP listen address
    #[arg(short, long, default_value = "0.0.0.0:2222")]
    listen: String,
    
    /// Enable verbose logging
    #[arg(short, long)]
    verbose: bool,
    
    /// List available serial ports
    #[arg(short = 'L', long)]
    list_ports: bool,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    
    // Initialize logging
    let log_level = if args.verbose { "debug" } else { "info" };
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or(log_level))
        .init();
    
    // List ports if requested
    if args.list_ports {
        list_serial_ports();
        return Ok(());
    }
    
    info!("╔════════════════════════════════════════╗");
    info!("║     Arxos Mesh Bridge v0.1.0           ║");
    info!("║     UART ↔ TCP Bridge                  ║");
    info!("╚════════════════════════════════════════╝");
    
    // Open serial port
    info!("Opening serial port {} at {} baud", args.port, args.baud);
    let serial = serialport::new(&args.port, args.baud)
        .timeout(Duration::from_millis(100))
        .open()?;
    
    let serial = Arc::new(Mutex::new(serial));
    info!("Serial port opened successfully");
    
    // Start TCP listener
    info!("Starting TCP listener on {}", args.listen);
    let listener = TcpListener::bind(&args.listen)?;
    info!("TCP server listening for connections");
    
    // Accept connections
    for stream in listener.incoming() {
        match stream {
            Ok(tcp_stream) => {
                info!("New connection from {}", tcp_stream.peer_addr()?);
                handle_connection(tcp_stream, serial.clone());
            }
            Err(e) => {
                error!("Connection failed: {}", e);
            }
        }
    }
    
    Ok(())
}

/// Handle a TCP connection
fn handle_connection(mut tcp_stream: TcpStream, serial: Arc<Mutex<Box<dyn SerialPort>>>) {
    // Clone for the threads
    let serial_tx = serial.clone();
    let serial_rx = serial.clone();
    let mut tcp_tx = tcp_stream.try_clone().expect("Failed to clone TCP stream");
    let mut tcp_rx = tcp_stream;
    
    // Set TCP nodelay for lower latency
    tcp_tx.set_nodelay(true).ok();
    tcp_rx.set_nodelay(true).ok();
    
    // Send welcome message
    let welcome = b"\r\nArxos Mesh Bridge Connected\r\n";
    tcp_tx.write_all(welcome).ok();
    
    // Thread 1: TCP → Serial
    let tcp_to_serial = thread::spawn(move || {
        let mut buffer = [0u8; 1024];
        loop {
            match tcp_rx.read(&mut buffer) {
                Ok(0) => {
                    info!("TCP connection closed");
                    break;
                }
                Ok(n) => {
                    debug!("TCP → Serial: {} bytes", n);
                    if let Ok(mut serial) = serial_tx.lock() {
                        if let Err(e) = serial.write_all(&buffer[..n]) {
                            error!("Serial write error: {}", e);
                            break;
                        }
                        serial.flush().ok();
                    }
                }
                Err(e) => {
                    error!("TCP read error: {}", e);
                    break;
                }
            }
        }
    });
    
    // Thread 2: Serial → TCP
    let serial_to_tcp = thread::spawn(move || {
        let mut buffer = [0u8; 1024];
        loop {
            if let Ok(mut serial) = serial_rx.lock() {
                match serial.read(&mut buffer) {
                    Ok(n) if n > 0 => {
                        debug!("Serial → TCP: {} bytes", n);
                        if let Err(e) = tcp_tx.write_all(&buffer[..n]) {
                            error!("TCP write error: {}", e);
                            break;
                        }
                        tcp_tx.flush().ok();
                    }
                    Ok(_) => {
                        // No data available, continue
                    }
                    Err(e) if e.kind() == std::io::ErrorKind::TimedOut => {
                        // Timeout is normal, continue
                    }
                    Err(e) => {
                        error!("Serial read error: {}", e);
                        break;
                    }
                }
            }
            
            // Small delay to prevent tight loop
            thread::sleep(Duration::from_millis(10));
        }
    });
    
    // Wait for threads to finish
    tcp_to_serial.join().ok();
    serial_to_tcp.join().ok();
    
    info!("Connection closed");
}

/// List available serial ports
fn list_serial_ports() {
    println!("Available serial ports:");
    
    let ports = serialport::available_ports().expect("Failed to list ports");
    
    if ports.is_empty() {
        println!("  No serial ports found");
        return;
    }
    
    for port in ports {
        print!("  {} ", port.port_name);
        
        match port.port_type {
            serialport::SerialPortType::UsbPort(info) => {
                println!("(USB: VID={:04x} PID={:04x})", 
                    info.vid, info.pid);
            }
            serialport::SerialPortType::PciPort => {
                println!("(PCI)");
            }
            serialport::SerialPortType::BluetoothPort => {
                println!("(Bluetooth)");
            }
            serialport::SerialPortType::Unknown => {
                println!("(Unknown)");
            }
        }
    }
}