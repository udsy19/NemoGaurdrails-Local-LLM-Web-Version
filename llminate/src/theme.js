import { createTheme } from '@mui/material/styles';

// Custom color palette adapted from the main AI Safety System
// Optimized for dashboard viewing with enhanced readability
const colors = {
  primary: {
    main: '#00D4AA',      // Cyan-green for primary actions
    dark: '#00A085',      // Darker cyan-green
    light: '#4DFFCC',     // Lighter cyan-green
    contrastText: '#000000'
  },
  secondary: {
    main: '#FF6B6B',      // Coral red for alerts and warnings
    dark: '#CC5555',      // Darker red
    light: '#FF9999',     // Lighter red
    contrastText: '#FFFFFF'
  },
  error: {
    main: '#FF3D71',      // High-risk indicators
    dark: '#CC1F47',
    light: '#FF7AA3',
  },
  warning: {
    main: '#FFB800',      // Medium-risk indicators
    dark: '#CC9200',
    light: '#FFCC4D',
  },
  success: {
    main: '#00D4AA',      // Low-risk / safe indicators
    dark: '#00A085',
    light: '#4DFFCC',
  },
  info: {
    main: '#3B82F6',      // Information and analytics
    dark: '#1D4ED8',
    light: '#60A5FA',
  },
  background: {
    default: '#0A0E1A',   // Main dashboard background
    paper: '#1A1F2E',     // Card and panel backgrounds
    elevation1: '#242938', // Elevated surfaces
    elevation2: '#2D3441', // Higher elevation
  },
  surface: {
    main: '#1E2332',      // Main surface color
    variant: '#2A2F3E',   // Variant surface
    disabled: '#3A3F4E',  // Disabled surface
  },
  text: {
    primary: '#FFFFFF',    // Primary dashboard text
    secondary: '#A8B2D1',  // Secondary text and labels
    disabled: '#6B7280',   // Disabled text
    hint: '#9CA3AF',       // Hints and placeholders
  },
  divider: '#374151',
  
  // Dashboard-specific colors
  dashboard: {
    riskHigh: '#FF3D71',      // High risk (70-100)
    riskMedium: '#FFB800',    // Medium risk (40-69)
    riskLow: '#00D4AA',       // Low risk (0-39)
    threat: '#FF6B6B',        // Active threats
    blocked: '#FF8A80',       // Blocked requests
    allowed: '#81C784',       // Allowed requests
    exfiltration: '#E91E63',  // Data exfiltration
    injection: '#FF5722',     // Prompt injection
    toxicity: '#9C27B0',      // Toxicity
  },
  
  // Chart colors for consistency
  chart: {
    primary: '#00D4AA',
    secondary: '#3B82F6',
    tertiary: '#FFB800',
    quaternary: '#FF6B6B',
    grid: '#374151',
    text: '#A8B2D1',
  },
  
  gradient: {
    primary: 'linear-gradient(135deg, #00D4AA 0%, #007A6B 100%)',
    secondary: 'linear-gradient(135deg, #FF6B6B 0%, #CC3333 100%)',
    background: 'linear-gradient(135deg, #0A0E1A 0%, #1A1F2E 100%)',
    card: 'linear-gradient(135deg, #1A1F2E 0%, #242938 100%)',
    risk: 'linear-gradient(135deg, #FF3D71 0%, #FFB800 50%, #00D4AA 100%)',
  }
};

export const dashboardTheme = createTheme({
  palette: {
    mode: 'dark',
    ...colors,
  },
  typography: {
    fontFamily: '"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif',
    h1: {
      fontSize: '2.25rem',
      fontWeight: 700,
      lineHeight: 1.2,
      color: colors.text.primary,
    },
    h2: {
      fontSize: '1.875rem',
      fontWeight: 600,
      lineHeight: 1.3,
      color: colors.text.primary,
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
      color: colors.text.primary,
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 500,
      lineHeight: 1.4,
      color: colors.text.primary,
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 500,
      lineHeight: 1.4,
      color: colors.text.primary,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.4,
      color: colors.text.primary,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
      color: colors.text.primary,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
      color: colors.text.secondary,
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.4,
      color: colors.text.disabled,
    },
    // Dashboard-specific typography
    metric: {
      fontSize: '2rem',
      fontWeight: 700,
      lineHeight: 1.2,
      fontFamily: '"JetBrains Mono", "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, monospace',
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background: colors.gradient.background,
          backgroundAttachment: 'fixed',
          fontFamily: '"Inter", sans-serif',
        },
        '*::-webkit-scrollbar': {
          width: '8px',
        },
        '*::-webkit-scrollbar-track': {
          background: colors.background.paper,
        },
        '*::-webkit-scrollbar-thumb': {
          background: colors.primary.main,
          borderRadius: '4px',
        },
        '*::-webkit-scrollbar-thumb:hover': {
          background: colors.primary.dark,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          background: colors.gradient.card,
          border: `1px solid ${colors.divider}`,
          backdropFilter: 'blur(10px)',
        },
        elevation1: {
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
        },
        elevation2: {
          boxShadow: '0 8px 40px rgba(0, 0, 0, 0.25)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
          background: colors.gradient.card,
          border: `1px solid ${colors.divider}`,
          backdropFilter: 'blur(10px)',
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: '0 8px 40px rgba(0, 212, 170, 0.1)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          textTransform: 'none',
          fontWeight: 600,
          padding: '8px 16px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 4px 20px rgba(0, 212, 170, 0.25)',
            transform: 'translateY(-1px)',
          },
        },
        contained: {
          background: colors.gradient.primary,
          '&:hover': {
            background: colors.gradient.primary,
            filter: 'brightness(1.1)',
          },
        },
        outlined: {
          borderColor: colors.primary.main,
          color: colors.primary.main,
          '&:hover': {
            backgroundColor: `${colors.primary.main}15`,
            borderColor: colors.primary.light,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          fontWeight: 500,
          fontSize: '0.75rem',
        },
        filled: {
          backgroundColor: colors.surface.variant,
          color: colors.text.primary,
        },
        colorError: {
          backgroundColor: colors.dashboard.riskHigh,
          color: '#FFFFFF',
        },
        colorWarning: {
          backgroundColor: colors.dashboard.riskMedium,
          color: '#000000',
        },
        colorSuccess: {
          backgroundColor: colors.dashboard.riskLow,
          color: '#000000',
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          height: 8,
          borderRadius: 4,
          backgroundColor: colors.surface.variant,
        },
        bar: {
          borderRadius: 4,
          background: colors.gradient.primary,
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          border: 'none',
          fontSize: '0.875rem',
        },
        standardError: {
          backgroundColor: `${colors.error.main}20`,
          color: colors.error.light,
          '& .MuiAlert-icon': {
            color: colors.error.main,
          },
        },
        standardWarning: {
          backgroundColor: `${colors.warning.main}20`,
          color: colors.warning.light,
          '& .MuiAlert-icon': {
            color: colors.warning.main,
          },
        },
        standardInfo: {
          backgroundColor: `${colors.info.main}20`,
          color: colors.info.light,
          '& .MuiAlert-icon': {
            color: colors.info.main,
          },
        },
        standardSuccess: {
          backgroundColor: `${colors.success.main}20`,
          color: colors.success.light,
          '& .MuiAlert-icon': {
            color: colors.success.main,
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderColor: colors.divider,
          padding: '12px 16px',
        },
        head: {
          backgroundColor: colors.background.elevation1,
          color: colors.text.primary,
          fontWeight: 600,
          fontSize: '0.875rem',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: colors.background.paper,
          border: `1px solid ${colors.divider}`,
        },
      },
    },
  },
  shape: {
    borderRadius: 12,
  },
  spacing: 8,
});

export default dashboardTheme;