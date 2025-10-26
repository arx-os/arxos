package com.arxos.mobile.service

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import com.arxos.mobile.*

class ArxOSCoreService(private val context: Context) {
    
    private var instance: ArxOSMobile? = null
    
    init {
        try {
            instance = ArxOSMobile()
        } catch (e: Exception) {
            android.util.Log.e("ArxOSCoreService", "Failed to initialize ArxOS core: ${e.message}")
        }
    }
    
    fun destroy() {
        instance = null
    }
    
    suspend fun executeCommand(command: String): CommandResult = withContext(Dispatchers.IO) {
        try {
            instance?.executeCommand(command) ?: throw Exception("ArxOS instance not initialized")
        } catch (e: Exception) {
            CommandResult(
                success = false,
                output = "",
                error = e.message,
                executionTimeMs = 0
            )
        }
    }
    
    suspend fun getRooms(): List<Room> = withContext(Dispatchers.IO) {
        try {
            instance?.getRooms()?.map { it.toRoom() } ?: emptyList()
        } catch (e: Exception) {
            android.util.Log.e("ArxOSCoreService", "Failed to get rooms: ${e.message}")
            emptyList()
        }
    }
    
    suspend fun getEquipment(): List<Equipment> = withContext(Dispatchers.IO) {
        try {
            instance?.getEquipment()?.map { it.toEquipment() } ?: emptyList()
        } catch (e: Exception) {
            android.util.Log.e("ArxOSCoreService", "Failed to get equipment: ${e.message}")
            emptyList()
        }
    }
    
    suspend fun getEquipmentByRoom(roomId: String): List<Equipment> = withContext(Dispatchers.IO) {
        try {
            instance?.getEquipmentByRoom(roomId)?.map { it.toEquipment() } ?: emptyList()
        } catch (e: Exception) {
            android.util.Log.e("ArxOSCoreService", "Failed to get equipment by room: ${e.message}")
            emptyList()
        }
    }
    
    suspend fun getGitStatus(): GitStatus? = withContext(Dispatchers.IO) {
        try {
            instance?.getGitStatus()?.toGitStatus()
        } catch (e: Exception) {
            android.util.Log.e("ArxOSCoreService", "Failed to get git status: ${e.message}")
            null
        }
    }
    
    suspend fun syncGit(): Boolean = withContext(Dispatchers.IO) {
        try {
            instance?.syncGit()
            true
        } catch (e: Exception) {
            android.util.Log.e("ArxOSCoreService", "Failed to sync git: ${e.message}")
            false
        }
    }
    
    suspend fun getGitHistory(limit: Int): List<String> = withContext(Dispatchers.IO) {
        try {
            instance?.getGitHistory(limit) ?: emptyList()
        } catch (e: Exception) {
            android.util.Log.e("ArxOSCoreService", "Failed to get git history: ${e.message}")
            emptyList()
        }
    }
    
    suspend fun getGitDiff(): String = withContext(Dispatchers.IO) {
        try {
            instance?.getGitDiff() ?: "No changes detected"
        } catch (e: Exception) {
            android.util.Log.e("ArxOSCoreService", "Failed to get git diff: ${e.message}")
            "Error retrieving diff"
        }
    }
    
    suspend fun createRoom(name: String, floor: Int, wing: String?): Room? = withContext(Dispatchers.IO) {
        try {
            instance?.createRoom(name, floor, wing)?.toRoom()
        } catch (e: Exception) {
            android.util.Log.e("ArxOSCoreService", "Failed to create room: ${e.message}")
            null
        }
    }
    
    suspend fun addEquipment(
        name: String, 
        equipmentType: String, 
        roomId: String, 
        position: Position?
    ): Equipment? = withContext(Dispatchers.IO) {
        try {
            val mobilePosition = position?.let { 
                MobilePosition(
                    x = it.x,
                    y = it.y,
                    z = it.z,
                    coordinateSystem = it.coordinateSystem,
                    accuracy = it.accuracy
                )
            }
            instance?.addEquipment(name, equipmentType, roomId, mobilePosition)?.toEquipment()
        } catch (e: Exception) {
            android.util.Log.e("ArxOSCoreService", "Failed to add equipment: ${e.message}")
            null
        }
    }
    
    suspend fun updateEquipmentStatus(equipmentId: String, status: String): Boolean = withContext(Dispatchers.IO) {
        try {
            instance?.updateEquipmentStatus(equipmentId, status)
            true
        } catch (e: Exception) {
            android.util.Log.e("ArxOSCoreService", "Failed to update equipment status: ${e.message}")
            false
        }
    }
    
    suspend fun processARScan(scanData: ByteArray, roomName: String): ARScanResult? = withContext(Dispatchers.IO) {
        try {
            instance?.processArScan(scanData.toList(), roomName)
        } catch (e: Exception) {
            android.util.Log.e("ArxOSCoreService", "Failed to process AR scan: ${e.message}")
            null
        }
    }
}

// Extension functions to convert UniFFI types to existing data classes
fun MobileRoom.toRoom(): Room {
    return Room(
        id = this.id,
        name = this.name,
        floor = this.floor,
        wing = this.wing,
        roomType = this.roomType,
        equipmentCount = this.equipmentCount
    )
}

fun MobileEquipment.toEquipment(): Equipment {
    return Equipment(
        id = this.id,
        name = this.name,
        equipmentType = this.equipmentType,
        status = this.status,
        location = this.location,
        roomId = this.roomId,
        position = this.position?.toPosition(),
        lastMaintenance = this.lastMaintenance
    )
}

fun MobilePosition.toPosition(): Position {
    return Position(
        x = this.x,
        y = this.y,
        z = this.z,
        coordinateSystem = this.coordinateSystem,
        accuracy = this.accuracy
    )
}

fun GitStatus.toGitStatus(): GitStatus {
    return GitStatus(
        branch = this.branch,
        commitCount = this.commitCount,
        lastCommit = this.lastCommit,
        hasChanges = this.hasChanges,
        syncStatus = this.syncStatus
    )
}

// Legacy data classes for backward compatibility
data class CommandResult(
    val success: Boolean,
    val output: String,
    val error: String?,
    val executionTimeMs: Long
)

data class Room(
    val id: String,
    val name: String,
    val floor: Int,
    val wing: String?,
    val roomType: String,
    val equipmentCount: Int
)

data class Equipment(
    val id: String,
    val name: String,
    val equipmentType: String,
    val status: String,
    val location: String,
    val roomId: String,
    val position: Position?,
    val lastMaintenance: String
)

data class Position(
    val x: Double,
    val y: Double,
    val z: Double,
    val coordinateSystem: String,
    val accuracy: Double
)

data class GitStatus(
    val branch: String,
    val commitCount: Int,
    val lastCommit: String,
    val hasChanges: Boolean,
    val syncStatus: String
)