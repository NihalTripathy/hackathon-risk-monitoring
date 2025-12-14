'use client'

import { Info, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react'
import { useState } from 'react'

interface ForecastExplanationProps {
  explanation?: {
    summary?: string
    details?: string
    plain_language?: string
    confidence_intervals?: Record<string, any>
    key_insights?: string[]
  }
  p50?: number
  p80?: number
  baselineFinishDays?: number
}

export default function ForecastExplanation({ explanation, p50, p80, baselineFinishDays }: ForecastExplanationProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!explanation && !p50 && !p80) {
    return null
  }

  const plainLanguage = explanation?.plain_language || explanation?.summary || explanation?.details

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-4 mb-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2 flex-1">
          <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="text-sm font-bold text-gray-900 mb-2 flex items-center gap-2">
              Forecast Explanation
              <span className="text-xs font-normal text-gray-600 bg-white px-2 py-0.5 rounded">
                Plain Language
              </span>
            </h3>
            
            {plainLanguage && (
              <div className="text-sm text-gray-700 leading-relaxed mb-3">
                <p className="whitespace-pre-line">{plainLanguage}</p>
              </div>
            )}

            {explanation?.key_insights && explanation.key_insights.length > 0 && (
              <div className="mt-3 space-y-2">
                <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Key Insights</h4>
                <ul className="space-y-1.5">
                  {explanation.key_insights.map((insight, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-xs text-gray-700">
                      <CheckCircle className="w-3.5 h-3.5 text-green-600 mt-0.5 flex-shrink-0" />
                      <span>{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {explanation?.details && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="mt-3 text-xs text-blue-600 hover:text-blue-700 font-medium underline transition-colors"
              >
                {isExpanded ? 'Show Less' : 'Show More Details'}
              </button>
            )}

            {isExpanded && explanation?.details && (
              <div className="mt-3 p-3 bg-white rounded border border-blue-100">
                <div className="text-xs text-gray-700 whitespace-pre-line leading-relaxed">
                  {explanation.details}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Visual comparison if baseline available */}
      {baselineFinishDays && p50 && (
        <div className="mt-4 pt-4 border-t border-blue-200">
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-blue-500"></div>
              <span className="text-gray-600">Baseline: <strong>{baselineFinishDays}</strong> days</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-indigo-500"></div>
              <span className="text-gray-600">P50 Forecast: <strong>{p50.toFixed(1)}</strong> days</span>
            </div>
            {p50 > baselineFinishDays && (
              <div className="flex items-center gap-1 text-red-600">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Delay: <strong>+{(p50 - baselineFinishDays).toFixed(1)}</strong> days</span>
              </div>
            )}
            {p50 < baselineFinishDays && (
              <div className="flex items-center gap-1 text-green-600">
                <TrendingUp className="w-3.5 h-3.5" />
                <span>Ahead: <strong>{(baselineFinishDays - p50).toFixed(1)}</strong> days</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

