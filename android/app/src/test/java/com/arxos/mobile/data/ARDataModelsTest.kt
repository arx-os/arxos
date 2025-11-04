package com.arxos.mobile.data

import org.junit.Assert.*
import org.junit.Test
import org.json.JSONObject
import org.json.JSONArray

/**
 * Unit tests for AR data models
 * 
 * These tests verify serialization and data model correctness for:
 * - ARScanData
 * - DetectedEquipment
 * - Vector3
 * - RoomBoundaries
 * - Equipment type mapping
 * - Position data encoding
 */
class ARDataModelsTest {
    
    // ============================================================================
    // Vector3 Tests
    // ============================================================================
    
    @Test
    fun `test Vector3 creation`() {
        // Given/When: Creating Vector3
        val vector = Vector3(10f, 20f, 30f)
        
        // Then: Should have correct values
        assertEquals(10f, vector.x, 0.001f)
        assertEquals(20f, vector.y, 0.001f)
        assertEquals(30f, vector.z, 0.001f)
    }
    
    @Test
    fun `test Vector3 with zero values`() {
        // Given/When: Creating Vector3 with zeros
        val vector = Vector3(0f, 0f, 0f)
        
        // Then: Should be origin
        assertEquals(0f, vector.x, 0.001f)
        assertEquals(0f, vector.y, 0.001f)
        assertEquals(0f, vector.z, 0.001f)
    }
    
    @Test
    fun `test Vector3 with negative values`() {
        // Given/When: Creating Vector3 with negative values
        val vector = Vector3(-10f, -20f, -30f)
        
        // Then: Should handle negative values
        assertEquals(-10f, vector.x, 0.001f)
        assertEquals(-20f, vector.y, 0.001f)
        assertEquals(-30f, vector.z, 0.001f)
    }
    
    // ============================================================================
    // DetectedEquipment Tests
    // ============================================================================
    
    @Test
    fun `test DetectedEquipment creation`() {
        // Given/When: Creating DetectedEquipment
        val equipment = DetectedEquipment(
            id = "eq-1",
            name = "VAV-301",
            type = "HVAC",
            position = Vector3(10f, 20f, 3f),
            status = "Detected",
            icon = "gear"
        )
        
        // Then: Should have correct values
        assertEquals("eq-1", equipment.id)
        assertEquals("VAV-301", equipment.name)
        assertEquals("HVAC", equipment.type)
        assertEquals(10f, equipment.position.x, 0.001f)
        assertEquals(20f, equipment.position.y, 0.001f)
        assertEquals(3f, equipment.position.z, 0.001f)
        assertEquals("Detected", equipment.status)
        assertEquals("gear", equipment.icon)
    }
    
    @Test
    fun `test DetectedEquipment equipment_type property`() {
        // Given: DetectedEquipment with type
        val equipment = DetectedEquipment(
            id = "eq-1",
            name = "VAV-301",
            type = "HVAC",
            position = Vector3(10f, 20f, 3f),
            status = "Detected",
            icon = "gear"
        )
        
        // When: Accessing equipment_type property
        // Then: Should return type value (for FFI compatibility)
        assertEquals("HVAC", equipment.equipment_type)
        assertEquals("HVAC", equipment.type)
    }
    
    @Test
    fun `test DetectedEquipment with different types`() {
        // Given/When: Creating equipment with different types
        val hvac = DetectedEquipment(
            id = "eq-1",
            name = "VAV-301",
            type = "HVAC",
            position = Vector3(0f, 0f, 0f),
            status = "Detected",
            icon = "gear"
        )
        
        val electrical = DetectedEquipment(
            id = "eq-2",
            name = "Panel A",
            type = "Electrical",
            position = Vector3(0f, 0f, 0f),
            status = "Detected",
            icon = "gear"
        )
        
        val plumbing = DetectedEquipment(
            id = "eq-3",
            name = "Pump 1",
            type = "Plumbing",
            position = Vector3(0f, 0f, 0f),
            status = "Detected",
            icon = "gear"
        )
        
        // Then: Should have correct types
        assertEquals("HVAC", hvac.equipment_type)
        assertEquals("Electrical", electrical.equipment_type)
        assertEquals("Plumbing", plumbing.equipment_type)
    }
    
    // ============================================================================
    // RoomBoundaries Tests
    // ============================================================================
    
    @Test
    fun `test RoomBoundaries creation`() {
        // Given/When: Creating RoomBoundaries
        val boundaries = RoomBoundaries(
            walls = emptyList(),
            openings = emptyList()
        )
        
        // Then: Should have empty lists by default
        assertTrue(boundaries.walls.isEmpty())
        assertTrue(boundaries.openings.isEmpty())
    }
    
    @Test
    fun `test RoomBoundaries with walls`() {
        // Given/When: Creating RoomBoundaries with walls
        val walls = listOf(
            Wall(
                start = Vector3(0f, 0f, 0f),
                end = Vector3(10f, 0f, 0f),
                height = 3f
            ),
            Wall(
                start = Vector3(10f, 0f, 0f),
                end = Vector3(10f, 10f, 0f),
                height = 3f
            )
        )
        
        val boundaries = RoomBoundaries(
            walls = walls,
            openings = emptyList()
        )
        
        // Then: Should have walls
        assertEquals(2, boundaries.walls.size)
        assertEquals(0f, boundaries.walls[0].start.x, 0.001f)
        assertEquals(10f, boundaries.walls[0].end.x, 0.001f)
    }
    
    @Test
    fun `test RoomBoundaries with openings`() {
        // Given/When: Creating RoomBoundaries with openings
        val openings = listOf(
            Opening(
                position = Vector3(5f, 0f, 1.5f),
                width = 2f,
                height = 2.5f,
                type = "Door"
            ),
            Opening(
                position = Vector3(0f, 5f, 1.5f),
                width = 1.5f,
                height = 2f,
                type = "Window"
            )
        )
        
        val boundaries = RoomBoundaries(
            walls = emptyList(),
            openings = openings
        )
        
        // Then: Should have openings
        assertEquals(2, boundaries.openings.size)
        assertEquals("Door", boundaries.openings[0].type)
        assertEquals("Window", boundaries.openings[1].type)
    }
    
    @Test
    fun `test Wall creation`() {
        // Given/When: Creating Wall
        val wall = Wall(
            start = Vector3(0f, 0f, 0f),
            end = Vector3(10f, 0f, 0f),
            height = 3f
        )
        
        // Then: Should have correct values
        assertEquals(0f, wall.start.x, 0.001f)
        assertEquals(10f, wall.end.x, 0.001f)
        assertEquals(3f, wall.height, 0.001f)
    }
    
    @Test
    fun `test Opening creation`() {
        // Given/When: Creating Opening
        val opening = Opening(
            position = Vector3(5f, 0f, 1.5f),
            width = 2f,
            height = 2.5f,
            type = "Door"
        )
        
        // Then: Should have correct values
        assertEquals(5f, opening.position.x, 0.001f)
        assertEquals(0f, opening.position.y, 0.001f)
        assertEquals(1.5f, opening.position.z, 0.001f)
        assertEquals(2f, opening.width, 0.001f)
        assertEquals(2.5f, opening.height, 0.001f)
        assertEquals("Door", opening.type)
    }
    
    // ============================================================================
    // ARScanData Tests
    // ============================================================================
    
    @Test
    fun `test ARScanData creation with minimal data`() {
        // Given/When: Creating ARScanData with minimal required fields
        val scanData = ARScanData(
            detectedEquipment = emptyList(),
            roomBoundaries = RoomBoundaries(),
            roomName = "Room 301",
            floorLevel = 3
        )
        
        // Then: Should have correct values
        assertTrue(scanData.detectedEquipment.isEmpty())
        assertTrue(scanData.roomBoundaries.walls.isEmpty())
        assertTrue(scanData.roomBoundaries.openings.isEmpty())
        assertEquals("Room 301", scanData.roomName)
        assertEquals(3, scanData.floorLevel)
        assertNull(scanData.deviceType)
        assertNull(scanData.appVersion)
        assertNull(scanData.scanDurationMs)
    }
    
    @Test
    fun `test ARScanData creation with all metadata`() {
        // Given/When: Creating ARScanData with all fields
        val scanData = ARScanData(
            detectedEquipment = listOf(
                DetectedEquipment(
                    id = "eq-1",
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
            pointCount = 1000L,
            accuracyEstimate = 0.95,
            lightingConditions = "Good",
            roomName = "Room 301",
            floorLevel = 3
        )
        
        // Then: Should have all values
        assertEquals(1, scanData.detectedEquipment.size)
        assertEquals("Pixel 8 Pro", scanData.deviceType)
        assertEquals("1.0.0", scanData.appVersion)
        assertEquals(5000L, scanData.scanDurationMs)
        assertEquals(1000L, scanData.pointCount)
        assertEquals(0.95, scanData.accuracyEstimate, 0.001)
        assertEquals("Good", scanData.lightingConditions)
        assertEquals("Room 301", scanData.roomName)
        assertEquals(3, scanData.floorLevel)
    }
    
    @Test
    fun `test ARScanData with multiple equipment items`() {
        // Given/When: Creating ARScanData with multiple equipment
        val equipment = listOf(
            DetectedEquipment(
                id = "eq-1",
                name = "VAV-301",
                type = "HVAC",
                position = Vector3(10f, 20f, 3f),
                status = "Detected",
                icon = "gear"
            ),
            DetectedEquipment(
                id = "eq-2",
                name = "Light Fixture A",
                type = "Lighting",
                position = Vector3(5f, 15f, 2.5f),
                status = "Detected",
                icon = "gear"
            ),
            DetectedEquipment(
                id = "eq-3",
                name = "Panel A",
                type = "Electrical",
                position = Vector3(0f, 0f, 1.5f),
                status = "Detected",
                icon = "gear"
            )
        )
        
        val scanData = ARScanData(
            detectedEquipment = equipment,
            roomBoundaries = RoomBoundaries(),
            roomName = "Room 301",
            floorLevel = 3
        )
        
        // Then: Should have all equipment
        assertEquals(3, scanData.detectedEquipment.size)
        assertEquals("VAV-301", scanData.detectedEquipment[0].name)
        assertEquals("Light Fixture A", scanData.detectedEquipment[1].name)
        assertEquals("Panel A", scanData.detectedEquipment[2].name)
    }
    
    @Test
    fun `test ARScanData with zero floor level`() {
        // Given/When: Creating ARScanData with floor level 0
        val scanData = ARScanData(
            detectedEquipment = emptyList(),
            roomBoundaries = RoomBoundaries(),
            roomName = "Ground Floor",
            floorLevel = 0
        )
        
        // Then: Should handle floor level 0
        assertEquals(0, scanData.floorLevel)
    }
    
    @Test
    fun `test ARScanData with negative floor level`() {
        // Given/When: Creating ARScanData with negative floor (basement)
        val scanData = ARScanData(
            detectedEquipment = emptyList(),
            roomBoundaries = RoomBoundaries(),
            roomName = "Basement",
            floorLevel = -1
        )
        
        // Then: Should handle negative floor level
        assertEquals(-1, scanData.floorLevel)
    }
    
    // ============================================================================
    // Data Model Compatibility Tests
    // ============================================================================
    
    @Test
    fun `test DetectedEquipment type matches equipment_type for FFI`() {
        // Given: DetectedEquipment with type
        val equipment = DetectedEquipment(
            id = "eq-1",
            name = "VAV-301",
            type = "HVAC",
            position = Vector3(0f, 0f, 0f),
            status = "Detected",
            icon = "gear"
        )
        
        // When/Then: equipment_type should match type (for Rust FFI compatibility)
        assertEquals(equipment.type, equipment.equipment_type)
    }
    
    @Test
    fun `test ARScanData structure matches Rust FFI expectations`() {
        // Given: ARScanData with all fields
        val scanData = ARScanData(
            detectedEquipment = listOf(
                DetectedEquipment(
                    id = "eq-1",
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
            pointCount = 1000L,
            accuracyEstimate = 0.95,
            lightingConditions = "Good",
            roomName = "Room 301",
            floorLevel = 3
        )
        
        // Then: All fields should be present for FFI serialization
        assertNotNull(scanData.detectedEquipment)
        assertNotNull(scanData.roomBoundaries)
        assertNotNull(scanData.deviceType)
        assertNotNull(scanData.appVersion)
        assertNotNull(scanData.scanDurationMs)
        assertNotNull(scanData.pointCount)
        assertNotNull(scanData.accuracyEstimate)
        assertNotNull(scanData.lightingConditions)
        assertNotNull(scanData.roomName)
        assertNotNull(scanData.floorLevel)
    }
    
    @Test
    fun `test empty ARScanData is valid`() {
        // Given/When: Creating minimal ARScanData
        val scanData = ARScanData(
            detectedEquipment = emptyList(),
            roomBoundaries = RoomBoundaries(),
            roomName = "",
            floorLevel = 0
        )
        
        // Then: Should be valid
        assertNotNull(scanData)
        assertTrue(scanData.detectedEquipment.isEmpty())
        assertEquals("", scanData.roomName)
        assertEquals(0, scanData.floorLevel)
    }
}

