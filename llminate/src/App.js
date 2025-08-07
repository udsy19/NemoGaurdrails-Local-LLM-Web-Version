import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate
} from 'react-router-dom';
import {
  ThemeProvider,
  CssBaseline,
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Chip,
} from '@mui/material';
import {
  Dashboard,
  People,
  Shield,
  Assessment,
} from '@mui/icons-material';

import dashboardTheme from './theme';
import MainDashboard from './components/dashboard/MainDashboard';
import UserDashboard from './components/dashboard/UserDashboard';
// Debug components (can be removed in production)
import WebSocketDebugger from './components/debug/WebSocketDebugger';
import TestDashboard from './components/debug/TestDashboard';
import { useWebSocket } from './hooks/useWebSocket';

function App() {
  const { isConnected, connectionStatus } = useWebSocket();

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'success';
      case 'connecting':
        return 'warning';
      case 'disconnected':
        return 'error';
      default:
        return 'default';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'disconnected':
        return 'Disconnected';
      default:
        return 'Unknown';
    }
  };

  return (
    <ThemeProvider theme={dashboardTheme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
          {/* Navigation Bar */}
          <AppBar 
            position="static" 
            elevation={0}
            sx={{ 
              backgroundColor: 'background.paper',
              borderBottom: 1,
              borderColor: 'divider',
            }}
          >
            <Toolbar>
              <Shield sx={{ mr: 2, color: 'primary.main' }} />
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                LLMinate Security Analytics
              </Typography>
              
              <Button
                color="inherit"
                startIcon={<Dashboard />}
                href="/main"
                sx={{ mr: 2 }}
              >
                CISO Dashboard
              </Button>
              
              <Button
                color="inherit"
                startIcon={<People />}
                href="/users"
                sx={{ mr: 2 }}
              >
                User Analytics
              </Button>
              
              {/* Debug buttons - remove in production */}
              {process.env.NODE_ENV === 'development' && (
                <>
                  <Button
                    color="inherit"
                    startIcon={<Assessment />}
                    href="/debug"
                    sx={{ mr: 1, fontSize: '0.8rem' }}
                    size="small"
                  >
                    Debug
                  </Button>
                  <Button
                    color="inherit"
                    startIcon={<Assessment />}
                    href="/test"
                    sx={{ mr: 2, fontSize: '0.8rem' }}
                    size="small"
                  >
                    Test
                  </Button>
                </>
              )}
              
              <Chip
                label={getConnectionStatusText()}
                color={getConnectionStatusColor()}
                size="small"
                variant="filled"
                icon={<Assessment />}
              />
            </Toolbar>
          </AppBar>

          {/* Main Content */}
          <Box sx={{ 
            flex: 1, 
            width: '100%',
            minHeight: 'calc(100vh - 64px)', // Account for AppBar height
            overflow: 'auto'
          }}>
            <Routes>
              <Route path="/main" element={<MainDashboard />} />
              <Route path="/users" element={<UserDashboard />} />
              {/* Debug routes - only in development */}
              {process.env.NODE_ENV === 'development' && (
                <>
                  <Route path="/debug" element={<WebSocketDebugger />} />
                  <Route path="/test" element={<TestDashboard />} />
                </>
              )}
              <Route path="/" element={<Navigate to="/main" replace />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
