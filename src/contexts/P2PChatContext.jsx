import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import storageService from '../services/storageService';
import p2pService from '../services/p2pService';
import encryptionService from '../services/encryptionService';

const P2PChatContext = createContext();

export const useP2PChat = () => {
  const context = useContext(P2PChatContext);
  if (!context) {
    throw new Error('useP2PChat must be used within a P2PChatProvider');
  }
  return context;
};

export const P2PChatProvider = ({ children }) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [chatrooms, setChatrooms] = useState([]);
  const [currentChatroom, setCurrentChatroom] = useState(null);
  const [connectedPeers, setConnectedPeers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [typingUsers, setTypingUsers] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  // Initialize P2P service when user is available
  useEffect(() => {
    if (user) {
      initializeP2P();
    }

    return () => {
      if (p2pService.isInitialized) {
        p2pService.disconnectAll();
      }
    };
  }, [user]);

  // Set up P2P event listeners
  useEffect(() => {
    if (!p2pService.isInitialized) return;

    const handleMessageReceived = (data) => {
      const { chatroomId, message } = data;
      if (chatroomId === currentChatroom?.id) {
        setMessages(prev => [...prev, message]);
      }
    };

    const handlePeerConnected = (data) => {
      console.log('Peer connected:', data.peerId);
      setConnectionStatus('connected');
      loadConnectedPeers();
    };

    const handlePeerDisconnected = (data) => {
      console.log('Peer disconnected:', data.peerId);
      loadConnectedPeers();
    };

    const handleTypingIndicator = (data) => {
      const { peerId, chatroomId, isTyping, username } = data;
      
      if (chatroomId === currentChatroom?.id) {
        setTypingUsers(prev => {
          if (isTyping) {
            return [...prev.filter(u => u.peerId !== peerId), { peerId, username }];
          } else {
            return prev.filter(u => u.peerId !== peerId);
          }
        });
      }
    };

    p2pService.on('message-received', handleMessageReceived);
    p2pService.on('peer-connected', handlePeerConnected);
    p2pService.on('peer-disconnected', handlePeerDisconnected);
    p2pService.on('typing-indicator', handleTypingIndicator);

    return () => {
      p2pService.off('message-received', handleMessageReceived);
      p2pService.off('peer-connected', handlePeerConnected);
      p2pService.off('peer-disconnected', handlePeerDisconnected);
      p2pService.off('typing-indicator', handleTypingIndicator);
    };
  }, [currentChatroom]);

  const initializeP2P = async () => {
    try {
      setLoading(true);
      
      // Initialize storage
      await storageService.initialize();
      
      // Set current user in storage
      await storageService.setCurrentUser(user.id);
      
      // Save/update user info
      await storageService.saveUser(user);
      
      // Initialize P2P service
      await p2pService.initialize(user);
      
      // Load existing chatrooms
      await loadChatrooms();
      
      setConnectionStatus('initialized');
      console.log('P2P Chat initialized successfully');
    } catch (error) {
      console.error('Failed to initialize P2P chat:', error);
      setError('Failed to initialize chat system');
    } finally {
      setLoading(false);
    }
  };

  const loadChatrooms = async () => {
    try {
      const rooms = await storageService.getAllChatrooms();
      setChatrooms(rooms);
    } catch (error) {
      console.error('Failed to load chatrooms:', error);
      setError('Failed to load chatrooms');
    }
  };

  const loadMessages = async (chatroomId) => {
    try {
      setLoading(true);
      const msgs = await storageService.getMessages(chatroomId, 100);
      
      // Decrypt messages if needed
      const decryptedMessages = [];
      for (const msg of msgs) {
        if (msg.isEncrypted && encryptionService.getEncryptionStatus(chatroomId).isEnabled) {
          try {
            const decrypted = await encryptionService.decryptMessage(chatroomId, msg.content);
            decryptedMessages.push({ ...msg, content: decrypted });
          } catch (error) {
            console.warn('Failed to decrypt message:', error);
            decryptedMessages.push({ ...msg, content: '[Encrypted message]' });
          }
        } else {
          decryptedMessages.push(msg);
        }
      }
      
      setMessages(decryptedMessages);
    } catch (error) {
      console.error('Failed to load messages:', error);
      setError('Failed to load messages');
    } finally {
      setLoading(false);
    }
  };

  const loadConnectedPeers = async () => {
    try {
      if (currentChatroom) {
        const peers = await storageService.getPeers(currentChatroom.id);
        // For demo, show all users who have been in this chatroom
        // In real P2P, this would be actual connected peers
        setConnectedPeers(peers);
      }
    } catch (error) {
      console.error('Failed to load connected peers:', error);
    }
  };

  const addUserToChatroom = async (chatroomId, userInfo) => {
    try {
      // Add/update user in the chatroom's peer list
      const peerData = {
        id: `${chatroomId}-${userInfo.id}`,
        userId: userInfo.id,
        username: userInfo.username,
        displayName: userInfo.displayName || userInfo.username,
        chatroomId: chatroomId,
        isOnline: true,
        lastSeen: new Date().toISOString(),
        joinedAt: new Date().toISOString()
      };
      
      await storageService.savePeer(peerData);
      console.log(`Added user ${userInfo.username} to chatroom ${chatroomId}`);
    } catch (error) {
      console.error('Failed to add user to chatroom:', error);
    }
  };

  const createChatroom = async (name, description = '', isPrivate = true) => {
    try {
      setLoading(true);
      
      const chatroomData = {
        name,
        description,
        createdBy: user.id,
        isPrivate,
        encryptionEnabled: true
      };
      
      const chatroom = await storageService.saveChatroom(chatroomData);
      
      // Generate encryption key for the room
      if (chatroom.encryptionEnabled) {
        await encryptionService.generateRoomKey(chatroom.id, chatroom.secretCode);
      }
      
      // Add to chatrooms list
      setChatrooms(prev => [...prev, chatroom]);
      
      return chatroom;
    } catch (error) {
      console.error('Failed to create chatroom:', error);
      setError('Failed to create chatroom');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const joinChatroomByCode = async (secretCode) => {
    try {
      setLoading(true);
      
      // Check if chatroom exists locally
      let chatroom = await storageService.getChatroomBySecretCode(secretCode);
      
      if (!chatroom) {
        // For demo purposes, create a placeholder chatroom that can be joined
        // In a real P2P implementation, this would be discovered through the network
        console.log(`Creating placeholder chatroom for code: ${secretCode}`);
        
        chatroom = {
          id: storageService.generateId(),
          name: `Room ${secretCode}`,
          description: `Joined using code ${secretCode}`,
          secretCode: secretCode,
          createdBy: 'unknown', // Since we don't know who created it
          createdAt: new Date().toISOString(),
          isPrivate: true,
          maxMembers: 50,
          encryptionEnabled: true
        };
        
        // Save the chatroom locally
        await storageService.saveChatroom(chatroom);
      }
      
      // Generate encryption key using the secret code (room id now equals code)
      if (chatroom.encryptionEnabled) {
        await encryptionService.generateRoomKey(chatroom.id, secretCode);
      }
      
      // Update chatrooms list if not already present
      setChatrooms(prev => {
        const exists = prev.find(room => room.id === chatroom.id);
        return exists ? prev : [...prev, chatroom];
      });
      
      // Add current user to the chatroom's peer list and announce presence
      await addUserToChatroom(chatroom.id, user);
      p2pService.joinRoom(chatroom.id, secretCode);
      
      console.log(`Successfully joined chatroom: ${chatroom.name}`);
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
      setCurrentChatroom(chatroom);
      setMessages([]);
      setTypingUsers([]);
      
      // Load messages for this chatroom
      await loadMessages(chatroom.id);
      
      // Add current user to this chatroom's peer list
      await addUserToChatroom(chatroom.id, user);

      // Announce presence for P2P discovery (local signaling)
      if (chatroom.secretCode) {
        p2pService.joinRoom(chatroom.id, chatroom.secretCode);
      }
      
      // Load connected peers (including current user)
      await loadConnectedPeers();
      
      console.log(`Selected chatroom: ${chatroom.name}`);
      
    } catch (error) {
      console.error('Failed to select chatroom:', error);
      setError('Failed to load chatroom');
    }
  };

  const sendMessage = async (content, messageType = 'text') => {
    if (!currentChatroom || !content.trim()) return;

    try {
      // Create message object
      const message = {
        chatroomId: currentChatroom.id,
        userId: user.id,
        username: user.username,
        content: content.trim(),
        messageType,
        timestamp: new Date().toISOString(),
        isEncrypted: false
      };

      // Encrypt message if encryption is enabled
      if (currentChatroom.encryptionEnabled && 
          encryptionService.getEncryptionStatus(currentChatroom.id).isEnabled) {
        try {
          const encrypted = await encryptionService.encryptMessage(currentChatroom.id, content);
          message.content = encrypted;
          message.isEncrypted = true;
        } catch (error) {
          console.warn('Failed to encrypt message, sending unencrypted:', error);
        }
      }

      // Save message locally
      await storageService.saveMessage(message);

      // Add to messages list (with decrypted content for display)
      const displayMessage = {
        ...message,
        content: content.trim() // Show original content in UI
      };
      setMessages(prev => [...prev, displayMessage]);

      // Broadcast to connected peers
      const results = await p2pService.broadcastMessage(currentChatroom.id, message);
      
      console.log('Message broadcast results:', results);

    } catch (error) {
      console.error('Failed to send message:', error);
      setError('Failed to send message');
    }
  };

  const sendTypingIndicator = useCallback(async (isTyping) => {
    if (!currentChatroom) return;

    try {
      // Broadcast typing indicator to peers
      const peers = await storageService.getPeers(currentChatroom.id);
      
      for (const peer of peers) {
        if (peer.isOnline && peer.userId !== user.id) {
          await p2pService.sendMessageToPeer(peer.userId, {
            type: 'typing-indicator',
            chatroomId: currentChatroom.id,
            isTyping,
            username: user.username
          });
        }
      }
    } catch (error) {
      console.error('Failed to send typing indicator:', error);
    }
  }, [currentChatroom, user]);

  const deleteChatroom = async (chatroomId) => {
    try {
      await storageService.deleteChatroom(chatroomId);
      setChatrooms(prev => prev.filter(room => room.id !== chatroomId));
      
      if (currentChatroom?.id === chatroomId) {
        setCurrentChatroom(null);
        setMessages([]);
      }
      
      // Clear encryption keys
      encryptionService.clearChatroomKeys(chatroomId);
      
    } catch (error) {
      console.error('Failed to delete chatroom:', error);
      setError('Failed to delete chatroom');
    }
  };

  const exportChatData = async () => {
    try {
      const data = await storageService.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `chat-backup-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export chat data:', error);
      setError('Failed to export data');
    }
  };

  const importChatData = async (file) => {
    try {
      setLoading(true);
      
      const text = await file.text();
      const data = JSON.parse(text);
      
      await storageService.importData(data);
      await loadChatrooms();
      
      console.log('Chat data imported successfully');
    } catch (error) {
      console.error('Failed to import chat data:', error);
      setError('Failed to import data');
    } finally {
      setLoading(false);
    }
  };

  const clearAllData = async () => {
    try {
      await storageService.clearAllData();
      setChatrooms([]);
      setMessages([]);
      setCurrentChatroom(null);
      setConnectedPeers([]);
      encryptionService.clearAllKeys();
      
      console.log('All data cleared');
    } catch (error) {
      console.error('Failed to clear data:', error);
      setError('Failed to clear data');
    }
  };

  const getConnectionStatus = () => {
    return {
      status: connectionStatus,
      p2pStatus: p2pService.getConnectionStatus(),
      encryptionSupported: encryptionService.isSupported,
      connectedPeersCount: connectedPeers.length
    };
  };

  const value = {
    // State
    messages,
    chatrooms,
    currentChatroom,
    connectedPeers,
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
    exportChatData,
    importChatData,
    clearAllData,
    getConnectionStatus,
    
    // Utilities
    setError: (error) => setError(error),
    clearError: () => setError(null)
  };

  return (
    <P2PChatContext.Provider value={value}>
      {children}
    </P2PChatContext.Provider>
  );
};

export default P2PChatContext;
