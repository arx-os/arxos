// Disambiguation layer: uniquely named free functions call UniFFI free functions.
// (Façade method names collide with generated `initBuilding`, `commitBuilding`, …)

import Foundation

func uniffiVersion() -> String { version() }

func uniffiHello(name: String) -> String { hello(name: name) }

func uniffiGenerateBuildingId() -> String { generateBuildingId() }

func uniffiInitBuilding(storePath: String, name: String?) throws -> FfiBuildingSummary {
    try initBuilding(storePath: storePath, name: name)
}

func uniffiOpenBuilding(storePath: String, buildingId: String) throws -> FfiBuildingSummary {
    try openBuilding(storePath: storePath, buildingId: buildingId)
}

func uniffiListBuildings(storePath: String) throws -> [FfiBuildingSummary] {
    try listBuildings(storePath: storePath)
}

func uniffiCaptureSpace(
    storePath: String, buildingId: String, name: String?,
    x: Double, y: Double, z: Double
) throws -> FfiCapturePutResult {
    try captureSpace(
        storePath: storePath, buildingId: buildingId, name: name, x: x, y: y, z: z
    )
}

func uniffiCaptureAnnotation(
    storePath: String, buildingId: String, text: String,
    x: Double, y: Double, z: Double
) throws -> FfiCapturePutResult {
    try captureAnnotation(
        storePath: storePath, buildingId: buildingId, text: text, x: x, y: y, z: z
    )
}

func uniffiCapturePointCloud(
    storePath: String, buildingId: String, pointsXyzF32Le: Data,
    x: Double, y: Double, z: Double
) throws -> FfiCapturePutResult {
    try capturePointCloud(
        storePath: storePath, buildingId: buildingId,
        pointsXyzF32Le: pointsXyzF32Le, x: x, y: y, z: z
    )
}

func uniffiCommitBuilding(
    storePath: String, buildingId: String, message: String?
) throws -> FfiCommitSummary {
    try commitBuilding(storePath: storePath, buildingId: buildingId, message: message)
}

func uniffiAnnotationsNear(
    storePath: String, buildingId: String,
    x: Double, y: Double, z: Double, radiusM: Double
) throws -> [FfiAnnotationOverlay] {
    try annotationsNear(
        storePath: storePath, buildingId: buildingId,
        x: x, y: y, z: z, radiusM: radiusM
    )
}

func uniffiIngestRoomPlan(
    storePath: String, buildingId: String, geometry: RoomPlanGeometry
) throws -> IngestResult {
    try ingestRoomPlan(storePath: storePath, buildingId: buildingId, geometry: geometry)
}

func uniffiQuerySpatialVolume(
    storePath: String, buildingId: String,
    minX: Double, minY: Double, minZ: Double,
    maxX: Double, maxY: Double, maxZ: Double
) throws -> [SpatialQueryResult] {
    try querySpatialVolume(
        storePath: storePath, buildingId: buildingId,
        minX: minX, minY: minY, minZ: minZ,
        maxX: maxX, maxY: maxY, maxZ: maxZ
    )
}

func uniffiMergeBuildingRoot(
    storePath: String, buildingId: String,
    otherRootCid: String, message: String?
) throws -> MergeSummary {
    try mergeBuildingRoot(
        storePath: storePath, buildingId: buildingId,
        otherRootCid: otherRootCid, message: message
    )
}

func uniffiPullRemoteRoot(
    storePath: String, peerTicket: String, rootCid: String,
    buildingId: String?, setHead: Bool, allowUntrusted: Bool
) throws -> PullResultSummary {
    try pullRemoteRoot(
        storePath: storePath, peerTicket: peerTicket, rootCid: rootCid,
        buildingId: buildingId, setHead: setHead, allowUntrusted: allowUntrusted
    )
}

func uniffiExportUsd(storePath: String, buildingId: String, outputPath: String) throws {
    try exportUsd(storePath: storePath, buildingId: buildingId, outputPath: outputPath)
}

func uniffiExportIfc(storePath: String, buildingId: String, outputPath: String) throws {
    try exportIfc(storePath: storePath, buildingId: buildingId, outputPath: outputPath)
}
