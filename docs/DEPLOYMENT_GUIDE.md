# P2P Chat - Deployment Guide

This guide will help you deploy your P2P Chat application to various hosting platforms.

## 🚀 Quick Deployment Options

### 1. Netlify (Recommended)

**One-click deployment:**
1. Build the project: `npm run build`
2. Drag and drop the `dist` folder to [Netlify Drop](https://app.netlify.com/drop)
3. Your app is live instantly!

**Git-based deployment:**
1. Push your code to GitHub/GitLab
2. Connect your repository to Netlify
3. Set build command: `npm run build`
4. Set publish directory: `dist`
5. Deploy automatically on every push

### 2. Vercel

**GitHub integration:**
1. Push code to GitHub
2. Visit [vercel.com](https://vercel.com)
3. Import your repository
4. Vercel auto-detects Vite settings
5. Deploy with one click

**Manual deployment:**
```bash
npm install -g vercel
npm run build
vercel --prod
```

### 3. GitHub Pages

**Using GitHub Actions:**
1. Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'
        
    - name: Install dependencies
      run: npm ci
      
    - name: Build
      run: npm run build
      
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./dist
```

2. Enable GitHub Pages in repository settings
3. Select "gh-pages" branch as source

### 4. Firebase Hosting

```bash
npm install -g firebase-tools
npm run build
firebase login
firebase init hosting
# Select 'dist' as public directory
# Configure as single-page app: Yes
firebase deploy
```

### 5. Self-Hosting

**Simple HTTP Server:**
```bash
npm run build

# Python 3
python -m http.server 8000 -d dist

# Node.js
npx serve dist

# PHP
php -S localhost:8000 -t dist
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/your/dist;
    index index.html;
    
    # Handle client-side routing
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

## 🔐 HTTPS Requirements

**Important:** WebRTC requires HTTPS in production. All recommended hosting platforms provide free SSL certificates.

For self-hosting, you can use:
- [Let's Encrypt](https://letsencrypt.org/) for free SSL certificates
- [Cloudflare](https://www.cloudflare.com/) for free SSL proxy

## 🌐 Custom Domain

Most platforms support custom domains:

1. **Add CNAME record** pointing to your hosting platform
2. **Configure domain** in your hosting platform's dashboard
3. **Enable SSL** (usually automatic)

## 📱 PWA (Progressive Web App)

To make your chat app installable, add to `public/manifest.json`:

```json
{
  "name": "P2P Chat",
  "short_name": "P2P Chat",
  "description": "Secure peer-to-peer chat application",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#3b82f6",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

And add to `index.html`:
```html
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#3b82f6">
```

## 🔧 Environment Configuration

For production, you might want to configure:

**Vite Environment Variables** (`.env.production`):
```env
VITE_APP_TITLE=P2P Chat
VITE_STUN_SERVERS=stun:stun.l.google.com:19302,stun:stun1.l.google.com:19302
```

**Build Optimization** (`vite.config.js`):
```js
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          crypto: ['crypto-js']
        }
      }
    }
  }
})
```

## 📊 Analytics (Optional)

Add privacy-friendly analytics:

**Plausible Analytics:**
```html
<script defer data-domain="yourdomain.com" src="https://plausible.io/js/script.js"></script>
```

**Simple Analytics:**
```html
<script async defer src="https://scripts.simpleanalyticscdn.com/latest.js"></script>
```

## 🛠️ Troubleshooting Deployment

### Common Issues:

**1. Blank page after deployment:**
- Check if build completed successfully
- Verify `dist` folder contains files
- Check browser console for errors

**2. 404 on refresh:**
- Configure hosting for Single Page Application
- Add redirect rules for client-side routing

**3. WebRTC not working:**
- Ensure HTTPS is enabled
- Check STUN server configuration
- Verify browser compatibility

**4. Storage issues:**
- Check if IndexedDB is supported
- Verify browser storage permissions
- Test in different browsers

### Debug Commands:
```bash
# Check build output
npm run build && ls -la dist/

# Test production build locally
npm run preview

# Check for console errors
# Open browser dev tools after deployment
```

## 🚀 Performance Tips

1. **Enable gzip compression** on your server
2. **Use CDN** for static assets (Cloudflare, etc.)
3. **Optimize images** before including in build
4. **Enable caching headers** for static assets
5. **Monitor bundle size** with `npm run build`

## 📈 Scaling Considerations

Since this is a P2P application:
- No server scaling needed
- Performance depends on client devices
- Consider WebRTC TURN servers for better connectivity
- Monitor user experience across different networks

---

Your P2P Chat application is now ready for the world! 🌍🔒
