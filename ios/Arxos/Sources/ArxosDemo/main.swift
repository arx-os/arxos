import Foundation
import ArxosCore

/// Capture-loop smoke test against the real UniFFI → Rust CAS (requires linked arxos-ffi).
print("=== Arxos demo (real UniFFI path) ===")
print(ArxosCore.hello(name: "iOS"))
print("version=\(ArxosCore.version())")

let store = FileManager.default.temporaryDirectory
    .appendingPathComponent("arxos-phase1-demo-\(UUID().uuidString)", isDirectory: true)
    .path
try FileManager.default.createDirectory(atPath: store, withIntermediateDirectories: true)
print("store=\(store)")

do {
    let building = try ArxosCore.initBuilding(storePath: store, name: "Demo Hall")
    print("init building_id=\(building.buildingId)")
    print("init head=\(building.headRoot ?? "none")")

    let space = try ArxosCore.captureSpace(
        storePath: store, buildingId: building.buildingId,
        name: "Electrical", x: 1, y: 0, z: 2
    )
    print("space=\(space.cid) type=\(space.objectType)")

    var cloud = Data()
    let pts: [(Float, Float, Float)] = [(0, 0, 0), (2, 0, 0), (2, 0, 2), (0, 0, 2)]
    for p in pts {
        var x = p.0, y = p.1, z = p.2
        withUnsafeBytes(of: &x) { cloud.append(contentsOf: $0) }
        withUnsafeBytes(of: &y) { cloud.append(contentsOf: $0) }
        withUnsafeBytes(of: &z) { cloud.append(contentsOf: $0) }
    }
    let pc = try ArxosCore.capturePointCloud(
        storePath: store, buildingId: building.buildingId,
        pointsXYZF32LE: cloud, x: 0, y: 0, z: 0
    )
    print("point_cloud=\(pc.cid)")

    let ann = try ArxosCore.captureAnnotation(
        storePath: store, buildingId: building.buildingId,
        text: "Main disconnect", x: 1.1, y: 1.4, z: 2.0
    )
    print("annotation=\(ann.cid)")

    let commit = try ArxosCore.commitBuilding(
        storePath: store, buildingId: building.buildingId, message: "phase1 demo"
    )
    print("commit root=\(commit.rootCid) objects=\(commit.objectCount)")

    let reopened = try ArxosCore.openBuilding(storePath: store, buildingId: building.buildingId)
    print("reload head=\(reopened.headRoot ?? "none")")
    assert(reopened.headRoot == commit.rootCid, "head must match committed root")

    let near = try ArxosCore.annotationsNear(
        storePath: store, buildingId: building.buildingId,
        x: 1, y: 1.5, z: 2, radiusM: 5
    )
    print("nearby=\(near.count)")
    for a in near {
        print("  \(String(format: "%.2fm", a.distanceM)) \(a.text)")
    }
    assert(near.contains(where: { $0.text == "Main disconnect" }))

    // Fail-closed: opening a non-existent building must throw, not crash.
    do {
        _ = try ArxosCore.openBuilding(
            storePath: store,
            buildingId: "01NOTAREALBUILDINGID00000000"
        )
        fputs("error: expected open of missing building to throw\n", stderr)
        exit(1)
    } catch {
        print("missing building correctly failed: \(error.localizedDescription)")
    }

    print("=== Demo OK ===")
} catch {
    fputs("demo failed: \(error.localizedDescription)\n", stderr)
    exit(1)
}
