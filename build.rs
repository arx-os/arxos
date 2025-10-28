// Build script for ArxOS
fn main() {
    // Tell Cargo to link against libc
    println!("cargo:rustc-link-lib=c");
    
    // Rebuild if Cargo.toml changes
    println!("cargo:rerun-if-changed=Cargo.toml");
    
    // Rebuild if source files change
    println!("cargo:rerun-if-changed=src");
}

