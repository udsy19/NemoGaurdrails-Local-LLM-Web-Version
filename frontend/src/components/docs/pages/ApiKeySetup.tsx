import React from 'react';
import {
  Box,
  Typography,
  Alert,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Chip,
  Step,
  Stepper,
  StepLabel,
  Paper,
} from '@mui/material';
import {
  Key as KeyIcon,
  Security as SecurityIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import CodeBlock from '../components/CodeBlock';

const ApiKeySetup: React.FC = () => {
  const steps = [
    'Obtain API Keys from Providers',
    'Configure Environment Variables',
    'Set Up Keys in Application',
    'Test Provider Connections'
  ];

  const providerInstructions = [
    {
      name: 'OpenAI',
      icon: '🤖',
      steps: [
        'Visit https://platform.openai.com/api-keys',
        'Sign in to your OpenAI account',
        'Click "Create new secret key"',
        'Copy the generated API key',
        'Store it securely (it won\'t be shown again)'
      ],
      envVar: 'OPENAI_API_KEY',
      pricing: 'Pay-per-use',
      models: ['GPT-4o', 'GPT-4o Mini', 'GPT-4 Turbo', 'GPT-3.5 Turbo']
    },
    {
      name: 'Anthropic Claude',
      icon: '🧠',
      steps: [
        'Go to https://console.anthropic.com/settings/keys',
        'Log into your Anthropic account',
        'Click "Create Key"',
        'Name your key and set permissions',
        'Copy the generated key immediately'
      ],
      envVar: 'ANTHROPIC_API_KEY',
      pricing: 'Pay-per-use',
      models: ['Claude 3.5 Sonnet', 'Claude 3 Opus', 'Claude 3 Sonnet', 'Claude 3 Haiku']
    },
    {
      name: 'Google Gemini',
      icon: '💎',
      steps: [
        'Navigate to https://aistudio.google.com/app/apikey',
        'Sign in with your Google account',
        'Click "Create API Key"',
        'Select your Google Cloud project',
        'Copy the generated API key'
      ],
      envVar: 'GOOGLE_API_KEY',
      pricing: 'Free tier available',
      models: ['Gemini 2.0 Flash', 'Gemini 1.5 Pro', 'Gemini 1.5 Flash', 'Gemini 1.0 Pro']
    },
    {
      name: 'Azure OpenAI',
      icon: '☁️',
      steps: [
        'Access Azure Portal at https://portal.azure.com',
        'Navigate to your Azure OpenAI resource',
        'Go to "Keys and Endpoint" section',
        'Copy your API key and endpoint URL',
        'Note your deployment name and API version'
      ],
      envVar: 'AZURE_OPENAI_API_KEY',
      pricing: 'Enterprise pricing',
      models: ['GPT-4o (Azure)', 'GPT-4o Mini (Azure)', 'GPT-4 Turbo (Azure)', 'GPT-3.5 Turbo (Azure)']
    }
  ];

  const envExamples = [
    {
      language: 'bash',
      filename: '.env',
      code: `# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Google Gemini Configuration
GOOGLE_API_KEY=your-google-api-key-here

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your-azure-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Optional: Local Ollama (no API key required)
OLLAMA_BASE_URL=http://localhost:11434`
    },
    {
      language: 'python',
      filename: 'config.py',
      code: `import os
from typing import Optional

class APIConfig:
    """Configuration class for API keys and endpoints."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY: Optional[str] = os.getenv('ANTHROPIC_API_KEY')
    
    # Google Gemini Configuration
    GOOGLE_API_KEY: Optional[str] = os.getenv('GOOGLE_API_KEY')
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: Optional[str] = os.getenv('AZURE_OPENAI_API_KEY')
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_API_VERSION: str = os.getenv('AZURE_OPENAI_API_VERSION', '2024-10-21')
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
    
    # Ollama Configuration (local)
    OLLAMA_BASE_URL: str = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    @classmethod
    def validate_keys(cls) -> dict[str, bool]:
        """Validate which API keys are properly configured."""
        return {
            'openai': bool(cls.OPENAI_API_KEY),
            'anthropic': bool(cls.ANTHROPIC_API_KEY),
            'google': bool(cls.GOOGLE_API_KEY),
            'azure': bool(cls.AZURE_OPENAI_API_KEY and cls.AZURE_OPENAI_ENDPOINT),
            'ollama': True  # Always available locally
        }`
    },
    {
      language: 'javascript',
      filename: 'config.js',
      code: `// API Configuration
const config = {
  // OpenAI Configuration
  openai: {
    apiKey: process.env.OPENAI_API_KEY,
    baseURL: 'https://api.openai.com/v1'
  },
  
  // Anthropic Configuration
  anthropic: {
    apiKey: process.env.ANTHROPIC_API_KEY,
    baseURL: 'https://api.anthropic.com'
  },
  
  // Google Gemini Configuration
  google: {
    apiKey: process.env.GOOGLE_API_KEY,
    baseURL: 'https://generativelanguage.googleapis.com'
  },
  
  // Azure OpenAI Configuration
  azure: {
    apiKey: process.env.AZURE_OPENAI_API_KEY,
    endpoint: process.env.AZURE_OPENAI_ENDPOINT,
    apiVersion: process.env.AZURE_OPENAI_API_VERSION || '2024-10-21',
    deploymentName: process.env.AZURE_OPENAI_DEPLOYMENT_NAME
  },
  
  // Ollama Configuration (local)
  ollama: {
    baseURL: process.env.OLLAMA_BASE_URL || 'http://localhost:11434'
  }
};

// Validation function
function validateConfig() {
  const results = {
    openai: !!config.openai.apiKey,
    anthropic: !!config.anthropic.apiKey,
    google: !!config.google.apiKey,
    azure: !!(config.azure.apiKey && config.azure.endpoint),
    ollama: true
  };
  
  console.log('API Configuration Status:', results);
  return results;
}

module.exports = { config, validateConfig };`
    }
  ];

  return (
    <Box sx={{ p: 4, maxHeight: '100vh', overflow: 'auto' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Introduction */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" sx={{ color: '#ffffff', fontWeight: 700, mb: 2 }}>
            API Key Configuration
          </Typography>
          <Typography variant="body1" sx={{ color: '#a1a1aa', mb: 3, lineHeight: 1.6 }}>
            Before you can use the AI Guardrails system, you'll need to configure API keys for the 
            language model providers you want to use. This guide will walk you through obtaining 
            and setting up API keys for each supported provider.
          </Typography>

          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Security Notice:</strong> Never commit API keys to version control or share them publicly. 
              Always use environment variables or secure configuration management systems in production.
            </Typography>
          </Alert>
        </Box>

        {/* Progress Stepper */}
        <Paper sx={{ 
          p: 3, 
          mb: 4, 
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid rgba(255, 255, 255, 0.06)'
        }}>
          <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
            Setup Process
          </Typography>
          <Stepper activeStep={-1} alternativeLabel>
            {steps.map((label, index) => (
              <Step key={label}>
                <StepLabel sx={{
                  '& .MuiStepLabel-label': { color: '#a1a1aa' },
                  '& .MuiStepIcon-root': { color: '#6b7280' }
                }}>
                  {label}
                </StepLabel>
              </Step>
            ))}
          </Stepper>
        </Paper>

        {/* Provider Instructions */}
        <Typography variant="h5" sx={{ color: '#ffffff', fontWeight: 600, mb: 3 }}>
          Step 1: Obtain API Keys from Providers
        </Typography>

        <Box sx={{ display: 'grid', gap: 3, mb: 4 }}>
          {providerInstructions.map((provider, index) => (
            <motion.div
              key={provider.name}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
            >
              <Card sx={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                '&:hover': {
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(0, 212, 170, 0.3)'
                },
                transition: 'all 0.2s ease-in-out'
              }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Typography variant="h4" sx={{ fontSize: '2rem' }}>
                      {provider.icon}
                    </Typography>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600 }}>
                        {provider.name}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                        <Chip
                          label={provider.pricing}
                          size="small"
                          sx={{
                            backgroundColor: '#00D4AA20',
                            color: '#00D4AA',
                            fontSize: '0.7rem'
                          }}
                        />
                        <Chip
                          label={`${provider.models.length} models`}
                          size="small"
                          variant="outlined"
                          sx={{
                            borderColor: '#6b7280',
                            color: '#6b7280',
                            fontSize: '0.7rem'
                          }}
                        />
                      </Box>
                    </Box>
                  </Box>

                  <Typography variant="body2" sx={{ color: '#a1a1aa', mb: 2 }}>
                    Environment Variable: <code style={{ 
                      color: '#00D4AA', 
                      backgroundColor: 'rgba(0, 212, 170, 0.1)', 
                      padding: '2px 6px', 
                      borderRadius: '4px',
                      fontFamily: 'monospace'
                    }}>
                      {provider.envVar}
                    </code>
                  </Typography>

                  <Typography variant="subtitle2" sx={{ color: '#ffffff', mb: 1 }}>
                    How to get your API key:
                  </Typography>
                  <List dense>
                    {provider.steps.map((step, stepIndex) => (
                      <ListItem key={stepIndex} sx={{ py: 0.5 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <Typography variant="body2" sx={{ 
                            color: '#00D4AA', 
                            fontWeight: 'bold',
                            width: 20,
                            height: 20,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            backgroundColor: 'rgba(0, 212, 170, 0.2)',
                            borderRadius: '50%',
                            fontSize: '0.75rem'
                          }}>
                            {stepIndex + 1}
                          </Typography>
                        </ListItemIcon>
                        <ListItemText 
                          primary={step}
                          primaryTypographyProps={{
                            variant: 'body2',
                            sx: { color: '#e2e8f0' }
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>

                  <Divider sx={{ my: 2, borderColor: 'rgba(255, 255, 255, 0.1)' }} />
                  
                  <Typography variant="subtitle2" sx={{ color: '#ffffff', mb: 1 }}>
                    Available Models:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {provider.models.map((model) => (
                      <Chip
                        key={model}
                        label={model}
                        size="small"
                        variant="outlined"
                        sx={{
                          borderColor: 'rgba(255, 255, 255, 0.2)',
                          color: '#e2e8f0',
                          fontSize: '0.7rem'
                        }}
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </Box>

        {/* Environment Configuration */}
        <Typography variant="h5" sx={{ color: '#ffffff', fontWeight: 600, mb: 3 }}>
          Step 2: Configure Environment Variables
        </Typography>

        <CodeBlock
          examples={envExamples}
          title="Environment Configuration Examples"
          description="Choose the configuration method that best fits your development workflow:"
        />

        {/* Security Best Practices */}
        <Card sx={{
          background: 'rgba(239, 68, 68, 0.05)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          mb: 4
        }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <SecurityIcon sx={{ color: '#ef4444' }} />
              <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600 }}>
                Security Best Practices
              </Typography>
            </Box>
            
            <List>
              <ListItem>
                <ListItemIcon>
                  <WarningIcon sx={{ color: '#f59e0b', fontSize: '1.2rem' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Never hardcode API keys in your source code"
                  secondary="Always use environment variables or secure configuration systems"
                  primaryTypographyProps={{ color: '#ffffff', variant: 'body2' }}
                  secondaryTypographyProps={{ color: '#a1a1aa', variant: 'caption' }}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <VisibilityOffIcon sx={{ color: '#f59e0b', fontSize: '1.2rem' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Add .env files to your .gitignore"
                  secondary="Prevent accidental commits of sensitive information"
                  primaryTypographyProps={{ color: '#ffffff', variant: 'body2' }}
                  secondaryTypographyProps={{ color: '#a1a1aa', variant: 'caption' }}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <KeyIcon sx={{ color: '#f59e0b', fontSize: '1.2rem' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Rotate API keys regularly"
                  secondary="Change your keys periodically and immediately if compromised"
                  primaryTypographyProps={{ color: '#ffffff', variant: 'body2' }}
                  secondaryTypographyProps={{ color: '#a1a1aa', variant: 'caption' }}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <CheckIcon sx={{ color: '#10b981', fontSize: '1.2rem' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Use separate keys for development and production"
                  secondary="Maintain different API keys for different environments"
                  primaryTypographyProps={{ color: '#ffffff', variant: 'body2' }}
                  secondaryTypographyProps={{ color: '#a1a1aa', variant: 'caption' }}
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>

        {/* Next Steps */}
        <Alert severity="info" sx={{ mb: 4 }}>
          <Typography variant="body2">
            <strong>Next:</strong> Once you've configured your API keys, proceed to the 
            "Using the Application" section to learn how to test your provider connections 
            and configure guardrails settings.
          </Typography>
        </Alert>
      </motion.div>
    </Box>
  );
};

export default ApiKeySetup;