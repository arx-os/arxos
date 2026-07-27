// Phase 0 UniFFI surface for arxos-core.
//
// When `Scripts/generate_bindings.sh` has been run against a UniFFI-enabled
// build, replace this shim with the generated `arxos_core.swift` (or keep this
// file as a thin re-export). Until the native library is linked, the pure-Swift
// fallback implements the same API for UI compile checks.

import Foundation

#if canImport(ArxosCoreFFI)
import ArxosCoreFFI
#endif

/// Public Swift façade matching the UniFFI namespace `arxos_core`.
public enum ArxosCore {
    /// Library version string (e.g. "0.1.0").
    public static func version() -> String {
        #if canImport(ArxosCoreFFI)
        return ArxosCoreFFI.version()
        #else
        return Phase0Shim.version
        #endif
    }

    /// Smoke-test greeting used by the blank SwiftUI app.
    public static func hello(name: String) -> String {
        #if canImport(ArxosCoreFFI)
        return ArxosCoreFFI.hello(name: name)
        #else
        return "Hello, \(name) — Arxos core \(version())"
        #endif
    }

    /// Generate a new BuildingId (ULID string).
    public static func generateBuildingId() -> String {
        #if canImport(ArxosCoreFFI)
        return ArxosCoreFFI.generateBuildingId()
        #else
        return Phase0Shim.generateBuildingId()
        #endif
    }
}

/// Pure-Swift fallback so the app compiles without a linked staticlib.
enum Phase0Shim {
    static let version = "0.1.0"

    static func generateBuildingId() -> String {
        // Not a real ULID; only for offline UI previews.
        let ts = UInt64(Date().timeIntervalSince1970 * 1000)
        return String(format: "01PREVIEW%010llX", ts)
    }
}
