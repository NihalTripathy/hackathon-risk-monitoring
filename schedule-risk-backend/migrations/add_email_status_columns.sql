-- Migration: Add email status tracking columns to notification_preferences table
-- Date: 2025-01-15
-- Description: Adds columns to track email notification success/failure status

-- Add email status tracking columns
ALTER TABLE notification_preferences
ADD COLUMN IF NOT EXISTS last_email_sent TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_email_error TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS email_error_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS email_error_message TEXT;

-- Update existing rows to have default values
UPDATE notification_preferences
SET email_error_count = 0
WHERE email_error_count IS NULL;

-- Add comment to columns for documentation
COMMENT ON COLUMN notification_preferences.last_email_sent IS 'Timestamp of last successful email notification';
COMMENT ON COLUMN notification_preferences.last_email_error IS 'Timestamp of last email notification failure';
COMMENT ON COLUMN notification_preferences.email_error_count IS 'Count of consecutive email failures';
COMMENT ON COLUMN notification_preferences.email_error_message IS 'Last error message from email sending attempt';

