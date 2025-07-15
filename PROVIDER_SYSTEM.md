# AI Provider System Documentation

## Overview

The AI Provider System enables seamless integration with multiple Large Language Model (LLM) providers through a unified proxy architecture. Each provider runs on a dedicated port with built-in guardrails protection.

## Supported Providers

### 🧠 OpenAI (Port: 8891)
**Latest 2025 Model Strings:**
- `gpt-4o` - Latest flagship model with text, vision, and advanced reasoning
- `gpt-4o-mini` - Lightweight, cheaper GPT-4o with strong reasoning  
- `gpt-4-turbo` - Prior generation turbo-optimized GPT-4
- `gpt-4` - Original GPT-4 model
- `gpt-3.5-turbo` - Fast and efficient for most tasks
- `gpt-3.5-turbo-instruct` - Instruct variant for prompt-based completions

**Requirements:** API Key from OpenAI

### 🤖 Anthropic Claude (Port: 8892)
**Latest 2025 Model Strings:**
- `claude-3-5-sonnet-20241022` - Latest and most capable Claude model
- `claude-3-opus-20240229` - Most powerful model for complex reasoning
- `claude-3-sonnet-20240229` - Balanced performance and speed
- `claude-3-haiku-20240307` - Fastest model for quick tasks

**Requirements:** API Key from Anthropic

### 🌐 Google Gemini (Port: 8893)
**Latest 2025 Model Strings:**
- `gemini-2.0-flash-exp` - Latest multimodal model with advanced capabilities
- `gemini-1.5-pro` - Most capable Gemini model for complex tasks
- `gemini-1.5-flash` - Fast and efficient for most tasks
- `gemini-1.0-pro` - Original Gemini Pro model

**Requirements:** API Key from Google Cloud

### 🏠 Ollama (Port: 8895)
**Popular 2025 Models:**
- `llama3.2` - Meta's latest open-source model (1B/3B/11B/90B)
- `llama3.1` - Previous generation Llama model (8B/70B/405B)
- `qwen2.5` - Alibaba's multilingual model (0.5B-72B)
- `mistral` - High-quality 7B parameter model
- `codellama` - Specialized for code generation
- `phi3` - Microsoft's efficient small language model
- `gemma2` - Google's latest Gemma model (2B/9B/27B)
- `deepseek-coder` - Specialized for coding tasks

**Requirements:** Ollama running locally on port 11434

---

## How to Use the Provider System

### 1. Enable a Provider

1. **Navigate to Providers Tab** in the web interface
2. **Set API Key** (for cloud providers):
   - Click the key icon next to the provider
   - Enter your API key
   - The system will validate the key

3. **Select Model**:
   - Choose from the dropdown of available models
   - Default models are pre-selected for optimal performance

4. **Enable Provider**:
   - Toggle the switch to enable the provider
   - The system will automatically start the proxy server

### 2. Port Conflict Resolution

If a port is already in use when enabling a provider, you'll see a **Port Conflict Dialog** with three options:

#### 🔥 Force Enable (Kill Process)
- **What it does:** Terminates the conflicting process and starts the proxy server
- **When to use:** If you know the conflicting process can be safely terminated
- **Risk:** May disrupt other services using that port

#### ⚙️ Use Next Available Port
- **What it does:** Automatically finds and uses the next available port
- **When to use:** When you want to avoid conflicts and don't mind using a different port
- **Benefit:** Safe option that doesn't disrupt existing services
- **Note:** The system will inform you of the new port number

#### ❌ Cancel
- **What it does:** Keeps the provider disabled
- **When to use:** When you want to manually resolve the conflict later

### 3. API Endpoints

Once a provider is enabled, you can access it through:

```
http://localhost:[PORT]/v1/chat/completions
```

For example:
- OpenAI: `http://localhost:8891/v1/chat/completions`
- Anthropic: `http://localhost:8892/v1/chat/completions`
- Gemini: `http://localhost:8893/v1/chat/completions`
- Ollama: `http://localhost:8895/v1/chat/completions`

### 4. Health Check

Each provider has a health endpoint:
```
http://localhost:[PORT]/health
```

Returns:
```json
{
  "status": "healthy",
  "provider": "OpenAI",
  "port": 8891,
  "model": "gpt-4o",
  "timestamp": "2025-07-15T15:20:31.151034"
}
```

---

## Code Examples

### OpenAI API Call
```python
import requests

response = requests.post(
    "http://localhost:8891/v1/chat/completions",
    headers={"Content-Type": "application/json"},
    json={
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "max_tokens": 100
    }
)

print(response.json())
```

### Anthropic API Call
```python
import requests

response = requests.post(
    "http://localhost:8892/v1/chat/completions",
    headers={"Content-Type": "application/json"},
    json={
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {"role": "user", "content": "Explain quantum computing"}
        ],
        "max_tokens": 200
    }
)

print(response.json())
```

### Ollama API Call
```python
import requests

response = requests.post(
    "http://localhost:8895/api/generate",
    headers={"Content-Type": "application/json"},
    json={
        "model": "llama3.2",
        "prompt": "Write a poem about AI",
        "stream": False
    }
)

print(response.json())
```

---

## Guardrails Integration

All providers are protected by the integrated guardrails system:

### Input Filtering
- **Toxicity Detection:** Blocks harmful or offensive content
- **PII Protection:** Prevents processing of personal information
- **Prompt Injection:** Detects and blocks prompt injection attempts

### Output Filtering
- **Content Safety:** Ensures generated content meets safety standards
- **Consistency Checks:** Validates output against configured policies

### Blocked Request Response
```json
{
  "blocked": true,
  "blocking_reasons": ["Toxic content detected (confidence: 0.96)"],
  "input_analysis": {
    "toxicity": {
      "blocked": true,
      "confidence": 0.96
    }
  },
  "provider": "OpenAI",
  "timestamp": "2025-07-15T15:20:31.151034"
}
```

---

## Configuration Management

### Environment Variables
```bash
# Backend URL (default: http://localhost:8000)
REACT_APP_BACKEND_URL=http://localhost:8000

# Default ports (can be changed in provider settings)
OPENAI_PORT=8891
ANTHROPIC_PORT=8892
GEMINI_PORT=8893
OLLAMA_PORT=8895
```

### Provider Configuration
Each provider can be configured with:
- **API Key:** Required for cloud providers
- **Selected Model:** Choose from available models
- **Port:** Network port for the proxy server
- **Enabled Status:** Whether the provider is active

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
**Error:** "Port conflict detected"
**Solution:** Use the Port Conflict Dialog to either force enable or use next available port

#### 2. API Key Invalid
**Error:** "API key required" or "HTTP 401: Unauthorized"
**Solution:** Check your API key in the provider settings

#### 3. Provider Not Responding
**Error:** "Provider [Name] unavailable"
**Solution:** 
- Check if the provider is enabled
- Verify the proxy server is running (`lsof -i :[PORT]`)
- Test the connection using the "Test Connection" button

#### 4. Ollama Connection Failed
**Error:** "Ollama not accessible"
**Solution:** 
- Ensure Ollama is running on port 11434
- Check: `curl http://localhost:11434/api/tags`

### Debug Commands

#### Check Running Proxy Servers
```bash
# Check specific port
lsof -i :8891

# Check all provider ports
lsof -i :8891 -i :8892 -i :8893 -i :8895
```

#### Test Provider Health
```bash
# Test OpenAI proxy
curl http://localhost:8891/health

# Test all providers
curl http://localhost:8891/health
curl http://localhost:8892/health
curl http://localhost:8893/health
curl http://localhost:8895/health
```

#### Check Backend Logs
```bash
# View backend logs
tail -f logs/backend.log

# View specific provider logs
grep "OpenAI" logs/backend.log
```

---

## Security Considerations

### API Key Protection
- API keys are stored securely in the backend
- Keys are never logged or exposed in responses
- Use environment variables for production deployments

### Network Security
- Proxy servers bind to localhost by default
- Enable firewall rules for production environments
- Use HTTPS in production with proper SSL certificates

### Guardrails Enforcement
- All requests pass through the guardrails system
- Blocked requests are logged for monitoring
- Configure detection thresholds based on your use case

---

## Performance Optimization

### Model Selection
- **For speed:** Use `gpt-4o-mini`, `claude-3-haiku`, or `gemini-1.5-flash`
- **For quality:** Use `gpt-4o`, `claude-3-5-sonnet`, or `gemini-1.5-pro`
- **For cost:** Use `gpt-3.5-turbo` or Ollama local models

### Caching
- Enable response caching for repeated queries
- Configure cache TTL based on your use case
- Monitor cache hit rates for optimization

### Load Balancing
- Use multiple provider instances for high availability
- Implement request routing based on content type
- Monitor response times and error rates

---

## Support and Maintenance

### Monitoring
- Check provider status in the web interface
- Monitor response times and error rates
- Set up alerts for provider failures

### Updates
- Keep provider API keys updated
- Monitor for new model releases
- Update model strings when new versions are available

### Backup and Recovery
- Export provider configurations
- Backup API keys securely
- Document custom configurations

---

## API Reference

### Backend Endpoints

#### List Providers
```
GET /api/providers/
```

#### Enable Provider
```
POST /api/providers/{provider_id}/enable
```

#### Disable Provider
```
POST /api/providers/{provider_id}/disable
```

#### Test Connection
```
POST /api/providers/{provider_id}/test-connection
```

#### Update Configuration
```
PUT /api/providers/{provider_id}/config
```

#### Set API Key
```
POST /api/providers/{provider_id}/api-key?api_key={key}
```

#### Select Model
```
POST /api/providers/{provider_id}/select-model?model_id={model}
```

### Frontend Components

#### useProviders Hook
```typescript
const {
  providers,
  stats,
  loading,
  error,
  enableProvider,
  disableProvider,
  enableProviderWithPortSelection,
  testConnection,
  updateProviderConfig,
} = useProviders();
```

#### ProvidersConfig Component
```typescript
<ProvidersConfig onProviderChange={handleProviderChange} />
```

#### PortConflictDialog Component
```typescript
<PortConflictDialog
  open={open}
  onClose={handleClose}
  provider={provider}
  conflictData={conflictData}
  onForceEnable={handleForceEnable}
  onUseNextPort={handleUseNextPort}
/>
```

---

This documentation provides a comprehensive guide to using the AI Provider System. For additional support, check the logs or contact the development team.