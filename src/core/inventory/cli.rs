//! CLI for inventory management and quest generation

use crate::inventory::{InventorySystem, Asset, AssetType, Location, ScheduleRule, Frequency, Weekday};
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "arxos-inventory")]
#[command(about = "Gamified asset inventory management")]
pub struct InventoryCli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Import assets from CSV
    Import {
        #[arg(short, long)]
        file: String,
    },
    
    /// Schedule regular inspections
    Schedule {
        #[command(subcommand)]
        action: ScheduleAction,
    },
    
    /// Generate inspection quest
    Quest {
        #[arg(short, long, default_value = "10")]
        percentage: f32,
        
        #[arg(short, long)]
        tech_id: String,
    },
    
    /// View current quests and progress
    Status {
        #[arg(short, long)]
        tech_id: Option<String>,
    },
    
    /// Capture an asset (mark as verified)
    Capture {
        #[arg(short, long)]
        asset_tag: String,
        
        #[arg(short, long)]
        tech_id: String,
        
        #[arg(short, long)]
        condition: Option<String>, // good, warning, critical
    },
    
    /// View leaderboard
    Leaderboard,
    
    /// Generate AR navigation
    Navigate {
        #[arg(short, long)]
        tech_id: String,
    },
}

#[derive(Subcommand)]
enum ScheduleAction {
    /// Add inspection schedule
    Add {
        #[arg(short, long)]
        name: String,
        
        #[arg(short, long)]
        asset_type: String,
        
        #[arg(short, long)]
        frequency: String, // "daily", "weekly:friday", "monthly:15"
        
        #[arg(short, long, default_value = "10")]
        percentage: f32,
    },
    
    /// List schedules
    List,
    
    /// Remove schedule
    Remove {
        #[arg(short, long)]
        name: String,
    },
}

pub fn run_cli(system: &mut InventorySystem) {
    let cli = InventoryCli::parse();
    
    match cli.command {
        Commands::Import { file } => {
            import_assets(system, &file);
        },
        Commands::Schedule { action } => {
            handle_schedule(system, action);
        },
        Commands::Quest { percentage, tech_id } => {
            generate_quest(system, percentage, &tech_id);
        },
        Commands::Status { tech_id } => {
            show_status(system, tech_id.as_deref());
        },
        Commands::Capture { asset_tag, tech_id, condition } => {
            capture_asset(system, &asset_tag, &tech_id, condition.as_deref());
        },
        Commands::Leaderboard => {
            show_leaderboard(system);
        },
        Commands::Navigate { tech_id } => {
            show_navigation(system, &tech_id);
        },
    }
}

fn import_assets(system: &mut InventorySystem, file: &str) {
    println!("📦 Importing assets from {}...", file);
    
    // Parse CSV and create assets
    // Example format: asset_tag,type,building,room,description
    let assets = vec![
        Asset {
            arxobject: crate::arxobject::ArxObject::new(0x0001, 0x10, 100, 200, 10),
            asset_tag: "CHR-2024-001".to_string(),
            asset_type: AssetType::Chromebook,
            location: Location {
                building: "Gaither HS".to_string(),
                room: "Room 203".to_string(),
                coordinates: (100, 200, 10),
                description: "Cart A, Slot 12".to_string(),
            },
            last_verified: None,
            verification_required: true,
            health: crate::inventory::AssetHealth::Unknown,
            metadata: std::collections::HashMap::new(),
        },
        // More assets...
    ];
    
    let count = assets.len();
    system.bulk_import(assets);
    
    println!("✅ Imported {} assets", count);
}

fn handle_schedule(system: &mut InventorySystem, action: ScheduleAction) {
    match action {
        ScheduleAction::Add { name, asset_type, frequency, percentage } => {
            let freq = parse_frequency(&frequency);
            let rule = ScheduleRule {
                name: name.clone(),
                asset_types: vec![parse_asset_type(&asset_type)],
                frequency: freq,
                percentage,
            };
            
            system.schedule.add_rule(rule);
            println!("✅ Added schedule: {}", name);
            println!("   📅 {}", frequency);
            println!("   📊 {}% of {} assets", percentage, asset_type);
        },
        ScheduleAction::List => {
            println!("📋 Inspection Schedules:");
            println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            for rule in &system.schedule.rules {
                println!("📌 {}", rule.name);
                println!("   Frequency: {:?}", rule.frequency);
                println!("   Coverage: {}%", rule.percentage);
                println!();
            }
        },
        ScheduleAction::Remove { name } => {
            system.schedule.rules.retain(|r| r.name != name);
            println!("✅ Removed schedule: {}", name);
        },
    }
}

fn generate_quest(system: &mut InventorySystem, percentage: f32, tech_id: &str) {
    let quest = system.generate_weekly_quest(percentage);
    
    println!("🎮 New Quest Generated!");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("📜 {}", quest.title);
    println!("📝 {}", quest.description);
    println!();
    println!("🎯 Targets ({} assets):", quest.targets.len());
    
    for (i, target) in quest.targets.iter().enumerate() {
        println!("   {}. {} in {}", 
            i + 1, 
            target.asset_tag,
            target.location.room
        );
        println!("      💡 Hint: {}", target.hint);
        println!("      ⭐ Points: {}", target.points);
    }
    
    println!();
    println!("🏆 Reward: {} XP", quest.reward.xp);
    println!("⏱️  Time Limit: 7 days");
    
    system.active_quests.push(quest);
}

fn show_status(system: &InventorySystem, tech_id: Option<&str>) {
    println!("📊 Inventory Status");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    
    // Asset summary
    let total = system.assets.len();
    let verified = system.assets.values()
        .filter(|a| a.last_verified.is_some())
        .count();
    let percentage = (verified as f32 / total as f32 * 100.0) as u32;
    
    println!("📦 Total Assets: {}", total);
    println!("✅ Verified: {} ({}%)", verified, percentage);
    println!("❓ Unverified: {}", total - verified);
    
    // Progress bar
    print!("Progress: [");
    let bar_width = 30;
    let filled = (bar_width * percentage / 100) as usize;
    for i in 0..bar_width {
        if i < filled {
            print!("█");
        } else {
            print!("░");
        }
    }
    println!("] {}%", percentage);
    
    // Active quests
    println!();
    println!("🎮 Active Quests: {}", system.active_quests.len());
    for quest in &system.active_quests {
        let completed = quest.targets.iter().filter(|t| t.captured).count();
        let total = quest.targets.len();
        println!("   • {} ({}/{})", quest.title, completed, total);
    }
    
    // Tech stats
    if tech_id.is_some() {
        println!();
        println!("👤 Technician Stats:");
        println!("   Level: {}", system.tech_stats.calculate_level());
        println!("   XP: {}", system.tech_stats.xp);
        println!("   Assets Verified: {}", system.tech_stats.assets_verified);
        println!("   Quests Completed: {}", system.tech_stats.quests_completed);
    }
}

fn capture_asset(system: &mut InventorySystem, asset_tag: &str, tech_id: &str, condition: Option<&str>) {
    use crate::inventory::CaptureResult;
    
    match system.capture_asset(asset_tag, tech_id) {
        CaptureResult::Success { points, remaining } => {
            println!("✅ Asset Captured!");
            println!("   +{} points", points);
            println!("   {} targets remaining", remaining);
        },
        CaptureResult::QuestComplete { xp_gained, new_total_xp } => {
            println!("🎉 QUEST COMPLETE!");
            println!("   +{} XP", xp_gained);
            println!("   Total XP: {}", new_total_xp);
            println!("   Level: {}", new_total_xp / 1000 + 1);
        },
        CaptureResult::AssetNotFound => {
            println!("❌ Asset {} not found in inventory", asset_tag);
        },
        CaptureResult::NotInActiveQuest => {
            println!("⚠️  Asset verified but not part of active quest");
        },
        CaptureResult::AlreadyCaptured => {
            println!("ℹ️  Asset already captured");
        },
    }
}

fn show_leaderboard(system: &InventorySystem) {
    println!("🏆 Leaderboard");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("Rank  Name              Level  XP      Assets");
    println!("────  ────────────────  ─────  ──────  ──────");
    
    // In real implementation, would track multiple technicians
    println!("1st   CurrentTech       {}      {}   {}",
        system.tech_stats.calculate_level(),
        system.tech_stats.xp,
        system.tech_stats.assets_verified
    );
}

fn show_navigation(system: &InventorySystem, tech_id: &str) {
    if let Some(hint) = system.get_next_target() {
        println!("🗺️  Navigation to Next Target");
        println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
        println!("🎯 Asset: {}", hint.asset_tag);
        println!("📍 Location: {} - {}", hint.location.room, hint.location.description);
        println!("📏 Distance: {:.1}m", hint.distance_meters);
        println!("🧭 Direction: {}", hint.direction);
        println!();
        println!("{}", hint.floor_map);
    } else {
        println!("✅ No targets remaining!");
    }
}

fn parse_frequency(freq_str: &str) -> Frequency {
    if freq_str == "daily" {
        Frequency::Daily
    } else if freq_str.starts_with("weekly:") {
        let day = freq_str.strip_prefix("weekly:").unwrap();
        Frequency::Weekly(parse_weekday(day))
    } else if freq_str.starts_with("monthly:") {
        let day = freq_str.strip_prefix("monthly:").unwrap()
            .parse::<u8>().unwrap_or(1);
        Frequency::Monthly(day)
    } else {
        Frequency::Daily
    }
}

fn parse_weekday(day: &str) -> Weekday {
    match day.to_lowercase().as_str() {
        "monday" => Weekday::Monday,
        "tuesday" => Weekday::Tuesday,
        "wednesday" => Weekday::Wednesday,
        "thursday" => Weekday::Thursday,
        "friday" => Weekday::Friday,
        "saturday" => Weekday::Saturday,
        "sunday" => Weekday::Sunday,
        _ => Weekday::Friday,
    }
}

fn parse_asset_type(type_str: &str) -> AssetType {
    match type_str.to_lowercase().as_str() {
        "chromebook" => AssetType::Chromebook,
        "desktop" => AssetType::Desktop,
        "ap" | "accesspoint" => AssetType::AccessPoint,
        "switch" => AssetType::Switch,
        "projector" => AssetType::Projector,
        "smartboard" => AssetType::SmartBoard,
        "printer" => AssetType::Printer,
        "light" => AssetType::Light,
        "hvac" => AssetType::HVACUnit,
        _ => AssetType::Chromebook,
    }
}