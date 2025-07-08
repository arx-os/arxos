-- Add authentication and scheduling fields to cmms_connections
ALTER TABLE cmms_connections
	ADD COLUMN IF NOT EXISTS api_key VARCHAR(255),
	ADD COLUMN IF NOT EXISTS username VARCHAR(255),
	ADD COLUMN IF NOT EXISTS password VARCHAR(255),
	ADD COLUMN IF NOT EXISTS oauth2_client_id VARCHAR(255),
	ADD COLUMN IF NOT EXISTS oauth2_secret VARCHAR(255),
	ADD COLUMN IF NOT EXISTS oauth2_token_url VARCHAR(255),
	ADD COLUMN IF NOT EXISTS oauth2_scope VARCHAR(255),
	ADD COLUMN IF NOT EXISTS sync_interval_min INTEGER DEFAULT 60,
	ADD COLUMN IF NOT EXISTS last_sync_status VARCHAR(50),
	ADD COLUMN IF NOT EXISTS last_sync_error TEXT; 