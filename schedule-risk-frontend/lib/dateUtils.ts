/**
 * Date formatting utilities
 * Ensures consistent DD-MM-YYYY format throughout the application
 */

/**
 * Parse a date string in DD-MM-YYYY format or other formats to Date object
 * @param dateStr - Date string in DD-MM-YYYY, ISO format, or other parseable format
 * @returns Date object or null if invalid
 */
function parseDateString(dateStr: string): Date | null {
  // Check if it's already in DD-MM-YYYY format (e.g., "25-01-2025")
  const ddMMyyyyPattern = /^(\d{1,2})-(\d{1,2})-(\d{4})$/
  const match = dateStr.match(ddMMyyyyPattern)
  
  if (match) {
    const day = parseInt(match[1], 10)
    const month = parseInt(match[2], 10) - 1 // JavaScript months are 0-indexed
    const year = parseInt(match[3], 10)
    const dateObj = new Date(year, month, day)
    
    // Validate the date
    if (dateObj.getDate() === day && dateObj.getMonth() === month && dateObj.getFullYear() === year) {
      return dateObj
    }
  }
  
  // Try standard Date parsing for ISO format and other formats
  const dateObj = new Date(dateStr)
  if (!isNaN(dateObj.getTime())) {
    return dateObj
  }
  
  return null
}

/**
 * Format a date string or Date object to DD-MM-YYYY format
 * @param date - Date string (DD-MM-YYYY, ISO format, or any parseable format) or Date object
 * @returns Formatted date string in DD-MM-YYYY format
 */
export function formatDateDDMMYYYY(date: string | Date): string {
  let dateObj: Date | null = null
  
  if (typeof date === 'string') {
    // Try parsing DD-MM-YYYY format first, then fallback to standard parsing
    dateObj = parseDateString(date)
    
    if (!dateObj) {
      console.warn(`Invalid date string: ${date}`)
      return date // Return original string if invalid
    }
  } else {
    dateObj = date
  }
  
  // Format as DD-MM-YYYY
  const day = String(dateObj.getDate()).padStart(2, '0')
  const month = String(dateObj.getMonth() + 1).padStart(2, '0')
  const year = dateObj.getFullYear()
  
  return `${day}-${month}-${year}`
}

/**
 * Format a date string or Date object to DD-MM-YYYY HH:MM format (with time)
 * @param date - Date string (DD-MM-YYYY, ISO format, or any parseable format) or Date object
 * @returns Formatted date string in DD-MM-YYYY HH:MM format
 */
export function formatDateTimeDDMMYYYY(date: string | Date): string {
  let dateObj: Date | null = null
  
  if (typeof date === 'string') {
    // Try parsing DD-MM-YYYY format first, then fallback to standard parsing
    dateObj = parseDateString(date)
    
    if (!dateObj) {
      console.warn(`Invalid date string: ${date}`)
      return date
    }
  } else {
    dateObj = date
  }
  
  const day = String(dateObj.getDate()).padStart(2, '0')
  const month = String(dateObj.getMonth() + 1).padStart(2, '0')
  const year = dateObj.getFullYear()
  const hours = String(dateObj.getHours()).padStart(2, '0')
  const minutes = String(dateObj.getMinutes()).padStart(2, '0')
  
  return `${day}-${month}-${year} ${hours}:${minutes}`
}

