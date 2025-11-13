//! Minimal build script for ArxOS.
//!
//! The legacy mobile FFI header generation pipeline has been removed. We only
//! expose the crate version to the compiler and watch for manifest changes.

fn main() {
    println!(
        "cargo:rustc-env=ARXOS_VERSION={}",
        env!("CARGO_PKG_VERSION")
    );
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=../Cargo.toml");
}
