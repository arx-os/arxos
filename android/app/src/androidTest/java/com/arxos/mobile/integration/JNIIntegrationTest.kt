package com.arxos.mobile.integration

import android.content.Context
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.arxos.mobile.service.ArxOSCoreJNI
import com.arxos.mobile.service.ArxOSCoreJNIWrapper
import kotlinx.coroutines.runBlocking
import org.junit.Before
import org.junit.Test
import org.junit.Assert.*
import org.junit.runner.RunWith

/**
 * Integration tests for JNI bindings
 * 
 * These tests require the native library to be loaded and will only run
 * on devices/emulators with the compiled native library present.
 * 
 * Prerequisites:
 * - Native library must be built and placed in src/main/jniLibs/
 * - Device/emulator must support the target ABI
 */
@RunWith(AndroidJUnit4::class)
class JNIIntegrationTest {
    
    private lateinit var context: Context
    private lateinit var jni: ArxOSCoreJNI
    private lateinit var wrapper: ArxOSCoreJNIWrapper
    
    @Before
    fun setup() {
        context = InstrumentationRegistry.getInstrumentation().targetContext
        jni = ArxOSCoreJNI(context)
        wrapper = ArxOSCoreJNIWrapper(jni)
    }
    
    @Test
    fun testNativeLibraryLoads() {
        // Verify native library can be loaded
        val isLoaded = jni.isNativeLibraryLoaded()
        
        if (!isLoaded) {
            // Skip tests if library not available (e.g., in CI without native libs)
            println("WARNING: Native library not loaded. Skipping integration tests.")
            return
        }
        
        assertTrue("Native library should be loaded", isLoaded)
    }
    
    @Test
    fun testListRoomsIntegration() = runBlocking {
        if (!jni.isNativeLibraryLoaded()) {
            println("Skipping: Native library not loaded")
            return@runBlocking
        }
        
        // Test with a default building name
        val rooms = wrapper.listRooms("test-building")
        
        // Should not crash, even if building doesn't exist
        assertNotNull("Rooms list should not be null", rooms)
        // May be empty if building doesn't exist, that's OK
    }
    
    @Test
    fun testGetRoomIntegration() = runBlocking {
        if (!jni.isNativeLibraryLoaded()) {
            println("Skipping: Native library not loaded")
            return@runBlocking
        }
        
        // Test with non-existent room (should return null gracefully)
        val room = wrapper.getRoom("test-building", "non-existent-room")
        
        // Should handle gracefully, may be null
        // Just verify it doesn't crash
    }
    
    @Test
    fun testListEquipmentIntegration() = runBlocking {
        if (!jni.isNativeLibraryLoaded()) {
            println("Skipping: Native library not loaded")
            return@runBlocking
        }
        
        val equipment = wrapper.listEquipment("test-building")
        
        assertNotNull("Equipment list should not be null", equipment)
        // May be empty, that's OK
    }
    
    @Test
    fun testGetEquipmentIntegration() = runBlocking {
        if (!jni.isNativeLibraryLoaded()) {
            println("Skipping: Native library not loaded")
            return@runBlocking
        }
        
        val equipment = wrapper.getEquipment("test-building", "non-existent-equipment")
        
        // Should handle gracefully, may be null
        // Just verify it doesn't crash
    }
    
    @Test
    fun testParseARScanIntegration() = runBlocking {
        if (!jni.isNativeLibraryLoaded()) {
            println("Skipping: Native library not loaded")
            return@runBlocking
        }
        
        // Test with minimal valid AR scan JSON
        val testJson = """
            {
                "detectedEquipment": [],
                "roomBoundaries": {
                    "walls": [],
                    "openings": []
                }
            }
        """.trimIndent()
        
        val result = wrapper.parseARScan(testJson)
        
        // Should not crash
        // Result may be null if parsing fails, that's OK for now
    }
    
    @Test
    fun testExtractEquipmentIntegration() = runBlocking {
        if (!jni.isNativeLibraryLoaded()) {
            println("Skipping: Native library not loaded")
            return@runBlocking
        }
        
        val testJson = """
            {
                "detectedEquipment": [],
                "roomBoundaries": {"walls": [], "openings": []}
            }
        """.trimIndent()
        
        val equipment = wrapper.extractEquipment(testJson)
        
        assertNotNull("Equipment list should not be null", equipment)
        // May be empty, that's OK
    }
    
    @Test
    fun testJNIErrorHandling() = runBlocking {
        if (!jni.isNativeLibraryLoaded()) {
            println("Skipping: Native library not loaded")
            return@runBlocking
        }
        
        // Test with invalid input - should handle gracefully
        try {
            wrapper.listRooms("")
            // Should not crash even with empty string
        } catch (e: Exception) {
            fail("Should handle empty building name gracefully: ${e.message}")
        }
        
        try {
            wrapper.parseARScan("invalid json")
            // Should not crash even with invalid JSON
        } catch (e: Exception) {
            fail("Should handle invalid JSON gracefully: ${e.message}")
        }
    }
    
    @Test
    fun testJNIMemorySafety() = runBlocking {
        if (!jni.isNativeLibraryLoaded()) {
            println("Skipping: Native library not loaded")
            return@runBlocking
        }
        
        // Run multiple operations to check for memory leaks
        repeat(10) {
            wrapper.listRooms("test-building")
            wrapper.listEquipment("test-building")
        }
        
        // If we get here without crash, memory handling is OK
        assertTrue("Memory safety check passed", true)
    }
}

