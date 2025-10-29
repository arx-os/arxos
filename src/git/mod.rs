// Git operations for ArxOS
use git2::Repository;
use std::path::Path;

pub mod manager;
pub use manager::*;

pub struct GitClient {
    repository: Repository,
}

impl GitClient {
    pub fn new(repo_path: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let repository = Repository::open(repo_path)?;
        Ok(Self { repository })
    }
    
    pub fn write_file(&self, path: &str, content: &str) -> Result<(), Box<dyn std::error::Error>> {
        let file_path = Path::new(&self.repository.path()).join(path);
        std::fs::write(file_path, content)?;
        Ok(())
    }
    
    pub fn commit(&self, message: &str) -> Result<(), Box<dyn std::error::Error>> {
        let mut index = self.repository.index()?;
        index.add_all(["*"], git2::IndexAddOption::DEFAULT, None)?;
        index.write()?;
        
        let tree_id = index.write_tree()?;
        let tree = self.repository.find_tree(tree_id)?;
        
        let signature = git2::Signature::now("ArxOS", "arxos@example.com")?;
        
        // Handle initial commit (no HEAD) or detached HEAD gracefully
        let parents: Vec<git2::Commit> = match self.repository.head() {
            Ok(head) => {
                if let Some(target) = head.target() {
                    match self.repository.find_commit(target) {
                        Ok(parent) => vec![parent],
                        Err(_) => vec![], // Invalid commit reference, treat as initial commit
                    }
                } else {
                    vec![] // No target, treat as initial commit
                }
            }
            Err(_) => vec![], // No HEAD, initial commit
        };
        
        let parent_refs: Vec<&git2::Commit> = parents.iter().collect();
        
        self.repository.commit(
            Some("HEAD"),
            &signature,
            &signature,
            message,
            &tree,
            &parent_refs,
        )?;
        
        Ok(())
    }
}
