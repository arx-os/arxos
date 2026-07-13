//! CLI help surface honesty (compiler-first ordering).
//!
//! Guards pilot UX: spine commands present; dead spatial theater absent;
//! lab commands still available but not required for L1.

use clap::CommandFactory;

#[test]
fn help_lists_compiler_spine_commands() {
    let mut cmd = arxos::cli::Cli::command();
    let help = cmd.render_long_help().to_string();

    for name in [
        "init",
        "import",
        "edit",
        "validate",
        "export",
        "query",
        "migrate",
        "status",
        "stage",
        "commit",
    ] {
        assert!(
            help.contains(name),
            "expected spine command `{name}` in help:\n{help}"
        );
    }
}

#[test]
fn help_orders_spine_before_lab_economy() {
    let mut cmd = arxos::cli::Cli::command();
    let help = cmd.render_long_help().to_string();

    let export_pos = help
        .find("export")
        .expect("export in help");
    let contribute_pos = help
        .find("contribute")
        .expect("contribute in help");
    let access_pos = help.find("access").expect("access in help");

    assert!(
        export_pos < contribute_pos,
        "export (spine) should appear before contribute (lab) in help"
    );
    assert!(
        export_pos < access_pos,
        "export (spine) should appear before access (lab) in help"
    );
}

#[test]
fn help_does_not_advertise_dead_spatial_theater() {
    let mut cmd = arxos::cli::Cli::command();
    // Build spatial help if present
    let spatial = cmd.find_subcommand_mut("spatial");
    assert!(spatial.is_some(), "spatial command should still exist");
    let spatial_help = spatial.unwrap().render_long_help().to_string();

    for dead in ["grid-to-real", "real-to-grid", "relate"] {
        assert!(
            !spatial_help.contains(dead),
            "dead spatial verb `{dead}` must not appear in help:\n{spatial_help}"
        );
    }
    for keep in ["query", "transform", "validate"] {
        assert!(
            spatial_help.contains(keep),
            "implemented spatial verb `{keep}` should appear in help"
        );
    }
}

#[test]
fn about_mentions_tui_default_and_pilot_loop() {
    let mut cmd = arxos::cli::Cli::command();
    let help = cmd.render_long_help().to_string();
    assert!(
        help.contains("TUI") || help.contains("tui") || help.contains("Primary UI"),
        "help should acknowledge TUI as primary UI"
    );
    assert!(
        help.contains("export") && help.contains("ifc"),
        "help should point at IFC export path"
    );
}

#[test]
fn remote_absent_without_agent_feature() {
    let cmd = arxos::cli::Cli::command();
    #[cfg(not(feature = "agent"))]
    {
        assert!(
            cmd.find_subcommand("remote").is_none(),
            "remote must not appear without agent feature"
        );
    }
    #[cfg(feature = "agent")]
    {
        assert!(
            cmd.find_subcommand("remote").is_some(),
            "remote should appear with agent feature"
        );
    }
}
