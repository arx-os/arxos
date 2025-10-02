-- Migration: 011_circuit_tables.down.sql
-- Description: Drop circuit-related tables for CADTUI functionality
-- Author: ArxOS Team
-- Date: 2024

-- Drop triggers first
DROP TRIGGER IF EXISTS update_field_markups_updated_at ON field_markups;
DROP TRIGGER IF EXISTS update_circuit_animations_updated_at ON circuit_animations;
DROP TRIGGER IF EXISTS update_circuits_updated_at ON circuits;

-- Drop function
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS simulation_results;
DROP TABLE IF EXISTS field_markups;
DROP TABLE IF EXISTS circuit_animations;
DROP TABLE IF EXISTS circuit_particles;
DROP TABLE IF EXISTS circuit_connections;
DROP TABLE IF EXISTS circuit_components;
DROP TABLE IF EXISTS circuits;
