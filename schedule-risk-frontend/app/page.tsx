'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Upload, FileText, TrendingUp, Shield, ArrowRight, Zap, BarChart3, CheckCircle2, Sparkles, Clock, FolderOpen, LogOut, User, Layers, Trash2, CheckSquare, Square } from 'lucide-react'
import axios from 'axios'
import { getProjects, ProjectInfo, uploadProject, setAuthToken, deleteProject, deleteSelectedProjects, deleteAllProjects } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import Navigation from '@/components/Navigation'
import { formatDateTimeDDMMYYYY } from '@/lib/dateUtils'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api'

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [projects, setProjects] = useState<ProjectInfo[]>([])
  const [loadingProjects, setLoadingProjects] = useState(true)
  const [selectedProjects, setSelectedProjects] = useState<Set<string>>(new Set())
  const [deleting, setDeleting] = useState(false)
  const [showDeleteAllConfirm, setShowDeleteAllConfirm] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()
  const { user, loading: authLoading, isAuthenticated, logout } = useAuth()

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) {
      // Add a small delay to ensure token is available
      const timer = setTimeout(() => {
        loadProjects()
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [isAuthenticated])

  const loadProjects = async () => {
    try {
      setLoadingProjects(true)
      // Verify token exists before making request
      const token = localStorage.getItem('auth_token')
      if (!token) {
        console.warn('[Home] No auth token found, redirecting to login')
        router.push('/login')
        return
      }
      console.log('[Home] Loading projects with token:', token.substring(0, 20) + '...')
      const data = await getProjects(20)
      setProjects(data.projects)
    } catch (err: any) {
      console.error('[Home] Failed to load projects:', err)
      console.error('[Home] Error details:', {
        status: err.response?.status,
        data: err.response?.data,
        headers: err.config?.headers
      })
      // If 401, let the interceptor handle it, but don't show error
      if (err.response?.status === 401) {
        // Token is invalid, will be handled by interceptor
        console.error('[Home] 401 Unauthorized - token may be invalid')
        return
      }
      setError('Failed to load projects. Please try again.')
    } finally {
      setLoadingProjects(false)
    }
  }


  const handleProjectClick = (projectId: string) => {
    router.push(`/projects/${projectId}`)
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
    if (projects.length > 0) {
      const allIds = new Set(projects.map(p => p.project_id))
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
      setSelectedProjects(prev => {
        const next = new Set(prev)
        next.delete(projectId)
        return next
      })
      await loadProjects()
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
      await loadProjects()
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

    if (!confirm(`WARNING: This will delete ALL your projects (${projects.length} projects). This action cannot be undone. Are you absolutely sure?`)) {
      setShowDeleteAllConfirm(false)
      return
    }

    try {
      setDeleting(true)
      await deleteAllProjects()
      setSelectedProjects(new Set())
      setShowDeleteAllConfirm(false)
      await loadProjects()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete all projects')
      setShowDeleteAllConfirm(false)
    } finally {
      setDeleting(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile)
        setError(null)
      } else {
        setError('Please upload a CSV file')
      }
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a CSV file')
      return
    }

    setUploading(true)
    setError(null)

    try {
      const response = await uploadProject(file)

      if (response.project_id) {
        // Reload projects list after successful upload
        await loadProjects()
        router.push(`/projects/${response.project_id}`)
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        // Token expired or invalid
        logout()
        router.push('/login')
      } else {
        setError(err.response?.data?.detail || 'Failed to upload file. Please try again.')
        setUploading(false)
      }
    }
  }

  // Show loading or nothing while checking auth
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
    <div className="min-h-screen bg-white">
      {/* Top Navigation Bar */}
      <Navigation />

      {/* Main Content - Two Column Layout */}
      <div className="container mx-auto px-4 py-6">
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left Column - Main Upload Area (2/3 width) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Hero Section */}
            <div className="bg-gradient-to-br from-primary-600 to-blue-700 rounded-lg p-6 text-white">
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-2xl font-bold mb-2">Schedule Risk Monitoring</h1>
                  <p className="text-sm text-primary-100 opacity-90">
                    Advanced project risk analysis, forecasting, and mitigation planning
                  </p>
                </div>
                <Zap className="w-8 h-8 text-yellow-300 flex-shrink-0" />
              </div>
            </div>

            {/* Upload Card */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Upload Project CSV</h2>
              
              {/* Drag and Drop Area */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
                  isDragging
                    ? 'border-primary-500 bg-primary-50'
                    : file
                    ? 'border-green-300 bg-green-50'
                    : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <div className="flex flex-col items-center gap-3">
                  <div className={`p-3 rounded-lg ${
                    file ? 'bg-green-500' : 'bg-primary-100'
                  }`}>
                    <Upload className={`w-6 h-6 ${file ? 'text-white' : 'text-primary-600'}`} />
                  </div>
                  {file ? (
                    <>
                      <div className="flex items-center gap-2">
                        <FileText className="w-5 h-5 text-green-600" />
                        <span className="text-sm font-semibold text-gray-900">{file.name}</span>
                      </div>
                      <span className="text-xs text-gray-500">{(file.size / 1024).toFixed(2)} KB</span>
                      <span className="text-xs text-gray-500">Click to change file</span>
                    </>
                  ) : (
                    <>
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-1">
                          Drag and drop your CSV file here
                        </p>
                        <p className="text-xs text-gray-500">or click to browse</p>
                      </div>
                      <button className="text-xs text-primary-600 hover:text-primary-700 font-medium">
                        Select CSV File
                      </button>
                    </>
                  )}
                </div>
              </div>

              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-800">
                  {error}
                </div>
              )}

              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium bg-primary-600 hover:bg-primary-700 text-white rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Uploading & Analyzing...</span>
                  </>
                ) : (
                  <>
                    <span>Upload & Analyze</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
              
            </div>

            {/* Portfolio Quick Access Card */}
            {projects.length > 0 && (
              <div 
                onClick={() => router.push('/portfolio')}
                className="bg-gradient-to-br from-purple-600 to-indigo-700 rounded-lg p-6 text-white cursor-pointer hover:shadow-lg transition-all group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Layers className="w-5 h-5" />
                      <h3 className="text-lg font-bold">Portfolio Dashboard</h3>
                    </div>
                    <p className="text-sm text-purple-100 opacity-90">
                      View all projects, aggregate risks, and resource allocation across your portfolio
                    </p>
                  </div>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </div>
                <div className="flex items-center gap-4 mt-4 pt-4 border-t border-purple-400/30">
                  <div>
                    <p className="text-xs text-purple-200">Total Projects</p>
                    <p className="text-xl font-bold">{projects.length}</p>
                  </div>
                  <div>
                    <p className="text-xs text-purple-200">Total Activities</p>
                    <p className="text-xl font-bold">
                      {projects.reduce((sum, p) => sum + (p.activity_count || 0), 0)}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Features Grid */}
            <div className="grid md:grid-cols-3 gap-4">
              <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mb-3">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                </div>
                <h3 className="text-sm font-bold text-gray-900 mb-2">Monte Carlo Forecasting</h3>
                <p className="text-xs text-gray-600 leading-relaxed">
                  P50 and P80 completion forecasts with confidence intervals
                </p>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center mb-3">
                  <Shield className="w-5 h-5 text-red-600" />
                </div>
                <h3 className="text-sm font-bold text-gray-900 mb-2">Risk Analysis</h3>
                <p className="text-xs text-gray-600 leading-relaxed">
                  AI-powered risk identification and scoring
                </p>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mb-3">
                  <FileText className="w-5 h-5 text-green-600" />
                </div>
                <h3 className="text-sm font-bold text-gray-900 mb-2">Audit Trail</h3>
                <p className="text-xs text-gray-600 leading-relaxed">
                  Complete log of all project actions and changes
                </p>
              </div>
            </div>

            {/* Past Projects Section */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <FolderOpen className="w-5 h-5 text-primary-600" />
                  Recent Projects
                </h2>
                <div className="flex items-center gap-2">
                  {selectedProjects.size > 0 && (
                    <button
                      onClick={handleDeleteSelected}
                      disabled={deleting}
                      className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
                    >
                      <Trash2 className="w-3 h-3" />
                      Delete ({selectedProjects.size})
                    </button>
                  )}
                  {projects.length > 0 && (
                    <button
                      onClick={handleDeleteAll}
                      disabled={deleting}
                      className={`flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                        showDeleteAllConfirm
                          ? 'text-white bg-red-600 hover:bg-red-700'
                          : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
                      } disabled:opacity-50`}
                    >
                      <Trash2 className="w-3 h-3" />
                      {showDeleteAllConfirm ? 'Confirm' : 'Delete All'}
                    </button>
                  )}
                  <button
                    onClick={loadProjects}
                    disabled={loadingProjects}
                    className="text-xs text-primary-600 hover:text-primary-700 font-medium disabled:opacity-50"
                  >
                    {loadingProjects ? 'Loading...' : 'Refresh'}
                  </button>
                </div>
              </div>
              
              {loadingProjects ? (
                <div className="text-center py-8">
                  <div className="w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                  <p className="text-xs text-gray-500">Loading projects...</p>
                </div>
              ) : projects.length > 0 ? (
                <>
                  <div className="mb-3 flex items-center justify-between">
                    <button
                      onClick={handleSelectAll}
                      className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-900"
                    >
                      {selectedProjects.size === projects.length ? (
                        <CheckSquare className="w-4 h-4" />
                      ) : (
                        <Square className="w-4 h-4" />
                      )}
                      {selectedProjects.size === projects.length ? 'Deselect All' : 'Select All'}
                    </button>
                  </div>
                  <div className="grid md:grid-cols-2 gap-3">
                    {projects.map((project) => {
                      const isSelected = selectedProjects.has(project.project_id)
                      return (
                        <div
                          key={project.project_id}
                          className={`border rounded-lg p-4 transition-all ${
                            isSelected
                              ? 'bg-primary-50 border-primary-400'
                              : 'border-gray-200 hover:border-primary-400 hover:shadow-md'
                          }`}
                        >
                          <div 
                            className="flex items-start justify-between mb-2 cursor-pointer group"
                            onClick={() => handleProjectClick(project.project_id)}
                          >
                            <div className="flex items-center gap-2 flex-1 min-w-0">
                              <button
                                onClick={(e) => handleToggleSelect(project.project_id, e)}
                                className="flex-shrink-0 text-primary-600 hover:text-primary-700"
                              >
                                {isSelected ? (
                                  <CheckSquare className="w-4 h-4" />
                                ) : (
                                  <Square className="w-4 h-4" />
                                )}
                              </button>
                              <div className="flex-1 min-w-0">
                                <h3 className={`text-sm font-semibold truncate transition-colors ${
                                  isSelected ? 'text-primary-900' : 'text-gray-900 group-hover:text-primary-600'
                                }`}>
                                  {project.filename}
                                </h3>
                                <p className="text-xs text-gray-500 mt-1">
                                  {project.activity_count} activities
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0">
                              <button
                                onClick={(e) => handleDeleteProject(project.project_id, e)}
                                disabled={deleting}
                                className="p-1.5 text-red-600 hover:text-red-700 hover:bg-red-50 rounded disabled:opacity-50 transition-colors"
                                title="Delete project"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                              <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-primary-600 transition-colors" />
                            </div>
                          </div>
                          <div className="flex items-center gap-2 text-xs text-gray-500 mt-2">
                            <Clock className="w-3 h-3" />
                            <span>{formatDateTimeDDMMYYYY(project.created_at)}</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">No projects yet. Upload your first CSV file above!</p>
                </div>
              )}
            </div>
          </div>

          {/* Right Sidebar - Quick Info (1/3 width) */}
          <div className="lg:col-span-1 space-y-4">
            {/* Portfolio Quick Access - Only show if user has projects */}
            {projects.length > 0 && (
              <div 
                onClick={() => router.push('/portfolio')}
                className="bg-gradient-to-br from-purple-600 to-indigo-700 rounded-lg p-4 text-white cursor-pointer hover:shadow-lg transition-all group"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Layers className="w-5 h-5" />
                    <h3 className="text-sm font-bold">Portfolio View</h3>
                  </div>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
                <p className="text-xs text-purple-100 opacity-90 mb-3">
                  View all projects, risks, and resources in one dashboard
                </p>
                <div className="flex items-center gap-3 pt-3 border-t border-purple-400/30">
                  <div>
                    <p className="text-xs text-purple-200">Projects</p>
                    <p className="text-lg font-bold">{projects.length}</p>
                  </div>
                  <div>
                    <p className="text-xs text-purple-200">Activities</p>
                    <p className="text-lg font-bold">
                      {projects.reduce((sum, p) => sum + (p.activity_count || 0), 0)}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Quick Stats Card */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary-600" />
                Key Features
              </h3>
              <ul className="space-y-2">
                <li className="flex items-start gap-2 text-xs text-gray-700">
                  <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                  <span>Real-time risk scoring</span>
                </li>
                <li className="flex items-start gap-2 text-xs text-gray-700">
                  <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                  <span>AI-powered explanations</span>
                </li>
                <li className="flex items-start gap-2 text-xs text-gray-700">
                  <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                  <span>What-if simulations</span>
                </li>
                <li className="flex items-start gap-2 text-xs text-gray-700">
                  <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                  <span>Comprehensive audit logs</span>
                </li>
              </ul>
            </div>

            {/* How It Works */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-bold text-gray-900 mb-3">How It Works</h3>
              <ol className="space-y-3">
                <li className="flex gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xs font-bold">
                    1
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-900">Upload CSV</p>
                    <p className="text-xs text-gray-600">Upload your project schedule file</p>
                  </div>
                </li>
                <li className="flex gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xs font-bold">
                    2
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-900">Analyze</p>
                    <p className="text-xs text-gray-600">AI analyzes risks and forecasts</p>
                  </div>
                </li>
                <li className="flex gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xs font-bold">
                    3
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-900">Review</p>
                    <p className="text-xs text-gray-600">View detailed risk insights</p>
                  </div>
                </li>
              </ol>
            </div>

            {/* Info Card */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-xs font-bold text-blue-900 mb-2">CSV Format</h3>
              <p className="text-xs text-blue-800 mb-2">
                Your CSV should include:
              </p>
              <ul className="text-xs text-blue-700 space-y-1">
                <li>• Activity ID</li>
                <li>• Activity Name</li>
                <li>• Duration</li>
                <li>• Dependencies (optional)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

