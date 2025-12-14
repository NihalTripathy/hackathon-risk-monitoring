'use client'

import { useEffect, useState, useMemo } from 'react'
import { useParams } from 'next/navigation'
import Layout from '@/components/Layout'
import { FileText, Clock, Loader2, RefreshCw, History, ChevronDown, ChevronUp } from 'lucide-react'
import api from '@/lib/api'
import { formatDateTimeDDMMYYYY } from '@/lib/dateUtils'
const EVENTS_PER_PAGE = 20

interface AuditEvent {
  timestamp: string
  event: string
  project_id: string
  details?: Record<string, any> | null
}

interface AuditLog {
  project_id: string
  total_events: number
  events: AuditEvent[]
}

export default function AuditLogPage() {
  const params = useParams()
  const projectId = params.id as string

  // Store current path for settings page navigation
  useEffect(() => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('lastPath', `/projects/${projectId}/audit`)
      sessionStorage.setItem('lastProjectId', projectId)
    }
  }, [projectId])

  const [auditLog, setAuditLog] = useState<AuditLog | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [visibleCount, setVisibleCount] = useState(EVENTS_PER_PAGE)
  const [expandedEvents, setExpandedEvents] = useState<Set<number>>(new Set())

  const fetchAuditLog = async () => {
    try {
      setError(null)
      setLoading(true)
      const response = await api.get(`/projects/${projectId}/audit`)
      setAuditLog(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load audit log')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    if (projectId) {
      fetchAuditLog()
    }
  }, [projectId])

  const handleRefresh = () => {
    setRefreshing(true)
    setVisibleCount(EVENTS_PER_PAGE)
    setExpandedEvents(new Set())
    fetchAuditLog()
  }

  const toggleExpand = (index: number) => {
    const newExpanded = new Set(expandedEvents)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedEvents(newExpanded)
  }

  const loadMore = () => {
    setVisibleCount(prev => prev + EVENTS_PER_PAGE)
  }

  const visibleEvents = useMemo(() => {
    return auditLog?.events.slice(0, visibleCount) || []
  }, [auditLog?.events, visibleCount])

  const hasMore = useMemo(() => {
    return (auditLog?.events.length || 0) > visibleCount
  }, [auditLog?.events.length, visibleCount])


  const getEventTypeColor = (eventType: string | undefined | null) => {
    if (!eventType) {
      return 'bg-gray-500 text-white'
    }
    const colors: Record<string, string> = {
      project_upload: 'bg-blue-500 text-white',
      forecast: 'bg-purple-500 text-white',
      risk_scan: 'bg-red-500 text-white',
      explanation: 'bg-yellow-500 text-white',
      simulation: 'bg-green-500 text-white',
    }
    return colors[eventType] || 'bg-gray-500 text-white'
  }

  const formatEventType = (eventType: string | undefined | null) => {
    if (!eventType) {
      return 'Unknown'
    }
    return eventType
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  if (loading) {
    return (
      <Layout projectId={projectId}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-700">Loading...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout projectId={projectId}>
        <div className="bg-red-50 border border-red-200 rounded-lg text-red-800 p-4">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-red-600" />
            <p className="text-sm font-medium">{error}</p>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout projectId={projectId}>
      {/* Compact Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Audit Log</h1>
          <p className="text-xs text-gray-500">Project activity history</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors mt-2 sm:mt-0 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Compact Summary */}
      {auditLog && (
        <div className="bg-gradient-to-r from-primary-600 to-blue-600 text-white rounded-lg p-3 mb-4 flex items-center gap-3">
          <History className="w-4 h-4 flex-shrink-0" />
          <div className="flex items-baseline gap-2">
            <span className="text-xs font-medium opacity-90">Total Events:</span>
            <span className="text-lg font-bold">{auditLog.total_events}</span>
          </div>
        </div>
      )}

      {/* Compact Events List */}
      <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-200">
        {auditLog && auditLog.events.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="w-8 h-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500">No audit events found</p>
          </div>
        ) : (
          <>
            {visibleEvents.map((event, idx) => {
              const hasDetails = event.details && Object.keys(event.details).length > 0
              const isExpanded = expandedEvents.has(idx)
              
              return (
                <div
                  key={`${event.timestamp}-${idx}`}
                  className="p-3 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getEventTypeColor(
                          event.event
                        )}`}
                      >
                        {formatEventType(event.event)}
                      </span>
                      <div className="flex items-center gap-1.5 text-xs text-gray-500 flex-shrink-0">
                        <Clock className="w-3 h-3" />
                        <span>{formatDateTimeDDMMYYYY(event.timestamp)}</span>
                      </div>
                    </div>
                    {hasDetails && (
                      <button
                        onClick={() => toggleExpand(idx)}
                        className="flex items-center gap-1 text-xs text-gray-600 hover:text-primary-600 transition-colors flex-shrink-0"
                      >
                        {isExpanded ? (
                          <>
                            <ChevronUp className="w-3.5 h-3.5" />
                            <span>Hide</span>
                          </>
                        ) : (
                          <>
                            <ChevronDown className="w-3.5 h-3.5" />
                            <span>Details</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                  
                  {isExpanded && hasDetails && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <div className="text-xs font-medium text-gray-700 mb-1.5 flex items-center gap-1.5">
                        <FileText className="w-3 h-3 text-primary-600" />
                        Details
                      </div>
                      <div className="bg-gray-50 rounded p-2 border border-gray-200">
                        <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed overflow-x-auto">
                          {JSON.stringify(event.details, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
            
            {hasMore && (
              <div className="p-3 text-center">
                <button
                  onClick={loadMore}
                  className="text-xs font-medium text-primary-600 hover:text-primary-700 transition-colors"
                >
                  Load More ({auditLog.events.length - visibleCount} remaining)
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  )
}
