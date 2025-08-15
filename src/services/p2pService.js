/**
 * Peer-to-Peer Service
 * Handles WebRTC connections for direct peer-to-peer communication
 */

import storageService from './storageService.js';
import encryptionService from './encryptionService.js';

class P2PService {
  constructor() {
    this.peers = new Map(); // Map of peerId -> RTCPeerConnection
    this.dataChannels = new Map(); // Map of peerId -> RTCDataChannel
    this.signalingServer = null; // Simple signaling server for peer discovery
    this.currentUser = null;
    this.eventListeners = new Map();
    this.isInitialized = false;
    this.joinedRooms = new Map(); // Map of chatroomId -> secretCode
    this.roomPresenceTimers = new Map(); // Map of chatroomId -> intervalId
    
    // WebRTC configuration
    this.rtcConfig = {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' },
        { urls: 'stun:stun2.l.google.com:19302' }
      ]
    };

    // Simple signaling server (you can replace with any WebSocket server)
    this.signalingUrl = 'wss://signaling-server.example.com'; // Replace with actual signaling server
    this.useLocalSignaling = true; // Use local storage for signaling in demo
  }

  /**
   * Initialize P2P service
   */
  async initialize(user) {
    if (this.isInitialized) return;

    this.currentUser = user;
    
    // Initialize signaling
    if (this.useLocalSignaling) {
      this.initializeLocalSignaling();
    } else {
      await this.initializeWebSocketSignaling();
    }

    this.isInitialized = true;
    console.log('P2P Service initialized');
  }

  /**
   * Initialize local signaling using localStorage for demo purposes
   * In production, you'd use a WebSocket signaling server
   */
  initializeLocalSignaling() {
    // Listen for signaling messages in localStorage
    window.addEventListener('storage', (event) => {
      if (event.key && event.key.startsWith('p2p-signal-')) {
        const targetUserId = event.key.replace('p2p-signal-', '');
        if (targetUserId === this.currentUser.id && event.newValue) {
          try {
            const signal = JSON.parse(event.newValue);
            this.handleSignalingMessage(signal);
          } catch (error) {
            console.error('Failed to parse signaling message:', error);
          }
        }
      }

      // Room presence announcements
      if (event.key && event.key.startsWith('p2p-room-') && event.newValue) {
        try {
          const presence = JSON.parse(event.newValue);
          const { type, from, username, chatroomId } = presence || {};
          if (!type || from === this.currentUser.id) return;

          // Only react to presence for rooms we have joined
          if (type === 'presence' && this.joinedRooms.has(chatroomId)) {
            // Simple glare avoidance: only the lexicographically greater user initiates
            if (this.shouldInitiateConnection(from)) {
              if (!this.peers.has(from)) {
                console.log(`Presence detected for room ${chatroomId} from ${username} (${from}), initiating connection`);
                this.connectToPeer(from).catch((err) => console.error('Connect to peer failed:', err));
              }
            } else {
              // Let the other side initiate
              console.log(`Presence detected from ${from}, waiting for them to initiate (glare avoidance)`);
            }
          }
        } catch (error) {
          console.error('Failed to parse room presence message:', error);
        }
      }
    });

    console.log('Local signaling initialized');
  }

  /**
   * Decide who initiates to avoid glare (both initiating at once)
   * Returns true if this client should initiate connection to otherUserId
   */
  shouldInitiateConnection(otherUserId) {
    try {
      // Stable ordering by string compare
      return String(this.currentUser.id) > String(otherUserId);
    } catch (_) {
      return true;
    }
  }

  /**
   * Announce presence in a chatroom and remember joined room
   * @param {string} chatroomId
   * @param {string} secretCode
   */
  joinRoom(chatroomId, secretCode) {
    if (!chatroomId || !secretCode) return;
    // Remember this room
    this.joinedRooms.set(chatroomId, secretCode);
    // Announce presence so other tabs can connect
    this.sendRoomSignal(secretCode, {
      type: 'presence',
      chatroomId,
      from: this.currentUser.id,
      username: this.currentUser.username,
      timestamp: Date.now(),
    });

    // Start periodic presence pings for better discovery
    if (!this.roomPresenceTimers.has(chatroomId)) {
      const intervalId = setInterval(() => {
        this.sendRoomSignal(secretCode, {
          type: 'presence',
          chatroomId,
          from: this.currentUser.id,
          username: this.currentUser.username,
          timestamp: Date.now(),
        });
      }, 3000);
      this.roomPresenceTimers.set(chatroomId, intervalId);
    }
  }

  /**
   * Send a broadcast signal for a specific room via localStorage
   */
  sendRoomSignal(secretCode, payload) {
    try {
      const key = `p2p-room-${secretCode}`;
      localStorage.setItem(key, JSON.stringify(payload));
      // Clean up shortly after to allow future events
      setTimeout(() => {
        // Only remove if the same payload (avoid races)
        const current = localStorage.getItem(key);
        if (current) {
          try {
            const parsed = JSON.parse(current);
            if (parsed && parsed.timestamp === payload.timestamp) {
              localStorage.removeItem(key);
            }
          } catch (_) {
            localStorage.removeItem(key);
          }
        }
      }, 2000);
    } catch (error) {
      console.error('Failed to send room signal:', error);
    }
  }

  /**
   * Initialize WebSocket signaling server
   */
  async initializeWebSocketSignaling() {
    return new Promise((resolve, reject) => {
      try {
        this.signalingServer = new WebSocket(this.signalingUrl);
        
        this.signalingServer.onopen = () => {
          console.log('Connected to signaling server');
          
          // Register with signaling server
          this.sendSignalingMessage({
            type: 'register',
            userId: this.currentUser.id,
            username: this.currentUser.username
          });
          
          resolve();
        };

        this.signalingServer.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleSignalingMessage(message);
          } catch (error) {
            console.error('Failed to parse signaling message:', error);
          }
        };

        this.signalingServer.onerror = (error) => {
          console.error('Signaling server error:', error);
          reject(error);
        };

        this.signalingServer.onclose = () => {
          console.log('Disconnected from signaling server');
          this.signalingServer = null;
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Create a new peer connection
   */
  async createPeerConnection(peerId, isInitiator = false) {
    const peerConnection = new RTCPeerConnection(this.rtcConfig);
    
    // Store the peer connection
    this.peers.set(peerId, peerConnection);

    // Set up event handlers
    peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        this.sendSignalingMessage({
          type: 'ice-candidate',
          candidate: event.candidate,
          to: peerId,
          from: this.currentUser.id
        });
      }
    };

    peerConnection.onconnectionstatechange = () => {
      console.log(`Peer ${peerId} connection state:`, peerConnection.connectionState);
      
      if (peerConnection.connectionState === 'connected') {
        this.emit('peer-connected', { peerId });
        this.updatePeerStatus(peerId, true);
      } else if (peerConnection.connectionState === 'disconnected' || 
                 peerConnection.connectionState === 'failed') {
        this.emit('peer-disconnected', { peerId });
        this.updatePeerStatus(peerId, false);
        this.cleanupPeerConnection(peerId);
      }
    };

    // Create data channel for messages
    if (isInitiator) {
      const dataChannel = peerConnection.createDataChannel('messages', {
        ordered: true
      });
      this.setupDataChannel(peerId, dataChannel);
    } else {
      peerConnection.ondatachannel = (event) => {
        this.setupDataChannel(peerId, event.channel);
      };
    }

    return peerConnection;
  }

  /**
   * Setup data channel for peer communication
   */
  setupDataChannel(peerId, dataChannel) {
    this.dataChannels.set(peerId, dataChannel);

    dataChannel.onopen = () => {
      console.log(`Data channel opened with peer ${peerId}`);
      this.emit('data-channel-open', { peerId });

      // Share our info and joined rooms so peers can record presence
      const rooms = Array.from(this.joinedRooms.keys());
      rooms.forEach((roomId) => {
        try {
          const infoMessage = {
            type: 'peer-info',
            chatroomId: roomId,
            userInfo: {
              userId: this.currentUser.id,
              username: this.currentUser.username,
            },
          };
          dataChannel.send(JSON.stringify(infoMessage));
        } catch (err) {
          console.error('Failed to send peer-info:', err);
        }
      });
    };

    dataChannel.onclose = () => {
      console.log(`Data channel closed with peer ${peerId}`);
      this.emit('data-channel-close', { peerId });
    };

    dataChannel.onmessage = async (event) => {
      try {
        const message = JSON.parse(event.data);
        await this.handlePeerMessage(peerId, message);
      } catch (error) {
        console.error('Failed to parse peer message:', error);
      }
    };

    dataChannel.onerror = (error) => {
      console.error(`Data channel error with peer ${peerId}:`, error);
    };
  }

  /**
   * Connect to a peer
   */
  async connectToPeer(peerId) {
    if (this.peers.has(peerId)) {
      console.log(`Already connected to peer ${peerId}`);
      return;
    }

    console.log(`Connecting to peer ${peerId}`);
    
    const peerConnection = await this.createPeerConnection(peerId, true);
    
    // Create offer
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);

    // Send offer through signaling
    this.sendSignalingMessage({
      type: 'offer',
      offer: offer,
      to: peerId,
      from: this.currentUser.id
    });
  }

  /**
   * Handle incoming signaling messages
   */
  async handleSignalingMessage(message) {
    const { type, from, to } = message;

    // Ignore messages not intended for us
    if (to && to !== this.currentUser.id) return;

    switch (type) {
      case 'offer':
        await this.handleOffer(message);
        break;
      
      case 'answer':
        await this.handleAnswer(message);
        break;
      
      case 'ice-candidate':
        await this.handleIceCandidate(message);
        break;
      
      case 'peer-list':
        this.handlePeerList(message);
        break;
      
      default:
        console.log('Unknown signaling message type:', type);
    }
  }

  /**
   * Handle incoming offer
   */
  async handleOffer(message) {
    const { offer, from } = message;
    
    console.log(`Received offer from ${from}`);
    
    const peerConnection = await this.createPeerConnection(from, false);
    
    await peerConnection.setRemoteDescription(offer);
    
    // Create answer
    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);

    // Send answer
    this.sendSignalingMessage({
      type: 'answer',
      answer: answer,
      to: from,
      from: this.currentUser.id
    });
  }

  /**
   * Handle incoming answer
   */
  async handleAnswer(message) {
    const { answer, from } = message;
    
    console.log(`Received answer from ${from}`);
    
    const peerConnection = this.peers.get(from);
    if (peerConnection) {
      await peerConnection.setRemoteDescription(answer);
    }
  }

  /**
   * Handle ICE candidate
   */
  async handleIceCandidate(message) {
    const { candidate, from } = message;
    
    const peerConnection = this.peers.get(from);
    if (peerConnection) {
      await peerConnection.addIceCandidate(candidate);
    }
  }

  /**
   * Handle peer list from signaling server
   */
  handlePeerList(message) {
    const { peers } = message;
    this.emit('peer-list-updated', { peers });
  }

  /**
   * Send message through signaling
   */
  sendSignalingMessage(message) {
    if (this.useLocalSignaling) {
      // For local signaling, store message in localStorage
      const key = `p2p-signal-${message.to}`;
      localStorage.setItem(key, JSON.stringify(message));
      
      // Clean up after a short delay
      setTimeout(() => {
        localStorage.removeItem(key);
      }, 5000);
    } else if (this.signalingServer && this.signalingServer.readyState === WebSocket.OPEN) {
      this.signalingServer.send(JSON.stringify(message));
    } else {
      console.warn('Signaling server not connected');
    }
  }

  /**
   * Send message to peer
   */
  async sendMessageToPeer(peerId, message) {
    const dataChannel = this.dataChannels.get(peerId);
    
    if (dataChannel && dataChannel.readyState === 'open') {
      try {
        dataChannel.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error(`Failed to send message to peer ${peerId}:`, error);
        return false;
      }
    } else {
      console.warn(`Data channel not open for peer ${peerId}`);
      return false;
    }
  }

  /**
   * Broadcast message to all peers in chatroom
   */
  async broadcastMessage(chatroomId, message) {
    const results = [];
    // Send to all open data channels (peers). The message carries chatroomId.
    for (const [peerUserId, channel] of this.dataChannels.entries()) {
      if (channel && channel.readyState === 'open' && peerUserId !== this.currentUser.id) {
        const success = await this.sendMessageToPeer(peerUserId, {
          type: 'chat-message',
          chatroomId,
          message,
        });
        results.push({ peerId: peerUserId, success });
      }
    }
    return results;
  }

  /**
   * Handle incoming peer message
   */
  async handlePeerMessage(peerId, data) {
    const { type } = data;

    switch (type) {
      case 'chat-message':
        await this.handleChatMessage(peerId, data);
        break;
      
      case 'typing-indicator':
        this.handleTypingIndicator(peerId, data);
        break;
      
      case 'peer-info':
        await this.handlePeerInfo(peerId, data);
        break;
      
      default:
        console.log('Unknown peer message type:', type);
    }
  }

  /**
   * Handle incoming chat message
   */
  async handleChatMessage(peerId, data) {
    const { chatroomId, message } = data;

    try {
      // Decrypt message if encrypted
      let decryptedContent = message.content;
      if (message.isEncrypted) {
        decryptedContent = await encryptionService.decryptMessage(chatroomId, message.content);
      }

      // Save message to local storage
      await storageService.saveMessage({
        ...message,
        content: decryptedContent,
        receivedFrom: peerId
      });

      // Emit event for UI update
      this.emit('message-received', {
        chatroomId,
        message: {
          ...message,
          content: decryptedContent
        },
        from: peerId
      });

    } catch (error) {
      console.error('Failed to handle chat message:', error);
    }
  }

  /**
   * Handle typing indicator
   */
  handleTypingIndicator(peerId, data) {
    this.emit('typing-indicator', {
      peerId,
      chatroomId: data.chatroomId,
      isTyping: data.isTyping,
      username: data.username
    });
  }

  /**
   * Handle peer info
   */
  async handlePeerInfo(peerId, data) {
    const { userInfo } = data;
    const { chatroomId } = data;
    if (!chatroomId) return;
    // Update peer information in storage for this room
    await storageService.savePeer({
      id: `${chatroomId}-${peerId}`,
      userId: peerId,
      username: userInfo.username,
      chatroomId: chatroomId,
      isOnline: true,
      lastSeen: new Date().toISOString(),
    });

    this.emit('peer-info-updated', { peerId, userInfo });
  }

  /**
   * Join chatroom by secret code
   */
  async joinChatroomByCode(secretCode) {
    try {
      // Check if chatroom exists locally first
      let chatroom = await storageService.getChatroomBySecretCode(secretCode);
      
      if (!chatroom) {
        // Try to discover chatroom through signaling
        this.sendSignalingMessage({
          type: 'discover-chatroom',
          secretCode: secretCode,
          from: this.currentUser.id
        });

        // Wait for response (in a real implementation, you'd handle this better)
        return new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            reject(new Error('Chatroom not found'));
          }, 10000);

          const handler = (data) => {
            if (data.secretCode === secretCode) {
              clearTimeout(timeout);
              this.off('chatroom-discovered', handler);
              resolve(data.chatroom);
            }
          };

          this.on('chatroom-discovered', handler);
        });
      }

      return chatroom;
    } catch (error) {
      console.error('Failed to join chatroom:', error);
      throw error;
    }
  }

  /**
   * Update peer status
   */
  async updatePeerStatus(peerId, isOnline) {
    await storageService.updatePeerStatus(peerId, isOnline);
    this.emit('peer-status-changed', { peerId, isOnline });
  }

  /**
   * Cleanup peer connection
   */
  cleanupPeerConnection(peerId) {
    const peerConnection = this.peers.get(peerId);
    if (peerConnection) {
      peerConnection.close();
      this.peers.delete(peerId);
    }

    const dataChannel = this.dataChannels.get(peerId);
    if (dataChannel) {
      dataChannel.close();
      this.dataChannels.delete(peerId);
    }

    console.log(`Cleaned up peer connection for ${peerId}`);
  }

  /**
   * Disconnect from all peers
   */
  disconnectAll() {
    for (const peerId of this.peers.keys()) {
      this.cleanupPeerConnection(peerId);
    }

    if (this.signalingServer) {
      this.signalingServer.close();
      this.signalingServer = null;
    }

    // Stop presence timers
    for (const intervalId of this.roomPresenceTimers.values()) {
      clearInterval(intervalId);
    }
    this.roomPresenceTimers.clear();

    console.log('Disconnected from all peers');
  }

  /**
   * Get connection status
   */
  getConnectionStatus() {
    const status = {
      connectedPeers: this.peers.size,
      activeDataChannels: this.dataChannels.size,
      signalingConnected: this.signalingServer ? 
        this.signalingServer.readyState === WebSocket.OPEN : false
    };

    return status;
  }

  // Event handling
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in P2P event listener for ${event}:`, error);
        }
      });
    }
  }
}

// Create singleton instance
const p2pService = new P2PService();

export default p2pService;
