-- Migration: Add file_hash column to projects table for duplicate detection
-- This migration adds support for detecting duplicate CSV uploads

-- Add file_hash column (nullable for backward compatibility with existing projects)
ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64);

-- Create index for fast duplicate lookup (scoped to user_id)
CREATE INDEX IF NOT EXISTS idx_projects_user_hash 
ON projects(user_id, file_hash) 
WHERE file_hash IS NOT NULL;

-- Add comment to column
COMMENT ON COLUMN projects.file_hash IS 'SHA256 hash of uploaded CSV file content for duplicate detection';

