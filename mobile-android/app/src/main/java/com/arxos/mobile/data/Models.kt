package com.arxos.mobile.data

import com.google.ar.sceneform.math.Vector3

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
