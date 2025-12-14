import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token to every request
api.interceptors.request.use(
  (config) => {
    // Only run in browser environment
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
        // Debug logging (remove in production)
        if (process.env.NODE_ENV === 'development') {
          console.log('[API] Adding token to request:', config.url, token.substring(0, 20) + '...')
        }
      } else {
        // Remove authorization header if no token
        delete config.headers.Authorization
        if (process.env.NODE_ENV === 'development') {
          console.warn('[API] No token found for request:', config.url)
        }
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle 401 errors (unauthorized)
let isRedirecting = false

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Don't redirect for auth endpoints (login, register, me)
      const url = error.config?.url || ''
      const isAuthEndpoint = 
        url.includes('/auth/login') || 
        url.includes('/auth/register') || 
        url.includes('/auth/me')
      
      if (!isAuthEndpoint && typeof window !== 'undefined' && !isRedirecting) {
        // Check if we're on a page that might be loading (portfolio, projects)
        // Give it a chance to handle the error itself
        const currentPath = window.location.pathname
        const isProtectedPage = currentPath.startsWith('/portfolio') || currentPath.startsWith('/projects')
        
        // For protected pages, let them handle the error first
        // Only auto-redirect if we're sure it's a real auth failure
        if (isProtectedPage) {
          // Check if token exists - if not, it's definitely an auth issue
          const token = localStorage.getItem('auth_token')
          if (!token) {
            // No token at all - clear and redirect
            localStorage.removeItem('auth_token')
            delete api.defaults.headers.common['Authorization']
            if (currentPath !== '/login' && currentPath !== '/signup') {
              isRedirecting = true
              setTimeout(() => {
                if (window.location.pathname !== '/login' && window.location.pathname !== '/signup') {
                  window.location.href = '/login'
                }
                isRedirecting = false
              }, 200)
            }
          }
          // If token exists, let the page handle it (might be expired, but let page decide)
        } else {
          // For other pages, clear token and redirect
          localStorage.removeItem('auth_token')
          delete api.defaults.headers.common['Authorization']
          if (currentPath !== '/login' && currentPath !== '/signup') {
            isRedirecting = true
            setTimeout(() => {
              if (window.location.pathname !== '/login' && window.location.pathname !== '/signup') {
                window.location.href = '/login'
              }
              isRedirecting = false
            }, 200)
          }
        }
      }
    }
    return Promise.reject(error)
  }
)

// Helper to set auth token
export const setAuthToken = (token: string | null) => {
  if (typeof window !== 'undefined') {
    if (token) {
      try {
        localStorage.setItem('auth_token', token)
        // Also set in axios defaults as backup
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`
        console.log('[API] setAuthToken: Token set in localStorage and axios defaults')
        
        // Verify it was saved
        const verify = localStorage.getItem('auth_token')
        if (verify !== token) {
          console.error('[API] setAuthToken: Verification failed! Retrying...')
          localStorage.setItem('auth_token', token)
        }
      } catch (error) {
        console.error('[API] setAuthToken: Error saving token:', error)
        throw error
      }
    } else {
      localStorage.removeItem('auth_token')
      delete api.defaults.headers.common['Authorization']
      console.log('[API] setAuthToken: Token removed')
    }
  }
}

export interface Forecast {
  p50: number
  p80: number
  p90?: number
  p95?: number
  mean?: number
  std?: number
  min?: number
  max?: number
  current?: number
  criticality_indices?: Record<string, number>
  num_simulations?: number
  warnings?: string[]
  explanation?: {
    summary?: string
    details?: string
    plain_language?: string
    confidence_intervals?: Record<string, any>
    key_insights?: string[]
  }
  // Forensic Intelligence fields
  forensic_modulation_applied?: boolean
  forensic_insights?: {
    drift_activities: number
    skill_bottlenecks: number
    high_risk_clusters: number
    bridge_nodes: number
  }
  forensic_explanation?: string
}

export interface Risk {
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
  // Legacy fields for backward compatibility
  activity_name?: string
  risk_category?: string
  impact_days?: number
}

export interface TopRisksResponse {
  total_risks: number
  top_risks: Risk[]
}

export interface Explanation {
  activity_id: string
  activity_name: string
  risk_score: number
  explanation: string
  key_factors?: string[]
  recommendations?: string[]
}

export interface SimulationResult {
  original_forecast: { p50: number; p80: number }
  new_forecast: { p50: number; p80: number }
  improvement: {
    p50_improvement: number
    p80_improvement: number
    p50_improvement_pct?: number
    p80_improvement_pct?: number
  }
  risk_score_impact?: {
    original_risk_score: number
    new_risk_score: number
    risk_score_improvement: number
  }
  activity_id: string
  mitigation_applied: {
    new_duration?: number
    risk_reduced?: boolean
    new_fte?: number
    new_cost?: number
  }
  // Legacy fields
  baseline?: { p50: number; p80: number }
  mitigated?: { p50: number; p80: number }
}

export interface AuditEvent {
  id: number
  project_id: string
  event_type: string
  timestamp: string
  metadata: Record<string, any>
}

export interface AuditLog {
  project_id: string
  total_events: number
  events: AuditEvent[]
}

export interface ProjectInfo {
  project_id: string
  filename: string
  activity_count: number
  created_at: string
  updated_at: string | null
}

export interface ProjectList {
  total: number
  projects: ProjectInfo[]
}

export const uploadProject = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post<{ project_id: string; count: number }>(
    '/projects/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  return response.data
}

export const getForecast = async (projectId: string): Promise<Forecast> => {
  const response = await api.get<Forecast>(`/projects/${projectId}/forecast`)
  return response.data
}

export const getForensicForecast = async (
  projectId: string,
  numSimulations: number = 2000,
  forceRecompute: boolean = false
): Promise<Forecast> => {
  const params = new URLSearchParams()
  params.append('num_simulations', numSimulations.toString())
  if (forceRecompute) params.append('force_recompute', 'true')
  params.append('include_explanation', 'true')
  
  const response = await api.get<Forecast>(
    `/projects/${projectId}/forecast/forensic?${params.toString()}`
  )
  return response.data
}

export const getTopRisks = async (projectId: string, limit = 10): Promise<TopRisksResponse> => {
  const response = await api.get<TopRisksResponse>(`/projects/${projectId}/risks/top?limit=${limit}&include_explanations=true`)
  return response.data
}

export interface Anomaly {
  zombie_tasks: Array<{
    activity_id: string
    name: string
    planned_start: string
    days_overdue: number
    anomaly_type: string
    predecessors_ready?: boolean
    note?: string
    plain_language?: string
    business_impact?: {
      severity?: string
      blocked_tasks?: number
      blocked_task_names?: string[]
      urgency_days?: number
    }
    recommended_action?: string
    enhanced_explanation?: {
      summary?: string
      reasons?: string[]
      suggestions?: string[]
      impact?: {
        blocked_tasks_count?: number
        blocked_task_names?: string[]
        urgency_days?: number
        plain_language?: string
      }
    }
  }>
  black_holes: Array<{
    resource_id: string
    utilization: number
    max_overlap_utilization?: number
    total_fte: number
    max_fte: number
    max_overlap_fte?: number
    max_overlap_period?: [string, string]
    activity_count: number
    activities: string[]
    critical_overlaps?: Array<{
      period: [string, string]
      total_fte: number
      utilization: number
      activities: string[]
    }>
    anomaly_type: string
    enhanced_explanation?: {
      summary?: string
      reasons?: string[]
      suggestions?: string[]
      impact?: {
        max_overlap_utilization?: number
        max_overlap_period?: [string, string]
        critical_overlaps_count?: number
        plain_language?: string
      }
    }
  }>
  total_anomalies: number
}

export const getAnomalies = async (projectId: string): Promise<Anomaly> => {
  const response = await api.get<Anomaly>(`/projects/${projectId}/anomalies`)
  return response.data
}

export interface MitigationOption {
  type: string
  description: string
  parameters: Record<string, any>
  estimated_cost_multiplier: number
  estimated_ftedays: number
  improvement: {
    p50_improvement: number
    p80_improvement: number
    p50_new: number
    p80_new: number
  }
  utility_score: number
  action_id?: string
}

export interface MitigationOptionsResponse {
  activity_id: string
  baseline_forecast: Forecast
  ranked_mitigations: MitigationOption[]
  total_options: number
}

export const getMitigationOptions = async (projectId: string, activityId: string): Promise<MitigationOptionsResponse> => {
  const response = await api.get<MitigationOptionsResponse>(`/projects/${projectId}/mitigations/${activityId}`)
  return response.data
}

export const getExplanation = async (
  projectId: string,
  activityId: string,
  useLLM = false
): Promise<Explanation> => {
  const response = await api.get<Explanation>(
    `/projects/${projectId}/explain/${activityId}?use_llm=${useLLM}`
  )
  return response.data
}

export const simulateMitigation = async (
  projectId: string,
  activityId: string,
  newDuration?: number,
  reduceRisk = false,
  newFte?: number,
  newCost?: number
): Promise<SimulationResult> => {
  const response = await api.post<SimulationResult>(`/projects/${projectId}/simulate`, {
    activity_id: activityId,
    new_duration: newDuration,
    reduce_risk: reduceRisk,
    new_fte: newFte,
    new_cost: newCost,
  })
  return response.data
}

export const getAuditLog = async (projectId: string): Promise<AuditLog> => {
  const response = await api.get<AuditLog>(`/projects/${projectId}/audit`)
  return response.data
}

export const getProjects = async (limit = 50): Promise<ProjectList> => {
  const response = await api.get<ProjectList>(`/projects?limit=${limit}`)
  return response.data
}

// Portfolio-level analysis types and functions
export interface PortfolioSummary {
  total_projects: number
  total_activities: number
  portfolio_risk_score: number
  projects_at_risk: number
  high_risk_projects: Array<{
    project_id: string
    filename: string | null
    risk_score: number
    activity_count: number
  }>
  resource_summary: Record<string, {
    total_fte: number
    max_fte: number
    utilization_pct: number
    project_count: number
    is_overallocated: boolean
  }>
  computation_time_ms: number
}

export interface PortfolioRisk {
  activity_id: string
  name: string
  risk_score: number
  project_id: string
  project_filename: string
  risk_factors?: Record<string, any>
  features?: Record<string, any>
  percent_complete?: number
  on_critical_path?: boolean
}

export interface PortfolioRisksResponse {
  total_risks: number
  top_risks: PortfolioRisk[]
  projects_analyzed: number
}

export interface PortfolioDependencies {
  total_projects: number
  potential_dependencies: any[]
  note: string
}

export interface ResourceAllocation {
  resource_id: string
  total_fte: number
  max_fte: number
  utilization_pct: number
  project_count: number
  activity_count: number
  is_overallocated: boolean
  allocations: Array<{
    project_id: string
    activity_id: string
    activity_name: string
    fte: number
    max_fte: number
  }>
}

export interface PortfolioResourcesResponse {
  total_resources: number
  overallocated_resources: number
  resources: Record<string, ResourceAllocation>
}

export const getPortfolioSummary = async (projectIds?: string[]): Promise<PortfolioSummary> => {
  const params = projectIds ? `?project_ids=${projectIds.join(',')}` : ''
  const response = await api.get<PortfolioSummary>(`/portfolio/summary${params}`)
  return response.data
}

export const getPortfolioRisks = async (projectIds?: string[], limit = 20): Promise<PortfolioRisksResponse> => {
  const params = new URLSearchParams()
  if (projectIds) params.append('project_ids', projectIds.join(','))
  params.append('limit', limit.toString())
  const response = await api.get<PortfolioRisksResponse>(`/portfolio/risks?${params.toString()}`)
  return response.data
}

export const getPortfolioDependencies = async (projectIds?: string[]): Promise<PortfolioDependencies> => {
  const params = projectIds ? `?project_ids=${projectIds.join(',')}` : ''
  const response = await api.get<PortfolioDependencies>(`/portfolio/dependencies${params}`)
  return response.data
}

export const getPortfolioResources = async (projectIds?: string[]): Promise<PortfolioResourcesResponse> => {
  const params = projectIds ? `?project_ids=${projectIds.join(',')}` : ''
  const response = await api.get<PortfolioResourcesResponse>(`/portfolio/resources${params}`)
  return response.data
}

export interface ReAnalyzePortfolioResponse {
  status: string
  message: string
  projects_scheduled: number
  note: string
}

export const reAnalyzePortfolio = async (): Promise<ReAnalyzePortfolioResponse> => {
  const response = await api.post<ReAnalyzePortfolioResponse>('/portfolio/re-analyze')
  return response.data
}

// Authentication types and functions
export interface User {
  id: number
  email: string
  full_name: string | null
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export const register = async (email: string, password: string, fullName?: string): Promise<AuthResponse> => {
  console.log('[API] Starting registration for:', email)
  
  // Create a temporary axios instance without interceptors for registration
  const registerApi = axios.create({
    baseURL: API_BASE,
    headers: {
      'Content-Type': 'application/json',
    },
  })
  
  const response = await registerApi.post<AuthResponse>('/auth/register', {
    email,
    password,
    full_name: fullName,
  })
  
  console.log('[API] Registration response received:', {
    hasToken: !!response.data.access_token,
    tokenLength: response.data.access_token?.length,
    user: response.data.user?.email
  })
  
  // Set token immediately and verify it's set
  const token = response.data.access_token
  if (!token) {
    console.error('[API] No token in response!', response.data)
    throw new Error('No token received from registration response')
  }
  
  // Save token directly to localStorage first
  if (typeof window !== 'undefined') {
    localStorage.setItem('auth_token', token)
    console.log('[API] Token saved directly to localStorage')
    
    // Also set in axios defaults
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    console.log('[API] Token set in axios defaults')
    
    // Verify it was saved
    const storedToken = localStorage.getItem('auth_token')
    if (storedToken !== token) {
      console.error('[API] Token verification failed! Expected:', token.substring(0, 20), 'Got:', storedToken?.substring(0, 20))
      // Force save again
      localStorage.setItem('auth_token', token)
    } else {
      console.log('[API] Token verified in localStorage:', storedToken.substring(0, 20) + '...')
    }
  }
  
  return response.data
}

export const login = async (email: string, password: string): Promise<AuthResponse> => {
  console.log('[API] Starting login for:', email)
  
  // Make login request WITHOUT token (it's a public endpoint)
  // Create a temporary axios instance without interceptors for login
  const loginApi = axios.create({
    baseURL: API_BASE,
    headers: {
      'Content-Type': 'application/json',
    },
  })
  
  const response = await loginApi.post<AuthResponse>('/auth/login-json', {
    email,
    password,
  })
  
  console.log('[API] Login response received:', {
    hasToken: !!response.data.access_token,
    tokenLength: response.data.access_token?.length,
    user: response.data.user?.email
  })
  
  // Set token immediately and verify it's set
  const token = response.data.access_token
  if (!token) {
    console.error('[API] No token in response!', response.data)
    throw new Error('No token received from login response')
  }
  
  // Save token directly to localStorage first
  if (typeof window !== 'undefined') {
    localStorage.setItem('auth_token', token)
    console.log('[API] Token saved directly to localStorage')
    
    // Also set in axios defaults
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    console.log('[API] Token set in axios defaults')
    
    // Verify it was saved
    const storedToken = localStorage.getItem('auth_token')
    if (storedToken !== token) {
      console.error('[API] Token verification failed! Expected:', token.substring(0, 20), 'Got:', storedToken?.substring(0, 20))
      // Force save again
      localStorage.setItem('auth_token', token)
    } else {
      console.log('[API] Token verified in localStorage:', storedToken.substring(0, 20) + '...')
    }
  }
  
  return response.data
}

export const getCurrentUser = async (): Promise<User> => {
  const response = await api.get<User>('/auth/me')
  return response.data
}

export const logout = () => {
  setAuthToken(null)
}

// Delete operations
export interface DeleteResponse {
  success: boolean
  message: string
  deleted_projects?: number
  deleted_activities?: number
  project_id?: string
}

export const deleteProject = async (projectId: string): Promise<DeleteResponse> => {
  const response = await api.delete<DeleteResponse>(`/projects/${projectId}`)
  return response.data
}

export const deleteSelectedProjects = async (projectIds: string[]): Promise<DeleteResponse> => {
  const response = await api.post<DeleteResponse>('/projects/delete-selected', {
    project_ids: projectIds
  })
  return response.data
}

export const deleteAllProjects = async (): Promise<DeleteResponse> => {
  const response = await api.delete<DeleteResponse>('/projects/all?confirm=true')
  return response.data
}

// Re-analyze project
export interface ReAnalyzeResponse {
  project_id: string
  status: string
  message: string
  activity_count: number
  note: string
}

export const reAnalyzeProject = async (projectId: string): Promise<ReAnalyzeResponse> => {
  const response = await api.post<ReAnalyzeResponse>(`/projects/${projectId}/re-analyze`)
  return response.data
}

// UX Enhancement APIs

// Notification Preferences
export interface NotificationPreferences {
  email_enabled: boolean
  email_risk_alerts: boolean
  email_daily_digest: boolean
  email_weekly_summary: boolean
  risk_alert_threshold: number
  risk_digest_threshold: number
  digest_frequency: string
  project_preferences: Record<string, any>
}

export const getNotificationPreferences = async (): Promise<NotificationPreferences> => {
  const response = await api.get<NotificationPreferences>('/notifications/preferences')
  return response.data
}

export const updateNotificationPreferences = async (prefs: Partial<NotificationPreferences>): Promise<NotificationPreferences> => {
  const response = await api.put<NotificationPreferences>('/notifications/preferences', prefs)
  return response.data
}

// Webhooks
export interface WebhookConfig {
  id: number
  user_id: number
  project_id?: string
  name: string
  url: string
  event_type: string
  payload_template?: Record<string, any>
  is_active: boolean
  created_at: string
  updated_at: string
}

export const getWebhooks = async (projectId?: string): Promise<WebhookConfig[]> => {
  const params = projectId ? `?project_id=${projectId}` : ''
  const response = await api.get<WebhookConfig[]>(`/webhooks${params}`)
  return response.data
}

export const createWebhook = async (webhook: Omit<WebhookConfig, 'id' | 'user_id' | 'created_at' | 'updated_at'>): Promise<WebhookConfig> => {
  const response = await api.post<WebhookConfig>('/webhooks', webhook)
  return response.data
}

export const updateWebhook = async (webhookId: number, webhook: Partial<WebhookConfig>): Promise<WebhookConfig> => {
  const response = await api.put<WebhookConfig>(`/webhooks/${webhookId}`, webhook)
  return response.data
}

export const deleteWebhook = async (webhookId: number): Promise<void> => {
  await api.delete(`/webhooks/${webhookId}`)
}

export const testWebhook = async (webhookId: number): Promise<{ message: string }> => {
  const response = await api.post<{ message: string }>(`/webhooks/${webhookId}/trigger-test`)
  return response.data
}

// User Preferences
export interface UserPreferences {
  risk_threshold_high: number
  risk_threshold_medium: number
  risk_threshold_low: number
  dashboard_layout: Record<string, any>
  default_filters: Record<string, any>
  default_views: Record<string, any>
  show_p50_first: boolean
  show_p80_first: boolean
  show_anomalies_section: boolean
  show_resource_summary: boolean
}

export const getUserPreferences = async (): Promise<UserPreferences> => {
  const response = await api.get<UserPreferences>('/user/preferences')
  return response.data
}

export const updateUserPreferences = async (prefs: Partial<UserPreferences>): Promise<UserPreferences> => {
  const response = await api.put<UserPreferences>('/user/preferences', prefs)
  return response.data
}

// Feedback
export interface Feedback {
  id: number
  user_id: number
  project_id?: string
  activity_id?: string
  feature: string
  rating?: number
  comment?: string
  timestamp: string
}

export const submitFeedback = async (feedback: Omit<Feedback, 'id' | 'user_id' | 'timestamp'>): Promise<Feedback> => {
  const response = await api.post<Feedback>('/feedback', feedback)
  return response.data
}

// Gantt Chart
export interface GanttTask {
  id: string
  name: string
  start: string
  end: string
  progress: number
  dependencies?: string[]
  risk_score: number
  risk_level: string
  on_critical_path: boolean
  float_days?: number
  resource_id?: string
  fte_allocation?: number
}

export interface GanttDataResponse {
  project_id: string
  activities: GanttTask[]
  critical_path: string[]
  total_activities: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
}

export const getGanttData = async (projectId: string): Promise<GanttTask[]> => {
  const response = await api.get<GanttDataResponse>(`/projects/${projectId}/gantt`)
  return response.data.activities || []
}

// Onboarding
export interface OnboardingStep {
  id: string
  title: string
  description: string
  target_element?: string | null
  position?: string | null
  action?: string | null
}

export interface OnboardingTour {
  tour_id: string
  name: string
  description: string
  steps: OnboardingStep[]
}

export interface OnboardingStatus {
  completed_tours: string[]
  current_tour?: string | null
  current_step?: number | null
}

export interface OnboardingToursResponse {
  tours: Array<{
    tour_id: string
    name: string
    description: string
    step_count: number
  }>
}

export const getOnboardingTours = async (): Promise<OnboardingToursResponse> => {
  const response = await api.get<OnboardingToursResponse>('/onboarding/tours')
  return response.data
}

export const getOnboardingTour = async (tourId: string): Promise<OnboardingTour> => {
  const response = await api.get<OnboardingTour>(`/onboarding/tours/${tourId}`)
  return response.data
}

export const getOnboardingStatus = async (): Promise<OnboardingStatus> => {
  const response = await api.get<OnboardingStatus>('/onboarding/status')
  return response.data
}

export const completeOnboardingTour = async (tourId: string): Promise<{ message: string; tour_id: string }> => {
  const response = await api.post<{ message: string; tour_id: string }>(`/onboarding/complete/${tourId}`)
  return response.data
}

export default api

