import React, { useState } from 'react'
import { X, Edit3, Save, XCircle, Eye, FileText, Mail } from 'lucide-react'
import Button from './Button'

const DocumentPreview = ({ 
  isOpen, 
  onClose, 
  title, 
  content, 
  type = 'resume', // 'resume' or 'cover_letter'
  onSave 
}) => {
  const [isEditing, setIsEditing] = useState(false)
  const [editedContent, setEditedContent] = useState(content)

  const handleSave = () => {
    onSave(editedContent)
    setIsEditing(false)
  }

  const handleCancel = () => {
    setEditedContent(content)
    setIsEditing(false)
  }

  const formatContent = (text) => {
    if (!text) return ''
    
    return text.split('\n').map((line, index) => {
      const trimmedLine = line.trim()
      
      // Handle empty lines
      if (trimmedLine === '') {
        return <div key={index} className="h-3" />
      }
      
      // Handle name (first line, all caps, no special chars)
      if (index === 0 && trimmedLine.match(/^[A-Z\s]+$/) && trimmedLine.length > 3) {
        return (
          <div key={index} className="text-left font-bold text-lg text-gray-900 mb-2">
            {trimmedLine}
          </div>
        )
      }
      
      // Handle contact info (contains email, phone, or LinkedIn)
      if (trimmedLine.includes('@') || trimmedLine.includes('linkedin.com') || 
          (trimmedLine.includes('|') && index < 5)) {
        return (
          <div key={index} className="text-left text-gray-600 mb-3 text-sm">
            {trimmedLine}
          </div>
        )
      }
      
      // Handle section headers (all caps, common resume sections)
      if (trimmedLine.match(/^[A-Z\s&]+$/) && trimmedLine.length > 3 && 
          ['PROFESSIONAL SUMMARY', 'WORK EXPERIENCE', 'EDUCATION', 'SKILLS', 'PROJECTS', 
           'CERTIFICATIONS', 'EXTRACURRICULAR ACTIVITIES', 'AWARDS & ACHIEVEMENTS', 
           'VOLUNTEER', 'LANGUAGES', 'INTERESTS'].some(section => trimmedLine.includes(section))) {
        return (
          <div key={index} className="font-bold text-gray-900 text-sm mb-2 mt-4 border-b border-gray-300 pb-1">
            {trimmedLine}
          </div>
        )
      }
      
      // Handle job titles/company (contains |)
      if (trimmedLine.includes('|') && trimmedLine.split('|').length >= 2) {
        return (
          <div key={index} className="font-semibold text-gray-800 mb-1 text-sm">
            {trimmedLine}
          </div>
        )
      }
      
      // Handle bullet points
      if (trimmedLine.startsWith('•')) {
        return (
          <div key={index} className="ml-6 mb-1 text-gray-700 flex items-start">
            <span className="text-gray-500 mr-2 mt-1">•</span>
            <span className="text-xs">{trimmedLine.substring(1).trim()}</span>
          </div>
        )
      }
      
      // Handle skills (contains :)
      if (trimmedLine.includes(':') && !trimmedLine.includes('@')) {
        return (
          <div key={index} className="mb-1 text-gray-700">
            <span className="font-medium text-xs">{trimmedLine.split(':')[0]}:</span>
            <span className="ml-1 text-xs">{trimmedLine.split(':').slice(1).join(':').trim()}</span>
          </div>
        )
      }
      
      // Handle regular paragraphs
      return (
        <div key={index} className="text-gray-700 mb-2 leading-relaxed text-xs">
          {trimmedLine}
        </div>
      )
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                    {type === 'resume' ? (
                      <FileText className="w-6 h-6 text-white" />
                    ) : (
                      <Mail className="w-6 h-6 text-white" />
                    )}
                  </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              <p className="text-sm text-gray-500">
                {type === 'resume' ? 'Resume Preview' : 'Cover Letter Preview'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {!isEditing ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-2"
              >
                <Edit3 className="w-4 h-4" />
                Edit
              </Button>
            ) : (
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCancel}
                  className="flex items-center gap-2"
                >
                  <XCircle className="w-4 h-4" />
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleSave}
                  className="flex items-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  Save
                </Button>
              </div>
            )}
            
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>
        
        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {isEditing ? (
            <textarea
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              className="w-full h-96 p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm"
              placeholder="Edit your document content..."
            />
          ) : (
            <div className="max-w-none">
              <div className="bg-white p-8 rounded-xl border shadow-sm" style={{ fontFamily: 'Arial, sans-serif' }}>
                <div className="max-w-4xl mx-auto">
                  {formatContent(content)}
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-6 border-t border-gray-100 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Eye className="w-4 h-4" />
              <span>
                {isEditing ? 'Editing mode - make your changes and save' : 'Preview mode - click Edit to modify'}
              </span>
            </div>
            
            <div className="text-sm text-gray-500">
              {content?.length || 0} characters
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DocumentPreview
