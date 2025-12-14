-- Migration: Add analysis_date_mode and csv_reference_date to projects table
-- These columns support the "as of date" feature for CSV-based analysis

-- Add analysis_date_mode column (stores user preference: 'today' or 'csv_date')
ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS analysis_date_mode VARCHAR(20) DEFAULT 'today';

-- Add csv_reference_date column (stores auto-detected date from CSV)
ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS csv_reference_date DATE NULL;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_projects_analysis_date_mode ON projects(analysis_date_mode);

-- Add comment for documentation
COMMENT ON COLUMN projects.analysis_date_mode IS 'Analysis date mode: "today" (use current date) or "csv_date" (use CSV reference date)';
COMMENT ON COLUMN projects.csv_reference_date IS 'Auto-detected reference date from CSV data (latest actual_start/actual_finish date)';
