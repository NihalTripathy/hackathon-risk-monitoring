'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { User, login as apiLogin, register as apiRegister, getCurrentUser, logout as apiLogout } from '@/lib/api'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Check if user is already logged in
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token')
        if (token) {
          console.log('[AuthContext] Checking auth with token:', token.substring(0, 20) + '...')
          try {
            const currentUser = await getCurrentUser()
            setUser(currentUser)
            console.log('[AuthContext] User authenticated:', currentUser.email)
          } catch (authError: any) {
            // Only clear token if it's definitely invalid (not a network error)
            if (authError.response?.status === 401) {
              console.log('[AuthContext] Token invalid (401), clearing')
              localStorage.removeItem('auth_token')
            } else {
              // Network error or other issue - keep token, might work later
              console.warn('[AuthContext] Auth check failed but keeping token:', authError.message)
            }
          }
        } else {
          console.log('[AuthContext] No token found')
        }
      } catch (error: any) {
        console.error('[AuthContext] Unexpected error during auth check:', error)
        // Don't clear token on unexpected errors
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      console.log('[AuthContext] Attempting login for:', email)
      const response = await apiLogin(email, password)
      console.log('[AuthContext] Login successful, user:', response.user.email)
      setUser(response.user)
      
      // Verify token is set
      const token = localStorage.getItem('auth_token')
      if (!token) {
        console.error('[AuthContext] Token not set after login!')
        throw new Error('Token not set after login')
      }
      console.log('[AuthContext] Token verified, redirecting...')
      
      // Wait a bit to ensure token is set before redirecting
      await new Promise(resolve => setTimeout(resolve, 200))
      router.push('/')
    } catch (error: any) {
      console.error('[AuthContext] Login failed:', error)
      throw error
    }
  }

  const register = async (email: string, password: string, fullName?: string) => {
    const response = await apiRegister(email, password, fullName)
    setUser(response.user)
    // Wait a bit to ensure token is set before redirecting
    await new Promise(resolve => setTimeout(resolve, 100))
    router.push('/')
  }

  const logout = () => {
    apiLogout()
    setUser(null)
    router.push('/login')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

