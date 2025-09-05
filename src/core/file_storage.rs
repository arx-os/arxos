//! File-Based Storage System for ArxOS
//! 
//! Simple file-based storage system that replaces SQLite database functionality.
//! Optimized for RF mesh environments with minimal dependencies.

use std::collections::HashMap;
use std::fs::{File, OpenOptions, create_dir_all, read_dir, remove_file};
use std::io::{BufReader, BufWriter, BufRead, Write, Read, Seek, SeekFrom};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use uuid::Uuid;
use serde::{Serialize, Deserialize};
use serde_json;
use crate::{ArxObject, error::ArxosError};

/// Configuration for file storage
#[derive(Debug, Clone)]
pub struct FileStorageConfig {
    pub base_path: PathBuf,
    pub max_objects_per_file: usize,
    pub enable_compression: bool,
}

impl Default for FileStorageConfig {
    fn default() -> Self {
        Self {
            base_path: PathBuf::from("./arxos_data"),
            max_objects_per_file: 1000,
            enable_compression: false,
        }
    }
}

/// File-based storage implementation
#[derive(Debug)]
pub struct FileStorage {
    config: FileStorageConfig,
    index_cache: HashMap<Uuid, ObjectMetadata>,
}

/// Metadata for stored objects
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectMetadata {
    pub id: Uuid,
    pub object_type: u8,
    pub building_id: u32,
    pub created_at: u64,
    pub updated_at: u64,
    pub file_path: String,
    pub file_offset: usize,
}

/// Statistics about the storage system
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageStats {
    pub total_objects: usize,
    pub total_files: usize,
    pub storage_size_bytes: u64,
    pub index_size: usize,
    pub last_updated: u64,
}

/// Stored ArxObject with metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StoredObject {
    pub id: Uuid,
    pub arxobject: ArxObject,
    pub created_at: u64,
    pub updated_at: u64,
    pub tags: Vec<String>,
}

impl FileStorage {
    /// Create a new file storage instance
    pub fn new(config: FileStorageConfig) -> Result<Self, ArxosError> {
        // Create base directory if it doesn't exist
        create_dir_all(&config.base_path)
            .map_err(|e| ArxosError::Io(format!("Failed to create storage directory: {}", e)))?;
        
        let mut storage = FileStorage {
            config,
            index_cache: HashMap::new(),
        };
        
        // Load existing index
        storage.load_index()?;
        
        Ok(storage)
    }
    
    /// Store an ArxObject
    pub fn store_object(&mut self, object: &ArxObject, tags: Vec<String>) -> Result<Uuid, ArxosError> {
        let id = Uuid::new_v4();
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        let stored_object = StoredObject {
            id,
            arxobject: *object,
            created_at: now,
            updated_at: now,
            tags,
        };
        
        // Serialize object
        let object_data = serde_json::to_string(&stored_object)
            .map_err(|e| ArxosError::Serialization(format!("Failed to serialize object: {}", e)))?;
        
        // Determine file path based on building ID and object type
        let file_path = self.get_file_path(object.building_id, object.object_type());
        
        // Append to file
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&file_path)
            .map_err(|e| ArxosError::Io(format!("Failed to open file: {}", e)))?;
        
        let file_offset = file.seek(SeekFrom::End(0))
            .map_err(|e| ArxosError::Io(format!("Failed to seek file: {}", e)))? as usize;
        
        writeln!(file, "{}", object_data)
            .map_err(|e| ArxosError::Io(format!("Failed to write to file: {}", e)))?;
        
        // Update index
        let metadata = ObjectMetadata {
            id,
            object_type: object.object_type(),
            building_id: object.building_id,
            created_at: now,
            updated_at: now,
            file_path: file_path.to_string_lossy().to_string(),
            file_offset,
        };
        
        self.index_cache.insert(id, metadata);
        self.save_index()?;
        
        Ok(id)
    }
    
    /// Retrieve an object by ID
    pub fn get_object(&self, id: &Uuid) -> Result<Option<StoredObject>, ArxosError> {
        let metadata = match self.index_cache.get(id) {
            Some(meta) => meta,
            None => return Ok(None),
        };
        
        let file = File::open(&metadata.file_path)
            .map_err(|e| ArxosError::Io(format!("Failed to open file: {}", e)))?;
        
        let mut reader = BufReader::new(file);
        reader.seek(SeekFrom::Start(metadata.file_offset as u64))
            .map_err(|e| ArxosError::Io(format!("Failed to seek file: {}", e)))?;
        
        let mut line = String::new();
        reader.read_line(&mut line)
            .map_err(|e| ArxosError::Io(format!("Failed to read line: {}", e)))?;
        
        let stored_object: StoredObject = serde_json::from_str(&line.trim())
            .map_err(|e| ArxosError::Serialization(format!("Failed to deserialize object: {}", e)))?;
        
        Ok(Some(stored_object))
    }
    
    /// Get all objects for a building
    pub fn get_building_objects(&self, building_id: u32) -> Result<Vec<StoredObject>, ArxosError> {
        let mut objects = Vec::new();
        
        for (id, metadata) in &self.index_cache {
            if metadata.building_id == building_id {
                if let Some(object) = self.get_object(id)? {
                    objects.push(object);
                }
            }
        }
        
        Ok(objects)
    }
    
    /// Get objects by type
    pub fn get_objects_by_type(&self, object_type: u8) -> Result<Vec<StoredObject>, ArxosError> {
        let mut objects = Vec::new();
        
        for (id, metadata) in &self.index_cache {
            if metadata.object_type == object_type {
                if let Some(object) = self.get_object(id)? {
                    objects.push(object);
                }
            }
        }
        
        Ok(objects)
    }
    
    /// Delete an object
    pub fn delete_object(&mut self, id: &Uuid) -> Result<bool, ArxosError> {
        if self.index_cache.remove(id).is_some() {
            self.save_index()?;
            // Note: In a production system, you might want to implement
            // file compaction to actually remove the data from disk
            Ok(true)
        } else {
            Ok(false)
        }
    }
    
    /// Get storage statistics
    pub fn get_stats(&self) -> Result<StorageStats, ArxosError> {
        let total_objects = self.index_cache.len();
        let mut file_set = std::collections::HashSet::new();
        let mut storage_size = 0u64;
        
        // Count unique files and calculate total size
        for metadata in self.index_cache.values() {
            file_set.insert(&metadata.file_path);
        }
        
        for file_path in &file_set {
            if let Ok(metadata) = std::fs::metadata(file_path) {
                storage_size += metadata.len();
            }
        }
        
        let stats = StorageStats {
            total_objects,
            total_files: file_set.len(),
            storage_size_bytes: storage_size,
            index_size: self.index_cache.len(),
            last_updated: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        };
        
        Ok(stats)
    }
    
    /// Compact storage by removing deleted entries
    pub fn compact(&mut self) -> Result<(), ArxosError> {
        // This is a simplified compaction - in production you might want
        // to rewrite files to remove deleted entries
        self.save_index()?;
        Ok(())
    }
    
    /// Get file path for storing objects of a given type and building
    fn get_file_path(&self, building_id: u32, object_type: u8) -> PathBuf {
        let filename = format!("building_{}_type_{}.jsonl", building_id, object_type);
        self.config.base_path.join(filename)
    }
    
    /// Load the index from disk
    fn load_index(&mut self) -> Result<(), ArxosError> {
        let index_path = self.config.base_path.join("index.json");
        
        if !index_path.exists() {
            return Ok(());
        }
        
        let file = File::open(&index_path)
            .map_err(|e| ArxosError::Io(format!("Failed to open index: {}", e)))?;
        
        let reader = BufReader::new(file);
        self.index_cache = serde_json::from_reader(reader)
            .map_err(|e| ArxosError::Serialization(format!("Failed to load index: {}", e)))?;
        
        Ok(())
    }
    
    /// Save the index to disk
    fn save_index(&self) -> Result<(), ArxosError> {
        let index_path = self.config.base_path.join("index.json");
        
        let file = File::create(&index_path)
            .map_err(|e| ArxosError::Io(format!("Failed to create index: {}", e)))?;
        
        let writer = BufWriter::new(file);
        serde_json::to_writer_pretty(writer, &self.index_cache)
            .map_err(|e| ArxosError::Serialization(format!("Failed to save index: {}", e)))?;
        
        Ok(())
    }
}

/// Simple ArxObject database interface for compatibility
pub trait Database {
    fn store_object(&mut self, object: &ArxObject) -> Result<Uuid, ArxosError>;
    fn get_object(&self, id: &Uuid) -> Result<Option<ArxObject>, ArxosError>;
    fn get_building_objects(&self, building_id: u32) -> Result<Vec<ArxObject>, ArxosError>;
    fn get_stats(&self) -> Result<StorageStats, ArxosError>;
}

impl Database for FileStorage {
    fn store_object(&mut self, object: &ArxObject) -> Result<Uuid, ArxosError> {
        self.store_object(object, Vec::new())
    }
    
    fn get_object(&self, id: &Uuid) -> Result<Option<ArxObject>, ArxosError> {
        Ok(self.get_object(id)?.map(|stored| stored.arxobject))
    }
    
    fn get_building_objects(&self, building_id: u32) -> Result<Vec<ArxObject>, ArxosError> {
        Ok(self.get_building_objects(building_id)?
           .into_iter()
           .map(|stored| stored.arxobject)
           .collect())
    }
    
    fn get_stats(&self) -> Result<StorageStats, ArxosError> {
        self.get_stats()
    }
}

/// Simple in-memory database for testing and lightweight use
#[derive(Debug)]
pub struct MemoryDatabase {
    objects: HashMap<Uuid, ArxObject>,
    building_index: HashMap<u32, Vec<Uuid>>,
}

impl MemoryDatabase {
    pub fn new() -> Self {
        Self {
            objects: HashMap::new(),
            building_index: HashMap::new(),
        }
    }
    
    pub fn len(&self) -> usize {
        self.objects.len()
    }
    
    pub fn is_empty(&self) -> bool {
        self.objects.is_empty()
    }
}

impl Database for MemoryDatabase {
    fn store_object(&mut self, object: &ArxObject) -> Result<Uuid, ArxosError> {
        let id = Uuid::new_v4();
        self.objects.insert(id, *object);
        
        // Update building index
        self.building_index
            .entry(object.building_id)
            .or_insert_with(Vec::new)
            .push(id);
        
        Ok(id)
    }
    
    fn get_object(&self, id: &Uuid) -> Result<Option<ArxObject>, ArxosError> {
        Ok(self.objects.get(id).copied())
    }
    
    fn get_building_objects(&self, building_id: u32) -> Result<Vec<ArxObject>, ArxosError> {
        let mut objects = Vec::new();
        
        if let Some(object_ids) = self.building_index.get(&building_id) {
            for id in object_ids {
                if let Some(object) = self.objects.get(id) {
                    objects.push(*object);
                }
            }
        }
        
        Ok(objects)
    }
    
    fn get_stats(&self) -> Result<StorageStats, ArxosError> {
        Ok(StorageStats {
            total_objects: self.objects.len(),
            total_files: 0,
            storage_size_bytes: (self.objects.len() * std::mem::size_of::<ArxObject>()) as u64,
            index_size: self.building_index.len(),
            last_updated: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::arxobject::object_types;
    use tempfile::TempDir;
    
    #[test]
    fn test_memory_database() {
        let mut db = MemoryDatabase::new();
        
        let object = ArxObject::new(0x1234, object_types::OUTLET, 100, 200, 150);
        let id = db.store_object(&object).unwrap();
        
        let retrieved = db.get_object(&id).unwrap().unwrap();
        assert_eq!(object, retrieved);
        
        let stats = db.get_stats().unwrap();
        assert_eq!(stats.total_objects, 1);
    }
    
    #[test]
    fn test_file_storage() {
        let temp_dir = TempDir::new().unwrap();
        let config = FileStorageConfig {
            base_path: temp_dir.path().to_path_buf(),
            ..Default::default()
        };
        
        let mut storage = FileStorage::new(config).unwrap();
        
        let object = ArxObject::new(0x1234, object_types::OUTLET, 100, 200, 150);
        let id = storage.store_object(&object, vec!["test".to_string()]).unwrap();
        
        let stored = storage.get_object(&id).unwrap().unwrap();
        assert_eq!(object, stored.arxobject);
        assert_eq!(stored.tags, vec!["test".to_string()]);
        
        let stats = storage.get_stats().unwrap();
        assert_eq!(stats.total_objects, 1);
    }
    
    #[test]
    fn test_building_objects() {
        let mut db = MemoryDatabase::new();
        
        let object1 = ArxObject::new(0x1234, object_types::OUTLET, 100, 200, 150);
        let object2 = ArxObject::new(0x5678, object_types::OUTLET, 300, 400, 350);
        
        db.store_object(&object1).unwrap();
        db.store_object(&object2).unwrap();
        
        let building_objects = db.get_building_objects(100).unwrap();
        assert_eq!(building_objects.len(), 2);
    }
}