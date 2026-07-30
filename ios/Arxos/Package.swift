// swift-tools-version: 5.9
import PackageDescription
import Foundation

let packageRoot = URL(fileURLWithPath: #filePath).deletingLastPathComponent().path
// Prefer release, fall back to debug for local `cargo build -p arxos-ffi`.
let rustLibCandidates = [
    packageRoot + "/../../target/release",
    packageRoot + "/../../target/debug",
]
let rustLibDir = rustLibCandidates.first { FileManager.default.fileExists(atPath: $0 + "/libarxos_core.a") }
    ?? (packageRoot + "/../../target/debug")

let package = Package(
    name: "Arxos",
    platforms: [
        .iOS(.v16),
        .macOS(.v13),
    ],
    products: [
        .library(name: "ArxosCore", targets: ["ArxosCore"]),
        .library(name: "ArxosAppLib", targets: ["ArxosApp"]),
        .executable(name: "ArxosDemo", targets: ["ArxosDemo"]),
    ],
    targets: [
        .systemLibrary(
            name: "arxos_coreFFI",
            path: "Sources/CArxosCoreFFI"
        ),
        .target(
            name: "ArxosCore",
            dependencies: ["arxos_coreFFI"],
            path: "Sources/ArxosCore",
            exclude: [
                "Generated/arxos_coreFFI.h",
            ],
            linkerSettings: [
                .linkedLibrary("arxos_core"),
                .unsafeFlags([
                    "-L\(rustLibDir)",
                    "-framework", "SystemConfiguration",
                    "-framework", "Security",
                    "-framework", "CoreFoundation",
                ]),
            ]
        ),
        .target(
            name: "ArxosApp",
            dependencies: ["ArxosCore"],
            path: "Sources/ArxosApp",
            exclude: ["ArxosApp.swift"]
        ),
        .executableTarget(
            name: "ArxosDemo",
            dependencies: ["ArxosCore"],
            path: "Sources/ArxosDemo"
        ),
    ]
)
