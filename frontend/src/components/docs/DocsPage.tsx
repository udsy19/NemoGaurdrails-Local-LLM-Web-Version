import React, { useState, Suspense } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Breadcrumbs,
  Link,
  Chip,
  Paper,
  CircularProgress,
} from '@mui/material';
import {
  Description as DocsIcon,
  Key as KeyIcon,
  PlayArrow as StartIcon,
  Code as CodeIcon,
  IntegrationInstructions as IntegrateIcon,
  Security as SecurityIcon,
  Api as ApiIcon,
  Settings as ConfigIcon,
  NavigateNext as NavigateNextIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

// Lazy load documentation subpages for better performance
const ApiKeySetup = React.lazy(() => import('./pages/ApiKeySetup'));
const ApplicationUsage = React.lazy(() => import('./pages/ApplicationUsage'));
const PythonProjectSetup = React.lazy(() => import('./pages/PythonProjectSetup'));
const GuardrailsIntegration = React.lazy(() => import('./pages/GuardrailsIntegration'));
const AdvancedConfiguration = React.lazy(() => import('./pages/AdvancedConfiguration'));
const ApiReference = React.lazy(() => import('./pages/ApiReference'));

interface DocsPageProps {
  onNavigate?: (page: string) => void;
}

interface DocSection {
  id: string;
  title: string;
  description: string;
  icon: React.ReactElement;
  component: React.ComponentType;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  estimatedTime: string;
}

const docSections: DocSection[] = [
  {
    id: 'api-key-setup',
    title: '1. API Key Configuration',
    description: 'Set up your API keys for OpenAI, Anthropic, Google Gemini, and Azure OpenAI',
    icon: <KeyIcon />,
    component: ApiKeySetup,
    difficulty: 'Beginner',
    estimatedTime: '5 min'
  },
  {
    id: 'application-usage',
    title: '2. Using the Application',
    description: 'Learn how to use the web interface, configure guardrails, and test providers',
    icon: <StartIcon />,
    component: ApplicationUsage,
    difficulty: 'Beginner',
    estimatedTime: '10 min'
  },
  {
    id: 'python-project-setup',
    title: '3. Setting Up Your First Project',
    description: 'Create a new Python project and install the necessary dependencies',
    icon: <CodeIcon />,
    component: PythonProjectSetup,
    difficulty: 'Intermediate',
    estimatedTime: '15 min'
  },
  {
    id: 'guardrails-integration',
    title: '4. Integrating Guardrails',
    description: 'Add AI safety guardrails to your application with code examples for multiple languages',
    icon: <IntegrateIcon />,
    component: GuardrailsIntegration,
    difficulty: 'Intermediate',
    estimatedTime: '20 min'
  },
  {
    id: 'advanced-configuration',
    title: '5. Advanced Configuration',
    description: 'Custom detectors, thresholds, and enterprise deployment options',
    icon: <ConfigIcon />,
    component: AdvancedConfiguration,
    difficulty: 'Advanced',
    estimatedTime: '30 min'
  },
  {
    id: 'api-reference',
    title: '6. API Reference',
    description: 'Complete API documentation with examples and response schemas',
    icon: <ApiIcon />,
    component: ApiReference,
    difficulty: 'Advanced',
    estimatedTime: '45 min'
  }
];

const DocsPage: React.FC<DocsPageProps> = ({ onNavigate }) => {
  const [selectedSection, setSelectedSection] = useState<string | null>(null);

  const handleSectionSelect = (sectionId: string) => {
    setSelectedSection(sectionId);
  };

  const handleBackToOverview = () => {
    setSelectedSection(null);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner': return '#10b981';
      case 'Intermediate': return '#f59e0b';
      case 'Advanced': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const selectedSectionData = selectedSection 
    ? docSections.find(section => section.id === selectedSection)
    : null;

  if (selectedSection && selectedSectionData) {
    const ComponentToRender = selectedSectionData.component;
    
    return (
      <Box sx={{ minHeight: '500px', maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {/* Header with breadcrumbs */}
        <Paper sx={{ 
          p: 2, 
          background: 'rgba(255, 255, 255, 0.02)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: 0
        }}>
          <Breadcrumbs 
            separator={<NavigateNextIcon fontSize="small" sx={{ color: '#6b7280' }} />}
            sx={{ mb: 1 }}
          >
            <Link
              component="button"
              variant="body2"
              onClick={handleBackToOverview}
              sx={{ 
                color: '#6b7280',
                textDecoration: 'none',
                '&:hover': { color: '#00D4AA' }
              }}
            >
              Documentation
            </Link>
            <Typography variant="body2" sx={{ color: '#ffffff' }}>
              {selectedSectionData.title}
            </Typography>
          </Breadcrumbs>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ color: '#00D4AA' }}>
              {selectedSectionData.icon}
            </Box>
            <Typography variant="h5" sx={{ color: '#ffffff', fontWeight: 600 }}>
              {selectedSectionData.title}
            </Typography>
            <Chip
              label={selectedSectionData.difficulty}
              size="small"
              sx={{
                backgroundColor: getDifficultyColor(selectedSectionData.difficulty) + '20',
                color: getDifficultyColor(selectedSectionData.difficulty),
                border: `1px solid ${getDifficultyColor(selectedSectionData.difficulty)}`,
                fontSize: '0.7rem'
              }}
            />
            <Chip
              label={selectedSectionData.estimatedTime}
              size="small"
              variant="outlined"
              sx={{
                borderColor: '#6b7280',
                color: '#6b7280',
                fontSize: '0.7rem'
              }}
            />
          </Box>
        </Paper>

        {/* Content */}
        <Box sx={{ flex: 1, overflow: 'auto' }}>
          <Suspense fallback={
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              height: '300px',
              flexDirection: 'column',
              gap: 2
            }}>
              <CircularProgress size={40} sx={{ color: '#00D4AA' }} />
              <Typography variant="body2" sx={{ color: '#6b7280' }}>
                Loading documentation...
              </Typography>
            </Box>
          }>
            <ComponentToRender />
          </Suspense>
        </Box>
      </Box>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Box sx={{ p: 4, maxWidth: '1200px', mx: 'auto' }}>
        {/* Header */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <SecurityIcon sx={{ fontSize: 48, color: '#00D4AA', mb: 2 }} />
          <Typography variant="h3" sx={{ color: '#ffffff', fontWeight: 700, mb: 2 }}>
            AI Guardrails Documentation
          </Typography>
          <Typography variant="h6" sx={{ color: '#a1a1aa', maxWidth: '600px', mx: 'auto' }}>
            Complete guide to integrating AI safety guardrails into your applications.
            Protect your users from toxic content, prompt injection, and privacy violations.
          </Typography>
        </Box>

        {/* Quick Stats */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: 2, 
          mb: 4 
        }}>
          <Card sx={{ 
            background: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            textAlign: 'center'
          }}>
            <CardContent>
              <Typography variant="h4" sx={{ color: '#10b981', fontWeight: 'bold' }}>
                6
              </Typography>
              <Typography variant="body2" sx={{ color: '#6b7280' }}>
                Documentation Sections
              </Typography>
            </CardContent>
          </Card>
          
          <Card sx={{ 
            background: 'rgba(0, 212, 170, 0.1)',
            border: '1px solid rgba(0, 212, 170, 0.2)',
            textAlign: 'center'
          }}>
            <CardContent>
              <Typography variant="h4" sx={{ color: '#00D4AA', fontWeight: 'bold' }}>
                5
              </Typography>
              <Typography variant="body2" sx={{ color: '#6b7280' }}>
                Programming Languages
              </Typography>
            </CardContent>
          </Card>
          
          <Card sx={{ 
            background: 'rgba(245, 158, 11, 0.1)',
            border: '1px solid rgba(245, 158, 11, 0.2)',
            textAlign: 'center'
          }}>
            <CardContent>
              <Typography variant="h4" sx={{ color: '#f59e0b', fontWeight: 'bold' }}>
                15+
              </Typography>
              <Typography variant="body2" sx={{ color: '#6b7280' }}>
                Code Examples
              </Typography>
            </CardContent>
          </Card>
          
          <Card sx={{ 
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            textAlign: 'center'
          }}>
            <CardContent>
              <Typography variant="h4" sx={{ color: '#ef4444', fontWeight: 'bold' }}>
                6
              </Typography>
              <Typography variant="body2" sx={{ color: '#6b7280' }}>
                AI Safety Detectors
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Documentation Sections */}
        <Typography variant="h4" sx={{ color: '#ffffff', fontWeight: 600, mb: 3 }}>
          Getting Started Guide
        </Typography>

        <Box sx={{ display: 'grid', gap: 2 }}>
          {docSections.map((section, index) => (
            <motion.div
              key={section.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
            >
              <Card sx={{ 
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                '&:hover': {
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(0, 212, 170, 0.3)',
                  transform: 'translateY(-2px)',
                },
                transition: 'all 0.2s ease-in-out',
                cursor: 'pointer'
              }}>
                <CardContent>
                  <ListItemButton 
                    onClick={() => handleSectionSelect(section.id)}
                    sx={{ 
                      borderRadius: 1,
                      '&:hover': { backgroundColor: 'transparent' }
                    }}
                  >
                    <ListItemIcon sx={{ color: '#00D4AA', minWidth: 48 }}>
                      {section.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600 }}>
                            {section.title}
                          </Typography>
                          <Chip
                            label={section.difficulty}
                            size="small"
                            sx={{
                              backgroundColor: getDifficultyColor(section.difficulty) + '20',
                              color: getDifficultyColor(section.difficulty),
                              border: `1px solid ${getDifficultyColor(section.difficulty)}`,
                              fontSize: '0.7rem'
                            }}
                          />
                          <Chip
                            label={section.estimatedTime}
                            size="small"
                            variant="outlined"
                            sx={{
                              borderColor: '#6b7280',
                              color: '#6b7280',
                              fontSize: '0.7rem'
                            }}
                          />
                        </Box>
                      }
                      secondary={
                        <Typography variant="body2" sx={{ color: '#a1a1aa', mt: 1 }}>
                          {section.description}
                        </Typography>
                      }
                    />
                  </ListItemButton>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </Box>

        {/* Footer */}
        <Box sx={{ mt: 6, textAlign: 'center' }}>
          <Typography variant="body2" sx={{ color: '#6b7280' }}>
            Need help? Check out our{' '}
            <Link 
              href="#" 
              sx={{ 
                color: '#00D4AA',
                textDecoration: 'none',
                '&:hover': { textDecoration: 'underline' }
              }}
            >
              community forum
            </Link>{' '}
            or{' '}
            <Link 
              href="#" 
              sx={{ 
                color: '#00D4AA',
                textDecoration: 'none',
                '&:hover': { textDecoration: 'underline' }
              }}
            >
              contact support
            </Link>
          </Typography>
        </Box>
      </Box>
    </motion.div>
  );
};

export default DocsPage;