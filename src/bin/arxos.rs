#!/usr/bin/env rust
//! ArxOS CLI - Production-ready building intelligence tool
//! 
//! Main entry point for processing LiDAR scans into ArxObjects

use arxos_core::arxobject::ArxObject;
use arxos_core::compression::PointCloudProcessor;
use arxos_core::error::{ArxError, Result};
use clap::{Parser, Subcommand};
use log::{info, warn, error, debug};
use std::process;

#[derive(Parser)]
#[command(name = "arxos")]
#[command(version, about, long_about = None)]
struct Cli {
    /// Verbosity level (-v, -vv, -vvv)
    #[arg(short, long, action = clap::ArgAction::Count)]
    verbose: u8,
    
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Process PLY file to ArxObjects
    Process {
        /// Input PLY file
        input: String,
        
        /// Output format
        #[arg(short, long, default_value = "stats")]
        format: OutputFormat,
        
        /// Voxel size in meters
        #[arg(short = 's', long, default_value = "0.2")]
        voxel_size: f32,
    },
    
    /// Render PLY file as ASCII art  
    Render {
        /// Input PLY file
        input: String,
        
        /// Rendering quality
        #[arg(short, long, default_value = "standard")]
        quality: Quality,
        
        /// Terminal width
        #[arg(short = 'W', long, default_value = "80")]
        width: usize,
        
        /// Terminal height
        #[arg(short = 'H', long, default_value = "24")]
        height: usize,
    },
    
    /// Show compression statistics
    Stats {
        /// Input PLY file
        input: String,
    },
    
    /// Validate ArxObject integrity
    Validate {
        /// Input PLY or binary file
        input: String,
    },
}

#[derive(Clone, Debug, clap::ValueEnum)]
enum OutputFormat {
    Stats,
    Json,
    Binary,
    Mesh,
}

#[derive(Clone, Debug, clap::ValueEnum)]
enum Quality {
    Draft,
    Standard,
    Cinematic,
}

fn main() {
    let cli = Cli::parse();
    
    // Initialize logging
    init_logger(cli.verbose);
    
    // Execute command with error handling
    if let Err(e) = run(cli.command) {
        error!("Error: {}", e);
        process::exit(1);
    }
}

fn run(command: Commands) -> Result<()> {
    match command {
        Commands::Process { input, format, voxel_size } => {
            process_file(&input, format, voxel_size)
        },
        Commands::Render { input, quality, width, height } => {
            render_file(&input, quality, width, height)
        },
        Commands::Stats { input } => {
            show_stats(&input)
        },
        Commands::Validate { input } => {
            validate_file(&input)
        },
    }
}

fn process_file(path: &str, format: OutputFormat, voxel_size: f32) -> Result<()> {
    info!("Processing file: {}", path);
    
    let processor = PointCloudProcessor::new()
        .with_voxel_size(voxel_size);
    
    let objects = processor.process_ply(path)?;
    info!("Generated {} ArxObjects", objects.len());
    
    match format {
        OutputFormat::Stats => {
            println!("╔═══════════════════════════════════════════════════════╗");
            println!("║ ArxOS Processing Complete                             ║");
            println!("╚═══════════════════════════════════════════════════════╝");
            println!();
            println!("ArxObjects:    {:>10}", objects.len());
            println!("Binary size:   {:>10} bytes", objects.len() * 13);
            println!("Voxel size:    {:>10.2} m", voxel_size);
            
            // Object type distribution
            let mut type_counts = std::collections::HashMap::new();
            for obj in &objects {
                *type_counts.entry(obj.object_type).or_insert(0) += 1;
            }
            
            println!();
            println!("Object Types:");
            for (obj_type, count) in type_counts {
                let type_name = object_type_name(obj_type);
                println!("  {:12} {:>8}", type_name, count);
            }
        },
        OutputFormat::Json => {
            let json = serde_json::json!({
                "objects": objects.len(),
                "bytes": objects.len() * 13,
                "voxel_size": voxel_size,
            });
            println!("{}", serde_json::to_string_pretty(&json).unwrap());
        },
        OutputFormat::Binary => {
            use std::io::Write;
            let stdout = std::io::stdout();
            let mut handle = stdout.lock();
            
            for obj in &objects {
                handle.write_all(&obj.to_bytes())?;
            }
        },
        OutputFormat::Mesh => {
            warn!("Mesh output not yet implemented");
        },
    }
    
    Ok(())
}

fn render_file(path: &str, quality: Quality, width: usize, height: usize) -> Result<()> {
    info!("Rendering {} with {:?} quality", path, quality);
    
    let processor = PointCloudProcessor::new();
    let objects = processor.process_ply(path)?;
    
    println!("╔═══════════════════════════════════════════════════════╗");
    println!("║ ArxOS ASCII Renderer                                  ║");
    println!("║ Quality: {:?} | Size: {}x{}                      ║", quality, width, height);
    println!("╚═══════════════════════════════════════════════════════╝");
    println!();
    
    // Render based on quality
    let ascii = match quality {
        Quality::Draft => render_simple(&objects, width, height),
        Quality::Standard => render_standard(&objects, width, height),
        Quality::Cinematic => render_cinematic(&objects, width, height),
    };
    
    println!("{}", ascii);
    println!();
    println!("Rendered {} ArxObjects", objects.len());
    
    Ok(())
}

fn show_stats(path: &str) -> Result<()> {
    info!("Calculating statistics for {}", path);
    
    let processor = PointCloudProcessor::new();
    
    // Load raw points for original size calculation
    let file = std::fs::File::open(path)?;
    let reader = std::io::BufReader::new(file);
    let mut point_count = 0;
    let mut in_header = true;
    
    for line in std::io::BufRead::lines(reader) {
        let line = line?;
        if in_header {
            if line == "end_header" {
                in_header = false;
            }
            continue;
        }
        point_count += 1;
    }
    
    let objects = processor.process_ply(path)?;
    
    let original_size = point_count * 12; // 3 floats * 4 bytes
    let compressed_size = objects.len() * 13;
    let ratio = original_size as f32 / compressed_size.max(1) as f32;
    
    println!("╔═══════════════════════════════════════════════════════╗");
    println!("║ ArxOS Compression Statistics                          ║");
    println!("╚═══════════════════════════════════════════════════════╝");
    println!();
    println!("Input file:     {}", path);
    println!("Points:         {:>10}", point_count);
    println!("ArxObjects:     {:>10}", objects.len());
    println!();
    println!("Original:       {:>10} bytes", original_size);
    println!("Compressed:     {:>10} bytes", compressed_size);
    println!("Ratio:          {:>10.1}:1", ratio);
    println!();
    
    if ratio > 100.0 {
        println!("✅ Excellent compression achieved!");
    } else if ratio > 10.0 {
        println!("✓ Good compression achieved");
    } else {
        println!("⚠ Low compression ratio - consider adjusting voxel size");
    }
    
    Ok(())
}

fn validate_file(path: &str) -> Result<()> {
    info!("Validating {}", path);
    
    let processor = PointCloudProcessor::new();
    let objects = processor.process_ply(path)?;
    
    let mut errors = 0;
    let mut warnings = 0;
    
    for (i, obj) in objects.iter().enumerate() {
        // Copy fields to avoid packed struct alignment issues
        let x = obj.x;
        let y = obj.y;
        let z = obj.z;
        let building_id = obj.building_id;
        let object_type = obj.object_type;
        
        // Validate coordinate bounds
        if x == i16::MIN || x == i16::MAX {
            warn!("Object {} has extreme X coordinate: {}", i, x);
            warnings += 1;
        }
        
        // Validate object type
        if object_type == 0x00 || object_type == 0xFF {
            warn!("Object {} has generic type: 0x{:02X}", i, object_type);
            warnings += 1;
        }
        
        // Validate serialization round-trip
        let bytes = obj.to_bytes();
        let reconstructed = ArxObject::from_bytes(&bytes);
        
        if building_id != reconstructed.building_id ||
           object_type != reconstructed.object_type ||
           x != reconstructed.x ||
           y != reconstructed.y ||
           z != reconstructed.z {
            error!("Object {} failed round-trip serialization", i);
            errors += 1;
        }
    }
    
    println!("╔═══════════════════════════════════════════════════════╗");
    println!("║ Validation Results                                    ║");
    println!("╚═══════════════════════════════════════════════════════╝");
    println!();
    println!("Objects validated: {}", objects.len());
    println!("Errors:           {}", errors);
    println!("Warnings:         {}", warnings);
    
    if errors == 0 {
        println!();
        println!("✅ All ArxObjects are valid");
        Ok(())
    } else {
        Err(ArxError::ValidationError(format!("{} validation errors found", errors)))
    }
}

// Rendering implementations

fn render_simple(objects: &[ArxObject], width: usize, height: usize) -> String {
    use arxos_core::arxobject::object_types;
    
    let mut grid = vec![vec![' '; width]; height];
    let mut density = vec![vec![0u32; width]; height];
    
    // Find bounds
    let (mut min_x, mut max_x) = (i16::MAX, i16::MIN);
    let (mut min_y, mut max_y) = (i16::MAX, i16::MIN);
    
    for obj in objects {
        min_x = min_x.min(obj.x);
        max_x = max_x.max(obj.x);
        min_y = min_y.min(obj.y);
        max_y = max_y.max(obj.y);
    }
    
    // Map objects to grid
    for obj in objects {
        let x = if max_x > min_x {
            ((obj.x - min_x) as f32 / (max_x - min_x) as f32 * (width - 1) as f32) as usize
        } else { width / 2 };
        
        let y = if max_y > min_y {
            ((obj.y - min_y) as f32 / (max_y - min_y) as f32 * (height - 1) as f32) as usize
        } else { height / 2 };
        
        if x < width && y < height {
            density[y][x] += 1;
        }
    }
    
    // Convert density to ASCII
    for y in 0..height {
        for x in 0..width {
            grid[y][x] = match density[y][x] {
                0 => ' ',
                1 => '·',
                2 => '░',
                3 => '▒',
                4 => '▓',
                _ => '█',
            };
        }
    }
    
    grid.iter()
        .map(|row| row.iter().collect::<String>())
        .collect::<Vec<_>>()
        .join("\n")
}

fn render_standard(objects: &[ArxObject], width: usize, height: usize) -> String {
    // Enhanced rendering with edge detection
    render_simple(objects, width, height) // Placeholder
}

fn render_cinematic(objects: &[ArxObject], width: usize, height: usize) -> String {
    // High quality rendering with shading
    render_simple(objects, width, height) // Placeholder
}

fn object_type_name(obj_type: u8) -> &'static str {
    use arxos_core::arxobject::object_types;
    
    match obj_type {
        t if t == object_types::WALL => "Wall",
        t if t == object_types::FLOOR => "Floor",
        t if t == object_types::CEILING => "Ceiling",
        t if t == object_types::DOOR => "Door",
        t if t == object_types::WINDOW => "Window",
        t if t == object_types::COLUMN => "Column",
        _ => "Generic",
    }
}

fn init_logger(verbosity: u8) {
    let level = match verbosity {
        0 => log::LevelFilter::Warn,
        1 => log::LevelFilter::Info,
        2 => log::LevelFilter::Debug,
        _ => log::LevelFilter::Trace,
    };
    
    env_logger::Builder::from_default_env()
        .filter_level(level)
        .init();
    
    debug!("Logger initialized at level: {:?}", level);
}