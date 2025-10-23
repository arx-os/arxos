fn main() {
    uniffi_build::generate_scaffolding("src/arxos_mobile.udl").unwrap();
    
    // Set up proper linking for mobile platforms
    let target = std::env::var("TARGET").unwrap();
    
    if target.contains("ios") {
        println!("cargo:rustc-link-lib=framework=Foundation");
        println!("cargo:rustc-link-lib=framework=Security");
        println!("cargo:rustc-link-lib=framework=SystemConfiguration");
    } else if target.contains("android") {
        println!("cargo:rustc-link-lib=log");
        println!("cargo:rustc-link-lib=android");
    }
}