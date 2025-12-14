'use client'

import { Clock, Users, Network, AlertTriangle, TrendingUp } from 'lucide-react'

interface ForensicInsightsProps {
  insights?: {
    drift_activities: number
    skill_bottlenecks: number
    high_risk_clusters: number
    bridge_nodes: number
  }
}

export default function ForensicInsights({ insights }: ForensicInsightsProps) {
  if (!insights) return null

  const cards = [
    {
      icon: Clock,
      label: 'Drift Activities',
      value: insights.drift_activities,
      color: 'blue',
      description: 'Activities with baseline drift'
    },
    {
      icon: Users,
      label: 'Skill Bottlenecks',
      value: insights.skill_bottlenecks,
      color: 'orange',
      description: 'Resource skill conflicts'
    },
    {
      icon: Network,
      label: 'Bridge Nodes',
      value: insights.bridge_nodes,
      color: 'purple',
      description: 'Critical path connections'
    },
    {
      icon: AlertTriangle,
      label: 'High-Risk Clusters',
      value: insights.high_risk_clusters,
      color: 'red',
      description: 'ML-identified risk patterns'
    }
  ]

  return (
    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg border border-indigo-200 p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp className="w-5 h-5 text-indigo-600" />
        <h3 className="text-sm font-bold text-gray-900">Forensic Intelligence Insights</h3>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {cards.map((card, idx) => {
          const Icon = card.icon
          const colorClasses = {
            blue: 'bg-blue-100 text-blue-700 border-blue-200',
            orange: 'bg-orange-100 text-orange-700 border-orange-200',
            purple: 'bg-purple-100 text-purple-700 border-purple-200',
            red: 'bg-red-100 text-red-700 border-red-200'
          }
          
          return (
            <div
              key={idx}
              className={`p-3 rounded-lg border ${colorClasses[card.color as keyof typeof colorClasses]}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Icon className="w-4 h-4" />
                <span className="text-xs font-semibold">{card.label}</span>
              </div>
              <div className="text-2xl font-bold">{card.value}</div>
              <div className="text-[10px] text-gray-600 mt-1">{card.description}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
