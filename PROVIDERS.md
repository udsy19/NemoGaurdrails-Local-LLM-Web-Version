# 🌐 Multi-Provider LLM System with Port Management

## Overview

The AI Safety System now includes comprehensive support for multiple LLM providers with intelligent traffic routing and guardrail protection. Each provider operates on a dedicated port, enabling precise traffic management and monitoring.

## ✨ Features

### 🔧 Provider Management
- **Multiple Provider Support**: OpenAI, Anthropic Claude, Google Gemini, Ollama (Local)
- **Real-time Configuration**: Dynamic provider settings with instant updates
- **API Key Management**: Secure handling of provider credentials
- **Model Selection**: Choose from available models for each provider
- **Connection Testing**: Verify provider connectivity and authentication

### 🌐 Port-Based Traffic Routing
- **Dedicated Ports**: Each provider has its own port for precise traffic control
- **Guardrail Integration**: All traffic flows through safety guardrails
- **Load Balancing**: Intelligent request distribution across providers
- **Monitoring**: Real-time traffic metrics and provider health

### 🛡️ Enhanced Security
- **Guardrail Protection**: Every request processed through safety filters
- **API Key Encryption**: Secure storage and transmission of credentials
- **Traffic Isolation**: Provider-specific ports prevent cross-contamination
- **Audit Logging**: Comprehensive request/response logging

## 🚀 Quick Start

### 1. Access Provider Configuration
Navigate to the **Providers** tab in the web interface to configure LLM providers.

### 2. Configure Providers
1. **Enable Provider**: Toggle the switch to activate a provider
2. **Add API Key**: Enter your provider's API key (if required)
3. **Select Model**: Choose from available models
4. **Test Connection**: Verify connectivity and authentication

### 3. Traffic Flow
```
User Request → Provider Port → Guardrails → LLM Service → Safe Response
```

## 📊 Provider Details

### OpenAI (Port 8891)
- **Models**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **API Key**: Required (from OpenAI Platform)
- **Context**: Up to 128k tokens (GPT-4 Turbo)
- **Use Case**: Advanced reasoning, complex tasks

### Anthropic Claude (Port 8892)
- **Models**: Claude 3 Opus, Sonnet, Haiku
- **API Key**: Required (from Anthropic Console)
- **Context**: Up to 200k tokens
- **Use Case**: Constitutional AI, safe interactions

### Google Gemini (Port 8893)
- **Models**: Gemini Pro, Gemini Pro Vision
- **API Key**: Required (from Google AI Studio)
- **Context**: Up to 32k tokens
- **Use Case**: Multimodal AI, coding assistance

### Ollama Local (Port 8895)
- **Models**: Llama 2, Code Llama, Mistral, Neural Chat
- **API Key**: Not required (local models)
- **Context**: Varies by model (4k-16k tokens)
- **Use Case**: Private, offline AI processing

## ⚠️ Important Security Notes

### Ollama Users
- **Port 8895**: Routes through guardrails (RECOMMENDED for safety)
- **Port 11434**: Direct Ollama access (BYPASSES all safety checks)

Always use port 8895 for production to ensure all safety measures are active.

## 🔌 API Endpoints

### Provider Management
```
GET    /api/providers/                    # List all providers
GET    /api/providers/{id}                # Get specific provider
PUT    /api/providers/{id}/config         # Update provider config
POST   /api/providers/{id}/test-connection # Test provider connection
POST   /api/providers/{id}/enable         # Enable provider
POST   /api/providers/{id}/disable        # Disable provider
```

### Statistics and Monitoring
```
GET    /api/providers/stats/summary       # Provider statistics
GET    /api/providers/port/{port}         # Get provider by port
POST   /api/providers/test-all-connections # Test all enabled providers
```

## 🛠️ Configuration Examples

### OpenAI Setup
```json
{
  "enabled": true,
  "api_key": "sk-...",
  "selected_model": "gpt-4",
  "port": 8891
}
```

### Anthropic Claude Setup
```json
{
  "enabled": true,
  "api_key": "sk-ant-...",
  "selected_model": "claude-3-sonnet",
  "port": 8892
}
```

### Ollama Local Setup
```json
{
  "enabled": true,
  "selected_model": "llama2",
  "port": 8895
}
```

## 📈 Monitoring and Analytics

### Provider Statistics
- Total/enabled/connected provider counts
- Port mapping and status overview
- Real-time connection health
- Request/error rate tracking

### Traffic Analytics
- Request volume per provider
- Response time metrics
- Error rate monitoring
- Guardrail trigger statistics

## 🔧 Advanced Configuration

### Environment Variables
```bash
# Backend URL for frontend
REACT_APP_BACKEND_URL=http://localhost:8000

# Provider-specific settings
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
```

### Custom Port Configuration
The system uses the following default ports:
- **OpenAI**: 8891
- **Anthropic**: 8892
- **Google Gemini**: 8893
- **Ollama**: 8895

Ports can be customized in the provider service configuration.

## 🐛 Troubleshooting

### Common Issues

#### Provider Not Connecting
1. Verify API key is correct and active
2. Check provider service status
3. Ensure network connectivity
4. Review error messages in logs

#### Port Conflicts
1. Check if ports are already in use
2. Modify port configuration if needed
3. Restart the application
4. Verify firewall settings

#### Guardrails Not Working
1. Ensure provider traffic flows through correct port
2. Check guardrail configuration
3. Verify detector status
4. Review guardrail logs

### Error Codes
- **401**: Invalid API key
- **403**: Rate limit exceeded
- **503**: Provider service unavailable
- **500**: Internal server error

## 🎯 Best Practices

### Security
1. **Use Environment Variables**: Store API keys securely
2. **Regular Key Rotation**: Update API keys periodically
3. **Monitor Access**: Track provider usage patterns
4. **Enable All Guardrails**: Maximum safety protection

### Performance
1. **Test Connections**: Regularly verify provider health
2. **Monitor Metrics**: Track response times and errors
3. **Load Distribution**: Use multiple providers for redundancy
4. **Cache Responses**: Implement caching for common queries

### Reliability
1. **Multiple Providers**: Configure fallback providers
2. **Health Checks**: Automated provider monitoring
3. **Error Handling**: Graceful degradation on failures
4. **Backup Plans**: Local Ollama as final fallback

## 🚀 Future Enhancements

### Planned Features
- **Auto-failover**: Automatic provider switching on failures
- **Load Balancing**: Intelligent request distribution
- **Custom Models**: Support for fine-tuned models
- **Provider Pools**: Grouped providers for specific use cases
- **Advanced Analytics**: Detailed usage and performance metrics

### Integration Roadmap
- **Kubernetes Support**: Container orchestration
- **Cloud Deployment**: AWS, GCP, Azure integration
- **Enterprise Features**: SSO, RBAC, audit logging
- **API Gateway**: Centralized traffic management

---

For technical support or feature requests, please refer to the main documentation or create an issue in the project repository.