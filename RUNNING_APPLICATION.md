# Running Application Guide
## Ephemeral Intent Synthesis System

---

## ✅ Application Status: RUNNING

### Backend Server
- **Status**: ✅ Running
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **WebSocket**: ws://localhost:8000/ws

### Frontend Application
- **Status**: ✅ Running
- **Local URL**: http://localhost:3000
- **Network URLs**:
  - http://172.21.80.1:3000
  - http://192.168.88.12:3000
  - http://172.17.192.1:3000

---

## 🚀 Quick Start

### Access the Application
1. Open your browser
2. Navigate to: **http://localhost:3000**
3. Allow camera access when prompted (required for biometric capture)

### Test the Full Pipeline

#### Step 1: Enter a Query
```
Example queries:
- "How do React hooks work?"
- "Explain machine learning basics"
- "What is async/await in JavaScript?"
```

#### Step 2: Biometric Capture
- Click "Start Learning"
- The system will capture your facial biometrics for 3 seconds
- You'll see real-time feedback with:
  - Progress bar
  - Frames processed
  - Landmarks detected
  - Processing time

#### Step 3: View Results
After capture, you'll see:
- **Biometric Analysis**: Cognitive load, attention score, urgency, confidence
- **Knowledge Content**: Personalized learning modules
- **Dynamic UI**: Adaptive interface based on your cognitive state

#### Step 4: Navigate Content
- Click "Continue" to move to the next module
- Click "Need Help" if you're confused
- Progress bar shows your learning progress

---

## 🔍 What to Observe

### Biometric Capture
- **Green dots**: Facial landmarks being tracked (468 points)
- **Progress bar**: Capture completion (0-100%)
- **Stats**: Real-time processing metrics

### Biometric Analysis Display
- **Cognitive Load**: high/medium/low
- **Attention Score**: 0-100%
- **Urgency**: immediate/moderate/low
- **Confidence**: Analysis confidence level

### Dynamic UI Features
- **Cognitive Load Indicator**: Color-coded status (green/yellow/red)
- **Animated Transitions**: Smooth content changes
- **Adaptive Font Size**: Based on cognitive load
- **Module Controls**: Continue and Need Help buttons

### WebSocket Connection
- **Top right corner**: Connection status indicator
  - Green "Connected" = Active WebSocket
  - Red "Disconnected" = Connection lost

---

## 🧪 Testing Scenarios

### Scenario 1: Basic Flow
1. Enter query: "What is React?"
2. Complete biometric capture
3. Review biometric analysis
4. Navigate through learning modules
5. Complete session

### Scenario 2: Error Handling
1. Disconnect internet
2. Try to submit query
3. Observe offline mode activation
4. Reconnect internet
5. Watch automatic sync

### Scenario 3: Engagement Signals
1. Start learning session
2. Click "Need Help" on a module
3. Observe UI adaptation
4. Click "Continue" when ready

---

## 📊 Monitoring

### Browser Console
Open Developer Tools (F12) to see:
- WebSocket messages
- Analytics events
- State changes
- Performance metrics
- Error logs (if any)

### Network Tab
Monitor:
- WebSocket connection
- API requests
- Resource loading
- Performance timing

### Application Tab
Check:
- IndexedDB storage (offline data)
- LocalStorage (session persistence)
- Service Worker status

---

## 🐛 Troubleshooting

### Camera Not Working
**Issue**: Camera access denied
**Solution**: 
- Check browser permissions
- Ensure HTTPS or localhost
- Try different browser
- Check camera is not in use

### WebSocket Connection Failed
**Issue**: Red "Disconnected" status
**Solution**:
- Verify backend is running (http://localhost:8000/health)
- Check firewall settings
- Restart both servers
- Clear browser cache

### Blank Screen
**Issue**: Frontend not loading
**Solution**:
- Check browser console for errors
- Verify frontend is running (Terminal 2)
- Clear browser cache
- Try incognito mode

### Build Errors
**Issue**: TypeScript or build errors
**Solution**:
- Run `npm install` in frontend directory
- Delete `node_modules` and reinstall
- Check Node.js version (>= 18.0.0)

---

## 🔧 Development Tools

### Hot Reload
Both servers support hot reload:
- **Backend**: Auto-reloads on Python file changes
- **Frontend**: Auto-reloads on TypeScript/React changes

### Debug Mode
Enable debug logging:
```bash
# Backend
DEBUG=true uvicorn app.main:app --reload

# Frontend
# Already enabled in development mode
```

### API Documentation
Access interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📱 Browser Compatibility

### Recommended Browsers
- ✅ Chrome/Edge (v90+)
- ✅ Firefox (v88+)
- ✅ Safari (v14+)

### Required Features
- WebSocket support
- MediaPipe support
- Camera API access
- IndexedDB support
- ES2020+ JavaScript

---

## 🎯 Key Features to Test

### 1. Biometric Capture
- [ ] Camera initializes
- [ ] Landmarks detected
- [ ] Progress updates
- [ ] Stats display correctly
- [ ] Capture completes

### 2. WebSocket Communication
- [ ] Connection established
- [ ] Messages sent/received
- [ ] Auto-reconnection works
- [ ] Heartbeat active

### 3. State Management
- [ ] Session persists
- [ ] State updates correctly
- [ ] Module navigation works
- [ ] Progress tracked

### 4. Error Handling
- [ ] Errors display properly
- [ ] Recovery options work
- [ ] Logs captured

### 5. Offline Mode
- [ ] Data cached locally
- [ ] Actions queued
- [ ] Sync on reconnect

### 6. Analytics
- [ ] Events tracked
- [ ] Performance monitored
- [ ] Console logs visible

---

## 📈 Performance Metrics

### Expected Performance
- **Page Load**: < 2 seconds
- **Biometric Capture**: 3 seconds (configurable)
- **WebSocket Latency**: < 100ms
- **UI Transitions**: 60 FPS

### Monitor Performance
```javascript
// In browser console
performance.getEntriesByType('navigation')
performance.getEntriesByType('resource')
```

---

## 🛑 Stopping the Application

### Stop Servers
1. **Backend**: Press `Ctrl+C` in Terminal 1
2. **Frontend**: Press `Ctrl+C` in Terminal 2

### Clean Shutdown
```bash
# Stop all processes
Ctrl+C (in each terminal)

# Optional: Clear cache
rm -rf frontend/node_modules/.vite
```

---

## 🔄 Restarting

### Quick Restart
```bash
# Terminal 1 (Backend)
cd backend
uvicorn app.main:app --reload

# Terminal 2 (Frontend)
cd frontend
npm run dev
```

### Full Restart
```bash
# Stop all servers (Ctrl+C)
# Clear caches
# Restart as above
```

---

## 📞 Support

### Check Logs
- **Backend**: Terminal 1 output
- **Frontend**: Terminal 2 output + Browser console
- **Network**: Browser DevTools Network tab

### Common Issues
See DEPLOYMENT_GUIDE.md "Troubleshooting" section

### Debug Checklist
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Camera permissions granted
- [ ] WebSocket connected
- [ ] No console errors

---

## 🎉 Success Indicators

You'll know everything is working when:
1. ✅ Both servers start without errors
2. ✅ Frontend loads at http://localhost:3000
3. ✅ "Connected" status shows in top right
4. ✅ Camera initializes when starting capture
5. ✅ Biometric data displays after capture
6. ✅ Learning modules render correctly
7. ✅ Navigation works smoothly

---

**Made with Bob for IBM AI Builders Challenge 2024** 🚀

**Current Status**: ✅ RUNNING AND READY TO TEST