package com.arxos.mobile.service

import android.content.Context
import com.arxos.mobile.data.Equipment
import com.arxos.mobile.data.ARScanData
import com.arxos.mobile.data.DetectedEquipment
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Singleton factory for ArxOSCoreService
 * Use Application context for long-lived service
 */
object ArxOSCoreServiceFactory {
    @Volatile
    private var instance: ArxOSCoreService? = null
    
    fun getInstance(context: Context): ArxOSCoreService {
        return instance ?: synchronized(this) {
            instance ?: ArxOSCoreService(context.applicationContext).also { instance = it }
        }
    }
    
    fun destroy() {
        instance = null
    }
}

class ArxOSCoreService(private val context: Context) {

    private val jni = ArxOSCoreJNI(context)
    private val wrapper = ArxOSCoreJNIWrapper(jni)

    @Volatile
    private var activeBuildingName: String = DEFAULT_BUILDING

    init {
        android.util.Log.i("ArxOSCoreService", "ArxOS Core Service initialized")
    }

    fun setActiveBuilding(buildingName: String) {
        activeBuildingName = buildingName.takeIf { it.isNotBlank() } ?: DEFAULT_BUILDING
    }

    fun destroy() {
        // Service cleanup
    }

    private fun resolveBuildingName(requested: String?): String {
        return requested?.takeIf { it.isNotBlank() } ?: activeBuildingName
    }

    suspend fun executeCommand(command: String): CommandResult = withContext(Dispatchers.IO) {
        try {
            val output = FFIWrapper.executeCommand(command)
            CommandResult(
                success = true,
                output = output,
                error = null,
                executionTimeMs = 0
            )
        } catch (e: Exception) {
            CommandResult(
                success = false,
                output = "",
                error = e.message,
                executionTimeMs = 0
            )
        }
    }

    suspend fun getRooms(buildingName: String? = null): List<Room> = withContext(Dispatchers.IO) {
        wrapper.listRooms(resolveBuildingName(buildingName))
    }

    suspend fun getEquipment(buildingName: String? = null): List<Equipment> = withContext(Dispatchers.IO) {
        wrapper.listEquipment(resolveBuildingName(buildingName))
    }

    suspend fun getEquipmentByRoom(buildingName: String? = null, roomId: String): List<Equipment> = withContext(Dispatchers.IO) {
        val equipment = wrapper.listEquipment(resolveBuildingName(buildingName))
        equipment.filter { it.location.contains(roomId, ignoreCase = true) || it.name.contains(roomId, ignoreCase = true) }
    }

    suspend fun getGitStatus(): GitStatus? = withContext(Dispatchers.IO) {
        null
    }

    suspend fun syncGit() = withContext(Dispatchers.IO) {
        // Git sync implementation
    }

    suspend fun getGitHistory(): List<GitCommit> = withContext(Dispatchers.IO) {
        emptyList()
    }

    suspend fun getGitDiff(): String = withContext(Dispatchers.IO) {
        ""
    }

    suspend fun createRoom(room: Room): Boolean = withContext(Dispatchers.IO) {
        false
    }

    suspend fun addEquipment(equipment: Equipment): Boolean = withContext(Dispatchers.IO) {
        false
    }

    suspend fun updateEquipmentStatus(equipmentId: String, status: String): Boolean = withContext(Dispatchers.IO) {
        false
    }

    suspend fun processARScan(scanData: ARScanData, buildingName: String? = null): ARScanResult = withContext(Dispatchers.IO) {
        val result = wrapper.saveARScan(scanData, resolveBuildingName(buildingName), 0.7)
 
         if (result.success) {
             ARScanResult(
                 success = true,
                 detectedEquipment = scanData.detectedEquipment,
                 message = "AR scan processed: ${result.pendingCount} pending items created"
             )
         } else {
             ARScanResult(
                 success = false,
                 detectedEquipment = scanData.detectedEquipment,
                 message = result.error ?: "Failed to process AR scan"
             )
         }
     }

    suspend fun saveARScan(
        scanData: ARScanData,
        buildingName: String? = null,
        confidenceThreshold: Double = 0.7
    ): ARScanSaveResult = withContext(Dispatchers.IO) {
        wrapper.saveARScan(scanData, resolveBuildingName(buildingName ?: scanData.roomName), confidenceThreshold)
    }

    suspend fun loadARModel(buildingName: String, format: String = "gltf"): ARModelLoadResult = withContext(Dispatchers.IO) {
        wrapper.loadARModel(resolveBuildingName(buildingName), format, null)
    }

    suspend fun listPendingEquipment(buildingName: String? = null): PendingEquipmentListResult = withContext(Dispatchers.IO) {
        wrapper.listPendingEquipment(resolveBuildingName(buildingName))
    }

    suspend fun confirmPendingEquipment(
        buildingName: String,
        pendingId: String,
        commitToGit: Boolean = true
    ): PendingEquipmentConfirmResult = withContext(Dispatchers.IO) {
        wrapper.confirmPendingEquipment(resolveBuildingName(buildingName), pendingId, commitToGit)
    }

    suspend fun rejectPendingEquipment(
        buildingName: String,
        pendingId: String
    ): PendingEquipmentRejectResult = withContext(Dispatchers.IO) {
        wrapper.rejectPendingEquipment(resolveBuildingName(buildingName), pendingId)
    }

    companion object {
        private const val DEFAULT_BUILDING = "main"
    }
}

// MARK: - FFI Wrapper
object FFIWrapper {
    fun executeCommand(command: String): String {
        // FFI implementation when JNI is linked
        throw UnsupportedOperationException("FFI library not yet linked")
    }
}

// Data classes
data class CommandResult(
    val success: Boolean,
    val output: String,
    val error: String?,
    val executionTimeMs: Long
)

data class Room(
    val id: String,
    val name: String,
    val floor: String,
    val coordinates: String
)

data class GitStatus(
    val branch: String,
    val commitCount: Int,
    val lastCommit: String,
    val hasChanges: Boolean,
    val syncStatus: String
)

data class GitCommit(
    val id: String,
    val message: String,
    val author: String,
    val timestamp: Long
)

data class ARScanResult(
    val success: Boolean,
    val detectedEquipment: List<DetectedEquipment>,
    val message: String
)
