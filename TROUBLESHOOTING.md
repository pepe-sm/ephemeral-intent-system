# Troubleshooting Guide - Ephemeral Intent System

## Issue: System Stuck in "Voice Guidance Active" State

### Symptoms
- Interface shows "Voice guidance active" message
- No content is being displayed
- System appears frozen or unresponsive
- Biometric data was captured but nothing happens after

### Root Causes

1. **Backend Pipeline Failure**
   - One of the pipeline steps (biometric analysis, knowledge query, or UI orchestration) failed
   - Backend service is not running or crashed
   - WebSocket connection was interrupted

2. **Missing UI Component Tree**
   - Backend sent knowledge payload but failed to send UI update
   - UI orchestrator encountered an error
   - Component tree structure is malformed

3. **Frontend State Mismatch**
   - Frontend received partial data but not complete pipeline response
   - State management issue preventing UI render

### Solutions

#### Immediate Fix (User)
1. **Refresh the page** - This will reset the entire session
2. **Check browser console** - Look for error messages (F12 → Console tab)
3. **Wait 30 seconds** - The system now has a timeout that will show a "Restart Session" button

#### For Developers

##### Check Backend Logs
```bash
# Check if backend is running
curl http://localhost:8000/health

# View backend logs
docker-compose logs -f backend

# Or if running locally
tail -f backend/logs/app.log
```

##### Check WebSocket Connection
Open browser console and look for:
- `WebSocket connection status: true` - Connection is working
- `WebSocket message received:` - Messages are being received
- Any error messages about WebSocket failures

##### Verify Pipeline Steps
The pipeline should complete these steps in order:
1. `biometric_analysis` → `biometric_token` response
2. `knowledge_query` → `knowledge_payload` response  
3. `ui_orchestration` → `ui_update` response
4. `pipeline_complete` message

Check console logs to see which step failed.

##### Common Backend Issues

**Issue: RAG Engine Not Initialized**
```bash
# Check if ChromaDB is accessible
ls -la backend/chroma_db/

# Reinitialize if needed
cd backend
python -c "from app.services.rag_engine import RAGEngine; RAGEngine()"
```

**Issue: MediaPipe/OpenCV Not Working**
```bash
# Reinstall dependencies
pip install --force-reinstall mediapipe opencv-python
```

**Issue: WebSocket Connection Fails**
- Check CORS settings in `backend/app/main.py`
- Verify WebSocket endpoint is accessible: `ws://localhost:8000/ws/{session_id}`
- Check firewall/network settings

##### Frontend Debugging

**Enable Debug Mode**
Set in `.env`:
```
VITE_DEBUG_MODE=true
```

This will show:
- Detailed console logs
- Debug panel with session info
- Frame capture counts

**Check State in React DevTools**
1. Install React DevTools browser extension
2. Open DevTools → Components tab
3. Find `App` component
4. Check state values:
   - `knowledgePayload` - Should have data
   - `uiComponentTree` - Should have component structure
   - `isCapturingBiometrics` - Should be false
   - `error` - Check for error messages

### New Features Added (Fix)

#### 1. Loading State Indicator
When knowledge payload is received but UI hasn't been generated yet, a loading spinner is shown with:
- "Generating Personalized Learning Experience" message
- "Voice guidance will be active" indicator
- Visual feedback that system is working

#### 2. Timeout Detection
- 30-second timeout after biometric capture
- Automatically shows error if pipeline doesn't complete
- "Restart Session" button appears for easy recovery

#### 3. Enhanced Logging
- All WebSocket messages now logged with full data
- Pipeline status updates tracked
- Missing component tree detected and logged
- Better error messages for debugging

#### 4. Graceful Error Handling
- Invalid UI configurations detected
- Clear error messages shown to user
- Automatic state cleanup on errors

### Testing the Fix

1. **Start the system**
   ```bash
   docker-compose up
   ```

2. **Open browser console** (F12)

3. **Submit a query** and watch the console for:
   ```
   WebSocket message received: biometric_token
   Processing biometric token: {...}
   WebSocket message received: knowledge_payload
   Processing knowledge payload: {...}
   WebSocket message received: ui_update
   Processing UI update: {...}
   ```

4. **Verify loading states**:
   - After biometric capture: Loading spinner should appear
   - After 30 seconds: Timeout error should appear if stuck
   - After UI update: Content should render

### Prevention

To prevent this issue:

1. **Always check backend health before starting**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Monitor backend logs** during development
   ```bash
   docker-compose logs -f backend
   ```

3. **Use the debug panel** (development mode) to track state

4. **Test with simple queries first** before complex ones

### Related Files Modified

- `frontend/src/App.tsx` - Added loading state, timeout, retry button
- `frontend/src/hooks/useWebSocket.ts` - Enhanced logging and error handling
- `frontend/src/config/index.ts` - Added new message types
- `TROUBLESHOOTING.md` - This guide

### Contact

If issues persist:
1. Check GitHub issues
2. Review backend logs for stack traces
3. Verify all dependencies are installed correctly
4. Try with a fresh Docker build: `docker-compose build --no-cache`

---
Made with Bob for IBM AI Builders Challenge