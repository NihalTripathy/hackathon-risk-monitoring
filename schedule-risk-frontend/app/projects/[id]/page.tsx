'use client'

import { useEffect, useState, useMemo, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import ForecastChart from '@/components/ForecastChart'
import ForecastExplanation from '@/components/ForecastExplanation'
import EnhancedZombieTask from '@/components/EnhancedZombieTask'
import FeedbackWidget from '@/components/FeedbackWidget'
import OnboardingTour from '@/components/OnboardingTour'
import ForensicToggle from '@/components/ForensicToggle'
import ForensicInsights from '@/components/ForensicInsights'
import ForensicForecastChart from '@/components/ForensicForecastChart'
import { getOnboardingTour, getOnboardingStatus, getForensicForecast } from '@/lib/api'
import {
  AlertTriangle,
  TrendingUp,
  Calendar,
  ArrowRight,
  Loader2,
  RefreshCw,
  Activity,
  Users,
  Zap,
  RotateCcw,
} from 'lucide-react'
import api, { getAnomalies, type Anomaly, type Forecast } from '@/lib/api'
import { useReAnalyze } from '@/hooks/useReAnalyze'

// Forecast interface now includes explanation from API

interface Risk {
  activity_id: string
  name: string
  risk_score: number
  risk_level?: string
  explanation?: string
  risk_factors?: {
    delay?: string
    critical_path?: string
    resource?: string
  }
  key_metrics?: {
    delay_days?: number
    float_days?: number
    on_critical_path?: boolean
    resource_overbooked?: boolean
    progress_slip_pct?: number
  }
  detailed_explanation?: {
    reasons?: string[]
    suggestions?: string[]
  }
  percent_complete?: number
  on_critical_path?: boolean
}

export default function ProjectDashboard() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string

  // Store current path for settings page navigation
  useEffect(() => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('lastPath', `/projects/${projectId}`)
      sessionStorage.setItem('lastProjectId', projectId)
    }
  }, [projectId])

  const [forecast, setForecast] = useState<Forecast | null>(null)
  const [risks, setRisks] = useState<Risk[]>([])
  const [totalRisks, setTotalRisks] = useState(0)
  const [anomalies, setAnomalies] = useState<Anomaly | null>(null)
  const [anomaliesLoading, setAnomaliesLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [onboardingSteps, setOnboardingSteps] = useState<any[]>([])
  // Forensic Intelligence state
  const [isForensicMode, setIsForensicMode] = useState(false)
  const [forensicForecast, setForensicForecast] = useState<Forecast | null>(null)
  const [forensicLoading, setForensicLoading] = useState(false)

  // Check onboarding status
  const checkOnboarding = useCallback(async () => {
    try {
      const status = await getOnboardingStatus()
      // Show dashboard tour if user hasn't completed it
      if (!status.completed_tours?.includes('dashboard')) {
        const tour = await getOnboardingTour('dashboard')
        setOnboardingSteps(tour.steps)
        setShowOnboarding(true)
      }
    } catch (error) {
      console.error('Failed to check onboarding:', error)
      // Don't show tour if API fails
    }
  }, [])

  // OPTIMIZATION: Memoize fetchData to avoid recreation on every render
  const fetchData = useCallback(async () => {
    try {
      setError(null)
      const [forecastRes, risksRes] = await Promise.all([
        api.get(`/projects/${projectId}/forecast?include_explanation=true`),
        api.get(`/projects/${projectId}/risks/top?limit=10&include_explanations=true`),
      ])

      setForecast({
        p50: forecastRes.data.p50,
        p80: forecastRes.data.p80,
        p90: forecastRes.data.p90,
        p95: forecastRes.data.p95,
        current: forecastRes.data.current || 0,
        criticality_indices: forecastRes.data.criticality_indices,
        warnings: forecastRes.data.warnings,
        explanation: forecastRes.data.explanation,
      } as Forecast)
      
      // Handle both old format (array) and new format (object with top_risks)
      if (Array.isArray(risksRes.data)) {
        setRisks(risksRes.data)
        setTotalRisks(risksRes.data.length)
      } else {
        setRisks(risksRes.data.top_risks || [])
        setTotalRisks(risksRes.data.total_risks || 0)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load project data')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [projectId])

  // Fetch forensic forecast when forensic mode is enabled
  const fetchForensicForecast = useCallback(async () => {
    if (!isForensicMode) {
      setForensicForecast(null)
      return
    }
    
    try {
      setForensicLoading(true)
      setError(null)
      const forecast = await getForensicForecast(projectId, 2000, false)
      setForensicForecast(forecast)
    } catch (err: any) {
      console.error('Failed to fetch forensic forecast:', err)
      setError(err.response?.data?.detail || 'Failed to load forensic forecast')
      setForensicForecast(null)
    } finally {
      setForensicLoading(false)
    }
  }, [projectId, isForensicMode])

  useEffect(() => {
    if (isForensicMode) {
      fetchForensicForecast()
    }
  }, [isForensicMode, fetchForensicForecast])

  // OPTIMIZATION: Memoize fetchAnomalies
  const fetchAnomalies = useCallback(async () => {
    try {
      setAnomaliesLoading(true)
      const anomaliesRes = await api.get(`/projects/${projectId}/anomalies`)
      if (anomaliesRes.data) {
        setAnomalies(anomaliesRes.data)
      }
    } catch (err: any) {
      // Silently fail - anomalies are optional
      console.warn('Failed to load anomalies:', err)
    } finally {
      setAnomaliesLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    if (projectId) {
      fetchData()
      // Load anomalies after a short delay to prioritize main content
      const timer = setTimeout(() => {
        fetchAnomalies()
      }, 100)
      
      // Check if user needs onboarding (after data loads)
      const onboardingTimer = setTimeout(() => {
        checkOnboarding()
      }, 1000)
      
      return () => {
        clearTimeout(timer)
        clearTimeout(onboardingTimer)
      }
    }
  }, [projectId, checkOnboarding, fetchData, fetchAnomalies])

  // OPTIMIZATION: Memoize handleRefresh
  const handleRefresh = useCallback(() => {
    setRefreshing(true)
    fetchData()
    fetchAnomalies()
  }, [fetchData, fetchAnomalies])

  // Use centralized re-analyze hook
  const { handleReAnalyze, reAnalyzing: reAnalyzingState, error: reAnalyzeError } = useReAnalyze(projectId, {
    onDataRefresh: async () => {
      await fetchData()
      await fetchAnomalies()
    },
    pollingInterval: 1000,
    maxAttempts: 30,
  })

  // Merge re-analyze error with page error
  useEffect(() => {
    if (reAnalyzeError) {
      setError(reAnalyzeError)
    }
  }, [reAnalyzeError])

  // Helper functions (pure functions, safe to keep as regular functions)
  const getRiskColor = (score: number) => {
    if (score >= 0.7) return 'text-red-700 bg-red-100 border-red-300'
    if (score >= 0.4) return 'text-yellow-700 bg-yellow-100 border-yellow-300'
    return 'text-green-700 bg-green-100 border-green-300'
  }

  const getRiskLabel = (score: number) => {
    if (score >= 0.7) return 'High'
    if (score >= 0.4) return 'Medium'
    return 'Low'
  }

  // Normalize risk score (handle both 0-1 and 0-100 formats)
  const normalizeRiskScore = (score: number) => {
    return score > 1 ? score / 100 : score
  }

  // Get risk bar color based on score
  const getRiskBarColor = (score: number) => {
    const normalized = normalizeRiskScore(score)
    if (normalized >= 0.7) return 'from-red-500 to-red-600'
    if (normalized >= 0.4) return 'from-yellow-500 to-yellow-600'
    return 'from-green-500 to-green-600'
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
            <AlertTriangle className="w-4 h-4 text-red-600" />
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
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold text-gray-900">Project Dashboard</h1>
          </div>
          <p className="text-xs text-gray-500 font-mono">{projectId}</p>
        </div>
        <div className="flex items-center gap-2 mt-2 sm:mt-0">
          <button
            onClick={handleReAnalyze}
            disabled={reAnalyzingState || refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Re-calculate all analytics with latest logic"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${reAnalyzingState ? 'animate-spin' : ''}`} />
            <span>{reAnalyzingState ? 'Re-analyzing...' : 'Re-analyze'}</span>
          </button>
          <button
            onClick={handleRefresh}
            disabled={refreshing || reAnalyzingState}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Compact Forecast Cards */}
      <div className="grid md:grid-cols-3 gap-3 mb-4" data-tour="forecast-cards">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-blue-100 uppercase tracking-wide">P50 Forecast</span>
            <TrendingUp className="w-4 h-4 text-blue-100" />
          </div>
          <div className="text-2xl font-bold mb-1">
            {forecast ? `${forecast.p50.toFixed(1)}` : '—'}
          </div>
          <p className="text-xs text-blue-100 opacity-90">days • 50% confidence</p>
        </div>

        <div className="bg-gradient-to-br from-red-500 to-rose-600 text-white rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-red-100 uppercase tracking-wide">P80 Forecast</span>
            <AlertTriangle className="w-4 h-4 text-red-100" />
          </div>
          <div className="text-2xl font-bold mb-1">
            {forecast ? `${forecast.p80.toFixed(1)}` : '—'}
          </div>
          <p className="text-xs text-red-100 opacity-90">days • 80% confidence</p>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-emerald-600 text-white rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-green-100 uppercase tracking-wide">Progress</span>
            <Calendar className="w-4 h-4 text-green-100" />
          </div>
          <div className="text-2xl font-bold mb-1">
            {forecast ? `${forecast.current.toFixed(1)}%` : '—'}
          </div>
          <p className="text-xs text-green-100 opacity-90">completion status</p>
        </div>
      </div>

      {/* Forensic Toggle */}
      <ForensicToggle
        isForensic={isForensicMode}
        onToggle={setIsForensicMode}
        isLoading={forensicLoading}
      />

      {/* Forensic Insights */}
      {isForensicMode && forensicForecast?.forensic_insights && (
        <ForensicInsights insights={forensicForecast.forensic_insights} />
      )}

      {/* Forecast Visualization */}
      {isForensicMode && forensicForecast && forecast ? (
        <ForensicForecastChart
          standard={forecast}
          forensic={forensicForecast}
          current={forecast.current || 0}
          forensicModulationApplied={forensicForecast.forensic_modulation_applied}
        />
      ) : forecast ? (
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-bold text-gray-900">Forecast Visualization</h2>
            {forecast.criticality_indices && Object.keys(forecast.criticality_indices).length > 0 && (
              <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                {Object.keys(forecast.criticality_indices).length} activities analyzed
              </span>
            )}
          </div>
          <div className="h-64">
            <ForecastChart p50={forecast.p50} p80={forecast.p80} current={forecast.current || 0} />
          </div>
          {forecast.p90 && forecast.p95 && (
            <div className="mt-3 flex gap-4 text-xs text-gray-600">
              <span>P90: <strong>{forecast.p90}</strong> days</span>
              <span>P95: <strong>{forecast.p95}</strong> days</span>
            </div>
          )}
          {forecast.warnings && forecast.warnings.length > 0 && (
            <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-xs font-semibold text-yellow-900 mb-1">Warning</p>
                  {forecast.warnings.map((warning, idx) => (
                    <p key={idx} className="text-xs text-yellow-800">{warning}</p>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      ) : null}

      {/* Anomalies Section - Loading */}
      {anomaliesLoading && !anomalies && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600" />
              Hidden Anomalies Detected
            </h2>
            <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
          </div>
          <p className="text-xs text-gray-500">Loading anomalies...</p>
        </div>
      )}

      {/* Anomalies Section */}
      {anomalies && anomalies.total_anomalies > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4" data-tour="anomalies">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600" />
              Hidden Anomalies Detected
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-xs text-red-600 font-bold bg-red-50 px-2 py-1 rounded border border-red-200">
                {anomalies.total_anomalies} {anomalies.total_anomalies === 1 ? 'anomaly' : 'anomalies'}
              </span>
              <button
                onClick={() => router.push(`/projects/${projectId}/anomalies`)}
                className="text-xs font-medium text-primary-600 hover:text-primary-700 underline transition-colors"
              >
                View All
              </button>
            </div>
          </div>
          
          <div className="space-y-3">
            {/* Zombie Tasks */}
            {anomalies.zombie_tasks && anomalies.zombie_tasks.length > 0 && (
              <div className="p-3 bg-red-50 border border-red-200 rounded">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-4 h-4 text-red-600" />
                  <h3 className="text-xs font-bold text-red-900">Zombie Tasks ({anomalies.zombie_tasks.length})</h3>
                </div>
                <p className="text-xs text-red-700 mb-2">Tasks that should have started but didn't:</p>
                <div className="space-y-3">
                  {anomalies.zombie_tasks.slice(0, 3).map((zombie) => (
                    <EnhancedZombieTask 
                      key={zombie.activity_id} 
                      zombie={zombie} 
                      projectId={projectId}
                    />
                  ))}
                  {anomalies.zombie_tasks.length > 3 && (
                    <button
                      onClick={() => router.push(`/projects/${projectId}/anomalies?type=zombie`)}
                      className="text-xs text-red-600 hover:text-red-700 font-medium underline transition-colors"
                    >
                      +{anomalies.zombie_tasks.length - 3} more...
                    </button>
                  )}
                </div>
              </div>
            )}
            
            {/* Resource Black Holes */}
            {anomalies.black_holes && anomalies.black_holes.length > 0 && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="w-4 h-4 text-amber-600" />
                  <h3 className="text-xs font-bold text-amber-900">Resource Black Holes ({anomalies.black_holes.length})</h3>
                </div>
                <p className="text-xs text-amber-700 mb-2">Overloaded resources causing bottlenecks:</p>
                <div className="space-y-1.5">
                  {anomalies.black_holes.slice(0, 3).map((bh) => (
                    <div key={bh.resource_id} className="text-xs text-amber-800 bg-white p-2 rounded border border-amber-200">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold">{bh.resource_id}</span>
                        <span className="text-amber-600 font-bold">
                          {((bh.max_overlap_utilization || bh.utilization) * 100).toFixed(0)}% utilized
                        </span>
                      </div>
                      {bh.max_overlap_period && (
                        <p className="text-amber-600 text-[10px] mt-1">
                          Max overlap: {bh.max_overlap_period[0]} to {bh.max_overlap_period[1]}
                        </p>
                      )}
                    </div>
                  ))}
                  {anomalies.black_holes.length > 3 && (
                    <button
                      onClick={() => router.push(`/projects/${projectId}/anomalies?type=blackhole`)}
                      className="text-xs text-amber-600 hover:text-amber-700 font-medium underline transition-colors"
                    >
                      +{anomalies.black_holes.length - 3} more...
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Top Risks - Compact Header */}
      <div className="mb-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">Top Risks</h2>
          <span className="text-xs text-gray-600 font-medium bg-gray-100 px-2 py-1 rounded">
            {risks.length} of {totalRisks || risks.length} {totalRisks === 1 ? 'risk' : 'risks'}
          </span>
        </div>
      </div>

      {/* Top Risks Cards */}
      {risks.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 text-center py-8">
          <AlertTriangle className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <p className="text-sm text-gray-500">No risks identified</p>
        </div>
      ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {risks.map((risk) => {
              const normalizedScore = normalizeRiskScore(risk.risk_score)
              const displayScore = normalizedScore * 100
              const riskLabel = risk.risk_level || getRiskLabel(normalizedScore)
              const riskColor = getRiskColor(normalizedScore)
              const barColor = getRiskBarColor(risk.risk_score)
              const activityName = risk.name || (risk as any).activity_name || 'Unknown Activity'
              
              return (
                <div
                  key={risk.activity_id}
                  className="bg-white rounded-lg border border-gray-200 p-3 hover:shadow-md hover:border-primary-300 transition-all group flex flex-col"
                >
                  {/* Card Header */}
                  <div className="mb-3">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-bold text-gray-900 group-hover:text-primary-700 transition-colors line-clamp-2">
                          {activityName}
                        </h3>
                        <p className="text-xs text-gray-500 font-mono mt-0.5">{risk.activity_id}</p>
                      </div>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold border flex-shrink-0 ${riskColor}`}
                      >
                        {riskLabel}
                      </span>
                    </div>
                  </div>

                  {/* Explanation (Problem Statement Format) */}
                  {risk.explanation && (
                    <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded">
                      <p className="text-xs text-blue-900 font-medium leading-relaxed">
                        {risk.explanation}
                      </p>
                    </div>
                  )}

                  {/* Risk Score Section */}
                  <div className="mb-3 flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">Risk</span>
                      <span className="text-lg font-bold text-gray-900">
                        {displayScore.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3 shadow-inner overflow-hidden">
                      <div
                        className={`bg-gradient-to-r ${barColor} h-3 rounded-full transition-all duration-700 flex items-center justify-end pr-1`}
                        style={{ width: `${Math.min(displayScore, 100)}%` }}
                      >
                        {displayScore > 15 && (
                          <span className="text-[10px] font-bold text-white drop-shadow-sm">
                            {displayScore.toFixed(0)}%
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Key Metrics */}
                  {risk.key_metrics && (
                    <div className="mb-3 space-y-1.5">
                      {risk.key_metrics.delay_days !== undefined && risk.key_metrics.delay_days > 0 && (
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-600">Delay:</span>
                          <span className="font-bold text-red-600">
                            +{risk.key_metrics.delay_days} days <span className="text-gray-500 text-[10px] font-normal">(vs baseline)</span>
                          </span>
                        </div>
                      )}
                      {risk.key_metrics.float_days !== undefined && (
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-600">Float:</span>
                          <span className={`font-bold ${risk.key_metrics.float_days <= 2 ? 'text-red-600' : 'text-gray-700'}`}>
                            {risk.key_metrics.float_days.toFixed(1)} days
                          </span>
                        </div>
                      )}
                      {risk.key_metrics.on_critical_path && (
                        <div className="flex items-center gap-1 text-xs">
                          <span className="text-red-600 font-bold">●</span>
                          <span className="text-gray-700">On Critical Path</span>
                        </div>
                      )}
                      {risk.key_metrics.resource_overbooked && (
                        <div className="flex items-center gap-1 text-xs">
                          <span className="text-amber-600 font-bold">●</span>
                          <span className="text-gray-700">Resource Overloaded</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Risk Factors */}
                  {risk.risk_factors && (
                    <div className="mb-3 flex flex-wrap gap-1">
                      {risk.risk_factors.delay && (
                        <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                          risk.risk_factors.delay === 'high' ? 'bg-red-100 text-red-700' :
                          risk.risk_factors.delay === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          Delay: {risk.risk_factors.delay}
                        </span>
                      )}
                      {risk.risk_factors.critical_path && (
                        <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                          risk.risk_factors.critical_path === 'high' ? 'bg-red-100 text-red-700' :
                          risk.risk_factors.critical_path === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          Critical: {risk.risk_factors.critical_path}
                        </span>
                      )}
                      {risk.risk_factors.resource && (
                        <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                          risk.risk_factors.resource === 'high' ? 'bg-red-100 text-red-700' :
                          risk.risk_factors.resource === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          Resource: {risk.risk_factors.resource}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Legacy Impact Days (backward compatibility) */}
                  {(risk as any).impact_days && (risk as any).impact_days > 0 && (
                    <div className="mb-3 p-2 bg-amber-50 border border-amber-200 rounded">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                        <div>
                          <span className="text-[10px] font-medium text-amber-900 uppercase tracking-wide">Impact</span>
                          <div className="text-sm font-bold text-amber-700">
                            +{(risk as any).impact_days.toFixed(1)} days
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Action Button */}
                  <button
                    onClick={() =>
                      router.push(`/projects/${projectId}/activities/${risk.activity_id}`)
                    }
                    className="w-full flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium bg-primary-600 hover:bg-primary-700 text-white rounded-md transition-colors mt-auto"
                  >
                    View Details
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
              )
            })}
          </div>
        )}

      {/* Feedback Widget - NEW UX Enhancement */}
      <FeedbackWidget 
        feature="project_dashboard" 
        projectId={projectId}
        position="bottom-right"
      />

      {/* Onboarding Tour */}
      {showOnboarding && onboardingSteps.length > 0 && (
        <OnboardingTour
          tourId="dashboard"
          steps={onboardingSteps}
          onComplete={() => setShowOnboarding(false)}
        />
      )}
    </Layout>
  )
}

