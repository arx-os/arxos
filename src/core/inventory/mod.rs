//! Asset Inventory System - Gamified inspection workflows
//! 
//! Pokemon Go for IT inventory and building maintenance

pub mod asset;
pub mod schedule;
pub mod quest;

use crate::arxobject::ArxObject;
use std::collections::HashMap;
use std::time::{SystemTime, Duration};

/// IT Asset as ArxObject with metadata
#[derive(Clone, Debug)]
pub struct Asset {
    pub arxobject: ArxObject,
    pub asset_tag: String,
    pub asset_type: AssetType,
    pub location: Location,
    pub last_verified: Option<SystemTime>,
    pub verification_required: bool,
    pub health: AssetHealth,
    pub metadata: HashMap<String, String>,
}

#[derive(Clone, Debug, PartialEq)]
pub enum AssetType {
    // IT Assets
    Chromebook,
    Desktop,
    AccessPoint,
    Switch,
    Projector,
    SmartBoard,
    Printer,
    
    // Building Systems
    Light,
    HVACUnit,
    FireExtinguisher,
    ExitSign,
    SecurityCamera,
    DoorLock,
}

#[derive(Clone, Debug)]
pub struct Location {
    pub building: String,
    pub room: String,
    pub coordinates: (i16, i16, i16), // ArxObject coordinates
    pub description: String, // "Northwest corner, mounted on wall"
}

#[derive(Clone, Debug, PartialEq)]
pub enum AssetHealth {
    Good,
    Warning,      // Needs attention soon
    Critical,     // Needs immediate attention  
    Unknown,      // Not verified recently
    Missing,      // Expected but not found
}

/// Inventory management system
pub struct InventorySystem {
    pub assets: HashMap<String, Asset>,
    pub schedule: InspectionSchedule,
    pub active_quests: Vec<InspectionQuest>,
    pub completed_quests: Vec<CompletedQuest>,
    pub tech_stats: TechnicianStats,
}

impl InventorySystem {
    pub fn new() -> Self {
        Self {
            assets: HashMap::new(),
            schedule: InspectionSchedule::new(),
            active_quests: Vec::new(),
            completed_quests: Vec::new(),
            tech_stats: TechnicianStats::new(),
        }
    }

    /// Import assets from CSV or database
    pub fn bulk_import(&mut self, assets: Vec<Asset>) {
        for asset in assets {
            self.assets.insert(asset.asset_tag.clone(), asset);
        }
    }

    /// Generate weekly inspection quest
    pub fn generate_weekly_quest(&mut self, percentage: f32) -> InspectionQuest {
        let total = self.assets.len();
        let to_inspect = ((total as f32 * percentage / 100.0).ceil() as usize).max(1);
        
        // Randomly select assets, prioritizing those not recently verified
        let mut candidates: Vec<_> = self.assets.values()
            .filter(|a| a.verification_required || 
                       a.last_verified.is_none() ||
                       a.last_verified.unwrap().elapsed().unwrap() > Duration::from_secs(30 * 24 * 3600))
            .collect();
        
        // Shuffle and take required number
        use rand::seq::SliceRandom;
        let mut rng = rand::thread_rng();
        candidates.shuffle(&mut rng);
        
        let targets: Vec<QuestTarget> = candidates.iter()
            .take(to_inspect)
            .map(|asset| QuestTarget {
                asset_tag: asset.asset_tag.clone(),
                location: asset.location.clone(),
                asset_type: asset.asset_type.clone(),
                points: calculate_points(&asset.asset_type),
                hint: generate_hint(asset),
                captured: false,
            })
            .collect();

        InspectionQuest {
            id: generate_quest_id(),
            title: format!("Weekly Inventory Hunt - {} assets", targets.len()),
            description: format!("Locate and verify {} assets throughout the building", targets.len()),
            targets,
            reward: QuestReward {
                xp: to_inspect as u32 * 10,
                badges: vec![],
                title: None,
            },
            time_limit: Duration::from_secs(7 * 24 * 3600), // 1 week
            created: SystemTime::now(),
            quest_type: QuestType::Weekly,
        }
    }

    /// Process asset "capture" from AR app
    pub fn capture_asset(&mut self, asset_tag: &str, tech_id: &str) -> CaptureResult {
        // Find asset
        let asset = match self.assets.get_mut(asset_tag) {
            Some(a) => a,
            None => return CaptureResult::AssetNotFound,
        };

        // Update asset status
        asset.last_verified = Some(SystemTime::now());
        asset.verification_required = false;
        asset.health = AssetHealth::Good; // Or based on tech input

        // Find active quest with this target
        for quest in &mut self.active_quests {
            for target in &mut quest.targets {
                if target.asset_tag == asset_tag && !target.captured {
                    target.captured = true;
                    
                    // Update tech stats
                    self.tech_stats.assets_verified += 1;
                    self.tech_stats.xp += target.points;
                    
                    // Check if quest complete
                    if quest.targets.iter().all(|t| t.captured) {
                        self.tech_stats.quests_completed += 1;
                        self.tech_stats.xp += quest.reward.xp;
                        
                        return CaptureResult::QuestComplete {
                            xp_gained: quest.reward.xp,
                            new_total_xp: self.tech_stats.xp,
                        };
                    }
                    
                    return CaptureResult::Success {
                        points: target.points,
                        remaining: quest.targets.iter().filter(|t| !t.captured).count(),
                    };
                }
            }
        }

        CaptureResult::NotInActiveQuest
    }

    /// Get next inspection target with navigation hints
    pub fn get_next_target(&self) -> Option<NavigationHint> {
        for quest in &self.active_quests {
            for target in &quest.targets {
                if !target.captured {
                    return Some(NavigationHint {
                        asset_tag: target.asset_tag.clone(),
                        location: target.location.clone(),
                        distance_meters: calculate_distance(&target.location),
                        direction: calculate_direction(&target.location),
                        floor_map: generate_floor_map(&target.location),
                    });
                }
            }
        }
        None
    }
}

/// Inspection quest (like Pokemon Go daily quests)
#[derive(Clone, Debug)]
pub struct InspectionQuest {
    pub id: String,
    pub title: String,
    pub description: String,
    pub targets: Vec<QuestTarget>,
    pub reward: QuestReward,
    pub time_limit: Duration,
    pub created: SystemTime,
    pub quest_type: QuestType,
}

#[derive(Clone, Debug)]
pub struct QuestTarget {
    pub asset_tag: String,
    pub location: Location,
    pub asset_type: AssetType,
    pub points: u32,
    pub hint: String,
    pub captured: bool,
}

#[derive(Clone, Debug)]
pub enum QuestType {
    Daily,
    Weekly,
    Monthly,
    Emergency,
    Special,
}

#[derive(Clone, Debug)]
pub struct QuestReward {
    pub xp: u32,
    pub badges: Vec<String>,
    pub title: Option<String>, // "Chromebook Master"
}

/// Result of capturing an asset
pub enum CaptureResult {
    Success { points: u32, remaining: usize },
    QuestComplete { xp_gained: u32, new_total_xp: u32 },
    AssetNotFound,
    NotInActiveQuest,
    AlreadyCaptured,
}

/// Navigation hint for AR overlay
pub struct NavigationHint {
    pub asset_tag: String,
    pub location: Location,
    pub distance_meters: f32,
    pub direction: String, // "Northwest, up one floor"
    pub floor_map: String, // ASCII mini-map
}

/// Technician stats and achievements
#[derive(Clone, Debug)]
pub struct TechnicianStats {
    pub xp: u32,
    pub level: u32,
    pub assets_verified: u32,
    pub quests_completed: u32,
    pub streak_days: u32,
    pub badges: Vec<Badge>,
}

impl TechnicianStats {
    pub fn new() -> Self {
        Self {
            xp: 0,
            level: 1,
            assets_verified: 0,
            quests_completed: 0,
            streak_days: 0,
            badges: Vec::new(),
        }
    }

    pub fn calculate_level(&self) -> u32 {
        (self.xp / 1000) + 1 // Level up every 1000 XP
    }
}

#[derive(Clone, Debug)]
pub struct Badge {
    pub name: String,
    pub description: String,
    pub icon: String, // ASCII art icon
    pub earned: SystemTime,
}

/// Inspection schedule generator
pub struct InspectionSchedule {
    pub rules: Vec<ScheduleRule>,
}

impl InspectionSchedule {
    pub fn new() -> Self {
        Self { rules: Vec::new() }
    }

    pub fn add_rule(&mut self, rule: ScheduleRule) {
        self.rules.push(rule);
    }

    pub fn generate_daily_tasks(&self) -> Vec<InspectionQuest> {
        // Generate tasks based on rules
        let mut tasks = Vec::new();
        
        for rule in &self.rules {
            if rule.should_run_today() {
                // Generate quest based on rule
                // This would create specific inspection quests
            }
        }
        
        tasks
    }
}

#[derive(Clone, Debug)]
pub struct ScheduleRule {
    pub name: String,
    pub asset_types: Vec<AssetType>,
    pub frequency: Frequency,
    pub percentage: f32,
}

impl ScheduleRule {
    pub fn should_run_today(&self) -> bool {
        // Check if this rule applies today
        match self.frequency {
            Frequency::Daily => true,
            Frequency::Weekly(day) => {
                // Check if today is the specified day
                true // Simplified
            },
            Frequency::Monthly(day) => {
                // Check if today is the specified day of month
                false // Simplified
            },
        }
    }
}

#[derive(Clone, Debug)]
pub enum Frequency {
    Daily,
    Weekly(Weekday),
    Monthly(u8), // Day of month
}

#[derive(Clone, Debug)]
pub enum Weekday {
    Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday,
}

#[derive(Clone, Debug)]
pub struct CompletedQuest {
    pub quest: InspectionQuest,
    pub completed: SystemTime,
    pub tech_id: String,
}

// Helper functions
fn calculate_points(asset_type: &AssetType) -> u32 {
    match asset_type {
        AssetType::Chromebook => 10,
        AssetType::AccessPoint => 25,
        AssetType::Switch => 30,
        AssetType::Projector => 20,
        _ => 15,
    }
}

fn generate_hint(asset: &Asset) -> String {
    format!("{} - {}", asset.location.room, asset.location.description)
}

fn generate_quest_id() -> String {
    format!("quest_{}", SystemTime::now().duration_since(SystemTime::UNIX_EPOCH).unwrap().as_secs())
}

fn calculate_distance(location: &Location) -> f32 {
    // Calculate distance from current position
    50.0 // Placeholder
}

fn calculate_direction(location: &Location) -> String {
    "Head northwest, up one floor".to_string() // Placeholder
}

fn generate_floor_map(location: &Location) -> String {
    // Generate ASCII mini-map
    r#"
    ┌───┬───┬───┐
    │   │ X │   │  X = Target
    ├───┼───┼───┤  @ = You
    │   │   │   │
    ├───┼───┼───┤
    │ @ │   │   │
    └───┴───┴───┘
    "#.to_string()
}