'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import Layout from '@/components/Layout'
import {
  AlertTriangle,
  Activity,
  Users,
  Loader2,
  RefreshCw,
  ArrowLeft,
  Calendar,
} from 'lucide-react'
import { getAnomalies, type Anomaly } from '@/lib/api'
import { formatDateDDMMYYYY } from '@/lib/dateUtils'
import EnhancedZombieTask from '@/components/EnhancedZombieTask'

export default function AnomaliesPage() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const projectId = params.id as string
  const filterType = searchParams.get('type') // 'zombie' or 'blackhole'

  // Store current path for settings page navigation
  useEffect(() => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('lastPath', `/projects/${projectId}/anomalies`)
      sessionStorage.setItem('lastProjectId', projectId)
    }
  }, [projectId])

  const [anomalies, setAnomalies] = useState<Anomaly | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAnomalies = async () => {
    try {
      setError(null)
      setLoading(true)
      const data = await getAnomalies(projectId)
      setAnomalies(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load anomalies')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    if (projectId) {
      fetchAnomalies()
    }
  }, [projectId])

  const handleRefresh = () => {
    setRefreshing(true)
    fetchAnomalies()
  }

  if (loading) {
    return (
      <Layout projectId={projectId}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-700">Loading anomalies...</p>
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
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <p className="text-sm font-medium">{error}</p>
          </div>
        </div>
      </Layout>
    )
  }

  const showZombies = !filterType || filterType === 'zombie'
  const showBlackHoles = !filterType || filterType === 'blackhole'

  return (
    <Layout projectId={projectId}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
        <div className="flex items-center gap-3 mb-2 sm:mb-0">
          <button
            onClick={() => router.push(`/projects/${projectId}`)}
            className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
            aria-label="Back to dashboard"
          >
            <ArrowLeft className="w-4 h-4 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Hidden Anomalies</h1>
            <p className="text-xs text-gray-500 font-mono">{projectId}</p>
          </div>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Summary */}
      {anomalies && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <h2 className="text-lg font-bold text-gray-900">Total Anomalies</h2>
            </div>
            <span className="text-2xl font-bold text-red-600">
              {anomalies.total_anomalies}
            </span>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3">
            <div className="bg-red-50 border border-red-200 rounded p-3">
              <div className="text-xs text-red-700 font-medium mb-1">Zombie Tasks</div>
              <div className="text-xl font-bold text-red-900">
                {anomalies.zombie_tasks?.length || 0}
              </div>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded p-3">
              <div className="text-xs text-amber-700 font-medium mb-1">Resource Black Holes</div>
              <div className="text-xl font-bold text-amber-900">
                {anomalies.black_holes?.length || 0}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Zombie Tasks Section */}
      {showZombies && anomalies?.zombie_tasks && anomalies.zombie_tasks.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-red-600" />
            <h2 className="text-lg font-bold text-gray-900">
              Zombie Tasks ({anomalies.zombie_tasks.length})
            </h2>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Tasks that should have started but didn't:
          </p>
          <div className="space-y-3">
            {anomalies.zombie_tasks.map((zombie) => (
              <EnhancedZombieTask 
                key={zombie.activity_id} 
                zombie={zombie} 
                projectId={projectId}
              />
            ))}
          </div>
        </div>
      )}

      {/* Resource Black Holes Section */}
      {showBlackHoles && anomalies?.black_holes && anomalies.black_holes.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-5 h-5 text-amber-600" />
            <h2 className="text-lg font-bold text-gray-900">
              Resource Black Holes ({anomalies.black_holes.length})
            </h2>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Overloaded resources causing bottlenecks:
          </p>
          <div className="space-y-3">
            {anomalies.black_holes.map((bh) => (
              <div
                key={bh.resource_id}
                className="bg-amber-50 border border-amber-200 rounded-lg p-4 hover:bg-amber-100 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-mono font-bold text-amber-900 text-lg">{bh.resource_id}</span>
                      <span className="text-amber-600 font-bold">
                        {((bh.max_overlap_utilization || bh.utilization) * 100).toFixed(0)}% utilized
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-xs text-amber-700 mb-2">
                      <div>
                        <span className="font-medium">Max FTE:</span> {bh.max_fte.toFixed(1)}
                      </div>
                      <div>
                        <span className="font-medium">Total FTE:</span> {bh.total_fte.toFixed(1)}
                      </div>
                      <div>
                        <span className="font-medium">Max Overlap FTE:</span> {bh.max_overlap_fte?.toFixed(1) || 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Activities:</span> {bh.activity_count}
                      </div>
                    </div>
                    {bh.max_overlap_period && (
                      <div className="flex items-center gap-1 text-xs text-amber-600 mb-2">
                        <Calendar className="w-3 h-3" />
                        <span>
                          Max overlap: {formatDateDDMMYYYY(bh.max_overlap_period[0])} to{' '}
                          {formatDateDDMMYYYY(bh.max_overlap_period[1])}
                        </span>
                      </div>
                    )}
                    {bh.activities && bh.activities.length > 0 && (
                      <div className="mt-2">
                        <span className="text-xs font-medium text-amber-700">Affected Activities:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {bh.activities.slice(0, 10).map((activityId) => (
                            <span
                              key={activityId}
                              className="text-xs font-mono bg-white border border-amber-200 rounded px-1.5 py-0.5 text-amber-800"
                            >
                              {activityId}
                            </span>
                          ))}
                          {bh.activities.length > 10 && (
                            <span className="text-xs text-amber-600 italic">
                              +{bh.activities.length - 10} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                    {bh.critical_overlaps && bh.critical_overlaps.length > 0 && (
                      <div className="mt-3 pt-2 border-t border-amber-300">
                        <span className="text-xs font-medium text-red-700 mb-1 block">
                          Critical Period Overlaps:
                        </span>
                        <div className="space-y-1">
                          {bh.critical_overlaps.map((overlap, idx) => (
                            <div key={idx} className="text-xs bg-white border border-red-200 rounded p-2">
                              <div className="font-medium text-red-800 mb-1">
                                Period: {formatDateDDMMYYYY(overlap.period[0])} to{' '}
                                {formatDateDDMMYYYY(overlap.period[1])}
                              </div>
                              <div className="text-red-700">
                                Utilization: {(overlap.utilization * 100).toFixed(0)}% ({overlap.total_fte.toFixed(1)} FTE)
                              </div>
                              {overlap.activities && overlap.activities.length > 0 && (
                                <div className="mt-1 text-red-600">
                                  Activities: {overlap.activities.join(', ')}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {anomalies && anomalies.total_anomalies === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 text-center py-12">
          <AlertTriangle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-lg font-medium text-gray-700 mb-1">No Anomalies Detected</p>
          <p className="text-sm text-gray-500">Your project schedule looks healthy!</p>
        </div>
      )}

      {/* Filtered Empty State */}
      {((filterType === 'zombie' && (!anomalies?.zombie_tasks || anomalies.zombie_tasks.length === 0)) ||
        (filterType === 'blackhole' && (!anomalies?.black_holes || anomalies.black_holes.length === 0))) && (
        <div className="bg-white rounded-lg border border-gray-200 text-center py-12">
          <AlertTriangle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-lg font-medium text-gray-700 mb-1">No {filterType === 'zombie' ? 'Zombie Tasks' : 'Resource Black Holes'}</p>
          <p className="text-sm text-gray-500">
            {filterType === 'zombie'
              ? 'All tasks have started on time or are not yet due.'
              : 'No resources are currently overloaded.'}
          </p>
        </div>
      )}
    </Layout>
  )
}

