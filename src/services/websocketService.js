/**
 * WebSocket Service
 * Handles server-based real-time communication
 */

class WebSocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.isConnecting = false;
    this.eventListeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.currentUser = null;
    this.currentChatroom = null;
    this.messageQueue = [];
  }

  /**
   * Initialize WebSocket connection
   */
  async initialize(user, token) {
    if (this.isConnected || this.isConnecting) {
      return;
    }

    this.currentUser = user;
    this.isConnecting = true;

    try {
      const wsUrl = `ws://localhost:8000/ws?token=${encodeURIComponent(token)}`;
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        
        // Process queued messages
        this.processMessageQueue();
        
        this.emit('connected', { user });
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.socket.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;
        this.isConnecting = false;
        
        this.emit('disconnected', { code: event.code, reason: event.reason });
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', { error });
      };

    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      this.isConnecting = false;
      throw error;
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  handleMessage(data) {
    const { event, data: eventData } = data;
    
    console.log('WebSocket message received:', event, eventData);

    switch (event) {
      case 'connected':
        this.emit('connected', eventData);
        break;
        
      case 'message_received':
        this.emit('message_received', eventData);
        break;
        
      case 'user_joined':
        this.emit('user_joined', eventData);
        break;
        
      case 'user_left':
        this.emit('user_left', eventData);
        break;
        
      case 'user_online':
        this.emit('user_online', eventData);
        break;
        
      case 'user_offline':
        this.emit('user_offline', eventData);
        break;
        
      case 'typing_indicator':
        this.emit('typing_indicator', eventData);
        break;
        
      case 'pong':
        this.emit('pong', eventData);
        break;
        
      default:
        console.log('Unknown WebSocket event:', event);
        this.emit(event, eventData);
    }
  }

  /**
   * Send message through WebSocket
   */
  send(event, data) {
    const message = { event, data };
    
    if (this.isConnected && this.socket.readyState === WebSocket.OPEN) {
      try {
        this.socket.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        return false;
      }
    } else {
      // Queue message for later
      this.messageQueue.push(message);
      return false;
    }
  }

  /**
   * Join a chatroom
   */
  joinChatroom(chatroomId) {
    this.currentChatroom = chatroomId;
    return this.send('join_chatroom', { chatroom_id: chatroomId });
  }

  /**
   * Leave a chatroom
   */
  leaveChatroom(chatroomId) {
    if (this.currentChatroom === chatroomId) {
      this.currentChatroom = null;
    }
    return this.send('leave_chatroom', { chatroom_id: chatroomId });
  }

  /**
   * Send a chat message
   */
  sendMessage(chatroomId, content, messageType = 'text', clientId = null) {
    return this.send('send_message', {
      chatroom_id: chatroomId,
      content,
      message_type: messageType,
      client_id: clientId || `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    });
  }

  /**
   * Send typing indicator
   */
  sendTypingStart(chatroomId) {
    return this.send('typing_start', { chatroom_id: chatroomId });
  }

  /**
   * Send typing stop indicator
   */
  sendTypingStop(chatroomId) {
    return this.send('typing_stop', { chatroom_id: chatroomId });
  }

  /**
   * Send ping to server
   */
  ping() {
    return this.send('ping', { timestamp: new Date().toISOString() });
  }

  /**
   * Process queued messages
   */
  processMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.socket.send(JSON.stringify(message));
    }
  }

  /**
   * Schedule reconnection attempt
   */
  scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (!this.isConnected && this.currentUser) {
        const token = localStorage.getItem('token');
        if (token) {
          this.initialize(this.currentUser, token);
        }
      }
    }, delay);
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect() {
    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
    this.isConnected = false;
    this.isConnecting = false;
    this.currentUser = null;
    this.currentChatroom = null;
    this.messageQueue = [];
  }

  /**
   * Get connection status
   */
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      isConnecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      currentChatroom: this.currentChatroom
    };
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
          console.error(`Error in WebSocket event listener for ${event}:`, error);
        }
      });
    }
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

export default websocketService;
