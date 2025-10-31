package com.arxos.mobile.service

import android.content.Context
import android.util.Log
import com.arxos.mobile.data.Equipment

/**
 * JNI wrapper for ArxOS FFI functions
 */
class ArxOSCoreJNI(private val context: Context) {
    
    private var nativeLibraryLoaded = false
    
    init {
        try {
            System.loadLibrary("arxos")
            nativeLibraryLoaded = true
            Log.i(TAG, "Native library loaded successfully")
        } catch (e: UnsatisfiedLinkError) {
            nativeLibraryLoaded = false
            Log.w(TAG, "Native library not found - will work in simulation mode", e)
        } catch (e: Exception) {
            nativeLibraryLoaded = false
            Log.e(TAG, "Error loading native library", e)
        }
    }
    
    /**
     * List all rooms in a building
     */
    external fun nativeListRooms(buildingName: String): String
    
    /**
     * Get a specific room by ID
     */
    external fun nativeGetRoom(buildingName: String, roomId: String): String
    
    /**
     * List all equipment in a building
     */
    external fun nativeListEquipment(buildingName: String): String
    
    /**
     * Get a specific equipment item by ID
     */
    external fun nativeGetEquipment(buildingName: String, equipmentId: String): String
    
    /**
     * Parse AR scan data from JSON
     */
    external fun nativeParseARScan(jsonData: String): String
    
    /**
     * Extract equipment information from AR scan
     */
    external fun nativeExtractEquipment(jsonData: String): String
    
    companion object {
        private const val TAG = "ArxOSCoreJNI"
        
        /**
         * Free a string allocated by native code
         */
        external fun nativeFreeString(ptr: Long)
    }
    
    /**
     * Check if native library is loaded and available
     */
    fun isNativeLibraryLoaded(): Boolean {
        return nativeLibraryLoaded
    }
}

/**
 * Wrapper class to call JNI functions with error handling and JSON parsing
 */
class ArxOSCoreJNIWrapper(private val jni: ArxOSCoreJNI) {
    private val TAG = "ArxOSCoreJNIWrapper"
    
    /**
     * List all rooms in a building
     * Returns empty list if library not loaded or on error
     */
    suspend fun listRooms(buildingName: String): List<Room> {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded - returning empty list")
            return emptyList()
        }
        
        return try {
            val json = jni.nativeListRooms(buildingName)
            if (json.isEmpty()) {
                Log.w(TAG, "Empty JSON response from nativeListRooms")
                return emptyList()
            }
            
            // Check for error JSON
            if (json.contains("\"error\"")) {
                val errorMsg = extractErrorMessage(json)
                Log.e(TAG, "Error from nativeListRooms: $errorMsg")
                return emptyList()
            }
            
            // Parse JSON array of RoomInfo from Rust
            val roomInfos = parseRoomInfoList(json)
            roomInfos.map { roomInfo ->
                Room(
                    id = roomInfo.id,
                    name = roomInfo.name,
                    floor = roomInfo.properties["floor"] ?: "0",
                    coordinates = "${roomInfo.position.x},${roomInfo.position.y},${roomInfo.position.z}"
                )
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to list rooms: ${e.message}", e)
            emptyList()
        }
    }
    
    /**
     * Get a specific room by ID
     */
    suspend fun getRoom(buildingName: String, roomId: String): Room? {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded")
            return null
        }
        
        return try {
            val json = jni.nativeGetRoom(buildingName, roomId)
            if (json.isEmpty()) {
                Log.w(TAG, "Empty JSON response from nativeGetRoom")
                return null
            }
            
            // Check for error JSON
            if (json.contains("\"error\"")) {
                val errorMsg = extractErrorMessage(json)
                Log.e(TAG, "Error from nativeGetRoom: $errorMsg")
                return null
            }
            
            // Parse RoomInfo from Rust
            val roomInfo = parseRoomInfo(json)
            Room(
                id = roomInfo.id,
                name = roomInfo.name,
                floor = roomInfo.properties["floor"] ?: "0",
                coordinates = "${roomInfo.position.x},${roomInfo.position.y},${roomInfo.position.z}"
            )
        } catch (e: Exception) {
            Log.e(TAG, "Failed to get room: ${e.message}", e)
            null
        }
    }
    
    /**
     * List all equipment in a building
     */
    suspend fun listEquipment(buildingName: String): List<Equipment> {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded")
            return emptyList()
        }
        
        return try {
            val json = jni.nativeListEquipment(buildingName)
            if (json.isEmpty()) {
                Log.w(TAG, "Empty JSON response from nativeListEquipment")
                return emptyList()
            }
            
            // Check for error JSON
            if (json.contains("\"error\"")) {
                val errorMsg = extractErrorMessage(json)
                Log.e(TAG, "Error from nativeListEquipment: $errorMsg")
                return emptyList()
            }
            
            // Parse JSON array of EquipmentInfo from Rust
            val equipmentInfos = parseEquipmentInfoList(json)
            equipmentInfos.map { eqInfo ->
                Equipment(
                    id = eqInfo.id,
                    name = eqInfo.name,
                    type = eqInfo.equipment_type,
                    status = eqInfo.status,
                    location = "${eqInfo.position.x},${eqInfo.position.y},${eqInfo.position.z}",
                    lastMaintenance = eqInfo.properties["lastMaintenance"] ?: ""
                )
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to list equipment: ${e.message}", e)
            emptyList()
        }
    }
    
    /**
     * Get a specific equipment item by ID
     */
    suspend fun getEquipment(buildingName: String, equipmentId: String): Equipment? {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded")
            return null
        }
        
        return try {
            val json = jni.nativeGetEquipment(buildingName, equipmentId)
            if (json.isEmpty()) {
                Log.w(TAG, "Empty JSON response from nativeGetEquipment")
                return null
            }
            
            // Check for error JSON
            if (json.contains("\"error\"")) {
                val errorMsg = extractErrorMessage(json)
                Log.e(TAG, "Error from nativeGetEquipment: $errorMsg")
                return null
            }
            
            // Parse EquipmentInfo from Rust
            val eqInfo = parseEquipmentInfo(json)
            Equipment(
                id = eqInfo.id,
                name = eqInfo.name,
                type = eqInfo.equipment_type,
                status = eqInfo.status,
                location = "${eqInfo.position.x},${eqInfo.position.y},${eqInfo.position.z}",
                lastMaintenance = eqInfo.properties["lastMaintenance"] ?: ""
            )
        } catch (e: Exception) {
            Log.e(TAG, "Failed to get equipment: ${e.message}", e)
            null
        }
    }
    
    /**
     * Parse AR scan data from JSON
     */
    suspend fun parseARScan(jsonData: String): ARScanData? {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded")
            return null
        }
        
        return try {
            val json = jni.nativeParseARScan(jsonData)
            if (json.isEmpty()) {
                Log.w(TAG, "Empty JSON response from nativeParseARScan")
                return null
            }
            
            // Check for error JSON
            if (json.contains("\"error\"")) {
                val errorMsg = extractErrorMessage(json)
                Log.e(TAG, "Error from nativeParseARScan: $errorMsg")
                return null
            }
            
            // Parse ARScanData from Rust (matching Rust ARScanData structure)
            parseARScanData(json)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse AR scan: ${e.message}", e)
            null
        }
    }
    
    /**
     * Extract equipment information from AR scan
     */
    suspend fun extractEquipment(jsonData: String): List<Equipment> {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded")
            return emptyList()
        }
        
        return try {
            val json = jni.nativeExtractEquipment(jsonData)
            if (json.isEmpty()) {
                Log.w(TAG, "Empty JSON response from nativeExtractEquipment")
                return emptyList()
            }
            
            // Check for error JSON
            if (json.contains("\"error\"")) {
                val errorMsg = extractErrorMessage(json)
                Log.e(TAG, "Error from nativeExtractEquipment: $errorMsg")
                return emptyList()
            }
            
            // Parse JSON array of EquipmentInfo from Rust
            val equipmentInfos = parseEquipmentInfoList(json)
            equipmentInfos.map { eqInfo ->
                Equipment(
                    id = eqInfo.id,
                    name = eqInfo.name,
                    type = eqInfo.equipment_type,
                    status = eqInfo.status,
                    location = "${eqInfo.position.x},${eqInfo.position.y},${eqInfo.position.z}",
                    lastMaintenance = eqInfo.properties["lastMaintenance"] ?: ""
                )
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to extract equipment: ${e.message}", e)
            emptyList()
        }
    }
    
    // Private helper functions for JSON parsing
    
    private fun extractErrorMessage(json: String): String {
        return try {
            val jsonObj = org.json.JSONObject(json)
            jsonObj.optString("error", "Unknown error")
        } catch (e: Exception) {
            "Failed to parse error message"
        }
    }
    
    private fun parseRoomInfoList(json: String): List<RoomInfo> {
        return try {
            val jsonArray = org.json.JSONArray(json)
            (0 until jsonArray.length()).map { i ->
                parseRoomInfo(jsonArray.getJSONObject(i).toString())
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse room info list: ${e.message}", e)
            emptyList()
        }
    }
    
    private fun parseRoomInfo(json: String): RoomInfo {
        val obj = org.json.JSONObject(json)
        val positionObj = obj.getJSONObject("position")
        val propertiesObj = obj.optJSONObject("properties") ?: org.json.JSONObject()
        
        val properties = mutableMapOf<String, String>()
        propertiesObj.keys().forEach { key ->
            properties[key] = propertiesObj.optString(key, "")
        }
        
        return RoomInfo(
            id = obj.getString("id"),
            name = obj.getString("name"),
            room_type = obj.getString("room_type"),
            position = Position(
                x = positionObj.getDouble("x"),
                y = positionObj.getDouble("y"),
                z = positionObj.getDouble("z")
            ),
            properties = properties
        )
    }
    
    private fun parseEquipmentInfoList(json: String): List<EquipmentInfo> {
        return try {
            val jsonArray = org.json.JSONArray(json)
            (0 until jsonArray.length()).map { i ->
                parseEquipmentInfo(jsonArray.getJSONObject(i).toString())
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse equipment info list: ${e.message}", e)
            emptyList()
        }
    }
    
    private fun parseEquipmentInfo(json: String): EquipmentInfo {
        val obj = org.json.JSONObject(json)
        val positionObj = obj.getJSONObject("position")
        val propertiesObj = obj.optJSONObject("properties") ?: org.json.JSONObject()
        
        val properties = mutableMapOf<String, String>()
        propertiesObj.keys().forEach { key ->
            properties[key] = propertiesObj.optString(key, "")
        }
        
        return EquipmentInfo(
            id = obj.getString("id"),
            name = obj.getString("name"),
            equipment_type = obj.getString("equipment_type"),
            status = obj.getString("status"),
            position = Position(
                x = positionObj.getDouble("x"),
                y = positionObj.getDouble("y"),
                z = positionObj.getDouble("z")
            ),
            properties = properties
        )
    }
    
    private fun parseARScanData(json: String): ARScanData {
        val obj = org.json.JSONObject(json)
        val detectedEquipmentArray = obj.getJSONArray("detectedEquipment")
        val equipmentList = (0 until detectedEquipmentArray.length()).map { i ->
            val eqObj = detectedEquipmentArray.getJSONObject(i)
            val posObj = eqObj.getJSONObject("position")
            DetectedEquipment(
                id = eqObj.optString("id", ""),
                name = eqObj.getString("name"),
                type = eqObj.getString("type"),
                position = "${posObj.getDouble("x")},${posObj.getDouble("y")},${posObj.getDouble("z")}"
            )
        }
        return ARScanData(equipment = equipmentList)
    }
    
    // Data classes matching Rust structures
    private data class RoomInfo(
        val id: String,
        val name: String,
        val room_type: String,
        val position: Position,
        val properties: Map<String, String>
    )
    
    private data class EquipmentInfo(
        val id: String,
        val name: String,
        val equipment_type: String,
        val status: String,
        val position: Position,
        val properties: Map<String, String>
    )
    
    private data class Position(
        val x: Double,
        val y: Double,
        val z: Double
    )
}
