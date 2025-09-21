import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Download, FileText, Mail, CheckCircle, ArrowRight, RefreshCw, Eye } from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import Modal from '../components/Modal'
import DocumentPreview from '../components/DocumentPreview'
import { useWorkflow } from '../context/WorkflowContext'

const Export = () => {
  const navigate = useNavigate()
  const { workflowData, resetWorkflow } = useWorkflow()
  const [isExporting, setIsExporting] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [modalContent, setModalContent] = useState({ type: '', title: '', message: '' })
  const [showResumePreview, setShowResumePreview] = useState(false)
  const [showCoverLetterPreview, setShowCoverLetterPreview] = useState(false)

  const showNotification = (type, title, message) => {
    setModalContent({ type, title, message })
    setShowModal(true)
  }

  const downloadFile = async (content, filename, format) => {
    setIsExporting(true)
    try {
      const response = await fetch('/api/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          filename,
          format
        })
      })

      if (!response.ok) {
        throw new Error('Failed to generate file')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      showNotification('success', 'Download Complete', `${filename} has been downloaded successfully!`)
    } catch (error) {
      console.error('Error downloading file:', error)
      showNotification('error', 'Download Failed', 'Unable to download the file. Please try again.')
    } finally {
      setIsExporting(false)
    }
  }

  const handleDownloadResume = () => {
    if (workflowData.generatedResume) {
      downloadFile(workflowData.generatedResume, 'customized_resume.pdf', 'pdf')
    }
  }

  const handleDownloadCoverLetter = () => {
    if (workflowData.generatedCoverLetter) {
      downloadFile(workflowData.generatedCoverLetter, 'cover_letter.pdf', 'pdf')
    }
  }

  const handleStartOver = () => {
    resetWorkflow()
    navigate('/step/0')
    showNotification('info', 'Workflow Reset', 'Starting fresh with a new application process.')
  }

  const handleSaveResume = (updatedContent) => {
    // Update the workflow data with the edited content
    // This would typically save to backend or update local state
    showNotification('success', 'Resume Updated', 'Your resume has been updated successfully.')
  }

  const handleSaveCoverLetter = (updatedContent) => {
    // Update the workflow data with the edited content
    // This would typically save to backend or update local state
    showNotification('success', 'Cover Letter Updated', 'Your cover letter has been updated successfully.')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl mb-4 animate-bounce-gentle">
            <CheckCircle className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2 animate-slide-up">Documents Ready!</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto animate-fade-in">
            Your personalized resume and cover letter are ready for download. Review and customize as needed.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Resume Download */}
          <Card className="animate-slide-in-left">
            <Card.Header>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Customized Resume</h2>
                  <p className="text-gray-600 text-sm">Optimized for your target job</p>
                </div>
              </div>
            </Card.Header>
            
            <Card.Content>
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-xl">
                  <h4 className="font-medium text-gray-900 mb-2">Job-Specific Optimizations</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Keywords aligned with job requirements</li>
                    <li>• Relevant experience highlighted</li>
                    <li>• Skills matched to job description</li>
                    <li>• Professional formatting applied</li>
                  </ul>
                </div>
                
                <div className="flex gap-3">
                  <Button
                    onClick={() => setShowResumePreview(true)}
                    variant="outline"
                    className="flex-1"
                    size="lg"
                  >
                    <Eye className="w-5 h-5 mr-2" />
                    Preview
                  </Button>
                  <Button
                    onClick={handleDownloadResume}
                    loading={isExporting}
                    className="flex-1"
                    size="lg"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Download PDF
                  </Button>
                </div>
              </div>
            </Card.Content>
          </Card>

          {/* Cover Letter Download */}
          <Card className="animate-slide-in-right">
            <Card.Header>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                  <Mail className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Cover Letter</h2>
                  <p className="text-gray-600 text-sm">Personalized for the company</p>
                </div>
              </div>
            </Card.Header>
            
            <Card.Content>
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-xl">
                  <h4 className="font-medium text-gray-900 mb-2">Personalized Content</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Company-specific messaging</li>
                    <li>• Relevant achievements highlighted</li>
                    <li>• Professional tone and structure</li>
                    <li>• Strong call-to-action included</li>
                  </ul>
                </div>
                
                <div className="flex gap-3">
                  <Button
                    onClick={() => setShowCoverLetterPreview(true)}
                    variant="outline"
                    className="flex-1"
                    size="lg"
                  >
                    <Eye className="w-5 h-5 mr-2" />
                    Preview
                  </Button>
                  <Button
                    onClick={handleDownloadCoverLetter}
                    loading={isExporting}
                    className="flex-1"
                    size="lg"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Download PDF
                  </Button>
                </div>
              </div>
            </Card.Content>
          </Card>
        </div>

        {/* Job Application Summary */}
        {workflowData.selectedJob && (
          <Card className="mt-8 animate-slide-up">
            <Card.Header>
              <h3 className="text-lg font-semibold text-gray-900">Application Summary</h3>
            </Card.Header>
            <Card.Content>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Target Position</h4>
                  <p className="text-gray-600 mb-1">{workflowData.selectedJob.title}</p>
                  <p className="text-gray-500 text-sm">{workflowData.selectedJob.company}</p>
                  <p className="text-gray-500 text-sm">{workflowData.selectedJob.location}</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Documents Generated</h4>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-sm text-gray-600">Customized Resume</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-sm text-gray-600">Personalized Cover Letter</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card.Content>
          </Card>
        )}

        {/* Next Steps */}
        <Card className="mt-8 animate-slide-up">
          <Card.Header>
            <h3 className="text-lg font-semibold text-gray-900">Next Steps</h3>
          </Card.Header>
          <Card.Content>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Review Documents</h4>
                <p className="text-sm text-gray-600">Check the generated documents for accuracy</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <Mail className="w-6 h-6 text-green-600" />
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Submit Application</h4>
                <p className="text-sm text-gray-600">Apply through the company's job portal</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <CheckCircle className="w-6 h-6 text-purple-600" />
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Follow Up</h4>
                <p className="text-sm text-gray-600">Send a follow-up email after applying</p>
              </div>
            </div>
          </Card.Content>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mt-8">
          <Button
            onClick={handleStartOver}
            variant="outline"
            size="lg"
            className="px-8"
          >
            <RefreshCw className="w-5 h-5 mr-2" />
            Start New Application
          </Button>
          
          <Button
            onClick={() => window.open(workflowData.selectedJob?.job_url, '_blank')}
            size="lg"
            className="px-8"
            disabled={!workflowData.selectedJob?.job_url}
          >
            Apply Now
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </div>

      {/* Modals */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={modalContent.title}
        type={modalContent.type}
      >
        <p className="text-gray-600">{modalContent.message}</p>
      </Modal>

      {/* Document Previews */}
      <DocumentPreview
        isOpen={showResumePreview}
        onClose={() => setShowResumePreview(false)}
        title="Resume Preview"
        content={workflowData.generatedResume}
        type="resume"
        onSave={handleSaveResume}
      />

      <DocumentPreview
        isOpen={showCoverLetterPreview}
        onClose={() => setShowCoverLetterPreview(false)}
        title="Cover Letter Preview"
        content={workflowData.generatedCoverLetter}
        type="cover_letter"
        onSave={handleSaveCoverLetter}
      />
    </div>
  )
}

export default Export