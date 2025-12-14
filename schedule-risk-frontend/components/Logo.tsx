'use client'

import Link from 'next/link'
import { Activity } from 'lucide-react'

interface LogoProps {
  className?: string
  showText?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export default function Logo({ className = '', showText = true, size = 'md' }: LogoProps) {
  const sizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-6 h-6',
  }

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-lg',
    lg: 'text-xl',
  }

  return (
    <Link 
      href="/" 
      className={`flex items-center gap-2 font-bold text-gray-900 hover:text-primary-600 transition-colors ${className}`}
      aria-label="Schedule Risk Monitoring - Home"
    >
      <div className={`p-1.5 bg-primary-600 rounded-lg ${sizeClasses[size]}`}>
        <Activity className={`${sizeClasses[size]} text-white`} />
      </div>
      {showText && (
        <span className={textSizeClasses[size]}>Risk Monitor</span>
      )}
    </Link>
  )
}

