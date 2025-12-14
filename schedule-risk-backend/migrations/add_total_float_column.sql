-- Migration: Add total_float and schedule analysis fields to activities table
-- Date: 2025-01-XX
-- Description: Adds Total_Float column and schedule analysis fields (ES, EF, LS, LF) 
--              to preserve float values from CSV imports

-- Add schedule analysis fields if they don't exist
ALTER TABLE activities 
ADD COLUMN IF NOT EXISTS early_start VARCHAR(255) NULL,
ADD COLUMN IF NOT EXISTS early_finish VARCHAR(255) NULL,
ADD COLUMN IF NOT EXISTS late_start VARCHAR(255) NULL,
ADD COLUMN IF NOT EXISTS late_finish VARCHAR(255) NULL,
ADD COLUMN IF NOT EXISTS total_float FLOAT NULL;

-- Add index on total_float for faster queries (optional, but helpful for filtering)
CREATE INDEX IF NOT EXISTS idx_activities_total_float ON activities(total_float);

-- Update existing records: set total_float to 0.0 for activities on critical path
-- (This is a reasonable default - actual values will come from CSV on next import)
UPDATE activities 
SET total_float = 0.0 
WHERE on_critical_path = TRUE AND total_float IS NULL;

