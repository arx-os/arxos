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
        .library(name: "ArxosAppLib", targets: ["ArxosApp"]),
        .executable(name: "ArxosDemo", targets: ["ArxosDemo"]),
    ],
    targets: [
        .target(
            name: "ArxosCore",
            path: "Sources/ArxosCore"
        ),
        // App sources as a library so `swift build` typechecks UI without @main iOS app.
        .target(
            name: "ArxosApp",
            dependencies: ["ArxosCore"],
            path: "Sources/ArxosApp",
            exclude: ["ArxosApp.swift"] // @main app entry is for Xcode; demo uses ArxosDemo
        ),
        .executableTarget(
            name: "ArxosDemo",
            dependencies: ["ArxosCore"],
            path: "Sources/ArxosDemo"
        ),
    ]
)
