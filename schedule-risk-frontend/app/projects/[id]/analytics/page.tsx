'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Layout from '@/components/Layout'
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  Area,
  AreaChart,
} from 'recharts'
import {
  Loader2,
  AlertTriangle,
  TrendingUp,
  Activity,
  Users,
  Target,
  BarChart3,
  RefreshCw,
  RotateCcw,
} from 'lucide-react'
import api, { getTopRisks, getAnomalies, getForecast, type Risk, type Anomaly, type Forecast } from '@/lib/api'
import { useReAnalyze } from '@/hooks/useReAnalyze'

interface ChartData {
  name: string
  value: number
  fill?: string
}

export default function AnalyticsDashboard() {
  const params = useParams()
  const projectId = params.id as string

  // Store current path for settings page navigation
  useEffect(() => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('lastPath', `/projects/${projectId}/analytics`)
      sessionStorage.setItem('lastProjectId', projectId)
    }
  }, [projectId])

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Data states
  const [risks, setRisks] = useState<Risk[]>([])
  const [totalRisks, setTotalRisks] = useState(0)
  const [anomalies, setAnomalies] = useState<Anomaly | null>(null)
  const [forecast, setForecast] = useState<Forecast | null>(null)

  // Chart data states
  const [riskDistribution, setRiskDistribution] = useState<ChartData[]>([])
  const [riskScoreHistogram, setRiskScoreHistogram] = useState<ChartData[]>([])
  const [criticalPathData, setCriticalPathData] = useState<ChartData[]>([])
  const [resourceUtilization, setResourceUtilization] = useState<ChartData[]>([])
  const [completionStatus, setCompletionStatus] = useState<ChartData[]>([])
  const [riskFactors, setRiskFactors] = useState<ChartData[]>([])

  const fetchData = async () => {
    try {
      setError(null)
      // Request a high limit to get all risks, or use total_risks if available
      const [risksRes, anomaliesRes, forecastRes] = await Promise.all([
        api.get(`/projects/${projectId}/risks/top?limit=1000&include_explanations=true`),
        api.get(`/projects/${projectId}/anomalies`).catch(() => ({ data: null })),
        api.get(`/projects/${projectId}/forecast`),
      ])

      // Process risks
      const risksData = Array.isArray(risksRes.data) 
        ? risksRes.data 
        : (risksRes.data.top_risks || [])
      setRisks(risksData)
      const totalRisksCount = risksRes.data.total_risks || risksData.length
      setTotalRisks(totalRisksCount)

      // Process anomalies
      if (anomaliesRes.data) {
        setAnomalies(anomaliesRes.data)
      }

      // Process forecast
      setForecast(forecastRes.data)

      // Process chart data
      processChartData(risksData, anomaliesRes.data, forecastRes.data, totalRisksCount)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load analytics data')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const processChartData = (risksData: Risk[], anomaliesData: Anomaly | null, forecastData: Forecast, totalActivities: number) => {
    // 1. Risk Distribution by Level (High/Medium/Low)
    const riskLevels = { High: 0, Medium: 0, Low: 0 }
    risksData.forEach(risk => {
      // Use risk_level from backend if available, otherwise calculate from score
      // Backend returns capitalized: "High", "Medium", "Low"
      let level = risk.risk_level
      if (!level) {
        // Fallback: calculate from score (score is 0-100 range)
        const score = risk.risk_score > 1 ? risk.risk_score : risk.risk_score * 100
        level = score >= 70 ? 'High' : score >= 40 ? 'Medium' : 'Low'
      }
      // Normalize to capitalized format
      level = level.charAt(0).toUpperCase() + level.slice(1).toLowerCase()
      if (level === 'High' || level === 'Medium' || level === 'Low') {
        riskLevels[level as keyof typeof riskLevels]++
      }
    })
    
    // Only count activities that have risk data - don't assume missing ones are low risk
    // This ensures accuracy of the risk distribution
    
    // Always show all three categories for better visualization
    // Even if some are zero, this ensures the chart renders properly
    const distributionData = [
      { name: 'High Risk', value: Math.max(riskLevels.High, 0), fill: '#ef4444' },
      { name: 'Medium Risk', value: Math.max(riskLevels.Medium, 0), fill: '#f59e0b' },
      { name: 'Low Risk', value: Math.max(riskLevels.Low, 0), fill: '#10b981' },
    ]
    
    // If total is 0, show placeholder
    const total = distributionData.reduce((sum, item) => sum + item.value, 0)
    if (total === 0) {
      setRiskDistribution([
        { name: 'No Data', value: 1, fill: '#9ca3af' },
      ])
    } else {
      setRiskDistribution(distributionData)
    }

    // 2. Risk Score Histogram (buckets)
    const buckets = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    const histogram: number[] = new Array(buckets.length - 1).fill(0)
    risksData.forEach(risk => {
      const score = risk.risk_score > 1 ? risk.risk_score / 100 : risk.risk_score
      for (let i = 0; i < buckets.length - 1; i++) {
        if (score >= buckets[i] && score < buckets[i + 1]) {
          histogram[i]++
          break
        }
      }
    })
    setRiskScoreHistogram(
      histogram.map((count, i) => ({
        name: `${(buckets[i] * 100).toFixed(0)}-${(buckets[i + 1] * 100).toFixed(0)}%`,
        value: count,
      }))
    )

    // 3. Critical Path vs Non-Critical
    const critical = risksData.filter(r => r.on_critical_path || r.key_metrics?.on_critical_path).length
    const nonCritical = risksData.length - critical
    setCriticalPathData([
      { name: 'On Critical Path', value: critical, fill: '#dc2626' },
      { name: 'Not Critical', value: nonCritical, fill: '#6b7280' },
    ])

    // 4. Resource Utilization (from anomalies)
    if (anomaliesData?.black_holes) {
      const resourceData = anomaliesData.black_holes
        .slice(0, 10)
        .map(bh => ({
          name: bh.resource_id.length > 12 ? bh.resource_id.substring(0, 12) + '...' : bh.resource_id,
          value: Math.round((bh.max_overlap_utilization || bh.utilization) * 100),
          fill: (bh.max_overlap_utilization || bh.utilization) > 1 ? '#ef4444' : '#f59e0b',
        }))
      setResourceUtilization(resourceData)
    }

    // 5. Completion Status
    const completed = risksData.filter(r => (r.percent_complete || 0) >= 100).length
    const inProgress = risksData.filter(r => (r.percent_complete || 0) > 0 && (r.percent_complete || 0) < 100).length
    const notStarted = risksData.filter(r => (r.percent_complete || 0) === 0).length
    setCompletionStatus([
      { name: 'Completed', value: completed, fill: '#10b981' },
      { name: 'In Progress', value: inProgress, fill: '#3b82f6' },
      { name: 'Not Started', value: notStarted, fill: '#9ca3af' },
    ])

    // 6. Risk Factors Breakdown
    const factors: Record<string, number> = { Delay: 0, 'Critical Path': 0, Resource: 0 }
    risksData.forEach(risk => {
      if (risk.risk_factors?.delay) factors.Delay++
      if (risk.risk_factors?.critical_path) factors['Critical Path']++
      if (risk.risk_factors?.resource) factors.Resource++
      if (risk.key_metrics?.delay_days && risk.key_metrics.delay_days > 0) factors.Delay++
      if (risk.key_metrics?.on_critical_path) factors['Critical Path']++
      if (risk.key_metrics?.resource_overbooked) factors.Resource++
    })
    setRiskFactors([
      { name: 'Delay Issues', value: factors.Delay, fill: '#ef4444' },
      { name: 'Critical Path', value: factors['Critical Path'], fill: '#dc2626' },
      { name: 'Resource Overload', value: factors.Resource, fill: '#f59e0b' },
    ])
  }

  useEffect(() => {
    if (projectId) {
      fetchData()
    }
  }, [projectId])

  const handleRefresh = () => {
    setRefreshing(true)
    fetchData()
  }

  // Use centralized re-analyze hook
  const { handleReAnalyze, reAnalyzing, error: reAnalyzeError } = useReAnalyze(projectId, {
    onDataRefresh: fetchData,
    pollingInterval: 2000,
    maxAttempts: 20,
  })

  // Merge re-analyze error with page error
  useEffect(() => {
    if (reAnalyzeError) {
      setError(reAnalyzeError)
    }
  }, [reAnalyzeError])

  const COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899']

  if (loading) {
    return (
      <Layout projectId={projectId}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-700">Loading analytics...</p>
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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-primary-600" />
            Analytics Dashboard
          </h1>
          <p className="text-sm text-gray-600">Comprehensive project insights and visualizations</p>
        </div>
        <div className="flex items-center gap-2 mt-2 sm:mt-0">
          <button
            onClick={handleReAnalyze}
            disabled={reAnalyzing || refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Re-calculate all analytics with latest logic"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${reAnalyzing ? 'animate-spin' : ''}`} />
            <span>{reAnalyzing ? 'Re-analyzing...' : 'Re-analyze'}</span>
          </button>
          <button
            onClick={handleRefresh}
            disabled={refreshing || reAnalyzing}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg p-4 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <Activity className="w-5 h-5 text-blue-100" />
            <span className="text-xs font-semibold text-blue-100 uppercase">Total Activities</span>
          </div>
          <div className="text-3xl font-bold">{totalRisks || risks.length}</div>
          <p className="text-xs text-blue-100 mt-1">activities analyzed</p>
        </div>

        <div className="bg-gradient-to-br from-red-500 to-rose-600 text-white rounded-lg p-4 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <AlertTriangle className="w-5 h-5 text-red-100" />
            <span className="text-xs font-semibold text-red-100 uppercase">High Risks</span>
          </div>
          <div className="text-3xl font-bold">
            {riskDistribution.find(r => r.name === 'High Risk')?.value || 0}
          </div>
          <p className="text-xs text-red-100 mt-1">activities at high risk</p>
        </div>

        <div className="bg-gradient-to-br from-amber-500 to-orange-600 text-white rounded-lg p-4 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <Users className="w-5 h-5 text-amber-100" />
            <span className="text-xs font-semibold text-amber-100 uppercase">Resource Issues</span>
          </div>
          <div className="text-3xl font-bold">{anomalies?.black_holes?.length || 0}</div>
          <p className="text-xs text-amber-100 mt-1">overloaded resources</p>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-emerald-600 text-white rounded-lg p-4 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <Target className="w-5 h-5 text-green-100" />
            <span className="text-xs font-semibold text-green-100 uppercase">P50 Forecast</span>
          </div>
          <div className="text-3xl font-bold">{forecast?.p50?.toFixed(0) || '—'}</div>
          <p className="text-xs text-green-100 mt-1">days to completion</p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Risk Distribution Pie Chart */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            Risk Distribution
          </h3>
          <p className="text-xs text-gray-600 mb-4">
            Breakdown of activities by risk level. Shows how many activities are at high, medium, or low risk.
          </p>
          {riskDistribution.length === 0 || (riskDistribution.length === 1 && riskDistribution[0].name === 'No Data') ? (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              <div className="text-center">
                <AlertTriangle className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">No risk data available</p>
              </div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={riskDistribution.filter(item => item.value > 0)}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value, percent }) => 
                    value > 0 ? `${name}: ${value} (${(percent * 100).toFixed(0)}%)` : ''
                  }
                  outerRadius={100}
                  innerRadius={0}
                  fill="#8884d8"
                  dataKey="value"
                  animationBegin={0}
                  animationDuration={800}
                >
                  {riskDistribution.filter(item => item.value > 0).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill || '#8884d8'} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value: number, name: string) => [`${value} activities`, name]}
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: '4px' }}
                />
                <Legend 
                  formatter={(value, entry) => {
                    const dataItem = riskDistribution.find(item => item.name === value)
                    return `${value}: ${dataItem?.value || 0}`
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Risk Score Histogram */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            Risk Score Distribution
          </h3>
          <p className="text-xs text-gray-600 mb-4">
            Number of activities in each risk score range. Helps identify if risks are concentrated in specific ranges.
          </p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={riskScoreHistogram}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#3b82f6" name="Number of Activities" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Critical Path Breakdown */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-600" />
            Critical Path Analysis
          </h3>
          <p className="text-xs text-gray-600 mb-4">
            Activities on the critical path vs non-critical. Critical path activities have zero float and directly impact project completion.
          </p>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={criticalPathData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {criticalPathData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Completion Status */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-green-600" />
            Activity Completion Status
          </h3>
          <p className="text-xs text-gray-600 mb-4">
            Progress breakdown showing how many activities are completed, in progress, or not started.
          </p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={completionStatus}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#10b981" name="Number of Activities">
                {completionStatus.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Full Width Charts */}
      <div className="grid grid-cols-1 gap-6 mb-6">
        {/* Resource Utilization */}
        {resourceUtilization.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-amber-600" />
              Resource Utilization (Top 10 Overloaded Resources)
            </h3>
            <p className="text-xs text-gray-600 mb-4">
              Resources that are overloaded (utilization &gt; 100%). Shows which resources need immediate attention.
            </p>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={resourceUtilization} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 150]} label={{ value: 'Utilization %', position: 'insideBottom', offset: -5 }} />
                <YAxis dataKey="name" type="category" width={120} />
                <Tooltip formatter={(value: number) => `${value}%`} />
                <Legend />
                <Bar dataKey="value" name="Utilization %">
                  {resourceUtilization.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Risk Factors Breakdown */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-red-600" />
            Risk Factors Breakdown
          </h3>
          <p className="text-xs text-gray-600 mb-4">
            Common risk factors affecting activities. Shows which types of issues are most prevalent in your project.
          </p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={riskFactors}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" name="Number of Activities">
                {riskFactors.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Forecast Comparison */}
        {forecast && (
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              Forecast Comparison
            </h3>
            <p className="text-xs text-gray-600 mb-4">
              Project completion forecasts at different confidence levels. P50 is most likely, P80 is worst-case scenario.
            </p>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { name: 'P50 (Most Likely)', value: forecast.p50, fill: '#3b82f6' },
                { name: 'P80 (Worst Case)', value: forecast.p80, fill: '#ef4444' },
                ...(forecast.p90 ? [{ name: 'P90', value: forecast.p90, fill: '#dc2626' }] : []),
                ...(forecast.p95 ? [{ name: 'P95', value: forecast.p95, fill: '#991b1b' }] : []),
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis label={{ value: 'Days', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value: number) => `${value.toFixed(1)} days`} />
                <Legend />
                <Bar dataKey="value" name="Days to Completion">
                  {[
                    { fill: '#3b82f6' },
                    { fill: '#ef4444' },
                    ...(forecast.p90 ? [{ fill: '#dc2626' }] : []),
                    ...(forecast.p95 ? [{ fill: '#991b1b' }] : []),
                  ].map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Summary Section */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-600" />
          Dashboard Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-700 mb-2">
              <strong>Total Activities:</strong> {totalRisks || risks.length} activities are being monitored
            </p>
            <p className="text-gray-700 mb-2">
              <strong>High Risk Activities:</strong> {riskDistribution.find(r => r.name === 'High Risk')?.value || 0} activities require immediate attention
            </p>
            <p className="text-gray-700">
              <strong>Critical Path:</strong> {criticalPathData.find(r => r.name === 'On Critical Path')?.value || 0} activities are on the critical path
            </p>
          </div>
          <div>
            <p className="text-gray-700 mb-2">
              <strong>Resource Issues:</strong> {anomalies?.black_holes?.length || 0} resources are overloaded
            </p>
            <p className="text-gray-700 mb-2">
              <strong>Zombie Tasks:</strong> {anomalies?.zombie_tasks?.length || 0} tasks should have started but didn't
            </p>
            <p className="text-gray-700">
              <strong>Forecast:</strong> Project likely to complete in {forecast?.p50?.toFixed(0) || '—'} days (P50)
            </p>
          </div>
        </div>
      </div>
    </Layout>
  )
}

