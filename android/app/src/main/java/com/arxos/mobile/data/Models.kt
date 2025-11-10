package com.arxos.mobile.data

// Simple vector class to replace ARCore dependency
data class Vector3(val x: Float, val y: Float, val z: Float)

data class DetectedEquipment(
    val id: String,
    val name: String,
    val type: String,
    val position: Vector3,
    val status: String,
    val icon: String
) {
    /**
     * Equipment type property for FFI compatibility
     */
    val equipment_type: String
        get() = type
}

data class Equipment(
    val id: String,
    val name: String,
    val type: String,
    val status: String,
    val location: String,
    val lastMaintenance: String
)

// Equipment filter enum for UI
enum class EquipmentFilter(val displayName: String) {
    ALL("All"),
    HVAC("HVAC"),
    ELECTRICAL("Electrical"),
    PLUMBING("Plumbing"),
    SAFETY("Safety")
}

data class Room(
    val id: String,
    val name: String,
    val floor: Int,
    val equipment: List<Equipment> = emptyList()
)

data class TerminalOutput(
    val lines: List<String> = emptyList(),
    val isExecuting: Boolean = false
)

data class EconomySnapshot(
    val walletAddress: String,
    val arxoBalance: String,
    val pendingRewards: String,
    val totalAssessedValue: String
)

data class ARScanResult(
    val room: String,
    val equipment: List<DetectedEquipment>,
    val timestamp: Long = System.currentTimeMillis()
)

/**
 * AR Scan Data - matches Rust ARScanData structure
 * Used for serialization to FFI
 */
data class ARScanData(
    val detectedEquipment: List<DetectedEquipment>,
    val roomBoundaries: RoomBoundaries = RoomBoundaries(),
    val deviceType: String? = null,
    val appVersion: String? = null,
    val scanDurationMs: Long? = null,
    val pointCount: Long? = null,
    val accuracyEstimate: Double? = null,
    val lightingConditions: String? = null,
    val roomName: String = "",
    val floorLevel: Int = 0
)

/**
 * Room boundaries for AR scan
 */
data class RoomBoundaries(
    val walls: List<Wall> = emptyList(),
    val openings: List<Opening> = emptyList()
)

/**
 * Wall definition
 */
data class Wall(
    val start: Vector3,
    val end: Vector3,
    val height: Float
)

/**
 * Opening definition (doors, windows)
 */
data class Opening(
    val position: Vector3,
    val width: Float,
    val height: Float,
    val type: String
)
