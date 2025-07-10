# Ollama API Timeout Improvements

## Changes Made

### 1. Increased Timeout Values
- **Async streaming**: Changed from 60s to 300s total timeout
- **Connection timeout**: Set to 30s (separate from total)
- **Socket read timeout**: Set to 120s for ongoing data transfer
- **Sync requests**: Increased from 60s to 300s

### 2. Granular Timeout Configuration
```python
# Before
timeout=aiohttp.ClientTimeout(total=60)

# After
timeout=aiohttp.ClientTimeout(total=300, connect=30, sock_read=120)
```

### 3. Enhanced Error Messages
- More specific timeout error messages
- Distinguishes between connection and streaming timeouts
- Better guidance for users on what to do

### 4. Added Debug Logging
- Logs start of streaming requests
- Shows conversation size and prompt length
- Tracks chunk count and response size
- Confirms when stream completes successfully

## Timeout Breakdown

| Phase | Timeout | Purpose |
|-------|---------|---------|
| Connection | 30s | Time to establish connection to Ollama |
| Socket Read | 120s | Time between chunks during streaming |
| Total | 300s | Maximum time for entire request |

## Why These Values?

1. **Large System Instructions**: The AI system instructions are quite comprehensive (~8KB+), which takes time to process
2. **Mistral Model Size**: Large language models need time to generate responses
3. **Streaming Nature**: Response generation happens in real-time, not all at once
4. **Network Variability**: Docker networking can add latency

## Expected Behavior

✅ **Connection Phase** (0-30s): Establishing connection to Ollama service
✅ **Processing Phase** (0-60s): Model processes the large system instructions  
✅ **Streaming Phase** (0-240s): Model generates and streams response chunks
✅ **Total Time** (max 300s): Complete request lifecycle

The improvements should resolve the timeout issues you were experiencing during streaming responses.
