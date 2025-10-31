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
 * Wrapper class to call JNI functions with error handling
 */
class ArxOSCoreJNIWrapper(private val jni: ArxOSCoreJNI) {
    private val TAG = "ArxOSCoreJNIWrapper"
    
    suspend fun listRooms(buildingName: String): List<Room> {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w(TAG, "Native library not loaded - returning empty list")
            return emptyList()
        }
        
        return try {
            val json = jni.nativeListRooms(buildingName)
            // TODO: Parse JSON response when library is linked
            // val rooms = Json.decodeFromString<List<Room>>(json)
            // rooms
            emptyList()
        } catch (e: Exception) {
            Log.e(TAG, "Failed to list rooms: ${e.message}", e)
            emptyList()
        }
    }
    
    suspend fun getRoom(buildingName: String, roomId: String): Room? {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w("ArxOSCoreJNI", "Native library not loaded")
            return null
        }
        
        return try {
            val json = jni.nativeGetRoom(buildingName, roomId)
            null
        } catch (e: Exception) {
            Log.e("ArxOSCoreJNI", "Failed to get room: ${e.message}")
            null
        }
    }
    
    suspend fun listEquipment(buildingName: String): List<Equipment> {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w("ArxOSCoreJNI", "Native library not loaded")
            return emptyList()
        }
        
        return try {
            val json = jni.nativeListEquipment(buildingName)
            emptyList()
        } catch (e: Exception) {
            Log.e("ArxOSCoreJNI", "Failed to list equipment: ${e.message}")
            emptyList()
        }
    }
    
    suspend fun getEquipment(buildingName: String, equipmentId: String): Equipment? {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w("ArxOSCoreJNI", "Native library not loaded")
            return null
        }
        
        return try {
            val json = jni.nativeGetEquipment(buildingName, equipmentId)
            null
        } catch (e: Exception) {
            Log.e("ArxOSCoreJNI", "Failed to get equipment: ${e.message}")
            null
        }
    }
    
    suspend fun parseARScan(jsonData: String): ARScanData? {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w("ArxOSCoreJNI", "Native library not loaded")
            return null
        }
        
        return try {
            val json = jni.nativeParseARScan(jsonData)
            null
        } catch (e: Exception) {
            Log.e("ArxOSCoreJNI", "Failed to parse AR scan: ${e.message}")
            null
        }
    }
    
    suspend fun extractEquipment(jsonData: String): List<Equipment> {
        if (!jni.isNativeLibraryLoaded()) {
            Log.w("ArxOSCoreJNI", "Native library not loaded")
            return emptyList()
        }
        
        return try {
            val json = jni.nativeExtractEquipment(jsonData)
            emptyList()
        } catch (e: Exception) {
            Log.e("ArxOSCoreJNI", "Failed to extract equipment: ${e.message}")
            emptyList()
        }
    }
}
