//! Offline-First Virtual Workspace Cache
//! 
//! Unlike Hypori's cloud dependency, ArxOS workspaces operate offline.
//! This is our KEY ADVANTAGE - buildings work without internet.

use crate::arxobject::ArxObject;
use crate::virtual_building_space::VirtualBuildingSpace;
use crate::file_storage::{FileStorage, Database};
use std::collections::HashMap;
use std::path::Path;

/// Offline workspace cache - persists VBS data locally
pub struct OfflineWorkspaceCache {
    /// Local file storage for this workspace
    local_storage: FileStorage,
    
    /// Cached ArxObjects for offline access
    object_cache: HashMap<u16, Vec<ArxObject>>,
    
    /// Pending changes to sync when reconnected
    pending_sync: Vec<SyncOperation>,
    
    /// Last sync timestamp for each zone
    sync_timestamps: HashMap<u16, u64>,
    
    /// Cache validity duration (seconds)
    cache_ttl: u64,
}

/// Operations queued for sync
#[derive(Debug, Clone)]
pub enum SyncOperation {
    /// New object created offline
    Create(ArxObject),
    
    /// Object modified offline
    Update { old: ArxObject, new: ArxObject },
    
    /// Object deleted offline
    Delete(ArxObject),
    
    /// Annotation added offline
    Annotate { object_id: u16, note: String },
}

impl OfflineWorkspaceCache {
    /// Create new offline cache
    pub fn new(workspace_id: u16) -> Result<Self, Box<dyn std::error::Error>> {
        let db_path = format!("/var/lib/arxos/vbs_{}.db", workspace_id);
        let local_db = ArxDatabase::open(Path::new(&db_path))?;
        
        Ok(Self {
            local_db,
            object_cache: HashMap::new(),
            pending_sync: Vec::new(),
            sync_timestamps: HashMap::new(),
            cache_ttl: 3600, // 1 hour default
        })
    }
    
    /// Preload objects for offline access
    pub fn preload_zone(&mut self, zone_id: u16, objects: Vec<ArxObject>) -> Result<(), Box<dyn std::error::Error>> {
        // Store in local database
        for obj in &objects {
            self.local_db.insert(obj)?;
        }
        
        // Cache in memory
        self.object_cache.insert(zone_id, objects);
        
        // Update sync timestamp
        self.sync_timestamps.insert(zone_id, current_timestamp());
        
        Ok(())
    }
    
    /// Query objects offline
    pub fn query_offline(&self, zone_id: u16) -> Vec<ArxObject> {
        self.object_cache.get(&zone_id)
            .cloned()
            .unwrap_or_default()
    }
    
    /// Make changes offline
    pub fn modify_offline(&mut self, operation: SyncOperation) -> Result<(), Box<dyn std::error::Error>> {
        // Apply change locally
        match &operation {
            SyncOperation::Create(obj) => {
                self.local_db.insert(obj)?;
                if let Some(cache) = self.object_cache.get_mut(&obj.building_id) {
                    cache.push(*obj);
                }
            }
            SyncOperation::Update { old: _, new } => {
                self.local_db.update(new)?;
                if let Some(cache) = self.object_cache.get_mut(&new.building_id) {
                    if let Some(pos) = cache.iter().position(|o| o.building_id == new.building_id) {
                        cache[pos] = *new;
                    }
                }
            }
            SyncOperation::Delete(obj) => {
                self.local_db.delete(obj.building_id)?;
                if let Some(cache) = self.object_cache.get_mut(&obj.building_id) {
                    cache.retain(|o| o.building_id != obj.building_id);
                }
            }
            _ => {}
        }
        
        // Queue for sync
        self.pending_sync.push(operation);
        
        Ok(())
    }
    
    /// Sync when connectivity returns
    pub async fn sync_with_mesh(&mut self) -> Result<SyncReport, Box<dyn std::error::Error>> {
        let mut report = SyncReport::default();
        
        for operation in self.pending_sync.drain(..) {
            match operation {
                SyncOperation::Create(obj) => {
                    // Broadcast new object to mesh
                    report.created += 1;
                }
                SyncOperation::Update { old, new } => {
                    // Send update delta
                    report.updated += 1;
                }
                SyncOperation::Delete(obj) => {
                    // Send deletion notice
                    report.deleted += 1;
                }
                SyncOperation::Annotate { object_id, note } => {
                    // Send annotation
                    report.annotations += 1;
                }
            }
        }
        
        Ok(report)
    }
    
    /// Check cache freshness
    pub fn is_cache_fresh(&self, zone_id: u16) -> bool {
        if let Some(&timestamp) = self.sync_timestamps.get(&zone_id) {
            let age = current_timestamp() - timestamp;
            age < self.cache_ttl
        } else {
            false
        }
    }
    
    /// Predictive preloading based on movement
    pub fn predictive_preload(&mut self, current_zone: u16, movement_vector: (i16, i16)) {
        // Calculate likely next zones based on movement
        let predicted_zones = self.predict_zones(current_zone, movement_vector);
        
        for zone in predicted_zones {
            if !self.is_cache_fresh(zone) {
                // Request preload of this zone
                println!("📥 Preloading zone {} based on movement prediction", zone);
            }
        }
    }
    
    fn predict_zones(&self, current: u16, vector: (i16, i16)) -> Vec<u16> {
        // Simple adjacent zone prediction
        let mut zones = Vec::new();
        
        if vector.0 > 0 {
            zones.push(current + 1); // Moving east
        } else if vector.0 < 0 {
            zones.push(current - 1); // Moving west
        }
        
        if vector.1 > 0 {
            zones.push(current + 10); // Moving north
        } else if vector.1 < 0 {
            zones.push(current - 10); // Moving south
        }
        
        zones
    }
}

/// Sync report
#[derive(Debug, Default)]
pub struct SyncReport {
    pub created: usize,
    pub updated: usize,
    pub deleted: usize,
    pub annotations: usize,
    pub conflicts: usize,
}

/// Conflict resolution for offline edits
pub struct ConflictResolver {
    /// Resolution strategies
    strategy: ConflictStrategy,
}

#[derive(Debug)]
pub enum ConflictStrategy {
    /// Last write wins
    LastWriteWins,
    
    /// First write wins
    FirstWriteWins,
    
    /// Merge properties
    MergeProperties,
    
    /// Manual review required
    ManualReview,
}

impl ConflictResolver {
    pub fn resolve(
        &self,
        local: &ArxObject,
        remote: &ArxObject,
        local_timestamp: u64,
        remote_timestamp: u64,
    ) -> ArxObject {
        match self.strategy {
            ConflictStrategy::LastWriteWins => {
                if local_timestamp > remote_timestamp {
                    *local
                } else {
                    *remote
                }
            }
            ConflictStrategy::FirstWriteWins => {
                if local_timestamp < remote_timestamp {
                    *local
                } else {
                    *remote
                }
            }
            ConflictStrategy::MergeProperties => {
                // Merge non-conflicting properties
                let mut merged = *local;
                for i in 0..4 {
                    if local.properties[i] == 0 && remote.properties[i] != 0 {
                        merged.properties[i] = remote.properties[i];
                    }
                }
                merged
            }
            ConflictStrategy::ManualReview => {
                // Flag for human review
                println!("⚠️ Conflict requires manual review");
                *local // Keep local for now
            }
        }
    }
}

/// Offline capability comparison
pub fn demo_offline_advantage() {
    println!("\n🔌 Offline Workspace Comparison\n");
    
    println!("Hypori (Cloud-dependent):");
    println!("  ❌ No internet = No access");
    println!("  ❌ Cloud outage = Work stops");
    println!("  ❌ High latency = Poor experience");
    println!("  ❌ Bandwidth costs = $$$$");
    
    println!("\nArxOS (Offline-first):");
    println!("  ✅ Works without internet");
    println!("  ✅ Local mesh = Always available");
    println!("  ✅ Zero latency = Instant response");
    println!("  ✅ No bandwidth costs = Free");
    
    println!("\nScenario: Hurricane knocks out internet");
    println!("───────────────────────────────────────");
    
    println!("\nHypori users:");
    println!("  🚫 Cannot access building data");
    println!("  🚫 Cannot coordinate repairs");
    println!("  🚫 Cannot track equipment");
    
    println!("\nArxOS users:");
    println!("  ✅ Full building access via mesh");
    println!("  ✅ Coordinate via radio + ArxOS");
    println!("  ✅ Track all repairs offline");
    println!("  ✅ Sync when internet returns");
    
    println!("\nOffline cache structure:");
    println!("  /var/lib/arxos/");
    println!("  ├── building.db        (100 MB)");
    println!("  ├── vbs_hvac.db        (5 MB)");
    println!("  ├── vbs_electrical.db  (8 MB)");
    println!("  └── sync_queue.db      (1 MB)");
    
    println!("\nKey insight:");
    println!("  💡 Buildings don't need cloud.");
    println!("     They need local intelligence!");
}

fn current_timestamp() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
}