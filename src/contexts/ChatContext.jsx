import React, { createContext, useContext, useState, useEffect } from 'react'
import { useAuth } from './AuthContext'

const ChatContext = createContext()

export const useChat = () => {
  const context = useContext(ChatContext)
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider')
  }
  return context
}

export const ChatProvider = ({ children }) => {
  const { user } = useAuth()
  const [messages, setMessages] = useState([])
  const [chatrooms, setChatrooms] = useState([])
  const [currentChatroom, setCurrentChatroom] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // WebSocket connection
  const [ws, setWs] = useState(null)

  useEffect(() => {
    if (user) {
      // Initialize WebSocket connection
      const websocket = new WebSocket(`ws://localhost:8000/ws/${user.id}`)
      
      websocket.onopen = () => {
        console.log('WebSocket connected')
        setWs(websocket)
      }

      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        handleIncomingMessage(data)
      }

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error)
        setError('Connection error')
      }

      websocket.onclose = () => {
        console.log('WebSocket disconnected')
        setWs(null)
      }

      return () => {
        websocket.close()
      }
    }
  }, [user])

  const handleIncomingMessage = (data) => {
    if (data.type === 'message') {
      setMessages(prev => [...prev, data.message])
    } else if (data.type === 'chatroom_update') {
      setChatrooms(prev => 
        prev.map(room => 
          room.id === data.chatroom.id ? data.chatroom : room
        )
      )
    }
  }

  const sendMessage = async (content, chatroomId) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      setError('WebSocket not connected')
      return
    }

    const message = {
      type: 'message',
      content,
      chatroom_id: chatroomId,
      user_id: user.id
    }

    ws.send(JSON.stringify(message))
  }

  const createChatroom = async (name, description = '') => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/chatrooms/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({ name, description })
      })

      if (!response.ok) {
        throw new Error('Failed to create chatroom')
      }

      const chatroom = await response.json()
      setChatrooms(prev => [...prev, chatroom])
      return chatroom
    } catch (error) {
      setError(error.message)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const joinChatroom = async (chatroomId) => {
    try {
      setLoading(true)
      const response = await fetch(`http://localhost:8000/api/chatrooms/${chatroomId}/join/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to join chatroom')
      }

      // Update chatrooms list
      const updatedChatroom = await response.json()
      setChatrooms(prev => 
        prev.map(room => 
          room.id === chatroomId ? updatedChatroom : room
        )
      )

      return updatedChatroom
    } catch (error) {
      setError(error.message)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const loadMessages = async (chatroomId) => {
    try {
      setLoading(true)
      const response = await fetch(`http://localhost:8000/api/chatrooms/${chatroomId}/messages/`, {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to load messages')
      }

      const messages = await response.json()
      setMessages(messages)
      setCurrentChatroom(chatroomId)
    } catch (error) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  const loadChatrooms = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/chatrooms/', {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to load chatrooms')
      }

      const chatrooms = await response.json()
      setChatrooms(chatrooms)
    } catch (error) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  const value = {
    messages,
    chatrooms,
    currentChatroom,
    loading,
    error,
    sendMessage,
    createChatroom,
    joinChatroom,
    loadMessages,
    loadChatrooms,
    setCurrentChatroom
  }

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  )
}