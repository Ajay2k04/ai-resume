import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, MapPin, Calendar, Users, Filter, ArrowRight } from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import Input from '../components/Input'
import Modal from '../components/Modal'
import { useWorkflow } from '../context/WorkflowContext'

const JobSearch = () => {
  const navigate = useNavigate()
  const { updateWorkflowData, nextStep } = useWorkflow()
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState([])
  const [showModal, setShowModal] = useState(false)
  const [modalContent, setModalContent] = useState({ type: '', title: '', message: '' })
  
  const [searchParams, setSearchParams] = useState({
    job_titles: ['Software Engineer'],
    location: 'United States',
    remote_only: false,
    posted_within_days: 7,
    num_results: 10
  })

  const showNotification = (type, title, message) => {
    setModalContent({ type, title, message })
    setShowModal(true)
  }

  const handleSearch = async () => {
    setIsSearching(true)
    try {
      const response = await fetch('/api/jobs/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchParams)
      })

      if (!response.ok) {
        throw new Error('Failed to search jobs')
      }

      const data = await response.json()
      setSearchResults(data.jobs)
      updateWorkflowData('jobsData', data.jobs)
      
      if (data.jobs.length > 0) {
        showNotification('success', 'Search Complete', `Found ${data.jobs.length} job opportunities!`)
        setTimeout(() => {
          nextStep()
          navigate('/step/2')
        }, 1500)
      } else {
        showNotification('warning', 'No Jobs Found', 'Try adjusting your search criteria or location.')
      }
    } catch (error) {
      console.error('Error searching jobs:', error)
      showNotification('error', 'Search Failed', 'Unable to search for jobs. Please try again.')
    } finally {
      setIsSearching(false)
    }
  }

  const addJobTitle = () => {
    setSearchParams(prev => ({
      ...prev,
      job_titles: [...prev.job_titles, '']
    }))
  }

  const updateJobTitle = (index, value) => {
    setSearchParams(prev => ({
      ...prev,
      job_titles: prev.job_titles.map((title, i) => i === index ? value : title)
    }))
  }

  const removeJobTitle = (index) => {
    setSearchParams(prev => ({
      ...prev,
      job_titles: prev.job_titles.filter((_, i) => i !== index)
    }))
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl mb-4">
            <Search className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Find Your Dream Job</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Discover opportunities from top companies using our AI-powered job search engine
          </p>
        </div>

        <Card className="animate-slide-up">
          <Card.Header>
            <h2 className="text-xl font-semibold text-gray-900">Search Criteria</h2>
            <p className="text-gray-600 mt-1">Tell us what you're looking for</p>
          </Card.Header>
          
          <Card.Content className="space-y-6">
            {/* Job Titles */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Job Titles
              </label>
              <div className="space-y-3">
                {searchParams.job_titles.map((title, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <Input
                      value={title}
                      onChange={(e) => updateJobTitle(index, e.target.value)}
                      placeholder="e.g., Software Engineer, Data Scientist"
                      className="flex-1"
                    />
                    {searchParams.job_titles.length > 1 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeJobTitle(index)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        Remove
                      </Button>
                    )}
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={addJobTitle}
                  className="w-full"
                >
                  + Add Another Job Title
                </Button>
              </div>
            </div>

            {/* Location */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Input
                  label="Location"
                  value={searchParams.location}
                  onChange={(e) => setSearchParams(prev => ({ ...prev, location: e.target.value }))}
                  placeholder="e.g., San Francisco, CA"
                  icon={<MapPin className="w-5 h-5 text-gray-400" />}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Posted Within
                </label>
                <select
                  value={searchParams.posted_within_days}
                  onChange={(e) => setSearchParams(prev => ({ ...prev, posted_within_days: parseInt(e.target.value) }))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                >
                  <option value={1}>Last 24 hours</option>
                  <option value={3}>Last 3 days</option>
                  <option value={7}>Last week</option>
                  <option value={14}>Last 2 weeks</option>
                  <option value={30}>Last month</option>
                </select>
              </div>
            </div>

            {/* Options */}
            <div className="flex items-center space-x-6">
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={searchParams.remote_only}
                  onChange={(e) => setSearchParams(prev => ({ ...prev, remote_only: e.target.checked }))}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">Remote only</span>
              </label>
              
              <div className="flex items-center space-x-2">
                <Users className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-600">Max results:</span>
                <select
                  value={searchParams.num_results}
                  onChange={(e) => setSearchParams(prev => ({ ...prev, num_results: parseInt(e.target.value) }))}
                  className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={30}>30</option>
                </select>
              </div>
            </div>
          </Card.Content>
          
          <Card.Footer>
            <Button
              onClick={handleSearch}
              loading={isSearching}
              disabled={!searchParams.job_titles.some(title => title.trim())}
              className="w-full md:w-auto"
              size="lg"
            >
              {isSearching ? 'Searching Jobs...' : 'Search Jobs'}
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Card.Footer>
        </Card>

        {/* Search Results Preview */}
        {searchResults.length > 0 && (
          <Card className="mt-6 animate-slide-up">
            <Card.Header>
              <h3 className="text-lg font-semibold text-gray-900">Search Results</h3>
              <p className="text-gray-600">Found {searchResults.length} opportunities</p>
            </Card.Header>
            <Card.Content>
              <div className="space-y-3">
                {searchResults.slice(0, 3).map((job, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                    <div>
                      <h4 className="font-medium text-gray-900">{job.title}</h4>
                      <p className="text-sm text-gray-600">{job.company}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">{job.location}</p>
                    </div>
                  </div>
                ))}
                {searchResults.length > 3 && (
                  <p className="text-sm text-gray-500 text-center">
                    And {searchResults.length - 3} more opportunities...
                  </p>
                )}
              </div>
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

export default JobSearch