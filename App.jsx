import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './src/contexts/AuthContext'
import LoginPage from './src/pages/LoginPage'
import RegisterPage from './src/pages/RegisterPage'
import ChatPage from './src/pages/ChatPage'
import './App.css'

function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-300">Loading Real-Time Chat...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Routes>
        <Route 
          path="/login" 
          element={user ? <Navigate to="/chat" replace /> : <LoginPage />} 
        />
        <Route 
          path="/register" 
          element={user ? <Navigate to="/chat" replace /> : <RegisterPage />} 
        />
        <Route 
          path="/chat" 
          element={user ? <ChatPage /> : <Navigate to="/login" replace />} 
        />
        <Route 
          path="/" 
          element={<Navigate to={user ? "/chat" : "/login"} replace />} 
        />
      </Routes>
    </div>
  )
}

export default App

