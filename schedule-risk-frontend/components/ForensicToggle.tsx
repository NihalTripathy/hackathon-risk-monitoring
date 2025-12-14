'use client'

import { Info, Brain, BarChart3 } from 'lucide-react'

interface ForensicToggleProps {
  isForensic: boolean
  onToggle: (isForensic: boolean) => void
  isLoading?: boolean
}

export default function ForensicToggle({ 
  isForensic, 
  onToggle, 
  isLoading = false 
}: ForensicToggleProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-gray-600" />
            <h3 className="text-sm font-semibold text-gray-900">Forecast Mode</h3>
          </div>
          
          {/* Toggle Switch */}
          <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => onToggle(false)}
              disabled={isLoading}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                !isForensic
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              Standard
            </button>
            <button
              onClick={() => onToggle(true)}
              disabled={isLoading}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                isForensic
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <Brain className="w-4 h-4" />
              Forensic
            </button>
          </div>
        </div>
        
        {/* Info Tooltip */}
        <div className="group relative">
          <Info className="w-5 h-5 text-gray-400 hover:text-gray-600 cursor-help" />
          <div className="absolute right-0 top-6 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
            <p className="font-semibold mb-1">Forensic Intelligence</p>
            <p>Uses advanced analytics including drift velocity, skill bottlenecks, topology analysis, and ML clustering to provide more accurate forecasts.</p>
          </div>
        </div>
      </div>
      
      {isLoading && (
        <div className="mt-3 flex items-center gap-2 text-xs text-indigo-600">
          <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <span>Loading forensic forecast...</span>
        </div>
      )}
    </div>
  )
}
