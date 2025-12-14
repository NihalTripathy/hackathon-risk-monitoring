'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import {
  Bell,
  Webhook,
  Sliders,
  Save,
  Loader2,
  CheckCircle,
  X,
  Plus,
  Trash2,
  TestTube,
  Mail,
  Clock,
  ArrowLeft,
  Info,
  AlertTriangle,
} from 'lucide-react'
import {
  getNotificationPreferences,
  updateNotificationPreferences,
  getWebhooks,
  createWebhook,
  updateWebhook,
  deleteWebhook,
  testWebhook,
  getUserPreferences,
  updateUserPreferences,
  type NotificationPreferences,
  type WebhookConfig,
  type UserPreferences,
} from '@/lib/api'

export default function SettingsPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'notifications' | 'webhooks' | 'preferences'>('notifications')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previousPath, setPreviousPath] = useState<string | null>(null)

  // Detect previous page for back button
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Try to get from sessionStorage (set by Layout when navigating from project)
      const lastPath = sessionStorage.getItem('lastPath') || sessionStorage.getItem('lastProjectId')
      if (lastPath) {
        // If it's a project ID, construct the path
        if (lastPath.startsWith('/')) {
          setPreviousPath(lastPath)
        } else {
          setPreviousPath(`/projects/${lastPath}`)
        }
      } else {
        // Fallback: check document.referrer
        const referrer = document.referrer
        if (referrer) {
          try {
            const url = new URL(referrer)
            const path = url.pathname
            if (path && path !== '/settings' && path !== '/') {
              setPreviousPath(path)
            }
          } catch (e) {
            // Invalid URL, ignore
          }
        }
      }
    }
  }, [])

  // Notification preferences
  const [notifPrefs, setNotifPrefs] = useState<NotificationPreferences | null>(null)
  
  // Webhooks
  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([])
  const [showWebhookForm, setShowWebhookForm] = useState(false)
  const [editingWebhook, setEditingWebhook] = useState<WebhookConfig | null>(null)
  const [webhookForm, setWebhookForm] = useState({
    name: '',
    url: '',
    event_type: 'high_risk_alert',
    is_active: true,
  })

  // User preferences
  const [userPrefs, setUserPrefs] = useState<UserPreferences | null>(null)

  useEffect(() => {
    loadAllData()
  }, [])

  const loadAllData = async () => {
    setLoading(true)
    try {
      const [notif, webhooksData, prefs] = await Promise.all([
        getNotificationPreferences(),
        getWebhooks(),
        getUserPreferences(),
      ])
      setNotifPrefs(notif)
      setWebhooks(webhooksData)
      setUserPrefs(prefs)
      setError(null)
    } catch (error: any) {
      console.error('Failed to load settings:', error)
      setError(error.response?.data?.detail || 'Failed to load settings. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveNotifications = async () => {
    if (!notifPrefs) return
    setSaving(true)
    try {
      await updateNotificationPreferences(notifPrefs)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (error) {
      console.error('Failed to save notification preferences:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleSavePreferences = async () => {
    if (!userPrefs) return
    setSaving(true)
    setError(null)
    try {
      await updateUserPreferences(userPrefs)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (error: any) {
      console.error('Failed to save preferences:', error)
      setError(error.response?.data?.detail || 'Failed to save preferences')
    } finally {
      setSaving(false)
    }
  }

  const handleCreateWebhook = async () => {
    setSaving(true)
    try {
      if (editingWebhook) {
        await updateWebhook(editingWebhook.id, webhookForm)
      } else {
        await createWebhook(webhookForm)
      }
      await loadAllData()
      setShowWebhookForm(false)
      setEditingWebhook(null)
      setWebhookForm({ name: '', url: '', event_type: 'high_risk_alert', is_active: true })
    } catch (error) {
      console.error('Failed to save webhook:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteWebhook = async (id: number) => {
    if (!confirm('Are you sure you want to delete this webhook?')) return
    try {
      await deleteWebhook(id)
      await loadAllData()
    } catch (error) {
      console.error('Failed to delete webhook:', error)
    }
  }

  const handleTestWebhook = async (id: number) => {
    try {
      await testWebhook(id)
      alert('Test webhook sent successfully!')
    } catch (error) {
      alert('Failed to send test webhook. Check console for details.')
      console.error('Failed to test webhook:', error)
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => {
            if (previousPath) {
              router.push(previousPath)
            } else {
              // Try browser back, fallback to home
              if (typeof window !== 'undefined' && window.history.length > 1) {
                router.back()
              } else {
                router.push('/')
              }
            }
          }}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          {previousPath ? 'Back' : 'Back to Home'}
        </button>

        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Info className="w-4 h-4" />
            <span>Customize your experience</span>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('notifications')}
            className={`px-4 py-2 font-medium text-sm transition-colors ${
              activeTab === 'notifications'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Bell className="w-4 h-4 inline mr-2" />
            Notifications
          </button>
          <button
            onClick={() => setActiveTab('webhooks')}
            className={`px-4 py-2 font-medium text-sm transition-colors ${
              activeTab === 'webhooks'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Webhook className="w-4 h-4 inline mr-2" />
            Webhooks
          </button>
          <button
            onClick={() => setActiveTab('preferences')}
            className={`px-4 py-2 font-medium text-sm transition-colors ${
              activeTab === 'preferences'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Sliders className="w-4 h-4 inline mr-2" />
            Preferences
          </button>
        </div>

        {/* Notifications Tab */}
        {activeTab === 'notifications' && notifPrefs && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Email Notifications</h2>
            
            <div className="space-y-4">
              {/* Email Enabled Toggle */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <label className="font-medium text-gray-900">Enable Email Notifications</label>
                  <p className="text-sm text-gray-600 mt-1">Master switch for all email notifications</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifPrefs.email_enabled}
                    onChange={(e) => setNotifPrefs({ ...notifPrefs, email_enabled: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>

              {notifPrefs.email_enabled && (
                <>
                  {/* Risk Alerts */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <label className="font-medium text-gray-900">Risk Alerts</label>
                      <p className="text-sm text-gray-600 mt-1">Get notified immediately when activities reach high risk</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notifPrefs.email_risk_alerts}
                        onChange={(e) => setNotifPrefs({ ...notifPrefs, email_risk_alerts: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>

                  {notifPrefs.email_risk_alerts && (
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <label className="block font-medium text-gray-900 mb-2">
                        Risk Alert Threshold
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        value={notifPrefs.risk_alert_threshold}
                        onChange={(e) => setNotifPrefs({ ...notifPrefs, risk_alert_threshold: parseFloat(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                      <p className="text-xs text-gray-600 mt-1">Only activities with risk score ≥ {notifPrefs.risk_alert_threshold} will trigger alerts</p>
                    </div>
                  )}

                  {/* Daily Digest */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <label className="font-medium text-gray-900">Daily Digest</label>
                      <p className="text-sm text-gray-600 mt-1">Receive a daily summary of all project risks</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notifPrefs.email_daily_digest}
                        onChange={(e) => setNotifPrefs({ ...notifPrefs, email_daily_digest: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>

                  {/* Weekly Summary */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <label className="font-medium text-gray-900">Weekly Summary</label>
                      <p className="text-sm text-gray-600 mt-1">Get a weekly overview of portfolio health</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notifPrefs.email_weekly_summary}
                        onChange={(e) => setNotifPrefs({ ...notifPrefs, email_weekly_summary: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>

                  {/* Digest Frequency */}
                  {(notifPrefs.email_daily_digest || notifPrefs.email_weekly_summary) && (
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <label className="block font-medium text-gray-900 mb-2">
                        Digest Frequency
                      </label>
                      <select
                        value={notifPrefs.digest_frequency}
                        onChange={(e) => setNotifPrefs({ ...notifPrefs, digest_frequency: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      >
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="never">Never</option>
                      </select>
                      <p className="text-xs text-gray-600 mt-1">How often to receive digest emails</p>
                    </div>
                  )}
                </>
              )}

              <button
                onClick={handleSaveNotifications}
                disabled={saving}
                className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white font-medium py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Save Notification Settings
                  </>
                )}
              </button>

              {saveSuccess && (
                <div className="flex items-center gap-2 text-green-600 text-sm">
                  <CheckCircle className="w-4 h-4" />
                  Settings saved successfully!
                </div>
              )}
            </div>
          </div>
        )}

        {/* Webhooks Tab */}
        {activeTab === 'webhooks' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">Webhook Integrations</h2>
              <button
                onClick={() => {
                  setShowWebhookForm(true)
                  setEditingWebhook(null)
                  setWebhookForm({ name: '', url: '', event_type: 'high_risk_alert', is_active: true })
                }}
                className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Webhook
              </button>
            </div>

            {showWebhookForm && (
              <div className="bg-white rounded-lg border border-gray-200 p-6 mb-4">
                <h3 className="text-md font-bold text-gray-900 mb-4">
                  {editingWebhook ? 'Edit Webhook' : 'Create New Webhook'}
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block font-medium text-gray-900 mb-2">Name</label>
                    <input
                      type="text"
                      value={webhookForm.name}
                      onChange={(e) => setWebhookForm({ ...webhookForm, name: e.target.value })}
                      placeholder="e.g., Slack Alerts"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-gray-900 mb-2">Webhook URL</label>
                    <input
                      type="url"
                      value={webhookForm.url}
                      onChange={(e) => setWebhookForm({ ...webhookForm, url: e.target.value })}
                      placeholder="https://hooks.slack.com/services/..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-gray-900 mb-2">Event Type</label>
                    <select
                      value={webhookForm.event_type}
                      onChange={(e) => setWebhookForm({ ...webhookForm, event_type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="high_risk_alert">High Risk Alert</option>
                      <option value="anomaly_detected">Anomaly Detected</option>
                      <option value="project_update">Project Update</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={webhookForm.is_active}
                      onChange={(e) => setWebhookForm({ ...webhookForm, is_active: e.target.checked })}
                      className="w-4 h-4"
                    />
                    <label className="text-sm text-gray-700">Active</label>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleCreateWebhook}
                      disabled={saving || !webhookForm.name || !webhookForm.url}
                      className="flex-1 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                    >
                      {saving ? 'Saving...' : editingWebhook ? 'Update' : 'Create'}
                    </button>
                    <button
                      onClick={() => {
                        setShowWebhookForm(false)
                        setEditingWebhook(null)
                      }}
                      className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-3">
              {webhooks.length === 0 ? (
                <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
                  <Webhook className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-600">No webhooks configured</p>
                </div>
              ) : (
                webhooks.map((webhook) => (
                  <div key={webhook.id} className="bg-white rounded-lg border border-gray-200 p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-bold text-gray-900">{webhook.name}</h3>
                          {webhook.is_active ? (
                            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Active</span>
                          ) : (
                            <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">Inactive</span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-1">
                          <strong>URL:</strong> {webhook.url}
                        </p>
                        <p className="text-sm text-gray-600">
                          <strong>Event:</strong> {webhook.event_type}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleTestWebhook(webhook.id)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          title="Test webhook"
                        >
                          <TestTube className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            setEditingWebhook(webhook)
                            setWebhookForm({
                              name: webhook.name,
                              url: webhook.url,
                              event_type: webhook.event_type,
                              is_active: webhook.is_active,
                            })
                            setShowWebhookForm(true)
                          }}
                          className="p-2 text-gray-600 hover:bg-gray-100 rounded transition-colors"
                          title="Edit webhook"
                        >
                          <Sliders className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteWebhook(webhook.id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="Delete webhook"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Preferences Tab */}
        {activeTab === 'preferences' && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="mb-6">
              <h2 className="text-lg font-bold text-gray-900 mb-2">User Preferences</h2>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-blue-900 mb-2">What are Preferences?</h3>
                    <p className="text-sm text-blue-800 mb-2">
                      Preferences let you customize how the system displays and categorizes risks according to your team's standards. 
                      These settings only affect <strong>how risks are shown to you</strong> - they don't change the actual risk calculations.
                    </p>
                    <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                      <li><strong>Risk Thresholds:</strong> Define what counts as "High", "Medium", or "Low" risk for your organization</li>
                      <li><strong>Dashboard Layout:</strong> Control which sections appear on your dashboard and in what order</li>
                      <li><strong>Default Filters:</strong> Save your preferred filters for quick access when viewing projects</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
            
            {!userPrefs ? (
              <div className="text-center py-8">
                <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-3" />
                <p className="text-gray-600">Loading preferences...</p>
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Risk Thresholds</h3>
                  <p className="text-sm text-gray-600 mb-4">Customize how risks are categorized (for display only, doesn't affect calculations)</p>
                  
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block font-medium text-gray-900 mb-2">High Risk Threshold</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        value={userPrefs.risk_threshold_high ?? 70}
                        onChange={(e) => setUserPrefs({
                          ...userPrefs,
                          risk_threshold_high: parseFloat(e.target.value)
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">Activities with score ≥ this are "High Risk"</p>
                    </div>
                    <div>
                      <label className="block font-medium text-gray-900 mb-2">Medium Risk Threshold</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        value={userPrefs.risk_threshold_medium ?? 40}
                        onChange={(e) => setUserPrefs({
                          ...userPrefs,
                          risk_threshold_medium: parseFloat(e.target.value)
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">Activities with score ≥ this are "Medium Risk"</p>
                    </div>
                    <div>
                      <label className="block font-medium text-gray-900 mb-2">Low Risk Threshold</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        value={userPrefs.risk_threshold_low ?? 0}
                        onChange={(e) => setUserPrefs({
                          ...userPrefs,
                          risk_threshold_low: parseFloat(e.target.value)
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">Activities below medium are "Low Risk"</p>
                    </div>
                  </div>
                </div>

                {/* Dashboard Layout Preferences */}
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Dashboard Display Options</h3>
                  <p className="text-sm text-gray-600 mb-4">Control which sections appear on your project dashboard</p>
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <label className="font-medium text-gray-900">Show P50 Forecast First</label>
                        <p className="text-xs text-gray-600 mt-1">Display P50 (most likely) forecast before P80</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={userPrefs.show_p50_first ?? false}
                          onChange={(e) => setUserPrefs({ ...userPrefs, show_p50_first: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                      </label>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <label className="font-medium text-gray-900">Show P80 Forecast First</label>
                        <p className="text-xs text-gray-600 mt-1">Display P80 (conservative) forecast before P50</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={userPrefs.show_p80_first ?? true}
                          onChange={(e) => setUserPrefs({ ...userPrefs, show_p80_first: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                      </label>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <label className="font-medium text-gray-900">Show Anomalies Section</label>
                        <p className="text-xs text-gray-600 mt-1">Display zombie tasks and resource black holes</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={userPrefs.show_anomalies_section ?? true}
                          onChange={(e) => setUserPrefs({ ...userPrefs, show_anomalies_section: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                      </label>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <label className="font-medium text-gray-900">Show Resource Summary</label>
                        <p className="text-xs text-gray-600 mt-1">Display resource allocation summary on dashboard</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={userPrefs.show_resource_summary ?? false}
                          onChange={(e) => setUserPrefs({ ...userPrefs, show_resource_summary: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Default Filters */}
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Default Filters</h3>
                  <p className="text-sm text-gray-600 mb-4">Save your preferred filters for quick access when viewing projects</p>
                  
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-sm text-gray-600 mb-3">Filter preferences are saved automatically when you apply filters on project pages.</p>
                    <div className="text-xs text-gray-500">
                      <p className="mb-1"><strong>Current saved filters:</strong></p>
                      {userPrefs.default_filters && Object.keys(userPrefs.default_filters).length > 0 ? (
                        <ul className="list-disc list-inside space-y-1">
                          {Object.entries(userPrefs.default_filters).map(([key, value]) => (
                            <li key={key}>{key}: {JSON.stringify(value)}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-gray-400 italic">No filters saved yet. Apply filters on project pages to save them here.</p>
                      )}
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleSavePreferences}
                  disabled={saving || !userPrefs}
                  className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white font-medium py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {saving ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4" />
                      Save Preferences
                    </>
                  )}
                </button>

                {saveSuccess && (
                  <div className="flex items-center gap-2 text-green-600 text-sm">
                    <CheckCircle className="w-4 h-4" />
                    Preferences saved successfully!
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  )
}

