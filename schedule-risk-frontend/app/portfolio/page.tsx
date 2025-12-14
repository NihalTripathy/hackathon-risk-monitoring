'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { 
  BarChart3, 
  TrendingUp, 
  AlertTriangle, 
  Users, 
  ArrowLeft, 
  RefreshCw,
  Activity,
  Shield,
  Zap,
  FolderOpen,
  Trash2,
  CheckSquare,
  Square
} from 'lucide-react'
import Navigation from '@/components/Navigation'
import { 
  getPortfolioSummary, 
  getPortfolioRisks, 
  getPortfolioResources,
  deleteProject,
  deleteSelectedProjects,
  deleteAllProjects,
  reAnalyzePortfolio,
  PortfolioSummary,
  PortfolioRisksResponse,
  PortfolioResourcesResponse
} from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'

export default function PortfolioPage() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null)
  const [risks, setRisks] = useState<PortfolioRisksResponse | null>(null)
  const [resources, setResources] = useState<PortfolioResourcesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'risks' | 'resources'>('overview')
  const [selectedProjects, setSelectedProjects] = useState<Set<string>>(new Set())
  const [deleting, setDeleting] = useState(false)
  const [showDeleteAllConfirm, setShowDeleteAllConfirm] = useState(false)
  const [reAnalyzing, setReAnalyzing] = useState(false)
  const router = useRouter()
  const { isAuthenticated, authLoading } = useAuth()

  // OPTIMIZATION: Memoize loadPortfolioData
  const loadPortfolioData = useCallback(async () => {
    // Check if token exists before making API calls
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        console.warn('[Portfolio] No token found, waiting for auth...')
        // Wait a bit for auth context to set token
        await new Promise(resolve => setTimeout(resolve, 500))
        const tokenAfterWait = localStorage.getItem('auth_token')
        if (!tokenAfterWait) {
          console.error('[Portfolio] Still no token after wait, redirecting to login')
          router.push('/login')
          return
        }
      }
    }

    try {
      setLoading(true)
      setError(null)
      
      const [summaryData, risksData, resourcesData] = await Promise.all([
        getPortfolioSummary(),
        getPortfolioRisks(undefined, 20),
        getPortfolioResources()
      ])
      
      setSummary(summaryData)
      setRisks(risksData)
      setResources(resourcesData)
    } catch (err: any) {
      console.error('[Portfolio] Error loading data:', err)
      
      // Don't logout on first 401 - might be a race condition
      if (err.response?.status === 401) {
        // Check if token exists - if not, it's a real auth issue
        const token = localStorage.getItem('auth_token')
        if (!token) {
          console.error('[Portfolio] 401 and no token - redirecting to login')
          router.push('/login')
          return
        }
        // If token exists, might be expired or invalid - show error but don't redirect immediately
        setError('Authentication failed. Please try refreshing the page.')
      } else {
        setError(err.response?.data?.detail || 'Failed to load portfolio data')
      }
    } finally {
      setLoading(false)
    }
  }, [router])

  useEffect(() => {
    // Wait for auth to finish loading before checking
    if (!authLoading) {
      if (!isAuthenticated) {
        router.push('/login')
        return
      }
      // Only load data after auth is confirmed
      loadPortfolioData()
    }
  }, [authLoading, isAuthenticated, router, loadPortfolioData])

  // Helper function (pure function, safe as regular function)
  const getRiskLevel = (score: number): { label: string; color: string; bgColor: string } => {
    if (score >= 70) return { label: 'High', color: 'text-red-700', bgColor: 'bg-red-100' }
    if (score >= 40) return { label: 'Medium', color: 'text-yellow-700', bgColor: 'bg-yellow-100' }
    return { label: 'Low', color: 'text-green-700', bgColor: 'bg-green-100' }
  }

  const handleToggleSelect = (projectId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedProjects(prev => {
      const next = new Set(prev)
      if (next.has(projectId)) {
        next.delete(projectId)
      } else {
        next.add(projectId)
      }
      return next
    })
  }

  const handleSelectAll = () => {
    if (summary && summary.high_risk_projects.length > 0) {
      const allIds = new Set(summary.high_risk_projects.map(p => p.project_id))
      if (selectedProjects.size === allIds.size) {
        setSelectedProjects(new Set())
      } else {
        setSelectedProjects(allIds)
      }
    }
  }

  const handleDeleteProject = async (projectId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm(`Are you sure you want to delete this project? This action cannot be undone.`)) {
      return
    }

    try {
      setDeleting(true)
      await deleteProject(projectId)
      // Remove from selected if it was selected
      setSelectedProjects(prev => {
        const next = new Set(prev)
        next.delete(projectId)
        return next
      })
      // Reload portfolio data
      await loadPortfolioData()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete project')
    } finally {
      setDeleting(false)
    }
  }

  const handleDeleteSelected = async () => {
    if (selectedProjects.size === 0) {
      setError('Please select at least one project to delete')
      return
    }

    if (!confirm(`Are you sure you want to delete ${selectedProjects.size} selected project(s)? This action cannot be undone.`)) {
      return
    }

    try {
      setDeleting(true)
      await deleteSelectedProjects(Array.from(selectedProjects))
      setSelectedProjects(new Set())
      await loadPortfolioData()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete projects')
    } finally {
      setDeleting(false)
    }
  }

  const handleDeleteAll = async () => {
    if (!showDeleteAllConfirm) {
      setShowDeleteAllConfirm(true)
      return
    }

    if (!confirm(`WARNING: This will delete ALL your projects (${summary?.total_projects || 0} projects). This action cannot be undone. Are you absolutely sure?`)) {
      setShowDeleteAllConfirm(false)
      return
    }

    try {
      setDeleting(true)
      await deleteAllProjects()
      setSelectedProjects(new Set())
      setShowDeleteAllConfirm(false)
      await loadPortfolioData()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete all projects')
      setShowDeleteAllConfirm(false)
    } finally {
      setDeleting(false)
    }
  }

  const handleReAnalyzePortfolio = async () => {
    if (!confirm(`This will re-analyze all ${summary?.total_projects || 0} projects in your portfolio. This may take a few minutes. Continue?`)) {
      return
    }

    try {
      setReAnalyzing(true)
      setError(null)
      const response = await reAnalyzePortfolio()
      console.log('[Portfolio] Re-analysis started:', response.message)
      
      // Show success message
      alert(response.message + '\n\n' + response.note)
      
      // Reload data after a short delay to show updated status
      setTimeout(() => {
        loadPortfolioData()
      }, 2000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to re-analyze portfolio')
    } finally {
      setReAnalyzing(false)
    }
  }

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-gray-500">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <Navigation />

      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-primary-600 rounded-lg">
                  <BarChart3 className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-xl font-bold text-gray-900">Portfolio Dashboard</h1>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {selectedProjects.size > 0 && (
                <button
                  onClick={handleDeleteSelected}
                  disabled={deleting}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete Selected ({selectedProjects.size})
                </button>
              )}
              {summary && summary.total_projects > 0 && (
                <button
                  onClick={handleDeleteAll}
                  disabled={deleting}
                  className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    showDeleteAllConfirm
                      ? 'text-white bg-red-600 hover:bg-red-700'
                      : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
                  } disabled:opacity-50`}
                >
                  <Trash2 className="w-4 h-4" />
                  {showDeleteAllConfirm ? 'Confirm Delete All' : 'Delete All'}
                </button>
              )}
              {summary && summary.total_projects > 0 && (
                <button
                  onClick={handleReAnalyzePortfolio}
                  disabled={reAnalyzing || loading}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:opacity-50 transition-colors"
                  title="Re-analyze all projects to update portfolio data with latest logic changes"
                >
                  <RefreshCw className={`w-4 h-4 ${reAnalyzing ? 'animate-spin' : ''}`} />
                  {reAnalyzing ? 'Re-analyzing...' : 'Re-analyze Portfolio'}
                </button>
              )}
              <button
                onClick={loadPortfolioData}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
            {error}
          </div>
        )}

        {loading && !summary ? (
          <div className="text-center py-12">
            <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm text-gray-500">Loading portfolio data...</p>
          </div>
        ) : summary ? (
          <>
            {/* Summary Cards */}
            <div className="grid md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-600">Total Projects</span>
                  <FolderOpen className="w-4 h-4 text-gray-400" />
                </div>
                <p className="text-2xl font-bold text-gray-900">{summary.total_projects}</p>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-600">Total Activities</span>
                  <Activity className="w-4 h-4 text-gray-400" />
                </div>
                <p className="text-2xl font-bold text-gray-900">{summary.total_activities}</p>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-600">Portfolio Risk</span>
                  <Shield className="w-4 h-4 text-gray-400" />
                </div>
                <p className="text-2xl font-bold text-gray-900">{summary.portfolio_risk_score.toFixed(1)}</p>
                <p className="text-xs text-gray-500 mt-1">Avg risk score</p>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-600">Projects at Risk</span>
                  <AlertTriangle className="w-4 h-4 text-gray-400" />
                </div>
                <p className="text-2xl font-bold text-gray-900">{summary.projects_at_risk}</p>
                <p className="text-xs text-gray-500 mt-1">Risk score ≥ 50</p>
              </div>
            </div>

            {/* Tabs */}
            <div className="bg-white border border-gray-200 rounded-lg mb-6">
              <div className="border-b border-gray-200">
                <nav className="flex -mb-px">
                  <button
                    onClick={() => setActiveTab('overview')}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'overview'
                        ? 'border-primary-600 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Overview
                  </button>
                  <button
                    onClick={() => setActiveTab('risks')}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'risks'
                        ? 'border-primary-600 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Top Risks
                  </button>
                  <button
                    onClick={() => setActiveTab('resources')}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'resources'
                        ? 'border-primary-600 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Resources
                  </button>
                </nav>
              </div>

              <div className="p-6">
                {/* Overview Tab */}
                {activeTab === 'overview' && (
                  <div className="space-y-6">
                    {/* High Risk Projects */}
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-red-600" />
                          High Risk Projects
                        </h3>
                        {summary.high_risk_projects.length > 0 && (
                          <button
                            onClick={handleSelectAll}
                            className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-900"
                          >
                            {selectedProjects.size === summary.high_risk_projects.length ? (
                              <CheckSquare className="w-4 h-4" />
                            ) : (
                              <Square className="w-4 h-4" />
                            )}
                            {selectedProjects.size === summary.high_risk_projects.length ? 'Deselect All' : 'Select All'}
                          </button>
                        )}
                      </div>
                      {summary.high_risk_projects.length > 0 ? (
                        <div className="space-y-2">
                          {summary.high_risk_projects.map((project) => {
                            const riskLevel = getRiskLevel(project.risk_score)
                            const isSelected = selectedProjects.has(project.project_id)
                            return (
                              <div
                                key={project.project_id}
                                className={`flex items-center justify-between p-3 border rounded-lg transition-colors ${
                                  isSelected
                                    ? 'bg-primary-50 border-primary-400'
                                    : 'bg-gray-50 border-gray-200 hover:border-primary-400 hover:bg-primary-50'
                                }`}
                              >
                                <div 
                                  className="flex items-center gap-3 flex-1 min-w-0 cursor-pointer"
                                  onClick={() => router.push(`/projects/${project.project_id}`)}
                                >
                                  <button
                                    onClick={(e) => handleToggleSelect(project.project_id, e)}
                                    className="flex-shrink-0 text-primary-600 hover:text-primary-700"
                                  >
                                    {isSelected ? (
                                      <CheckSquare className="w-5 h-5" />
                                    ) : (
                                      <Square className="w-5 h-5" />
                                    )}
                                  </button>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-gray-900 truncate">
                                      {project.filename || project.project_id}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-1">
                                      {project.activity_count} activities
                                    </p>
                                  </div>
                                </div>
                                <div className="flex items-center gap-3">
                                  <span className={`px-2 py-1 text-xs font-medium rounded ${riskLevel.bgColor} ${riskLevel.color}`}>
                                    {riskLevel.label}
                                  </span>
                                  <span className="text-sm font-semibold text-gray-900">
                                    {project.risk_score.toFixed(1)}
                                  </span>
                                  <button
                                    onClick={(e) => handleDeleteProject(project.project_id, e)}
                                    disabled={deleting}
                                    className="flex-shrink-0 p-1.5 text-red-600 hover:text-red-700 hover:bg-red-50 rounded disabled:opacity-50 transition-colors"
                                    title="Delete project"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No high-risk projects found.</p>
                      )}
                    </div>

                    {/* Resource Summary */}
                    <div>
                      <h3 className="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <Users className="w-4 h-4 text-blue-600" />
                        Resource Allocation Summary
                      </h3>
                      {Object.keys(summary.resource_summary).length > 0 ? (
                        <div className="grid md:grid-cols-2 gap-3">
                          {Object.entries(summary.resource_summary).slice(0, 6).map(([resourceId, data]) => (
                            <div
                              key={resourceId}
                              className="p-3 bg-gray-50 border border-gray-200 rounded-lg"
                            >
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-xs font-medium text-gray-900 truncate">{resourceId}</span>
                                {data.is_overallocated && (
                                  <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded">
                                    Over
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-2 text-xs text-gray-600">
                                <span>{data.total_fte.toFixed(1)} / {data.max_fte.toFixed(1)} FTE</span>
                                <span className="text-gray-400">•</span>
                                <span>{data.utilization_pct.toFixed(1)}%</span>
                                <span className="text-gray-400">•</span>
                                <span>{data.project_count} projects</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No resource data available.</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Risks Tab */}
                {activeTab === 'risks' && risks && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between mb-4">
                      <p className="text-sm text-gray-600">
                        Showing top {risks.top_risks.length} of {risks.total_risks} risks across {risks.projects_analyzed} projects
                      </p>
                    </div>
                    {risks.top_risks.length > 0 ? (
                      <div className="space-y-2">
                        {risks.top_risks.map((risk, index) => {
                          const riskLevel = getRiskLevel(risk.risk_score)
                          return (
                            <div
                              key={`${risk.project_id}-${risk.activity_id}`}
                              onClick={() => router.push(`/projects/${risk.project_id}/activities/${risk.activity_id}`)}
                              className="p-4 bg-gray-50 border border-gray-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 cursor-pointer transition-colors"
                            >
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xs font-medium text-gray-500">#{index + 1}</span>
                                    <span className="text-sm font-semibold text-gray-900 truncate">{risk.name}</span>
                                  </div>
                                  <p className="text-xs text-gray-600 truncate">
                                    {risk.project_filename || risk.project_id}
                                  </p>
                                </div>
                                <div className="flex items-center gap-3 ml-4">
                                  <span className={`px-2 py-1 text-xs font-medium rounded ${riskLevel.bgColor} ${riskLevel.color}`}>
                                    {riskLevel.label}
                                  </span>
                                  <span className="text-sm font-bold text-gray-900">
                                    {risk.risk_score.toFixed(1)}
                                  </span>
                                </div>
                              </div>
                              {risk.percent_complete !== undefined && (
                                <div className="mt-2">
                                  <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                                    <span>Progress</span>
                                    <span>{risk.percent_complete}%</span>
                                  </div>
                                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                                    <div
                                      className="bg-primary-600 h-1.5 rounded-full"
                                      style={{ width: `${risk.percent_complete}%` }}
                                    />
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500">No risks found.</p>
                    )}
                  </div>
                )}

                {/* Resources Tab */}
                {activeTab === 'resources' && resources && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between mb-4">
                      <p className="text-sm text-gray-600">
                        {resources.total_resources} resources • {resources.overallocated_resources} overallocated
                      </p>
                    </div>
                    {Object.keys(resources.resources).length > 0 ? (
                      <div className="space-y-3">
                        {Object.entries(resources.resources).map(([resourceId, data]) => (
                          <div
                            key={resourceId}
                            className="p-4 bg-gray-50 border border-gray-200 rounded-lg"
                          >
                            <div className="flex items-center justify-between mb-3">
                              <div>
                                <h4 className="text-sm font-semibold text-gray-900">{resourceId}</h4>
                                <p className="text-xs text-gray-600 mt-1">
                                  {data.activity_count} activities across {data.project_count} projects
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="text-sm font-semibold text-gray-900">
                                  {data.total_fte.toFixed(1)} / {data.max_fte.toFixed(1)} FTE
                                </p>
                                <p className={`text-xs font-medium ${
                                  data.is_overallocated ? 'text-red-600' : 'text-gray-600'
                                }`}>
                                  {data.utilization_pct.toFixed(1)}% utilized
                                </p>
                              </div>
                            </div>
                            {data.allocations.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-gray-200">
                                <p className="text-xs font-medium text-gray-700 mb-2">Recent Allocations:</p>
                                <div className="space-y-1">
                                  {data.allocations.slice(0, 3).map((alloc, idx) => (
                                    <div key={idx} className="flex items-center justify-between text-xs text-gray-600">
                                      <span className="truncate flex-1">{alloc.activity_name}</span>
                                      <span className="ml-2">{alloc.fte.toFixed(1)} FTE</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500">No resource data available.</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-12">
            <p className="text-sm text-gray-500">No portfolio data available.</p>
          </div>
        )}
      </div>
    </div>
  )
}

