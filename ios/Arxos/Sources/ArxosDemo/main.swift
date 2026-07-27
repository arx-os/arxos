import Foundation
import ArxosCore

/// CLI-style smoke check for the UniFFI / shim surface (macOS + CI).
print(ArxosCore.hello(name: "iOS"))
print("version=\(ArxosCore.version())")
print("building_id=\(ArxosCore.generateBuildingId())")
