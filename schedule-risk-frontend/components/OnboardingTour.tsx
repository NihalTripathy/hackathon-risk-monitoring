'use client'

import { useState } from 'react'
import { X, ArrowRight, CheckCircle } from 'lucide-react'
import { completeOnboardingTour, type OnboardingStep } from '@/lib/api'

interface OnboardingTourProps {
  tourId: string
  steps: OnboardingStep[]
  onComplete?: () => void
}

export default function OnboardingTour({ tourId, steps, onComplete }: OnboardingTourProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [completed, setCompleted] = useState(false)

  const handleNext = async () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      await handleComplete()
    }
  }

  const handleSkip = async () => {
    await handleComplete()
  }

  const handleComplete = async () => {
    try {
      await completeOnboardingTour(tourId)
      setCompleted(true)
      if (onComplete) {
        onComplete()
      }
    } catch (error) {
      console.error('Failed to complete onboarding tour:', error)
      // Still hide the tour even if API call fails
      setCompleted(true)
      if (onComplete) {
        onComplete()
      }
    }
  }

  if (completed || !steps || steps.length === 0 || currentStep >= steps.length) {
    return null
  }

  const step = steps[currentStep]
  if (!step) {
    return null
  }

  const targetElement = step.target_element ? document.querySelector(step.target_element) : null

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" />

      {/* Tour Card */}
      <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 bg-white rounded-lg shadow-2xl w-full max-w-md mx-4 animate-scale-in">
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-bold text-gray-900">{step.title}</h3>
              <p className="text-xs text-gray-500 mt-1">
                Step {currentStep + 1} of {steps.length}
              </p>
            </div>
            <button
              onClick={handleSkip}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <p className="text-sm text-gray-700 leading-relaxed mb-6">{step.description}</p>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleNext}
              className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {currentStep < steps.length - 1 ? (
                <>
                  Next
                  <ArrowRight className="w-4 h-4" />
                </>
              ) : (
                <>
                  Complete
                  <CheckCircle className="w-4 h-4" />
                </>
              )}
            </button>
            <button
              onClick={handleSkip}
              className="px-4 py-2.5 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Skip Tour
            </button>
          </div>
        </div>
      </div>

      {/* Highlight Target Element */}
      {targetElement && (
        <div
          className="fixed z-40 border-4 border-primary-500 rounded-lg pointer-events-none animate-pulse"
          style={{
            top: targetElement.getBoundingClientRect().top - 4,
            left: targetElement.getBoundingClientRect().left - 4,
            width: targetElement.getBoundingClientRect().width + 8,
            height: targetElement.getBoundingClientRect().height + 8,
          }}
        />
      )}
    </>
  )
}

