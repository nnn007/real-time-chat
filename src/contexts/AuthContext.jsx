import { createContext, useContext, useReducer, useEffect } from 'react'
import { authService } from '../services/authService'

// Initial state
const initialState = {
  user: null,
  token: null,
  refreshToken: null,
  loading: true,
  error: null,
}

// Action types
const AUTH_ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGOUT: 'LOGOUT',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  UPDATE_USER: 'UPDATE_USER',
}

// Reducer function
function authReducer(state, action) {
  switch (action.type) {
    case AUTH_ACTIONS.SET_LOADING:
      return {
        ...state,
        loading: action.payload,
      }
    
    case AUTH_ACTIONS.LOGIN_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.access_token,
        refreshToken: action.payload.refresh_token,
        loading: false,
        error: null,
      }
    
    case AUTH_ACTIONS.LOGOUT:
      return {
        ...initialState,
        loading: false,
      }
    
    case AUTH_ACTIONS.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        loading: false,
      }
    
    case AUTH_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null,
      }
    
    case AUTH_ACTIONS.UPDATE_USER:
      return {
        ...state,
        user: { ...state.user, ...action.payload },
      }
    
    default:
      return state
  }
}

// Create context
const AuthContext = createContext()

// AuthProvider component
export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState)

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = localStorage.getItem('access_token')
        const refreshToken = localStorage.getItem('refresh_token')
        const userData = localStorage.getItem('user_data')

        if (token && refreshToken && userData) {
          const user = JSON.parse(userData)
          
          // Verify token is still valid
          try {
            await authService.getCurrentUser(token)
            dispatch({
              type: AUTH_ACTIONS.LOGIN_SUCCESS,
              payload: {
                user,
                access_token: token,
                refresh_token: refreshToken,
              },
            })
          } catch (error) {
            // Token might be expired, try to refresh
            try {
              const response = await authService.refreshToken(refreshToken)
              localStorage.setItem('access_token', response.data.access_token)
              
              dispatch({
                type: AUTH_ACTIONS.LOGIN_SUCCESS,
                payload: {
                  user,
                  access_token: response.data.access_token,
                  refresh_token: refreshToken,
                },
              })
            } catch (refreshError) {
              // Refresh failed, clear stored data
              localStorage.removeItem('access_token')
              localStorage.removeItem('refresh_token')
              localStorage.removeItem('user_data')
              dispatch({ type: AUTH_ACTIONS.LOGOUT })
            }
          }
        } else {
          dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false })
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
        dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false })
      }
    }

    initializeAuth()
  }, [])

  // Login function
  const login = async (credentials) => {
    try {
      dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: true })
      dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR })

      const response = await authService.login(credentials)
      const { user, access_token, refresh_token } = response.data

      // Store in localStorage
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      localStorage.setItem('user_data', JSON.stringify(user))

      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: { user, access_token, refresh_token },
      })

      return response
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message || 'Login failed'
      dispatch({ type: AUTH_ACTIONS.SET_ERROR, payload: errorMessage })
      throw error
    }
  }

  // Register function
  const register = async (userData) => {
    try {
      dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: true })
      dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR })

      const response = await authService.register(userData)
      const { user, access_token, refresh_token } = response.data

      // Store in localStorage
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      localStorage.setItem('user_data', JSON.stringify(user))

      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: { user, access_token, refresh_token },
      })

      return response
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message || 'Registration failed'
      dispatch({ type: AUTH_ACTIONS.SET_ERROR, payload: errorMessage })
      throw error
    }
  }

  // Logout function
  const logout = async () => {
    try {
      if (state.token) {
        await authService.logout(state.token)
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear localStorage
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_data')

      dispatch({ type: AUTH_ACTIONS.LOGOUT })
    }
  }

  // Update user profile
  const updateUser = async (userData) => {
    try {
      const response = await authService.updateProfile(userData, state.token)
      const updatedUser = response.data

      // Update localStorage
      localStorage.setItem('user_data', JSON.stringify(updatedUser))

      dispatch({
        type: AUTH_ACTIONS.UPDATE_USER,
        payload: updatedUser,
      })

      return response
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message || 'Profile update failed'
      dispatch({ type: AUTH_ACTIONS.SET_ERROR, payload: errorMessage })
      throw error
    }
  }

  // Clear error
  const clearError = () => {
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR })
  }

  // Context value
  const value = {
    ...state,
    login,
    register,
    logout,
    updateUser,
    clearError,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// Custom hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

