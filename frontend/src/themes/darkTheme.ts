import { createTheme } from '@mui/material/styles';

// Custom color palette for the AI Safety System
const colors = {
  primary: {
    main: '#00D4AA',      // Cyan-green
    dark: '#00A085',      // Darker cyan-green
    light: '#4DFFCC',     // Lighter cyan-green
    contrastText: '#000000'
  },
  secondary: {
    main: '#FF6B6B',      // Coral red for alerts
    dark: '#CC5555',      // Darker red
    light: '#FF9999',     // Lighter red
    contrastText: '#FFFFFF'
  },
  error: {
    main: '#FF3D71',      // Vibrant red
    dark: '#CC1F47',      // Darker red
    light: '#FF7AA3',     // Lighter red
  },
  warning: {
    main: '#FFB800',      // Golden yellow
    dark: '#CC9200',      // Darker yellow
    light: '#FFCC4D',     // Lighter yellow
  },
  success: {
    main: '#00D4AA',      // Same as primary
    dark: '#00A085',      // Darker
    light: '#4DFFCC',     // Lighter
  },
  background: {
    default: '#0A0E1A',   // Very dark blue-black
    paper: '#1A1F2E',     // Dark blue-gray
    elevation1: '#242938', // Slightly lighter for elevated surfaces
    elevation2: '#2D3441', // Even lighter for higher elevation
  },
  surface: {
    main: '#1E2332',      // Main surface color
    variant: '#2A2F3E',   // Variant surface
    disabled: '#3A3F4E',  // Disabled surface
  },
  text: {
    primary: '#FFFFFF',    // Pure white for primary text
    secondary: '#A8B2D1',  // Light blue-gray for secondary text
    disabled: '#6B7280',   // Gray for disabled text
    hint: '#9CA3AF',       // Lighter gray for hints
  },
  divider: '#374151',      // Gray divider
  // Custom colors for specific components
  terminal: {
    background: '#0D1117', // GitHub dark terminal background
    text: '#C9D1D9',       // Light gray text
    cursor: '#00D4AA',     // Cyan cursor
    selection: '#264F78',  // Blue selection
  },
  guardrail: {
    active: '#00D4AA',     // Active guardrail color
    inactive: '#6B7280',   // Inactive guardrail color
    danger: '#FF3D71',     // Danger state
    warning: '#FFB800',    // Warning state
  },
  gradient: {
    primary: 'linear-gradient(135deg, #00D4AA 0%, #007A6B 100%)',
    secondary: 'linear-gradient(135deg, #FF6B6B 0%, #CC3333 100%)',
    background: 'linear-gradient(135deg, #0A0E1A 0%, #1A1F2E 100%)',
    card: 'linear-gradient(135deg, #1A1F2E 0%, #242938 100%)',
  }
};

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    ...colors,
  },
  typography: {
    fontFamily: '"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
      background: colors.gradient.primary,
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text',
    },
    h2: {
      fontSize: '2rem',
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
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          textTransform: 'none',
          fontWeight: 600,
          padding: '10px 24px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 4px 20px rgba(0, 212, 170, 0.25)',
            transform: 'translateY(-2px)',
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
            backgroundColor: `${colors.primary.main}20`,
            borderColor: colors.primary.light,
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '12px',
            backgroundColor: colors.background.paper,
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: colors.primary.main,
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: colors.primary.main,
              borderWidth: '2px',
            },
          },
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
            transform: 'translateY(-2px)',
            boxShadow: '0 8px 40px rgba(0, 212, 170, 0.15)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          fontWeight: 500,
        },
        filled: {
          backgroundColor: colors.surface.variant,
          color: colors.text.primary,
          '&.MuiChip-colorPrimary': {
            background: colors.gradient.primary,
            color: colors.primary.contrastText,
          },
        },
      },
    },
    MuiSwitch: {
      styleOverrides: {
        root: {
          '& .MuiSwitch-switchBase.Mui-checked': {
            color: colors.primary.main,
            '& + .MuiSwitch-track': {
              backgroundColor: colors.primary.main,
            },
          },
        },
      },
    },
  },
  shape: {
    borderRadius: 12,
  },
  spacing: 8,
});

export default darkTheme;