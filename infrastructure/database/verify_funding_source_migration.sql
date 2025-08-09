-- Funding Source Migration Verification Script
-- This script verifies that the funding_source feature has been properly implemented in the database

-- 1. Check if funding_source columns exist
SELECT
    'devices.funding_source' as column_name,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'devices' AND column_name = 'funding_source'
        ) THEN '✅ EXISTS'
        ELSE '❌ MISSING'
    END as status
UNION ALL
SELECT
    'building_assets.funding_source' as column_name,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'building_assets' AND column_name = 'funding_source'
        ) THEN '✅ EXISTS'
        ELSE '❌ MISSING'
    END as status;

-- 2. Check if funding_source indexes exist
SELECT
    'idx_devices_funding_source' as index_name,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE indexname = 'idx_devices_funding_source'
        ) THEN '✅ EXISTS'
        ELSE '❌ MISSING'
    END as status
UNION ALL
SELECT
    'idx_building_assets_funding_source' as index_name,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE indexname = 'idx_building_assets_funding_source'
        ) THEN '✅ EXISTS'
        ELSE '❌ MISSING'
    END as status;

-- 3. Check column data types
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE column_name = 'funding_source'
    AND table_name IN ('devices', 'building_assets')
ORDER BY table_name;

-- 4. Check for existing funding_source data
SELECT
    'devices' as table_name,
    COUNT(*) as total_records,
    COUNT(funding_source) as records_with_funding_source,
    COUNT(CASE WHEN funding_source IS NOT NULL AND funding_source != '' THEN 1 END) as non_empty_funding_source
FROM devices
UNION ALL
SELECT
    'building_assets' as table_name,
    COUNT(*) as total_records,
    COUNT(funding_source) as records_with_funding_source,
    COUNT(CASE WHEN funding_source IS NOT NULL AND funding_source != '' THEN 1 END) as non_empty_funding_source
FROM building_assets;

-- 5. Sample funding_source values
SELECT
    'devices' as table_name,
    funding_source,
    COUNT(*) as count
FROM devices
WHERE funding_source IS NOT NULL AND funding_source != ''
GROUP BY funding_source
ORDER BY count DESC
LIMIT 10;

SELECT
    'building_assets' as table_name,
    funding_source,
    COUNT(*) as count
FROM building_assets
WHERE funding_source IS NOT NULL AND funding_source != ''
GROUP BY funding_source
ORDER BY count DESC
LIMIT 10;

-- 6. Check for any constraints on funding_source columns
SELECT
    tc.table_name,
    tc.column_name,
    tc.constraint_name,
    tc.constraint_type,
    cc.check_clause
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.check_constraints cc
    ON tc.constraint_name = cc.constraint_name
WHERE tc.column_name = 'funding_source'
    AND tc.table_name IN ('devices', 'building_assets');

-- 7. Verify column comments
SELECT
    schemaname,
    tablename,
    attname as column_name,
    col_description(
        (schemaname || '.' || tablename)::regclass,
        attnum
    ) as comment
FROM pg_attribute a
JOIN pg_class c ON a.attrelid = c.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE attname = 'funding_source'
    AND tablename IN ('devices', 'building_assets')
    AND attnum > 0
    AND NOT attisdropped;

-- 8. Test INSERT with funding_source
DO $$
DECLARE
    test_device_id VARCHAR(255);
    test_asset_id VARCHAR(255);
BEGIN
    -- Test inserting device with funding_source
    INSERT INTO devices (
        object_id, name, object_type, type, system, category,
        funding_source, created_by, project_id
    ) VALUES (
        'TEST_DEVICE_' || EXTRACT(EPOCH FROM NOW())::INTEGER,
        'Test Device for Migration Verification',
        'device',
        'receptacle',
        'electrical',
        'electrical',
        'Capital Budget',
        1,
        1
    ) RETURNING object_id INTO test_device_id;

    RAISE NOTICE '✅ Successfully inserted test device with funding_source: %', test_device_id;

    -- Test inserting building asset with funding_source
    INSERT INTO building_assets (
        id, building_id, symbol_id, asset_type, system,
        funding_source, created_by
    ) VALUES (
        'TEST_ASSET_' || EXTRACT(EPOCH FROM NOW())::INTEGER,
        1,
        'receptacle',
        'Electrical',
        'electrical',
        'Operating Budget',
        1
    ) RETURNING id INTO test_asset_id;

    RAISE NOTICE '✅ Successfully inserted test asset with funding_source: %', test_asset_id;

    -- Clean up test data
    DELETE FROM devices WHERE object_id = test_device_id;
    DELETE FROM building_assets WHERE id = test_asset_id;

    RAISE NOTICE '✅ Test data cleaned up successfully';

EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '❌ Error during migration verification: %', SQLERRM;
END $$;

-- 9. Performance check - verify indexes are being used
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*)
FROM devices
WHERE funding_source = 'Capital Budget';

EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*)
FROM building_assets
WHERE funding_source = 'Operating Budget';

-- 10. Summary report
SELECT
    'MIGRATION VERIFICATION SUMMARY' as report_section,
    'All checks completed' as status,
    CURRENT_TIMESTAMP as verification_time;
