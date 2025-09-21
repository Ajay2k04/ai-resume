import React, { createContext, useContext, useState } from 'react'

const WorkflowContext = createContext()

export const useWorkflow = () => {
  const context = useContext(WorkflowContext)
  if (!context) {
    throw new Error('useWorkflow must be used within a WorkflowProvider')
  }
  return context
}

export const WorkflowProvider = ({ children }) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [workflowData, setWorkflowData] = useState({
    resumeData: null,
    jobsData: null,
    selectedJob: null,
    generatedResume: null,
    generatedCoverLetter: null
  })

  const updateWorkflowData = (key, value) => {
    setWorkflowData(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const nextStep = () => {
    setCurrentStep(prev => Math.min(prev + 1, 4))
  }

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0))
  }

  const resetWorkflow = () => {
    setCurrentStep(0)
    setWorkflowData({
      resumeData: null,
      jobsData: null,
      selectedJob: null,
      generatedResume: null,
      generatedCoverLetter: null
    })
  }

  const value = {
    currentStep,
    workflowData,
    updateWorkflowData,
    nextStep,
    prevStep,
    resetWorkflow
  }

  return (
    <WorkflowContext.Provider value={value}>
      {children}
    </WorkflowContext.Provider>
  )
}
