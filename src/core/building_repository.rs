//! Building Repository - Git-like Version Control for Buildings
//! 
//! Buildings have a "main" branch that represents truth.
//! Contractors work in branches and propose changes via merge requests.
//! This ensures building integrity while allowing field work.

use crate::arxobject::ArxObject;
use crate::simple_access_control::SimpleAccess;
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

/// Building repository with Git-like branching
pub struct BuildingRepository {
    /// Building identifier
    pub building_id: u16,
    
    /// Main branch - the source of truth
    pub main_branch: BuildingBranch,
    
    /// Active branches (contractor workspaces)
    pub branches: HashMap<String, BuildingBranch>,
    
    /// Merge requests awaiting approval
    pub merge_requests: Vec<MergeRequest>,
    
    /// History of all merges
    pub merge_history: Vec<MergeLog>,
}

/// A branch represents a view/version of the building
#[derive(Debug, Clone)]
pub struct BuildingBranch {
    /// Branch name (e.g., "main", "hvac-repair-2024-01-15")
    pub name: String,
    
    /// Branch owner (user_id or "system")
    pub owner: String,
    
    /// Base commit this branched from
    pub base_commit: CommitHash,
    
    /// Current state of ArxObjects in this branch
    pub objects: HashMap<u16, ArxObject>,
    
    /// Changes made in this branch
    pub changes: Vec<BuildingChange>,
    
    /// Branch metadata
    pub created_at: u64,
    pub updated_at: u64,
    pub expires_at: Option<u64>,
}

/// A change to the building
#[derive(Debug, Clone)]
pub enum BuildingChange {
    /// Add new object (e.g., installed new equipment)
    Add {
        object: ArxObject,
        reason: String,
        timestamp: u64,
    },
    
    /// Modify existing object (e.g., repaired, adjusted)
    Modify {
        object_id: u16,
        old: ArxObject,
        new: ArxObject,
        reason: String,
        timestamp: u64,
    },
    
    /// Remove object (e.g., decommissioned equipment)
    Remove {
        object: ArxObject,
        reason: String,
        timestamp: u64,
    },
    
    /// Annotate without changing (e.g., inspection notes)
    Annotate {
        object_id: u16,
        note: String,
        severity: Severity,
        timestamp: u64,
    },
}

/// Severity levels for annotations
#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum Severity {
    Info = 0,
    Warning = 1,
    Critical = 2,
    Emergency = 3,
}

/// Merge request from branch to main
#[derive(Debug, Clone)]
pub struct MergeRequest {
    /// Unique MR identifier
    pub mr_id: u32,
    
    /// Source branch name
    pub source_branch: String,
    
    /// Target (usually "main")
    pub target_branch: String,
    
    /// Who created this MR
    pub author: String,
    
    /// Title and description
    pub title: String,
    pub description: String,
    
    /// Changes to be merged
    pub changes: Vec<BuildingChange>,
    
    /// Review status
    pub status: MergeStatus,
    
    /// Reviewers and approvals
    pub reviewers: Vec<String>,
    pub approvals: Vec<Approval>,
    
    /// Timestamps
    pub created_at: u64,
    pub updated_at: u64,
}

#[derive(Debug, Clone, Copy)]
pub enum MergeStatus {
    Open,
    Approved,
    Merged,
    Rejected,
    Expired,
}

#[derive(Debug, Clone)]
pub struct Approval {
    pub reviewer: String,
    pub approved: bool,
    pub comment: String,
    pub timestamp: u64,
}

/// Log of merged changes
#[derive(Debug, Clone)]
pub struct MergeLog {
    pub commit_hash: CommitHash,
    pub mr_id: u32,
    pub author: String,
    pub merged_by: String,
    pub change_count: usize,
    pub timestamp: u64,
    pub description: String,
}

/// Simple commit hash
pub type CommitHash = [u8; 8];

impl BuildingRepository {
    /// Create new repository for a building
    pub fn new(building_id: u16) -> Self {
        let main_branch = BuildingBranch {
            name: "main".to_string(),
            owner: "system".to_string(),
            base_commit: [0; 8],
            objects: HashMap::new(),
            changes: Vec::new(),
            created_at: current_timestamp(),
            updated_at: current_timestamp(),
            expires_at: None,
        };
        
        Self {
            building_id,
            main_branch,
            branches: HashMap::new(),
            merge_requests: Vec::new(),
            merge_history: Vec::new(),
        }
    }
    
    /// Create a branch for a contractor
    pub fn create_branch(
        &mut self,
        branch_name: &str,
        owner: &str,
        expires_hours: u64,
    ) -> Result<&BuildingBranch, String> {
        if self.branches.contains_key(branch_name) {
            return Err("Branch already exists".to_string());
        }
        
        // Clone main branch as starting point
        let mut branch = self.main_branch.clone();
        branch.name = branch_name.to_string();
        branch.owner = owner.to_string();
        branch.base_commit = self.calculate_commit_hash(&self.main_branch);
        branch.changes = Vec::new();
        branch.created_at = current_timestamp();
        branch.updated_at = current_timestamp();
        branch.expires_at = Some(current_timestamp() + (expires_hours * 3600));
        
        self.branches.insert(branch_name.to_string(), branch);
        Ok(self.branches.get(branch_name).unwrap())
    }
    
    /// Make changes in a branch
    pub fn make_change(
        &mut self,
        branch_name: &str,
        change: BuildingChange,
    ) -> Result<(), String> {
        let branch = self.branches.get_mut(branch_name)
            .ok_or("Branch not found")?;
        
        // Apply change to branch's object state
        match &change {
            BuildingChange::Add { object, .. } => {
                branch.objects.insert(object.building_id, *object);
            }
            BuildingChange::Modify { object_id, new, .. } => {
                branch.objects.insert(*object_id, *new);
            }
            BuildingChange::Remove { object, .. } => {
                branch.objects.remove(&object.building_id);
            }
            BuildingChange::Annotate { .. } => {
                // Annotations don't change object state
            }
        }
        
        branch.changes.push(change);
        branch.updated_at = current_timestamp();
        
        Ok(())
    }
    
    /// Create merge request
    pub fn create_merge_request(
        &mut self,
        source_branch: &str,
        author: &str,
        title: String,
        description: String,
    ) -> Result<u32, String> {
        let branch = self.branches.get(source_branch)
            .ok_or("Branch not found")?;
        
        if branch.changes.is_empty() {
            return Err("No changes to merge".to_string());
        }
        
        let mr = MergeRequest {
            mr_id: self.merge_requests.len() as u32 + 1,
            source_branch: source_branch.to_string(),
            target_branch: "main".to_string(),
            author: author.to_string(),
            title,
            description,
            changes: branch.changes.clone(),
            status: MergeStatus::Open,
            reviewers: Vec::new(),
            approvals: Vec::new(),
            created_at: current_timestamp(),
            updated_at: current_timestamp(),
        };
        
        let mr_id = mr.mr_id;
        self.merge_requests.push(mr);
        
        Ok(mr_id)
    }
    
    /// Review and approve/reject merge request
    pub fn review_merge_request(
        &mut self,
        mr_id: u32,
        reviewer: &str,
        approved: bool,
        comment: String,
    ) -> Result<(), String> {
        let mr = self.merge_requests.iter_mut()
            .find(|m| m.mr_id == mr_id)
            .ok_or("Merge request not found")?;
        
        mr.approvals.push(Approval {
            reviewer: reviewer.to_string(),
            approved,
            comment,
            timestamp: current_timestamp(),
        });
        
        // Auto-approve if admin approved
        if approved && reviewer == "admin" {
            mr.status = MergeStatus::Approved;
        }
        
        mr.updated_at = current_timestamp();
        
        Ok(())
    }
    
    /// Merge approved changes to main
    pub fn merge_to_main(&mut self, mr_id: u32, merged_by: &str) -> Result<CommitHash, String> {
        let mr_index = self.merge_requests.iter()
            .position(|m| m.mr_id == mr_id)
            .ok_or("Merge request not found")?;
        
        let mr = &self.merge_requests[mr_index];
        
        if !matches!(mr.status, MergeStatus::Approved) {
            return Err("Merge request not approved".to_string());
        }
        
        // Apply changes to main branch
        for change in &mr.changes {
            match change {
                BuildingChange::Add { object, .. } => {
                    self.main_branch.objects.insert(object.building_id, *object);
                }
                BuildingChange::Modify { object_id, new, .. } => {
                    self.main_branch.objects.insert(*object_id, *new);
                }
                BuildingChange::Remove { object, .. } => {
                    self.main_branch.objects.remove(&object.building_id);
                }
                BuildingChange::Annotate { .. } => {
                    // Store annotations separately in production
                }
            }
        }
        
        // Update merge request status
        self.merge_requests[mr_index].status = MergeStatus::Merged;
        
        // Create commit hash
        let commit_hash = self.calculate_commit_hash(&self.main_branch);
        
        // Log the merge
        self.merge_history.push(MergeLog {
            commit_hash,
            mr_id,
            author: mr.author.clone(),
            merged_by: merged_by.to_string(),
            change_count: mr.changes.len(),
            timestamp: current_timestamp(),
            description: mr.title.clone(),
        });
        
        // Clean up branch
        self.branches.remove(&mr.source_branch);
        
        Ok(commit_hash)
    }
    
    /// Calculate commit hash from branch state
    fn calculate_commit_hash(&self, branch: &BuildingBranch) -> CommitHash {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        branch.name.hash(&mut hasher);
        branch.objects.len().hash(&mut hasher);
        branch.updated_at.hash(&mut hasher);
        
        let hash = hasher.finish();
        hash.to_le_bytes()
    }
    
    /// Get diff between branch and main
    pub fn diff(&self, branch_name: &str) -> Result<Vec<BuildingChange>, String> {
        let branch = self.branches.get(branch_name)
            .ok_or("Branch not found")?;
        
        Ok(branch.changes.clone())
    }
    
    /// Clean up expired branches
    pub fn cleanup_expired(&mut self) {
        let now = current_timestamp();
        
        self.branches.retain(|_, branch| {
            branch.expires_at.map_or(true, |exp| exp > now)
        });
    }
}

/// Practical example of contractor workflow
pub fn demo_contractor_branch_workflow() {
    println!("\n🌳 Building Repository Demo (Git-like)\n");
    
    println!("Setup: Building with main branch (truth)");
    println!("════════════════════════════════════════\n");
    
    println!("1️⃣ HVAC Tech arrives, gets branch:");
    println!("   $ arx -newuser 555-0100 @building --branch");
    println!("   ✅ Created branch: 'hvac-repair-2024-01-15'");
    println!("   ✅ SMS sent with access");
    println!();
    
    println!("2️⃣ Tech works in their branch:");
    println!("   • Views all equipment (read-only copy)");
    println!("   • Marks thermostat for replacement");
    println!("   • Adds note: 'Unit failing, needs new model'");
    println!("   • Adjusts HVAC schedule");
    println!();
    
    println!("3️⃣ Tech's changes (in branch only):");
    println!("   ┌─────────────────────────────────┐");
    println!("   │ BRANCH: hvac-repair-2024-01-15  │");
    println!("   │ Changes:                        │");
    println!("   │ • MODIFY thermostat-203         │");
    println!("   │ • ANNOTATE 'needs replacement'  │");
    println!("   │ • MODIFY schedule-hvac-2        │");
    println!("   └─────────────────────────────────┘");
    println!();
    
    println!("4️⃣ Tech creates merge request:");
    println!("   Title: 'Replace failed thermostat Room 203'");
    println!("   Description: 'Unit reading incorrectly, warranty expired'");
    println!("   Changes: 3 modifications");
    println!();
    
    println!("5️⃣ Facility manager reviews:");
    println!("   $ arx -review MR-42");
    println!("   Reviewing changes...");
    println!("   ✓ Thermostat replacement justified");
    println!("   ✓ Schedule changes reasonable");
    println!("   ✓ Within budget");
    println!();
    
    println!("6️⃣ Manager approves and merges:");
    println!("   $ arx -merge MR-42");
    println!("   ✅ Merged to main");
    println!("   ✅ Building truth updated");
    println!("   ✅ Work order generated");
    println!("   ✅ Branch deleted");
    println!();
    
    println!("Benefits:");
    println!("   • Contractors can't break production");
    println!("   • Full audit trail of changes");
    println!("   • Review before changes become truth");
    println!("   • Multiple contractors can work simultaneously");
    println!("   • Rollback capability if needed");
}

/// Show how this prevents issues
pub fn demo_branch_protection() {
    println!("\n🛡️ Branch Protection Demo\n");
    
    println!("Scenario: Malicious or mistaken changes");
    println!("════════════════════════════════════════\n");
    
    println!("❌ WITHOUT branches:");
    println!("   Contractor deletes critical equipment data");
    println!("   → Building system immediately affected");
    println!("   → Other systems fail due to missing data");
    println!("   → Recovery requires backup restoration");
    println!();
    
    println!("✅ WITH branches:");
    println!("   Contractor deletes equipment in their branch");
    println!("   → Main branch unaffected");
    println!("   → Merge request shows: 'DELETE electrical-panel-1'");
    println!("   → Manager rejects: 'Cannot delete critical infrastructure'");
    println!("   → Building remains safe");
    println!();
    
    println!("Real example:");
    println!("┌──────────────────────────────────────────┐");
    println!("│ MR-99: 'Electrical maintenance'          │");
    println!("│ Author: contractor-555-0100              │");
    println!("│                                          │");
    println!("│ Changes:                                 │");
    println!("│ ✓ MODIFY outlet-204 (fixed)             │");
    println!("│ ✓ ANNOTATE panel-2 (inspected)          │");
    println!("│ ⚠️ DELETE camera-5 (why?)               │");
    println!("│ ⚠️ MODIFY panel-1 (unauthorized)        │");
    println!("│                                          │");
    println!("│ Review: REJECTED                         │");
    println!("│ 'Cannot delete security equipment'       │");
    println!("└──────────────────────────────────────────┘");
}

fn current_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
}