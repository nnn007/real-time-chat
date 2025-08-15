import React, { useState, useEffect, useRef } from 'react';
import { useP2PChat } from '../contexts/P2PChatContext';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';
import { Separator } from '../components/ui/separator';
import { 
  MessageCircle, 
  Plus, 
  Users, 
  Lock, 
  Copy, 
  Send, 
  Settings,
  Download,
  Upload,
  Trash2,
  Wifi,
  WifiOff,
  Shield,
  Key
} from 'lucide-react';

const P2PChatPage = () => {
  const { user, logout } = useAuth();
  const {
    messages,
    chatrooms,
    currentChatroom,
    connectedPeers,
    loading,
    error,
    typingUsers,
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
    clearError
  } = useP2PChat();

  const [newMessage, setNewMessage] = useState('');
  const [showCreateRoom, setShowCreateRoom] = useState(false);
  const [showJoinRoom, setShowJoinRoom] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [roomName, setRoomName] = useState('');
  const [roomDescription, setRoomDescription] = useState('');
  const [joinCode, setJoinCode] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const fileInputRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle typing indicator
  useEffect(() => {
    if (isTyping) {
      sendTypingIndicator(true);
      
      // Clear existing timeout
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      
      // Set new timeout to stop typing indicator
      typingTimeoutRef.current = setTimeout(() => {
        setIsTyping(false);
        sendTypingIndicator(false);
      }, 2000);
    }

    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, [isTyping, sendTypingIndicator]);

  const handleCreateRoom = async () => {
    if (!roomName.trim()) return;

    try {
      const room = await createChatroom(roomName.trim(), roomDescription.trim());
      setShowCreateRoom(false);
      setRoomName('');
      setRoomDescription('');
      await selectChatroom(room);
    } catch (error) {
      console.error('Failed to create room:', error);
    }
  };

  const handleJoinRoom = async () => {
    if (!joinCode.trim()) return;

    try {
      const room = await joinChatroomByCode(joinCode.trim().toUpperCase());
      setShowJoinRoom(false);
      setJoinCode('');
      await selectChatroom(room);
      
      // Show success message
      console.log(`Successfully joined room: ${room.name}`);
    } catch (error) {
      console.error('Failed to join room:', error);
      // Error is already set in the context
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !currentChatroom) return;

    try {
      await sendMessage(newMessage.trim());
      setNewMessage('');
      setIsTyping(false);
      sendTypingIndicator(false);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    } else if (!isTyping && newMessage.trim()) {
      setIsTyping(true);
    }
  };

  const handleMessageChange = (e) => {
    setNewMessage(e.target.value);
    if (!isTyping && e.target.value.trim()) {
      setIsTyping(true);
    }
  };

  const copyRoomCode = (code) => {
    navigator.clipboard.writeText(code);
    // You could show a toast notification here
  };

  const handleFileImport = (e) => {
    const file = e.target.files[0];
    if (file) {
      importChatData(file);
    }
  };

  const handleDeleteRoom = async (roomId) => {
    if (confirm('Are you sure you want to delete this chatroom? This will remove all messages.')) {
      await deleteChatroom(roomId);
    }
  };

  const connectionStatus = getConnectionStatus();

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">P2P Chat</h1>
            <div className="flex items-center space-x-2">
              <div className="flex items-center">
                {connectionStatus.p2pStatus.connectedPeers > 0 ? (
                  <Wifi className="w-4 h-4 text-green-500" />
                ) : (
                  <WifiOff className="w-4 h-4 text-gray-400" />
                )}
                <span className="ml-1 text-sm text-gray-600 dark:text-gray-300">
                  {connectionStatus.p2pStatus.connectedPeers}
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSettings(true)}
              >
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
          
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowCreateRoom(true)}
              className="flex-1"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowJoinRoom(true)}
              className="flex-1"
            >
              <MessageCircle className="w-4 h-4 mr-2" />
              Join
            </Button>
          </div>
        </div>

        {/* User Info */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">{user?.username}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">{user?.email}</p>
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => {
                if (confirm('Are you sure you want to logout? This will disconnect you from all chatrooms.')) {
                  logout();
                }
              }}
            >
              Logout
            </Button>
          </div>
        </div>

        {/* Chatrooms List */}
        <ScrollArea className="flex-1">
          <div className="p-4">
            <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
              Chatrooms ({chatrooms.length})
            </h2>
            
            {chatrooms.length === 0 ? (
              <div className="text-center py-8">
                <MessageCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  No chatrooms yet. Create or join one to get started!
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {chatrooms.map((room) => (
                  <Card
                    key={room.id}
                    className={`cursor-pointer transition-colors ${
                      currentChatroom?.id === room.id
                        ? 'bg-blue-50 border-blue-200 dark:bg-blue-900/20'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                    onClick={() => selectChatroom(room)}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className="font-medium text-sm text-gray-900 dark:text-white truncate">
                          {room.name}
                        </h3>
                        <div className="flex items-center space-x-1">
                          {room.encryptionEnabled && (
                            <Shield className="w-3 h-3 text-green-500" />
                          )}
                          {room.isPrivate && (
                            <Lock className="w-3 h-3 text-gray-400" />
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          Code: {room.secretCode}
                        </p>
                        <div className="flex items-center space-x-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              copyRoomCode(room.secretCode);
                            }}
                            className="h-6 w-6 p-0"
                          >
                            <Copy className="w-3 h-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteRoom(room.id);
                            }}
                            className="h-6 w-6 p-0 text-red-500 hover:text-red-700"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentChatroom ? (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {currentChatroom.name}
                  </h2>
                  <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                    <span className="flex items-center">
                      <Users className="w-4 h-4 mr-1" />
                      {connectedPeers.length} members
                    </span>
                    <span className="flex items-center">
                      <Key className="w-4 h-4 mr-1" />
                      {currentChatroom.secretCode}
                    </span>
                    {currentChatroom.encryptionEnabled && (
                      <Badge variant="secondary" className="text-xs">
                        <Shield className="w-3 h-3 mr-1" />
                        Encrypted
                      </Badge>
                    )}
                  </div>
                  
                  {/* Show connected users */}
                  {connectedPeers.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Members:</p>
                      <div className="flex flex-wrap gap-1">
                        {connectedPeers.map((peer) => (
                          <Badge 
                            key={peer.id} 
                            variant="outline" 
                            className="text-xs"
                          >
                            {peer.username}
                            {peer.userId === user?.id && ' (You)'}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyRoomCode(currentChatroom.secretCode)}
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Copy Code
                </Button>
              </div>
            </div>

            {/* Messages Area */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.length === 0 ? (
                  <div className="text-center py-12">
                    <MessageCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      No messages yet
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400">
                      Start the conversation by sending a message!
                    </p>
                  </div>
                ) : (
                  messages.map((message, index) => (
                    <div
                      key={message.id || index}
                      className={`flex ${
                        message.userId === user?.id ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          message.userId === user?.id
                            ? 'bg-blue-500 text-white'
                            : 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white border'
                        }`}
                      >
                        {message.userId !== user?.id && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                            {message.username}
                          </p>
                        )}
                        <p className="text-sm">{message.content}</p>
                        <p className={`text-xs mt-1 ${
                          message.userId === user?.id
                            ? 'text-blue-100'
                            : 'text-gray-500 dark:text-gray-400'
                        }`}>
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))
                )}
                
                {/* Typing Indicators */}
                {typingUsers.length > 0 && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 dark:bg-gray-700 px-4 py-2 rounded-lg">
                      <p className="text-sm text-gray-600 dark:text-gray-300">
                        {typingUsers.map(user => user.username).join(', ')} 
                        {typingUsers.length === 1 ? ' is' : ' are'} typing...
                      </p>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Message Input */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <div className="flex items-center space-x-2">
                <Input
                  value={newMessage}
                  onChange={handleMessageChange}
                  onKeyPress={handleKeyPress}
                  placeholder="Type a message..."
                  className="flex-1"
                  disabled={loading}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={!newMessage.trim() || loading}
                  size="sm"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageCircle className="w-24 h-24 text-gray-300 mx-auto mb-6" />
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                Welcome to P2P Chat
              </h2>
              <p className="text-gray-500 dark:text-gray-400 mb-6">
                Select a chatroom or create a new one to start chatting
              </p>
              <div className="space-x-4">
                <Button onClick={() => setShowCreateRoom(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Chatroom
                </Button>
                <Button variant="outline" onClick={() => setShowJoinRoom(true)}>
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Join Chatroom
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create Room Modal */}
      {showCreateRoom && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4">
            <CardHeader>
              <CardTitle>Create Chatroom</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Room Name *
                </label>
                <Input
                  value={roomName}
                  onChange={(e) => setRoomName(e.target.value)}
                  placeholder="Enter room name"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description (optional)
                </label>
                <Input
                  value={roomDescription}
                  onChange={(e) => setRoomDescription(e.target.value)}
                  placeholder="Enter room description"
                />
              </div>
              
              <div className="flex space-x-2">
                <Button
                  onClick={() => setShowCreateRoom(false)}
                  variant="outline"
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateRoom}
                  disabled={!roomName.trim() || loading}
                  className="flex-1"
                >
                  {loading ? 'Creating...' : 'Create'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Join Room Modal */}
      {showJoinRoom && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4">
            <CardHeader>
              <CardTitle>Join Chatroom</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Room Code *
                </label>
                <Input
                  value={joinCode}
                  onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                  placeholder="Enter 8-character room code"
                  maxLength={8}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Enter any 8-character code to create/join a room
                </p>
              </div>
              
              <div className="flex space-x-2">
                <Button
                  onClick={() => setShowJoinRoom(false)}
                  variant="outline"
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleJoinRoom}
                  disabled={!joinCode.trim() || loading}
                  className="flex-1"
                >
                  {loading ? 'Joining...' : 'Join'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4">
            <CardHeader>
              <CardTitle>Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <h3 className="font-medium text-gray-900 dark:text-white">Data Management</h3>
                <div className="flex space-x-2">
                  <Button
                    onClick={exportChatData}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Export
                  </Button>
                  <Button
                    onClick={() => fileInputRef.current?.click()}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Import
                  </Button>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <h3 className="font-medium text-gray-900 dark:text-white">Connection Status</h3>
                <div className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
                  <div>Status: {connectionStatus.status}</div>
                  <div>Connected Peers: {connectionStatus.p2pStatus.connectedPeers}</div>
                  <div>Encryption: {connectionStatus.encryptionSupported ? 'Supported' : 'Not Supported'}</div>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Button
                  onClick={() => {
                    if (confirm('This will delete all local data. Are you sure?')) {
                      clearAllData();
                    }
                  }}
                  variant="destructive"
                  size="sm"
                  className="w-full"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Clear All Data
                </Button>
              </div>

              <div className="flex justify-end">
                <Button
                  onClick={() => setShowSettings(false)}
                  variant="outline"
                >
                  Close
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Hidden file input for import */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleFileImport}
        className="hidden"
      />

      {/* Error Display */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm">{error}</span>
            <Button
              onClick={clearError}
              variant="ghost"
              size="sm"
              className="text-white hover:bg-red-600 ml-2"
            >
              ×
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default P2PChatPage;
