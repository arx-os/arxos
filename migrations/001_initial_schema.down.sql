-- ArxOS Initial Database Schema Rollback
-- Version: 001
-- Description: Drop all tables created in initial schema

-- Drop tables in reverse order of dependencies
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS api_keys;
DROP TABLE IF EXISTS maintenance_records;
DROP TABLE IF EXISTS alarms;
DROP TABLE IF EXISTS timeseries_data;
DROP TABLE IF EXISTS points;
DROP TABLE IF EXISTS equipment;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS zones;
DROP TABLE IF EXISTS floors;
DROP TABLE IF EXISTS buildings;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS organizations;