// Build script for ArxOS
fn main() {
    // Only link against libc on Unix systems (Linux, macOS)
    // On Windows MSVC, the C runtime is automatically linked
    let target = std::env::var("TARGET").unwrap();
    if !target.contains("windows") && !target.contains("msvc") {
        println!("cargo:rustc-link-lib=c");
    }
    
    // Rebuild if Cargo.toml changes
    println!("cargo:rerun-if-changed=Cargo.toml");
    
    // Rebuild if source files change
    println!("cargo:rerun-if-changed=src");
}

