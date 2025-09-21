import React from 'react'
import { Briefcase, Sparkles } from 'lucide-react'
import { useWorkflow } from '../context/WorkflowContext'

const Header = () => {
  const { currentStep } = useWorkflow()
  const totalSteps = 5
  return (
    <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl">
              <Briefcase className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text">QuantiPeak</h1>
              <p className="text-xs text-gray-500">AI Recruitment Platform</p>
            </div>
          </div>
          
          {/* Progress */}
          <div className="hidden md:flex items-center space-x-4">
            <div className="text-sm text-gray-600">
              Step {currentStep + 1} of {totalSteps}
            </div>
              <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-blue-600 to-indigo-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
                  />
              </div>
          </div>
          
          {/* AI Badge */}
          <div className="flex items-center space-x-2 px-3 py-1 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-full border border-blue-200">
            <Sparkles className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-700">AI Powered</span>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header