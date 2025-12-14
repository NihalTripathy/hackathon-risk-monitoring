'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import { ArrowLeft, Loader2, Calendar, AlertTriangle, TrendingUp } from 'lucide-react'
import { getGanttData, type GanttTask } from '@/lib/api'

export default function GanttChartPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string

  const [tasks, setTasks] = useState<GanttTask[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTask, setSelectedTask] = useState<GanttTask | null>(null)

  // Store current path for settings page navigation
  useEffect(() => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('lastPath', `/projects/${projectId}/gantt`)
      sessionStorage.setItem('lastProjectId', projectId)
    }
  }, [projectId])

  useEffect(() => {
    loadGanttData()
  }, [projectId])

  const loadGanttData = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getGanttData(projectId)
      // Ensure data is an array
      setTasks(Array.isArray(data) ? data : [])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load Gantt chart data')
      setTasks([]) // Set empty array on error
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'high':
        return 'bg-red-500'
      case 'medium':
        return 'bg-yellow-500'
      default:
        return 'bg-green-500'
    }
  }

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const formatDateForTimeline = (date: Date) => {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const formatMonthYear = (date: Date) => {
    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
  }

  const calculateDays = (start: string, end: string) => {
    try {
      const startDate = new Date(start)
      const endDate = new Date(end)
      return Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24))
    } catch {
      return 0
    }
  }

  // Calculate timeline bounds - ensure tasks is an array
  const tasksArray = Array.isArray(tasks) ? tasks : []
  const allDates = tasksArray.flatMap(t => [t.start, t.end]).filter(Boolean)
  const minDate = allDates.length > 0 ? new Date(Math.min(...allDates.map(d => new Date(d).getTime()))) : new Date()
  const maxDate = allDates.length > 0 ? new Date(Math.max(...allDates.map(d => new Date(d).getTime()))) : new Date()
  const totalDays = Math.ceil((maxDate.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24)) || 1
  
  // Determine timeline scale based on project duration
  const isLongProject = totalDays > 180 // More than 6 months
  const timelineScale = isLongProject ? 'month' : totalDays > 90 ? 'biweekly' : 'week'
  
  // Calculate minimum timeline width to ensure bars are visible
  const minTimelineWidth = Math.max(800, totalDays * 2) // At least 2px per day

  if (loading) {
    return (
      <Layout projectId={projectId}>
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout projectId={projectId}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </Layout>
    )
  }

  return (
    <Layout projectId={projectId}>
      <div className="mb-4">
        <button
          onClick={() => router.push(`/projects/${projectId}`)}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </button>
        <h1 className="text-2xl font-bold text-gray-900">Gantt Chart</h1>
        <p className="text-sm text-gray-600 mt-1">Timeline view of project activities with risk indicators</p>
      </div>

      {tasksArray.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-600">No activities found for Gantt chart</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          {/* Legend */}
          <div className="flex items-center gap-4 mb-4 pb-4 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-500 rounded"></div>
              <span className="text-xs text-gray-600">High Risk</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-yellow-500 rounded"></div>
              <span className="text-xs text-gray-600">Medium Risk</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded"></div>
              <span className="text-xs text-gray-600">Low Risk</span>
            </div>
            <div className="flex items-center gap-2 ml-auto">
              <div className="w-4 h-4 border-2 border-red-500 border-dashed"></div>
              <span className="text-xs text-gray-600">Critical Path</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span>Timeline: {formatDateForTimeline(minDate)} - {formatDateForTimeline(maxDate)}</span>
              <span className="text-gray-400">({totalDays} days)</span>
            </div>
          </div>

          {/* Scrollable Gantt Chart Container */}
          <div className="overflow-x-auto" style={{ minWidth: '100%' }}>
            <div style={{ minWidth: `${minTimelineWidth}px` }}>
              {/* Gantt Chart */}
              <div className="space-y-2">
            {tasksArray.map((task) => {
              const startDate = new Date(task.start)
              const endDate = new Date(task.end)
              const daysFromStart = Math.max(0, Math.ceil((startDate.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24)))
              const taskDuration = Math.max(1, calculateDays(task.start, task.end))
              const leftPx = (daysFromStart / totalDays) * minTimelineWidth
              const widthPx = Math.max((taskDuration / totalDays) * minTimelineWidth, 4)

              return (
                <div
                  key={task.id}
                  className="relative h-16 border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer"
                  onClick={() => setSelectedTask(selectedTask?.id === task.id ? null : task)}
                >
                  {/* Task Info */}
                  <div className="absolute left-0 top-0 h-full flex items-center px-3 bg-white border-r border-gray-200 min-w-[200px] z-10">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-mono text-xs text-gray-500">{task.id}</span>
                        {task.on_critical_path && (
                          <span className="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded">
                            Critical
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-gray-900 truncate">{task.name}</p>
                      <div className="flex items-center gap-3 mt-1 text-xs text-gray-600">
                        <span>{formatDate(task.start)} - {formatDate(task.end)}</span>
                        {task.progress > 0 && (
                          <span>{task.progress}% complete</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Timeline Bar */}
                  <div className="ml-[200px] relative h-full" style={{ minWidth: `${minTimelineWidth}px` }}>
                    <div
                      className={`absolute top-1/2 -translate-y-1/2 h-8 rounded ${getRiskColor(task.risk_level)} ${
                        task.on_critical_path ? 'border-2 border-red-600 border-dashed' : ''
                      }`}
                      style={{
                        left: `${leftPx}px`,
                        width: `${widthPx}px`,
                        minWidth: '4px',
                      }}
                      title={`${task.name} (${task.risk_level} risk) - ${taskDuration} days`}
                    >
                      {/* Progress indicator */}
                      {task.progress > 0 && (
                        <div
                          className="absolute left-0 top-0 h-full bg-black/20 rounded"
                          style={{ width: `${task.progress}%` }}
                        />
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
              </div>

              {/* Timeline Header */}
              <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="ml-[200px] relative h-12" style={{ minWidth: `${minTimelineWidth}px` }}>
              {timelineScale === 'month' ? (
                // Monthly markers for long projects
                (() => {
                  const markers = []
                  let currentDate = new Date(minDate)
                  currentDate.setDate(1) // Start of month
                  
                  while (currentDate <= maxDate) {
                    const daysFromStart = Math.ceil((currentDate.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24))
                    const leftPos = (daysFromStart / totalDays) * minTimelineWidth
                    
                    markers.push(
                      <div
                        key={currentDate.toISOString()}
                        className="absolute top-0 border-l-2 border-gray-400 text-xs text-gray-700 font-medium pl-1"
                        style={{ left: `${leftPos}px` }}
                      >
                        <div>{formatMonthYear(currentDate)}</div>
                      </div>
                    )
                    
                    // Move to next month
                    currentDate = new Date(currentDate)
                    currentDate.setMonth(currentDate.getMonth() + 1)
                  }
                  
                  // Add week markers within current month
                  const currentMonthStart = new Date(minDate)
                  currentMonthStart.setDate(1)
                  let weekDate = new Date(currentMonthStart)
                  
                  while (weekDate <= maxDate) {
                    const daysFromStart = Math.ceil((weekDate.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24))
                    const leftPos = (daysFromStart / totalDays) * minTimelineWidth
                    
                    markers.push(
                      <div
                        key={`week-${weekDate.toISOString()}`}
                        className="absolute top-6 border-l border-gray-200 text-[10px] text-gray-500 pl-0.5"
                        style={{ left: `${leftPos}px` }}
                      >
                        {weekDate.getDate()}
                      </div>
                    )
                    
                    weekDate = new Date(weekDate)
                    weekDate.setDate(weekDate.getDate() + 7)
                  }
                  
                  return markers
                })()
              ) : timelineScale === 'biweekly' ? (
                // Bi-weekly markers for medium projects
                Array.from({ length: Math.ceil(totalDays / 14) }).map((_, biweekIdx) => {
                  const biweekStart = new Date(minDate)
                  biweekStart.setDate(biweekStart.getDate() + biweekIdx * 14)
                  const daysFromStart = biweekIdx * 14
                  const leftPos = (daysFromStart / totalDays) * minTimelineWidth
                  
                  return (
                    <div
                      key={biweekIdx}
                      className="absolute top-0 border-l border-gray-300 text-xs text-gray-600 pl-1"
                      style={{ left: `${leftPos}px` }}
                    >
                      {formatDateForTimeline(biweekStart)}
                    </div>
                  )
                })
              ) : (
                // Weekly markers for short projects
                Array.from({ length: Math.ceil(totalDays / 7) }).map((_, weekIdx) => {
                  const weekStart = new Date(minDate)
                  weekStart.setDate(weekStart.getDate() + weekIdx * 7)
                  const daysFromStart = weekIdx * 7
                  const leftPos = (daysFromStart / totalDays) * minTimelineWidth
                  
                  return (
                    <div
                      key={weekIdx}
                      className="absolute top-0 border-l border-gray-300 text-xs text-gray-600 pl-1"
                      style={{ left: `${leftPos}px` }}
                    >
                      {formatDateForTimeline(weekStart)}
                    </div>
                  )
                })
              )}
            </div>
          </div>
            </div>
          </div>
        </div>
      )}

      {/* Task Details Modal */}
      {selectedTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => setSelectedTask(null)}>
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-900 mb-4">{selectedTask.name}</h3>
            <div className="space-y-3 text-sm">
              <div>
                <span className="font-medium text-gray-700">Task ID:</span>
                <span className="ml-2 font-mono text-gray-900">{selectedTask.id}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Duration:</span>
                <span className="ml-2 text-gray-900">
                  {formatDate(selectedTask.start)} - {formatDate(selectedTask.end)}
                </span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Progress:</span>
                <span className="ml-2 text-gray-900">{selectedTask.progress}%</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Risk Level:</span>
                <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${
                  selectedTask.risk_level === 'High' ? 'bg-red-100 text-red-700' :
                  selectedTask.risk_level === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-green-100 text-green-700'
                }`}>
                  {selectedTask.risk_level}
                </span>
                <span className="ml-2 text-gray-600">({selectedTask.risk_score.toFixed(1)})</span>
              </div>
              {selectedTask.on_critical_path && (
                <div className="flex items-center gap-2 text-red-600">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="font-medium">On Critical Path</span>
                </div>
              )}
              {selectedTask.float_days !== undefined && (
                <div>
                  <span className="font-medium text-gray-700">Float:</span>
                  <span className="ml-2 text-gray-900">{selectedTask.float_days.toFixed(1)} days</span>
                </div>
              )}
              {selectedTask.resource_id && (
                <div>
                  <span className="font-medium text-gray-700">Resource:</span>
                  <span className="ml-2 text-gray-900">{selectedTask.resource_id}</span>
                </div>
              )}
              {selectedTask.dependencies && selectedTask.dependencies.length > 0 && (
                <div>
                  <span className="font-medium text-gray-700">Dependencies:</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {selectedTask.dependencies.map((dep) => (
                      <span key={dep} className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                        {dep}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <button
              onClick={() => router.push(`/projects/${projectId}/activities/${selectedTask.id}`)}
              className="mt-4 w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              View Full Details
            </button>
          </div>
        </div>
      )}
    </Layout>
  )
}

