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
)

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

data class ARScanResult(
    val room: String,
    val equipment: List<DetectedEquipment>,
    val timestamp: Long = System.currentTimeMillis()
)
