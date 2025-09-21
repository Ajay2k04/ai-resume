import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapPin, Building, Clock, ExternalLink, CheckCircle, ArrowRight } from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import Modal from '../components/Modal'
import { useWorkflow } from '../context/WorkflowContext'

const JobSelection = () => {
  const navigate = useNavigate()
  const { workflowData, updateWorkflowData, nextStep } = useWorkflow()
  const [selectedJob, setSelectedJob] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [modalContent, setModalContent] = useState({ type: '', title: '', message: '' })

  const showNotification = (type, title, message) => {
    setModalContent({ type, title, message })
    setShowModal(true)
  }

  const handleJobSelect = (job) => {
    setSelectedJob(job)
  }

  const handleContinue = () => {
    if (!selectedJob) {
      showNotification('warning', 'No Job Selected', 'Please select a job to continue.')
      return
    }

    updateWorkflowData('selectedJob', selectedJob)
    showNotification('success', 'Job Selected', 'Great choice! Let\'s customize your application.')
    
    setTimeout(() => {
      nextStep()
      navigate('/step/3')
    }, 1500)
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Recently posted'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl mb-4">
            <CheckCircle className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Select Your Target Job</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Choose the job you want to apply for. We'll customize your resume and cover letter accordingly.
          </p>
        </div>

        {workflowData.jobsData && workflowData.jobsData.length > 0 ? (
          <div className="space-y-6">
            {/* Job Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {workflowData.jobsData.map((job, index) => (
                <Card 
                  key={index} 
                  className={`cursor-pointer transition-all duration-200 ${
                    selectedJob?.job_url === job.job_url 
                      ? 'ring-2 ring-blue-500 bg-blue-50' 
                      : 'hover:shadow-medium'
                  }`}
                  onClick={() => handleJobSelect(job)}
                >
                  <Card.Content>
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          {job.title}
                        </h3>
                        <div className="flex items-center text-gray-600 mb-2">
                          <Building className="w-4 h-4 mr-2" />
                          <span className="font-medium">{job.company}</span>
                        </div>
                        <div className="flex items-center text-gray-600 mb-3">
                          <MapPin className="w-4 h-4 mr-2" />
                          <span>{job.location}</span>
                        </div>
                      </div>
                      
                      {selectedJob?.job_url === job.job_url && (
                        <div className="flex items-center justify-center w-8 h-8 bg-blue-600 rounded-full">
                          <CheckCircle className="w-5 h-5 text-white" />
                        </div>
                      )}
                    </div>

                    {/* Job Description Preview */}
                    {job.description && (
                      <div className="mb-4">
                        <p className="text-gray-700 text-sm line-clamp-3">
                          {job.description.substring(0, 200)}...
                        </p>
                      </div>
                    )}

                    {/* Job Details */}
                    <div className="flex items-center justify-between text-sm text-gray-500">
                      <div className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        <span>{formatDate(job.posted_date)}</span>
                      </div>
                      
                      {job.job_url && (
                        <a
                          href={job.job_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center text-blue-600 hover:text-blue-700"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <ExternalLink className="w-4 h-4 mr-1" />
                          View Job
                        </a>
                      )}
                    </div>
                  </Card.Content>
                </Card>
              ))}
            </div>

            {/* Continue Button */}
            <div className="flex justify-center pt-6">
              <Button
                onClick={handleContinue}
                disabled={!selectedJob}
                size="lg"
                className="px-8"
              >
                Continue with Selected Job
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </div>
          </div>
        ) : (
          <Card className="text-center py-12">
            <Card.Content>
              <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Building className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Jobs Found</h3>
              <p className="text-gray-600 mb-6">
                It looks like no jobs were found in your search. Try adjusting your search criteria.
              </p>
              <Button
                onClick={() => navigate('/step/1')}
                variant="outline"
              >
                Back to Job Search
              </Button>
            </Card.Content>
          </Card>
        )}
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

export default JobSelection