//! Scan to Database Integration
//! 
//! This module handles the flow from LiDAR scans to queryable building intelligence.
//! The database becomes the persistent memory of the building's spatial reality.

use crate::ply_parser::PlyParser;
use crate::point_cloud_processor::{PointCloudProcessor, ProcessingConfig};
use crate::database_impl::{ArxDatabase, DatabaseError};
use crate::arxobject::ArxObject;
use crate::error::{ArxError, Result};
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

/// Scan import statistics
#[derive(Debug)]
pub struct ImportStats {
    pub points_parsed: usize,
    pub objects_created: usize,
    pub objects_stored: usize,
    pub duplicates_skipped: usize,
    pub processing_time_ms: u64,
    pub compression_ratio: f64,
}

/// Manages the flow from scan files to database
pub struct ScanImporter {
    database: ArxDatabase,
    processor_config: ProcessingConfig,
}

impl ScanImporter {
    /// Create new scan importer
    pub fn new(database: ArxDatabase) -> Self {
        Self {
            database,
            processor_config: ProcessingConfig::default(),
        }
    }
    
    /// Import a PLY scan file into the database
    pub async fn import_scan(&mut self, 
        ply_path: &Path, 
        building_id: u16,
        scan_metadata: ScanMetadata,
    ) -> Result<ImportStats> {
        let start_time = SystemTime::now();
        
        println!("📥 Importing scan to database...");
        
        // Step 1: Parse PLY file
        println!("  1️⃣ Parsing PLY file...");
        let mut parser = PlyParser::new();
        parser.parse_file(ply_path)?;
        let points = parser.points();
        let points_parsed = points.len();
        println!("     ✓ Parsed {} points", points_parsed);
        
        // Step 2: Process into ArxObjects
        println!("  2️⃣ Processing to ArxObjects...");
        let mut processor = PointCloudProcessor::new(self.processor_config.clone());
        let arxobjects = processor.process(points, building_id)?;
        let objects_created = arxobjects.len();
        println!("     ✓ Created {} ArxObjects", objects_created);
        
        // Step 3: Store in database with deduplication
        println!("  3️⃣ Storing in database...");
        let (objects_stored, duplicates_skipped) = 
            self.store_with_deduplication(arxobjects, &scan_metadata).await?;
        println!("     ✓ Stored {} new objects ({} duplicates skipped)", 
            objects_stored, duplicates_skipped);
        
        // Step 4: Update spatial indices
        println!("  4️⃣ Updating spatial indices...");
        self.database.rebuild_spatial_index()?;
        println!("     ✓ Spatial index updated");
        
        // Step 5: Store scan metadata
        println!("  5️⃣ Recording scan metadata...");
        self.store_scan_metadata(&scan_metadata, building_id).await?;
        
        // Calculate statistics
        let processing_time_ms = start_time.elapsed()
            .map(|d| d.as_millis() as u64)
            .unwrap_or(0);
        
        let original_size = points_parsed * 12; // Approximate bytes per point
        let compressed_size = objects_created * 13; // 13 bytes per ArxObject
        let compression_ratio = original_size as f64 / compressed_size.max(1) as f64;
        
        let stats = ImportStats {
            points_parsed,
            objects_created,
            objects_stored,
            duplicates_skipped,
            processing_time_ms,
            compression_ratio,
        };
        
        println!("\n✅ Import complete!");
        println!("   Compression: {:.0}:1", compression_ratio);
        println!("   Time: {:.1}s", processing_time_ms as f64 / 1000.0);
        
        Ok(stats)
    }
    
    /// Store ArxObjects with deduplication
    async fn store_with_deduplication(
        &mut self,
        objects: Vec<ArxObject>,
        metadata: &ScanMetadata,
    ) -> Result<(usize, usize)> {
        let mut stored = 0;
        let mut skipped = 0;
        
        // Begin transaction for atomic storage
        self.database.begin_transaction()?;
        
        for obj in objects {
            // Check if object already exists at this location
            if self.object_exists(&obj)? {
                skipped += 1;
                
                // Update confidence/quality if new scan is better
                if metadata.scan_quality > self.get_object_quality(&obj)? {
                    self.update_object_quality(&obj, metadata.scan_quality)?;
                }
            } else {
                // Store new object
                self.database.insert(&obj)?;
                stored += 1;
            }
        }
        
        self.database.commit_transaction()?;
        
        Ok((stored, skipped))
    }
    
    /// Check if an object already exists at the same location
    fn object_exists(&self, obj: &ArxObject) -> Result<bool> {
        // Check within small radius (10cm) to handle scan alignment variance
        let nearby = self.database.find_within_radius(
            obj.x as f32, 
            obj.y as f32, 
            obj.z as f32, 
            100.0, // 10cm radius
        )?;
        
        // Check if any have the same type
        Ok(nearby.iter().any(|existing| existing.object_type == obj.object_type))
    }
    
    /// Get quality score for existing object
    fn get_object_quality(&self, _obj: &ArxObject) -> Result<f32> {
        // TODO: Implement quality tracking
        Ok(0.5)
    }
    
    /// Update object quality score
    fn update_object_quality(&mut self, obj: &ArxObject, quality: f32) -> Result<()> {
        // Store quality in properties or separate table
        let mut updated = *obj;
        updated.properties[3] = (quality * 255.0) as u8;
        self.database.update(&updated)?;
        Ok(())
    }
    
    /// Store scan metadata for provenance
    async fn store_scan_metadata(
        &mut self, 
        metadata: &ScanMetadata,
        building_id: u16,
    ) -> Result<()> {
        // This would store in a separate scans table
        // For now, we'll store as a special ArxObject
        let meta_obj = ArxObject {
            building_id,
            object_type: 0xFF, // Special type for metadata
            x: 0,
            y: 0, 
            z: 0,
            properties: [
                (metadata.scan_quality * 100.0) as u8,
                metadata.scanner_type as u8,
                0,
                0,
            ],
        };
        
        self.database.insert(&meta_obj)?;
        Ok(())
    }
}

/// Metadata about a scan
#[derive(Debug, Clone)]
pub struct ScanMetadata {
    pub scan_id: String,
    pub timestamp: u64,
    pub scanner_type: ScannerType,
    pub scan_quality: f32,
    pub operator_id: Option<String>,
    pub notes: Option<String>,
}

impl ScanMetadata {
    pub fn new(scanner_type: ScannerType) -> Self {
        Self {
            scan_id: uuid::Uuid::new_v4().to_string(),
            timestamp: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            scanner_type,
            scan_quality: 1.0,
            operator_id: None,
            notes: None,
        }
    }
}

/// Types of scanners
#[derive(Debug, Clone, Copy)]
#[repr(u8)]
pub enum ScannerType {
    IPhoneLidar = 1,
    TerrestrialLaser = 2,
    Photogrammetry = 3,
    StructuredLight = 4,
    TimeOfFlight = 5,
}

/// Database query interface for building intelligence
pub struct BuildingIntelligence {
    database: ArxDatabase,
}

impl BuildingIntelligence {
    pub fn new(database: ArxDatabase) -> Self {
        Self { database }
    }
    
    /// Query: "What's in room 127?"
    pub fn query_room(&self, room_bounds: RoomBounds) -> Result<Vec<ArxObject>> {
        self.database.find_in_bounds(
            room_bounds.min_x,
            room_bounds.max_x,
            room_bounds.min_y,
            room_bounds.max_y,
            room_bounds.min_z,
            room_bounds.max_z,
        )
    }
    
    /// Query: "Find all outlets on the second floor"
    pub fn find_objects_by_type_and_height(
        &self,
        object_type: u8,
        min_height: f32,
        max_height: f32,
    ) -> Result<Vec<ArxObject>> {
        self.database.query(
            "SELECT * FROM arxobjects 
             WHERE object_type = ?1 
             AND z >= ?2 AND z <= ?3",
            params![object_type, min_height as u16, max_height as u16],
        )
    }
    
    /// Query: "What equipment needs maintenance?"
    pub fn find_maintenance_candidates(&self) -> Result<Vec<ArxObject>> {
        // Objects with high usage or age (stored in properties)
        self.database.query(
            "SELECT * FROM arxobjects 
             WHERE object_type IN (?1, ?2, ?3)
             AND (properties[0] > 200 OR properties[1] > 180)",
            params![
                crate::arxobject::object_types::HVAC_VENT,
                crate::arxobject::object_types::ELECTRICAL_PANEL,
                crate::arxobject::object_types::LIGHT,
            ],
        )
    }
    
    /// Query: "Show heat map of activity"
    pub fn generate_activity_heatmap(&self, building_id: u16) -> Result<Vec<(u16, u16, u8)>> {
        // Return (x, y, intensity) for visualization
        let objects = self.database.get_building_objects(building_id)?;
        
        let mut heatmap = Vec::new();
        for obj in objects {
            // Activity level stored in properties[2]
            let activity = obj.properties[2];
            if activity > 0 {
                heatmap.push((obj.x, obj.y, activity));
            }
        }
        
        Ok(heatmap)
    }
}

/// Room boundary definition
#[derive(Debug)]
pub struct RoomBounds {
    pub min_x: f32,
    pub max_x: f32,
    pub min_y: f32,
    pub max_y: f32,
    pub min_z: f32,
    pub max_z: f32,
}

// Import uuid for scan IDs
use uuid;

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_scan_metadata_creation() {
        let metadata = ScanMetadata::new(ScannerType::IPhoneLidar);
        assert!(metadata.timestamp > 0);
        assert_eq!(metadata.scanner_type as u8, 1);
        assert_eq!(metadata.scan_quality, 1.0);
    }
}