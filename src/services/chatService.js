/**
 * Chat Service
 * Handles server-based chat functionality
 */

const API_BASE_URL = 'http://localhost:8000/api';

class ChatService {
  constructor() {
    this.token = null;
  }

  /**
   * Set authentication token
   */
  setToken(token) {
    this.token = token;
  }

  /**
   * Make authenticated API request
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
        const error = await response.text();
        throw new Error(`API request failed: ${response.status} ${error}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return await response.text();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  /**
   * Create a new chatroom
   */
  async createChatroom(name, description = '', isPrivate = true, maxMembers = 50) {
    const response = await this.apiRequest('/chatrooms', {
      method: 'POST',
      body: JSON.stringify({
        name,
        description,
        is_private: isPrivate,
        max_members: maxMembers,
        encryption_enabled: true
      })
    });
    return response.data.chatroom;
  }

  /**
   * Join a chatroom by secret code
   */
  async joinChatroomByCode(secretCode) {
    const response = await this.apiRequest(`/chatrooms/join/${secretCode}`, {
      method: 'POST'
    });
    return response.data.chatroom;
  }

  /**
   * Get user's chatrooms
   */
  async getChatrooms() {
    const response = await this.apiRequest('/chatrooms');
    return response.data.chatrooms || [];
  }

  /**
   * Get chatroom details
   */
  async getChatroom(chatroomId) {
    const response = await this.apiRequest(`/chatrooms/${chatroomId}`);
    return response.data.chatroom;
  }

  /**
   * Get chatroom members
   */
  async getChatroomMembers(chatroomId) {
    const response = await this.apiRequest(`/chatrooms/${chatroomId}/members`);
    return response.data.members || [];
  }

  /**
   * Get messages for a chatroom
   */
  async getMessages(chatroomId, limit = 50, offset = 0) {
    const response = await this.apiRequest(`/chatrooms/${chatroomId}/messages?limit=${limit}&offset=${offset}`);
    return response.data.messages || [];
  }

  /**
   * Delete a chatroom
   */
  async deleteChatroom(chatroomId) {
    return this.apiRequest(`/chatrooms/${chatroomId}`, {
      method: 'DELETE'
    });
  }

  /**
   * Leave a chatroom
   */
  async leaveChatroom(chatroomId) {
    return this.apiRequest(`/chatrooms/${chatroomId}/leave`, {
      method: 'POST'
    });
  }

  /**
   * Search messages
   */
  async searchMessages(chatroomId, query, limit = 20) {
    return this.apiRequest(`/chatrooms/${chatroomId}/messages/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  }

  /**
   * Get online users in a chatroom
   */
  async getOnlineUsers(chatroomId) {
    const response = await this.apiRequest(`/chatrooms/${chatroomId}/online`);
    return response.data.users || [];
  }
}

// Create singleton instance
const chatService = new ChatService();

export default chatService;
