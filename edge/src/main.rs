//! Arxos edge node — Phase 0 stub.
//!
//! Full edge packaging (Raspberry Pi class) lands in Phase 5.

fn main() {
    println!(
        "arxos-edge {} — stub (core {})",
        env!("CARGO_PKG_VERSION"),
        arxos_core::version()
    );
    println!("{}", arxos_core::hello("edge".into()));
}
