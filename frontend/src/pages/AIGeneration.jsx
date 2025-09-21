import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, FileText, Mail, Loader2, CheckCircle, ArrowRight } from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import Modal from '../components/Modal'
import { useWorkflow } from '../context/WorkflowContext'

const AIGeneration = () => {
  const navigate = useNavigate()
  const { workflowData, updateWorkflowData, nextStep } = useWorkflow()
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationStep, setGenerationStep] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [modalContent, setModalContent] = useState({ type: '', title: '', message: '' })

  const showNotification = (type, title, message) => {
    setModalContent({ type, title, message })
    setShowModal(true)
  }

  const handleGenerate = async () => {
    if (!workflowData.resumeData || !workflowData.selectedJob) {
      showNotification('error', 'Missing Data', 'Please ensure you have uploaded a resume and selected a job.')
      return
    }

    setIsGenerating(true)
    
    try {
      // Generate Resume
      setGenerationStep('Customizing your resume...')
      const resumeResponse = await fetch('/api/ai/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contentType: 'resume',
          resume_data: workflowData.resumeData,
          job_description: workflowData.selectedJob.description || '',
          job_title: workflowData.selectedJob.title || '',
          company_name: workflowData.selectedJob.company || ''
        })
      })

      if (!resumeResponse.ok) {
        throw new Error('Failed to generate resume')
      }

      const resumeData = await resumeResponse.json()
      updateWorkflowData('generatedResume', resumeData.content)

      // Generate Cover Letter
      setGenerationStep('Creating your cover letter...')
      const coverLetterResponse = await fetch('/api/ai/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contentType: 'cover_letter',
          resume_data: workflowData.resumeData,
          job_description: workflowData.selectedJob.description || '',
          job_title: workflowData.selectedJob.title || '',
          company_name: workflowData.selectedJob.company || ''
        })
      })

      if (!coverLetterResponse.ok) {
        throw new Error('Failed to generate cover letter')
      }

      const coverLetterData = await coverLetterResponse.json()
      updateWorkflowData('generatedCoverLetter', coverLetterData.content)

      showNotification('success', 'Generation Complete', 'Your personalized resume and cover letter are ready!')
      
      setTimeout(() => {
        nextStep()
        navigate('/step/4')
      }, 1500)

    } catch (error) {
      console.error('Error generating documents:', error)
      showNotification('error', 'Generation Failed', 'Unable to generate documents. Please try again.')
    } finally {
      setIsGenerating(false)
      setGenerationStep('')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl mb-4">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Document Generation</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Our AI will customize your resume and create a compelling cover letter tailored to your selected job.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Resume Generation */}
          <Card className="animate-slide-up">
            <Card.Header>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Resume Customization</h2>
                  <p className="text-gray-600 text-sm">Tailored to your target job</p>
                </div>
              </div>
            </Card.Header>
            
            <Card.Content>
              <div className="space-y-4">
                <div className="flex items-center space-x-3 text-sm text-gray-600">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Optimize keywords for ATS systems</span>
                </div>
                <div className="flex items-center space-x-3 text-sm text-gray-600">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Highlight relevant experience</span>
                </div>
                <div className="flex items-center space-x-3 text-sm text-gray-600">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Align skills with job requirements</span>
                </div>
                <div className="flex items-center space-x-3 text-sm text-gray-600">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Professional formatting</span>
                </div>
              </div>
            </Card.Content>
          </Card>

          {/* Cover Letter Generation */}
          <Card className="animate-slide-up">
            <Card.Header>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                  <Mail className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Cover Letter Creation</h2>
                  <p className="text-gray-600 text-sm">Personalized and compelling</p>
                </div>
              </div>
            </Card.Header>
            
            <Card.Content>
              <div className="space-y-4">
                <div className="flex items-center space-x-3 text-sm text-gray-600">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Company-specific messaging</span>
                </div>
                <div className="flex items-center space-x-3 text-sm text-gray-600">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Highlight relevant achievements</span>
                </div>
                <div className="flex items-center space-x-3 text-sm text-gray-600">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Professional tone and structure</span>
                </div>
                <div className="flex items-center space-x-3 text-sm text-gray-600">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Call-to-action for interview</span>
                </div>
              </div>
            </Card.Content>
          </Card>
        </div>

        {/* Job Summary */}
        {workflowData.selectedJob && (
          <Card className="mt-8 animate-slide-up">
            <Card.Header>
              <h3 className="text-lg font-semibold text-gray-900">Target Job Summary</h3>
            </Card.Header>
            <Card.Content>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">{workflowData.selectedJob.title}</h4>
                  <p className="text-gray-600 mb-1">{workflowData.selectedJob.company}</p>
                  <p className="text-gray-500 text-sm">{workflowData.selectedJob.location}</p>
                </div>
                <div>
                  <h5 className="font-medium text-gray-900 mb-2">Key Requirements</h5>
                  <p className="text-gray-600 text-sm">
                    {workflowData.selectedJob.description?.substring(0, 200)}...
                  </p>
                </div>
              </div>
            </Card.Content>
          </Card>
        )}

        {/* Generation Status */}
        {isGenerating && (
          <Card className="mt-8 animate-slide-up">
            <Card.Content className="text-center py-8">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Loader2 className="w-8 h-8 text-white animate-spin" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Generating Documents</h3>
              <p className="text-gray-600">{generationStep}</p>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-4">
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
              </div>
            </Card.Content>
          </Card>
        )}

        {/* Generate Button */}
        <div className="flex justify-center mt-8">
          <Button
            onClick={handleGenerate}
            loading={isGenerating}
            disabled={!workflowData.resumeData || !workflowData.selectedJob}
            size="lg"
            className="px-8"
          >
            {isGenerating ? 'Generating...' : 'Generate Documents'}
            <Sparkles className="w-5 h-5 ml-2" />
          </Button>
        </div>

        {/* Tips */}
        <Card className="mt-8 animate-slide-up">
          <Card.Header>
            <h3 className="text-lg font-semibold text-gray-900">AI Generation Tips</h3>
          </Card.Header>
          <Card.Content>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Quality Input</h4>
                <p className="text-sm text-gray-600">Better resume data leads to better AI output</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <Sparkles className="w-6 h-6 text-green-600" />
                </div>
                <h4 className="font-medium text-gray-900 mb-2">AI Optimization</h4>
                <p className="text-sm text-gray-600">Our AI optimizes for ATS and human readers</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <CheckCircle className="w-6 h-6 text-purple-600" />
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Review & Edit</h4>
                <p className="text-sm text-gray-600">Always review generated content before applying</p>
              </div>
            </div>
          </Card.Content>
        </Card>
      </div>

      {/* Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={modalContent.title}
        type={modalContent.type}
      >
        <p className="text-gray-600">{modalContent.message}</p>
      </Modal>
    </div>
  )
}

export default AIGeneration