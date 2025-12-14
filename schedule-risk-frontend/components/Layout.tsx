'use client'

import { useMemo, useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, BarChart3, FileText, TrendingUp, Settings, Calendar } from 'lucide-react'
import Logo from './Logo'

interface LayoutProps {
  children: React.ReactNode
  projectId?: string
}

export default function Layout({ children, projectId }: LayoutProps) {
  const pathname = usePathname()
  const [detectedProjectId, setDetectedProjectId] = useState<string | null>(null)

  // Try to detect projectId from pathname if not provided
  useEffect(() => {
    if (!projectId && pathname) {
      const projectMatch = pathname.match(/\/projects\/([^\/]+)/)
      if (projectMatch) {
        setDetectedProjectId(projectMatch[1])
      } else {
        // Check if we came from a project page (stored in sessionStorage)
        const lastProjectId = typeof window !== 'undefined' ? sessionStorage.getItem('lastProjectId') : null
        if (lastProjectId) {
          setDetectedProjectId(lastProjectId)
        }
      }
    } else if (projectId) {
      setDetectedProjectId(projectId)
      // Store in sessionStorage for settings page
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('lastProjectId', projectId)
      }
    }
  }, [pathname, projectId])

  // OPTIMIZATION: Memoize nav items to avoid recreation on every render
  const navItems = useMemo(() => {
    const activeProjectId = projectId || detectedProjectId
    
    // Always show Home and Settings
    const baseItems = [
      { href: '/', label: 'Home', icon: Home },
      { href: '/settings', label: 'Settings', icon: Settings },
    ]

    // If we have a project ID, add project-specific navigation
    if (activeProjectId) {
      return [
        { href: `/projects/${activeProjectId}`, label: 'Dashboard', icon: BarChart3 },
        { href: `/projects/${activeProjectId}/gantt`, label: 'Gantt Chart', icon: Calendar },
        { href: `/projects/${activeProjectId}/analytics`, label: 'Analytics', icon: TrendingUp },
        { href: `/projects/${activeProjectId}/audit`, label: 'Audit Log', icon: FileText },
        ...baseItems,
      ]
    }

    return baseItems
  }, [projectId, detectedProjectId])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Compact Navigation */}
      <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-gray-200 shadow-sm">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-14">
            <Logo size="md" showText={true} />
            <div className="flex items-center gap-1.5">
              {navItems.map((item, index) => {
                const Icon = item.icon
                const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-primary-600 text-white shadow-sm'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{item.label}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-4 animate-fade-in">{children}</main>
    </div>
  )
}

