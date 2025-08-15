import React, { createContext, useContext, useState, useEffect } from 'react'
import authService from '../services/authService'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Check for existing session
    checkExistingSession()
  }, [])

  const checkExistingSession = async () => {
    try {
      setLoading(true)
      
      // Try to initialize from stored token
      const authData = await authService.initializeFromStorage()
      
      if (authData) {
        setUser(authData.user)
        console.log('Session restored for user:', authData.user.username)
      } else {
        console.log('No valid session found')
      }
    } catch (error) {
      console.error('Failed to check existing session:', error)
      setError('Failed to restore session')
    } finally {
      setLoading(false)
    }
  }

  const login = async (username, password) => {
    try {
      setLoading(true)
      setError(null)
      
      // Use server-based authentication
      const authData = await authService.login(username, password)
      
      setUser(authData.user)
      console.log(`User ${username} logged in successfully:`, authData.user)
      return authData.user
    } catch (error) {
      setError(error.message)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const register = async (username, email, password) => {
    try {
      setLoading(true)
      setError(null)
      
      // Use server-based registration
      const authData = await authService.register(username, email, password)
      
      setUser(authData.user)
      console.log(`User ${username} registered successfully:`, authData.user)
      return authData.user
    } catch (error) {
      setError(error.message)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try {
      // Use server-based logout
      await authService.logout()
      setUser(null)
      console.log('User logged out successfully')
    } catch (error) {
      console.error('Failed to logout:', error)
      // Still clear the user state even if server logout fails
      setUser(null)
    }
  }

  const updateUser = async (updates) => {
    if (!user) return

    try {
      // Use server-based profile update
      const updatedUser = await authService.updateProfile(updates)
      setUser(updatedUser)
      return updatedUser
    } catch (error) {
      console.error('Failed to update user:', error)
      setError('Failed to update user profile')
      throw error
    }
  }

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    updateUser,
    isAuthenticated: !!user,
    setError,
    clearError: () => setError(null)
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}