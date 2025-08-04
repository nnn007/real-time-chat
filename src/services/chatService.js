import axios from 'axios'

// API base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
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

export const chatService = {
  // Get user's chatrooms
  getChatrooms: async (token) => {
    const response = await api.get('/chatrooms', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Create new chatroom
  createChatroom: async (chatroomData, token) => {
    const response = await api.post('/chatrooms', chatroomData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Get chatroom details
  getChatroom: async (chatroomId, token) => {
    const response = await api.get(`/chatrooms/${chatroomId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Update chatroom
  updateChatroom: async (chatroomId, chatroomData, token) => {
    const response = await api.put(`/chatrooms/${chatroomId}`, chatroomData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Delete chatroom
  deleteChatroom: async (chatroomId, token) => {
    const response = await api.delete(`/chatrooms/${chatroomId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Get chatroom messages
  getMessages: async (chatroomId, params = {}, token) => {
    const response = await api.get(`/messages/${chatroomId}/messages`, {
      params,
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Search messages
  searchMessages: async (chatroomId, searchData, token) => {
    const response = await api.post(`/messages/${chatroomId}/search`, searchData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Get chat summary
  getChatSummary: async (chatroomId, params = {}, token) => {
    const response = await api.get(`/messages/${chatroomId}/summary`, {
      params,
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Generate chat summary
  generateChatSummary: async (chatroomId, summaryData, token) => {
    const response = await api.post(`/messages/${chatroomId}/summary`, summaryData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Join chatroom with invitation
  joinChatroomWithInvite: async (inviteCode, token) => {
    const response = await api.post('/chatrooms/join', { invite_code: inviteCode }, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Create invitation
  createInvitation: async (chatroomId, invitationData, token) => {
    const response = await api.post(`/chatrooms/${chatroomId}/invitations`, invitationData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Get chatroom invitations
  getInvitations: async (chatroomId, token) => {
    const response = await api.get(`/chatrooms/${chatroomId}/invitations`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Revoke invitation
  revokeInvitation: async (chatroomId, invitationId, token) => {
    const response = await api.delete(`/chatrooms/${chatroomId}/invitations/${invitationId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Get chatroom members
  getMembers: async (chatroomId, token) => {
    const response = await api.get(`/chatrooms/${chatroomId}/members`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Add member to chatroom
  addMember: async (chatroomId, memberData, token) => {
    const response = await api.post(`/chatrooms/${chatroomId}/members`, memberData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Update member role
  updateMemberRole: async (chatroomId, memberId, roleData, token) => {
    const response = await api.put(`/chatrooms/${chatroomId}/members/${memberId}`, roleData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Remove member from chatroom
  removeMember: async (chatroomId, memberId, token) => {
    const response = await api.delete(`/chatrooms/${chatroomId}/members/${memberId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Leave chatroom
  leaveChatroom: async (chatroomId, token) => {
    const response = await api.post(`/chatrooms/${chatroomId}/leave`, {}, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Upload file
  uploadFile: async (file, token) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/upload/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Get user profile
  getUserProfile: async (userId, token) => {
    const response = await api.get(`/users/${userId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Search users
  searchUsers: async (query, token) => {
    const response = await api.get('/users/search', {
      params: { q: query },
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  // Encryption-related methods
  storePublicKey: async (chatroomId, keyData, token) => {
    const response = await api.post(`/encryption/${chatroomId}/keys`, keyData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  getPublicKeys: async (chatroomId, token) => {
    const response = await api.get(`/encryption/${chatroomId}/keys`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data.data.public_keys
  },

  getUserPublicKey: async (chatroomId, userId, token) => {
    const response = await api.get(`/encryption/${chatroomId}/keys/${userId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data.data
  },

  rotateEncryptionKeys: async (chatroomId, token) => {
    const response = await api.post(`/encryption/${chatroomId}/rotate-keys`, {}, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  getEncryptionStats: async (chatroomId, token) => {
    const response = await api.get(`/encryption/${chatroomId}/stats`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data.data
  },

  storeEncryptedMessage: async (messageId, encryptionData, token) => {
    const response = await api.post(`/encryption/messages/${messageId}/encrypt`, encryptionData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  getEncryptedMessage: async (messageId, token) => {
    const response = await api.get(`/encryption/messages/${messageId}/decrypt`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data.data
  },
}

export default chatService

