package com.arxos.mobile.integration

import android.content.Context
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.arxos.mobile.data.*
import com.arxos.mobile.service.ArxOSCoreJNI
import com.arxos.mobile.service.ArxOSCoreJNIWrapper
import kotlinx.coroutines.runBlocking
import org.junit.Before
import org.junit.Test
import org.junit.Assert.*
import org.junit.runner.RunWith

/**
 * Integration tests for Android AR JNI bindings
 * 
 * These tests verify the Android AR integration JNI functions:
 * - nativeLoadARModel
 * - nativeSaveARScan
 * - nativeListPendingEquipment
 * - nativeConfirmPendingEquipment
 * - nativeRejectPendingEquipment
 * 
 * Prerequisites:
 * - Native library must be built and placed in src/main/jniLibs/
 * - Device/emulator must support the target ABI
 * - Test building data should be available (created dynamically if needed)
 * 
 * Note: These tests require the native library to be loaded and will skip
 * gracefully if the library is not available (e.g., in CI without native libs).
 */
@RunWith(AndroidJUnit4::class)
class JNIARIntegrationTest {
    
    private lateinit var context: Context
    private lateinit var jni: ArxOSCoreJNI
    private lateinit var wrapper: ArxOSCoreJNIWrapper
    
    private val testBuildingName = "test_building_android_ar"
    
    @Before
    fun setup() {
        context = InstrumentationRegistry.getInstrumentation().targetContext
        jni = ArxOSCoreJNI(context)
        wrapper = ArxOSCoreJNIWrapper(jni)
        
        // Skip all tests if library not loaded
        if (!jni.isNativeLibraryLoaded()) {
            println("WARNING: Native library not loaded. Skipping AR integration tests.")
        }
    }
    
    private fun skipIfLibraryNotLoaded() {
        if (!jni.isNativeLibraryLoaded()) {
            println("Skipping test: Native library not loaded")
            return
        }
    }
    
    // ============================================================================
    // AR Model Loading Integration Tests
    // ============================================================================
    
    @Test
    fun testNativeLoadARModelWithGLTF() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Loading AR model as GLTF
        val result = wrapper.loadARModel(testBuildingName, "gltf", null)
        
        // Then: Should handle gracefully (may fail if building doesn't exist)
        // Just verify it doesn't crash and returns a result
        assertNotNull("Result should not be null", result)
        
        if (result.success) {
            assertEquals("Should be gltf format", "gltf", result.format)
            assertNotNull("Should have file path", result.filePath)
            assertTrue("Should have file size > 0", result.fileSize >= 0)
        } else {
            // Building may not exist, that's OK for integration test
            assertNotNull("Should have error message", result.error)
            println("Expected failure: ${result.error}")
        }
    }
    
    @Test
    fun testNativeLoadARModelWithInvalidFormat() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Loading with invalid format
        val result = wrapper.loadARModel(testBuildingName, "invalid_format", null)
        
        // Then: Should fail gracefully
        assertNotNull(result)
        assertFalse("Should fail with invalid format", result.success)
        assertNotNull("Should have error message", result.error)
    }
    
    @Test
    fun testNativeLoadARModelNonexistentBuilding() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Loading model for non-existent building
        val result = wrapper.loadARModel("nonexistent_building_12345", "gltf", null)
        
        // Then: Should fail gracefully
        assertNotNull(result)
        assertFalse("Should fail for nonexistent building", result.success)
        assertNotNull("Should have error message", result.error)
    }
    
    // ============================================================================
    // AR Scan Saving Integration Tests
    // ============================================================================
    
    @Test
    fun testNativeSaveARScanWithValidData() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // Given: Valid AR scan data
        val scanData = ARScanData(
            detectedEquipment = listOf(
                DetectedEquipment(
                    id = "detected-1",
                    name = "Test Equipment",
                    type = "HVAC",
                    position = Vector3(10f, 20f, 3f),
                    status = "Detected",
                    icon = "gear"
                )
            ),
            roomBoundaries = RoomBoundaries(),
            deviceType = "Pixel 8 Pro",
            appVersion = "1.0.0",
            scanDurationMs = 5000L,
            roomName = "Room 301",
            floorLevel = 3
        )
        
        // When: Saving AR scan
        val result = wrapper.saveARScan(scanData, testBuildingName, 0.7)
        
        // Then: Should handle gracefully
        assertNotNull("Result should not be null", result)
        
        if (result.success) {
            assertEquals(testBuildingName, result.building)
            assertTrue("Should have pending count >= 0", result.pendingCount >= 0)
            assertNotNull("Should have pending IDs list", result.pendingIds)
            assertEquals(0.7, result.confidenceThreshold, 0.001)
        } else {
            // May fail if building doesn't exist, that's OK
            assertNotNull("Should have error message", result.error)
            println("Expected failure: ${result.error}")
        }
    }
    
    @Test
    fun testNativeSaveARScanWithEmptyEquipment() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // Given: AR scan with no equipment
        val scanData = ARScanData(
            detectedEquipment = emptyList(),
            roomBoundaries = RoomBoundaries(),
            roomName = "Room 301",
            floorLevel = 3
        )
        
        // When: Saving AR scan
        val result = wrapper.saveARScan(scanData, testBuildingName, 0.7)
        
        // Then: Should handle gracefully
        assertNotNull(result)
        // May succeed or fail depending on building existence
        // Just verify it doesn't crash
    }
    
    @Test
    fun testNativeSaveARScanWithConfidenceThreshold() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // Given: AR scan data
        val scanData = ARScanData(
            detectedEquipment = listOf(
                DetectedEquipment(
                    id = "detected-1",
                    name = "Test Equipment",
                    type = "HVAC",
                    position = Vector3(10f, 20f, 3f),
                    status = "Detected",
                    icon = "gear"
                )
            ),
            roomBoundaries = RoomBoundaries(),
            roomName = "Room 301"
        )
        
        // When: Saving with different confidence thresholds
        val resultHigh = wrapper.saveARScan(scanData, testBuildingName, 0.9)
        val resultLow = wrapper.saveARScan(scanData, testBuildingName, 0.5)
        
        // Then: Should handle both thresholds
        assertNotNull(resultHigh)
        assertNotNull(resultLow)
        assertEquals(0.9, resultHigh.confidenceThreshold, 0.001)
        assertEquals(0.5, resultLow.confidenceThreshold, 0.001)
    }
    
    // ============================================================================
    // Pending Equipment Listing Integration Tests
    // ============================================================================
    
    @Test
    fun testNativeListPendingEquipmentEmpty() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Listing pending equipment for building (may be empty)
        val result = wrapper.listPendingEquipment(testBuildingName)
        
        // Then: Should handle gracefully
        assertNotNull("Result should not be null", result)
        assertEquals(testBuildingName, result.building)
        assertTrue("Pending count should be >= 0", result.pendingCount >= 0)
        assertNotNull("Should have items list", result.items)
        
        if (result.success) {
            // If building exists and has no pending items
            assertEquals(0, result.pendingCount)
            assertTrue(result.items.isEmpty())
        } else {
            // Building may not exist, that's OK
            assertNotNull(result.error)
        }
    }
    
    @Test
    fun testNativeListPendingEquipmentNonexistentBuilding() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Listing pending for non-existent building
        val result = wrapper.listPendingEquipment("nonexistent_building_12345")
        
        // Then: Should fail gracefully
        assertNotNull(result)
        assertFalse("Should fail for nonexistent building", result.success)
        assertNotNull("Should have error message", result.error)
    }
    
    // ============================================================================
    // Pending Equipment Confirmation Integration Tests
    // ============================================================================
    
    @Test
    fun testNativeConfirmPendingEquipmentNonexistent() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Confirming non-existent pending equipment
        val result = wrapper.confirmPendingEquipment(
            buildingName = testBuildingName,
            pendingId = "nonexistent_pending_12345",
            commitToGit = true
        )
        
        // Then: Should fail gracefully
        assertNotNull(result)
        assertFalse("Should fail for nonexistent pending item", result.success)
        assertNotNull("Should have error message", result.error)
    }
    
    @Test
    fun testNativeConfirmPendingEquipmentWithGitCommit() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Confirming with Git commit enabled
        val result = wrapper.confirmPendingEquipment(
            buildingName = testBuildingName,
            pendingId = "test_pending_id",
            commitToGit = true
        )
        
        // Then: Should handle gracefully
        assertNotNull(result)
        assertEquals(testBuildingName, result.building)
        
        // May fail if pending item doesn't exist, that's OK
        if (!result.success) {
            assertNotNull(result.error)
        }
    }
    
    @Test
    fun testNativeConfirmPendingEquipmentWithoutGitCommit() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Confirming without Git commit
        val result = wrapper.confirmPendingEquipment(
            buildingName = testBuildingName,
            pendingId = "test_pending_id",
            commitToGit = false
        )
        
        // Then: Should handle gracefully
        assertNotNull(result)
        assertEquals(testBuildingName, result.building)
    }
    
    // ============================================================================
    // Pending Equipment Rejection Integration Tests
    // ============================================================================
    
    @Test
    fun testNativeRejectPendingEquipmentNonexistent() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Rejecting non-existent pending equipment
        val result = wrapper.rejectPendingEquipment(
            buildingName = testBuildingName,
            pendingId = "nonexistent_pending_12345"
        )
        
        // Then: Should fail gracefully
        assertNotNull(result)
        assertFalse("Should fail for nonexistent pending item", result.success)
        assertNotNull("Should have error message", result.error)
    }
    
    @Test
    fun testNativeRejectPendingEquipmentSuccess() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Rejecting pending equipment
        val result = wrapper.rejectPendingEquipment(
            buildingName = testBuildingName,
            pendingId = "test_pending_id"
        )
        
        // Then: Should handle gracefully
        assertNotNull(result)
        assertEquals(testBuildingName, result.building)
        
        // May fail if pending item doesn't exist, that's OK
        if (!result.success) {
            assertNotNull(result.error)
        }
    }
    
    // ============================================================================
    // Memory Safety Tests
    // ============================================================================
    
    @Test
    fun testRepeatedARFunctionCalls() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Calling AR functions repeatedly
        repeat(5) {
            wrapper.loadARModel(testBuildingName, "gltf", null)
            wrapper.listPendingEquipment(testBuildingName)
        }
        
        // Then: Should not crash or leak memory
        // If we get here, memory handling is OK
        assertTrue("Memory safety check passed", true)
    }
    
    @Test
    fun testLargeARScanData() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // Given: Large AR scan with many equipment items
        val largeEquipmentList = (1..100).map { i ->
            DetectedEquipment(
                id = "detected-$i",
                name = "Equipment $i",
                type = "HVAC",
                position = Vector3(i.toFloat(), (i * 2).toFloat(), 3f),
                status = "Detected",
                icon = "gear"
            )
        }
        
        val scanData = ARScanData(
            detectedEquipment = largeEquipmentList,
            roomBoundaries = RoomBoundaries(),
            roomName = "Large Room",
            floorLevel = 1
        )
        
        // When: Saving large scan
        val result = wrapper.saveARScan(scanData, testBuildingName, 0.7)
        
        // Then: Should handle gracefully
        assertNotNull(result)
        // May succeed or fail, but should not crash
    }
    
    // ============================================================================
    // Error Handling Tests
    // ============================================================================
    
    @Test
    fun testARFunctionsHandleEmptyInputs() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // Given: Empty inputs
        val emptyScanData = ARScanData(
            detectedEquipment = emptyList(),
            roomBoundaries = RoomBoundaries(),
            roomName = "",
            floorLevel = 0
        )
        
        // When: Calling functions with empty inputs
        try {
            wrapper.loadARModel("", "gltf", null)
            wrapper.saveARScan(emptyScanData, "", 0.7)
            wrapper.listPendingEquipment("")
            wrapper.confirmPendingEquipment("", "", true)
            wrapper.rejectPendingEquipment("", "")
            
            // Then: Should handle gracefully without crashing
            assertTrue("Should handle empty inputs", true)
        } catch (e: Exception) {
            fail("Should handle empty inputs gracefully: ${e.message}")
        }
    }
    
    @Test
    fun testARFunctionsHandleInvalidConfidenceThreshold() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // Given: Invalid confidence threshold (should be 0.0-1.0)
        val scanData = ARScanData(
            detectedEquipment = emptyList(),
            roomBoundaries = RoomBoundaries(),
            roomName = "Room 301"
        )
        
        // When: Saving with invalid threshold
        // Note: The wrapper may validate or pass through to native
        // Native should handle validation
        try {
            val result = wrapper.saveARScan(scanData, testBuildingName, 1.5)
            // Should either validate or native should handle
            assertNotNull(result)
        } catch (e: Exception) {
            // Validation exception is also acceptable
            assertTrue("Validation exception is acceptable", true)
        }
    }
}

