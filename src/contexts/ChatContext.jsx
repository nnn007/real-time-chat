import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import websocketService from '../services/websocketService';
import chatService from '../services/chatService';

const ChatContext = createContext();

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

export const ChatProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [messages, setMessages] = useState([]);
  const [chatrooms, setChatrooms] = useState([]);
  const [currentChatroom, setCurrentChatroom] = useState(null);
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [typingUsers, setTypingUsers] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  // Initialize WebSocket connection when user is authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      initializeConnection();
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [isAuthenticated, user]);

  // Set up WebSocket event listeners
  useEffect(() => {
    const handleConnected = () => {
      console.log('WebSocket connected');
      setConnectionStatus('connected');
      setError(null);
      loadChatrooms(); // Load chatrooms when connected
    };

    const handleDisconnected = () => {
      console.log('WebSocket disconnected');
      setConnectionStatus('disconnected');
    };

    const handleError = ({ error }) => {
      console.error('WebSocket error:', error);
      setError('Connection error. Please try again.');
      setConnectionStatus('error');
    };

    const handleMessageReceived = ({ message }) => {
      console.log('Message received:', message);
      if (message.chatroom_id === currentChatroom?.id) {
        setMessages(prev => {
          // Avoid duplicates
          const exists = prev.find(m => m.id === message.id);
          if (exists) return prev;
          return [...prev, message];
        });
      }
    };

    const handleUserJoined = ({ user: joinedUser, chatroom_id }) => {
      console.log('User joined:', joinedUser, 'in chatroom:', chatroom_id);
      if (chatroom_id === currentChatroom?.id) {
        setOnlineUsers(prev => {
          const exists = prev.find(u => u.id === joinedUser.id);
          if (exists) return prev;
          return [...prev, joinedUser];
        });
      }
    };

    const handleUserLeft = ({ user_id, chatroom_id }) => {
      console.log('User left:', user_id, 'from chatroom:', chatroom_id);
      if (chatroom_id === currentChatroom?.id) {
        setOnlineUsers(prev => prev.filter(u => u.id !== user_id));
      }
    };

    const handleUserOnline = ({ user_id, username }) => {
      console.log('User online:', username);
      // Update online status for current chatroom
      if (currentChatroom) {
        setOnlineUsers(prev => {
          const exists = prev.find(u => u.id === user_id);
          if (!exists) {
            return [...prev, { id: user_id, username }];
          }
          return prev;
        });
      }
    };

    const handleUserOffline = ({ user_id }) => {
      console.log('User offline:', user_id);
      setOnlineUsers(prev => prev.filter(u => u.id !== user_id));
    };

    const handleTypingIndicator = ({ user_id, username, chatroom_id, is_typing }) => {
      if (chatroom_id === currentChatroom?.id && user_id !== user?.id) {
        setTypingUsers(prev => {
          if (is_typing) {
            const exists = prev.find(u => u.user_id === user_id);
            if (exists) return prev;
            return [...prev, { user_id, username }];
          } else {
            return prev.filter(u => u.user_id !== user_id);
          }
        });
      }
    };

    // Add event listeners
    websocketService.on('connected', handleConnected);
    websocketService.on('disconnected', handleDisconnected);
    websocketService.on('error', handleError);
    websocketService.on('message_received', handleMessageReceived);
    websocketService.on('user_joined', handleUserJoined);
    websocketService.on('user_left', handleUserLeft);
    websocketService.on('user_online', handleUserOnline);
    websocketService.on('user_offline', handleUserOffline);
    websocketService.on('typing_indicator', handleTypingIndicator);

    return () => {
      // Remove event listeners
      websocketService.off('connected', handleConnected);
      websocketService.off('disconnected', handleDisconnected);
      websocketService.off('error', handleError);
      websocketService.off('message_received', handleMessageReceived);
      websocketService.off('user_joined', handleUserJoined);
      websocketService.off('user_left', handleUserLeft);
      websocketService.off('user_online', handleUserOnline);
      websocketService.off('user_offline', handleUserOffline);
      websocketService.off('typing_indicator', handleTypingIndicator);
    };
  }, [currentChatroom, user]);

  const initializeConnection = async () => {
    try {
      setLoading(true);
      setConnectionStatus('connecting');
      
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const isDemo = localStorage.getItem('demo_mode') === 'true';
      
      if (isDemo) {
        console.log('Running in demo mode - using localStorage for chat data');
        setConnectionStatus('connected');
        loadChatrooms(); // Load demo chatrooms
        return;
      }

      // Set token for chat service
      chatService.setToken(token);
      
      // Initialize WebSocket connection
      await websocketService.initialize(user, token);
      
    } catch (error) {
      console.error('Failed to initialize connection:', error);
      
      // Fall back to demo mode if connection fails
      if (error.message.includes('fetch') || error.message.includes('WebSocket')) {
        console.warn('Server connection failed, falling back to demo mode');
        localStorage.setItem('demo_mode', 'true');
        setConnectionStatus('connected');
        setError('Running in demo mode - server not available');
        loadChatrooms();
      } else {
        setError('Failed to connect to chat server');
        setConnectionStatus('error');
      }
    } finally {
      setLoading(false);
    }
  };

  const disconnectWebSocket = () => {
    websocketService.disconnect();
    setConnectionStatus('disconnected');
    setMessages([]);
    setChatrooms([]);
    setCurrentChatroom(null);
    setOnlineUsers([]);
    setTypingUsers([]);
  };

  const loadChatrooms = async () => {
    try {
      setLoading(true);
      
      const isDemo = localStorage.getItem('demo_mode') === 'true';
      if (isDemo) {
        // Load demo chatrooms from localStorage
        const demoRooms = JSON.parse(localStorage.getItem('demo_chatrooms') || '[]');
        setChatrooms(demoRooms);
        return;
      }
      
      const rooms = await chatService.getChatrooms();
      setChatrooms(rooms);
    } catch (error) {
      console.error('Failed to load chatrooms:', error);
      setError('Failed to load chatrooms');
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (chatroomId) => {
    try {
      setLoading(true);
      
      const isDemo = localStorage.getItem('demo_mode') === 'true';
      if (isDemo) {
        // Load demo messages from localStorage
        const demoMessages = JSON.parse(localStorage.getItem('demo_messages') || '{}');
        const msgs = demoMessages[chatroomId] || [];
        setMessages(msgs);
        return;
      }
      
      const msgs = await chatService.getMessages(chatroomId, 50);
      setMessages(msgs || []);
    } catch (error) {
      console.error('Failed to load messages:', error);
      setError('Failed to load messages');
      setMessages([]);
    } finally {
      setLoading(false);
    }
  };

  const loadOnlineUsers = async (chatroomId) => {
    try {
      const users = await chatService.getOnlineUsers(chatroomId);
      setOnlineUsers(users || []);
    } catch (error) {
      console.error('Failed to load online users:', error);
      setOnlineUsers([]);
    }
  };

  const createChatroom = async (name, description = '', isPrivate = true) => {
    try {
      setLoading(true);
      
      const isDemo = localStorage.getItem('demo_mode') === 'true';
      if (isDemo) {
        // Create demo chatroom
        const chatroom = {
          id: `demo-room-${Date.now()}`,
          name,
          description,
          secret_code: Math.random().toString(36).substr(2, 8).toUpperCase(),
          is_private: isPrivate,
          encryption_enabled: true,
          created_by: user.id,
          created_at: new Date().toISOString(),
          member_count: 1
        };
        
        // Save to localStorage
        const demoRooms = JSON.parse(localStorage.getItem('demo_chatrooms') || '[]');
        demoRooms.push(chatroom);
        localStorage.setItem('demo_chatrooms', JSON.stringify(demoRooms));
        
        setChatrooms(prev => [...prev, chatroom]);
        return chatroom;
      }
      
      const chatroom = await chatService.createChatroom(name, description, isPrivate);
      setChatrooms(prev => [...prev, chatroom]);
      return chatroom;
    } catch (error) {
      console.error('Failed to create chatroom:', error);
      setError('Failed to create chatroom: ' + error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const joinChatroomByCode = async (secretCode) => {
    try {
      setLoading(true);
      
      const isDemo = localStorage.getItem('demo_mode') === 'true';
      if (isDemo) {
        // Look for existing demo chatroom or create one
        const demoRooms = JSON.parse(localStorage.getItem('demo_chatrooms') || '[]');
        let chatroom = demoRooms.find(room => room.secret_code === secretCode);
        
        if (!chatroom) {
          // Create a new demo chatroom with the provided code
          chatroom = {
            id: `demo-room-${Date.now()}`,
            name: `Room ${secretCode}`,
            description: `Joined using code ${secretCode}`,
            secret_code: secretCode,
            is_private: true,
            encryption_enabled: true,
            created_by: 'unknown',
            created_at: new Date().toISOString(),
            member_count: 1
          };
          
          demoRooms.push(chatroom);
          localStorage.setItem('demo_chatrooms', JSON.stringify(demoRooms));
        }
        
        setChatrooms(prev => {
          const exists = prev.find(room => room.id === chatroom.id);
          return exists ? prev : [...prev, chatroom];
        });
        
        return chatroom;
      }
      
      const chatroom = await chatService.joinChatroomByCode(secretCode);
      
      // Add to chatrooms list if not already present
      setChatrooms(prev => {
        const exists = prev.find(room => room.id === chatroom.id);
        return exists ? prev : [...prev, chatroom];
      });
      
      return chatroom;
    } catch (error) {
      console.error('Failed to join chatroom:', error);
      setError('Failed to join chatroom: ' + error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const selectChatroom = async (chatroom) => {
    try {
      // Leave current chatroom if any
      if (currentChatroom) {
        websocketService.leaveChatroom(currentChatroom.id);
      }

      setCurrentChatroom(chatroom);
      setMessages([]);
      setOnlineUsers([]);
      setTypingUsers([]);
      
      // Join new chatroom
      websocketService.joinChatroom(chatroom.id);
      
      // Load messages and online users
      await Promise.all([
        loadMessages(chatroom.id),
        loadOnlineUsers(chatroom.id)
      ]);
      
      console.log(`Selected chatroom: ${chatroom.name}`);
      
    } catch (error) {
      console.error('Failed to select chatroom:', error);
      setError('Failed to load chatroom');
    }
  };

  const sendMessage = async (content, messageType = 'text') => {
    if (!currentChatroom || !content.trim()) return;

    try {
      const isDemo = localStorage.getItem('demo_mode') === 'true';
      
      if (isDemo) {
        // Create demo message
        const message = {
          id: `demo-msg-${Date.now()}`,
          chatroom_id: currentChatroom.id,
          user_id: user.id,
          username: user.username,
          display_name: user.display_name || user.username,
          content: content.trim(),
          message_type: messageType,
          timestamp: new Date().toISOString(),
          edited: false
        };
        
        // Save to localStorage
        const demoMessages = JSON.parse(localStorage.getItem('demo_messages') || '{}');
        if (!demoMessages[currentChatroom.id]) {
          demoMessages[currentChatroom.id] = [];
        }
        demoMessages[currentChatroom.id].push(message);
        localStorage.setItem('demo_messages', JSON.stringify(demoMessages));
        
        // Add to messages list immediately
        setMessages(prev => [...prev, message]);
        
        // Simulate receiving messages from other demo users after a delay
        setTimeout(() => {
          const demoUsers = ['Alice', 'Bob', 'Charlie'];
          const randomUser = demoUsers[Math.floor(Math.random() * demoUsers.length)];
          if (randomUser !== user.username && Math.random() > 0.5) {
            const replyMessage = {
              id: `demo-msg-${Date.now()}-reply`,
              chatroom_id: currentChatroom.id,
              user_id: `demo-${randomUser}`,
              username: randomUser,
              display_name: randomUser,
              content: `Hey ${user.username}! I saw your message: "${content.trim()}"`,
              message_type: 'text',
              timestamp: new Date().toISOString(),
              edited: false
            };
            
            demoMessages[currentChatroom.id].push(replyMessage);
            localStorage.setItem('demo_messages', JSON.stringify(demoMessages));
            setMessages(prev => [...prev, replyMessage]);
          }
        }, 1000 + Math.random() * 2000);
        
        return;
      }

      const clientId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Send via WebSocket
      const success = websocketService.sendMessage(
        currentChatroom.id, 
        content.trim(), 
        messageType, 
        clientId
      );

      if (!success) {
        throw new Error('Failed to send message via WebSocket');
      }

    } catch (error) {
      console.error('Failed to send message:', error);
      setError('Failed to send message');
    }
  };

  const sendTypingIndicator = useCallback(async (isTyping) => {
    if (!currentChatroom) return;

    try {
      if (isTyping) {
        websocketService.sendTypingStart(currentChatroom.id);
      } else {
        websocketService.sendTypingStop(currentChatroom.id);
      }
    } catch (error) {
      console.error('Failed to send typing indicator:', error);
    }
  }, [currentChatroom]);

  const deleteChatroom = async (chatroomId) => {
    try {
      await chatService.deleteChatroom(chatroomId);
      setChatrooms(prev => prev.filter(room => room.id !== chatroomId));
      
      if (currentChatroom?.id === chatroomId) {
        setCurrentChatroom(null);
        setMessages([]);
        setOnlineUsers([]);
      }
      
    } catch (error) {
      console.error('Failed to delete chatroom:', error);
      setError('Failed to delete chatroom');
    }
  };

  const leaveChatroom = async (chatroomId) => {
    try {
      await chatService.leaveChatroom(chatroomId);
      setChatrooms(prev => prev.filter(room => room.id !== chatroomId));
      
      if (currentChatroom?.id === chatroomId) {
        websocketService.leaveChatroom(chatroomId);
        setCurrentChatroom(null);
        setMessages([]);
        setOnlineUsers([]);
      }
      
    } catch (error) {
      console.error('Failed to leave chatroom:', error);
      setError('Failed to leave chatroom');
    }
  };

  const getConnectionStatus = () => {
    return {
      status: connectionStatus,
      websocketStatus: websocketService.getConnectionStatus(),
      connectedUsersCount: onlineUsers.length
    };
  };

  const value = {
    // State
    messages,
    chatrooms,
    currentChatroom,
    onlineUsers,
    loading,
    error,
    typingUsers,
    connectionStatus,
    
    // Actions
    createChatroom,
    joinChatroomByCode,
    selectChatroom,
    sendMessage,
    sendTypingIndicator,
    deleteChatroom,
    leaveChatroom,
    loadChatrooms,
    getConnectionStatus,
    
    // Utilities
    setError: (error) => setError(error),
    clearError: () => setError(null)
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
};

export default ChatContext;
