package com.arxos.mobile.service

import android.content.Context
import android.util.Log
import com.arxos.mobile.data.Equipment
import com.arxos.mobile.data.ARScanData
import com.arxos.mobile.data.DetectedEquipment
import com.arxos.mobile.data.Vector3
import com.arxos.mobile.data.EconomySnapshot

/**
 * JNI wrapper for ArxOS FFI functions
 */
class ArxOSCoreJNI(val context: Context) {  // Changed from private to public for UserProfile access
    
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
    
    /**
     * Load/export building model for AR viewing
     */
    external fun nativeLoadARModel(
        buildingName: String,
        format: String,
        outputPath: String?
    ): String
    
    /**
     * Save AR scan data and process to pending equipment
     */
    external fun nativeSaveARScan(
        jsonData: String,
        buildingName: String,
        userEmail: String?,  // NEW: User email from mobile app (can be null for backward compatibility)
        confidenceThreshold: Double
    ): String
    
    /**
     * List all pending equipment for a building
     */
    external fun nativeListPendingEquipment(buildingName: String): String
    
    /**
     * Confirm a pending equipment item
     */
    external fun nativeConfirmPendingEquipment(
        buildingName: String,
        pendingId: String,
        userEmail: String?,  // NEW: User email from mobile app (can be null for backward compatibility)
        commitToGit: Boolean
    ): String
    
    /**
     * Reject a pending equipment item
     */
    external fun nativeRejectPendingEquipment(
        buildingName: String,
        pendingId: String
    ): String
    
    /**
     * Retrieve economy snapshot information.
     */
    external fun nativeEconomySnapshot(addressOverride: String?): String
    
    /**
     * Stake ARXO tokens.
     */
    external fun nativeEconomyStake(amount: String): String
    
    /**
     * Unstake ARXO tokens.
     */
    external fun nativeEconomyUnstake(amount: String): String
    
    /**
     * Claim staking rewards.
     */
    external fun nativeEconomyClaimRewards(): String
    
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
    
    /**
     * Fetch economy snapshot via JNI.
     */
    suspend fun economySnapshot(addressOverride: String? = null): EconomySnapshot? {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded - returning null economy snapshot")
            return null
        }
        
        return try {
            val json = jni.nativeEconomySnapshot(addressOverride)
            if (json.isEmpty()) {
                Log.w(TAG, "Empty JSON response from nativeEconomySnapshot")
                null
            } else if (json.contains("\"error\"")) {
                val errorMsg = extractErrorMessage(json)
                Log.e(TAG, "Error from nativeEconomySnapshot: $errorMsg")
                null
            } else {
                parseEconomySnapshot(json)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to fetch economy snapshot: ${e.message}", e)
            null
        }
    }
    
    /**
     * Stake ARXO tokens via JNI.
     */
    suspend fun stakeARXO(amount: String): Boolean {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded - stake call ignored")
            return false
        }
        
        return try {
            val json = jni.nativeEconomyStake(amount)
            if (json.contains("\"error\"")) {
                val errorMsg = extractErrorMessage(json)
                Log.e(TAG, "Error from nativeEconomyStake: $errorMsg")
                false
            } else {
                true
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to stake ARXO: ${e.message}", e)
            false
        }
    }
    
    /**
     * Unstake ARXO tokens via JNI.
     */
    suspend fun unstakeARXO(amount: String): Boolean {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded - unstake call ignored")
            return false
        }
        
        return try {
            val json = jni.nativeEconomyUnstake(amount)
            if (json.contains("\"error\"")) {
                val errorMsg = extractErrorMessage(json)
                Log.e(TAG, "Error from nativeEconomyUnstake: $errorMsg")
                false
            } else {
                true
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to unstake ARXO: ${e.message}", e)
            false
        }
    }
    
    /**
     * Claim staking rewards via JNI.
     */
    suspend fun claimStakingRewards(): Boolean {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded - claim call ignored")
            return false
        }
        
        return try {
            val json = jni.nativeEconomyClaimRewards()
            if (json.contains("\"error\"")) {
                val errorMsg = extractErrorMessage(json)
                Log.e(TAG, "Error from nativeEconomyClaimRewards: $errorMsg")
                false
            } else {
                true
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to claim staking rewards: ${e.message}", e)
            false
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
    
    private fun parseEconomySnapshot(json: String): EconomySnapshot? {
        return try {
            val obj = org.json.JSONObject(json)
            EconomySnapshot(
                walletAddress = obj.optString("wallet_address"),
                arxoBalance = obj.optString("arxo_balance"),
                pendingRewards = obj.optString("pending_rewards"),
                totalAssessedValue = obj.optString("total_assessed_value")
            )
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse economy snapshot: ${e.message}", e)
            null
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
            position = Vector3(
                x = positionObj.getDouble("x").toFloat(),
                y = positionObj.getDouble("y").toFloat(),
                z = positionObj.getDouble("z").toFloat()
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
            position = Vector3(
                x = positionObj.getDouble("x").toFloat(),
                y = positionObj.getDouble("y").toFloat(),
                z = positionObj.getDouble("z").toFloat()
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
                position = Vector3(
                    x = posObj.getDouble("x").toFloat(),
                    y = posObj.getDouble("y").toFloat(),
                    z = posObj.getDouble("z").toFloat()
                ),
                status = eqObj.optString("status", "Detected"),
                icon = eqObj.optString("icon", "default")
            )
        }
        return ARScanData(equipment = equipmentList)
    }
    
    /**
     * Load/export building model for AR viewing
     */
    suspend fun loadARModel(
        buildingName: String,
        format: String = "gltf",
        outputPath: String? = null
    ): ARModelLoadResult {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded")
            return ARModelLoadResult(
                success = false,
                building = buildingName,
                format = format,
                filePath = null,
                fileSize = 0,
                error = "Native library not loaded"
            )
        }
        
        return try {
            val json = jni.nativeLoadARModel(buildingName, format, outputPath)
            if (json.isEmpty()) {
                Log.w(TAG, "Empty JSON response from nativeLoadARModel")
                return ARModelLoadResult(
                    success = false,
                    building = buildingName,
                    format = format,
                    filePath = null,
                    fileSize = 0,
                    error = "Empty response from native function"
                )
            }
            
            val obj = org.json.JSONObject(json)
            if (!obj.optBoolean("success", false)) {
                val error = obj.optString("error", "Unknown error")
                Log.e(TAG, "Error from nativeLoadARModel: $error")
                return ARModelLoadResult(
                    success = false,
                    building = buildingName,
                    format = format,
                    filePath = null,
                    fileSize = 0,
                    error = error
                )
            }
            
            ARModelLoadResult(
                success = true,
                building = obj.getString("building"),
                format = obj.getString("format"),
                filePath = obj.optString("file_path", null),
                fileSize = obj.optLong("file_size", 0),
                error = null
            )
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load AR model: ${e.message}", e)
            ARModelLoadResult(
                success = false,
                building = buildingName,
                format = format,
                filePath = null,
                fileSize = 0,
                error = e.message ?: "Unknown error"
            )
        }
    }
    
    /**
     * Save AR scan data and process to pending equipment
     */
    suspend fun saveARScan(
        scanData: ARScanData,
        buildingName: String,
        confidenceThreshold: Double = 0.7
    ): ARScanSaveResult {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded")
            return ARScanSaveResult(
                success = false,
                building = buildingName,
                pendingCount = 0,
                pendingIds = emptyList(),
                confidenceThreshold = confidenceThreshold,
                error = "Native library not loaded"
            )
        }
        
        return try {
            val json = scanDataToJson(scanData)
            // Get user email from UserProfile (optional - can be null for backward compatibility)
            val userEmail = com.arxos.mobile.data.UserProfile.load(jni.context)?.email
            val responseJson = jni.nativeSaveARScan(json, buildingName, userEmail, confidenceThreshold)
            if (responseJson.isEmpty()) {
                Log.w(TAG, "Empty JSON response from nativeSaveARScan")
                return ARScanSaveResult(
                    success = false,
                    building = buildingName,
                    pendingCount = 0,
                    pendingIds = emptyList(),
                    confidenceThreshold = confidenceThreshold,
                    error = "Empty response from native function"
                )
            }
            
            val obj = org.json.JSONObject(responseJson)
            if (!obj.optBoolean("success", false)) {
                val error = obj.optString("error", "Unknown error")
                Log.e(TAG, "Error from nativeSaveARScan: $error")
                return ARScanSaveResult(
                    success = false,
                    building = buildingName,
                    pendingCount = 0,
                    pendingIds = emptyList(),
                    confidenceThreshold = confidenceThreshold,
                    error = error
                )
            }
            
            val pendingIdsArray = obj.optJSONArray("pending_ids")
            val pendingIds = if (pendingIdsArray != null) {
                (0 until pendingIdsArray.length()).map { i ->
                    pendingIdsArray.getString(i)
                }
            } else {
                emptyList()
            }
            
            ARScanSaveResult(
                success = true,
                building = obj.getString("building"),
                pendingCount = obj.optInt("pending_count", 0),
                pendingIds = pendingIds,
                confidenceThreshold = obj.optDouble("confidence_threshold", confidenceThreshold),
                error = null
            )
        } catch (e: Exception) {
            Log.e(TAG, "Failed to save AR scan: ${e.message}", e)
            ARScanSaveResult(
                success = false,
                building = buildingName,
                pendingCount = 0,
                pendingIds = emptyList(),
                confidenceThreshold = confidenceThreshold,
                error = e.message ?: "Unknown error"
            )
        }
    }
    
    /**
     * List all pending equipment for a building
     */
    suspend fun listPendingEquipment(buildingName: String): PendingEquipmentListResult {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded")
            return PendingEquipmentListResult(
                success = false,
                building = buildingName,
                pendingCount = 0,
                items = emptyList(),
                error = "Native library not loaded"
            )
        }
        
        return try {
            val json = jni.nativeListPendingEquipment(buildingName)
            if (json.isEmpty()) {
                Log.w(TAG, "Empty JSON response from nativeListPendingEquipment")
                return PendingEquipmentListResult(
                    success = false,
                    building = buildingName,
                    pendingCount = 0,
                    items = emptyList(),
                    error = "Empty response from native function"
                )
            }
            
            val obj = org.json.JSONObject(json)
            if (!obj.optBoolean("success", false)) {
                val error = obj.optString("error", "Unknown error")
                Log.e(TAG, "Error from nativeListPendingEquipment: $error")
                return PendingEquipmentListResult(
                    success = false,
                    building = buildingName,
                    pendingCount = 0,
                    items = emptyList(),
                    error = error
                )
            }
            
            val itemsArray = obj.optJSONArray("items")
            val items = if (itemsArray != null) {
                (0 until itemsArray.length()).map { i ->
                    parsePendingEquipmentItem(itemsArray.getJSONObject(i).toString())
                }
            } else {
                emptyList()
            }
            
            PendingEquipmentListResult(
                success = true,
                building = obj.getString("building"),
                pendingCount = obj.optInt("pending_count", 0),
                items = items,
                error = null
            )
        } catch (e: Exception) {
            Log.e(TAG, "Failed to list pending equipment: ${e.message}", e)
            PendingEquipmentListResult(
                success = false,
                building = buildingName,
                pendingCount = 0,
                items = emptyList(),
                error = e.message ?: "Unknown error"
            )
        }
    }
    
    /**
     * Confirm a pending equipment item
     */
    suspend fun confirmPendingEquipment(
        buildingName: String,
        pendingId: String,
        commitToGit: Boolean = true
    ): PendingEquipmentConfirmResult {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded")
            return PendingEquipmentConfirmResult(
                success = false,
                building = buildingName,
                pendingId = pendingId,
                equipmentId = null,
                committed = false,
                commitId = null,
                error = "Native library not loaded"
            )
        }
        
        return try {
            // Get user email from UserProfile (optional - can be null for backward compatibility)
            val userEmail = com.arxos.mobile.data.UserProfile.load(jni.context)?.email
            val json = jni.nativeConfirmPendingEquipment(buildingName, pendingId, userEmail, commitToGit)
            if (json.isEmpty()) {
                Log.w(TAG, "Empty JSON response from nativeConfirmPendingEquipment")
                return PendingEquipmentConfirmResult(
                    success = false,
                    building = buildingName,
                    pendingId = pendingId,
                    equipmentId = null,
                    committed = false,
                    commitId = null,
                    error = "Empty response from native function"
                )
            }
            
            val obj = org.json.JSONObject(json)
            if (!obj.optBoolean("success", false)) {
                val error = obj.optString("error", "Unknown error")
                Log.e(TAG, "Error from nativeConfirmPendingEquipment: $error")
                return PendingEquipmentConfirmResult(
                    success = false,
                    building = buildingName,
                    pendingId = pendingId,
                    equipmentId = null,
                    committed = false,
                    commitId = null,
                    error = error
                )
            }
            
            PendingEquipmentConfirmResult(
                success = true,
                building = obj.getString("building"),
                pendingId = obj.getString("pending_id"),
                equipmentId = obj.optString("equipment_id", null),
                committed = obj.optBoolean("committed", false),
                commitId = obj.optString("commit_id", null),
                error = null
            )
        } catch (e: Exception) {
            Log.e(TAG, "Failed to confirm pending equipment: ${e.message}", e)
            PendingEquipmentConfirmResult(
                success = false,
                building = buildingName,
                pendingId = pendingId,
                equipmentId = null,
                committed = false,
                commitId = null,
                error = e.message ?: "Unknown error"
            )
        }
    }
    
    /**
     * Reject a pending equipment item
     */
    suspend fun rejectPendingEquipment(
        buildingName: String,
        pendingId: String
    ): PendingEquipmentRejectResult {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded")
            return PendingEquipmentRejectResult(
                success = false,
                building = buildingName,
                pendingId = pendingId,
                error = "Native library not loaded"
            )
        }
        
        return try {
            val json = jni.nativeRejectPendingEquipment(buildingName, pendingId)
            if (json.isEmpty()) {
                Log.w(TAG, "Empty JSON response from nativeRejectPendingEquipment")
                return PendingEquipmentRejectResult(
                    success = false,
                    building = buildingName,
                    pendingId = pendingId,
                    error = "Empty response from native function"
                )
            }
            
            val obj = org.json.JSONObject(json)
            if (!obj.optBoolean("success", false)) {
                val error = obj.optString("error", "Unknown error")
                Log.e(TAG, "Error from nativeRejectPendingEquipment: $error")
                return PendingEquipmentRejectResult(
                    success = false,
                    building = buildingName,
                    pendingId = pendingId,
                    error = error
                )
            }
            
            PendingEquipmentRejectResult(
                success = true,
                building = obj.getString("building"),
                pendingId = obj.getString("pending_id"),
                error = null
            )
        } catch (e: Exception) {
            Log.e(TAG, "Failed to reject pending equipment: ${e.message}", e)
            PendingEquipmentRejectResult(
                success = false,
                building = buildingName,
                pendingId = pendingId,
                error = e.message ?: "Unknown error"
            )
        }
    }
    
    private fun scanDataToJson(scanData: ARScanData): String {
        val obj = org.json.JSONObject()
        val equipmentArray = org.json.JSONArray()
        
        scanData.detectedEquipment.forEach { eq ->
            val eqObj = org.json.JSONObject()
            eqObj.put("name", eq.name)
            eqObj.put("type", eq.equipment_type)
            
            // Convert Vector3 position to Position3D format
            val posObj = org.json.JSONObject()
            posObj.put("x", eq.position.x.toDouble())
            posObj.put("y", eq.position.y.toDouble())
            posObj.put("z", eq.position.z.toDouble())
            eqObj.put("position", posObj)
            
            // Add confidence and detection method (default values if not present)
            eqObj.put("confidence", 0.9)
            eqObj.put("detectionMethod", "ARCore")
            eqObj.put("status", eq.status)
            eqObj.put("icon", eq.icon)
            equipmentArray.put(eqObj)
        }
        
        obj.put("detectedEquipment", equipmentArray)
        
        // Add room boundaries
        val boundariesObj = org.json.JSONObject()
        boundariesObj.put("walls", org.json.JSONArray())
        boundariesObj.put("openings", org.json.JSONArray())
        obj.put("roomBoundaries", boundariesObj)
        
        // Add metadata fields
        scanData.deviceType?.let { obj.put("deviceType", it) }
        scanData.appVersion?.let { obj.put("appVersion", it) }
        scanData.scanDurationMs?.let { obj.put("scanDurationMs", it) }
        scanData.pointCount?.let { obj.put("pointCount", it) }
        scanData.accuracyEstimate?.let { obj.put("accuracyEstimate", it) }
        scanData.lightingConditions?.let { obj.put("lightingConditions", it) }
        obj.put("roomName", scanData.roomName)
        obj.put("floorLevel", scanData.floorLevel)
        
        return obj.toString()
    }
    
    private fun parsePendingEquipmentItem(json: String): PendingEquipmentItem {
        val obj = org.json.JSONObject(json)
        val positionObj = obj.getJSONObject("position")
        
        return PendingEquipmentItem(
            id = obj.getString("id"),
            name = obj.getString("name"),
            equipmentType = obj.getString("equipment_type"),
            position = Vector3(
                x = positionObj.getDouble("x").toFloat(),
                y = positionObj.getDouble("y").toFloat(),
                z = positionObj.getDouble("z").toFloat()
            ),
            confidence = obj.optDouble("confidence", 0.0),
            detectionMethod = obj.optString("detection_method", ""),
            detectedAt = obj.optString("detected_at", ""),
            floorLevel = obj.optInt("floor_level", 0),
            roomName = obj.optString("room_name", ""),
            status = obj.optString("status", "pending")
        )
    }
    
    // Data classes matching Rust structures
    private data class RoomInfo(
        val id: String,
        val name: String,
        val room_type: String,
        val position: Vector3,
        val properties: Map<String, String>
    )
    
    private data class EquipmentInfo(
        val id: String,
        val name: String,
        val equipment_type: String,
        val status: String,
        val position: Vector3,
        val properties: Map<String, String>
    )
    
    private data class Position(
        val x: Double,
        val y: Double,
        val z: Double
    )
    
    private data class PendingEquipmentItem(
        val id: String,
        val name: String,
        val equipmentType: String,
        val position: Vector3,
        val confidence: Double,
        val detectionMethod: String,
        val detectedAt: String,
        val floorLevel: Int,
        val roomName: String,
        val status: String
    )
}

// Data classes for AR integration results
data class ARModelLoadResult(
    val success: Boolean,
    val building: String,
    val format: String,
    val filePath: String?,
    val fileSize: Long,
    val error: String?
)

data class ARScanSaveResult(
    val success: Boolean,
    val building: String,
    val pendingCount: Int,
    val pendingIds: List<String>,
    val confidenceThreshold: Double,
    val error: String?
)

data class PendingEquipmentListResult(
    val success: Boolean,
    val building: String,
    val pendingCount: Int,
    val items: List<PendingEquipmentItem>,
    val error: String?
)

data class PendingEquipmentItem(
    val id: String,
    val name: String,
    val equipmentType: String,
    val position: Vector3,
    val confidence: Double,
    val detectionMethod: String,
    val detectedAt: String,
    val floorLevel: Int,
    val roomName: String,
    val status: String
)

data class Position(
    val x: Double,
    val y: Double,
    val z: Double
)

data class PendingEquipmentConfirmResult(
    val success: Boolean,
    val building: String,
    val pendingId: String,
    val equipmentId: String?,
    val committed: Boolean,
    val commitId: String?,
    val error: String?
)

data class PendingEquipmentRejectResult(
    val success: Boolean,
    val building: String,
    val pendingId: String,
    val error: String?
)
