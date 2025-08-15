# P2P Chat Application

A fully decentralized, peer-to-peer chat application with end-to-end encryption that runs entirely in your browser. No servers, no tracking, no data collection - your conversations stay between you and your contacts.

## 🚀 Features

### 🔒 **Complete Privacy**
- **End-to-End Encryption**: Messages are encrypted locally using Web Crypto API with AES-GCM
- **No Central Servers**: Direct peer-to-peer communication using WebRTC
- **Local Storage**: All data stored in your browser's IndexedDB - never leaves your device
- **No Registration**: Create accounts locally without any server involvement

### 💬 **Secret Room Codes**
- Create private chatrooms with unique 8-character codes
- Share codes with friends to invite them to your rooms
- Each room has its own encryption key derived from the secret code
- Perfect for private group conversations

### 🌐 **Peer-to-Peer Technology**
- Direct browser-to-browser communication using WebRTC
- No intermediary servers storing or processing your messages
- Works across different networks using STUN servers for NAT traversal
- Automatic peer discovery and connection management

### 🛡️ **Security Features**
- **AES-GCM Encryption**: Industry-standard authenticated encryption
- **Key Derivation**: Room keys derived from secret codes using PBKDF2
- **Forward Secrecy**: Each message uses a unique initialization vector
- **Local Key Storage**: Encryption keys never leave your device

## 🏃 Quick Start

### Prerequisites
- Modern web browser with WebRTC and IndexedDB support
- Node.js 16+ (for development)

### Installation

1. **Clone and install dependencies:**
   ```bash
   git clone <your-repo-url>
   cd Real-Time-Chat-App
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Open in browser:**
   Navigate to `http://localhost:5173`

### Production Build

```bash
npm run build
npm run preview
```

## 📱 How to Use

### Getting Started
1. **Create Account**: Choose any username and password (stored locally only)
2. **Create Room**: Click "Create" and give your room a name
3. **Share Code**: Copy the 8-character room code and share with friends
4. **Join Room**: Others can join using "Join" and entering the code

### Chatting
- Messages are automatically encrypted before sending
- Only people with the room code can decrypt and read messages
- Chat history is stored locally in your browser
- Export/import data for backup or transfer between devices

### Managing Data
- **Export Data**: Download all your chats as a JSON file
- **Import Data**: Restore from a previously exported file
- **Clear Data**: Delete all local data if needed

## 🔧 Technical Architecture

### Frontend Stack
- **React 18**: Modern UI with hooks and context
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Beautiful icons

### P2P Technologies
- **WebRTC**: Direct peer-to-peer communication
- **IndexedDB**: Browser-based persistent storage
- **Web Crypto API**: Native browser cryptography
- **LocalStorage**: Fallback and compatibility storage

### Encryption Implementation
- **Algorithm**: AES-GCM with 256-bit keys
- **Key Derivation**: PBKDF2 with 100,000 iterations
- **IV Generation**: Cryptographically secure random IVs
- **Salt**: Room ID used as salt for key derivation

## 🌍 Deployment Options

### Static Hosting
Since this is a pure client-side application, you can deploy it to any static hosting service:

- **Netlify**: Drag and drop the `dist` folder
- **Vercel**: Connect your Git repository
- **GitHub Pages**: Enable Pages in repository settings
- **Firebase Hosting**: Use Firebase CLI
- **Any Web Server**: Serve the `dist` folder

### Self-Hosting
```bash
npm run build
# Serve the 'dist' directory with any web server
python -m http.server 8000 -d dist  # Python
npx serve dist                       # Node.js
```

## 🔐 Security Considerations

### What's Secure
- ✅ Messages are encrypted end-to-end
- ✅ Keys never leave your device
- ✅ No central server can read your messages
- ✅ Room codes provide access control
- ✅ Data stored locally only

### Limitations
- ⚠️ Requires HTTPS for WebRTC in production
- ⚠️ Peers must be online simultaneously to exchange messages
- ⚠️ No message delivery guarantees when peers are offline
- ⚠️ Browser storage can be cleared (use export/import for backups)

## 🤝 How It Works

### Connection Process
1. User creates or joins a room with a secret code
2. Encryption key is derived from the secret code
3. WebRTC connection established with other room members
4. Messages encrypted locally and sent directly to peers
5. Recipients decrypt messages using the same room key

### Data Flow
```
Your Browser ←→ [WebRTC] ←→ Friend's Browser
     ↓                           ↓
[IndexedDB]                 [IndexedDB]
(Your Data)                (Their Data)
```

No servers involved in message storage or transmission!

## 📊 Browser Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| WebRTC | ✅ | ✅ | ✅ | ✅ |
| IndexedDB | ✅ | ✅ | ✅ | ✅ |
| Web Crypto | ✅ | ✅ | ✅ | ✅ |
| ES2020+ | ✅ | ✅ | ✅ | ✅ |

## 🛠️ Development

### Project Structure
```
src/
├── components/ui/     # Reusable UI components
├── contexts/          # React contexts for state management
├── pages/             # Main application pages
├── services/          # Core P2P and encryption services
└── utils/             # Utility functions
```

### Key Services
- `storageService.js`: IndexedDB wrapper for local data storage
- `p2pService.js`: WebRTC peer-to-peer communication
- `encryptionService.js`: End-to-end encryption using Web Crypto API

## 🐛 Troubleshooting

### Common Issues

**Can't connect to peers:**
- Ensure both users are online and in the same room
- Check browser console for WebRTC errors
- Try refreshing both browsers

**Messages not encrypting:**
- Verify Web Crypto API support in your browser
- Check that room codes match exactly
- Look for encryption errors in console

**Data not persisting:**
- Check if browser is in private/incognito mode
- Verify IndexedDB is enabled
- Ensure sufficient storage space

## 📄 License

MIT License - feel free to use this code for your own projects!

## 🚀 Future Enhancements

- File sharing support
- Voice/video calling
- Mobile app versions
- Improved peer discovery
- Message synchronization when offline
- Custom signaling servers

---

**Remember**: This is a decentralized application. Your data stays on your device, and you're in complete control of your privacy! 🔒✨
