// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Arxos",
    platforms: [
        .iOS(.v16),
        .macOS(.v13),
    ],
    products: [
        .library(name: "ArxosCore", targets: ["ArxosCore"]),
        .executable(name: "ArxosDemo", targets: ["ArxosDemo"]),
    ],
    targets: [
        // UniFFI-generated (or Phase 0 shim) Swift API over arxos-core.
        .target(
            name: "ArxosCore",
            path: "Sources/ArxosCore"
        ),
        .executableTarget(
            name: "ArxosDemo",
            dependencies: ["ArxosCore"],
            path: "Sources/ArxosDemo"
        ),
        // SwiftUI app sources live under Sources/ArxosApp for Xcode (Phase 1).
        // Not a SPM product here — @main apps need an Xcode target / iOS SDK.
    ]
)
