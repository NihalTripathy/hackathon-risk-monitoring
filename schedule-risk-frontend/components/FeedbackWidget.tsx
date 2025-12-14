'use client'

import { useState } from 'react'
import { ThumbsUp, ThumbsDown, MessageSquare, X, CheckCircle } from 'lucide-react'
import { submitFeedback } from '@/lib/api'

interface FeedbackWidgetProps {
  feature: string
  projectId?: string
  activityId?: string
  position?: 'top-right' | 'bottom-right' | 'inline'
}

export default function FeedbackWidget({ 
  feature, 
  projectId, 
  activityId,
  position = 'bottom-right' 
}: FeedbackWidgetProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [rating, setRating] = useState<number | null>(null)
  const [comment, setComment] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (rating === null) return

    setSubmitting(true)
    try {
      await submitFeedback({
        feature,
        project_id: projectId,
        activity_id: activityId,
        rating,
        comment: comment.trim() || undefined,
      })
      setSubmitted(true)
      setTimeout(() => {
        setIsOpen(false)
        setSubmitted(false)
        setRating(null)
        setComment('')
      }, 2000)
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    } finally {
      setSubmitting(false)
    }
  }

  if (position === 'inline') {
    return (
      <div className="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-200">
        <span className="text-xs text-gray-600">Was this helpful?</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => {
              setRating(1)
              handleSubmit()
            }}
            disabled={submitting || submitted}
            className={`p-1.5 rounded transition-colors ${
              rating === 1 || submitted
                ? 'bg-green-100 text-green-700'
                : 'bg-white text-gray-600 hover:bg-gray-100'
            }`}
          >
            <ThumbsUp className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              setRating(0)
              setIsOpen(true)
            }}
            disabled={submitting || submitted}
            className={`p-1.5 rounded transition-colors ${
              rating === 0
                ? 'bg-red-100 text-red-700'
                : 'bg-white text-gray-600 hover:bg-gray-100'
            }`}
          >
            <ThumbsDown className="w-4 h-4" />
          </button>
        </div>
        {submitted && (
          <span className="text-xs text-green-600 flex items-center gap-1">
            <CheckCircle className="w-3 h-3" />
            Thank you!
          </span>
        )}
      </div>
    )
  }

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className={`fixed ${position === 'bottom-right' ? 'bottom-6 right-6' : 'top-6 right-6'} z-50 bg-primary-600 hover:bg-primary-700 text-white p-3 rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center gap-2 group`}
        >
          <MessageSquare className="w-5 h-5" />
          <span className="text-sm font-medium hidden sm:inline group-hover:inline">Feedback</span>
        </button>
      )}

      {/* Feedback Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md mx-4 animate-scale-in">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900">Share Your Feedback</h3>
                <button
                  onClick={() => {
                    setIsOpen(false)
                    setRating(null)
                    setComment('')
                    setSubmitted(false)
                  }}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {!submitted ? (
                <>
                  <p className="text-sm text-gray-600 mb-4">
                    How helpful was the <strong>{feature}</strong> feature?
                  </p>

                  <div className="flex items-center gap-4 mb-4">
                    <button
                      onClick={() => setRating(1)}
                      className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                        rating === 1
                          ? 'border-green-500 bg-green-50'
                          : 'border-gray-200 hover:border-green-300'
                      }`}
                    >
                      <ThumbsUp className="w-6 h-6 mx-auto mb-2 text-green-600" />
                      <span className="text-sm font-medium">Helpful</span>
                    </button>
                    <button
                      onClick={() => setRating(0)}
                      className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                        rating === 0
                          ? 'border-red-500 bg-red-50'
                          : 'border-gray-200 hover:border-red-300'
                      }`}
                    >
                      <ThumbsDown className="w-6 h-6 mx-auto mb-2 text-red-600" />
                      <span className="text-sm font-medium">Not Helpful</span>
                    </button>
                  </div>

                  {rating === 0 && (
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        What can we improve? (Optional)
                      </label>
                      <textarea
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        placeholder="Share your thoughts..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none resize-none"
                        rows={3}
                      />
                    </div>
                  )}

                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleSubmit}
                      disabled={rating === null || submitting}
                      className="flex-1 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium py-2.5 px-4 rounded-lg transition-colors"
                    >
                      {submitting ? 'Submitting...' : 'Submit Feedback'}
                    </button>
                    <button
                      onClick={() => {
                        setIsOpen(false)
                        setRating(null)
                        setComment('')
                      }}
                      className="px-4 py-2.5 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                  <h4 className="text-lg font-bold text-gray-900 mb-2">Thank You!</h4>
                  <p className="text-sm text-gray-600">Your feedback helps us improve.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

