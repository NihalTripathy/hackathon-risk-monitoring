'use client'

import { useMemo } from 'react'

interface ForecastChartProps {
  p50: number
  p80: number
  current: number
}

export default function ForecastChart({ p50, p80, current }: ForecastChartProps) {
  // OPTIMIZATION: Memoize calculations to avoid recalculation on every render
  const { maxDays, p50Position, p80Position, currentPosition, areClose } = useMemo(() => {
    const max = Math.max(p80 * 1.1, 100)
    const p50Pos = (p50 / max) * 100
    const p80Pos = (p80 / max) * 100
    // current is now in percentage (0-100), so use it directly as position percentage
    const currentPos = Math.min(current, 100)
    const positionDiff = Math.abs(p80Pos - p50Pos)
    const close = positionDiff < 8
    return {
      maxDays: max,
      p50Position: p50Pos,
      p80Position: p80Pos,
      currentPosition: currentPos,
      areClose: close
    }
  }, [p50, p80, current])

  return (
    <div className="w-full h-full flex flex-col">
      {/* Simple Explanation */}
      <div className="mb-4 space-y-2">
        <p className="text-xs text-gray-600">
          <strong>What this shows:</strong> When your project might finish based on current data
        </p>
      </div>

      {/* Timeline Visualization */}
      <div className="flex-1 flex flex-col justify-center">
        {/* Timeline Bar */}
        <div className="relative mb-6" style={{ minHeight: areClose ? '60px' : '40px' }}>
          <div className="h-4 bg-gray-200 rounded-full overflow-hidden relative">
            {/* Current Progress */}
            {current > 0 && (
              <div
                className="h-full bg-green-500 rounded-full transition-all duration-500 absolute top-0 left-0"
                style={{ width: `${currentPosition}%` }}
              />
            )}
            
            {/* Timeline markers on the bar */}
            {/* P50 marker */}
            <div 
              className="absolute top-1/2"
              style={{ left: `${p50Position}%`, transform: 'translate(-50%, -50%)' }}
            >
              <div className="w-5 h-5 bg-blue-500 rounded-full border-2 border-white shadow-lg relative z-10">
                <div className={`absolute left-1/2 -translate-x-1/2 whitespace-nowrap ${areClose ? '-bottom-6' : '-top-6'}`}>
                  <div className="text-[10px] font-bold text-blue-600">{p50} days</div>
                </div>
              </div>
            </div>

            {/* P80 marker */}
            <div 
              className="absolute top-1/2"
              style={{ left: `${p80Position}%`, transform: 'translate(-50%, -50%)' }}
            >
              <div className="w-5 h-5 bg-red-500 rounded-full border-2 border-white shadow-lg relative z-10">
                <div className={`absolute left-1/2 -translate-x-1/2 whitespace-nowrap ${areClose ? '-top-6' : '-top-6'}`}>
                  <div className="text-[10px] font-bold text-red-600">{p80} days</div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Timeline labels below */}
          <div className="flex justify-between mt-6 text-xs text-gray-500">
            <span>Start (Day 0)</span>
            <span>End ({Math.ceil(maxDays)} days)</span>
          </div>
        </div>

        {/* Legend */}
        <div className="grid grid-cols-3 gap-3 mt-4">
          <div className="flex items-start gap-2 p-2 bg-blue-50 rounded border border-blue-200">
            <div className="w-3 h-3 bg-blue-500 rounded-full mt-0.5 flex-shrink-0"></div>
            <div>
              <div className="text-xs font-semibold text-blue-900">Most Likely</div>
              <div className="text-xs text-blue-700">{p50} days</div>
              <div className="text-[10px] text-blue-600">50% confidence</div>
            </div>
          </div>

          <div className="flex items-start gap-2 p-2 bg-red-50 rounded border border-red-200">
            <div className="w-3 h-3 bg-red-500 rounded-full mt-0.5 flex-shrink-0"></div>
            <div>
              <div className="text-xs font-semibold text-red-900">Worst Case</div>
              <div className="text-xs text-red-700">{p80} days</div>
              <div className="text-[10px] text-red-600">80% confidence</div>
            </div>
          </div>

          <div className="flex items-start gap-2 p-2 bg-green-50 rounded border border-green-200">
            <div className="w-3 h-3 bg-green-500 rounded-full mt-0.5 flex-shrink-0"></div>
            <div>
              <div className="text-xs font-semibold text-green-900">Progress</div>
              <div className="text-xs text-green-700">{current.toFixed(1)}%</div>
              <div className="text-[10px] text-green-600">completed</div>
            </div>
          </div>
        </div>

        {/* Simple Summary */}
        <div className="mt-4 p-3 bg-gray-50 rounded border border-gray-200">
          <p className="text-xs text-gray-700">
            <strong>Summary:</strong> Your project will most likely finish in <strong className="text-blue-600">{p50} days</strong>, 
            but could take up to <strong className="text-red-600">{p80} days</strong> in worst-case scenarios.
          </p>
        </div>
      </div>
    </div>
  )
}

