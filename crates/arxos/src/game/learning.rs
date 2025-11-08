//! Learning Mode
//!
//! Educational mode for learning from historical PRs with expert commentary,
//! tutorials, and best practice examples.

use crate::game::scenario::GameScenarioLoader;
use crate::game::state::GameState;
use crate::game::types::{GameMode, GameScenario};
use log::info;
use std::path::Path;

/// Learning mode with educational features
pub struct LearningMode {
    scenario: GameScenario,
    game_state: GameState,
    expert_commentary: Vec<ExpertCommentary>,
    tutorials: Vec<TutorialStep>,
}

/// Expert commentary on equipment placements
#[derive(Debug, Clone)]
pub struct ExpertCommentary {
    pub equipment_id: Option<String>,
    pub title: String,
    pub content: String,
    pub category: CommentaryCategory,
    pub timestamp: Option<String>, // When this commentary was added
}

/// Category of expert commentary
#[derive(Debug, Clone, PartialEq)]
pub enum CommentaryCategory {
    BestPractice,
    CommonMistake,
    CodeCompliance,
    StructuralConsideration,
    SpatialPlanning,
    CostOptimization,
    GeneralTip,
}

/// Tutorial step for learning mode
#[derive(Debug, Clone)]
pub struct TutorialStep {
    pub step_number: usize,
    pub title: String,
    pub description: String,
    pub instructions: Vec<String>,
    pub is_completed: bool,
}

impl LearningMode {
    /// Create learning mode from a PR
    pub fn from_pr(pr_id: &str, pr_dir: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        info!("Creating learning mode from PR: {}", pr_id);

        // Load scenario
        let scenario = GameScenarioLoader::create_learning_scenario(pr_id, pr_dir)?;

        // Initialize game state
        let mut game_state = GameState::new(GameMode::Learning);
        game_state.load_scenario(scenario.clone());

        // Load equipment items into game state
        for placement in &scenario.equipment_items {
            game_state.add_placement(placement.clone());
        }

        // Load expert commentary if available
        let commentary_path = pr_dir.join("expert_commentary.yaml");
        let expert_commentary = if commentary_path.exists() {
            Self::load_commentary(&commentary_path)?
        } else {
            // Generate default commentary based on scenario
            Self::generate_default_commentary(&scenario)
        };

        // Load tutorials if available
        let tutorials_path = pr_dir.join("tutorial.yaml");
        let tutorials = if tutorials_path.exists() {
            Self::load_tutorials(&tutorials_path)?
        } else {
            // Generate default tutorial
            Self::generate_default_tutorial(&scenario)
        };

        Ok(Self {
            scenario,
            game_state,
            expert_commentary,
            tutorials,
        })
    }

    /// Load expert commentary from YAML
    fn load_commentary(
        commentary_path: &Path,
    ) -> Result<Vec<ExpertCommentary>, Box<dyn std::error::Error>> {
        let content = std::fs::read_to_string(commentary_path)?;
        let data: serde_yaml::Value = serde_yaml::from_str(&content)?;

        let mut commentary = Vec::new();

        if let Some(comments) = data.get("commentary").and_then(|c| c.as_sequence()) {
            for comment_data in comments {
                let category_str = comment_data
                    .get("category")
                    .and_then(|c| c.as_str())
                    .unwrap_or("GeneralTip");

                let category = match category_str {
                    "BestPractice" => CommentaryCategory::BestPractice,
                    "CommonMistake" => CommentaryCategory::CommonMistake,
                    "CodeCompliance" => CommentaryCategory::CodeCompliance,
                    "StructuralConsideration" => CommentaryCategory::StructuralConsideration,
                    "SpatialPlanning" => CommentaryCategory::SpatialPlanning,
                    "CostOptimization" => CommentaryCategory::CostOptimization,
                    _ => CommentaryCategory::GeneralTip,
                };

                commentary.push(ExpertCommentary {
                    equipment_id: comment_data
                        .get("equipment_id")
                        .and_then(|e| e.as_str())
                        .map(|s| s.to_string()),
                    title: comment_data
                        .get("title")
                        .and_then(|t| t.as_str())
                        .unwrap_or("Expert Tip")
                        .to_string(),
                    content: comment_data
                        .get("content")
                        .and_then(|c| c.as_str())
                        .unwrap_or("")
                        .to_string(),
                    category,
                    timestamp: comment_data
                        .get("timestamp")
                        .and_then(|t| t.as_str())
                        .map(|s| s.to_string()),
                });
            }
        }

        Ok(commentary)
    }

    /// Generate default commentary based on scenario
    fn generate_default_commentary(_scenario: &GameScenario) -> Vec<ExpertCommentary> {
        let mut commentary = Vec::new();

        // Add general tips
        commentary.push(ExpertCommentary {
            equipment_id: None,
            title: "Learning from Historical PRs".to_string(),
            content: "This scenario shows a real-world equipment placement that was successfully reviewed and approved. Study the placements to understand best practices.".to_string(),
            category: CommentaryCategory::BestPractice,
            timestamp: None,
        });

        // Add commentary for each equipment item
        for placement in _scenario.equipment_items.iter() {
            if placement.constraint_validation.is_valid {
                commentary.push(ExpertCommentary {
                    equipment_id: Some(placement.equipment.id.clone()),
                    title: format!("Placement Best Practice: {}", placement.equipment.name),
                    content: format!(
                        "This {:?} equipment was placed successfully with all constraints satisfied. Notice the positioning relative to structural support and clearance requirements.",
                        placement.equipment.equipment_type
                    ),
                    category: CommentaryCategory::BestPractice,
                    timestamp: None,
                });
            } else {
                commentary.push(ExpertCommentary {
                    equipment_id: Some(placement.equipment.id.clone()),
                    title: format!("Learn from Violations: {}", placement.equipment.name),
                    content: format!("This placement had {} violation(s). Review the violations to understand common mistakes and how to avoid them.", 
                        placement.constraint_validation.violations.len()),
                    category: CommentaryCategory::CommonMistake,
                    timestamp: None,
                });
            }
        }

        commentary
    }

    /// Load tutorials from YAML
    fn load_tutorials(
        tutorial_path: &Path,
    ) -> Result<Vec<TutorialStep>, Box<dyn std::error::Error>> {
        let content = std::fs::read_to_string(tutorial_path)?;
        let data: serde_yaml::Value = serde_yaml::from_str(&content)?;

        let mut tutorials = Vec::new();

        if let Some(steps) = data.get("tutorial_steps").and_then(|s| s.as_sequence()) {
            for (idx, step_data) in steps.iter().enumerate() {
                let instructions: Vec<String> = step_data
                    .get("instructions")
                    .and_then(|i| i.as_sequence())
                    .map(|seq| {
                        seq.iter()
                            .filter_map(|v| v.as_str())
                            .map(|s| s.to_string())
                            .collect()
                    })
                    .unwrap_or_default();

                tutorials.push(TutorialStep {
                    step_number: idx + 1,
                    title: step_data
                        .get("title")
                        .and_then(|t| t.as_str())
                        .unwrap_or(&format!("Step {}", idx + 1))
                        .to_string(),
                    description: step_data
                        .get("description")
                        .and_then(|d| d.as_str())
                        .unwrap_or("")
                        .to_string(),
                    instructions,
                    is_completed: false,
                });
            }
        }

        Ok(tutorials)
    }

    /// Generate default tutorial based on scenario
    fn generate_default_tutorial(_scenario: &GameScenario) -> Vec<TutorialStep> {
        vec![
            TutorialStep {
                step_number: 1,
                title: "Review Equipment Placements".to_string(),
                description: "Study each equipment placement in this scenario".to_string(),
                instructions: vec![
                    "Navigate through the building using WASD keys".to_string(),
                    "Examine each equipment placement".to_string(),
                    "Note the validation results".to_string(),
                ],
                is_completed: false,
            },
            TutorialStep {
                step_number: 2,
                title: "Understand Constraints".to_string(),
                description: "Learn about constraint validation".to_string(),
                instructions: vec![
                    "Review constraint violations if any".to_string(),
                    "Understand why placements are valid or invalid".to_string(),
                    "Study the constraint types (spatial, structural, code)".to_string(),
                ],
                is_completed: false,
            },
            TutorialStep {
                step_number: 3,
                title: "Apply Best Practices".to_string(),
                description: "Take lessons learned to your own work".to_string(),
                instructions: vec![
                    "Identify patterns in successful placements".to_string(),
                    "Note common mistakes to avoid".to_string(),
                    "Consider how to apply these principles".to_string(),
                ],
                is_completed: false,
            },
        ]
    }

    /// Get expert commentary for equipment
    pub fn get_commentary_for_equipment(&self, equipment_id: &str) -> Vec<&ExpertCommentary> {
        self.expert_commentary
            .iter()
            .filter(|c| {
                c.equipment_id
                    .as_ref()
                    .map(|id| id == equipment_id)
                    .unwrap_or(false)
            })
            .collect()
    }

    /// Get all commentary
    pub fn get_all_commentary(&self) -> &[ExpertCommentary] {
        &self.expert_commentary
    }

    /// Get commentary by category
    pub fn get_commentary_by_category(
        &self,
        category: CommentaryCategory,
    ) -> Vec<&ExpertCommentary> {
        self.expert_commentary
            .iter()
            .filter(|c| c.category == category)
            .collect()
    }

    /// Get tutorials
    pub fn get_tutorials(&self) -> &[TutorialStep] {
        &self.tutorials
    }

    /// Mark tutorial step as completed
    pub fn complete_tutorial_step(&mut self, step_number: usize) -> Result<(), String> {
        if step_number == 0 || step_number > self.tutorials.len() {
            return Err(format!("Invalid tutorial step number: {}", step_number));
        }
        self.tutorials[step_number - 1].is_completed = true;
        Ok(())
    }

    /// Get game state
    pub fn game_state(&self) -> &GameState {
        &self.game_state
    }

    /// Get scenario
    pub fn scenario(&self) -> &GameScenario {
        &self.scenario
    }
}
