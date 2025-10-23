fn main() {
    // Handle Windows-specific linking for Git2
    #[cfg(target_os = "windows")]
    {
        println!("cargo:rustc-link-lib=advapi32");
        println!("cargo:rustc-link-lib=crypt32");
        println!("cargo:rustc-link-lib=user32");
        println!("cargo:rustc-link-lib=ole32");
        println!("cargo:rustc-link-lib=rpcrt4");
        println!("cargo:rustc-link-lib=winhttp");
        println!("cargo:rustc-link-lib=secur32");
        println!("cargo:rustc-link-lib=bcrypt");
        println!("cargo:rustc-link-lib=ntdll");
        println!("cargo:rustc-link-lib=userenv");
        println!("cargo:rustc-link-lib=ws2_32");
        println!("cargo:rustc-link-lib=dbghelp");
    }
}
