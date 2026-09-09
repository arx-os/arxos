//! ASCII slice of a 4×4 m hall is a hollow rectangle of `#`.

use assert_cmd::cargo::cargo_bin;
use assert_cmd::Command;
use tempfile::tempdir;

fn arx() -> Command {
    Command::new(cargo_bin("arx"))
}

#[test]
fn building_slice_hall_is_hollow_rectangle() {
    let dir = tempdir().unwrap();
    let store = dir.path().join("store");
    let store_s = store.to_str().unwrap();

    let out = arx()
        .args(["--store", store_s, "building", "init", "--name", "Hall", "--quiet"])
        .assert()
        .success()
        .get_output()
        .stdout
        .clone();
    let bid = String::from_utf8_lossy(&out).trim().to_string();

    arx()
        .args([
            "--store", store_s, "capture", "simulate", &bid, "--commit",
        ])
        .assert()
        .success();

    let slice = arx()
        .args([
            "--store",
            store_s,
            "building",
            "slice",
            &bid,
            "--z",
            "1.2",
            "--cell",
            "0.25",
        ])
        .assert()
        .success()
        .get_output()
        .stdout
        .clone();
    let text = String::from_utf8_lossy(&slice);
    let norm: String = text
        .lines()
        .map(|l| l.trim_end())
        .filter(|l| !l.is_empty())
        .collect::<Vec<_>>()
        .join("\n");
    assert!(norm.contains('#'), "expected wall glyphs:\n{norm}");
    let rows: Vec<&str> = norm.lines().collect();
    assert!(rows.len() >= 4, "too few rows:\n{norm}");
    let mid = rows[rows.len() / 2];
    assert!(mid.contains('.'), "expected hollow interior:\n{norm}");
    assert!(mid.contains('#'), "expected walls on mid row:\n{norm}");
}
