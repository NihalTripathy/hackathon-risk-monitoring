'use client'

import { useMemo } from 'react'
import { AlertCircle } from 'lucide-react'

interface ForensicForecastChartProps {
  standard: {
    p50: number
    p80: number
  }
  forensic: {
    p50: number
    p80: number
    p90?: number
    p95?: number
  }
  current: number
  forensicModulationApplied?: boolean
}

export default function ForensicForecastChart({
  standard,
  forensic,
  current,
  forensicModulationApplied = false
}: ForensicForecastChartProps) {
  const { maxDays, standardP50Pos, standardP80Pos, forensicP50Pos, forensicP80Pos, currentPos } = useMemo(() => {
    const max = Math.max(forensic.p80 * 1.1, standard.p80 * 1.1, 100)
    return {
      maxDays: max,
      standardP50Pos: (standard.p50 / max) * 100,
      standardP80Pos: (standard.p80 / max) * 100,
      forensicP50Pos: (forensic.p50 / max) * 100,
      forensicP80Pos: (forensic.p80 / max) * 100,
      currentPos: Math.min(current, 100)
    }
  }, [standard, forensic, current])

  const p50Diff = forensic.p50 - standard.p50
  const p80Diff = forensic.p80 - standard.p80

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-bold text-gray-900">Forecast Comparison</h2>
        {forensicModulationApplied && (
          <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
            Forensic Modulation Applied
          </span>
        )}
      </div>

      {/* Timeline Visualization */}
      <div className="relative mb-6" style={{ minHeight: '60px' }}>
        <div className="h-6 bg-gray-200 rounded-full overflow-hidden relative">
          {/* Current Progress */}
          {current > 0 && (
            <div
              className="h-full bg-green-500 rounded-full transition-all duration-500 absolute top-0 left-0"
              style={{ width: `${currentPos}%` }}
            />
          )}
          
          {/* Standard Forecast Markers */}
          <div 
            className="absolute top-1/2"
            style={{ left: `${standardP50Pos}%`, transform: 'translate(-50%, -50%)' }}
          >
            <div className="w-4 h-4 bg-blue-400 rounded-full border-2 border-white shadow-lg relative z-10">
              <div className="absolute left-1/2 -translate-x-1/2 -top-6 whitespace-nowrap">
                <div className="text-[10px] font-bold text-blue-600">Std P50: {standard.p50}d</div>
              </div>
            </div>
          </div>
          
          <div 
            className="absolute top-1/2"
            style={{ left: `${standardP80Pos}%`, transform: 'translate(-50%, -50%)' }}
          >
            <div className="w-4 h-4 bg-blue-600 rounded-full border-2 border-white shadow-lg relative z-10">
              <div className="absolute left-1/2 -translate-x-1/2 -top-6 whitespace-nowrap">
                <div className="text-[10px] font-bold text-blue-700">Std P80: {standard.p80}d</div>
              </div>
            </div>
          </div>

          {/* Forensic Forecast Markers */}
          <div 
            className="absolute top-1/2"
            style={{ left: `${forensicP50Pos}%`, transform: 'translate(-50%, -50%)' }}
          >
            <div className="w-4 h-4 bg-indigo-400 rounded-full border-2 border-white shadow-lg relative z-10">
              <div className="absolute left-1/2 -translate-x-1/2 -bottom-6 whitespace-nowrap">
                <div className="text-[10px] font-bold text-indigo-600">For P50: {forensic.p50}d</div>
              </div>
            </div>
          </div>
          
          <div 
            className="absolute top-1/2"
            style={{ left: `${forensicP80Pos}%`, transform: 'translate(-50%, -50%)' }}
          >
            <div className="w-4 h-4 bg-indigo-600 rounded-full border-2 border-white shadow-lg relative z-10">
              <div className="absolute left-1/2 -translate-x-1/2 -bottom-6 whitespace-nowrap">
                <div className="text-[10px] font-bold text-indigo-700">For P80: {forensic.p80}d</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-3 bg-blue-50 rounded border border-blue-200">
          <div className="text-xs font-semibold text-blue-900 mb-2">Standard Forecast</div>
          <div className="space-y-1">
            <div className="text-sm">
              <span className="text-gray-600">P50:</span> <strong className="text-blue-700">{standard.p50} days</strong>
            </div>
            <div className="text-sm">
              <span className="text-gray-600">P80:</span> <strong className="text-blue-700">{standard.p80} days</strong>
            </div>
          </div>
        </div>

        <div className="p-3 bg-indigo-50 rounded border border-indigo-200">
          <div className="text-xs font-semibold text-indigo-900 mb-2">Forensic Forecast</div>
          <div className="space-y-1">
            <div className="text-sm">
              <span className="text-gray-600">P50:</span> <strong className="text-indigo-700">{forensic.p50} days</strong>
              {p50Diff !== 0 && (
                <span className={`ml-2 text-xs ${p50Diff > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  ({p50Diff > 0 ? '+' : ''}{p50Diff.toFixed(1)} days)
                </span>
              )}
            </div>
            <div className="text-sm">
              <span className="text-gray-600">P80:</span> <strong className="text-indigo-700">{forensic.p80} days</strong>
              {p80Diff !== 0 && (
                <span className={`ml-2 text-xs ${p80Diff > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  ({p80Diff > 0 ? '+' : ''}{p80Diff.toFixed(1)} days)
                </span>
              )}
            </div>
            {forensic.p90 && (
              <div className="text-sm">
                <span className="text-gray-600">P90:</span> <strong className="text-indigo-700">{forensic.p90} days</strong>
              </div>
            )}
            {forensic.p95 && (
              <div className="text-sm">
                <span className="text-gray-600">P95:</span> <strong className="text-indigo-700">{forensic.p95} days</strong>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Explanation */}
      {forensicModulationApplied && (
        <div className="p-3 bg-indigo-50 rounded border border-indigo-200">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-indigo-600 mt-0.5 flex-shrink-0" />
            <div className="text-xs text-indigo-900">
              <strong>Forensic Intelligence Applied:</strong> This forecast accounts for baseline drift, skill bottlenecks, topology analysis, and ML-identified risk clusters to provide more accurate predictions.
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
