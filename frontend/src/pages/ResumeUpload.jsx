import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, CheckCircle, AlertCircle, X } from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import Modal from '../components/Modal'
import { useWorkflow } from '../context/WorkflowContext'

const ResumeUpload = () => {
  const navigate = useNavigate()
  const { updateWorkflowData, nextStep } = useWorkflow()
  const fileInputRef = useRef(null)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [isParsing, setIsParsing] = useState(false)
  const [parsedData, setParsedData] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [modalContent, setModalContent] = useState({ type: '', title: '', message: '' })

  const showNotification = (type, title, message) => {
    setModalContent({ type, title, message })
    setShowModal(true)
  }

  const handleFileSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
      if (file.type === 'application/pdf' || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
        setUploadedFile(file)
        setParsedData(null)
      } else {
        showNotification('error', 'Invalid File Type', 'Please upload a PDF or DOCX file.')
      }
    }
  }

  const handleDrop = (event) => {
    event.preventDefault()
    const file = event.dataTransfer.files[0]
    if (file) {
      if (file.type === 'application/pdf' || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
        setUploadedFile(file)
        setParsedData(null)
      } else {
        showNotification('error', 'Invalid File Type', 'Please upload a PDF or DOCX file.')
      }
    }
  }

  const handleDragOver = (event) => {
    event.preventDefault()
  }

  const removeFile = () => {
    setUploadedFile(null)
    setParsedData(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleUpload = async () => {
    if (!uploadedFile) return

    setIsParsing(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadedFile)

      const response = await fetch('/api/resumes/upload', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error('Failed to parse resume')
      }

      const data = await response.json()
      setParsedData(data)
      updateWorkflowData('resumeData', data)
      
      showNotification('success', 'Resume Parsed Successfully', 'Your resume has been analyzed and is ready for the next step.')
      
      setTimeout(() => {
        nextStep()
        navigate('/step/1')
      }, 1500)
    } catch (error) {
      console.error('Error parsing resume:', error)
      showNotification('error', 'Parsing Failed', 'Unable to parse your resume. Please try again with a different file.')
    } finally {
      setIsParsing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-green-600 to-emerald-600 rounded-2xl mb-4">
            <FileText className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Your Resume</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Upload your resume and let our AI extract key information to personalize your applications
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <Card className="animate-slide-up">
            <Card.Header>
              <h2 className="text-xl font-semibold text-gray-900">Upload Resume</h2>
              <p className="text-gray-600 mt-1">Supported formats: PDF, DOCX</p>
            </Card.Header>
            
            <Card.Content>
              {!uploadedFile ? (
                <div
                  className="border-2 border-dashed border-gray-300 rounded-2xl p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                >
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Drop your resume here</h3>
                  <p className="text-gray-600 mb-4">or click to browse files</p>
                  <Button variant="outline">Choose File</Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-xl">
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="w-6 h-6 text-green-600" />
                      <div>
                        <p className="font-medium text-green-900">{uploadedFile.name}</p>
                        <p className="text-sm text-green-700">
                          {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={removeFile}
                      className="p-2 hover:bg-green-100 rounded-lg transition-colors"
                    >
                      <X className="w-5 h-5 text-green-600" />
                    </button>
                  </div>
                  
                  <Button
                    onClick={handleUpload}
                    loading={isParsing}
                    className="w-full"
                    size="lg"
                  >
                    {isParsing ? 'Analyzing Resume...' : 'Parse Resume'}
                  </Button>
                </div>
              )}
              
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx"
                onChange={handleFileSelect}
                className="hidden"
              />
            </Card.Content>
          </Card>

          {/* Parsed Data Preview */}
          {parsedData && (
            <Card className="animate-slide-up">
              <Card.Header>
                <h2 className="text-xl font-semibold text-gray-900">Extracted Information</h2>
                <p className="text-gray-600 mt-1">Review the parsed data</p>
              </Card.Header>
              
              <Card.Content className="space-y-4">
                <div className="grid grid-cols-1 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    <p className="text-gray-900 bg-gray-50 p-3 rounded-lg">{parsedData.name || 'Not found'}</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <p className="text-gray-900 bg-gray-50 p-3 rounded-lg">{parsedData.email || 'Not found'}</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                    <p className="text-gray-900 bg-gray-50 p-3 rounded-lg">{parsedData.phone || 'Not found'}</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Skills</label>
                    <div className="flex flex-wrap gap-2">
                      {parsedData.skills?.slice(0, 8).map((skill, index) => (
                        <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                          {skill}
                        </span>
                      ))}
                      {parsedData.skills?.length > 8 && (
                        <span className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full">
                          +{parsedData.skills.length - 8} more
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Experience</label>
                    <p className="text-gray-900 bg-gray-50 p-3 rounded-lg">
                      {parsedData.experience || 'Not found'}
                    </p>
                  </div>
                </div>
              </Card.Content>
            </Card>
          )}
        </div>

        {/* Tips */}
        <Card className="mt-8 animate-slide-up">
          <Card.Header>
            <h3 className="text-lg font-semibold text-gray-900">Tips for Best Results</h3>
          </Card.Header>
          <Card.Content>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Clear Formatting</h4>
                <p className="text-sm text-gray-600">Use clear headings and bullet points for better parsing</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Complete Information</h4>
                <p className="text-sm text-gray-600">Include contact details, skills, and work experience</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <AlertCircle className="w-6 h-6 text-purple-600" />
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Recent Version</h4>
                <p className="text-sm text-gray-600">Upload your most up-to-date resume for accurate results</p>
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

export default ResumeUpload