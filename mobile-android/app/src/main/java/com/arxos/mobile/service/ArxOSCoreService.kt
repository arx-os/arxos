package com.arxos.mobile.service

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File

class ArxOSCoreService(private val context: Context) {
    
    companion object {
        init {
            System.loadLibrary("arxos_mobile")
        }
    }
    
    private var instance: Long = 0
    
    init {
        instance = createInstance()
    }
    
    fun destroy() {
        if (instance != 0L) {
            freeInstance(instance)
            instance = 0L
        }
    }
    
    suspend fun executeCommand(command: String): CommandResult = withContext(Dispatchers.IO) {
        try {
            val result = executeCommandNative(instance, command)
            val json = JSONObject(result)
            
            CommandResult(
                success = json.getBoolean("success"),
                output = json.getString("output"),
                error = if (json.has("error") && !json.isNull("error")) json.getString("error") else null,
                executionTimeMs = json.getLong("execution_time_ms")
            )
        } catch (e: Exception) {
            CommandResult(
                success = false,
                output = "",
                error = "Failed to execute command: ${e.message}",
                executionTimeMs = 0
            )
        }
    }
    
    suspend fun getRooms(): List<Room> = withContext(Dispatchers.IO) {
        try {
            val result = getRoomsNative(instance)
            val jsonArray = org.json.JSONArray(result)
            val rooms = mutableListOf<Room>()
            
            for (i in 0 until jsonArray.length()) {
                val roomJson = jsonArray.getJSONObject(i)
                rooms.add(
                    Room(
                        id = roomJson.getString("id"),
                        name = roomJson.getString("name"),
                        floor = roomJson.getInt("floor"),
                        wing = if (roomJson.has("wing") && !roomJson.isNull("wing")) roomJson.getString("wing") else null,
                        roomType = roomJson.getString("room_type"),
                        equipmentCount = roomJson.getInt("equipment_count")
                    )
                )
            }
            rooms
        } catch (e: Exception) {
            emptyList()
        }
    }
    
    suspend fun getEquipment(): List<Equipment> = withContext(Dispatchers.IO) {
        try {
            val result = getEquipmentNative(instance)
            val jsonArray = org.json.JSONArray(result)
            val equipment = mutableListOf<Equipment>()
            
            for (i in 0 until jsonArray.length()) {
                val equipmentJson = jsonArray.getJSONObject(i)
                val position = if (equipmentJson.has("position") && !equipmentJson.isNull("position")) {
                    val posJson = equipmentJson.getJSONObject("position")
                    Position(
                        x = posJson.getDouble("x"),
                        y = posJson.getDouble("y"),
                        z = posJson.getDouble("z"),
                        coordinateSystem = posJson.getString("coordinate_system"),
                        accuracy = posJson.getDouble("accuracy")
                    )
                } else null
                
                equipment.add(
                    Equipment(
                        id = equipmentJson.getString("id"),
                        name = equipmentJson.getString("name"),
                        equipmentType = equipmentJson.getString("equipment_type"),
                        status = equipmentJson.getString("status"),
                        location = equipmentJson.getString("location"),
                        roomId = equipmentJson.getString("room_id"),
                        position = position,
                        lastMaintenance = equipmentJson.getString("last_maintenance")
                    )
                )
            }
            equipment
        } catch (e: Exception) {
            emptyList()
        }
    }
    
    suspend fun getGitStatus(): GitStatus? = withContext(Dispatchers.IO) {
        try {
            val result = getGitStatusNative(instance)
            val json = JSONObject(result)
            
            GitStatus(
                branch = json.getString("branch"),
                commitCount = json.getInt("commit_count"),
                lastCommit = json.getString("last_commit"),
                hasChanges = json.getBoolean("has_changes"),
                syncStatus = json.getString("sync_status")
            )
        } catch (e: Exception) {
            null
        }
    }
    
    // Native method declarations
    private external fun createInstance(): Long
    private external fun createInstanceWithPath(path: String): Long
    private external fun freeInstance(instance: Long)
    private external fun executeCommandNative(instance: Long, command: String): String
    private external fun getRoomsNative(instance: Long): String
    private external fun getEquipmentNative(instance: Long): String
    private external fun getGitStatusNative(instance: Long): String
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