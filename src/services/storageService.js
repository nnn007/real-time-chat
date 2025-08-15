/**
 * Browser Storage Service
 * Handles local storage using IndexedDB for peer-to-peer chat application
 */

class StorageService {
  constructor() {
    this.dbName = 'P2PChatDB';
    this.version = 1;
    this.db = null;
    this.isInitialized = false;
  }

  /**
   * Initialize IndexedDB database
   */
  async initialize() {
    if (this.isInitialized) return this.db;

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = () => {
        console.error('Failed to open IndexedDB:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        this.isInitialized = true;
        console.log('IndexedDB initialized successfully');
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Users store
        if (!db.objectStoreNames.contains('users')) {
          const userStore = db.createObjectStore('users', { keyPath: 'id' });
          userStore.createIndex('username', 'username', { unique: true });
        }

        // Chatrooms store
        if (!db.objectStoreNames.contains('chatrooms')) {
          const chatroomStore = db.createObjectStore('chatrooms', { keyPath: 'id' });
          chatroomStore.createIndex('secretCode', 'secretCode', { unique: true });
          chatroomStore.createIndex('createdAt', 'createdAt');
        }

        // Messages store
        if (!db.objectStoreNames.contains('messages')) {
          const messageStore = db.createObjectStore('messages', { keyPath: 'id' });
          messageStore.createIndex('chatroomId', 'chatroomId');
          messageStore.createIndex('timestamp', 'timestamp');
          messageStore.createIndex('chatroomTimestamp', ['chatroomId', 'timestamp']);
        }

        // Peers store (for connected peers in chatrooms)
        if (!db.objectStoreNames.contains('peers')) {
          const peerStore = db.createObjectStore('peers', { keyPath: 'id' });
          peerStore.createIndex('chatroomId', 'chatroomId');
          peerStore.createIndex('lastSeen', 'lastSeen');
        }

        // Encryption keys store
        if (!db.objectStoreNames.contains('encryptionKeys')) {
          const keyStore = db.createObjectStore('encryptionKeys', { keyPath: 'id' });
          keyStore.createIndex('chatroomId', 'chatroomId');
        }

        // User settings store
        if (!db.objectStoreNames.contains('settings')) {
          db.createObjectStore('settings', { keyPath: 'key' });
        }

        console.log('IndexedDB schema created/updated');
      };
    });
  }

  /**
   * Generic method to add/update data in a store
   */
  async put(storeName, data) {
    await this.initialize();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.put(data);

      // Resolve with the stored object for caller convenience
      request.onsuccess = () => resolve(data);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Generic method to get data from a store
   */
  async get(storeName, key) {
    await this.initialize();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.get(key);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Generic method to get all data from a store
   */
  async getAll(storeName, indexName = null, query = null) {
    await this.initialize();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      
      let request;
      if (indexName) {
        const index = store.index(indexName);
        request = query ? index.getAll(query) : index.getAll();
      } else {
        request = store.getAll();
      }

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Generic method to delete data from a store
   */
  async delete(storeName, key) {
    await this.initialize();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.delete(key);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // User Management
  async saveUser(user) {
    return this.put('users', {
      id: user.id || this.generateId(),
      username: user.username,
      displayName: user.displayName || user.username,
      avatar: user.avatar || null,
      publicKey: user.publicKey || null,
      createdAt: user.createdAt || new Date().toISOString(),
      lastSeen: new Date().toISOString(),
      ...user
    });
  }

  async getUser(userId) {
    return this.get('users', userId);
  }

  async getUserByUsername(username) {
    const users = await this.getAll('users');
    return users.find(user => user.username === username) || null;
  }

  async getCurrentUser() {
    const currentUserId = await this.getSetting('currentUserId');
    return currentUserId ? this.getUser(currentUserId) : null;
  }

  async setCurrentUser(userId) {
    return this.setSetting('currentUserId', userId);
  }

  // Chatroom Management
  async saveChatroom(chatroom) {
    // Ensure a stable ID across peers by using the secret code as the ID
    const secret = chatroom.secretCode || this.generateSecretCode();
    const id = chatroom.id || secret;
    const record = {
      id,
      name: chatroom.name,
      description: chatroom.description || '',
      secretCode: secret,
      createdBy: chatroom.createdBy,
      createdAt: chatroom.createdAt || new Date().toISOString(),
      isPrivate: chatroom.isPrivate !== false, // default to private
      maxMembers: chatroom.maxMembers || 50,
      encryptionEnabled: chatroom.encryptionEnabled !== false, // default to enabled
      ...chatroom,
      id, // enforce stable id after spread
      secretCode: secret
    };
    return this.put('chatrooms', record);
  }

  async getChatroom(chatroomId) {
    return this.get('chatrooms', chatroomId);
  }

  async getChatroomBySecretCode(secretCode) {
    const chatrooms = await this.getAll('chatrooms', 'secretCode', secretCode);
    return chatrooms.length > 0 ? chatrooms[0] : null;
  }

  async getAllChatrooms() {
    return this.getAll('chatrooms', 'createdAt');
  }

  async deleteChatroom(chatroomId) {
    // Delete chatroom and all related data
    await this.delete('chatrooms', chatroomId);
    
    // Delete all messages in this chatroom
    const messages = await this.getAll('messages', 'chatroomId', chatroomId);
    for (const message of messages) {
      await this.delete('messages', message.id);
    }

    // Delete all peers in this chatroom
    const peers = await this.getAll('peers', 'chatroomId', chatroomId);
    for (const peer of peers) {
      await this.delete('peers', peer.id);
    }

    // Delete encryption keys for this chatroom
    const keys = await this.getAll('encryptionKeys', 'chatroomId', chatroomId);
    for (const key of keys) {
      await this.delete('encryptionKeys', key.id);
    }
  }

  // Message Management
  async saveMessage(message) {
    return this.put('messages', {
      id: message.id || this.generateId(),
      chatroomId: message.chatroomId,
      userId: message.userId,
      username: message.username,
      content: message.content, // This will be encrypted
      messageType: message.messageType || 'text',
      timestamp: message.timestamp || new Date().toISOString(),
      isEncrypted: message.isEncrypted || false,
      replyTo: message.replyTo || null,
      editedAt: message.editedAt || null,
      ...message
    });
  }

  async getMessages(chatroomId, limit = 100, offset = 0) {
    await this.initialize();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['messages'], 'readonly');
      const store = transaction.objectStore('messages');
      const index = store.index('chatroomTimestamp');
      
      const range = IDBKeyRange.bound([chatroomId, ''], [chatroomId, '\uffff']);
      const request = index.openCursor(range, 'prev'); // Get newest first
      
      const messages = [];
      let count = 0;
      let skipped = 0;

      request.onsuccess = (event) => {
        const cursor = event.target.result;
        
        if (cursor && count < limit) {
          if (skipped >= offset) {
            messages.push(cursor.value);
            count++;
          } else {
            skipped++;
          }
          cursor.continue();
        } else {
          resolve(messages.reverse()); // Return in chronological order
        }
      };

      request.onerror = () => reject(request.error);
    });
  }

  async deleteMessage(messageId) {
    return this.delete('messages', messageId);
  }

  // Peer Management
  async savePeer(peer) {
    return this.put('peers', {
      id: peer.id || this.generateId(),
      userId: peer.userId,
      username: peer.username,
      chatroomId: peer.chatroomId,
      peerId: peer.peerId, // WebRTC peer ID
      publicKey: peer.publicKey || null,
      isOnline: peer.isOnline || false,
      lastSeen: peer.lastSeen || new Date().toISOString(),
      connectionId: peer.connectionId || null,
      ...peer
    });
  }

  async getPeers(chatroomId) {
    return this.getAll('peers', 'chatroomId', chatroomId);
  }

  async deletePeer(peerId) {
    return this.delete('peers', peerId);
  }

  async updatePeerStatus(peerId, isOnline) {
    const peer = await this.get('peers', peerId);
    if (peer) {
      peer.isOnline = isOnline;
      peer.lastSeen = new Date().toISOString();
      return this.put('peers', peer);
    }
  }

  // Encryption Key Management
  async saveEncryptionKey(keyData) {
    return this.put('encryptionKeys', {
      id: keyData.id || this.generateId(),
      chatroomId: keyData.chatroomId,
      keyType: keyData.keyType, // 'symmetric', 'public', 'private'
      keyData: keyData.keyData,
      createdAt: keyData.createdAt || new Date().toISOString(),
      ...keyData
    });
  }

  async getEncryptionKeys(chatroomId) {
    return this.getAll('encryptionKeys', 'chatroomId', chatroomId);
  }

  // Settings Management
  async setSetting(key, value) {
    return this.put('settings', { key, value });
  }

  async getSetting(key) {
    const setting = await this.get('settings', key);
    return setting ? setting.value : null;
  }

  async getAllSettings() {
    const settings = await this.getAll('settings');
    const result = {};
    settings.forEach(setting => {
      result[setting.key] = setting.value;
    });
    return result;
  }

  // Utility Methods
  generateId() {
    return crypto.randomUUID ? crypto.randomUUID() : this.fallbackGenerateId();
  }

  fallbackGenerateId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  generateSecretCode() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < 8; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  // Database Management
  async clearAllData() {
    await this.initialize();
    
    const storeNames = ['users', 'chatrooms', 'messages', 'peers', 'encryptionKeys', 'settings'];
    
    for (const storeName of storeNames) {
      await new Promise((resolve, reject) => {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.clear();

        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });
    }
    
    console.log('All local data cleared');
  }

  async exportData() {
    await this.initialize();
    
    const data = {};
    const storeNames = ['users', 'chatrooms', 'messages', 'peers', 'encryptionKeys', 'settings'];
    
    for (const storeName of storeNames) {
      data[storeName] = await this.getAll(storeName);
    }
    
    return data;
  }

  async importData(data) {
    await this.initialize();
    
    for (const [storeName, items] of Object.entries(data)) {
      if (Array.isArray(items)) {
        for (const item of items) {
          await this.put(storeName, item);
        }
      }
    }
    
    console.log('Data imported successfully');
  }

  // Search functionality
  async searchMessages(chatroomId, query, limit = 50) {
    const messages = await this.getAll('messages', 'chatroomId', chatroomId);
    const searchTerm = query.toLowerCase();
    
    return messages
      .filter(message => {
        // Note: This only works for unencrypted content or after decryption
        if (typeof message.content === 'string') {
          return message.content.toLowerCase().includes(searchTerm);
        }
        return false;
      })
      .slice(0, limit);
  }

  // Statistics
  async getStats() {
    const stats = {
      users: 0,
      chatrooms: 0,
      messages: 0,
      peers: 0,
      totalSize: 0
    };

    const storeNames = ['users', 'chatrooms', 'messages', 'peers', 'encryptionKeys', 'settings'];
    
    for (const storeName of storeNames) {
      const items = await this.getAll(storeName);
      stats[storeName] = items.length;
      
      // Rough size calculation
      stats.totalSize += JSON.stringify(items).length;
    }

    return stats;
  }
}

// Create singleton instance
const storageService = new StorageService();

export default storageService;
