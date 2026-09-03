//! Wire path: concurrent controller tip via `arx net fetch --no-set-head`
//! then `arx merge apply` with the printed CID (unlabeled; no BuildingRecord field).

use std::io::{BufRead, BufReader};
use std::path::Path;
use std::process::{Child, Command, Stdio};
use std::sync::mpsc;
use std::thread;
use std::time::{Duration, Instant};

use assert_cmd::cargo::cargo_bin;
use assert_cmd::Command as AssertCommand;
use predicates::prelude::*;
use tempfile::tempdir;

fn arx() -> AssertCommand {
    AssertCommand::new(cargo_bin("arx"))
}

fn copy_dir(src: &Path, dst: &Path) {
    std::fs::create_dir_all(dst).unwrap();
    for ent in std::fs::read_dir(src).unwrap() {
        let ent = ent.unwrap();
        let to = dst.join(ent.file_name());
        if ent.file_type().unwrap().is_dir() {
            copy_dir(&ent.path(), &to);
        } else {
            let _ = std::fs::copy(ent.path(), &to);
        }
    }
}

fn field<'a>(stdout: &'a str, key: &str) -> &'a str {
    let prefix = format!("{key}=");
    stdout
        .lines()
        .find_map(|l| l.strip_prefix(&prefix))
        .unwrap_or_else(|| panic!("missing {prefix} in:\n{stdout}"))
        .trim()
}

fn spawn_serve(store: &str) -> (Child, String) {
    let mut child = Command::new(cargo_bin("arx"))
        .args(["--store", store, "net", "serve", "--no-mdns"])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("spawn arx net serve");
    let stdout = child.stdout.take().expect("serve stdout");
    let (tx, rx) = mpsc::channel::<String>();
    thread::spawn(move || {
        for line in BufReader::new(stdout).lines() {
            match line {
                Ok(l) => {
                    if tx.send(l).is_err() {
                        break;
                    }
                }
                Err(_) => break,
            }
        }
    });
    let mut ticket = None;
    let deadline = Instant::now() + Duration::from_secs(30);
    loop {
        match rx.recv_timeout(Duration::from_millis(200)) {
            Ok(line) => {
                if let Some(t) = line.strip_prefix("ticket=") {
                    ticket = Some(t.to_string());
                }
                if line.contains("serving") && ticket.is_some() {
                    break;
                }
            }
            Err(mpsc::RecvTimeoutError::Timeout) if Instant::now() < deadline => {}
            Err(_) => panic!("timeout or hang waiting for arx net serve ticket; ticket={ticket:?}"),
        }
    }
    (child, ticket.expect("ticket="))
}

#[test]
fn net_fetch_help_includes_no_set_head() {
    arx()
        .args(["net", "fetch", "--help"])
        .assert()
        .success()
        .stdout(predicate::str::contains("--no-set-head"));
}

#[test]
fn net_fetch_no_set_head_then_merge_apply_concurrent_controller_tip() {
    let tmp = tempdir().unwrap();
    let store_a = tmp.path().join("a");
    let store_b = tmp.path().join("b");
    let a = store_a.to_str().unwrap();
    let b = store_b.to_str().unwrap();

    let init = String::from_utf8(
        arx()
            .args(["--store", a, "building", "init", "--name", "Concurrent"])
            .assert()
            .success()
            .get_output()
            .stdout
            .clone(),
    )
    .unwrap();
    let bid = field(&init, "building_id").to_string();
    let base = field(&init, "head_root").to_string();
    assert_ne!(base, "none");

    copy_dir(&store_a, &store_b);

    arx()
        .args([
            "--store",
            a,
            "capture",
            "annotation",
            &bid,
            "--text",
            "left",
            "--x",
            "0",
            "--y",
            "0",
            "--z",
            "0",
        ])
        .assert()
        .success();
    let commit_a = String::from_utf8(
        arx()
            .args([
                "--store",
                a,
                "building",
                "commit",
                &bid,
                "--message",
                "left",
            ])
            .assert()
            .success()
            .get_output()
            .stdout
            .clone(),
    )
    .unwrap();
    let tip_a = field(&commit_a, "root_cid").to_string();

    arx()
        .args([
            "--store",
            b,
            "capture",
            "annotation",
            &bid,
            "--text",
            "right",
            "--x",
            "5",
            "--y",
            "0",
            "--z",
            "0",
        ])
        .assert()
        .success();
    let commit_b = String::from_utf8(
        arx()
            .args([
                "--store",
                b,
                "building",
                "commit",
                &bid,
                "--message",
                "right",
            ])
            .assert()
            .success()
            .get_output()
            .stdout
            .clone(),
    )
    .unwrap();
    let tip_b = field(&commit_b, "root_cid").to_string();
    assert_ne!(tip_a, tip_b);

    let list_before = String::from_utf8(
        arx()
            .args(["--store", b, "object", "list"])
            .assert()
            .success()
            .get_output()
            .stdout
            .clone(),
    )
    .unwrap();
    assert!(
        !list_before.lines().any(|l| l.starts_with(&tip_a)),
        "B must not already hold A's concurrent tip"
    );

    let (mut serve, ticket) = spawn_serve(a);
    let fetch_result = std::panic::catch_unwind(|| {
        let fetch = String::from_utf8(
            arx()
                .args([
                    "--store",
                    b,
                    "net",
                    "fetch",
                    "--peer",
                    &ticket,
                    "--root",
                    &tip_a,
                    "--building-id",
                    &bid,
                    "--no-set-head",
                ])
                .assert()
                .success()
                .get_output()
                .stdout
                .clone(),
        )
        .unwrap();
        assert!(
            fetch.contains(&format!("root_cid={tip_a}")),
            "no-adopt fetch must print root_cid=; got:\n{fetch}"
        );
        assert!(
            fetch.contains("objects_stored="),
            "no-adopt fetch must print objects_stored=; got:\n{fetch}"
        );
        assert!(
            fetch.contains("objects_skipped="),
            "no-adopt fetch must print objects_skipped=; got:\n{fetch}"
        );
        let stored: u64 = field(&fetch, "objects_stored").parse().unwrap();
        assert!(stored >= 1, "CAS should grow; stored={stored}");
        assert!(
            !fetch.contains("adopted_head="),
            "ingest-without-adopt must not print adopted_head=; got:\n{fetch}"
        );

        let status = String::from_utf8(
            arx()
                .args(["--store", b, "building", "status", &bid])
                .assert()
                .success()
                .get_output()
                .stdout
                .clone(),
        )
        .unwrap();
        assert_eq!(
            field(&status, "head_root"),
            tip_b,
            "head_root must stay B's tip after --no-set-head"
        );

        let list_after = String::from_utf8(
            arx()
                .args(["--store", b, "object", "list"])
                .assert()
                .success()
                .get_output()
                .stdout
                .clone(),
        )
        .unwrap();
        assert!(
            list_after.lines().any(|l| l.starts_with(&tip_a)),
            "fetched root CID must be in B's CAS"
        );

        arx()
            .args(["--store", b, "merge", "apply", &bid, &tip_a])
            .assert()
            .success()
            .stdout(predicate::str::contains("root_cid="));

        let status2 = String::from_utf8(
            arx()
                .args(["--store", b, "building", "status", &bid])
                .assert()
                .success()
                .get_output()
                .stdout
                .clone(),
        )
        .unwrap();
        let merged = field(&status2, "head_root");
        assert_ne!(merged, tip_b, "merge apply must move head");
        assert_ne!(
            merged, tip_a,
            "merge apply must not adopt the other tip as-is"
        );
    });
    let _ = serve.kill();
    let _ = serve.wait();
    fetch_result.unwrap();
}
