// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ArxOSMobile",
    platforms: [
        .iOS(.v17)
    ],
    products: [
        .library(
            name: "ArxOSMobile",
            targets: ["ArxOSMobile"]
        ),
    ],
    dependencies: [
        // Add dependencies for Rust FFI integration
        .package(path: "../crates/arxos-mobile")
    ],
    targets: [
        .target(
            name: "ArxOSMobile",
            dependencies: [
                // Link to Rust FFI library
                "ArxOSMobileFFI"
            ],
            path: "ArxOSMobile"
        ),
        .binaryTarget(
            name: "ArxOSMobileFFI",
            path: "../crates/arxos-mobile/target/universal/release/libarxos_mobile.a"
        )
    ]
)
