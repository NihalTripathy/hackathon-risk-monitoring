import { useState, useCallback } from 'react'
import { reAnalyzeProject } from '@/lib/api'

interface UseReAnalyzeOptions {
  /**
   * Callback function to refresh data after re-analysis completes
   * This will be called when new data is available
   */
  onDataRefresh?: () => Promise<void> | void
  
  /**
   * Custom polling interval in milliseconds (default: 2000ms)
   */
  pollingInterval?: number
  
  /**
   * Maximum number of polling attempts (default: 20)
   * Total max wait time = pollingInterval * maxAttempts
   */
  maxAttempts?: number
  
  /**
   * Whether to automatically refresh data after re-analysis (default: true)
   */
  autoRefresh?: boolean
}

interface UseReAnalyzeReturn {
  /**
   * Function to trigger re-analysis
   */
  handleReAnalyze: () => Promise<void>
  
  /**
   * Whether re-analysis is currently in progress
   */
  reAnalyzing: boolean
  
  /**
   * Error message if re-analysis failed
   */
  error: string | null
  
  /**
   * Clear the error state
   */
  clearError: () => void
}

/**
 * Custom hook for re-analyzing project data
 * 
 * This hook centralizes the re-analysis logic:
 * - Calls the re-analyze API endpoint
 * - Invalidates cache and triggers background recomputation
 * - Polls for results until data is available
 * - Automatically refreshes data when ready
 * 
 * @param projectId - The project ID to re-analyze
 * @param options - Configuration options
 * @returns Re-analyze handler function and state
 * 
 * @example
 * ```tsx
 * const { handleReAnalyze, reAnalyzing, error } = useReAnalyze(projectId, {
 *   onDataRefresh: async () => {
 *     await fetchData()
 *     await fetchAnomalies()
 *   }
 * })
 * ```
 */
export function useReAnalyze(
  projectId: string,
  options: UseReAnalyzeOptions = {}
): UseReAnalyzeReturn {
  const {
    onDataRefresh,
    pollingInterval = 2000,
    maxAttempts = 20,
    autoRefresh = true,
  } = options

  const [reAnalyzing, setReAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const handleReAnalyze = useCallback(async () => {
    try {
      setReAnalyzing(true)
      setError(null)

      // Call re-analyze endpoint (invalidates cache and triggers background recomputation)
      const response = await reAnalyzeProject(projectId)
      console.log('Re-analysis started:', response.message)

      if (!autoRefresh) {
        // If auto-refresh is disabled, just trigger the re-analysis and return
        setReAnalyzing(false)
        return
      }

      // Poll for results - the background task computes and caches results
      // We poll until cache is ready or max attempts reached
      let attempts = 0

      while (attempts < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, pollingInterval))
        attempts++

        try {
          // Try to refresh data - if cache is ready, it will return immediately
          // If not, the API will compute on-demand (which is fine)
          if (onDataRefresh) {
            await onDataRefresh()
          }

          // If refresh succeeded, we have data - stop polling
          setReAnalyzing(false)
          return
        } catch (err) {
          // Continue polling if there's an error
          console.log(`Polling for results... attempt ${attempts}/${maxAttempts}`)
        }
      }

      // If we've exhausted attempts, stop polling anyway
      setReAnalyzing(false)

      // Try one final refresh
      if (onDataRefresh) {
        try {
          await onDataRefresh()
        } catch (err) {
          // Ignore final refresh errors - data might still be computing
          console.log('Final refresh attempt failed, but re-analysis may still be in progress')
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to re-analyze project')
      setReAnalyzing(false)
    }
  }, [projectId, onDataRefresh, pollingInterval, maxAttempts, autoRefresh])

  return {
    handleReAnalyze,
    reAnalyzing,
    error,
    clearError,
  }
}

