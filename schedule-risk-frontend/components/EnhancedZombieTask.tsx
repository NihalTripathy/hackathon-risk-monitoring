'use client'

import { AlertTriangle, Clock, Users, ArrowRight, ExternalLink } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface EnhancedZombieTaskProps {
  zombie: {
    activity_id: string
    name: string
    days_overdue: number
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
  }
  projectId: string
}

export default function EnhancedZombieTask({ zombie, projectId }: EnhancedZombieTaskProps) {
  const router = useRouter()
  
  const impact = zombie.business_impact || zombie.enhanced_explanation?.impact
  const explanation = zombie.enhanced_explanation || {}
  const plainLanguage = zombie.plain_language || impact?.plain_language || explanation.summary
  
  const blockedCount = impact?.blocked_tasks || impact?.blocked_tasks_count || 0
  const blockedNames = impact?.blocked_task_names || []
  const urgencyDays = impact?.urgency_days ?? 0
  const severity = impact?.severity || (zombie.days_overdue > 7 ? 'critical' : zombie.days_overdue > 3 ? 'high' : 'medium')
  
  const severityColors = {
    critical: 'bg-red-100 border-red-300 text-red-900',
    high: 'bg-orange-100 border-orange-300 text-orange-900',
    medium: 'bg-yellow-100 border-yellow-300 text-yellow-900',
  }

  return (
    <div className={`rounded-lg border-2 p-4 ${severityColors[severity as keyof typeof severityColors] || severityColors.medium}`}>
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <h4 className="font-bold text-sm">Zombie Task Detected</h4>
            <span className="text-xs font-mono bg-white/80 px-2 py-0.5 rounded border">
              {zombie.activity_id}
            </span>
          </div>
          <p className="font-semibold text-sm mb-1">{zombie.name}</p>
        </div>
        <button
          onClick={() => router.push(`/projects/${projectId}/activities/${zombie.activity_id}`)}
          className="flex items-center gap-1 text-xs font-medium hover:underline transition-colors"
        >
          View Details
          <ExternalLink className="w-3 h-3" />
        </button>
      </div>

      {/* Plain Language Explanation */}
      {plainLanguage && (
        <div className="mb-3 p-3 bg-white/80 rounded border border-white/50">
          <p className="text-xs leading-relaxed text-gray-800">{plainLanguage}</p>
        </div>
      )}

      {/* Business Impact */}
      <div className="space-y-2 mb-3">
        <div className="flex items-center gap-2 text-xs">
          <Clock className="w-4 h-4" />
          <span className="font-semibold">{zombie.days_overdue} days overdue</span>
        </div>
        
        {blockedCount > 0 && (
          <div className="flex items-start gap-2 text-xs">
            <Users className="w-4 h-4 mt-0.5" />
            <div>
              <span className="font-semibold">Blocking {blockedCount} downstream task{blockedCount !== 1 ? 's' : ''}</span>
              {blockedNames.length > 0 && (
                <div className="mt-1 text-xs opacity-90">
                  {blockedNames.slice(0, 3).map((name, idx) => (
                    <span key={idx} className="inline-block mr-2">
                      {name}{idx < Math.min(blockedNames.length, 3) - 1 ? ',' : ''}
                    </span>
                  ))}
                  {blockedNames.length > 3 && <span>...</span>}
                </div>
              )}
            </div>
          </div>
        )}

        {urgencyDays !== undefined && urgencyDays <= 0 && (
          <div className="flex items-center gap-2 text-xs font-semibold">
            <AlertTriangle className="w-4 h-4" />
            <span>Immediate action required</span>
          </div>
        )}
        {urgencyDays !== undefined && urgencyDays > 0 && (
          <div className="flex items-center gap-2 text-xs">
            <Clock className="w-4 h-4" />
            <span>Approximately {urgencyDays} days until critical impact</span>
          </div>
        )}
      </div>

      {/* Recommended Actions */}
      {(zombie.recommended_action || explanation.suggestions) && (
        <div className="mt-3 pt-3 border-t border-current/20">
          <h5 className="text-xs font-bold mb-2 uppercase tracking-wide">Recommended Actions</h5>
          {zombie.recommended_action && (
            <p className="text-xs mb-2">{zombie.recommended_action}</p>
          )}
          {explanation.suggestions && explanation.suggestions.length > 0 && (
            <ul className="space-y-1.5">
              {explanation.suggestions.map((suggestion, idx) => (
                <li key={idx} className="flex items-start gap-2 text-xs">
                  <ArrowRight className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Reasons */}
      {explanation.reasons && explanation.reasons.length > 0 && (
        <div className="mt-3 pt-3 border-t border-current/20">
          <h5 className="text-xs font-bold mb-2 uppercase tracking-wide">Why This Matters</h5>
          <ul className="space-y-1.5">
            {explanation.reasons.map((reason, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-current mt-1.5 flex-shrink-0"></span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

