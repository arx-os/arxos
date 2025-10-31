package com.arxos.mobile.service

import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.mockito.Mock
import org.mockito.Mockito.*
import org.mockito.MockitoAnnotations
import kotlinx.coroutines.runBlocking

/**
 * Unit tests for ArxOSCoreJNIWrapper
 * 
 * These tests mock the JNI layer to test JSON parsing and error handling
 * without requiring the native library to be loaded.
 */
class ArxOSCoreJNIWrapperTest {
    
    @Mock
    private lateinit var mockJNI: ArxOSCoreJNI
    
    private lateinit var wrapper: ArxOSCoreJNIWrapper
    
    @Before
    fun setup() {
        MockitoAnnotations.openMocks(this)
        `when`(mockJNI.isNativeLibraryLoaded()).thenReturn(true)
        wrapper = ArxOSCoreJNIWrapper(mockJNI)
    }
    
    @Test
    fun `test listRooms with valid JSON`() = runBlocking {
        // Given: Valid JSON response from JNI
        val jsonResponse = """
            [
                {
                    "id": "room-1",
                    "name": "Conference Room A",
                    "room_type": "conference",
                    "position": {"x": 10.0, "y": 20.0, "z": 0.0, "coordinate_system": "World"},
                    "properties": {"floor": "2", "capacity": "12"}
                },
                {
                    "id": "room-2",
                    "name": "Office 101",
                    "room_type": "office",
                    "position": {"x": 15.0, "y": 25.0, "z": 0.0, "coordinate_system": "World"},
                    "properties": {"floor": "1", "capacity": "1"}
                }
            ]
        """.trimIndent()
        
        `when`(mockJNI.nativeListRooms("test-building")).thenReturn(jsonResponse)
        
        // When: Calling listRooms
        val rooms = wrapper.listRooms("test-building")
        
        // Then: Should parse correctly
        assertEquals(2, rooms.size)
        assertEquals("room-1", rooms[0].id)
        assertEquals("Conference Room A", rooms[0].name)
        assertEquals("2", rooms[0].floor)
        assertEquals("10.0,20.0,0.0", rooms[0].coordinates)
        
        assertEquals("room-2", rooms[1].id)
        assertEquals("Office 101", rooms[1].name)
        assertEquals("1", rooms[1].floor)
    }
    
    @Test
    fun `test listRooms with error JSON`() = runBlocking {
        // Given: Error response from JNI
        val errorJson = """{"error": "Building not found"}"""
        `when`(mockJNI.nativeListRooms("invalid")).thenReturn(errorJson)
        
        // When: Calling listRooms
        val rooms = wrapper.listRooms("invalid")
        
        // Then: Should return empty list
        assertTrue(rooms.isEmpty())
    }
    
    @Test
    fun `test listRooms when library not loaded`() = runBlocking {
        // Given: Library not loaded
        `when`(mockJNI.isNativeLibraryLoaded()).thenReturn(false)
        val wrapper = ArxOSCoreJNIWrapper(mockJNI)
        
        // When: Calling listRooms
        val rooms = wrapper.listRooms("test-building")
        
        // Then: Should return empty list
        assertTrue(rooms.isEmpty())
        verify(mockJNI, never()).nativeListRooms(anyString())
    }
    
    @Test
    fun `test getRoom with valid JSON`() = runBlocking {
        // Given: Valid JSON response
        val jsonResponse = """
            {
                "id": "room-1",
                "name": "Conference Room A",
                "room_type": "conference",
                "position": {"x": 10.0, "y": 20.0, "z": 0.0, "coordinate_system": "World"},
                "properties": {"floor": "2", "capacity": "12"}
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeGetRoom("test-building", "room-1")).thenReturn(jsonResponse)
        
        // When: Calling getRoom
        val room = wrapper.getRoom("test-building", "room-1")
        
        // Then: Should parse correctly
        assertNotNull(room)
        assertEquals("room-1", room!!.id)
        assertEquals("Conference Room A", room.name)
        assertEquals("2", room.floor)
    }
    
    @Test
    fun `test getRoom with not found error`() = runBlocking {
        // Given: Not found error
        val errorJson = """{"error": "Room not found"}"""
        `when`(mockJNI.nativeGetRoom("test-building", "invalid")).thenReturn(errorJson)
        
        // When: Calling getRoom
        val room = wrapper.getRoom("test-building", "invalid")
        
        // Then: Should return null
        assertNull(room)
    }
    
    @Test
    fun `test listEquipment with valid JSON`() = runBlocking {
        // Given: Valid JSON response
        val jsonResponse = """
            [
                {
                    "id": "eq-1",
                    "name": "HVAC Unit 1",
                    "equipment_type": "HVAC",
                    "status": "operational",
                    "position": {"x": 5.0, "y": 10.0, "z": 2.0, "coordinate_system": "World"},
                    "properties": {"lastMaintenance": "2024-01-15", "model": "AC-5000"}
                }
            ]
        """.trimIndent()
        
        `when`(mockJNI.nativeListEquipment("test-building")).thenReturn(jsonResponse)
        
        // When: Calling listEquipment
        val equipment = wrapper.listEquipment("test-building")
        
        // Then: Should parse correctly
        assertEquals(1, equipment.size)
        assertEquals("eq-1", equipment[0].id)
        assertEquals("HVAC Unit 1", equipment[0].name)
        assertEquals("HVAC", equipment[0].type)
        assertEquals("operational", equipment[0].status)
        assertEquals("5.0,10.0,2.0", equipment[0].location)
        assertEquals("2024-01-15", equipment[0].lastMaintenance)
    }
    
    @Test
    fun `test getEquipment with valid JSON`() = runBlocking {
        // Given: Valid JSON response
        val jsonResponse = """
            {
                "id": "eq-1",
                "name": "HVAC Unit 1",
                "equipment_type": "HVAC",
                "status": "operational",
                "position": {"x": 5.0, "y": 10.0, "z": 2.0, "coordinate_system": "World"},
                "properties": {"lastMaintenance": "2024-01-15"}
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeGetEquipment("test-building", "eq-1")).thenReturn(jsonResponse)
        
        // When: Calling getEquipment
        val equipment = wrapper.getEquipment("test-building", "eq-1")
        
        // Then: Should parse correctly
        assertNotNull(equipment)
        assertEquals("eq-1", equipment!!.id)
        assertEquals("HVAC Unit 1", equipment.name)
        assertEquals("operational", equipment.status)
    }
    
    @Test
    fun `test parseARScan with valid JSON`() = runBlocking {
        // Given: Valid AR scan JSON
        val inputJson = """{"detectedEquipment": [{"name": "AC Unit", "type": "HVAC", "position": {"x": 1.0, "y": 2.0, "z": 3.0}}]}"""
        val outputJson = """
            {
                "detectedEquipment": [
                    {
                        "id": "detected-1",
                        "name": "AC Unit",
                        "type": "HVAC",
                        "position": {"x": 1.0, "y": 2.0, "z": 3.0},
                        "confidence": 0.95,
                        "detectionMethod": "ARCore"
                    }
                ],
                "roomBoundaries": {"walls": [], "openings": []}
            }
        """.trimIndent()
        
        `when`(mockJNI.nativeParseARScan(inputJson)).thenReturn(outputJson)
        
        // When: Calling parseARScan
        val result = wrapper.parseARScan(inputJson)
        
        // Then: Should parse correctly
        assertNotNull(result)
        assertEquals(1, result!!.equipment.size)
        assertEquals("AC Unit", result.equipment[0].name)
        assertEquals("HVAC", result.equipment[0].type)
    }
    
    @Test
    fun `test extractEquipment with valid JSON`() = runBlocking {
        // Given: Valid equipment extraction JSON
        val inputJson = """{"scan": "data"}"""
        val outputJson = """
            [
                {
                    "id": "extracted-1",
                    "name": "Extracted Equipment",
                    "equipment_type": "Electrical",
                    "status": "operational",
                    "position": {"x": 1.0, "y": 2.0, "z": 3.0, "coordinate_system": "World"},
                    "properties": {}
                }
            ]
        """.trimIndent()
        
        `when`(mockJNI.nativeExtractEquipment(inputJson)).thenReturn(outputJson)
        
        // When: Calling extractEquipment
        val equipment = wrapper.extractEquipment(inputJson)
        
        // Then: Should parse correctly
        assertEquals(1, equipment.size)
        assertEquals("extracted-1", equipment[0].id)
        assertEquals("Extracted Equipment", equipment[0].name)
        assertEquals("Electrical", equipment[0].type)
    }
    
    @Test
    fun `test all functions handle empty JSON gracefully`() = runBlocking {
        `when`(mockJNI.nativeListRooms("test")).thenReturn("")
        `when`(mockJNI.nativeGetRoom("test", "room-1")).thenReturn("")
        `when`(mockJNI.nativeListEquipment("test")).thenReturn("")
        `when`(mockJNI.nativeGetEquipment("test", "eq-1")).thenReturn("")
        `when`(mockJNI.nativeParseARScan("{}")).thenReturn("")
        `when`(mockJNI.nativeExtractEquipment("{}")).thenReturn("")
        
        assertTrue(wrapper.listRooms("test").isEmpty())
        assertNull(wrapper.getRoom("test", "room-1"))
        assertTrue(wrapper.listEquipment("test").isEmpty())
        assertNull(wrapper.getEquipment("test", "eq-1"))
        assertNull(wrapper.parseARScan("{}"))
        assertTrue(wrapper.extractEquipment("{}").isEmpty())
    }
    
    @Test
    fun `test all functions handle JSON parse errors gracefully`() = runBlocking {
        `when`(mockJNI.nativeListRooms("test")).thenReturn("invalid json")
        `when`(mockJNI.nativeGetRoom("test", "room-1")).thenReturn("invalid json")
        
        // Should not throw, but return safe defaults
        assertTrue(wrapper.listRooms("test").isEmpty())
        assertNull(wrapper.getRoom("test", "room-1"))
    }
}

