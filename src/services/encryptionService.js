/**
 * Encryption Service
 * Handles end-to-end encryption using Web Crypto API
 */

class EncryptionService {
  constructor() {
    this.keyPairs = new Map(); // Store key pairs for each chatroom
    this.sharedKeys = new Map(); // Store shared keys for each chatroom
    this.publicKeys = new Map(); // Store public keys of other users
    this.isSupported = this.checkWebCryptoSupport();
  }

  /**
   * Check if Web Crypto API is supported
   * @returns {boolean} Whether Web Crypto API is supported
   */
  checkWebCryptoSupport() {
    return typeof window !== 'undefined' && 
           window.crypto && 
           window.crypto.subtle &&
           typeof window.crypto.subtle.generateKey === 'function';
  }

  /**
   * Generate a new key pair for a chatroom
   * @param {string} chatroomId - Chatroom ID
   * @returns {Promise<CryptoKeyPair>} Generated key pair
   */
  async generateKeyPair(chatroomId) {
    if (!this.isSupported) {
      throw new Error('Web Crypto API is not supported in this browser');
    }

    try {
      const keyPair = await window.crypto.subtle.generateKey(
        {
          name: 'ECDH',
          namedCurve: 'P-256'
        },
        true, // extractable
        ['deriveKey', 'deriveBits']
      );

      this.keyPairs.set(chatroomId, keyPair);
      
      console.log(`Generated key pair for chatroom: ${chatroomId}`);
      return keyPair;
    } catch (error) {
      console.error('Failed to generate key pair:', error);
      throw error;
    }
  }

  /**
   * Export public key for sharing
   * @param {string} chatroomId - Chatroom ID
   * @returns {Promise<ArrayBuffer>} Exported public key
   */
  async exportPublicKey(chatroomId) {
    const keyPair = this.keyPairs.get(chatroomId);
    if (!keyPair) {
      throw new Error(`No key pair found for chatroom: ${chatroomId}`);
    }

    try {
      const exportedKey = await window.crypto.subtle.exportKey(
        'raw',
        keyPair.publicKey
      );
      
      return exportedKey;
    } catch (error) {
      console.error('Failed to export public key:', error);
      throw error;
    }
  }

  /**
   * Import a public key from another user
   * @param {string} userId - User ID
   * @param {ArrayBuffer} publicKeyData - Public key data
   * @returns {Promise<CryptoKey>} Imported public key
   */
  async importPublicKey(userId, publicKeyData) {
    try {
      const publicKey = await window.crypto.subtle.importKey(
        'raw',
        publicKeyData,
        {
          name: 'ECDH',
          namedCurve: 'P-256'
        },
        false, // not extractable
        []
      );

      this.publicKeys.set(userId, publicKey);
      
      console.log(`Imported public key for user: ${userId}`);
      return publicKey;
    } catch (error) {
      console.error('Failed to import public key:', error);
      throw error;
    }
  }

  /**
   * Derive shared key for encryption/decryption
   * @param {string} chatroomId - Chatroom ID
   * @param {string} otherUserId - Other user's ID
   * @returns {Promise<CryptoKey>} Derived shared key
   */
  async deriveSharedKey(chatroomId, otherUserId) {
    const keyPair = this.keyPairs.get(chatroomId);
    const otherPublicKey = this.publicKeys.get(otherUserId);

    if (!keyPair) {
      throw new Error(`No key pair found for chatroom: ${chatroomId}`);
    }

    if (!otherPublicKey) {
      throw new Error(`No public key found for user: ${otherUserId}`);
    }

    try {
      const sharedKey = await window.crypto.subtle.deriveKey(
        {
          name: 'ECDH',
          public: otherPublicKey
        },
        keyPair.privateKey,
        {
          name: 'AES-GCM',
          length: 256
        },
        false, // not extractable
        ['encrypt', 'decrypt']
      );

      const keyId = `${chatroomId}:${otherUserId}`;
      this.sharedKeys.set(keyId, sharedKey);
      
      console.log(`Derived shared key for chatroom: ${chatroomId}, user: ${otherUserId}`);
      return sharedKey;
    } catch (error) {
      console.error('Failed to derive shared key:', error);
      throw error;
    }
  }

  /**
   * Generate a symmetric key for group encryption
   * @param {string} chatroomId - Chatroom ID
   * @returns {Promise<CryptoKey>} Generated symmetric key
   */
  async generateSymmetricKey(chatroomId) {
    try {
      const key = await window.crypto.subtle.generateKey(
        {
          name: 'AES-GCM',
          length: 256
        },
        true, // extractable for sharing
        ['encrypt', 'decrypt']
      );

      this.sharedKeys.set(chatroomId, key);
      
      console.log(`Generated symmetric key for chatroom: ${chatroomId}`);
      return key;
    } catch (error) {
      console.error('Failed to generate symmetric key:', error);
      throw error;
    }
  }

  /**
   * Export symmetric key for sharing with other users
   * @param {string} chatroomId - Chatroom ID
   * @returns {Promise<ArrayBuffer>} Exported key data
   */
  async exportSymmetricKey(chatroomId) {
    const key = this.sharedKeys.get(chatroomId);
    if (!key) {
      throw new Error(`No symmetric key found for chatroom: ${chatroomId}`);
    }

    try {
      const exportedKey = await window.crypto.subtle.exportKey('raw', key);
      return exportedKey;
    } catch (error) {
      console.error('Failed to export symmetric key:', error);
      throw error;
    }
  }

  /**
   * Import symmetric key from key data
   * @param {string} chatroomId - Chatroom ID
   * @param {ArrayBuffer} keyData - Key data
   * @returns {Promise<CryptoKey>} Imported symmetric key
   */
  async importSymmetricKey(chatroomId, keyData) {
    try {
      const key = await window.crypto.subtle.importKey(
        'raw',
        keyData,
        {
          name: 'AES-GCM',
          length: 256
        },
        false, // not extractable
        ['encrypt', 'decrypt']
      );

      this.sharedKeys.set(chatroomId, key);
      
      console.log(`Imported symmetric key for chatroom: ${chatroomId}`);
      return key;
    } catch (error) {
      console.error('Failed to import symmetric key:', error);
      throw error;
    }
  }

  /**
   * Encrypt a message
   * @param {string} chatroomId - Chatroom ID
   * @param {string} message - Message to encrypt
   * @returns {Promise<Object>} Encrypted message data
   */
  async encryptMessage(chatroomId, message) {
    const key = this.sharedKeys.get(chatroomId);
    if (!key) {
      throw new Error(`No encryption key found for chatroom: ${chatroomId}`);
    }

    try {
      // Generate random IV
      const iv = window.crypto.getRandomValues(new Uint8Array(12));
      
      // Convert message to ArrayBuffer
      const messageBuffer = new TextEncoder().encode(message);
      
      // Encrypt the message
      const encryptedBuffer = await window.crypto.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        key,
        messageBuffer
      );

      // Convert to base64 for transmission
      const encryptedData = this.arrayBufferToBase64(encryptedBuffer);
      const ivData = this.arrayBufferToBase64(iv.buffer);

      return {
        encryptedData,
        iv: ivData,
        algorithm: 'AES-GCM'
      };
    } catch (error) {
      console.error('Failed to encrypt message:', error);
      throw error;
    }
  }

  /**
   * Decrypt a message
   * @param {string} chatroomId - Chatroom ID
   * @param {Object} encryptedMessage - Encrypted message data
   * @returns {Promise<string>} Decrypted message
   */
  async decryptMessage(chatroomId, encryptedMessage) {
    const key = this.sharedKeys.get(chatroomId);
    if (!key) {
      throw new Error(`No decryption key found for chatroom: ${chatroomId}`);
    }

    try {
      // Convert from base64
      const encryptedBuffer = this.base64ToArrayBuffer(encryptedMessage.encryptedData);
      const iv = this.base64ToArrayBuffer(encryptedMessage.iv);

      // Decrypt the message
      const decryptedBuffer = await window.crypto.subtle.decrypt(
        {
          name: 'AES-GCM',
          iv: new Uint8Array(iv)
        },
        key,
        encryptedBuffer
      );

      // Convert back to string
      const decryptedMessage = new TextDecoder().decode(decryptedBuffer);
      
      return decryptedMessage;
    } catch (error) {
      console.error('Failed to decrypt message:', error);
      throw error;
    }
  }

  /**
   * Generate key fingerprint for verification
   * @param {string} chatroomId - Chatroom ID
   * @returns {Promise<string>} Key fingerprint
   */
  async generateKeyFingerprint(chatroomId) {
    try {
      const publicKeyData = await this.exportPublicKey(chatroomId);
      const hashBuffer = await window.crypto.subtle.digest('SHA-256', publicKeyData);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
      
      // Return first 16 characters as fingerprint
      return hashHex.substring(0, 16).toUpperCase();
    } catch (error) {
      console.error('Failed to generate key fingerprint:', error);
      throw error;
    }
  }

  /**
   * Clear all keys for a chatroom
   * @param {string} chatroomId - Chatroom ID
   */
  clearChatroomKeys(chatroomId) {
    this.keyPairs.delete(chatroomId);
    this.sharedKeys.delete(chatroomId);
    
    // Clear shared keys with specific users
    for (const [keyId] of this.sharedKeys) {
      if (keyId.startsWith(`${chatroomId}:`)) {
        this.sharedKeys.delete(keyId);
      }
    }
    
    console.log(`Cleared keys for chatroom: ${chatroomId}`);
  }

  /**
   * Clear all keys
   */
  clearAllKeys() {
    this.keyPairs.clear();
    this.sharedKeys.clear();
    this.publicKeys.clear();
    
    console.log('Cleared all encryption keys');
  }

  /**
   * Get encryption status for a chatroom
   * @param {string} chatroomId - Chatroom ID
   * @returns {Object} Encryption status
   */
  getEncryptionStatus(chatroomId) {
    return {
      isSupported: this.isSupported,
      hasKeyPair: this.keyPairs.has(chatroomId),
      hasSharedKey: this.sharedKeys.has(chatroomId),
      isEnabled: this.isSupported && (this.keyPairs.has(chatroomId) || this.sharedKeys.has(chatroomId))
    };
  }

  /**
   * Convert ArrayBuffer to base64 string
   * @param {ArrayBuffer} buffer - ArrayBuffer to convert
   * @returns {string} Base64 string
   */
  arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  /**
   * Convert base64 string to ArrayBuffer
   * @param {string} base64 - Base64 string
   * @returns {ArrayBuffer} ArrayBuffer
   */
  base64ToArrayBuffer(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  /**
   * Generate secure random string for key derivation
   * @param {number} length - Length of random string
   * @returns {string} Random string
   */
  generateSecureRandom(length = 32) {
    const array = new Uint8Array(length);
    window.crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }
}

// Create singleton instance
const encryptionService = new EncryptionService();

export default encryptionService;

