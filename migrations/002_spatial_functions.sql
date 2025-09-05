-- Spatial helper functions for ArxObject queries
-- Pure SQLite implementation using coordinate columns and indexes

-- View for objects with calculated real-world positions
CREATE VIEW IF NOT EXISTS arxobjects_spatial AS
SELECT 
    a.*,
    b.name as building_name,
    r.name as room_name,
    r.room_number,
    -- Convert mm to meters for display
    CAST(a.x AS REAL) / 1000.0 as x_meters,
    CAST(a.y AS REAL) / 1000.0 as y_meters,
    CAST(a.z AS REAL) / 1000.0 as z_meters,
    -- Calculate distance from origin
    SQRT(a.x * a.x + a.y * a.y + a.z * a.z) / 1000.0 as distance_from_origin_meters
FROM arxobjects a
JOIN buildings b ON a.building_id = b.id
LEFT JOIN rooms r ON a.room_id = r.id;

-- View for room utilization
CREATE VIEW IF NOT EXISTS room_utilization AS
SELECT 
    r.id,
    r.building_id,
    r.name,
    r.room_number,
    r.floor_number,
    r.area_sqm,
    COUNT(a.id) as object_count,
    COUNT(CASE WHEN a.object_type BETWEEN 0x10 AND 0x1F THEN 1 END) as electrical_count,
    COUNT(CASE WHEN a.object_type BETWEEN 0x20 AND 0x2F THEN 1 END) as hvac_count,
    COUNT(CASE WHEN a.object_type BETWEEN 0x30 AND 0x3F THEN 1 END) as sensor_count,
    COUNT(CASE WHEN a.validation_status = 'verified' THEN 1 END) as verified_count,
    CASE 
        WHEN COUNT(a.id) > 0 
        THEN CAST(COUNT(CASE WHEN a.validation_status = 'verified' THEN 1 END) AS REAL) / COUNT(a.id) * 100
        ELSE 0 
    END as verification_percentage
FROM rooms r
LEFT JOIN arxobjects a ON r.id = a.room_id
GROUP BY r.id;

-- View for building completion status
CREATE VIEW IF NOT EXISTS building_completion AS
SELECT 
    b.id,
    b.name,
    b.validation_status,
    COUNT(DISTINCT r.id) as total_rooms,
    COUNT(DISTINCT a.room_id) as mapped_rooms,
    COUNT(a.id) as total_objects,
    COUNT(CASE WHEN a.validation_status = 'verified' THEN 1 END) as verified_objects,
    CASE 
        WHEN COUNT(DISTINCT r.id) > 0 
        THEN CAST(COUNT(DISTINCT a.room_id) AS REAL) / COUNT(DISTINCT r.id) * 100
        ELSE 0 
    END as room_coverage_percentage,
    CASE 
        WHEN COUNT(a.id) > 0 
        THEN CAST(COUNT(CASE WHEN a.validation_status = 'verified' THEN 1 END) AS REAL) / COUNT(a.id) * 100
        ELSE 0 
    END as object_verification_percentage,
    MAX(a.last_verified) as last_activity
FROM buildings b
LEFT JOIN rooms r ON b.id = r.building_id
LEFT JOIN arxobjects a ON b.id = a.building_id
GROUP BY b.id;

-- View for BILT leaderboard
CREATE VIEW IF NOT EXISTS bilt_leaderboard AS
SELECT 
    b.user_id,
    b.total_earned,
    b.current_balance,
    COUNT(DISTINCT DATE(t.created_at)) as active_days,
    COUNT(DISTINCT t.arxobject_id) as objects_marked,
    AVG(t.points_earned) as avg_points_per_action,
    MAX(t.created_at) as last_activity
FROM bilt_balances b
LEFT JOIN bilt_transactions t ON b.user_id = t.user_id
GROUP BY b.user_id
ORDER BY b.total_earned DESC;

-- Helper function to find objects within a bounding box (SQLite compatible)
-- Usage: SELECT * FROM arxobjects WHERE id IN (SELECT * FROM objects_in_bbox(building_id, min_x, min_y, min_z, max_x, max_y, max_z))
CREATE VIEW IF NOT EXISTS objects_in_bbox_helper AS
SELECT 
    id,
    building_id,
    x, y, z
FROM arxobjects;

-- View for compliance critical objects
CREATE VIEW IF NOT EXISTS compliance_critical_objects AS
SELECT 
    a.*,
    CASE 
        WHEN a.object_type = 0x15 THEN 'Emergency Light'
        WHEN a.object_type = 0x36 THEN 'Smoke Detector'
        WHEN a.object_type = 0x41 THEN 'Fire Extinguisher'
        WHEN a.object_type = 0x42 THEN 'Sprinkler Head'
        WHEN a.object_type = 0x51 THEN 'Emergency Exit'
        WHEN a.object_type = 0x52 THEN 'Exit Sign'
        ELSE 'Other Safety Equipment'
    END as safety_type,
    CASE 
        WHEN a.validation_status = 'verified' AND 
             (julianday('now') - julianday(a.last_verified)) <= 30 
        THEN 'Current'
        WHEN a.validation_status = 'verified' 
        THEN 'Needs Revalidation'
        ELSE 'Unverified'
    END as compliance_status
FROM arxobjects a
WHERE a.object_type IN (
    0x15,  -- Emergency Light
    0x36,  -- Smoke Detector  
    0x41,  -- Fire Extinguisher
    0x42,  -- Sprinkler Head
    0x51,  -- Emergency Exit
    0x52   -- Exit Sign
);

-- View for progressive detail status
CREATE VIEW IF NOT EXISTS object_detail_status AS
SELECT 
    a.id,
    a.object_type,
    a.building_id,
    COUNT(DISTINCT d.chunk_type) as detail_types,
    COUNT(d.id) as total_chunks,
    GROUP_CONCAT(DISTINCT 
        CASE d.chunk_type
            WHEN 0x80 THEN 'Material'
            WHEN 0x90 THEN 'History'
            WHEN 0xA0 THEN 'Connections'
            WHEN 0xB0 THEN 'Simulation'
            WHEN 0xC0 THEN 'Predictive'
            ELSE 'Other'
        END
    ) as available_details,
    CASE 
        WHEN COUNT(d.id) = 0 THEN 'Basic'
        WHEN COUNT(d.id) < 10 THEN 'Enhanced'
        WHEN COUNT(d.id) < 50 THEN 'Detailed'
        ELSE 'Complete'
    END as detail_level
FROM arxobjects a
LEFT JOIN detail_chunks d ON a.id = d.arxobject_id
GROUP BY a.id;