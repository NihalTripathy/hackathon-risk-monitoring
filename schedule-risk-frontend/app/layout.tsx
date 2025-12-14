import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/contexts/AuthContext'

const inter = Inter({ subsets: ['latin'] })

// Comprehensive SEO metadata for professional app
export const metadata: Metadata = {
  title: {
    default: 'Schedule Risk Monitoring - Advanced Project Risk Analysis & Forecasting',
    template: '%s | Schedule Risk Monitoring'
  },
  description: 'Professional project risk monitoring and forecasting platform. Analyze schedule risks, detect anomalies, forecast completion dates with Monte Carlo simulation, and get AI-powered risk explanations. Perfect for project managers and PMO teams.',
  keywords: [
    'project risk management',
    'schedule risk analysis',
    'project forecasting',
    'Monte Carlo simulation',
    'project management',
    'risk monitoring',
    'schedule analysis',
    'project analytics',
    'PMO tools',
    'project risk assessment',
    'critical path analysis',
    'resource risk analysis'
  ],
  authors: [{ name: 'Schedule Risk Monitoring Team' }],
  creator: 'Schedule Risk Monitoring',
  publisher: 'Schedule Risk Monitoring',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: '/',
    siteName: 'Schedule Risk Monitoring',
    title: 'Schedule Risk Monitoring - Advanced Project Risk Analysis & Forecasting',
    description: 'Professional project risk monitoring and forecasting platform. Analyze schedule risks, detect anomalies, and forecast completion dates with AI-powered insights.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Schedule Risk Monitoring Dashboard',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Schedule Risk Monitoring - Advanced Project Risk Analysis',
    description: 'Professional project risk monitoring and forecasting platform with AI-powered insights.',
    images: ['/og-image.png'],
    creator: '@riskmonitor',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    // Add your verification codes here when available
    // google: 'your-google-verification-code',
    // yandex: 'your-yandex-verification-code',
    // bing: 'your-bing-verification-code',
  },
  category: 'Project Management Software',
  classification: 'Business Software',
  applicationName: 'Schedule Risk Monitoring',
  referrer: 'origin-when-cross-origin',
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
    other: [
      { rel: 'mask-icon', url: '/favicon.svg', color: '#2563eb' },
    ],
  },
  manifest: '/site.webmanifest',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Risk Monitor',
  },
  other: {
    'application-name': 'Schedule Risk Monitoring',
    'apple-mobile-web-app-capable': 'yes',
    'apple-mobile-web-app-status-bar-style': 'default',
    'apple-mobile-web-app-title': 'Risk Monitor',
    'mobile-web-app-capable': 'yes',
    'msapplication-TileColor': '#2563eb',
    'msapplication-config': '/browserconfig.xml',
  },
}

// Viewport configuration (separate export as required by Next.js 14)
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#2563eb' },
    { media: '(prefers-color-scheme: dark)', color: '#1e40af' },
  ],
  colorScheme: 'light',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
