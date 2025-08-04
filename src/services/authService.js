import axios from 'axios'

// API base URL - will be configured based on environment
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          })

          const { access_token } = response.data.data
          localStorage.setItem('access_token', access_token)

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user_data')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export const authService = {
  // Register new user
  register: async (userData) => {
    const response = await api.post('/auth/register', userData)
    return response.data
  },

  // Login user
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials)
    return response.data
  },

  // Refresh access token
  refreshToken: async (refreshToken) => {
    const response = await api.post('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  // Logout user
  logout: async (token) => {
    const response = await api.post('/auth/logout', {}, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Get current user profile
  getCurrentUser: async (token) => {
    const response = await api.get('/users/me', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Update user profile
  updateProfile: async (userData, token) => {
    const response = await api.put('/users/me', userData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Change password
  changePassword: async (passwordData, token) => {
    const response = await api.post('/auth/change-password', passwordData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Get user sessions
  getSessions: async (token) => {
    const response = await api.get('/auth/sessions', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Revoke session
  revokeSession: async (sessionId, token) => {
    const response = await api.delete(`/auth/sessions/${sessionId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Request password reset
  requestPasswordReset: async (email) => {
    const response = await api.post('/auth/password-reset', { email })
    return response.data
  },

  // Reset password with token
  resetPassword: async (token, newPassword) => {
    const response = await api.post('/auth/password-reset/confirm', {
      token,
      new_password: newPassword,
    })
    return response.data
  },

  // Verify email
  verifyEmail: async (token) => {
    const response = await api.post('/auth/verify-email', { token })
    return response.data
  },

  // Request email verification
  requestEmailVerification: async (email) => {
    const response = await api.post('/auth/verify-email/request', { email })
    return response.data
  },
}

export default authService

