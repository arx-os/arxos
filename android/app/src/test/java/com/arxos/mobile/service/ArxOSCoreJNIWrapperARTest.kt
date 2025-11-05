package com.arxos.mobile.service

import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.mockito.Mock
import org.mockito.Mockito.*
import org.mockito.MockitoAnnotations
import org.mockito.kotlin.any
import org.mockito.kotlin.anyDouble
import org.mockito.kotlin.anyOrNull
import org.mockito.kotlin.anyString
import org.mockito.kotlin.eq
import kotlinx.coroutines.runBlocking

/**
 * Unit tests for ArxOSCoreJNIWrapper AR integration functions
 * 
 * These tests mock the JNI layer to test JSON parsing and error handling
 * for AR-related functions without requiring the native library to be loaded.
 * 
 * Tests cover:
 * - AR model loading (loadARModel)
 * - AR scan saving (saveARScan)
 * - Pending equipment listing (listPendingEquipment)
 * - Pending equipment confirmation (confirmPendingEquipment)
 * - Pending equipment rejection (rejectPendingEquipment)
 */
class ArxOSCoreJNIWrapperARTest {
    
    @Mock
    private lateinit var mockJNI: ArxOSCoreJNI
    
    private lateinit var wrapper: ArxOSCoreJNIWrapper
    
    @Before
    fun setup() {
        MockitoAnnotations.openMocks(this)
        `when`(mockJNI.isNativeLibraryLoaded()).thenReturn(true)
        wrapper = ArxOSCoreJNIWrapper(mockJNI)
    }
    
    // ============================================================================
    // AR Model Loading Tests
    // ============================================================================
    
    @Test
    fun `test loadARModel with success response`() = runBlocking {
        // Given: Valid success response from JNI
        val jsonResponse = """
            {
                "success": true,
                "building": "Test Building",
                "format": "gltf",
                "file_path": "/tmp/arxos_test_building_12345.gltf",
                "file_size": 1024000,
                "message": "Building exported successfully"
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeLoadARModel("Test Building", "gltf", null))
            .thenReturn(jsonResponse)
        
        // When: Calling loadARModel
        val result = wrapper.loadARModel("Test Building", "gltf", null)
        
        // Then: Should parse correctly
        assertTrue("Should succeed", result.success)
        assertEquals("Test Building", result.building)
        assertEquals("gltf", result.format)
        assertEquals("/tmp/arxos_test_building_12345.gltf", result.filePath)
        assertEquals(1024000L, result.fileSize)
        assertNull("Should have no error", result.error)
    }
    
    @Test
    fun `test loadARModel with USDZ format`() = runBlocking {
        // Given: Valid success response for USDZ
        val jsonResponse = """
            {
                "success": true,
                "building": "Test Building",
                "format": "usdz",
                "file_path": "/tmp/arxos_test_building_12345.usdz",
                "file_size": 2048000
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeLoadARModel("Test Building", "usdz", null))
            .thenReturn(jsonResponse)
        
        // When: Calling loadARModel with USDZ
        val result = wrapper.loadARModel("Test Building", "usdz", null)
        
        // Then: Should parse correctly
        assertTrue(result.success)
        assertEquals("usdz", result.format)
        assertEquals("/tmp/arxos_test_building_12345.usdz", result.filePath)
    }
    
    @Test
    fun `test loadARModel with custom output path`() = runBlocking {
        // Given: Valid success response with custom path
        val customPath = "/custom/path/model.gltf"
        val jsonResponse = """
            {
                "success": true,
                "building": "Test Building",
                "format": "gltf",
                "file_path": "$customPath",
                "file_size": 512000
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeLoadARModel("Test Building", "gltf", customPath))
            .thenReturn(jsonResponse)
        
        // When: Calling loadARModel with custom path
        val result = wrapper.loadARModel("Test Building", "gltf", customPath)
        
        // Then: Should use custom path
        assertTrue(result.success)
        assertEquals(customPath, result.filePath)
    }
    
    @Test
    fun `test loadARModel with error response`() = runBlocking {
        // Given: Error response from JNI
        val errorJson = """
            {
                "success": false,
                "error": "Building not found: Test Building"
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeLoadARModel("Test Building", "gltf", null))
            .thenReturn(errorJson)
        
        // When: Calling loadARModel
        val result = wrapper.loadARModel("Test Building", "gltf", null)
        
        // Then: Should indicate failure
        assertFalse("Should fail", result.success)
        assertEquals("Building not found: Test Building", result.error)
        assertNull("Should have no file path on error", result.filePath)
        assertEquals(0L, result.fileSize)
    }
    
    @Test
    fun `test loadARModel with empty response`() = runBlocking {
        // Given: Empty response
        `when`(mockJNI.nativeLoadARModel("Test Building", "gltf", null))
            .thenReturn("")
        
        // When: Calling loadARModel
        val result = wrapper.loadARModel("Test Building", "gltf", null)
        
        // Then: Should handle gracefully
        assertFalse(result.success)
        assertNotNull("Should have error message", result.error)
        assertTrue("Error should mention empty response", 
            result.error?.contains("Empty") == true || result.error?.contains("empty") == true)
    }
    
    @Test
    fun `test loadARModel when library not loaded`() = runBlocking {
        // Given: Library not loaded
        `when`(mockJNI.isNativeLibraryLoaded()).thenReturn(false)
        val wrapper = ArxOSCoreJNIWrapper(mockJNI)
        
        // When: Calling loadARModel
        val result = wrapper.loadARModel("Test Building", "gltf", null)
        
        // Then: Should return safe default
        assertFalse(result.success)
        assertEquals("Native library not loaded", result.error)
        verify(mockJNI, never()).nativeLoadARModel(anyString(), anyString(), anyOrNull())
    }
    
    // ============================================================================
    // AR Scan Saving Tests
    // ============================================================================
    
    @Test
    fun `test saveARScan with success and pending items`() = runBlocking {
        // Given: Valid success response with pending items
        val jsonResponse = """
            {
                "success": true,
                "building": "Test Building",
                "pending_count": 3,
                "pending_ids": ["pending-1", "pending-2", "pending-3"],
                "confidence_threshold": 0.7,
                "scan_timestamp": "2024-01-15T10:30:00Z",
                "message": "AR scan processed successfully"
            }
        """.trimIndent()
        
        val scanData = com.arxos.mobile.data.ARScanData(
            detectedEquipment = emptyList(),
            roomName = "Room 301",
            floorLevel = 3
        )
        
        // Mock the JSON serialization (in real code, this is done in scanDataToJson)
        `when`(mockJNI.nativeSaveARScan(anyString(), eq("Test Building"), anyOrNull(), eq(0.7)))
            .thenReturn(jsonResponse)
        
        // When: Calling saveARScan
        val result = wrapper.saveARScan(scanData, "Test Building", 0.7)
        
        // Then: Should parse correctly
        assertTrue("Should succeed", result.success)
        assertEquals("Test Building", result.building)
        assertEquals(3, result.pendingCount)
        assertEquals(listOf("pending-1", "pending-2", "pending-3"), result.pendingIds)
        assertEquals(0.7, result.confidenceThreshold, 0.001)
        assertNull("Should have no error", result.error)
    }
    
    @Test
    fun `test saveARScan with success and no pending items`() = runBlocking {
        // Given: Success response with no pending items
        val jsonResponse = """
            {
                "success": true,
                "building": "Test Building",
                "pending_count": 0,
                "pending_ids": [],
                "confidence_threshold": 0.8
            }
        """.trimIndent()
        
        val scanData = com.arxos.mobile.data.ARScanData(
            detectedEquipment = emptyList(),
            roomName = "Room 301"
        )
        
        `when`(mockJNI.nativeSaveARScan(anyString(), eq("Test Building"), anyOrNull(), eq(0.8)))
            .thenReturn(jsonResponse)
        
        // When: Calling saveARScan
        val result = wrapper.saveARScan(scanData, "Test Building", 0.8)
        
        // Then: Should parse correctly
        assertTrue(result.success)
        assertEquals(0, result.pendingCount)
        assertTrue("Should have empty pending IDs", result.pendingIds.isEmpty())
    }
    
    @Test
    fun `test saveARScan with error response`() = runBlocking {
        // Given: Error response
        val errorJson = """
            {
                "success": false,
                "error": "Failed to parse AR scan JSON"
            }
        """.trimIndent()
        
        val scanData = com.arxos.mobile.data.ARScanData(
            detectedEquipment = emptyList(),
            roomName = "Room 301"
        )
        
        `when`(mockJNI.nativeSaveARScan(anyString(), eq("Test Building"), anyOrNull(), eq(0.7)))
            .thenReturn(errorJson)
        
        // When: Calling saveARScan
        val result = wrapper.saveARScan(scanData, "Test Building", 0.7)
        
        // Then: Should indicate failure
        assertFalse(result.success)
        assertEquals("Failed to parse AR scan JSON", result.error)
        assertEquals(0, result.pendingCount)
        assertTrue(result.pendingIds.isEmpty())
    }
    
    @Test
    fun `test saveARScan with empty response`() = runBlocking {
        // Given: Empty response
        val scanData = com.arxos.mobile.data.ARScanData(
            detectedEquipment = emptyList(),
            roomName = "Room 301"
        )
        
        `when`(mockJNI.nativeSaveARScan(anyString(), eq("Test Building"), anyOrNull(), eq(0.7)))
            .thenReturn("")
        
        // When: Calling saveARScan
        val result = wrapper.saveARScan(scanData, "Test Building", 0.7)
        
        // Then: Should handle gracefully
        assertFalse(result.success)
        assertNotNull(result.error)
    }
    
    @Test
    fun `test saveARScan when library not loaded`() = runBlocking {
        // Given: Library not loaded
        `when`(mockJNI.isNativeLibraryLoaded()).thenReturn(false)
        val wrapper = ArxOSCoreJNIWrapper(mockJNI)
        
        val scanData = com.arxos.mobile.data.ARScanData(
            detectedEquipment = emptyList(),
            roomName = "Room 301"
        )
        
        // When: Calling saveARScan
        val result = wrapper.saveARScan(scanData, "Test Building", 0.7)
        
        // Then: Should return safe default
        assertFalse(result.success)
        assertEquals("Native library not loaded", result.error)
        verify(mockJNI, never()).nativeSaveARScan(anyString(), anyString(), anyOrNull(), anyDouble())
    }
    
    // ============================================================================
    // Pending Equipment Listing Tests
    // ============================================================================
    
    @Test
    fun `test listPendingEquipment with items`() = runBlocking {
        // Given: Valid response with pending items
        val jsonResponse = """
            {
                "success": true,
                "building": "Test Building",
                "pending_count": 2,
                "items": [
                    {
                        "id": "pending-1",
                        "name": "VAV-301",
                        "equipment_type": "HVAC",
                        "position": {"x": 10.0, "y": 20.0, "z": 3.0},
                        "confidence": 0.9,
                        "detection_method": "ARCore",
                        "detected_at": "2024-01-15T10:30:00Z",
                        "floor_level": 3,
                        "room_name": "Room 301",
                        "status": "pending"
                    },
                    {
                        "id": "pending-2",
                        "name": "Light Fixture A",
                        "equipment_type": "Lighting",
                        "position": {"x": 5.0, "y": 15.0, "z": 2.5},
                        "confidence": 0.75,
                        "detection_method": "Tap-to-Place",
                        "detected_at": "2024-01-15T10:35:00Z",
                        "floor_level": 3,
                        "room_name": "Room 301",
                        "status": "pending"
                    }
                ]
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeListPendingEquipment("Test Building"))
            .thenReturn(jsonResponse)
        
        // When: Calling listPendingEquipment
        val result = wrapper.listPendingEquipment("Test Building")
        
        // Then: Should parse correctly
        assertTrue("Should succeed", result.success)
        assertEquals("Test Building", result.building)
        assertEquals(2, result.pendingCount)
        assertEquals(2, result.items.size)
        
        // Verify first item
        val item1 = result.items[0]
        assertEquals("pending-1", item1.id)
        assertEquals("VAV-301", item1.name)
        assertEquals("HVAC", item1.equipmentType)
        assertEquals(10.0, item1.position.x, 0.001)
        assertEquals(20.0, item1.position.y, 0.001)
        assertEquals(3.0, item1.position.z, 0.001)
        assertEquals(0.9, item1.confidence, 0.001)
        assertEquals("ARCore", item1.detectionMethod)
        assertEquals(3, item1.floorLevel)
        assertEquals("Room 301", item1.roomName)
        assertEquals("pending", item1.status)
        
        // Verify second item
        val item2 = result.items[1]
        assertEquals("pending-2", item2.id)
        assertEquals("Light Fixture A", item2.name)
        assertEquals("Lighting", item2.equipmentType)
        assertEquals(0.75, item2.confidence, 0.001)
    }
    
    @Test
    fun `test listPendingEquipment with empty list`() = runBlocking {
        // Given: Valid response with no items
        val jsonResponse = """
            {
                "success": true,
                "building": "Test Building",
                "pending_count": 0,
                "items": []
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeListPendingEquipment("Test Building"))
            .thenReturn(jsonResponse)
        
        // When: Calling listPendingEquipment
        val result = wrapper.listPendingEquipment("Test Building")
        
        // Then: Should parse correctly
        assertTrue(result.success)
        assertEquals(0, result.pendingCount)
        assertTrue("Should have empty items list", result.items.isEmpty())
    }
    
    @Test
    fun `test listPendingEquipment with error response`() = runBlocking {
        // Given: Error response
        val errorJson = """
            {
                "success": false,
                "error": "Building not found: Test Building"
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeListPendingEquipment("Test Building"))
            .thenReturn(errorJson)
        
        // When: Calling listPendingEquipment
        val result = wrapper.listPendingEquipment("Test Building")
        
        // Then: Should indicate failure
        assertFalse(result.success)
        assertEquals("Building not found: Test Building", result.error)
        assertEquals(0, result.pendingCount)
        assertTrue(result.items.isEmpty())
    }
    
    @Test
    fun `test listPendingEquipment when library not loaded`() = runBlocking {
        // Given: Library not loaded
        `when`(mockJNI.isNativeLibraryLoaded()).thenReturn(false)
        val wrapper = ArxOSCoreJNIWrapper(mockJNI)
        
        // When: Calling listPendingEquipment
        val result = wrapper.listPendingEquipment("Test Building")
        
        // Then: Should return safe default
        assertFalse(result.success)
        assertEquals("Native library not loaded", result.error)
        verify(mockJNI, never()).nativeListPendingEquipment(anyString())
    }
    
    // ============================================================================
    // Pending Equipment Confirmation Tests
    // ============================================================================
    
    @Test
    fun `test confirmPendingEquipment with success and Git commit`() = runBlocking {
        // Given: Valid success response with Git commit
        val jsonResponse = """
            {
                "success": true,
                "building": "Test Building",
                "pending_id": "pending-1",
                "equipment_id": "eq-123",
                "committed": true,
                "commit_id": "abc123def456",
                "message": "Equipment confirmed and added to building"
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeConfirmPendingEquipment("Test Building", "pending-1", anyOrNull(), true))
            .thenReturn(jsonResponse)
        
        // When: Calling confirmPendingEquipment
        val result = wrapper.confirmPendingEquipment("Test Building", "pending-1", true)
        
        // Then: Should parse correctly
        assertTrue("Should succeed", result.success)
        assertEquals("Test Building", result.building)
        assertEquals("pending-1", result.pendingId)
        assertEquals("eq-123", result.equipmentId)
        assertTrue("Should be committed", result.committed)
        assertEquals("abc123def456", result.commitId)
        assertNull("Should have no error", result.error)
    }
    
    @Test
    fun `test confirmPendingEquipment with success without Git commit`() = runBlocking {
        // Given: Success response without Git commit
        val jsonResponse = """
            {
                "success": true,
                "building": "Test Building",
                "pending_id": "pending-1",
                "equipment_id": "eq-123",
                "committed": false,
                "commit_id": null
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeConfirmPendingEquipment("Test Building", "pending-1", anyOrNull(), false))
            .thenReturn(jsonResponse)
        
        // When: Calling confirmPendingEquipment
        val result = wrapper.confirmPendingEquipment("Test Building", "pending-1", false)
        
        // Then: Should parse correctly
        assertTrue(result.success)
        assertFalse("Should not be committed", result.committed)
        assertNull("Should have no commit ID", result.commitId)
    }
    
    @Test
    fun `test confirmPendingEquipment with error response`() = runBlocking {
        // Given: Error response
        val errorJson = """
            {
                "success": false,
                "error": "Pending equipment not found: pending-999"
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeConfirmPendingEquipment("Test Building", "pending-999", anyOrNull(), true))
            .thenReturn(errorJson)
        
        // When: Calling confirmPendingEquipment
        val result = wrapper.confirmPendingEquipment("Test Building", "pending-999", true)
        
        // Then: Should indicate failure
        assertFalse(result.success)
        assertEquals("Pending equipment not found: pending-999", result.error)
        assertNull(result.equipmentId)
        assertFalse(result.committed)
    }
    
    @Test
    fun `test confirmPendingEquipment when library not loaded`() = runBlocking {
        // Given: Library not loaded
        `when`(mockJNI.isNativeLibraryLoaded()).thenReturn(false)
        val wrapper = ArxOSCoreJNIWrapper(mockJNI)
        
        // When: Calling confirmPendingEquipment
        val result = wrapper.confirmPendingEquipment("Test Building", "pending-1", true)
        
        // Then: Should return safe default
        assertFalse(result.success)
        assertEquals("Native library not loaded", result.error)
        verify(mockJNI, never()).nativeConfirmPendingEquipment(anyString(), anyString(), anyOrNull(), anyBoolean())
    }
    
    // ============================================================================
    // Pending Equipment Rejection Tests
    // ============================================================================
    
    @Test
    fun `test rejectPendingEquipment with success`() = runBlocking {
        // Given: Valid success response
        val jsonResponse = """
            {
                "success": true,
                "building": "Test Building",
                "pending_id": "pending-1",
                "message": "Equipment rejected"
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeRejectPendingEquipment("Test Building", "pending-1"))
            .thenReturn(jsonResponse)
        
        // When: Calling rejectPendingEquipment
        val result = wrapper.rejectPendingEquipment("Test Building", "pending-1")
        
        // Then: Should parse correctly
        assertTrue("Should succeed", result.success)
        assertEquals("Test Building", result.building)
        assertEquals("pending-1", result.pendingId)
        assertNull("Should have no error", result.error)
    }
    
    @Test
    fun `test rejectPendingEquipment with error response`() = runBlocking {
        // Given: Error response
        val errorJson = """
            {
                "success": false,
                "error": "Pending equipment not found: pending-999"
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeRejectPendingEquipment("Test Building", "pending-999"))
            .thenReturn(errorJson)
        
        // When: Calling rejectPendingEquipment
        val result = wrapper.rejectPendingEquipment("Test Building", "pending-999")
        
        // Then: Should indicate failure
        assertFalse(result.success)
        assertEquals("Pending equipment not found: pending-999", result.error)
    }
    
    @Test
    fun `test rejectPendingEquipment when library not loaded`() = runBlocking {
        // Given: Library not loaded
        `when`(mockJNI.isNativeLibraryLoaded()).thenReturn(false)
        val wrapper = ArxOSCoreJNIWrapper(mockJNI)
        
        // When: Calling rejectPendingEquipment
        val result = wrapper.rejectPendingEquipment("Test Building", "pending-1")
        
        // Then: Should return safe default
        assertFalse(result.success)
        assertEquals("Native library not loaded", result.error)
        verify(mockJNI, never()).nativeRejectPendingEquipment(anyString(), anyString())
    }
    
    // ============================================================================
    // Error Handling Tests
    // ============================================================================
    
    @Test
    fun `test all AR functions handle invalid JSON gracefully`() = runBlocking {
        // Given: Invalid JSON responses
        `when`(mockJNI.nativeLoadARModel(anyString(), anyString(), anyOrNull()))
            .thenReturn("invalid json")
        `when`(mockJNI.nativeSaveARScan(anyString(), anyString(), anyOrNull(), anyDouble()))
            .thenReturn("invalid json")
        `when`(mockJNI.nativeListPendingEquipment(anyString()))
            .thenReturn("invalid json")
        `when`(mockJNI.nativeConfirmPendingEquipment(anyString(), anyString(), anyOrNull(), anyBoolean()))
            .thenReturn("invalid json")
        `when`(mockJNI.nativeRejectPendingEquipment(anyString(), anyString()))
            .thenReturn("invalid json")
        
        val scanData = com.arxos.mobile.data.ARScanData(
            detectedEquipment = emptyList(),
            roomName = "Room 301"
        )
        
        // When: Calling all functions
        // Then: Should not throw, but return error results
        val loadResult = wrapper.loadARModel("Test", "gltf", null)
        val saveResult = wrapper.saveARScan(scanData, "Test", 0.7)
        val listResult = wrapper.listPendingEquipment("Test")
        val confirmResult = wrapper.confirmPendingEquipment("Test", "pending-1", true)
        val rejectResult = wrapper.rejectPendingEquipment("Test", "pending-1")
        
        // All should indicate failure
        assertFalse(loadResult.success)
        assertFalse(saveResult.success)
        assertFalse(listResult.success)
        assertFalse(confirmResult.success)
        assertFalse(rejectResult.success)
    }
    
    @Test
    fun `test all AR functions handle empty responses gracefully`() = runBlocking {
        // Given: Empty responses
        `when`(mockJNI.nativeLoadARModel(anyString(), anyString(), anyOrNull()))
            .thenReturn("")
        `when`(mockJNI.nativeSaveARScan(anyString(), anyString(), anyOrNull(), anyDouble()))
            .thenReturn("")
        `when`(mockJNI.nativeListPendingEquipment(anyString()))
            .thenReturn("")
        
        val scanData = com.arxos.mobile.data.ARScanData(
            detectedEquipment = emptyList(),
            roomName = "Room 301"
        )
        
        // When: Calling functions
        val loadResult = wrapper.loadARModel("Test", "gltf", null)
        val saveResult = wrapper.saveARScan(scanData, "Test", 0.7)
        val listResult = wrapper.listPendingEquipment("Test")
        
        // Then: Should handle gracefully
        assertFalse(loadResult.success)
        assertNotNull(loadResult.error)
        assertFalse(saveResult.success)
        assertNotNull(saveResult.error)
        assertFalse(listResult.success)
        assertNotNull(listResult.error)
    }
}

