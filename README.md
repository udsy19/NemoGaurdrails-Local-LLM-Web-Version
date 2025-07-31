# AI Safety System with Guardrails
### Multi-Provider LLM Gateway with Content Filtering and Analytics

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.1+-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.9+-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Current Features](#current-features)
3. [Architecture](#architecture)
4. [Detection Models](#detection-models)
5. [Provider Support](#provider-support)
6. [Installation & Setup](#installation--setup)
7. [API Documentation](#api-documentation)
8. [Configuration](#configuration)
9. [Roadmap](#roadmap)
10. [Development](#development)

---

## 🌟 System Overview

This is an **AI Safety System** that provides a secure gateway for accessing multiple Large Language Model (LLM) providers with built-in content filtering and monitoring capabilities. The system intercepts requests to AI providers, applies configurable safety checks, and provides analytics on usage patterns.

### Current Implementation Status

This is a **proof-of-concept system** with basic guardrail functionality. It demonstrates core concepts of AI safety filtering but is not yet production-ready for enterprise deployment.

### Key Features (Currently Implemented)

- **🛡️ Basic Content Filtering**: Toxicity, PII, and prompt injection detection
- **🔀 Multi-Provider Support**: OpenAI, Anthropic Claude, Google Gemini, and Ollama integration
- **🌐 Port-based Routing**: Dynamic port allocation for different providers
- **📊 Basic Analytics**: Request tracking and simple metrics
- **🎛️ Configuration Management**: YAML-based settings for guardrails and providers
- **🖥️ Web Interface**: React-based dashboard for system management

### Limitations

- **Single Model Detection**: Each guardrail type uses one primary model (not ensemble-based)
- **Basic Performance**: No advanced optimization or caching
- **Limited Analytics**: Simple request counting without sophisticated metrics
- **Development Stage**: Not optimized for production workloads
- **Manual Testing**: Limited automated testing and validation

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (React + TypeScript)              │
│                         Port 3000                              │
├─────────────────────────────────────────────────────────────────┤
│  • System Dashboard    • Provider Management                   │
│  • Analytics View      • Guardrails Configuration             │
│  • Testing Interface   • System Logs                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                Main API Gateway (FastAPI)                      │
│                         Port 8000                              │
├─────────────────────────────────────────────────────────────────┤
│  • /api/chat         • /api/providers                          │
│  • /api/analytics    • /api/config                             │
│  • /api/detectors    • /health                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Traffic Router                               │
├─────────────────────────────────────────────────────────────────┤
│  Provider-Specific Proxy Servers:                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Port 8891: OpenAI Proxy                                   │ │
│  │  • Basic request/response filtering                        │ │
│  │  • Simple analytics tracking                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Port 8892: Anthropic Proxy                                │ │
│  │  • Format conversion (OpenAI ↔ Anthropic)                  │ │
│  │  • Basic content filtering                                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Port 8893: Google Gemini Proxy                            │ │
│  │  • Request format conversion                               │ │
│  │  • Simple safety checks                                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Port 8894: Ollama Proxy                                   │ │
│  │  • Local model access                                     │ │
│  │  • Offline processing                                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Detection Services                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Toxicity   │  │     PII      │  │   Prompt     │          │
│  │  Detection   │  │  Detection   │  │  Injection   │          │
│  │              │  │              │  │  Detection   │          │
│  │ Single Model │  │ spaCy-based  │  │ Pattern-based│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

#### **Frontend (React)**
- **Dashboard**: Basic system monitoring and control
- **Provider Management**: Enable/disable providers and set API keys
- **Testing Interface**: Simple chat interface for testing
- **Analytics View**: Basic request statistics
- **Configuration**: Guardrail threshold settings

#### **API Gateway (FastAPI)**
- **RESTful API**: Standard HTTP endpoints
- **Request Routing**: Direct requests to appropriate services
- **Basic Authentication**: API key validation
- **Health Checks**: Simple service availability monitoring

#### **Traffic Router**
- **Port Management**: Static port allocation per provider
- **Request Forwarding**: Proxy requests to external APIs
- **Response Processing**: Basic response handling
- **Analytics Tracking**: Simple request counting

#### **Detection Services**
- **Single Model Processing**: One model per detection type
- **Basic Thresholding**: Simple pass/fail decisions
- **Configuration Loading**: YAML-based settings

---

## 🔍 Detection Models

### Currently Implemented Models

#### **1. Toxicity Detection**
- **Model**: `unitary/toxic-bert-base-uncased`
- **Type**: BERT-based binary classifier
- **Purpose**: Detect hate speech, profanity, and toxic content
- **Performance**: Basic functionality, no benchmarking data
- **Configuration**: Configurable threshold (default: 0.7)

#### **2. PII Detection**
- **Model**: `spacy/en_core_web_sm`
- **Type**: Named Entity Recognition
- **Purpose**: Detect personal information (names, emails, phone numbers)
- **Performance**: Basic NER functionality
- **Configuration**: Entity type selection

#### **3. Prompt Injection Detection**
- **Model**: Custom pattern matching + basic ML
- **Type**: Rule-based with simple classification
- **Purpose**: Detect attempt to manipulate AI behavior
- **Performance**: Basic pattern recognition
- **Configuration**: Pattern threshold settings

### Detection Pipeline

```
Input Text
    ↓
[Enabled Detectors Run Sequentially]
    ↓ 
[Simple Threshold Comparison]
    ↓
[Block/Allow Decision]
    ↓
[Basic Analytics Logging]
```

### Limitations
- **Single Models**: No ensemble or redundancy
- **Sequential Processing**: Not optimized for speed
- **Basic Thresholds**: Simple greater-than comparisons
- **No Confidence Scoring**: Binary pass/fail only
- **Limited Model Types**: Missing spam, fact-check, topic classification

---

## 🔗 Provider Support

### Supported AI Providers

#### **OpenAI**
- **Models**: GPT-4o, GPT-4o-mini, GPT-3.5-turbo
- **Features**: Standard OpenAI API compatibility
- **Port**: 8891
- **Status**: Basic implementation

#### **Anthropic Claude**
- **Models**: Claude-3.5-Sonnet, Claude-3-Opus, Claude-3-Haiku
- **Features**: Format conversion from OpenAI API
- **Port**: 8892
- **Status**: Basic implementation with format translation

#### **Google Gemini**
- **Models**: Gemini-2.0-Flash, Gemini-1.5-Pro
- **Features**: Basic API integration
- **Port**: 8893
- **Status**: Experimental implementation

#### **Ollama (Local)**
- **Models**: Any locally installed model (Llama, Mistral, etc.)
- **Features**: Local processing, offline capability
- **Port**: 8894
- **Status**: Basic proxy to local Ollama instance

### Provider Features
- **Basic API Key Management**: Simple storage and usage
- **Request Forwarding**: Direct proxy to provider APIs
- **Format Conversion**: Basic OpenAI → Provider format translation
- **Error Handling**: Simple error pass-through
- **Analytics**: Basic request counting per provider

---

## 🚀 Installation & Setup

### Prerequisites

- **Python**: 3.9 or higher
- **Node.js**: 18.0 or higher
- **Git**: For cloning the repository

### Quick Start

#### 1. Clone Repository
```bash
git clone https://github.com/udsy19/NemoGaurdrails-Local-LLM-Web-Version.git
cd NemoGaurdrails-Local-LLM-Web-Version
```

#### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
npm run build
```

#### 4. Configuration
```bash
# Edit main configuration
nano backend/configs/app_config.yml

# Configure guardrails (optional)
ls backend/configs/guardrails/
```

#### 5. Start Services
```bash
# Terminal 1: Start backend
cd backend
python app/main.py

# Terminal 2: Start frontend
cd frontend
npm start
```

#### 6. Access System
- **Frontend Dashboard**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

### Configuration

#### Basic Configuration (app_config.yml)
```yaml
server:
  host: "0.0.0.0"
  port: 8000
  debug: true

providers:
  openai:
    enabled: false
    api_key: ""
    default_model: "gpt-4o-mini"
    port: 8891
  
  anthropic:
    enabled: false
    api_key: ""
    default_model: "claude-3.5-sonnet"
    port: 8892

guardrails:
  input_enabled: true
  output_enabled: true

detectors:
  toxicity:
    enabled: true
    threshold: 0.7
  pii:
    enabled: true
    sensitivity: "medium"
  prompt_injection:
    enabled: true
    threshold: 0.8
```

---

## 📚 API Documentation

### Main Endpoints

#### Health Check
```http
GET /health
```
Returns system health status.

#### Chat Completion
```http
POST /api/chat/completions
Content-Type: application/json

{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "user", "content": "Hello"}
  ]
}
```

#### Provider Management
```http
GET /api/providers
POST /api/providers/{provider_id}/enable
POST /api/providers/{provider_id}/disable
```

#### Analytics
```http
GET /api/analytics/dashboard
GET /api/analytics/requests
GET /api/analytics/export?hours=24&comprehensive=true
```

#### Configuration
```http
GET /api/config/system
PUT /api/config/system
```

### Analytics Export Features

The system provides comprehensive analytics export capabilities:

#### **Comprehensive Export** (Default)
Downloads a complete JSON file containing:
- **Dashboard Data**: All charts, metrics, and visualizations
- **Individual Events**: Every request with full details
- **User Sessions**: Complete user activity tracking
- **Detector Analytics**: Detailed performance metrics
- **Provider Performance**: Response times and error rates
- **Threat Intelligence**: Security patterns and analysis
- **System Health**: Performance and capacity metrics

#### **Basic Export** (Legacy)
Downloads summary statistics only for basic reporting.

#### **Export Contents**
```json
{
  "analytics_summary": { /* Dashboard reconstruction data */ },
  "realtime_stats": { /* Current system metrics */ },
  "events": [ /* Individual request details */ ],
  "user_sessions": [ /* User activity tracking */ ],
  "detector_analytics": [ /* ML model performance */ ],
  "provider_performance": [ /* API provider metrics */ ],
  "threat_intelligence": [ /* Security analysis */ ],
  "performance_timeline": [ /* Historical performance */ ],
  "system_health": { /* Overall system status */ },
  "metadata": { /* Export information */ }
}
```

### Provider-Specific Endpoints

Each provider runs on its dedicated port with OpenAI-compatible API:

- **OpenAI**: http://localhost:8891/v1/chat/completions
- **Anthropic**: http://localhost:8892/v1/chat/completions
- **Gemini**: http://localhost:8893/v1/chat/completions
- **Ollama**: http://localhost:8894/v1/chat/completions

---

## 🛣️ Roadmap

### Current Status: Proof of Concept

### Short-term Goals (Next 1-2 months)
- [ ] **Improve Model Performance**: Benchmark and optimize existing detection models
- [ ] **Add More Detection Types**: Implement spam and topic classification
- [ ] **Enhanced Analytics**: Better metrics collection and visualization
- [ ] **Configuration UI**: Frontend interface for all settings
- [ ] **Basic Testing**: Unit tests for core functionality

### Medium-term Goals (3-6 months)
- [ ] **Ensemble Detection**: Multiple models per guardrail type
- [ ] **Performance Optimization**: Parallel processing and caching
- [ ] **Advanced Analytics**: Comprehensive metrics and dashboards
- [ ] **Enhanced UI**: Improved frontend with better UX
- [ ] **Production Hardening**: Error handling, logging, monitoring

### Long-term Goals (6+ months)
- [ ] **Enterprise Features**: Advanced analytics, reporting, compliance
- [ ] **Model Optimization**: Quantization, ONNX conversion, GPU support
- [ ] **Scalability**: Load balancing, clustering, auto-scaling
- [ ] **Advanced Security**: Rate limiting, DDoS protection, audit logs
- [ ] **Packaging**: Standalone executables, Docker containers

---

## 🛠️ Development

### Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── models/           # ML models and data models
│   ├── services/         # Business logic
│   ├── utils/            # Utility functions
│   └── main.py           # Application entry point
├── configs/              # Configuration files
└── requirements.txt      # Python dependencies

frontend/
├── src/
│   ├── components/       # React components
│   ├── services/         # API services
│   ├── types/            # TypeScript types
│   └── App.tsx           # Main application
└── package.json          # Node.js dependencies
```

### Development Setup

#### Backend Development
```bash
cd backend
pip install -r requirements.txt
python app/main.py
```

#### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Testing

Currently limited testing infrastructure. Basic manual testing through:
- Frontend testing interface
- Direct API calls
- Provider proxy testing

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate testing
4. Submit a pull request

---

## 🔧 Troubleshooting

### Common Issues

#### Installation Problems
**Python Dependencies**: Use virtual environment and update pip
```bash
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Node.js Issues**: Clear cache and reinstall
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

#### Runtime Issues
**Port Conflicts**: Check port availability
```bash
lsof -i :8000
lsof -i :3000
```

**Model Loading**: Ensure proper internet connection for initial model downloads

**API Keys**: Verify provider API keys are correctly configured

#### Performance Issues
**Slow Response**: Normal for initial model loading
**Memory Usage**: Models require 2-8GB RAM depending on configuration
**Network Issues**: Check internet connectivity for external providers

### Logs and Debugging

**Backend Logs**: Check console output where backend is running
**Frontend Logs**: Check browser console for React errors
**Network Issues**: Use browser developer tools to inspect API calls

---

## 📈 Performance Notes

### Current Performance Characteristics

- **Initial Startup**: 30-60 seconds (model loading)
- **First Request**: 5-15 seconds (model initialization)
- **Subsequent Requests**: 1-5 seconds (depending on detection enabled)
- **Memory Usage**: 2-8GB (depending on models loaded)
- **CPU Usage**: High during inference, idle otherwise

### Performance Limitations

- **Single-threaded Processing**: No parallel model execution
- **No Caching**: Each request processes from scratch
- **Unoptimized Models**: Full-precision models without quantization
- **Sequential Detection**: Guardrails run one after another

### Optimization Opportunities

- **Model Quantization**: Reduce memory usage and increase speed
- **Parallel Processing**: Run detection models simultaneously
- **Caching**: Store results for repeated content
- **Batch Processing**: Handle multiple requests together

---

## 📝 License and Credits

### License
This project is licensed under the **MIT License**. See the `LICENSE` file for details.

### Author
- **Primary Author**: Udaya Vijay Anand
- **GitHub**: [@udsy19](https://github.com/udsy19)
- **Repository**: [NemoGaurdrails-Local-LLM-Web-Version](https://github.com/udsy19/NemoGaurdrails-Local-LLM-Web-Version)

### Dependencies
- **FastAPI**: Web framework for Python APIs
- **React**: JavaScript library for user interfaces
- **Transformers**: Hugging Face machine learning models
- **Spacy**: Natural language processing library
- **Material-UI**: React component library

### Acknowledgments
- **Hugging Face**: For providing pre-trained models
- **OpenAI, Anthropic, Google**: For AI model APIs
- **Open Source Community**: For tools and libraries used

---

## 🚀 Getting Started

Ready to try the AI Safety System?

1. **Follow Installation Steps** above
2. **Configure Your API Keys** for desired providers
3. **Start the System** (backend + frontend)
4. **Access Dashboard** at http://localhost:3000
5. **Test Basic Functionality** through the testing interface

**Note**: This is a development/proof-of-concept system. For production use, additional security, performance, and reliability improvements are needed.

---

**Built with ❤️ by Udaya Vijay Anand | AI Safety Research & Development**