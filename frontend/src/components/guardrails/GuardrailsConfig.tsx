import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Slider,
  Switch,
  Alert,
  Divider,
  Grid,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  TextField,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Select,
  MenuItem,
  InputLabel,
  Tab,
  Tabs,
} from '@mui/material';
import {
  Shield,
  Eye,
  Lock,
  MessageSquare,
  CheckCircle,
  Filter,
  RefreshCw,
  Info,
  AlertTriangle,
  Settings,
  Code,
  MessageCircle,
  Plus,
  X,
  ChevronDown,
  Save,
  Upload,
  Download,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import TabPanel from '../common/TabPanel';

interface DetectorConfig {
  name: string;
  displayName: string;
  description: string;
  threshold: number;
  enabled: boolean;
  icon: React.ReactNode;
  color: string;
  defaultThreshold: number;
  customKeywords?: string[];
  blockedWords?: string[];
  allowedDomains?: string[];
  customResponse?: string;
  actionType?: 'block' | 'warn' | 'log';
  severity?: 'low' | 'medium' | 'high';
}

interface GuardrailsConfigProps {
  onConfigChange?: (config: { [key: string]: { enabled: boolean; threshold: number; [key: string]: any } }) => void;
}

const GuardrailsConfig: React.FC<GuardrailsConfigProps> = ({ onConfigChange }) => {
  const [detectors, setDetectors] = useState<DetectorConfig[]>([
    {
      name: 'toxicity',
      displayName: 'Toxicity Detection',
      description: 'Detects harmful, toxic, or offensive content',
      threshold: 0.7,
      enabled: true,
      icon: <Shield size={20} />,
      color: '#ef4444',
      defaultThreshold: 0.7,
      customKeywords: ['hate', 'toxic', 'offensive'],
      blockedWords: ['hate', 'toxic', 'offensive'],
      customResponse: 'This message contains content that may be harmful or offensive.',
      actionType: 'block',
      severity: 'high',
    },
    {
      name: 'pii',
      displayName: 'PII Detection',
      description: 'Identifies and protects personal information',
      threshold: 0.8,
      enabled: true,
      icon: <Lock size={20} />,
      color: '#f59e0b',
      defaultThreshold: 0.8,
      customKeywords: ['email', 'phone', 'ssn', 'credit card'],
      blockedWords: [],
      customResponse: 'Personal information detected. Please remove sensitive data.',
      actionType: 'block',
      severity: 'high',
    },
    {
      name: 'prompt_injection',
      displayName: 'Prompt Injection',
      description: 'Prevents prompt manipulation attacks',
      threshold: 0.5,
      enabled: true,
      icon: <AlertTriangle size={20} />,
      color: '#dc2626',
      defaultThreshold: 0.5,
      customKeywords: ['ignore', 'override', 'system'],
      blockedWords: ['ignore previous', 'override system'],
      customResponse: 'Potential prompt manipulation detected.',
      actionType: 'block',
      severity: 'high',
    },
    {
      name: 'topic',
      displayName: 'Topic Classification',
      description: 'Monitors content topics and categories',
      threshold: 0.7,
      enabled: true,
      icon: <MessageSquare size={20} />,
      color: '#3b82f6',
      defaultThreshold: 0.7,
      customKeywords: ['politics', 'religion', 'adult content'],
      blockedWords: [],
      customResponse: 'This topic is restricted in the current context.',
      actionType: 'warn',
      severity: 'medium',
    },
    {
      name: 'fact_check',
      displayName: 'Fact Checking',
      description: 'Verifies claims and factual accuracy',
      threshold: 0.5,
      enabled: false,
      icon: <CheckCircle size={20} />,
      color: '#10b981',
      defaultThreshold: 0.5,
      customKeywords: ['claim', 'fact', 'scientific'],
      blockedWords: [],
      customResponse: 'This claim requires fact-checking verification.',
      actionType: 'warn',
      severity: 'medium',
    },
    {
      name: 'spam',
      displayName: 'Spam Detection',
      description: 'Filters spam and low-quality content',
      threshold: 0.6,
      enabled: true,
      icon: <Filter size={20} />,
      color: '#8b5cf6',
      defaultThreshold: 0.6,
      customKeywords: ['spam', 'promotion', 'advertisement'],
      blockedWords: ['buy now', 'free money', 'click here'],
      customResponse: 'This content appears to be spam or promotional.',
      actionType: 'log',
      severity: 'low',
    },
  ]);

  const [loading, setLoading] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [selectedDetector, setSelectedDetector] = useState<DetectorConfig | null>(null);
  const [advancedDialogOpen, setAdvancedDialogOpen] = useState(false);
  const [newKeyword, setNewKeyword] = useState('');
  const [newBlockedWord, setNewBlockedWord] = useState('');

  // Notify parent component of config changes
  useEffect(() => {
    if (onConfigChange) {
      const config = detectors.reduce((acc, detector) => {
        acc[detector.name] = {
          enabled: detector.enabled,
          threshold: detector.threshold,
          customKeywords: detector.customKeywords || [],
          blockedWords: detector.blockedWords || [],
          customResponse: detector.customResponse || '',
          actionType: detector.actionType || 'block',
          severity: detector.severity || 'medium',
        };
        return acc;
      }, {} as { [key: string]: { enabled: boolean; threshold: number; [key: string]: any } });
      
      onConfigChange(config);
    }
  }, [detectors, onConfigChange]);

  const handleThresholdChange = (detectorName: string, newThreshold: number) => {
    setDetectors(prev => 
      prev.map(detector => 
        detector.name === detectorName 
          ? { ...detector, threshold: newThreshold }
          : detector
      )
    );
  };

  const handleToggleDetector = (detectorName: string, enabled: boolean) => {
    setDetectors(prev => 
      prev.map(detector => 
        detector.name === detectorName 
          ? { ...detector, enabled }
          : detector
      )
    );
    
    toast.success(`${detectors.find(d => d.name === detectorName)?.displayName} ${enabled ? 'enabled' : 'disabled'}`);
  };

  const resetToDefaults = () => {
    setDetectors(prev => 
      prev.map(detector => ({
        ...detector,
        threshold: detector.defaultThreshold,
        enabled: detector.name !== 'fact_check', // fact_check disabled by default
        customKeywords: detector.customKeywords || [],
        blockedWords: detector.blockedWords || [],
        customResponse: detector.customResponse || '',
        actionType: detector.actionType || 'block',
        severity: detector.severity || 'medium',
      }))
    );
    toast.success('Reset to default settings');
  };

  const handleAdvancedConfig = (detector: DetectorConfig) => {
    setSelectedDetector(detector);
    setAdvancedDialogOpen(true);
  };

  const handleAddKeyword = () => {
    if (newKeyword.trim() && selectedDetector) {
      const updatedDetectors = detectors.map(d => 
        d.name === selectedDetector.name 
          ? { ...d, customKeywords: [...(d.customKeywords || []), newKeyword.trim()] }
          : d
      );
      setDetectors(updatedDetectors);
      setNewKeyword('');
    }
  };

  const handleRemoveKeyword = (keyword: string) => {
    if (selectedDetector) {
      const updatedDetectors = detectors.map(d => 
        d.name === selectedDetector.name 
          ? { ...d, customKeywords: (d.customKeywords || []).filter(k => k !== keyword) }
          : d
      );
      setDetectors(updatedDetectors);
    }
  };

  const handleAddBlockedWord = () => {
    if (newBlockedWord.trim() && selectedDetector) {
      const updatedDetectors = detectors.map(d => 
        d.name === selectedDetector.name 
          ? { ...d, blockedWords: [...(d.blockedWords || []), newBlockedWord.trim()] }
          : d
      );
      setDetectors(updatedDetectors);
      setNewBlockedWord('');
    }
  };

  const handleRemoveBlockedWord = (word: string) => {
    if (selectedDetector) {
      const updatedDetectors = detectors.map(d => 
        d.name === selectedDetector.name 
          ? { ...d, blockedWords: (d.blockedWords || []).filter(w => w !== word) }
          : d
      );
      setDetectors(updatedDetectors);
    }
  };

  const handleUpdateDetectorProperty = (detectorName: string, property: string, value: any) => {
    setDetectors(prev => 
      prev.map(detector => 
        detector.name === detectorName 
          ? { ...detector, [property]: value }
          : detector
      )
    );
  };

  const exportConfig = () => {
    const config = detectors.reduce((acc, detector) => {
      acc[detector.name] = {
        enabled: detector.enabled,
        threshold: detector.threshold,
        customKeywords: detector.customKeywords || [],
        blockedWords: detector.blockedWords || [],
        customResponse: detector.customResponse || '',
        actionType: detector.actionType || 'block',
        severity: detector.severity || 'medium',
      };
      return acc;
    }, {} as any);
    
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'guardrails-config.json';
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Configuration exported successfully');
  };

  const importConfig = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const config = JSON.parse(e.target?.result as string);
          const updatedDetectors = detectors.map(detector => ({
            ...detector,
            ...(config[detector.name] || {})
          }));
          setDetectors(updatedDetectors);
          toast.success('Configuration imported successfully');
        } catch (error) {
          toast.error('Invalid configuration file');
        }
      };
      reader.readAsText(file);
    }
  };

  const formatThreshold = (value: number) => {
    return (value * 100).toFixed(0) + '%';
  };

  const getThresholdColor = (threshold: number) => {
    if (threshold >= 0.8) return '#10b981'; // Green - High security
    if (threshold >= 0.5) return '#f59e0b'; // Yellow - Medium security
    return '#ef4444'; // Red - Low security
  };

  const getThresholdLabel = (threshold: number) => {
    if (threshold >= 0.8) return 'High Security';
    if (threshold >= 0.5) return 'Medium Security';
    return 'Low Security';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Box sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Shield size={28} style={{ color: '#00D4AA' }} />
            <Typography variant="h4" sx={{ fontWeight: 600, color: '#ffffff' }}>
              Guardrails Configuration
            </Typography>
          </Box>
          <Typography variant="body1" sx={{ color: '#a1a1aa', mb: 2 }}>
            Configure and manage AI safety guardrails with advanced customization options.
          </Typography>
          
          <Alert 
            severity="info" 
            icon={<Info size={16} />}
            sx={{ 
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.2)',
              '& .MuiAlert-icon': { color: '#3b82f6' }
            }}
          >
            Real-time configuration changes affect new messages immediately. Settings are temporary and reset when the application restarts.
          </Alert>
        </Box>

        {/* Quick Actions */}
        <Box sx={{ mb: 4 }}>
          <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h6" sx={{ color: '#ffffff', mb: 1 }}>
                    Quick Actions
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                    Manage all guardrails at once
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Tooltip title="Export configuration">
                    <IconButton
                      onClick={exportConfig}
                      sx={{
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        color: '#ffffff',
                        '&:hover': {
                          backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        },
                      }}
                    >
                      <Download size={20} />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Import configuration">
                    <IconButton
                      component="label"
                      sx={{
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        color: '#ffffff',
                        '&:hover': {
                          backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        },
                      }}
                    >
                      <Upload size={20} />
                      <input
                        type="file"
                        accept=".json"
                        hidden
                        onChange={importConfig}
                      />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Reset all settings to defaults">
                    <IconButton
                      onClick={resetToDefaults}
                      sx={{
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        color: '#ffffff',
                        '&:hover': {
                          backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        },
                      }}
                    >
                      <RefreshCw size={20} />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Tabs */}
        <Box sx={{ mb: 3 }}>
          <Tabs
            value={tabValue}
            onChange={(_, newValue) => setTabValue(newValue)}
            sx={{
              '& .MuiTabs-indicator': {
                backgroundColor: '#00D4AA',
              },
              '& .MuiTab-root': {
                color: '#a1a1aa',
                '&.Mui-selected': {
                  color: '#00D4AA',
                },
              },
            }}
          >
            <Tab 
              label="Basic Configuration" 
              icon={<Settings size={16} />}
              iconPosition="start"
            />
            <Tab 
              label="Advanced Settings" 
              icon={<Code size={16} />}
              iconPosition="start"
            />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <TabPanel value={tabValue} index={0}>
          {/* Basic Configuration */}
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
            gap: 3 
          }}>
            {detectors.map((detector, index) => (
              <motion.div
                key={detector.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                  <Card 
                    sx={{ 
                      backgroundColor: detector.enabled 
                        ? 'rgba(255, 255, 255, 0.02)' 
                        : 'rgba(255, 255, 255, 0.01)',
                      border: detector.enabled 
                        ? `1px solid ${detector.color}40` 
                        : '1px solid rgba(255, 255, 255, 0.06)',
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        backgroundColor: 'rgba(255, 255, 255, 0.04)',
                        transform: 'translateY(-2px)',
                      },
                    }}
                  >
                    <CardContent sx={{ p: 3 }}>
                      {/* Detector Header */}
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Box
                            sx={{
                              p: 1.5,
                              borderRadius: '12px',
                              backgroundColor: `${detector.color}20`,
                              color: detector.color,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                          >
                            {detector.icon}
                          </Box>
                          <Box>
                            <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600 }}>
                              {detector.displayName}
                            </Typography>
                            <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                              {detector.description}
                            </Typography>
                          </Box>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Tooltip title="Advanced settings">
                            <IconButton
                              onClick={() => handleAdvancedConfig(detector)}
                              sx={{
                                color: detector.color,
                                '&:hover': {
                                  backgroundColor: `${detector.color}20`,
                                },
                              }}
                            >
                              <Settings size={16} />
                            </IconButton>
                          </Tooltip>
                          <Switch
                            checked={detector.enabled}
                            onChange={(e) => handleToggleDetector(detector.name, e.target.checked)}
                            sx={{
                              '& .MuiSwitch-switchBase.Mui-checked': {
                                color: detector.color,
                              },
                              '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                                backgroundColor: detector.color,
                              },
                            }}
                          />
                        </Box>
                      </Box>

                      {/* Threshold Configuration */}
                      <AnimatePresence>
                        {detector.enabled && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.3 }}
                          >
                            <Divider sx={{ mb: 3, borderColor: 'rgba(255, 255, 255, 0.06)' }} />
                            
                            <Box sx={{ mb: 2 }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                                <Typography variant="subtitle2" sx={{ color: '#ffffff', fontWeight: 500 }}>
                                  Threshold
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Chip
                                    label={getThresholdLabel(detector.threshold)}
                                    size="small"
                                    sx={{
                                      backgroundColor: `${getThresholdColor(detector.threshold)}20`,
                                      color: getThresholdColor(detector.threshold),
                                      fontSize: '0.7rem',
                                    }}
                                  />
                                  <Typography 
                                    variant="h6" 
                                    sx={{ 
                                      color: getThresholdColor(detector.threshold),
                                      fontWeight: 600,
                                      minWidth: '45px',
                                      textAlign: 'right',
                                    }}
                                  >
                                    {formatThreshold(detector.threshold)}
                                  </Typography>
                                </Box>
                              </Box>
                              
                              <Slider
                                value={detector.threshold}
                                onChange={(_, value) => handleThresholdChange(detector.name, value as number)}
                                min={0}
                                max={1}
                                step={0.01}
                                sx={{
                                  color: detector.color,
                                  '& .MuiSlider-thumb': {
                                    backgroundColor: detector.color,
                                    border: `2px solid ${detector.color}`,
                                    '&:hover': {
                                      boxShadow: `0 0 0 8px ${detector.color}20`,
                                    },
                                  },
                                  '& .MuiSlider-track': {
                                    backgroundColor: detector.color,
                                    border: 'none',
                                  },
                                  '& .MuiSlider-rail': {
                                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                                  },
                                }}
                              />
                              
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                                <Typography variant="caption" sx={{ color: '#a1a1aa' }}>
                                  0% (Permissive)
                                </Typography>
                                <Typography variant="caption" sx={{ color: '#a1a1aa' }}>
                                  100% (Strict)
                                </Typography>
                              </Box>
                            </Box>

                            {/* Quick Info */}
                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
                              <Chip
                                label={detector.actionType?.toUpperCase() || 'BLOCK'}
                                size="small"
                                sx={{
                                  backgroundColor: `${detector.color}20`,
                                  color: detector.color,
                                  fontSize: '0.7rem',
                                }}
                              />
                              <Chip
                                label={`${detector.severity?.toUpperCase() || 'MEDIUM'} SEVERITY`}
                                size="small"
                                sx={{
                                  backgroundColor: `${detector.color}20`,
                                  color: detector.color,
                                  fontSize: '0.7rem',
                                }}
                              />
                              {detector.customKeywords && detector.customKeywords.length > 0 && (
                                <Chip
                                  label={`${detector.customKeywords.length} KEYWORDS`}
                                  size="small"
                                  sx={{
                                    backgroundColor: `${detector.color}20`,
                                    color: detector.color,
                                    fontSize: '0.7rem',
                                  }}
                                />
                              )}
                            </Box>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </CardContent>
                  </Card>
              </motion.div>
            ))}
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {/* Advanced Settings */}
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' },
            gap: 3 
          }}>
            {detectors.map((detector, index) => (
              <motion.div
                key={detector.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <Card 
                  sx={{ 
                    backgroundColor: detector.enabled 
                      ? 'rgba(255, 255, 255, 0.02)' 
                      : 'rgba(255, 255, 255, 0.01)',
                    border: detector.enabled 
                      ? `1px solid ${detector.color}40` 
                      : '1px solid rgba(255, 255, 255, 0.06)',
                    opacity: detector.enabled ? 1 : 0.6,
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                      <Box
                        sx={{
                          p: 1.5,
                          borderRadius: '12px',
                          backgroundColor: `${detector.color}20`,
                          color: detector.color,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        {detector.icon}
                      </Box>
                      <Box>
                        <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600 }}>
                          {detector.displayName}
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                          Advanced configuration options
                        </Typography>
                      </Box>
                    </Box>

                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {/* Action Type */}
                      <FormControl fullWidth disabled={!detector.enabled}>
                        <InputLabel sx={{ color: '#a1a1aa' }}>Action Type</InputLabel>
                        <Select
                          value={detector.actionType || 'block'}
                          onChange={(e) => handleUpdateDetectorProperty(detector.name, 'actionType', e.target.value)}
                          sx={{
                            color: '#ffffff',
                            '& .MuiOutlinedInput-notchedOutline': {
                              borderColor: 'rgba(255, 255, 255, 0.1)',
                            },
                            '&:hover .MuiOutlinedInput-notchedOutline': {
                              borderColor: detector.color,
                            },
                          }}
                        >
                          <MenuItem value="block">Block</MenuItem>
                          <MenuItem value="warn">Warn</MenuItem>
                          <MenuItem value="log">Log Only</MenuItem>
                        </Select>
                      </FormControl>

                      {/* Severity */}
                      <FormControl fullWidth disabled={!detector.enabled}>
                        <InputLabel sx={{ color: '#a1a1aa' }}>Severity</InputLabel>
                        <Select
                          value={detector.severity || 'medium'}
                          onChange={(e) => handleUpdateDetectorProperty(detector.name, 'severity', e.target.value)}
                          sx={{
                            color: '#ffffff',
                            '& .MuiOutlinedInput-notchedOutline': {
                              borderColor: 'rgba(255, 255, 255, 0.1)',
                            },
                            '&:hover .MuiOutlinedInput-notchedOutline': {
                              borderColor: detector.color,
                            },
                          }}
                        >
                          <MenuItem value="low">Low</MenuItem>
                          <MenuItem value="medium">Medium</MenuItem>
                          <MenuItem value="high">High</MenuItem>
                        </Select>
                      </FormControl>

                      {/* Custom Response */}
                      <TextField
                        label="Custom Response Message"
                        multiline
                        rows={3}
                        value={detector.customResponse || ''}
                        onChange={(e) => handleUpdateDetectorProperty(detector.name, 'customResponse', e.target.value)}
                        disabled={!detector.enabled}
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            color: '#ffffff',
                            '& fieldset': {
                              borderColor: 'rgba(255, 255, 255, 0.1)',
                            },
                            '&:hover fieldset': {
                              borderColor: detector.color,
                            },
                            '&.Mui-focused fieldset': {
                              borderColor: detector.color,
                            },
                          },
                          '& .MuiInputLabel-root': {
                            color: '#a1a1aa',
                          },
                        }}
                      />

                      {/* Keywords Preview */}
                      <Box>
                        <Typography variant="subtitle2" sx={{ color: '#ffffff', mb: 1 }}>
                          Keywords ({detector.customKeywords?.length || 0})
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, minHeight: '40px' }}>
                          {detector.customKeywords?.slice(0, 3).map((keyword, idx) => (
                            <Chip
                              key={idx}
                              label={keyword}
                              size="small"
                              sx={{
                                backgroundColor: `${detector.color}20`,
                                color: detector.color,
                                fontSize: '0.7rem',
                              }}
                            />
                          ))}
                          {detector.customKeywords && detector.customKeywords.length > 3 && (
                            <Chip
                              label={`+${detector.customKeywords.length - 3} more`}
                              size="small"
                              sx={{
                                backgroundColor: `${detector.color}20`,
                                color: detector.color,
                                fontSize: '0.7rem',
                              }}
                            />
                          )}
                        </Box>
                      </Box>

                      <Button
                        variant="outlined"
                        onClick={() => handleAdvancedConfig(detector)}
                        disabled={!detector.enabled}
                        sx={{
                          borderColor: detector.color,
                          color: detector.color,
                          '&:hover': {
                            borderColor: detector.color,
                            backgroundColor: `${detector.color}20`,
                          },
                        }}
                      >
                        <Settings size={16} style={{ marginRight: '8px' }} />
                        Advanced Settings
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </Box>
        </TabPanel>

        {/* Configuration Summary */}
        <Box sx={{ mt: 4 }}>
          <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                Configuration Summary
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {detectors
                  .filter(d => d.enabled)
                  .map(detector => (
                    <Chip
                      key={detector.name}
                      label={`${detector.displayName}: ${formatThreshold(detector.threshold)}`}
                      size="small"
                      sx={{
                        backgroundColor: `${detector.color}20`,
                        color: detector.color,
                        border: `1px solid ${detector.color}40`,
                      }}
                    />
                  ))}
                {detectors.filter(d => d.enabled).length === 0 && (
                  <Typography variant="body2" sx={{ color: '#a1a1aa', fontStyle: 'italic' }}>
                    No guardrails enabled
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Advanced Configuration Dialog */}
        <Dialog
          open={advancedDialogOpen}
          onClose={() => setAdvancedDialogOpen(false)}
          maxWidth="md"
          fullWidth
          sx={{
            '& .MuiDialog-paper': {
              backgroundColor: 'rgba(0, 0, 0, 0.9)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            },
          }}
        >
          <DialogTitle sx={{ color: '#ffffff', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {selectedDetector?.icon}
              <Typography variant="h6">
                {selectedDetector?.displayName} - Advanced Configuration
              </Typography>
            </Box>
          </DialogTitle>
          <DialogContent sx={{ p: 3, color: '#ffffff' }}>
            {selectedDetector && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
                {/* Custom Keywords */}
                <Box>
                  <Typography variant="h6" sx={{ mb: 2, color: selectedDetector.color }}>
                    Custom Keywords
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <TextField
                      label="Add keyword"
                      value={newKeyword}
                      onChange={(e) => setNewKeyword(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleAddKeyword();
                        }
                      }}
                      sx={{
                        flexGrow: 1,
                        '& .MuiOutlinedInput-root': {
                          color: '#ffffff',
                          '& fieldset': {
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                          },
                          '&:hover fieldset': {
                            borderColor: selectedDetector.color,
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: selectedDetector.color,
                          },
                        },
                        '& .MuiInputLabel-root': {
                          color: '#a1a1aa',
                        },
                      }}
                    />
                    <Button
                      variant="outlined"
                      onClick={handleAddKeyword}
                      disabled={!newKeyword.trim()}
                      sx={{
                        borderColor: selectedDetector.color,
                        color: selectedDetector.color,
                        '&:hover': {
                          borderColor: selectedDetector.color,
                          backgroundColor: `${selectedDetector.color}20`,
                        },
                      }}
                    >
                      <Plus size={16} />
                    </Button>
                  </Box>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, maxHeight: '200px', overflowY: 'auto' }}>
                    {selectedDetector.customKeywords?.map((keyword, idx) => (
                      <Chip
                        key={idx}
                        label={keyword}
                        onDelete={() => handleRemoveKeyword(keyword)}
                        deleteIcon={<X size={14} />}
                        sx={{
                          backgroundColor: `${selectedDetector.color}20`,
                          color: selectedDetector.color,
                          '& .MuiChip-deleteIcon': {
                            color: selectedDetector.color,
                          },
                        }}
                      />
                    ))}
                  </Box>
                </Box>

                {/* Blocked Words */}
                <Box>
                  <Typography variant="h6" sx={{ mb: 2, color: selectedDetector.color }}>
                    Blocked Words/Phrases
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <TextField
                      label="Add blocked word/phrase"
                      value={newBlockedWord}
                      onChange={(e) => setNewBlockedWord(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleAddBlockedWord();
                        }
                      }}
                      sx={{
                        flexGrow: 1,
                        '& .MuiOutlinedInput-root': {
                          color: '#ffffff',
                          '& fieldset': {
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                          },
                          '&:hover fieldset': {
                            borderColor: selectedDetector.color,
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: selectedDetector.color,
                          },
                        },
                        '& .MuiInputLabel-root': {
                          color: '#a1a1aa',
                        },
                      }}
                    />
                    <Button
                      variant="outlined"
                      onClick={handleAddBlockedWord}
                      disabled={!newBlockedWord.trim()}
                      sx={{
                        borderColor: selectedDetector.color,
                        color: selectedDetector.color,
                        '&:hover': {
                          borderColor: selectedDetector.color,
                          backgroundColor: `${selectedDetector.color}20`,
                        },
                      }}
                    >
                      <Plus size={16} />
                    </Button>
                  </Box>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, maxHeight: '200px', overflowY: 'auto' }}>
                    {selectedDetector.blockedWords?.map((word, idx) => (
                      <Chip
                        key={idx}
                        label={word}
                        onDelete={() => handleRemoveBlockedWord(word)}
                        deleteIcon={<X size={14} />}
                        sx={{
                          backgroundColor: `${selectedDetector.color}20`,
                          color: selectedDetector.color,
                          '& .MuiChip-deleteIcon': {
                            color: selectedDetector.color,
                          },
                        }}
                      />
                    ))}
                  </Box>
                </Box>

                {/* Custom Response Template */}
                <Box>
                  <Typography variant="h6" sx={{ mb: 2, color: selectedDetector.color }}>
                    Custom Response Template
                  </Typography>
                  <TextField
                    label="Custom response message"
                    multiline
                    rows={4}
                    value={selectedDetector.customResponse || ''}
                    onChange={(e) => handleUpdateDetectorProperty(selectedDetector.name, 'customResponse', e.target.value)}
                    fullWidth
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        color: '#ffffff',
                        '& fieldset': {
                          borderColor: 'rgba(255, 255, 255, 0.1)',
                        },
                        '&:hover fieldset': {
                          borderColor: selectedDetector.color,
                        },
                        '&.Mui-focused fieldset': {
                          borderColor: selectedDetector.color,
                        },
                      },
                      '& .MuiInputLabel-root': {
                        color: '#a1a1aa',
                      },
                    }}
                  />
                </Box>

                {/* Action Configuration */}
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <FormControl fullWidth>
                    <FormLabel sx={{ color: '#ffffff', mb: 1 }}>Action Type</FormLabel>
                    <RadioGroup
                      value={selectedDetector.actionType || 'block'}
                      onChange={(e) => handleUpdateDetectorProperty(selectedDetector.name, 'actionType', e.target.value)}
                    >
                      <FormControlLabel
                        value="block"
                        control={<Radio sx={{ color: selectedDetector.color }} />}
                        label="Block"
                        sx={{ color: '#ffffff' }}
                      />
                      <FormControlLabel
                        value="warn"
                        control={<Radio sx={{ color: selectedDetector.color }} />}
                        label="Warn"
                        sx={{ color: '#ffffff' }}
                      />
                      <FormControlLabel
                        value="log"
                        control={<Radio sx={{ color: selectedDetector.color }} />}
                        label="Log Only"
                        sx={{ color: '#ffffff' }}
                      />
                    </RadioGroup>
                  </FormControl>

                  <FormControl fullWidth>
                    <FormLabel sx={{ color: '#ffffff', mb: 1 }}>Severity Level</FormLabel>
                    <RadioGroup
                      value={selectedDetector.severity || 'medium'}
                      onChange={(e) => handleUpdateDetectorProperty(selectedDetector.name, 'severity', e.target.value)}
                    >
                      <FormControlLabel
                        value="low"
                        control={<Radio sx={{ color: selectedDetector.color }} />}
                        label="Low"
                        sx={{ color: '#ffffff' }}
                      />
                      <FormControlLabel
                        value="medium"
                        control={<Radio sx={{ color: selectedDetector.color }} />}
                        label="Medium"
                        sx={{ color: '#ffffff' }}
                      />
                      <FormControlLabel
                        value="high"
                        control={<Radio sx={{ color: selectedDetector.color }} />}
                        label="High"
                        sx={{ color: '#ffffff' }}
                      />
                    </RadioGroup>
                  </FormControl>
                </Box>
              </Box>
            )}
          </DialogContent>
          <DialogActions sx={{ p: 3, borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
            <Button
              onClick={() => setAdvancedDialogOpen(false)}
              sx={{
                color: '#a1a1aa',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={() => {
                setAdvancedDialogOpen(false);
                toast.success(`${selectedDetector?.displayName} configuration saved`);
              }}
              variant="contained"
              sx={{
                backgroundColor: selectedDetector?.color,
                '&:hover': {
                  backgroundColor: selectedDetector?.color,
                  opacity: 0.8,
                },
              }}
            >
              <Save size={16} style={{ marginRight: '8px' }} />
              Save Configuration
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </motion.div>
  );
};

export default GuardrailsConfig;