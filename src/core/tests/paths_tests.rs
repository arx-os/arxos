#[cfg(feature = "std")]
#[test]
fn test_workspace_db_path_suffix() {
    use arxos_core::paths::workspace_db_path;
    let p = workspace_db_path(123);
    let s = p.to_string_lossy();
    assert!(s.ends_with("vbs_123.db"));
}


