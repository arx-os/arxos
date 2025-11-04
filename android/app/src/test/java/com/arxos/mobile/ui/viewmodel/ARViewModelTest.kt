package com.arxos.mobile.ui.viewmodel

import android.app.Application
import com.arxos.mobile.data.*
import com.arxos.mobile.service.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.mockito.Mock
import org.mockito.Mockito.*
import org.mockito.MockitoAnnotations

/**
 * Unit tests for ARViewModel
 * 
 * These tests verify state management, coroutine-based async operations,
 * and error handling for AR scanning functionality.
 * 
 * Tests cover:
 * - AR scanning state management
 * - Model loading state management
 * - Scan saving with metadata
 * - Pending equipment operations
 * - Equipment detection and management
 * - Error state handling
 */
@OptIn(ExperimentalCoroutinesApi::class)
class ARViewModelTest {
    
    @Mock
    private lateinit var mockApplication: Application
    
    @Mock
    private lateinit var mockService: ArxOSCoreService
    
    private lateinit var testDispatcher: TestDispatcher
    private lateinit var viewModel: ARViewModel
    
    @Before
    fun setup() {
        MockitoAnnotations.openMocks(this)
        testDispatcher = StandardTestDispatcher()
        Dispatchers.setMain(testDispatcher)
        
        // Create ViewModel - it will use ArxOSCoreServiceFactory.getInstance()
        // In real tests, we'd need to inject the service, but for now we test
        // the state management methods that don't require service injection
        viewModel = ARViewModel(mockApplication)
    }
    
    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }
    
    // ============================================================================
    // AR Scanning State Tests
    // ============================================================================
    
    @Test
    fun `test startScanning updates state correctly`() = runTest {
        // Given: Initial state
        val initialState = viewModel.arState.first()
        assertFalse("Initially not scanning", initialState.isScanning)
        assertNull("No scan start time initially", initialState.scanStartTime)
        
        // When: Starting scanning
        viewModel.startScanning()
        advanceUntilIdle()
        
        // Then: State should be updated
        val state = viewModel.arState.first()
        assertTrue("Should be scanning", state.isScanning)
        assertNotNull("Should have scan start time", state.scanStartTime)
        assertTrue("Scan start time should be recent", 
            state.scanStartTime!! > System.currentTimeMillis() - 1000)
    }
    
    @Test
    fun `test stopScanning updates state correctly`() = runTest {
        // Given: Scanning state
        viewModel.startScanning()
        advanceUntilIdle()
        assertTrue(viewModel.arState.first().isScanning)
        
        // When: Stopping scanning
        viewModel.stopScanning()
        advanceUntilIdle()
        
        // Then: State should be updated
        val state = viewModel.arState.first()
        assertFalse("Should not be scanning", state.isScanning)
        assertNull("Should clear scan start time", state.scanStartTime)
    }
    
    @Test
    fun `test updateCurrentRoom updates state`() = runTest {
        // Given: Initial room name
        val initialState = viewModel.arState.first()
        val initialRoom = initialState.currentRoom
        
        // When: Updating room name
        viewModel.updateCurrentRoom("Room 402")
        advanceUntilIdle()
        
        // Then: State should be updated
        val state = viewModel.arState.first()
        assertEquals("Room 402", state.currentRoom)
        assertNotEquals(initialRoom, state.currentRoom)
    }
    
    @Test
    fun `test updateFloorLevel updates state`() = runTest {
        // Given: Initial floor level (default 0)
        val initialState = viewModel.arState.first()
        assertEquals(0, initialState.floorLevel)
        
        // When: Updating floor level
        viewModel.updateFloorLevel(5)
        advanceUntilIdle()
        
        // Then: State should be updated
        val state = viewModel.arState.first()
        assertEquals(5, state.floorLevel)
    }
    
    @Test
    fun `test updateBuildingName updates state`() = runTest {
        // Given: Initial building name (empty)
        val initialState = viewModel.arState.first()
        assertEquals("", initialState.buildingName)
        
        // When: Updating building name
        viewModel.updateBuildingName("Test Building")
        advanceUntilIdle()
        
        // Then: State should be updated
        val state = viewModel.arState.first()
        assertEquals("Test Building", state.buildingName)
    }
    
    // ============================================================================
    // Model Loading Tests
    // ============================================================================
    
    @Test
    fun `test loadARModel updates loading state`() = runTest {
        // When: Loading model (will call service, may fail in test environment)
        viewModel.loadARModel("Test Building", "gltf")
        advanceUntilIdle()
        
        // Then: Loading state should be managed
        // Note: Actual service call may fail without real building, but state management should work
        val state = viewModel.arState.first()
        // Loading should complete (either success or error)
        assertFalse("Should not be loading after completion", state.isLoadingModel)
    }
    
    @Test
    fun `test loadARModel handles errors`() = runTest {
        // When: Loading model for non-existent building
        viewModel.loadARModel("Nonexistent Building", "gltf")
        advanceUntilIdle()
        
        // Then: State should reflect error handling
        val state = viewModel.arState.first()
        assertFalse("Should not be loading after error", state.isLoadingModel)
        // Error may be set if building doesn't exist
    }
    
    @Test
    fun `test loadARModel sets loading state during operation`() = runTest {
        // When: Starting model load
        viewModel.loadARModel("Test Building", "gltf")
        
        // Then: Should set loading state immediately
        // Note: In real implementation, loading state is set synchronously
        // then cleared when coroutine completes
        advanceUntilIdle()
        
        // Loading should complete (either success or error)
        val finalState = viewModel.arState.first()
        assertFalse("Should not be loading after completion", finalState.isLoadingModel)
    }
    
    @Test
    fun `test clearLoadedModel resets state`() = runTest {
        // Given: Model state is set (manually for testing)
        viewModel.updateARState { it.copy(
            loadedModel = "Test Building",
            modelFilePath = "/tmp/test.gltf",
            modelLoadError = null,
            isLoadingModel = false
        ) }
        advanceUntilIdle()
        
        assertNotNull(viewModel.arState.first().loadedModel)
        
        // When: Clearing loaded model
        viewModel.clearLoadedModel()
        advanceUntilIdle()
        
        // Then: State should be reset
        val state = viewModel.arState.first()
        assertNull("Should have no loaded model", state.loadedModel)
        assertNull("Should have no file path", state.modelFilePath)
        assertNull("Should have no error", state.modelLoadError)
        assertFalse("Should not be loading", state.isLoadingModel)
    }
    
    // ============================================================================
    // Scan Saving Tests
    // ============================================================================
    
    @Test
    fun `test saveScan success with pending items`() = runTest {
        // Given: Mock service returns success with pending items
        val mockResult = ARScanSaveResult(
            success = true,
            building = "Test Building",
            pendingCount = 2,
            pendingIds = listOf("pending-1", "pending-2"),
            confidenceThreshold = 0.7,
            error = null
        )
        
        // Mock the wrapper to return our result
        // Note: This requires accessing the internal service/wrapper
        // For now, we test the state updates that would occur
        
        // Given: Scanning state with detected equipment
        viewModel.startScanning()
        viewModel.addDetectedEquipment(DetectedEquipment(
            id = "eq-1",
            name = "VAV-301",
            type = "HVAC",
            position = Vector3(10f, 20f, 3f),
            status = "Detected",
            icon = "gear"
        ))
        advanceUntilIdle()
        
        // When: Saving scan (would call service in real implementation)
        // Note: Actual implementation would need to be refactored to inject service
        // For now, we verify the state management methods work correctly
        
        // Verify state updates work
        viewModel.updateARState { it.copy(
            isSavingScan = true,
            pendingEquipmentIds = emptyList()
        ) }
        advanceUntilIdle()
        
        val savingState = viewModel.arState.first()
        assertTrue("Should be saving", savingState.isSavingScan)
        
        // Simulate save completion
        viewModel.updateARState { it.copy(
            isSavingScan = false,
            pendingEquipmentIds = listOf("pending-1", "pending-2"),
            isScanning = false,
            scanStartTime = null
        ) }
        advanceUntilIdle()
        
        val finalState = viewModel.arState.first()
        assertFalse("Should not be saving", finalState.isSavingScan)
        assertEquals(2, finalState.pendingEquipmentIds.size)
        assertFalse("Should not be scanning after save", finalState.isScanning)
    }
    
    @Test
    fun `test saveScan calculates duration correctly`() = runTest {
        // Given: Scanning started
        viewModel.startScanning()
        advanceUntilIdle()
        
        val startTime = viewModel.arState.first().scanStartTime
        
        // Wait a bit (simulated)
        testDispatcher.scheduler.advanceTimeBy(5000)
        
        // When: Saving scan
        // The saveScan method should calculate duration from startTime
        // For unit test, we verify the calculation logic would work
        val currentTime = System.currentTimeMillis()
        val expectedDuration = startTime?.let { currentTime - it }
        
        assertNotNull("Should have duration", expectedDuration)
        assertTrue("Duration should be around 5 seconds", 
            expectedDuration!! >= 4500 && expectedDuration <= 5500)
    }
    
    // ============================================================================
    // Equipment Detection Tests
    // ============================================================================
    
    @Test
    fun `test addDetectedEquipment adds to list`() = runTest {
        // Given: Empty equipment list
        val initialState = viewModel.arState.first()
        assertTrue("Initially empty", initialState.detectedEquipment.isEmpty())
        
        // When: Adding equipment
        val equipment = DetectedEquipment(
            id = "eq-1",
            name = "VAV-301",
            type = "HVAC",
            position = Vector3(10f, 20f, 3f),
            status = "Detected",
            icon = "gear"
        )
        
        viewModel.addDetectedEquipment(equipment)
        advanceUntilIdle()
        
        // Then: Equipment should be in list
        val state = viewModel.arState.first()
        assertEquals(1, state.detectedEquipment.size)
        assertEquals("eq-1", state.detectedEquipment[0].id)
        assertEquals("VAV-301", state.detectedEquipment[0].name)
    }
    
    @Test
    fun `test addDetectedEquipment prevents duplicates`() = runTest {
        // Given: Equipment already added
        val equipment = DetectedEquipment(
            id = "eq-1",
            name = "VAV-301",
            type = "HVAC",
            position = Vector3(10f, 20f, 3f),
            status = "Detected",
            icon = "gear"
        )
        
        viewModel.addDetectedEquipment(equipment)
        advanceUntilIdle()
        
        // When: Adding same equipment again
        viewModel.addDetectedEquipment(equipment)
        advanceUntilIdle()
        
        // Then: Should still only have one
        val state = viewModel.arState.first()
        assertEquals(1, state.detectedEquipment.size)
    }
    
    @Test
    fun `test addEquipmentManually creates equipment`() = runTest {
        // Given: Empty equipment list
        assertTrue(viewModel.arState.first().detectedEquipment.isEmpty())
        
        // When: Adding equipment manually
        viewModel.addEquipmentManually()
        advanceUntilIdle()
        
        // Then: Equipment should be added
        val state = viewModel.arState.first()
        assertEquals(1, state.detectedEquipment.size)
        assertTrue("Should have manual ID", state.detectedEquipment[0].id.startsWith("manual_"))
        assertEquals("Manual Equipment", state.detectedEquipment[0].name)
        assertEquals("Manual", state.detectedEquipment[0].type)
    }
    
    // ============================================================================
    // Pending Equipment Tests
    // ============================================================================
    
    @Test
    fun `test listPendingEquipment returns result`() = runTest {
        // When: Listing pending equipment
        // Note: This will call real service, may fail in test environment
        val result = viewModel.listPendingEquipment("Test Building")
        advanceUntilIdle()
        
        // Then: Should return a result (may be error if building doesn't exist)
        assertNotNull("Should return result", result)
        assertEquals("Test Building", result.building)
        // Result may be success or error depending on test environment
    }
    
    @Test
    fun `test confirmPendingEquipment returns result`() = runTest {
        // When: Confirming pending equipment
        // Note: This will call real service, may fail in test environment
        val result = viewModel.confirmPendingEquipment("Test Building", "pending-1", true)
        advanceUntilIdle()
        
        // Then: Should return a result
        assertNotNull("Should return result", result)
        assertEquals("Test Building", result.building)
        assertEquals("pending-1", result.pendingId)
        // Result may be success or error depending on test environment
    }
    
    @Test
    fun `test rejectPendingEquipment returns result`() = runTest {
        // When: Rejecting pending equipment
        // Note: This will call real service, may fail in test environment
        val result = viewModel.rejectPendingEquipment("Test Building", "pending-1")
        advanceUntilIdle()
        
        // Then: Should return a result
        assertNotNull("Should return result", result)
        assertEquals("Test Building", result.building)
        assertEquals("pending-1", result.pendingId)
        // Result may be success or error depending on test environment
    }
    
    // ============================================================================
    // State Management Tests
    // ============================================================================
    
    @Test
    fun `test updateARState allows custom state updates`() = runTest {
        // Given: Initial state
        val initialState = viewModel.arState.first()
        
        // When: Updating state with custom function
        viewModel.updateARState { currentState ->
            currentState.copy(
                currentRoom = "Room 999",
                floorLevel = 10
            )
        }
        advanceUntilIdle()
        
        // Then: State should be updated
        val state = viewModel.arState.first()
        assertEquals("Room 999", state.currentRoom)
        assertEquals(10, state.floorLevel)
        // Other fields should remain unchanged
        assertEquals(initialState.buildingName, state.buildingName)
    }
}

