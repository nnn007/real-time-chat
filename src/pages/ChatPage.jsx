import { useState, useEffect } from 'react'
import { Routes, Route, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useChat } from '../contexts/ChatContext'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  MessageCircle, 
  Plus, 
  Settings, 
  LogOut, 
  Users, 
  Hash,
  Lock,
  Shield,
  Search,
  MoreVertical
} from 'lucide-react'

// Placeholder components for different chat views
function ChatroomList() {
  const { chatrooms, loadChatrooms, setCurrentChatroom } = useChat()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      try {
        await loadChatrooms()
      } catch (error) {
        console.error('Failed to load chatrooms:', error)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [loadChatrooms])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Your Chatrooms</h2>
        <Button size="sm">
          <Plus className="h-4 w-4 mr-2" />
          New Chat
        </Button>
      </div>

      {chatrooms.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <MessageCircle className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No chatrooms yet</h3>
            <p className="text-muted-foreground text-center mb-4">
              Create your first chatroom or join one with an invitation link
            </p>
            <div className="flex space-x-2">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Chatroom
              </Button>
              <Button variant="outline">Join with Link</Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {chatrooms.map((chatroom) => (
            <Card key={chatroom.id} className="cursor-pointer hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="bg-primary/10 p-2 rounded-full">
                      {chatroom.is_private ? (
                        <Lock className="h-4 w-4 text-primary" />
                      ) : (
                        <Hash className="h-4 w-4 text-primary" />
                      )}
                    </div>
                    <div>
                      <h3 className="font-medium">{chatroom.name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {chatroom.description || 'No description'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="secondary">
                      <Users className="h-3 w-3 mr-1" />
                      {chatroom.member_count || 0}
                    </Badge>
                    {chatroom.encryption_enabled && (
                      <Shield className="h-4 w-4 text-green-500" />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

function WelcomeView() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center">
      <div className="bg-primary/10 p-6 rounded-full mb-6">
        <MessageCircle className="h-16 w-16 text-primary" />
      </div>
      <h1 className="text-3xl font-bold mb-4">Welcome to RealTime Chat</h1>
      <p className="text-muted-foreground max-w-md mb-8">
        Secure, end-to-end encrypted messaging with real-time features. 
        Create a chatroom or join one to get started.
      </p>
      <div className="flex space-x-4">
        <Button size="lg">
          <Plus className="h-5 w-5 mr-2" />
          Create Chatroom
        </Button>
        <Button variant="outline" size="lg">
          Join with Invite
        </Button>
      </div>
    </div>
  )
}

export default function ChatPage() {
  const { user, logout } = useAuth()
  const { connected } = useChat()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-80' : 'w-16'} bg-card border-r transition-all duration-300 flex flex-col`}>
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            {sidebarOpen && (
              <div className="flex items-center space-x-2">
                <div className="bg-primary rounded-full p-2">
                  <MessageCircle className="h-5 w-5 text-primary-foreground" />
                </div>
                <span className="font-semibold">RealTime Chat</span>
              </div>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* User Profile */}
        {sidebarOpen && (
          <div className="p-4 border-b">
            <div className="flex items-center space-x-3">
              <Avatar>
                <AvatarImage src={user?.avatar_url} />
                <AvatarFallback>
                  {user?.display_name?.charAt(0)?.toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{user?.display_name}</p>
                <p className="text-sm text-muted-foreground truncate">
                  @{user?.username}
                </p>
              </div>
              <div className="flex items-center space-x-1">
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-xs text-muted-foreground">
                  {connected ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        {sidebarOpen && (
          <div className="flex-1 p-4">
            <ScrollArea className="h-full">
              <ChatroomList />
            </ScrollArea>
          </div>
        )}

        {/* Footer */}
        {sidebarOpen && (
          <div className="p-4 border-t">
            <div className="flex space-x-2">
              <Button variant="outline" size="sm" className="flex-1">
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="h-16 border-b bg-card flex items-center justify-between px-6">
          <div className="flex items-center space-x-4">
            <h1 className="text-lg font-semibold">Chat</h1>
            {connected && (
              <Badge variant="outline" className="text-green-600 border-green-600">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2" />
                Connected
              </Badge>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm">
              <Search className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Chat Content */}
        <div className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<WelcomeView />} />
            <Route path="/room/:roomId" element={<div>Chat Room View - Coming Soon</div>} />
            <Route path="/settings" element={<div>Settings - Coming Soon</div>} />
          </Routes>
        </div>
      </div>
    </div>
  )
}

