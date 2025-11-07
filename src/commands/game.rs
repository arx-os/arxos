//! Game command handlers for gamified PR review and planning

use crate::game::export::export_game_to_ifc;
use crate::game::planning::PlanningGame;
use crate::game::pr_game::PRReviewGame;
use crate::render3d::interactive::InteractiveRenderer;
use crate::render3d::{ProjectionType, Render3DConfig, ViewAngle};
use crate::utils::loading::load_building_data;
use log::info;
use std::path::Path;

/// Game command configuration
#[derive(Debug, Clone)]
pub struct GameCommandConfig {
    pub mode: GameMode,
    pub building: Option<String>,
    pub pr_id: Option<String>,
    pub pr_dir: Option<String>,
    pub output: Option<String>,
    pub interactive: bool,
}

/// Game mode for commands
#[derive(Debug, Clone)]
pub enum GameMode {
    Review,
    Plan,
    Learn,
}

/// Handle game review command
pub fn handle_game_review(
    pr_id: String,
    pr_dir: Option<String>,
    building: String,
    interactive: bool,
    export_ifc: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    info!("Starting PR review game mode for PR: {}", pr_id);

    // Determine PR directory
    let pr_dir_path = if let Some(dir) = pr_dir {
        Path::new(&dir).to_path_buf()
    } else {
        Path::new("prs").join(format!("pr_{}", pr_id))
    };

    if !pr_dir_path.exists() {
        return Err(format!("PR directory not found: {:?}", pr_dir_path).into());
    }

    // Create PR review game
    let mut review_game = PRReviewGame::new(&pr_id, &pr_dir_path)?;

    // Validate PR
    let _validation_results = review_game.validate_pr();
    let summary = review_game.get_validation_summary();

    // Display summary
    println!("╔════════════════════════════════════════════════════════════╗");
    println!("║                 PR Review Summary                          ║");
    println!("╠════════════════════════════════════════════════════════════╣");
    println!("║ Total Items:        {:<42} ║", summary.total_items);
    println!("║ Valid Items:        {:<42} ║", summary.valid_items);
    println!(
        "║ Items with Issues:  {:<42} ║",
        summary.items_with_violations
    );
    println!("║ Total Violations:   {:<42} ║", summary.total_violations);
    println!(
        "║ Critical Issues:    {:<42} ║",
        summary.critical_violations
    );
    println!("╚════════════════════════════════════════════════════════════╝");

    // Export to IFC if requested
    if let Some(ifc_path) = export_ifc {
        let game_state = review_game.game_state();
        export_game_to_ifc(game_state, Path::new(&ifc_path))?;
        println!("✅ Exported review results to IFC: {}", ifc_path);
    }

    // Interactive mode
    if interactive {
        println!("\n🎮 Starting interactive review mode...");
        println!("Navigate with WASD/Arrow keys, Press 'h' for help");
        println!("Press 'a' to approve, 'r' to reject, 'c' to request changes");

        // Load building data for rendering
        let building_data = load_building_data(&building)?;
        let render_config = Render3DConfig {
            show_status: true,
            show_rooms: true,
            show_equipment: true,
            show_connections: false,
            projection_type: ProjectionType::Isometric,
            view_angle: ViewAngle::Isometric,
            scale_factor: 1.0,
            max_width: 120,
            max_height: 40,
        };

        let mut renderer = InteractiveRenderer::with_config(
            building_data,
            render_config,
            crate::render3d::interactive::InteractiveConfig::default(),
        )?;

        // Start game mode in renderer
        renderer.start_game_mode(review_game.game_state().clone());

        // Start interactive session
        renderer.start_interactive_session()?;
    }

    Ok(())
}

/// Handle game plan command
pub fn handle_game_plan(
    building: String,
    interactive: bool,
    export_pr: Option<String>,
    export_ifc: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    info!("Starting planning game mode for building: {}", building);

    // Create planning game
    let planning_game = PlanningGame::new(&building)?;

    println!("╔════════════════════════════════════════════════════════════╗");
    println!("║            Planning Game Mode Activated                     ║");
    println!("╠════════════════════════════════════════════════════════════╣");
    println!("║ Building: {:<51} ║", building);
    println!("║ Session ID: {:<47} ║", planning_game.session_id());
    println!("╚════════════════════════════════════════════════════════════╝");

    // Interactive mode
    if interactive {
        println!("\n🎮 Starting interactive planning mode...");
        println!("Navigate with WASD/Arrow keys, Press 'h' for help");
        println!("Press 'p' to place equipment, 'm' to move, 'd' to delete");

        // Load building data for rendering
        let building_data = load_building_data(&building)?;
        let render_config = Render3DConfig {
            show_status: true,
            show_rooms: true,
            show_equipment: true,
            show_connections: false,
            projection_type: ProjectionType::Isometric,
            view_angle: ViewAngle::Isometric,
            scale_factor: 1.0,
            max_width: 120,
            max_height: 40,
        };

        let mut renderer = InteractiveRenderer::with_config(
            building_data,
            render_config,
            crate::render3d::interactive::InteractiveConfig::default(),
        )?;

        // Start game mode in renderer
        renderer.start_game_mode(planning_game.game_state().clone());

        // Start interactive session
        renderer.start_interactive_session()?;

        // After interactive session, update planning game state
        if let Some(game_state) = renderer.game_state() {
            // Game state updates are handled in real-time during session
            println!("\n📊 Final Planning Summary:");
            let summary = game_state.get_stats();
            println!("  Placements: {}", summary.total_placements);
            println!("  Valid: {}", summary.valid_placements);
            println!("  Score: {}", summary.score);
        }
    }

    // Export to PR if requested
    if let Some(pr_dir) = export_pr {
        let pr_path = Path::new(&pr_dir);
        planning_game.export_to_pr(
            pr_path,
            Some("Planning Session".to_string()),
            Some(format!("Planning session for {}", building)),
        )?;
        println!("✅ Exported planning session to PR: {}", pr_dir);
    }

    // Export to IFC if requested
    if let Some(ifc_path) = export_ifc {
        let game_state = planning_game.game_state();
        export_game_to_ifc(game_state, Path::new(&ifc_path))?;
        println!("✅ Exported planning to IFC: {}", ifc_path);
    }

    Ok(())
}

/// Handle game learn command
pub fn handle_game_learn(
    pr_id: String,
    pr_dir: Option<String>,
    building: String,
) -> Result<(), Box<dyn std::error::Error>> {
    info!("Starting learning mode from PR: {}", pr_id);

    // Determine PR directory
    let pr_dir_path = if let Some(dir) = pr_dir {
        Path::new(&dir).to_path_buf()
    } else {
        Path::new("prs").join(format!("pr_{}", pr_id))
    };

    if !pr_dir_path.exists() {
        return Err(format!("PR directory not found: {:?}", pr_dir_path).into());
    }

    // Create learning mode
    use crate::game::learning::LearningMode;
    let learning_mode = LearningMode::from_pr(&pr_id, &pr_dir_path)?;

    // Display learning information
    let commentary = learning_mode.get_all_commentary();
    let tutorials = learning_mode.get_tutorials();

    println!("\n📚 Expert Commentary Available: {}", commentary.len());
    for (idx, comment) in commentary.iter().take(3).enumerate() {
        println!(
            "   {}. {} - {}",
            idx + 1,
            comment.title,
            comment.content.chars().take(60).collect::<String>()
        );
    }

    println!("\n📖 Tutorial Steps: {}", tutorials.len());
    for tutorial in tutorials {
        println!("   {}: {}", tutorial.step_number, tutorial.title);
    }

    let scenario = learning_mode.scenario();
    println!("╔════════════════════════════════════════════════════════════╗");
    println!("║              Learning Mode - Scenario Loaded                ║");
    println!("╠════════════════════════════════════════════════════════════╣");
    println!("║ PR ID: {:<52} ║", pr_id);
    println!("║ Objective: {:<49} ║", scenario.objective);
    println!(
        "║ Equipment Items: {:<43} ║",
        scenario.equipment_items.len()
    );
    println!("╚════════════════════════════════════════════════════════════╝");

    println!("\n📚 This is a learning scenario. Study the equipment placements");
    println!("   and constraints to understand best practices.");

    // Load building data for rendering
    let building_data = load_building_data(&building)?;
    let render_config = Render3DConfig {
        show_status: true,
        show_rooms: true,
        show_equipment: true,
        show_connections: false,
        projection_type: ProjectionType::Isometric,
        view_angle: ViewAngle::Isometric,
        scale_factor: 1.0,
        max_width: 120,
        max_height: 40,
    };

    let mut renderer = InteractiveRenderer::with_config(
        building_data,
        render_config,
        crate::render3d::interactive::InteractiveConfig::default(),
    )?;

    // Use learning mode game state
    let game_state = learning_mode.game_state().clone();
    renderer.start_game_mode(game_state);
    renderer.start_interactive_session()?;

    Ok(())
}
