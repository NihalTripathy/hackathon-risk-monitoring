-- Migration: Add Onboarding Tour Completion Tracking
-- Adds completed_tours field to user_preferences table to track which tours users have completed

-- Add completed_tours JSONB field to store list of completed tour IDs
ALTER TABLE user_preferences 
ADD COLUMN IF NOT EXISTS completed_tours JSONB DEFAULT '[]'::jsonb;

-- Create index for efficient queries on completed_tours
CREATE INDEX IF NOT EXISTS idx_user_preferences_completed_tours 
ON user_preferences USING GIN (completed_tours);

-- Add comment for documentation
COMMENT ON COLUMN user_preferences.completed_tours IS 'Array of completed onboarding tour IDs (e.g., ["dashboard", "forecast", "risks"])';

