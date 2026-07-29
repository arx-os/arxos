// Phase 1 UniFFI surface for arxos-core.
//
// When native FFI is linked (`ArxosCoreFFI`), calls go to Rust.
// Otherwise a pure-Swift local CAS shim enables UI + capture-loop development
// on macOS / simulator without an XCFramework.

import Foundation

#if canImport(ArxosCoreFFI)
import ArxosCoreFFI
#endif

#if !canImport(ArxosCoreFFI) && !ALLOW_SHIM
#error("Real UniFFI backend (ArxosCoreFFI) is required for production builds. Define ALLOW_SHIM if you are working on UI styling / demo without the Rust backend.")
#endif

// MARK: - Public models

public struct BuildingSummary: Equatable, Sendable {
    public var buildingId: String
    public var name: String?
    public var headRoot: String?
    public var buildingObject: String?
    public var stagedCount: UInt64

    public init(
        buildingId: String,
        name: String? = nil,
        headRoot: String? = nil,
        buildingObject: String? = nil,
        stagedCount: UInt64 = 0
    ) {
        self.buildingId = buildingId
        self.name = name
        self.headRoot = headRoot
        self.buildingObject = buildingObject
        self.stagedCount = stagedCount
    }
}

public struct CapturePutResult: Equatable, Sendable {
    public var cid: String
    public var objectType: String
}

public struct CommitSummary: Equatable, Sendable {
    public var rootCid: String
    public var buildingId: String
    public var objectCount: UInt64
    public var previousRoot: String?
}

public struct AnnotationOverlay: Equatable, Identifiable, Sendable {
    public var id: String { cid }
    public var cid: String
    public var text: String
    public var x: Double
    public var y: Double
    public var z: Double
    public var distanceM: Double
}

// MARK: - Facade

/// Public Swift façade matching the UniFFI namespace `arxos_core`.
public enum ArxosCore {
    public static func version() -> String {
        #if canImport(ArxosCoreFFI)
        return ArxosCoreFFI.version()
        #else
        return LocalStore.shared.version
        #endif
    }

    public static func hello(name: String) -> String {
        #if canImport(ArxosCoreFFI)
        return ArxosCoreFFI.hello(name: name)
        #else
        return "Hello, \(name) — Arxos core \(version())"
        #endif
    }

    public static func generateBuildingId() -> String {
        #if canImport(ArxosCoreFFI)
        return ArxosCoreFFI.generateBuildingId()
        #else
        return LocalStore.shared.generateBuildingId()
        #endif
    }

    public static func defaultStorePath() -> String {
        let base = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first
            ?? FileManager.default.temporaryDirectory
        let path = base.appendingPathComponent("arxos-store", isDirectory: true).path
        try? FileManager.default.createDirectory(atPath: path, withIntermediateDirectories: true)
        return path
    }

    public static func initBuilding(storePath: String, name: String?) -> BuildingSummary {
        #if canImport(ArxosCoreFFI)
        let s = ArxosCoreFFI.initBuilding(storePath: storePath, name: name)
        return BuildingSummary(
            buildingId: s.buildingId,
            name: s.name,
            headRoot: s.headRoot,
            buildingObject: s.buildingObject,
            stagedCount: s.stagedCount
        )
        #else
        return LocalStore.shared.initBuilding(storePath: storePath, name: name)
        #endif
    }

    public static func openBuilding(storePath: String, buildingId: String) -> BuildingSummary {
        #if canImport(ArxosCoreFFI)
        let s = ArxosCoreFFI.openBuilding(storePath: storePath, buildingId: buildingId)
        return BuildingSummary(
            buildingId: s.buildingId,
            name: s.name,
            headRoot: s.headRoot,
            buildingObject: s.buildingObject,
            stagedCount: s.stagedCount
        )
        #else
        return LocalStore.shared.openBuilding(storePath: storePath, buildingId: buildingId)
        #endif
    }

    public static func listBuildings(storePath: String) -> [BuildingSummary] {
        #if canImport(ArxosCoreFFI)
        return ArxosCoreFFI.listBuildings(storePath: storePath).map {
            BuildingSummary(
                buildingId: $0.buildingId,
                name: $0.name,
                headRoot: $0.headRoot,
                buildingObject: $0.buildingObject,
                stagedCount: $0.stagedCount
            )
        }
        #else
        return LocalStore.shared.listBuildings(storePath: storePath)
        #endif
    }

    public static func captureSpace(
        storePath: String,
        buildingId: String,
        name: String?,
        x: Double, y: Double, z: Double
    ) -> CapturePutResult {
        #if canImport(ArxosCoreFFI)
        let r = ArxosCoreFFI.captureSpace(
            storePath: storePath, buildingId: buildingId, name: name, x: x, y: y, z: z
        )
        return CapturePutResult(cid: r.cid, objectType: r.objectType)
        #else
        return LocalStore.shared.captureSpace(
            storePath: storePath, buildingId: buildingId, name: name, x: x, y: y, z: z
        )
        #endif
    }

    public static func captureAnnotation(
        storePath: String,
        buildingId: String,
        text: String,
        x: Double, y: Double, z: Double
    ) -> CapturePutResult {
        #if canImport(ArxosCoreFFI)
        let r = ArxosCoreFFI.captureAnnotation(
            storePath: storePath, buildingId: buildingId, text: text, x: x, y: y, z: z
        )
        return CapturePutResult(cid: r.cid, objectType: r.objectType)
        #else
        return LocalStore.shared.captureAnnotation(
            storePath: storePath, buildingId: buildingId, text: text, x: x, y: y, z: z
        )
        #endif
    }

    public static func capturePointCloud(
        storePath: String,
        buildingId: String,
        pointsXYZF32LE: Data,
        x: Double, y: Double, z: Double
    ) -> CapturePutResult {
        #if canImport(ArxosCoreFFI)
        let r = ArxosCoreFFI.capturePointCloud(
            storePath: storePath,
            buildingId: buildingId,
            pointsXyzF32Le: pointsXYZF32LE,
            x: x, y: y, z: z
        )
        return CapturePutResult(cid: r.cid, objectType: r.objectType)
        #else
        return LocalStore.shared.capturePointCloud(
            storePath: storePath, buildingId: buildingId,
            points: pointsXYZF32LE, x: x, y: y, z: z
        )
        #endif
    }

    public static func commitBuilding(
        storePath: String,
        buildingId: String,
        message: String?
    ) -> CommitSummary {
        #if canImport(ArxosCoreFFI)
        let r = ArxosCoreFFI.commitBuilding(
            storePath: storePath, buildingId: buildingId, message: message
        )
        return CommitSummary(
            rootCid: r.rootCid,
            buildingId: r.buildingId,
            objectCount: r.objectCount,
            previousRoot: r.previousRoot
        )
        #else
        return LocalStore.shared.commitBuilding(
            storePath: storePath, buildingId: buildingId, message: message
        )
        #endif
    }

    public static func annotationsNear(
        storePath: String,
        buildingId: String,
        x: Double, y: Double, z: Double,
        radiusM: Double
    ) -> [AnnotationOverlay] {
        #if canImport(ArxosCoreFFI)
        return ArxosCoreFFI.annotationsNear(
            storePath: storePath, buildingId: buildingId,
            x: x, y: y, z: z, radiusM: radiusM
        ).map {
            AnnotationOverlay(
                cid: $0.cid, text: $0.text,
                x: $0.x, y: $0.y, z: $0.z, distanceM: $0.distanceM
            )
        }
        #else
        return LocalStore.shared.annotationsNear(
            storePath: storePath, buildingId: buildingId,
            x: x, y: y, z: z, radiusM: radiusM
        )
        #endif
    }

    public static func ingestRoomPlan(
        storePath: String,
        buildingId: String,
        surfaces: [RoomPlanSurface],
        objects: [RoomPlanObject]
    ) -> IngestSummary {
        #if canImport(ArxosCoreFFI)
        let geom = ArxosCoreFFI.RoomPlanGeometry(
            surfaces: surfaces.map { ArxosCoreFFI.RoomPlanSurface(id: $0.id, category: $0.category, transform: $0.transform, dimensions: $0.dimensions) },
            objects: objects.map { ArxosCoreFFI.RoomPlanObject(id: $0.id, category: $0.category, transform: $0.transform, dimensions: $0.dimensions) }
        )
        let r = ArxosCoreFFI.ingestRoomPlan(storePath: storePath, buildingId: buildingId, geometry: geom)
        return IngestSummary(
            spaceCid: r.spaceCid,
            surfaceCids: r.surfaceCids,
            objectCids: r.objectCids
        )
        #else
        // LocalStore Shim fallback if allowed (just return dummy)
        return IngestSummary(
            spaceCid: "b3:shimspace",
            surfaceCids: surfaces.map { _ in "b3:shimsurface" },
            objectCids: objects.map { _ in "b3:shimobject" }
        )
        #endif
    }

    public static func querySpatialVolume(
        storePath: String,
        buildingId: String,
        minX: Double, minY: Double, minZ: Double,
        maxX: Double, maxY: Double, maxZ: Double
    ) -> [SpatialItem] {
        #if canImport(ArxosCoreFFI)
        return ArxosCoreFFI.querySpatialVolume(
            storePath: storePath, buildingId: buildingId,
            minX: minX, minY: minY, minZ: minZ,
            maxX: maxX, maxY: maxY, maxZ: maxZ
        ).map { item in
            var props = [String: String]()
            for kv in item.properties {
                props[kv.key] = kv.value
            }
            return SpatialItem(
                cid: item.cid,
                objectType: item.objectType,
                name: item.name,
                x: item.poseX,
                y: item.poseY,
                z: item.poseZ,
                properties: props
            )
        }
        #else
        return []
        #endif
    }

    public static func mergeBuildingRoot(
        storePath: String,
        buildingId: String,
        otherRootCid: String,
        message: String?
    ) -> MergeResultSummary {
        #if canImport(ArxosCoreFFI)
        let r = ArxosCoreFFI.mergeBuildingRoot(
            storePath: storePath, buildingId: buildingId,
            otherRootCid: otherRootCid, message: message
        )
        return MergeResultSummary(
            rootCid: r.rootCid,
            objectCount: r.objectCount,
            kept: r.kept,
            dedupedAnnotations: r.dedupedAnnotations,
            spatialIndexRoot: r.spatialIndexRoot,
            parentA: r.parentA,
            parentB: r.parentB
        )
        #else
        fatalError("Shim mergeBuildingRoot not supported")
        #endif
    }

    public static func pullRemoteRoot(
        storePath: String,
        peerTicket: String,
        rootCid: String,
        buildingId: String?,
        setHead: Bool,
        allowUntrusted: Bool
    ) -> PullSummary {
        #if canImport(ArxosCoreFFI)
        let r = ArxosCoreFFI.pullRemoteRoot(
            storePath: storePath, peerTicket: peerTicket,
            rootCid: rootCid, buildingId: buildingId,
            setHead: setHead, allowUntrusted: allowUntrusted
        )
        return PullSummary(
            rootCid: r.rootCid,
            objectsStored: r.objectsStored,
            objectsSkipped: r.objectsSkipped,
            adoptedRoot: r.adoptedRoot
        )
        #else
        fatalError("Shim pullRemoteRoot not supported")
        #endif
    }

    public static func exportUsd(
        storePath: String,
        buildingId: String,
        outputPath: String
    ) -> Bool {
        #if canImport(ArxosCoreFFI)
        return ArxosCoreFFI.exportUsd(storePath: storePath, buildingId: buildingId, outputPath: outputPath)
        #else
        return false
        #endif
    }

    public static func exportIfc(
        storePath: String,
        buildingId: String,
        outputPath: String
    ) -> Bool {
        #if canImport(ArxosCoreFFI)
        return ArxosCoreFFI.exportIfc(storePath: storePath, buildingId: buildingId, outputPath: outputPath)
        #else
        return false
        #endif
    }
}

public struct RoomPlanSurface: Equatable, Sendable {
    public var id: String
    public var category: String
    public var transform: [Double]
    public var dimensions: [Double]

    public init(id: String, category: String, transform: [Double], dimensions: [Double]) {
        self.id = id
        self.category = category
        self.transform = transform
        self.dimensions = dimensions
    }
}

public struct RoomPlanObject: Equatable, Sendable {
    public var id: String
    public var category: String
    public var transform: [Double]
    public var dimensions: [Double]

    public init(id: String, category: String, transform: [Double], dimensions: [Double]) {
        self.id = id
        self.category = category
        self.transform = transform
        self.dimensions = dimensions
    }
}

public struct IngestSummary: Equatable, Sendable {
    public var spaceCid: String
    public var surfaceCids: [String]
    public var objectCids: [String]

    public init(spaceCid: String, surfaceCids: [String], objectCids: [String]) {
        self.spaceCid = spaceCid
        self.surfaceCids = surfaceCids
        self.objectCids = objectCids
    }
}

public struct SpatialItem: Equatable, Sendable {
    public var cid: String
    public var objectType: String
    public var name: String?
    public var x: Double
    public var y: Double
    public var z: Double
    public var properties: [String: String]

    public init(cid: String, objectType: String, name: String?, x: Double, y: Double, z: Double, properties: [String: String]) {
        self.cid = cid
        self.objectType = objectType
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.properties = properties
    }
}

public struct MergeResultSummary: Equatable, Sendable {
    public var rootCid: String
    public var objectCount: UInt64
    public var kept: UInt64
    public var dedupedAnnotations: UInt64
    public var spatialIndexRoot: String?
    public var parentA: String
    public var parentB: String

    public init(rootCid: String, objectCount: UInt64, kept: UInt64, dedupedAnnotations: UInt64, spatialIndexRoot: String?, parentA: String, parentB: String) {
        self.rootCid = rootCid
        self.objectCount = objectCount
        self.kept = kept
        self.dedupedAnnotations = dedupedAnnotations
        self.spatialIndexRoot = spatialIndexRoot
        self.parentA = parentA
        self.parentB = parentB
    }
}

public struct PullSummary: Equatable, Sendable {
    public var rootCid: String
    public var objectsStored: UInt64
    public var objectsSkipped: UInt64
    public var adoptedRoot: String?

    public init(rootCid: String, objectsStored: UInt64, objectsSkipped: UInt64, adoptedRoot: String?) {
        self.rootCid = rootCid
        self.objectsStored = objectsStored
        self.objectsSkipped = objectsSkipped
        self.adoptedRoot = adoptedRoot
    }
}

// MARK: - Local Swift shim (no Rust link)

/// File-backed capture store for UI development without UniFFI native lib.
/// Not the production CAS — production uses arxos-core via UniFFI.
final class LocalStore: @unchecked Sendable {
    static let shared = LocalStore()
    let version = "0.1.0"

    private let lock = NSLock()
    private var buildings: [String: BuildingRecord] = [:]
    private var objects: [String: LocalObject] = [:]

    struct BuildingRecord {
        var buildingId: String
        var name: String?
        var headRoot: String?
        var buildingObject: String?
        var pending: [String]
        var headObjects: Set<String>
    }

    struct LocalObject {
        var type: String
        var text: String?
        var name: String?
        var x: Double
        var y: Double
        var z: Double
        var pointCount: Int
    }

    private func key(_ storePath: String, _ buildingId: String) -> String {
        "\(storePath)||\(buildingId)"
    }

    private func cid(for payload: String) -> String {
        // Stable-ish pseudo CID for shim only (not BLAKE3).
        let digest = payload.utf8.reduce(into: UInt64(5381)) { h, b in
            h = ((h << 5) &+ h) &+ UInt64(b)
        }
        return String(format: "b3:shim%056llx", digest)
    }

    func generateBuildingId() -> String {
        let ts = UInt64(Date().timeIntervalSince1970 * 1000)
        let r = UInt64.random(in: 0...UInt64.max)
        return String(format: "01%010llX%016llX", ts & 0xFFFFFFFFFF, r)
    }

    func initBuilding(storePath: String, name: String?) -> BuildingSummary {
        lock.lock(); defer { lock.unlock() }
        let id = generateBuildingId()
        let buildingCid = cid(for: "building:\(id)")
        let rootCid = cid(for: "root:\(id):init")
        let rec = BuildingRecord(
            buildingId: id,
            name: name,
            headRoot: rootCid,
            buildingObject: buildingCid,
            pending: [],
            headObjects: [buildingCid]
        )
        buildings[key(storePath, id)] = rec
        objects[buildingCid] = LocalObject(
            type: "building", text: nil, name: name, x: 0, y: 0, z: 0, pointCount: 0
        )
        persist(storePath: storePath)
        return BuildingSummary(
            buildingId: id, name: name, headRoot: rootCid,
            buildingObject: buildingCid, stagedCount: 0
        )
    }

    func openBuilding(storePath: String, buildingId: String) -> BuildingSummary {
        lock.lock(); defer { lock.unlock() }
        load(storePath: storePath)
        guard let rec = buildings[key(storePath, buildingId)] else {
            return BuildingSummary(buildingId: buildingId)
        }
        return BuildingSummary(
            buildingId: rec.buildingId,
            name: rec.name,
            headRoot: rec.headRoot,
            buildingObject: rec.buildingObject,
            stagedCount: UInt64(rec.pending.count)
        )
    }

    func listBuildings(storePath: String) -> [BuildingSummary] {
        lock.lock(); defer { lock.unlock() }
        load(storePath: storePath)
        return buildings
            .filter { $0.key.hasPrefix(storePath + "||") }
            .map {
                BuildingSummary(
                    buildingId: $0.value.buildingId,
                    name: $0.value.name,
                    headRoot: $0.value.headRoot,
                    buildingObject: $0.value.buildingObject,
                    stagedCount: UInt64($0.value.pending.count)
                )
            }
            .sorted { $0.buildingId < $1.buildingId }
    }

    func captureSpace(
        storePath: String, buildingId: String, name: String?,
        x: Double, y: Double, z: Double
    ) -> CapturePutResult {
        put(storePath: storePath, buildingId: buildingId, type: "space",
            text: nil, name: name, x: x, y: y, z: z, pointCount: 0)
    }

    func captureAnnotation(
        storePath: String, buildingId: String, text: String,
        x: Double, y: Double, z: Double
    ) -> CapturePutResult {
        put(storePath: storePath, buildingId: buildingId, type: "annotation",
            text: text, name: nil, x: x, y: y, z: z, pointCount: 0)
    }

    func capturePointCloud(
        storePath: String, buildingId: String, points: Data,
        x: Double, y: Double, z: Double
    ) -> CapturePutResult {
        put(storePath: storePath, buildingId: buildingId, type: "point_cloud_chunk",
            text: nil, name: nil, x: x, y: y, z: z, pointCount: points.count / 12)
    }

    private func put(
        storePath: String, buildingId: String, type: String,
        text: String?, name: String?,
        x: Double, y: Double, z: Double, pointCount: Int
    ) -> CapturePutResult {
        lock.lock(); defer { lock.unlock() }
        load(storePath: storePath)
        let k = key(storePath, buildingId)
        guard var rec = buildings[k] else {
            return CapturePutResult(cid: "b3:error", objectType: type)
        }
        let objectCid = cid(for: "\(type):\(buildingId):\(UUID().uuidString):\(x):\(y):\(z):\(text ?? name ?? "")")
        objects[objectCid] = LocalObject(
            type: type, text: text, name: name, x: x, y: y, z: z, pointCount: pointCount
        )
        rec.pending.append(objectCid)
        buildings[k] = rec
        persist(storePath: storePath)
        return CapturePutResult(cid: objectCid, objectType: type)
    }

    func commitBuilding(storePath: String, buildingId: String, message: String?) -> CommitSummary {
        lock.lock(); defer { lock.unlock() }
        load(storePath: storePath)
        let k = key(storePath, buildingId)
        guard var rec = buildings[k] else {
            return CommitSummary(rootCid: "b3:error", buildingId: buildingId, objectCount: 0, previousRoot: nil)
        }
        let prev = rec.headRoot
        for p in rec.pending { rec.headObjects.insert(p) }
        let rootCid = cid(for: "root:\(buildingId):\(rec.headObjects.sorted().joined()):\(message ?? "")")
        rec.headRoot = rootCid
        let count = UInt64(rec.headObjects.count)
        rec.pending.removeAll()
        buildings[k] = rec
        persist(storePath: storePath)
        return CommitSummary(
            rootCid: rootCid, buildingId: buildingId,
            objectCount: count, previousRoot: prev
        )
    }

    func annotationsNear(
        storePath: String, buildingId: String,
        x: Double, y: Double, z: Double, radiusM: Double
    ) -> [AnnotationOverlay] {
        lock.lock(); defer { lock.unlock() }
        load(storePath: storePath)
        let k = key(storePath, buildingId)
        guard let rec = buildings[k] else { return [] }
        var hits: [AnnotationOverlay] = []
        for cid in rec.headObjects.union(Set(rec.pending)) {
            guard let obj = objects[cid], obj.type == "annotation" else { continue }
            let dx = obj.x - x, dy = obj.y - y, dz = obj.z - z
            let d = (dx * dx + dy * dy + dz * dz).squareRoot()
            if d <= radiusM {
                hits.append(AnnotationOverlay(
                    cid: cid, text: obj.text ?? "",
                    x: obj.x, y: obj.y, z: obj.z, distanceM: d
                ))
            }
        }
        return hits.sorted { $0.distanceM < $1.distanceM }
    }

    // Persist as JSON under storePath/shim for reload across launches.
    private func metaURL(storePath: String) -> URL {
        URL(fileURLWithPath: storePath).appendingPathComponent("shim-meta.json")
    }

    private func persist(storePath: String) {
        let relevant = buildings.filter { $0.key.hasPrefix(storePath + "||") }
        var payload: [String: Any] = [:]
        var bmap: [String: Any] = [:]
        for (_, rec) in relevant {
            bmap[rec.buildingId] = [
                "name": rec.name as Any,
                "headRoot": rec.headRoot as Any,
                "buildingObject": rec.buildingObject as Any,
                "pending": rec.pending,
                "headObjects": Array(rec.headObjects),
            ]
        }
        payload["buildings"] = bmap
        var omap: [String: Any] = [:]
        for (cid, obj) in objects {
            omap[cid] = [
                "type": obj.type,
                "text": obj.text as Any,
                "name": obj.name as Any,
                "x": obj.x, "y": obj.y, "z": obj.z,
                "pointCount": obj.pointCount,
            ]
        }
        payload["objects"] = omap
        if let data = try? JSONSerialization.data(withJSONObject: payload, options: [.prettyPrinted]) {
            try? FileManager.default.createDirectory(
                at: URL(fileURLWithPath: storePath), withIntermediateDirectories: true
            )
            try? data.write(to: metaURL(storePath: storePath))
        }
    }

    private func load(storePath: String) {
        let url = metaURL(storePath: storePath)
        guard let data = try? Data(contentsOf: url),
              let payload = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        else { return }

        if let bmap = payload["buildings"] as? [String: [String: Any]] {
            for (id, v) in bmap {
                let pending = v["pending"] as? [String] ?? []
                let headObjects = Set(v["headObjects"] as? [String] ?? [])
                buildings[key(storePath, id)] = BuildingRecord(
                    buildingId: id,
                    name: v["name"] as? String,
                    headRoot: v["headRoot"] as? String,
                    buildingObject: v["buildingObject"] as? String,
                    pending: pending,
                    headObjects: headObjects
                )
            }
        }
        if let omap = payload["objects"] as? [String: [String: Any]] {
            for (cid, v) in omap {
                objects[cid] = LocalObject(
                    type: v["type"] as? String ?? "blob",
                    text: v["text"] as? String,
                    name: v["name"] as? String,
                    x: v["x"] as? Double ?? 0,
                    y: v["y"] as? Double ?? 0,
                    z: v["z"] as? Double ?? 0,
                    pointCount: v["pointCount"] as? Int ?? 0
                )
            }
        }
    }
}
