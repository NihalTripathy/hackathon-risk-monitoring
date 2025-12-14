'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import FeedbackWidget from '@/components/FeedbackWidget'
import {
  AlertTriangle,
  Calculator,
  Lightbulb,
  ArrowLeft,
  Loader2,
  TrendingDown,
  Clock,
  Sparkles,
} from 'lucide-react'
import api from '@/lib/api'

interface Explanation {
  activity_id: string
  activity_name: string
  risk_score: number
  explanation?: string
  reasons?: string[]
  suggestions?: string[]
  key_factors?: string[]
  recommendations?: string[]
  method?: string
  model_used?: string
  llm_error?: string
}

interface SimulationResult {
  original_forecast?: { p50: number; p80: number }
  new_forecast?: { p50: number; p80: number }
  baseline?: { p50: number; p80: number }
  mitigated?: { p50: number; p80: number }
  improvement?: {
    p50_improvement?: number
    p80_improvement?: number
    p50_days_saved?: number
    p80_days_saved?: number
    p50_improvement_pct?: number
    p80_improvement_pct?: number
  }
  risk_score_impact?: {
    original_risk_score: number
    new_risk_score: number
    risk_score_improvement: number
  }
  activity_id?: string
  mitigation_applied?: {
    new_duration?: number
    risk_reduced?: boolean
    new_fte?: number
    new_cost?: number
  }
}

interface MitigationOption {
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
}

interface MitigationOptionsResponse {
  activity_id: string
  baseline_forecast: any
  ranked_mitigations: MitigationOption[]
  total_options: number
}

export default function ActivityDetail() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string
  const activityId = params.aid as string

  // Store current path for settings page navigation
  useEffect(() => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('lastPath', `/projects/${projectId}/activities/${activityId}`)
      sessionStorage.setItem('lastProjectId', projectId)
    }
  }, [projectId, activityId])

  const [explanation, setExplanation] = useState<Explanation | null>(null)
  const [simulation, setSimulation] = useState<SimulationResult | null>(null)
  const [mitigationOptions, setMitigationOptions] = useState<MitigationOptionsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [simulating, setSimulating] = useState(false)
  const [loadingMitigations, setLoadingMitigations] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [useLLM, setUseLLM] = useState(false)

  const [simulationType, setSimulationType] = useState<'duration' | 'risk' | 'fte' | 'cost'>('duration')
  const [newDuration, setNewDuration] = useState<string>('')
  const [reduceRisk, setReduceRisk] = useState(false)
  const [newFte, setNewFte] = useState<string>('')
  const [newCost, setNewCost] = useState<string>('')

  const fetchExplanation = async (useLLMValue: boolean) => {
    try {
      setError(null)
      setLoading(true)
      const response = await api.get(
        `/projects/${projectId}/explain/${activityId}?use_llm=${useLLMValue}`
      )
      setExplanation(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load explanation')
    } finally {
      setLoading(false)
    }
  }

  const fetchMitigationOptions = async () => {
    try {
      setLoadingMitigations(true)
      setError(null)
      const response = await api.get(`/projects/${projectId}/mitigations/${activityId}`)
      setMitigationOptions(response.data)
    } catch (err: any) {
      console.error('Failed to load mitigation options:', err)
      // Don't set error, just log - mitigations are optional
    } finally {
      setLoadingMitigations(false)
    }
  }

  useEffect(() => {
    if (projectId && activityId) {
      fetchExplanation(useLLM)
      fetchMitigationOptions()
    }
  }, [projectId, activityId, useLLM])

  const handleSimulate = async () => {
    if (simulationType === 'duration' && !newDuration) {
      setError('Please enter a new duration')
      return
    }
    if (simulationType === 'fte' && !newFte) {
      setError('Please enter a new FTE allocation')
      return
    }
    if (simulationType === 'cost' && !newCost) {
      setError('Please enter a new cost')
      return
    }

    setSimulating(true)
    setError(null)

    try {
      const response = await api.post(`/projects/${projectId}/simulate`, {
        activity_id: activityId,
        new_duration: simulationType === 'duration' ? parseFloat(newDuration) : null,
        reduce_risk: simulationType === 'risk' ? true : false,
        new_fte: simulationType === 'fte' ? parseFloat(newFte) : null,
        new_cost: simulationType === 'cost' ? parseFloat(newCost) : null,
      })
      // Map backend response to frontend interface
      const data = response.data
      const mappedData: SimulationResult = {
        original_forecast: data.original_forecast || data.baseline,
        new_forecast: data.new_forecast || data.mitigated,
        baseline: data.baseline,
        mitigated: data.mitigated,
        improvement: data.improvement ? {
          p50_improvement: data.improvement.p50_improvement ?? data.improvement.p50_days_saved,
          p80_improvement: data.improvement.p80_improvement ?? data.improvement.p80_days_saved,
          p50_days_saved: data.improvement.p50_days_saved,
          p80_days_saved: data.improvement.p80_days_saved,
          p50_improvement_pct: data.improvement.p50_improvement_pct,
          p80_improvement_pct: data.improvement.p80_improvement_pct,
        } : undefined,
        risk_score_impact: data.risk_score_impact,
        activity_id: data.activity_id,
        mitigation_applied: data.mitigation_applied,
      }
      setSimulation(mappedData)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to run simulation')
    } finally {
      setSimulating(false)
    }
  }

  const getRiskColor = (score: number) => {
    if (score >= 0.7) return 'text-red-700 bg-red-100 border-red-300'
    if (score >= 0.4) return 'text-yellow-700 bg-yellow-100 border-yellow-300'
    return 'text-green-700 bg-green-100 border-green-300'
  }

  const getRiskLabel = (score: number) => {
    if (score >= 0.7) return 'High Risk'
    if (score >= 0.4) return 'Medium Risk'
    return 'Low Risk'
  }

  // Parse markdown explanation to extract structured content
  const parseExplanation = (explanationText: string) => {
    if (!explanationText) return { mainText: '', reasons: [], suggestions: [] }
    
    let mainText = ''
    const reasons: string[] = []
    const suggestions: string[] = []
    
    // Remove markdown headers and split by sections
    // Handle various header formats: "### Explanation", "### Explanation of Risk Score", etc.
    const explanationMatch = explanationText.match(/###\s*Explanation[^\n]*\n\n(.*?)(?=\n###|$)/s)
    const suggestionsMatch = explanationText.match(/###\s*Actionable\s*Suggestions?[^\n]*\n\n(.*?)(?=\n###|$)/s)
    
    if (explanationMatch) {
      let explanationContent = explanationMatch[1].trim()
      
      // Remove any remaining markdown headers that might be in the content
      explanationContent = explanationContent.replace(/^###\s+[^\n]+\n\n?/gm, '')
      
      // Extract numbered list items (reasons) - handle multiline descriptions
      const lines = explanationContent.split('\n')
      let currentReason = ''
      let inReasonList = false
      let introText = ''
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim()
        
        // Match numbered list items with bold titles: "1. **Title**: description"
        // Also match without bold: "1. Title: description" or "1. Title"
        const numberedMatchBold = line.match(/^\d+\.\s*\*\*(.*?)\*\*:\s*(.+)$/)
        const numberedMatchPlain = line.match(/^\d+\.\s*([^:]+?):\s*(.+)$/)
        const numberedMatchSimple = line.match(/^\d+\.\s*(.+)$/)
        
        if (numberedMatchBold) {
          // Save previous reason if exists
          if (currentReason) {
            reasons.push(currentReason.trim())
          }
          // Save intro text before first numbered item
          if (!inReasonList && introText) {
            mainText = introText.trim()
          }
          currentReason = `${numberedMatchBold[1]}: ${numberedMatchBold[2]}`
          inReasonList = true
        } else if (numberedMatchPlain) {
          if (currentReason) {
            reasons.push(currentReason.trim())
          }
          if (!inReasonList && introText) {
            mainText = introText.trim()
          }
          currentReason = `${numberedMatchPlain[1].trim()}: ${numberedMatchPlain[2]}`
          inReasonList = true
        } else if (numberedMatchSimple && !inReasonList) {
          // Simple numbered item without colon - might be start of a list
          if (introText) {
            mainText = introText.trim()
          }
          currentReason = numberedMatchSimple[1].trim()
          inReasonList = true
        } else if (inReasonList && line && !line.match(/^\d+\./)) {
          // Continuation of current reason (not a new numbered item)
          if (line.match(/^\*\*/)) {
            // New bold item without number, might be a sub-item
            if (currentReason) {
              reasons.push(currentReason.trim())
            }
            const boldMatch = line.match(/\*\*(.*?)\*\*:\s*(.+)$/)
            if (boldMatch) {
              currentReason = `${boldMatch[1]}: ${boldMatch[2]}`
            } else {
              currentReason = line.replace(/\*\*/g, '')
            }
          } else {
            // Regular continuation
            currentReason += ' ' + line
          }
        } else if (inReasonList && !line) {
          // Empty line might end the reason
          if (currentReason) {
            reasons.push(currentReason.trim())
            currentReason = ''
          }
        } else if (!inReasonList && line) {
          // Text before the numbered list (intro text)
          if (!line.match(/^#{1,6}\s/)) { // Skip any remaining headers
            introText += (introText ? '\n' : '') + line
          }
        }
      }
      
      // Add last reason if exists
      if (currentReason) {
        reasons.push(currentReason.trim())
      }
      
      // If no numbered reasons found, use the whole explanation as main text
      if (reasons.length === 0) {
        mainText = explanationContent.replace(/^\d+\.\s*/gm, '').trim()
      } else if (!mainText && introText) {
        mainText = introText.trim()
      }
    } else {
      // No explicit explanation section, try to parse the whole text
      // Remove markdown headers
      let cleanText = explanationText.replace(/^###\s+[^\n]+\n\n?/gm, '')
      
      // Try to extract numbered items
      const lines = cleanText.split('\n')
      let currentReason = ''
      let introText = ''
      let inReasonList = false
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim()
        const numberedMatchBold = line.match(/^\d+\.\s*\*\*(.*?)\*\*:\s*(.+)$/)
        const numberedMatchPlain = line.match(/^\d+\.\s*([^:]+?):\s*(.+)$/)
        const numberedMatchSimple = line.match(/^\d+\.\s*(.+)$/)
        
        if (numberedMatchBold) {
          if (currentReason) {
            reasons.push(currentReason.trim())
          }
          if (!inReasonList && introText) {
            mainText = introText.trim()
          }
          currentReason = `${numberedMatchBold[1]}: ${numberedMatchBold[2]}`
          inReasonList = true
        } else if (numberedMatchPlain) {
          if (currentReason) {
            reasons.push(currentReason.trim())
          }
          if (!inReasonList && introText) {
            mainText = introText.trim()
          }
          currentReason = `${numberedMatchPlain[1].trim()}: ${numberedMatchPlain[2]}`
          inReasonList = true
        } else if (numberedMatchSimple && !inReasonList) {
          if (introText) {
            mainText = introText.trim()
          }
          currentReason = numberedMatchSimple[1].trim()
          inReasonList = true
        } else if (inReasonList && line && !line.match(/^\d+\./)) {
          currentReason += ' ' + line
        } else if (inReasonList && !line) {
          if (currentReason) {
            reasons.push(currentReason.trim())
            currentReason = ''
          }
        } else if (!inReasonList && line) {
          introText += (introText ? '\n' : '') + line
        }
      }
      
      if (currentReason) {
        reasons.push(currentReason.trim())
      }
      
      if (reasons.length === 0) {
        mainText = cleanText.trim()
      } else if (!mainText && introText) {
        mainText = introText.trim()
      }
    }
    
    if (suggestionsMatch) {
      let suggestionsContent = suggestionsMatch[1].trim()
      // Remove any markdown headers
      suggestionsContent = suggestionsContent.replace(/^###\s+[^\n]+\n\n?/gm, '')
      
      const lines = suggestionsContent.split('\n')
      let currentSuggestion = ''
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim()
        const numberedMatch = line.match(/^\d+\.\s*\*\*(.*?)\*\*:\s*(.+)$/)
        
        if (numberedMatch) {
          if (currentSuggestion) {
            suggestions.push(currentSuggestion.trim())
          }
          currentSuggestion = `${numberedMatch[1]}: ${numberedMatch[2]}`
        } else if (currentSuggestion && line && !line.match(/^\d+\./)) {
          currentSuggestion += ' ' + line
        } else if (currentSuggestion && !line) {
          suggestions.push(currentSuggestion.trim())
          currentSuggestion = ''
        }
      }
      
      if (currentSuggestion) {
        suggestions.push(currentSuggestion.trim())
      }
    }
    
    return { mainText: mainText.trim(), reasons, suggestions }
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

  if (error && !explanation) {
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
      {/* Compact Back Button */}
      <button
        onClick={() => router.push(`/projects/${projectId}`)}
        className="flex items-center gap-1.5 text-xs text-gray-600 hover:text-gray-900 mb-3 font-medium transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        Back to Dashboard
      </button>

      {explanation && (
        <>
          {/* Compact Activity Header */}
          <div className="bg-gradient-to-r from-primary-600 to-blue-600 text-white rounded-lg p-3 mb-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex-1">
                <h1 className="text-lg font-bold mb-1">
                  {explanation.activity_name}
                </h1>
                <p className="text-xs text-primary-100 font-mono">ID: {explanation.activity_id}</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-xs font-medium text-primary-100 mb-1">Risk Score</div>
                  <div className="text-2xl font-bold">
                    {explanation.risk_score > 1 
                      ? `${explanation.risk_score.toFixed(1)}%`
                      : `${(explanation.risk_score * 100).toFixed(1)}%`}
                  </div>
                </div>
                <span
                  className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold border ${getRiskColor(
                    explanation.risk_score > 1 ? explanation.risk_score / 100 : explanation.risk_score
                  )} bg-white/90`}
                >
                  {getRiskLabel(explanation.risk_score > 1 ? explanation.risk_score / 100 : explanation.risk_score)}
                </span>
              </div>
            </div>
          </div>

          {/* Compact Explanation Section */}
          <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-yellow-500" />
                <h2 className="text-base font-bold text-gray-900">Risk Explanation</h2>
              </div>
              {/* Compact LLM Toggle */}
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-600">Rule-based</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useLLM}
                    onChange={(e) => {
                      setUseLLM(e.target.checked)
                    }}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
                <span className="text-xs font-medium text-gray-600">AI (LLM)</span>
              </div>
            </div>
            
            {explanation.method === 'llm_huggingface' && explanation.llm_error && (
              <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
                <strong>Note:</strong> LLM failed, showing rule-based fallback.
              </div>
            )}

            {/* Show method badge */}
            {explanation.method && (
              <div className="mb-3">
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                  explanation.method === 'llm_huggingface' 
                    ? 'bg-purple-100 text-purple-800 border border-purple-300' 
                    : 'bg-gray-100 text-gray-800 border border-gray-300'
                }`}>
                  {explanation.method === 'llm_huggingface' ? '🤖 AI-Generated' : '📋 Rule-Based'}
                </span>
                {explanation.model_used && explanation.method === 'llm_huggingface' && (
                  <span className="ml-2 text-xs text-gray-500">({explanation.model_used})</span>
                )}
              </div>
            )}

            {/* Parse and display LLM explanation with structured format */}
            {explanation.method === 'llm_huggingface' && explanation.explanation && (() => {
              const parsed = parseExplanation(explanation.explanation)
              
              return (
                <>
                  {/* Main explanation text */}
                  {parsed.mainText && (
                    <div className="mb-4">
                      <h3 className="text-sm font-bold text-gray-900 mb-2">
                        Explanation for {explanation.activity_name}
                      </h3>
                      <p className="text-xs text-gray-700 leading-relaxed">
                        {parsed.mainText}
                      </p>
                    </div>
                  )}

                  {/* Breakdown of reasons */}
                  {parsed.reasons.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-xs font-bold text-gray-900 mb-2">Breakdown:</h4>
                      <ol className="space-y-2 ml-4">
                        {parsed.reasons.map((reason, idx) => {
                          const colonIndex = reason.indexOf(':')
                          if (colonIndex > 0) {
                            const title = reason.substring(0, colonIndex).trim()
                            const description = reason.substring(colonIndex + 1).trim()
                            return (
                              <li key={idx} className="text-xs text-gray-700">
                                <span className="font-bold text-gray-900">{title}:</span> {description}
                              </li>
                            )
                          }
                          return (
                            <li key={idx} className="text-xs text-gray-700">
                              {reason}
                            </li>
                          )
                        })}
                      </ol>
                    </div>
                  )}

                  {/* Fallback - if parsing didn't extract content, show cleaned version */}
                  {parsed.reasons.length === 0 && !parsed.mainText && (
                    <div className="text-xs text-gray-700 leading-relaxed whitespace-pre-line">
                      {explanation.explanation
                        .replace(/^###\s+Explanation[^\n]*\n\n?/gim, '') // Remove any explanation header
                        .replace(/^###\s+Actionable\s+Suggestions?[^\n]*\n\n?/gim, '') // Remove suggestions header
                        .replace(/^#{1,6}\s+[^\n]+\n\n?/gm, '') // Remove any other markdown headers
                        .trim()}
                    </div>
                  )}
                </>
              )
            })()}

            {/* Rule-based Reasons */}
            {explanation.reasons && explanation.reasons.length > 0 && 
             (explanation.method !== 'llm_huggingface' || !explanation.explanation) && (
              <div>
                <h3 className="text-xs font-bold text-gray-900 mb-2">Key Reasons:</h3>
                <ul className="space-y-2 mb-4">
                  {explanation.reasons.map((reason, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-xs text-gray-700">
                      <span className="text-primary-600 font-bold mt-0.5">•</span>
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {explanation.key_factors && explanation.key_factors.length > 0 && (
              <div className="mt-3 p-3 bg-gray-50 rounded border border-gray-200">
                <h3 className="text-xs font-bold text-gray-900 mb-2 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-primary-600" />
                  Key Factors
                </h3>
                <ul className="space-y-1.5">
                  {explanation.key_factors.map((factor, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-xs text-gray-700">
                      <span className="text-primary-600 font-bold mt-0.5">•</span>
                      <span className="font-medium">{factor}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Compact Recommendations */}
            {(() => {
              const suggestions = explanation.suggestions || explanation.recommendations || []
              const parsed = explanation.method === 'llm_huggingface' && explanation.explanation 
                ? parseExplanation(explanation.explanation) 
                : { suggestions: [] }
              const allSuggestions = suggestions.length > 0 ? suggestions : parsed.suggestions
              
              return allSuggestions.length > 0 ? (
                <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded">
                  <h3 className="text-xs font-bold text-blue-900 mb-2 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                    Recommendations
                  </h3>
                  <ul className="space-y-2">
                    {allSuggestions.map((rec, idx) => {
                      const boldMatch = rec.match(/\*\*(.*?)\*\*:\s*(.+)/)
                      if (boldMatch) {
                        const title = boldMatch[1]
                        const description = boldMatch[2]
                        return (
                          <li key={idx} className="flex items-start gap-2 text-xs">
                            <span className="text-blue-600 font-bold mt-0.5">•</span>
                            <div>
                              <span className="font-bold text-blue-900">{title}:</span>
                              <span className="text-blue-800 ml-1">{description}</span>
                            </div>
                          </li>
                        )
                      }
                      return (
                        <li key={idx} className="flex items-start gap-2 text-xs text-blue-800">
                          <span className="text-blue-600 font-bold mt-0.5">•</span>
                          <span className="font-medium">{rec}</span>
                        </li>
                      )
                    })}
                  </ul>
                </div>
              ) : null
            })()}
          </div>

          {/* Compact Simulator Section */}
          <div id="simulator" className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Calculator className="w-4 h-4 text-primary-600" />
              <h2 className="text-base font-bold text-gray-900">What-If Simulator</h2>
            </div>

            <div className="space-y-3">
              {/* Simulation Type Selection */}
              <div>
                <label className="block text-xs font-bold text-gray-800 mb-2">
                  Simulation Type
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="simType"
                      value="duration"
                      checked={simulationType === 'duration'}
                      onChange={() => setSimulationType('duration')}
                      className="w-4 h-4 text-primary-600 cursor-pointer"
                    />
                    <span className="text-xs font-medium text-gray-700">
                      Duration
                    </span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="simType"
                      value="risk"
                      checked={simulationType === 'risk'}
                      onChange={() => setSimulationType('risk')}
                      className="w-4 h-4 text-primary-600 cursor-pointer"
                    />
                    <span className="text-xs font-medium text-gray-700">
                      Risk
                    </span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="simType"
                      value="fte"
                      checked={simulationType === 'fte'}
                      onChange={() => setSimulationType('fte')}
                      className="w-4 h-4 text-primary-600 cursor-pointer"
                    />
                    <span className="text-xs font-medium text-gray-700">
                      People (FTE)
                    </span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="simType"
                      value="cost"
                      checked={simulationType === 'cost'}
                      onChange={() => setSimulationType('cost')}
                      className="w-4 h-4 text-primary-600 cursor-pointer"
                    />
                    <span className="text-xs font-medium text-gray-700">
                      Cost
                    </span>
                  </label>
                </div>
              </div>

              {/* Duration Input */}
              {simulationType === 'duration' && (
                <div>
                  <label className="block text-xs font-bold text-gray-800 mb-2">
                    New Duration (days)
                  </label>
                  <input
                    type="number"
                    value={newDuration}
                    onChange={(e) => setNewDuration(e.target.value)}
                    placeholder="Enter new duration"
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                    min="0"
                    step="0.1"
                  />
                </div>
              )}

              {/* Risk Mitigation Toggle */}
              {simulationType === 'risk' && (
                <div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={reduceRisk}
                      onChange={(e) => setReduceRisk(e.target.checked)}
                      className="w-4 h-4 text-primary-600 rounded cursor-pointer"
                    />
                    <span className="text-xs font-medium text-gray-700">
                      Apply risk mitigation
                    </span>
                  </label>
                </div>
              )}

              {/* FTE Input */}
              {simulationType === 'fte' && (
                <div>
                  <label className="block text-xs font-bold text-gray-800 mb-2">
                    FTE Allocation (can increase or decrease)
                  </label>
                  <input
                    type="number"
                    value={newFte}
                    onChange={(e) => setNewFte(e.target.value)}
                    placeholder="Enter new FTE (e.g., 2.0 for 2 people, 0.5 to reduce)"
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                    min="0"
                    step="0.1"
                  />
                  <p className="text-xs text-gray-500 mt-1">FTE = Full-Time Equivalent (1.0 = 1 person full-time). You can increase or decrease from current value.</p>
                </div>
              )}

              {/* Cost Input */}
              {simulationType === 'cost' && (
                <div>
                  <label className="block text-xs font-bold text-gray-800 mb-2">
                    New Planned Cost ($)
                  </label>
                  <input
                    type="number"
                    value={newCost}
                    onChange={(e) => setNewCost(e.target.value)}
                    placeholder="Enter new cost"
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                    min="0"
                    step="0.01"
                  />
                </div>
              )}

              {/* Compact Simulate Button */}
              <button
                onClick={handleSimulate}
                disabled={
                  simulating || 
                  (simulationType === 'duration' && !newDuration) ||
                  (simulationType === 'fte' && !newFte) ||
                  (simulationType === 'cost' && !newCost)
                }
                className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium bg-primary-600 hover:bg-primary-700 text-white rounded-md transition-colors disabled:opacity-50"
              >
                {simulating ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Simulating...</span>
                  </>
                ) : (
                  <>
                    <Calculator className="w-3.5 h-3.5" />
                    <span>Run Simulation</span>
                  </>
                )}
              </button>

              {/* Mitigation Options Section */}
              {mitigationOptions && mitigationOptions.ranked_mitigations && mitigationOptions.ranked_mitigations.length > 0 && (
                <div className="mt-4 bg-white rounded-lg border border-gray-200 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
                      <Lightbulb className="w-4 h-4 text-primary-600" />
                      Recommended Mitigation Options
                    </h2>
                    <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                      {mitigationOptions.total_options} options
                    </span>
                  </div>
                  
                  <div className="space-y-3">
                    {mitigationOptions.ranked_mitigations.slice(0, 5).map((option, idx) => (
                      <div
                        key={idx}
                        className="p-3 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs font-bold text-primary-600 bg-primary-50 px-2 py-0.5 rounded">
                                #{idx + 1}
                              </span>
                              <span className="text-xs font-medium text-gray-600">
                                {option.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                              </span>
                              {option.utility_score > 0 && (
                                <span className="text-xs font-bold text-green-600">
                                  Utility: {option.utility_score.toFixed(1)}
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-gray-700 mb-2">{option.description}</p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <span className="text-gray-600">P50 Improvement:</span>
                            <span className="font-bold text-green-600 ml-1">
                              {option.improvement.p50_improvement > 0 ? '+' : ''}
                              {option.improvement.p50_improvement.toFixed(1)} days
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">P80 Improvement:</span>
                            <span className={`font-bold ml-1 ${option.improvement.p80_improvement > 0 ? 'text-green-600' : option.improvement.p80_improvement === 0 ? 'text-gray-500' : 'text-red-600'}`}>
                              {option.improvement.p80_improvement > 0 ? '+' : ''}
                              {option.improvement.p80_improvement.toFixed(1)} days
                            </span>
                            {option.improvement.p80_improvement === 0 && option.improvement.p50_improvement > 0 && (
                              <span className="text-[10px] text-gray-500 ml-1" title="P80 (worst-case) may not improve if other tasks dominate the critical path or improvement is very small">
                                (worst-case unchanged)
                              </span>
                            )}
                          </div>
                          {option.estimated_cost_multiplier > 1 && (
                            <div>
                              <span className="text-gray-600">Cost Impact:</span>
                              <span className="font-bold text-amber-600 ml-1">
                                {(option.estimated_cost_multiplier * 100).toFixed(0)}%
                              </span>
                            </div>
                          )}
                          {option.estimated_ftedays > 0 && (
                            <div>
                              <span className="text-gray-600">FTE Days:</span>
                              <span className="font-bold text-blue-600 ml-1">
                                {option.estimated_ftedays.toFixed(1)}
                              </span>
                            </div>
                          )}
                        </div>
                        
                        <button
                          onClick={() => {
                            if (option.type === 'reduce_duration' && option.parameters.new_duration) {
                              setNewDuration(option.parameters.new_duration.toString())
                              setSimulationType('duration')
                            } else if (option.type === 'reduce_risk') {
                              setReduceRisk(true)
                              setSimulationType('risk')
                            } else if (option.type === 'add_fte' && option.parameters.new_fte) {
                              // For FTE options, set both FTE and potentially duration if estimated
                              setNewFte(option.parameters.new_fte.toString())
                              setSimulationType('fte')
                              // Note: Duration reduction is estimated but not automatically applied
                              // User can manually adjust if needed
                            }
                            // Scroll to simulator
                            setTimeout(() => {
                              document.getElementById('simulator')?.scrollIntoView({ behavior: 'smooth' })
                            }, 100)
                          }}
                          className="mt-2 w-full text-xs font-medium text-primary-600 hover:text-primary-700 border border-primary-300 rounded px-2 py-1 hover:bg-primary-50 transition-colors"
                        >
                          Use This Option →
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Compact Simulation Results */}
              {simulation && simulation.original_forecast && simulation.new_forecast && (() => {
                const p50Change = simulation.improvement?.p50_improvement ?? simulation.improvement?.p50_days_saved ?? 0
                const isPositive = p50Change > 0
                const bgGradient = isPositive 
                  ? 'bg-gradient-to-r from-green-500 to-emerald-600' 
                  : 'bg-gradient-to-r from-yellow-500 to-orange-600'
                
                return (
                <div className={`mt-3 p-4 ${bgGradient} text-white rounded-lg`}>
                  <div className="flex items-center gap-2 mb-3">
                    {isPositive ? (
                      <TrendingDown className="w-4 h-4" />
                    ) : (
                      <TrendingDown className="w-4 h-4 rotate-180" />
                    )}
                    <h3 className="text-sm font-bold">Simulation Results</h3>
                  </div>

                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="bg-white/10 rounded p-2 border border-white/20">
                      <h4 className="text-xs font-bold text-green-100 mb-2">Original</h4>
                      <div className="space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-green-100">P50:</span>
                          <span className="text-sm font-bold">
                            {simulation.original_forecast.p50 != null ? simulation.original_forecast.p50.toFixed(1) : 'N/A'}d
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-green-100">P80:</span>
                          <span className="text-sm font-bold">
                            {simulation.original_forecast.p80 != null ? simulation.original_forecast.p80.toFixed(1) : 'N/A'}d
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white/10 rounded p-2 border border-white/20">
                      <h4 className="text-xs font-bold text-green-100 mb-2">New</h4>
                      <div className="space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-green-100">P50:</span>
                          <span className="text-sm font-bold">
                            {simulation.new_forecast.p50 != null ? simulation.new_forecast.p50.toFixed(1) : 'N/A'}d
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-green-100">P80:</span>
                          <span className="text-sm font-bold">
                            {simulation.new_forecast.p80 != null ? simulation.new_forecast.p80.toFixed(1) : 'N/A'}d
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Risk Score Impact */}
                  {simulation.risk_score_impact && (
                    <div className="mb-3 p-3 bg-purple-500/20 rounded border border-purple-300/30">
                      <h4 className="text-xs font-bold text-purple-100 mb-2">Risk Score Impact</h4>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="bg-white/10 rounded p-1.5">
                          <span className="text-purple-100">Original:</span>
                          <div className="text-sm font-bold text-white">
                            {simulation.risk_score_impact.original_risk_score.toFixed(1)}
                          </div>
                        </div>
                        <div className="bg-white/10 rounded p-1.5">
                          <span className="text-purple-100">New:</span>
                          <div className="text-sm font-bold text-white">
                            {simulation.risk_score_impact.new_risk_score.toFixed(1)}
                          </div>
                        </div>
                        <div className="bg-white/10 rounded p-1.5">
                          <span className="text-purple-100">Improvement:</span>
                          <div className="text-sm font-bold text-green-200">
                            {simulation.risk_score_impact.risk_score_improvement > 0 ? '-' : '+'}
                            {Math.abs(simulation.risk_score_impact.risk_score_improvement).toFixed(1)} pts
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Changes Applied Section */}
                  {simulation.mitigation_applied && (() => {
                    const applied = simulation.mitigation_applied
                    const changes: string[] = []
                    
                    if (applied.new_duration) {
                      changes.push(`Duration: ${applied.new_duration} days`)
                    }
                    if (applied.new_fte !== null && applied.new_fte !== undefined) {
                      changes.push(`FTE: ${applied.new_fte}`)
                    }
                    if (applied.new_cost !== null && applied.new_cost !== undefined) {
                      changes.push(`Cost: $${applied.new_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`)
                    }
                    if (applied.risk_reduced) {
                      changes.push(`Risk: Reduced by 50%`)
                    }
                    
                    if (changes.length > 0) {
                      return (
                        <div className="mb-3 p-3 bg-blue-500/20 rounded border border-blue-300/30">
                          <h4 className="text-xs font-bold text-blue-100 mb-2">Changes Applied</h4>
                          <div className="space-y-1">
                            {changes.map((change, idx) => (
                              <div key={idx} className="text-xs text-blue-100 flex items-center gap-2">
                                <span className="w-1.5 h-1.5 bg-blue-300 rounded-full"></span>
                                {change}
                              </div>
                            ))}
                          </div>
                        </div>
                      )
                    }
                    return null
                  })()}

                  {simulation.improvement && (() => {
                    const p50Change = simulation.improvement.p50_improvement ?? simulation.improvement.p50_days_saved ?? 0
                    const p80Change = simulation.improvement.p80_improvement ?? simulation.improvement.p80_days_saved ?? 0
                    const hasImprovement = p50Change > 0 || p80Change > 0
                    const hasNegativeImpact = p50Change < 0 || p80Change < 0
                    const isNeutral = p50Change === 0 && p80Change === 0
                    
                    return (
                      <div className="pt-3 border-t border-white/30">
                        <h4 className={`text-xs font-bold mb-2 ${
                          hasImprovement ? 'text-green-100' : 
                          hasNegativeImpact ? 'text-red-200' : 
                          'text-blue-100'
                        }`}>
                          {hasImprovement ? 'Schedule Improvement' : 
                           hasNegativeImpact ? 'Duration Impact' : 
                           'No Duration Change'}
                        </h4>
                        <div className="space-y-2">
                          <div className="flex justify-between items-center bg-white/10 rounded p-2">
                            <span className="text-xs font-medium text-green-100">P50:</span>
                            <span className={`text-sm font-bold ${
                              p50Change > 0 ? 'text-green-100' : 
                              p50Change < 0 ? 'text-red-200' : 
                              'text-blue-100'
                            }`}>
                              {p50Change > 0 ? '-' : p50Change < 0 ? '+' : ''}{Math.abs(p50Change).toFixed(1)} days
                            </span>
                          </div>
                          <div className="flex justify-between items-center bg-white/10 rounded p-2">
                            <span className="text-xs font-medium text-green-100">P80:</span>
                            <span className={`text-sm font-bold ${
                              p80Change > 0 ? 'text-green-100' : 
                              p80Change < 0 ? 'text-red-200' : 
                              'text-blue-100'
                            }`}>
                              {p80Change > 0 ? '-' : p80Change < 0 ? '+' : ''}{Math.abs(p80Change).toFixed(1)} days
                            </span>
                          </div>
                        </div>
                        {hasNegativeImpact && (
                          <div className="mt-2 p-2 bg-red-500/20 rounded border border-red-300/30">
                            <p className="text-xs text-red-100">
                              ⚠️ This change increases project duration. Consider alternative mitigation strategies.
                            </p>
                          </div>
                        )}
                        {isNeutral && (
                          <div className="mt-2 p-2 bg-blue-500/20 rounded border border-blue-300/30">
                            <p className="text-xs text-blue-100">
                              ℹ️ This change has no impact on project duration. The change may affect other factors like cost or risk.
                            </p>
                          </div>
                        )}
                      </div>
                    )
                  })()}
                </div>
                )
              })()}

              {error && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-red-800 text-xs font-medium">
                  {error}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Feedback Widget - NEW UX Enhancement */}
      <FeedbackWidget 
        feature="activity_explanation" 
        projectId={projectId}
        activityId={activityId}
        position="bottom-right"
      />
    </Layout>
  )
}
