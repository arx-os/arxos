//! CLI smoke tests for the field reliability loop:
//! init → capture/simulate → commit → status → entity list → score.
//!
//! Also checks root create fails closed without controller authorization.

use assert_cmd::cargo::cargo_bin;
use assert_cmd::Command;
use predicates::prelude::*;
use tempfile::tempdir;

fn arx() -> Command {
    Command::new(cargo_bin("arx"))
}

#[test]
fn field_loop_init_capture_commit_status_entity_score() {
    let dir = tempdir().unwrap();
    let store = dir.path().join("store");
    let store_s = store.to_str().unwrap();

    // init
    let out = arx()
        .args(["--store", store_s, "building", "init", "--name", "Smoke"])
        .assert()
        .success()
        .get_output()
        .stdout
        .clone();
    let stdout = String::from_utf8_lossy(&out);
    // Extract building id from output (line like building_id=...)
    let bid = stdout
        .lines()
        .find_map(|l| l.strip_prefix("building_id="))
        .expect("building_id in init output")
        .trim()
        .to_string();

    // simulate capture + commit
    arx()
        .args([
            "--store",
            store_s,
            "capture",
            "simulate",
            &bid,
            "--name",
            "Room",
            "--text",
            "smoke note",
            "--commit",
        ])
        .assert()
        .success();

    // status
    arx()
        .args(["--store", store_s, "building", "status", &bid])
        .assert()
        .success()
        .stdout(predicate::str::contains(&bid));

    // entity list (may be empty if simulate spaces have entity ids — spaces always get ids)
    arx()
        .args(["--store", store_s, "entity", "list", &bid])
        .assert()
        .success();

    // score (diagnostic)
    arx()
        .args(["--store", store_s, "score", &bid])
        .assert()
        .success()
        .stdout(predicate::str::contains("total").or(predicate::str::contains("score")).or(predicate::str::contains("objects")));
}

#[test]
fn root_create_rejects_unauthorized_seed() {
    let dir = tempdir().unwrap();
    let store = dir.path().join("store");
    let store_s = store.to_str().unwrap();

    let out = arx()
        .args(["--store", store_s, "building", "init", "--name", "Auth"])
        .assert()
        .success()
        .get_output()
        .stdout
        .clone();
    let stdout = String::from_utf8_lossy(&out);
    let bid = stdout
        .lines()
        .find_map(|l| l.strip_prefix("building_id="))
        .expect("building_id")
        .trim()
        .to_string();

    // Outsider seed (not a controller)
    let outsider = "aa".repeat(32);
    arx()
        .args([
            "--store",
            store_s,
            "root",
            "create",
            "--building-id",
            &bid,
            "--all",
            "--seed",
            &outsider,
        ])
        .assert()
        .failure()
        .stderr(
            predicate::str::contains("authorization")
                .or(predicate::str::contains("controller"))
                .or(predicate::str::contains("author")),
        );
}

#[test]
fn version_prints_core() {
    arx()
        .arg("version")
        .assert()
        .success()
        .stdout(predicate::str::contains("arx").and(predicate::str::contains("core")));
}
