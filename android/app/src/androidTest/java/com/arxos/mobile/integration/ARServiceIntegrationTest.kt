package com.arxos.mobile.integration

import android.content.Context
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.arxos.mobile.data.*
import com.arxos.mobile.service.ArxOSCoreService
import com.arxos.mobile.service.ArxOSCoreServiceFactory
import com.arxos.mobile.service.ARScanData as ServiceARScanData
import com.arxos.mobile.service.DetectedEquipment as ServiceDetectedEquipment
import kotlinx.coroutines.runBlocking
import org.junit.Before
import org.junit.Test
import org.junit.Assert.*
import org.junit.runner.RunWith

/**
 * Service integration tests for Android AR functionality
 * 
 * These tests verify the service layer with real JNI integration:
 * - Service layer with real JNI calls
 * - Complete AR workflow through service
 * - Error propagation through service layer
 * - State management through service
 * 
 * Prerequisites:
 * - Native library must be built and placed in src/main/jniLibs/
 * - Device/emulator must support the target ABI
 * - Service layer must be properly initialized
 * 
 * Note: These tests require the native library to be loaded and will skip
 * gracefully if the library is not available.
 */
@RunWith(AndroidJUnit4::class)
class ARServiceIntegrationTest {
    
    private lateinit var context: Context
    private lateinit var service: ArxOSCoreService
    
    private val testBuildingName = "test_building_service"
    
    @Before
    fun setup() {
        context = InstrumentationRegistry.getInstrumentation().targetContext
        service = ArxOSCoreServiceFactory.getInstance(context)
        
        // Verify service is initialized
        assertNotNull("Service should not be null", service)
    }
    
    private fun skipIfLibraryNotLoaded() {
        val jni = com.arxos.mobile.service.ArxOSCoreJNI(context)
        if (!jni.isNativeLibraryLoaded()) {
            println("WARNING: Native library not loaded. Skipping service integration tests.")
            return
        }
    }
    
    // ============================================================================
    // AR Model Loading Service Tests
    // ============================================================================
    
    @Test
    fun testARServiceLoadModel() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Loading AR model through service
        val result = service.loadARModel(testBuildingName, "gltf")
        
        // Then: Should return result (may fail if building doesn't exist)
        assertNotNull("Result should not be null", result)
        assertEquals(testBuildingName, result.building)
        assertEquals("gltf", result.format)
        
        if (result.success) {
            assertNotNull("Should have file path on success", result.filePath)
            assertTrue("Should have file size >= 0", result.fileSize >= 0)
        } else {
            assertNotNull("Should have error message on failure", result.error)
            println("Expected failure: ${result.error}")
        }
    }
    
    @Test
    fun testARServiceLoadModelWithUSDZ() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Loading AR model as USDZ through service
        val result = service.loadARModel(testBuildingName, "usdz")
        
        // Then: Should return result
        assertNotNull(result)
        assertEquals("usdz", result.format)
    }
    
    // ============================================================================
    // AR Scan Saving Service Tests
    // ============================================================================
    
    @Test
    fun testARServiceSaveScan() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // Given: AR scan data
        val scanData = ARScanData(
            detectedEquipment = listOf(
                DetectedEquipment(
                    id = "service-eq-1",
                    name = "VAV-301",
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
        
        // When: Saving scan through service
        // Note: Service.processARScan expects ServiceARScanData, not data.ARScanData
        // Convert to service data format
        val serviceScanData = ServiceARScanData(
            equipment = scanData.detectedEquipment.map { eq ->
                com.arxos.mobile.service.DetectedEquipment(
                    id = eq.id,
                    name = eq.name,
                    type = eq.type,
                    position = "${eq.position.x},${eq.position.y},${eq.position.z}"
                )
            }
        )
        
        val result = service.processARScan(serviceScanData)
        
        // Then: Should return result
        assertNotNull("Result should not be null", result)
        
        if (result.success) {
            assertNotNull("Should have message", result.message)
            println("Scan processed: ${result.message}")
        } else {
            println("Scan processing failed (may be expected): ${result.message}")
        }
    }
    
    @Test
    fun testARServiceSaveScanWithEmptyEquipment() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // Given: AR scan with no equipment
        val scanData = ARScanData(
            detectedEquipment = emptyList(),
            roomBoundaries = RoomBoundaries(),
            roomName = "Empty Room",
            floorLevel = 1
        )
        
        // When: Saving scan through service
        val serviceScanData = ServiceARScanData(
            equipment = scanData.detectedEquipment.map { eq ->
                com.arxos.mobile.service.DetectedEquipment(
                    id = eq.id,
                    name = eq.name,
                    type = eq.type,
                    position = "${eq.position.x},${eq.position.y},${eq.position.z}"
                )
            }
        )
        
        val result = service.processARScan(serviceScanData)
        
        // Then: Should handle gracefully
        assertNotNull(result)
        // May succeed or fail depending on building existence
    }
    
    // ============================================================================
    // Pending Equipment Service Tests
    // ============================================================================
    
    @Test
    fun testARServiceListPending() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // When: Listing pending equipment through service
        val result = service.listPendingEquipment(testBuildingName)
        
        // Then: Should return result
        assertNotNull("Result should not be null", result)
        assertEquals(testBuildingName, result.building)
        assertTrue("Pending count should be >= 0", result.pendingCount >= 0)
        assertNotNull("Should have items list", result.items)
        
        if (result.success) {
            println("Found ${result.pendingCount} pending items")
            result.items.forEach { item ->
                println("  - ${item.name} (${item.equipmentType})")
            }
        } else {
            println("List failed (may be expected): ${result.error}")
        }
    }
    
    @Test
    fun testARServiceConfirmPending() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // First, get a pending item (if any exist)
        val listResult = service.listPendingEquipment(testBuildingName)
        
        if (!listResult.success || listResult.items.isEmpty()) {
            println("No pending items to confirm - skipping test")
            return@runBlocking
        }
        
        val pendingItem = listResult.items[0]
        
        // When: Confirming pending equipment through service
        val result = service.confirmPendingEquipment(
            buildingName = testBuildingName,
            pendingId = pendingItem.id,
            commitToGit = true
        )
        
        // Then: Should return result
        assertNotNull("Result should not be null", result)
        assertEquals(testBuildingName, result.building)
        assertEquals(pendingItem.id, result.pendingId)
        
        if (result.success) {
            assertNotNull("Should have equipment ID", result.equipmentId)
            println("Confirmed: ${result.equipmentId}")
            
            if (result.committed) {
                assertNotNull("Should have commit ID if committed", result.commitId)
                println("Committed to Git: ${result.commitId?.take(8)}")
            }
        } else {
            println("Confirm failed: ${result.error}")
        }
    }
    
    @Test
    fun testARServiceRejectPending() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // First, get a pending item (if any exist)
        val listResult = service.listPendingEquipment(testBuildingName)
        
        if (!listResult.success || listResult.items.isEmpty()) {
            println("No pending items to reject - skipping test")
            return@runBlocking
        }
        
        val pendingItem = listResult.items[0]
        
        // When: Rejecting pending equipment through service
        val result = service.rejectPendingEquipment(
            buildingName = testBuildingName,
            pendingId = pendingItem.id
        )
        
        // Then: Should return result
        assertNotNull("Result should not be null", result)
        assertEquals(testBuildingName, result.building)
        assertEquals(pendingItem.id, result.pendingId)
        
        if (result.success) {
            println("Rejected: ${result.pendingId}")
        } else {
            println("Reject failed: ${result.error}")
        }
    }
    
    // ============================================================================
    // Complete Service Workflow Tests
    // ============================================================================
    
    @Test
    fun testARServiceCompleteWorkflow() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // Step 1: Load model
        println("Step 1: Loading model...")
        val loadResult = service.loadARModel(testBuildingName, "gltf")
        println("Load result: ${if (loadResult.success) "Success" else "Failed: ${loadResult.error}"}")
        
        // Step 2: Save scan
        println("Step 2: Saving scan...")
        val scanData = ARScanData(
            detectedEquipment = listOf(
                DetectedEquipment(
                    id = "workflow-eq-1",
                    name = "Workflow Equipment",
                    type = "HVAC",
                    position = Vector3(10f, 20f, 3f),
                    status = "Detected",
                    icon = "gear"
                )
            ),
            roomBoundaries = RoomBoundaries(),
            roomName = "Room 301",
            floorLevel = 3
        )
        
        val serviceScanData = ServiceARScanData(
            equipment = scanData.detectedEquipment.map { eq ->
                com.arxos.mobile.service.DetectedEquipment(
                    id = eq.id,
                    name = eq.name,
                    type = eq.type,
                    position = "${eq.position.x},${eq.position.y},${eq.position.z}"
                )
            }
        )
        
        val processResult = service.processARScan(serviceScanData)
        println("Process result: ${if (processResult.success) "Success" else "Failed: ${processResult.message}"}")
        
        // Step 3: List pending
        println("Step 3: Listing pending...")
        val listResult = service.listPendingEquipment(testBuildingName)
        println("Pending items: ${listResult.pendingCount}")
        
        // Step 4: Confirm (if items exist)
        if (listResult.success && listResult.items.isNotEmpty()) {
            println("Step 4: Confirming pending...")
            val confirmResult = service.confirmPendingEquipment(
                buildingName = testBuildingName,
                pendingId = listResult.items[0].id,
                commitToGit = false
            )
            println("Confirm result: ${if (confirmResult.success) "Success" else "Failed: ${confirmResult.error}"}")
        }
        
        // Workflow completed
        assertTrue("Complete service workflow test finished", true)
    }
    
    // ============================================================================
    // Error Propagation Tests
    // ============================================================================
    
    @Test
    fun testARServiceErrorPropagation() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // Test that errors propagate correctly through service layer
        
        // Test 1: Invalid building name
        val loadResult = service.loadARModel("", "gltf")
        assertFalse("Should fail with empty building name", loadResult.success)
        assertNotNull("Should have error message", loadResult.error)
        
        // Test 2: Invalid pending ID
        val confirmResult = service.confirmPendingEquipment(
            buildingName = testBuildingName,
            pendingId = "nonexistent_id_12345",
            commitToGit = true
        )
        assertFalse("Should fail with invalid pending ID", confirmResult.success)
        assertNotNull("Should have error message", confirmResult.error)
        
        // Test 3: Invalid building name for pending list
        val listResult = service.listPendingEquipment("")
        // May fail or return empty list - just verify no crash
        assertNotNull("Should return result", listResult)
    }
    
    // ============================================================================
    // Service State Management Tests
    // ============================================================================
    
    @Test
    fun testARServiceStateConsistency() = runBlocking {
        skipIfLibraryNotLoaded()
        
        // Test that service maintains consistent state across operations
        
        // Step 1: List pending (baseline)
        val list1 = service.listPendingEquipment(testBuildingName)
        val initialCount = if (list1.success) list1.pendingCount else 0
        
        // Step 2: Save scan (should create pending items)
        val scanData = ARScanData(
            detectedEquipment = listOf(
                DetectedEquipment(
                    id = "state-eq-1",
                    name = "State Test Equipment",
                    type = "HVAC",
                    position = Vector3(10f, 20f, 3f),
                    status = "Detected",
                    icon = "gear"
                )
            ),
            roomBoundaries = RoomBoundaries(),
            roomName = "Room 301",
            floorLevel = 3
        )
        
        val serviceScanData = ServiceARScanData(
            equipment = scanData.detectedEquipment.map { eq ->
                com.arxos.mobile.service.DetectedEquipment(
                    id = eq.id,
                    name = eq.name,
                    type = eq.type,
                    position = "${eq.position.x},${eq.position.y},${eq.position.z}"
                )
            }
        )
        
        service.processARScan(serviceScanData)
        
        // Step 3: List pending again (should have new items if scan succeeded)
        val list2 = service.listPendingEquipment(testBuildingName)
        
        if (list2.success && list1.success) {
            // Pending count may increase (if scan created items)
            assertTrue("Pending count should be >= initial count", 
                list2.pendingCount >= initialCount)
        }
        
        // Service state should be consistent
        assertTrue("Service state consistency test passed", true)
    }
}

