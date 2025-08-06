import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  CssBaseline,
  ThemeProvider,
  Typography,
  TextField,
  IconButton,
  Switch,
  Chip,
  Card,
  CardContent,
  LinearProgress,
  Tooltip,
  Fade,
  Collapse,
  Alert,
  MenuItem,
  Button,
} from '@mui/material';
import {
  Send,
  Terminal,
  Download,
  Cpu,
  HardDrive,
  Zap,
  CheckCircle,
  AlertCircle,
  X,
  Search,
  Filter,
  ArrowDown,
  TestTube,
} from 'lucide-react';
import { Shield } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster, toast } from 'react-hot-toast';

// Theme and services
import { darkTheme } from '../themes/darkTheme';
import { useApi, useSystemHealth, useDetectors, useChat } from '../hooks/useApi';
import { useRealTimeLogs } from '../hooks/useRealTime';
import { useProviders } from '../hooks/useProviders';
import { ollamaService, SystemInfo, ModelRecommendation, OllamaModel } from '../services/ollama';
import { ollamaDownloadService, DownloadProgress } from '../services/ollamaDownload';
import GuardrailsConfig from './guardrails/GuardrailsConfig';
import ProvidersConfig from './providers/ProvidersConfig';
import AnalyticsOverview from './analytics/AnalyticsOverview';
import GuardrailAnalyticsDashboard from './analytics/GuardrailAnalyticsDashboard';
import AdvancedTestingPlayground from './testing/AdvancedTestingPlayground';
import ChatGPTInterface from './chat/ChatGPTInterface';
import GPUAcceleration from './gpu/GPUAcceleration';
import DistributedProcessing from './distributed/DistributedProcessing';
import DocsPage from './docs/DocsPage';
import LogoutButton from './auth/LogoutButton';

// Linear-inspired minimal theme
const minimalTheme = {
  ...darkTheme,
  components: {
    ...darkTheme.components,
    MuiCard: {
      styleOverrides: {
        root: {
          background: 'rgba(255, 255, 255, 0.02)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '12px',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(0, 212, 170, 0.2)',
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            background: 'rgba(255, 255, 255, 0.02)',
            border: 'none',
            borderRadius: '8px',
            '&:hover': {
              background: 'rgba(255, 255, 255, 0.04)',
            },
            '&.Mui-focused': {
              background: 'rgba(255, 255, 255, 0.06)',
              boxShadow: '0 0 0 1px rgba(0, 212, 170, 0.3)',
            },
          },
        },
      },
    },
  },
};

const AuthenticatedApp: React.FC = () => {
  // Core state
  const [activeTab, setActiveTab] = useState('chat');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [selectedDetectors, setSelectedDetectors] = useState<string[]>(['toxicity']);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Enhanced hooks - providing default parameters to avoid errors
  const { detectors, selectedDetectors: hookSelectedDetectors, updateDetectorConfig } = useDetectors();
  const { clearHistory } = useChat('default');
  const { providers, enabledProviders } = useProviders();

  // Mock data for demonstration
  const [messages, setMessages] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [connectedProviders] = useState([
    { id: 'openai', display_name: 'OpenAI GPT', status: 'connected' }
  ]);
  const [selectedProvider, setSelectedProvider] = useState('openai');

  const handleSendMessage = async (message: string, provider: string, detectorConfig: any) => {
    // Mock message handling - replace with actual implementation
    console.log('Sending message:', { message, provider, detectorConfig });
  };

  // Navigation
  const navigationItems = [
    { id: 'chat', label: 'Chat', icon: '💬' },
    { id: 'guardrails', label: 'Guardrails', icon: '🛡️' },
    { id: 'providers', label: 'Providers', icon: '🔌' },
    { id: 'analytics', label: 'Analytics', icon: '📊' },
    { id: 'testing', label: 'Testing', icon: '🧪' },
    { id: 'gpu', label: 'GPU', icon: '🚀' },
    { id: 'distributed', label: 'Distributed', icon: '🌐' },
    { id: 'docs', label: 'Documentation', icon: '📚' },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return (
          <ChatGPTInterface
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            selectedProvider={selectedProvider}
            connectedProviders={connectedProviders}
            onProviderChange={setSelectedProvider}
            detectorConfig={{}}
          />
        );
      case 'guardrails':
        return <GuardrailsConfig />;
      case 'providers':
        return <ProvidersConfig />;
      case 'analytics':
        return <GuardrailAnalyticsDashboard />;
      case 'testing':
        return <AdvancedTestingPlayground />;
      case 'gpu':
        return <GPUAcceleration />;
      case 'distributed':
        return <DistributedProcessing />;
      case 'docs':
        return <DocsPage />;
      default:
        return <ChatGPTInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          selectedProvider={selectedProvider}
          connectedProviders={connectedProviders}
          onProviderChange={setSelectedProvider}
          detectorConfig={{}}
        />;
    }
  };

  return (
    <ThemeProvider theme={minimalTheme}>
      <CssBaseline />
      <Box sx={{
        height: '100vh',
        background: 'linear-gradient(135deg, #0A0E1A 0%, #1A1F2E 100%)',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <Box sx={{
          height: '64px',
          background: 'rgba(255, 255, 255, 0.02)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 3,
          position: 'sticky',
          top: 0,
          zIndex: 1000,
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Shield sx={{ color: '#00D4AA', fontSize: 28 }} />
            <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600 }}>
              AI Safety System
            </Typography>
          </Box>
          
          <LogoutButton variant="icon" showUserInfo={true} />
        </Box>

        <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Sidebar */}
          <Box sx={{
            width: sidebarCollapsed ? '60px' : '240px',
            background: 'rgba(255, 255, 255, 0.02)',
            backdropFilter: 'blur(20px)',
            borderRight: '1px solid rgba(255, 255, 255, 0.06)',
            transition: 'width 0.3s ease',
            display: 'flex',
            flexDirection: 'column',
          }}>
            {/* Navigation */}
            <Box sx={{ p: 2 }}>
              {navigationItems.map((item) => (
                <Box
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                    p: 2,
                    mb: 1,
                    borderRadius: 2,
                    cursor: 'pointer',
                    background: activeTab === item.id 
                      ? 'rgba(0, 212, 170, 0.1)' 
                      : 'transparent',
                    border: activeTab === item.id 
                      ? '1px solid rgba(0, 212, 170, 0.3)'
                      : '1px solid transparent',
                    color: activeTab === item.id ? '#00D4AA' : 'rgba(255, 255, 255, 0.7)',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      background: 'rgba(0, 212, 170, 0.05)',
                      color: '#00D4AA',
                    },
                  }}
                >
                  <span style={{ fontSize: '20px' }}>{item.icon}</span>
                  {!sidebarCollapsed && (
                    <Typography sx={{ fontWeight: 500, fontSize: '14px' }}>
                      {item.label}
                    </Typography>
                  )}
                </Box>
              ))}
            </Box>

            {/* Collapse Toggle */}
            <Box sx={{ mt: 'auto', p: 2, borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
              <IconButton
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                sx={{
                  color: 'rgba(255, 255, 255, 0.7)',
                  width: '100%',
                  '&:hover': {
                    color: '#00D4AA',
                    background: 'rgba(0, 212, 170, 0.1)',
                  },
                }}
              >
                {sidebarCollapsed ? '→' : '←'}
              </IconButton>
            </Box>
          </Box>

          {/* Main Content */}
          <Box sx={{
            flex: 1,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}>
            <Box sx={{ flex: 1, p: 3, overflow: 'auto' }}>
              {renderContent()}
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Toast Notifications */}
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: 'rgba(0, 0, 0, 0.8)',
            color: '#fff',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(10px)',
          },
        }}
      />
    </ThemeProvider>
  );
};

export default AuthenticatedApp;