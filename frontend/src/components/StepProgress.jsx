const StepProgress = ({ currentStep }) => {
  const steps = [
    { number: 1, title: 'Job Search', description: 'Find relevant job postings' },
    { number: 2, title: 'Resume Upload', description: 'Upload and parse your resume' },
    { number: 3, title: 'Job Selection', description: 'Choose target positions' },
    { number: 4, title: 'AI Generation', description: 'Generate tailored documents' },
    { number: 5, title: 'Export', description: 'Download your documents' }
  ]

  const getStepStatus = (stepNumber) => {
    if (stepNumber < currentStep) return 'completed'
    if (stepNumber === currentStep) return 'active'
    return 'pending'
  }

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={step.number} className="flex items-center">
            <div className="flex flex-col items-center">
              <div className={`step-indicator ${
                getStepStatus(step.number) === 'completed' ? 'step-completed' :
                getStepStatus(step.number) === 'active' ? 'step-active' :
                'step-pending'
              }`}>
                {getStepStatus(step.number) === 'completed' ? '✓' : step.number}
              </div>
              <div className="mt-2 text-center">
                <div className={`text-sm font-medium ${
                  getStepStatus(step.number) === 'active' ? 'text-primary-500' :
                  getStepStatus(step.number) === 'completed' ? 'text-green-500' :
                  'text-dark-400'
                }`}>
                  {step.title}
                </div>
                <div className="text-xs text-dark-500 mt-1">
                  {step.description}
                </div>
              </div>
            </div>
            {index < steps.length - 1 && (
              <div className={`flex-1 h-0.5 mx-4 ${
                step.number < currentStep ? 'bg-green-500' : 'bg-dark-600'
              }`} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default StepProgress
