/**
 * Authentication Service
 * Handles server-based authentication
 */

const API_BASE_URL = 'http://localhost:8000/api';

class AuthService {
  constructor() {
    this.token = null;
    this.user = null;
  }

  /**
   * Make API request
   */
  async apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Auth API request failed:', error);
      throw error;
    }
  }

  /**
   * Login user
   */
  async login(username, password) {
    try {
      const response = await this.apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username,
          password
        })
      });

      this.token = response.data.access_token;
      this.user = response.data.user;

      // Store in localStorage
      localStorage.setItem('token', this.token);
      localStorage.setItem('user', JSON.stringify(this.user));

      return { token: this.token, user: this.user };
    } catch (error) {
      // Fallback to demo mode if server is not available
      if (error.message.includes('fetch') || error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
        console.warn('Backend server not available, using demo mode');
        return this.demoLogin(username, password);
      }
      throw new Error(`Login failed: ${error.message}`);
    }
  }

  /**
   * Demo login for offline mode
   */
  demoLogin(username, password) {
    // Create demo user
    const demoUser = {
      id: `demo-${username}-${Date.now()}`,
      username,
      email: `${username}@demo.local`,
      display_name: username,
      is_active: true,
      created_at: new Date().toISOString()
    };

    const demoToken = `demo-token-${demoUser.id}`;

    this.token = demoToken;
    this.user = demoUser;

    // Store in localStorage
    localStorage.setItem('token', this.token);
    localStorage.setItem('user', JSON.stringify(this.user));
    localStorage.setItem('demo_mode', 'true');

    return { token: this.token, user: this.user };
  }

  /**
   * Register new user
   */
  async register(username, email, password) {
    try {
      const response = await this.apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          username,
          email,
          password,
          display_name: username
        })
      });

      this.token = response.data.access_token;
      this.user = response.data.user;

      // Store in localStorage
      localStorage.setItem('token', this.token);
      localStorage.setItem('user', JSON.stringify(this.user));

      return { token: this.token, user: this.user };
    } catch (error) {
      // Fallback to demo mode if server is not available
      if (error.message.includes('fetch') || error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
        console.warn('Backend server not available, using demo mode for registration');
        return this.demoRegister(username, email, password);
      }
      throw new Error(`Registration failed: ${error.message}`);
    }
  }

  /**
   * Demo registration for offline mode
   */
  demoRegister(username, email, password) {
    // Check if user already exists in demo mode
    const existingUsers = JSON.parse(localStorage.getItem('demo_users') || '[]');
    if (existingUsers.find(u => u.username === username)) {
      throw new Error('Username already exists in demo mode');
    }

    // Create demo user
    const demoUser = {
      id: `demo-${username}-${Date.now()}`,
      username,
      email,
      display_name: username,
      is_active: true,
      created_at: new Date().toISOString()
    };

    const demoToken = `demo-token-${demoUser.id}`;

    // Store user in demo users list
    existingUsers.push(demoUser);
    localStorage.setItem('demo_users', JSON.stringify(existingUsers));

    this.token = demoToken;
    this.user = demoUser;

    // Store in localStorage
    localStorage.setItem('token', this.token);
    localStorage.setItem('user', JSON.stringify(this.user));
    localStorage.setItem('demo_mode', 'true');

    return { token: this.token, user: this.user };
  }

  /**
   * Logout user
   */
  async logout() {
    try {
      if (this.token && !localStorage.getItem('demo_mode')) {
        await this.apiRequest('/auth/logout', {
          method: 'POST'
        });
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with local logout even if API fails
    }

    this.token = null;
    this.user = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('demo_mode');
  }

  /**
   * Get current user profile
   */
  async getCurrentUser() {
    if (!this.token) {
      throw new Error('No authentication token');
    }

    try {
      const response = await this.apiRequest('/auth/me');
      this.user = response.data.user;
      localStorage.setItem('user', JSON.stringify(this.user));
      return this.user;
    } catch (error) {
      throw new Error(`Failed to get user profile: ${error.message}`);
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(updates) {
    if (!this.token) {
      throw new Error('No authentication token');
    }

    try {
      const response = await this.apiRequest('/auth/me', {
        method: 'PUT',
        body: JSON.stringify(updates)
      });

      this.user = response.data.user;
      localStorage.setItem('user', JSON.stringify(this.user));
      return this.user;
    } catch (error) {
      throw new Error(`Failed to update profile: ${error.message}`);
    }
  }

  /**
   * Verify token validity
   */
  async verifyToken() {
    if (!this.token) {
      return false;
    }

    try {
      await this.getCurrentUser();
      return true;
    } catch (error) {
      console.error('Token verification failed:', error);
      this.logout(); // Clear invalid token
      return false;
    }
  }

  /**
   * Initialize from stored token
   */
  async initializeFromStorage() {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedUser) {
      try {
        this.token = storedToken;
        this.user = JSON.parse(storedUser);

        // Verify token is still valid
        const isValid = await this.verifyToken();
        if (isValid) {
          return { token: this.token, user: this.user };
        }
      } catch (error) {
        console.error('Failed to initialize from storage:', error);
        this.logout(); // Clear invalid data
      }
    }

    return null;
  }

  /**
   * Get stored token
   */
  getToken() {
    return this.token || localStorage.getItem('token');
  }

  /**
   * Get stored user
   */
  getUser() {
    if (this.user) {
      return this.user;
    }

    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        return JSON.parse(storedUser);
      } catch (error) {
        console.error('Failed to parse stored user:', error);
      }
    }

    return null;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!(this.token || localStorage.getItem('token'));
  }
}

// Create singleton instance
const authService = new AuthService();

export default authService;
