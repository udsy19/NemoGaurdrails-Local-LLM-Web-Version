# 🛡️ AI Safety System - Modern React Frontend

A cutting-edge, dark-themed React frontend for the AI Safety System with real-time monitoring, interactive guardrail controls, and live CLI output visualization.

## ✨ Features

### 🎨 Modern Design
- **Dark Theme**: Carefully crafted dark UI with cyan-green accents
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile
- **Smooth Animations**: Framer Motion powered transitions and micro-interactions
- **Glassmorphism Effects**: Modern blur effects and gradients

### 🛡️ Guardrail Management
- **Interactive Controls**: Toggle detectors with real-time feedback
- **Advanced Configuration**: Adjust detection thresholds and parameters
- **Visual Status Indicators**: Clear health and status visualization
- **Quick Actions**: Enable/disable all detectors with one click

### 💬 Advanced Chat Interface
- **Real-time Processing**: Live visualization of AI processing stages
- **Message Analysis**: Detailed input/output detection results
- **Blocking Indicators**: Clear visualization when content is blocked
- **Confidence Scores**: Visual confidence indicators for each detector

### 📟 Live Terminal
- **Real-time Logs**: Live streaming of system logs and events
- **Interactive Commands**: Built-in terminal with system commands
- **Filtering**: Search and filter logs by source or content
- **Fullscreen Mode**: Dedicated terminal view with advanced features

### 📊 System Dashboard
- **Health Monitoring**: Real-time system health visualization
- **Performance Metrics**: Live charts and analytics
- **Threat Analysis**: Visual threat level analysis
- **Event Timeline**: Recent system events and notifications

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and npm
- Backend API running on port 8000

### Start Frontend Only
```bash
# From the project root
./start_frontend.sh
```

### Start Complete System
```bash
# From the project root  
./start_full_system.sh
```

### Manual Setup
```bash
cd frontend
npm install --legacy-peer-deps
npm start
```

The frontend will be available at `http://localhost:3000`

## 🛠️ Technology Stack

### Core Framework
- **React 19** with TypeScript
- **Material-UI (MUI)** for component library
- **Emotion** for styled components

### Real-time Features  
- **Socket.IO Client** for WebSocket connections
- **Axios** for HTTP API calls
- **React Hot Toast** for notifications

### Visualization
- **Recharts** for dashboard analytics
- **Framer Motion** for animations
- **React Syntax Highlighter** for code display

### Development Tools
- **TypeScript** for type safety
- **React Scripts** for build tooling
- **ESLint** for code quality

## 📁 Project Structure

```
frontend/src/
├── components/           # React components
│   ├── chat/            # Chat interface components
│   ├── dashboard/       # System dashboard
│   ├── guardrails/      # Guardrail control panels
│   └── terminal/        # Live terminal component
├── hooks/               # Custom React hooks
│   ├── useApi.ts        # API integration hooks
│   └── useRealTime.ts   # Real-time data hooks
├── services/            # External service integrations
│   ├── api.ts           # Backend API client
│   └── websocket.ts     # WebSocket service
├── themes/              # UI theme configuration
│   └── darkTheme.ts     # Dark theme definition
├── types/               # TypeScript type definitions
│   └── index.ts         # Type definitions
└── App.tsx              # Main application component
```

## 🎯 Key Components

### ChatInterface
Advanced chat component with:
- Real-time message processing visualization
- Detector analysis results display
- Blocking reason explanations
- Processing stage indicators

### GuardrailPanel  
Interactive guardrail management:
- Toggle detectors on/off
- Adjust detection thresholds
- View detector health status
- Quick enable/disable actions

### Terminal
Live terminal with:
- Real-time log streaming
- Interactive command input
- Log filtering and search
- Fullscreen capability

### SystemDashboard
Comprehensive monitoring:
- System health overview
- Performance metrics charts
- Threat level analysis
- Recent events timeline

## 🔗 Backend Integration

The frontend connects to the FastAPI backend via:

### REST API Endpoints
- `GET /health` - System health status
- `GET /api/detectors/` - Available detectors
- `POST /api/chat/message` - Send chat messages
- `GET /api/chat/history` - Chat history

### WebSocket Connections
- Real-time log streaming
- System health updates
- Detector status changes
- Performance metrics

## 🎨 Theme Customization

The dark theme is fully customizable in `src/themes/darkTheme.ts`:

```typescript
const colors = {
  primary: {
    main: '#00D4AA',      // Cyan-green
    dark: '#00A085',      
    light: '#4DFFCC',     
  },
  background: {
    default: '#0A0E1A',   // Very dark blue-black
    paper: '#1A1F2E',     // Dark blue-gray
  },
  // ... more theme configuration
};
```

## 📱 Responsive Design

The interface adapts to different screen sizes:
- **Desktop**: Full sidebar and dashboard layout
- **Tablet**: Collapsible sidebar with optimized spacing
- **Mobile**: Temporary drawer navigation with touch-friendly controls

## 🔧 Configuration

Environment variables can be set in `.env`:

```bash
REACT_APP_API_URL=http://localhost:8000
BROWSER=none
```

## 🚀 Deployment

### Development Build
```bash
npm run build
```

### Production Deployment
The built files in `build/` can be served by any static file server or integrated with the FastAPI backend.

## 🤝 Contributing

1. Follow the existing code style and component patterns
2. Use TypeScript for all new components
3. Maintain responsive design principles
4. Add proper error handling and loading states
5. Include animations for better UX

## 📄 License

This project is part of the AI Safety System and follows the same licensing as the parent project.

---

**🛡️ AI Safety System** - Protecting AI interactions with style and intelligence.