/**
 * WebSocket Service
 * Handles real-time communication with the backend WebSocket server
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.messageQueue = [];
    this.eventListeners = new Map();
    this.heartbeatInterval = null;
    this.heartbeatTimeout = null;
    this.token = null;
    this.userId = null;
    
    // Backend WebSocket URL
    this.wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
  }

  /**
   * Connect to WebSocket server
   * @param {string} token - JWT authentication token
   * @param {string} userId - User ID
   */
  async connect(token, userId) {
    if (this.isConnected) {
      console.warn('WebSocket already connected');
      return Promise.resolve();
    }

    this.token = token;
    this.userId = userId;

    return new Promise((resolve, reject) => {
      try {
        // Include token and user ID in WebSocket URL
        const wsUrl = `${this.wsUrl}?token=${encodeURIComponent(token)}&user_id=${encodeURIComponent(userId)}`;
        
        console.log('Connecting to WebSocket...');
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
          this.handleOpen();
          resolve();
        };
        
        this.ws.onmessage = this.handleMessage.bind(this);
        this.ws.onclose = this.handleClose.bind(this);
        this.ws.onerror = (error) => {
          this.handleError(error);
          reject(error);
        };
        
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.cleanup();
    }
  }

  /**
   * Send message through WebSocket
   * @param {Object} message - Message to send
   */
  send(message) {
    if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        this.messageQueue.push(message);
      }
    } else {
      // Queue message for when connection is restored
      this.messageQueue.push(message);
      console.warn('WebSocket not connected, message queued');
    }
  }

  /**
   * Send chat message
   * @param {string} chatroomId - Chatroom ID
   * @param {string} content - Message content
   * @param {string} messageType - Message type (text, image, file)
   * @param {Object} metadata - Additional message metadata
   */
  sendMessage(chatroomId, content, messageType = 'text', metadata = {}) {
    const message = {
      type: 'message',
      data: {
        chatroom_id: chatroomId,
        content,
        message_type: messageType,
        ...metadata
      }
    };
    
    this.send(message);
  }

  /**
   * Join a chatroom
   * @param {string} chatroomId - Chatroom ID to join
   */
  joinChatroom(chatroomId) {
    const message = {
      type: 'join_chatroom',
      data: {
        chatroom_id: chatroomId
      }
    };
    
    this.send(message);
  }

  /**
   * Leave a chatroom
   * @param {string} chatroomId - Chatroom ID to leave
   */
  leaveChatroom(chatroomId) {
    const message = {
      type: 'leave_chatroom',
      data: {
        chatroom_id: chatroomId
      }
    };
    
    this.send(message);
  }

  /**
   * Send typing indicator
   * @param {string} chatroomId - Chatroom ID
   * @param {boolean} isTyping - Whether user is typing
   */
  sendTypingIndicator(chatroomId, isTyping) {
    const message = {
      type: 'typing',
      data: {
        chatroom_id: chatroomId,
        is_typing: isTyping
      }
    };
    
    this.send(message);
  }

  /**
   * Update user status
   * @param {string} status - User status (online, away, busy, offline)
   */
  updateStatus(status) {
    const message = {
      type: 'status_update',
      data: {
        status
      }
    };
    
    this.send(message);
  }

  /**
   * Add event listener
   * @param {string} event - Event name
   * @param {Function} callback - Event callback
   */
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  /**
   * Remove event listener
   * @param {string} event - Event name
   * @param {Function} callback - Event callback to remove
   */
  off(event, callback) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  /**
   * Emit event to listeners
   * @param {string} event - Event name
   * @param {*} data - Event data
   */
  emit(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Handle WebSocket open event
   */
  handleOpen() {
    console.log('WebSocket connected successfully');
    this.isConnected = true;
    this.reconnectAttempts = 0;
    
    // Start heartbeat
    this.startHeartbeat();
    
    // Send queued messages
    this.flushMessageQueue();
    
    // Emit connection event
    this.emit('connected', { timestamp: new Date() });
  }

  /**
   * Handle WebSocket message event
   * @param {MessageEvent} event - WebSocket message event
   */
  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      
      // Handle different message types
      switch (message.type) {
        case 'message':
          this.emit('message', message.data);
          break;
          
        case 'typing':
          this.emit('typing', message.data);
          break;
          
        case 'user_joined':
          this.emit('user_joined', message.data);
          break;
          
        case 'user_left':
          this.emit('user_left', message.data);
          break;
          
        case 'status_update':
          this.emit('status_update', message.data);
          break;
          
        case 'error':
          this.emit('error', message.data);
          console.error('WebSocket error:', message.data);
          break;
          
        case 'pong':
          this.handlePong();
          break;
          
        default:
          console.warn('Unknown WebSocket message type:', message.type);
          this.emit('unknown_message', message);
      }
      
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket close event
   * @param {CloseEvent} event - WebSocket close event
   */
  handleClose(event) {
    console.log('WebSocket connection closed:', event.code, event.reason);
    this.cleanup();
    
    // Emit disconnection event
    this.emit('disconnected', { 
      code: event.code, 
      reason: event.reason,
      timestamp: new Date()
    });
    
    // Attempt reconnection if not a normal closure
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.attemptReconnect();
    }
  }

  /**
   * Handle WebSocket error event
   * @param {Event} event - WebSocket error event
   */
  handleError(event) {
    console.error('WebSocket error:', event);
    this.emit('connection_error', { error: event, timestamp: new Date() });
  }

  /**
   * Attempt to reconnect
   */
  attemptReconnect() {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
    
    setTimeout(() => {
      if (!this.isConnected && this.token && this.userId) {
        this.emit('reconnecting', { 
          attempt: this.reconnectAttempts,
          maxAttempts: this.maxReconnectAttempts
        });
        
        this.connect(this.token, this.userId).catch(error => {
          console.error('Reconnection failed:', error);
        });
      }
    }, delay);
  }

  /**
   * Flush queued messages
   */
  flushMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }

  /**
   * Start heartbeat mechanism
   */
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'ping' });
        
        // Set timeout for pong response
        this.heartbeatTimeout = setTimeout(() => {
          console.warn('Heartbeat timeout, closing connection');
          this.ws.close();
        }, 5000);
      }
    }, 30000); // Send ping every 30 seconds
  }

  /**
   * Handle pong response
   */
  handlePong() {
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  /**
   * Cleanup WebSocket connection
   */
  cleanup() {
    this.isConnected = false;
    this.ws = null;
    
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  /**
   * Get connection status
   * @returns {Object} Connection status information
   */
  getStatus() {
    return {
      isConnected: this.isConnected,
      readyState: this.ws ? this.ws.readyState : WebSocket.CLOSED,
      reconnectAttempts: this.reconnectAttempts,
      queuedMessages: this.messageQueue.length
    };
  }

  // Legacy methods for compatibility
  onMessage(handler) {
    this.on('message', handler);
    return () => this.off('message', handler);
  }

  onDisconnect(handler) {
    this.on('disconnected', handler);
    return () => this.off('disconnected', handler);
  }

  onError(handler) {
    this.on('connection_error', handler);
    return () => this.off('connection_error', handler);
  }

  onConnect(handler) {
    this.on('connected', handler);
    return () => this.off('connected', handler);
  }

  sendMessage(data) {
    this.send(data);
  }

  isConnected() {
    return this.isConnected;
  }

  getReadyState() {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED;
  }

  getReadyStateString() {
    const state = this.getReadyState();
    switch (state) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'OPEN';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'CLOSED';
      default:
        return 'UNKNOWN';
    }
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

export default websocketService;

