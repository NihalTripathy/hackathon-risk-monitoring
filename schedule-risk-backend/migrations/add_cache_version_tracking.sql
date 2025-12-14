-- Migration: Add data_hash column to cache tables
-- This migration adds automatic cache invalidation when CSV data changes
-- Note: logic_version column is optional (not used in simplified solution)

-- Add data_hash column to forecast_cache (REQUIRED - used for CSV change detection)
ALTER TABLE forecast_cache 
ADD COLUMN IF NOT EXISTS data_hash VARCHAR(16);

-- Add data_hash column to risks_cache (REQUIRED - used for CSV change detection)
ALTER TABLE risks_cache 
ADD COLUMN IF NOT EXISTS data_hash VARCHAR(16);

-- Add data_hash column to anomalies_cache (REQUIRED - used for CSV change detection)
ALTER TABLE anomalies_cache 
ADD COLUMN IF NOT EXISTS data_hash VARCHAR(16);

-- Optional: Add logic_version column (not used, but won't hurt if it exists)
ALTER TABLE forecast_cache 
ADD COLUMN IF NOT EXISTS logic_version VARCHAR(16);

ALTER TABLE risks_cache 
ADD COLUMN IF NOT EXISTS logic_version VARCHAR(16);

ALTER TABLE anomalies_cache 
ADD COLUMN IF NOT EXISTS logic_version VARCHAR(16);

-- Add comments
COMMENT ON COLUMN forecast_cache.data_hash IS 'Hash of activity data when computed - used for automatic cache invalidation on CSV data changes';
COMMENT ON COLUMN risks_cache.data_hash IS 'Hash of activity data when computed - used for automatic cache invalidation on CSV data changes';
COMMENT ON COLUMN anomalies_cache.data_hash IS 'Hash of activity data when computed - used for automatic cache invalidation on CSV data changes';

