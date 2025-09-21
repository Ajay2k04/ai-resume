import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Header from './components/Header'
import ResumeUpload from './pages/ResumeUpload'
import JobSearch from './pages/JobSearch'
import JobSelection from './pages/JobSelection'
import AIGeneration from './pages/AIGeneration'
import Export from './pages/Export'
import { WorkflowProvider } from './context/WorkflowContext'

function App() {
  return (
    <WorkflowProvider>
      <Router>
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
          <Header />
          
          <main>
            <Routes>
              <Route path="/" element={<Navigate to="/step/0" replace />} />
              <Route path="/step/0" element={<ResumeUpload />} />
              <Route path="/step/1" element={<JobSearch />} />
              <Route path="/step/2" element={<JobSelection />} />
              <Route path="/step/3" element={<AIGeneration />} />
              <Route path="/step/4" element={<Export />} />
            </Routes>
          </main>
        </div>
      </Router>
    </WorkflowProvider>
  )
}

export default App