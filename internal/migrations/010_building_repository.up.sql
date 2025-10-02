-- Create building repository tables

-- Building repositories table
CREATE TABLE IF NOT EXISTS building_repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    floors INTEGER NOT NULL DEFAULT 1,
    structure_json JSONB NOT NULL DEFAULT '{}',
    current_version_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Building versions table
CREATE TABLE IF NOT EXISTS building_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    tag VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    author VARCHAR(255) NOT NULL,
    hash VARCHAR(64) NOT NULL,
    parent_id UUID REFERENCES building_versions(id),
    changes_json JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(repository_id, tag)
);

-- IFC files table
CREATE TABLE IF NOT EXISTS ifc_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    version VARCHAR(20) NOT NULL,
    discipline VARCHAR(50) NOT NULL,
    size BIGINT NOT NULL,
    entities INTEGER NOT NULL DEFAULT 0,
    validated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add foreign key constraint for current_version_id
ALTER TABLE building_repositories 
ADD CONSTRAINT fk_building_repositories_current_version 
FOREIGN KEY (current_version_id) REFERENCES building_versions(id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_building_repositories_name ON building_repositories(name);
CREATE INDEX IF NOT EXISTS idx_building_repositories_type ON building_repositories(type);
CREATE INDEX IF NOT EXISTS idx_building_versions_repository_id ON building_versions(repository_id);
CREATE INDEX IF NOT EXISTS idx_building_versions_tag ON building_versions(repository_id, tag);
CREATE INDEX IF NOT EXISTS idx_building_versions_created_at ON building_versions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ifc_files_repository_id ON ifc_files(repository_id);
CREATE INDEX IF NOT EXISTS idx_ifc_files_discipline ON ifc_files(discipline);
CREATE INDEX IF NOT EXISTS idx_ifc_files_validated ON ifc_files(validated);
