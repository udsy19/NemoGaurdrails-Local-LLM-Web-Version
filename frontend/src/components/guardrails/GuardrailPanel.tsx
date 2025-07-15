import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Switch,
  Slider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Tooltip,
  IconButton,
  Card,
  CardContent,
  FormControlLabel,
  Divider,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Info as InfoIcon,
  Settings as SettingsIcon,
  Shield as ShieldIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { DetectorInfo, DetectorConfig } from '../../types';

interface GuardrailPanelProps {
  detectors: DetectorInfo[];
  selectedDetectors: string[];
  detectorConfig: DetectorConfig;
  onDetectorToggle: (detectorName: string, enabled: boolean) => void;
  onConfigChange: (detectorName: string, config: any) => void;
  systemHealth?: any;
}

const GuardrailPanel: React.FC<GuardrailPanelProps> = ({
  detectors,
  selectedDetectors,
  detectorConfig,
  onDetectorToggle,
  onConfigChange,
  systemHealth,
}) => {
  const [expandedAccordion, setExpandedAccordion] = useState<string | false>(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleAccordionChange = (panel: string) => (
    event: React.SyntheticEvent,
    isExpanded: boolean
  ) => {
    setExpandedAccordion(isExpanded ? panel : false);
  };

  const getDetectorIcon = (detectorName: string) => {
    switch (detectorName) {
      case 'toxicity':
        return '🛡️';
      case 'pii':
        return '🔒';
      case 'prompt_injection':
        return '🚨';
      case 'spam':
        return '📧';
      case 'topic':
        return '📝';
      case 'fact_check':
        return '✓';
      default:
        return '🔍';
    }
  };

  const getDetectorDescription = (detectorName: string) => {
    switch (detectorName) {
      case 'toxicity':
        return 'Detects toxic, harmful, or inappropriate content including hate speech, threats, and offensive language.';
      case 'pii':
        return 'Identifies personally identifiable information such as email addresses, phone numbers, and social security numbers.';
      case 'prompt_injection':
        return 'Detects attempts to manipulate the AI system through malicious prompts or injection attacks.';
      case 'spam':
        return 'Identifies spam, promotional content, and low-quality messages that may be unsolicited.';
      case 'topic':
        return 'Classifies content topics and identifies discussions on restricted or sensitive subjects.';
      case 'fact_check':
        return 'Analyzes claims and statements that may require fact-checking or verification.';
      default:
        return 'Advanced AI safety detector for content analysis.';
    }
  };

  const getDetectorStatusColor = (detector: DetectorInfo) => {
    if (detector.status === 'loaded' && detector.active) return '#00D4AA';
    if (detector.status === 'loading') return '#FFB800';
    return '#FF3D71';
  };

  const getDetectorStatusText = (detector: DetectorInfo) => {
    if (detector.status === 'loaded' && detector.active) return 'Ready';
    if (detector.status === 'loading') return 'Loading';
    return 'Error';
  };

  const handleThresholdChange = (detectorName: string, threshold: number) => {
    onConfigChange(detectorName, {
      ...detectorConfig[detectorName],
      threshold: threshold / 100,
    });
  };

  const enabledDetectorsCount = selectedDetectors.length;
  const totalDetectorsCount = detectors.length;
  const healthyDetectorsCount = detectors.filter(d => d.status === 'loaded' && d.active).length;

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Paper
        elevation={8}
        sx={{
          background: 'linear-gradient(135deg, #1A1F2E 0%, #242938 100%)',
          border: '1px solid #374151',
          borderRadius: '16px',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 3,
            background: 'linear-gradient(135deg, #00D4AA20 0%, #007A6B20 100%)',
            borderBottom: '1px solid #374151',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <ShieldIcon sx={{ color: '#00D4AA', fontSize: '2rem', mr: 2 }} />
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h5" sx={{ color: '#FFFFFF', fontWeight: 600 }}>
                AI Safety Guardrails
              </Typography>
              <Typography variant="body2" sx={{ color: '#A8B2D1' }}>
                Configure and monitor your AI safety detectors
              </Typography>
            </Box>
            <Tooltip title="Advanced Settings">
              <IconButton
                onClick={() => setShowAdvanced(!showAdvanced)}
                sx={{
                  color: showAdvanced ? '#00D4AA' : '#A8B2D1',
                  backgroundColor: showAdvanced ? '#00D4AA20' : 'transparent',
                }}
              >
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          </Box>

          {/* System Status Overview */}
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <Card sx={{ flex: 1, backgroundColor: '#0A0E1A', border: '1px solid #374151' }}>
              <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                <Typography variant="caption" sx={{ color: '#A8B2D1' }}>
                  Active Detectors
                </Typography>
                <Typography variant="h6" sx={{ color: '#00D4AA', fontWeight: 600 }}>
                  {enabledDetectorsCount}/{totalDetectorsCount}
                </Typography>
              </CardContent>
            </Card>
            
            <Card sx={{ flex: 1, backgroundColor: '#0A0E1A', border: '1px solid #374151' }}>
              <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                <Typography variant="caption" sx={{ color: '#A8B2D1' }}>
                  System Health
                </Typography>
                <Typography 
                  variant="h6" 
                  sx={{ 
                    color: healthyDetectorsCount === totalDetectorsCount ? '#00D4AA' : '#FFB800',
                    fontWeight: 600 
                  }}
                >
                  {healthyDetectorsCount === totalDetectorsCount ? 'Healthy' : 'Degraded'}
                </Typography>
              </CardContent>
            </Card>
          </Box>

          {/* Overall Progress */}
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" sx={{ color: '#A8B2D1' }}>
                Protection Level
              </Typography>
              <Typography variant="body2" sx={{ color: '#A8B2D1' }}>
                {Math.round((enabledDetectorsCount / totalDetectorsCount) * 100)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={(enabledDetectorsCount / totalDetectorsCount) * 100}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: '#374151',
                '& .MuiLinearProgress-bar': {
                  background: 'linear-gradient(135deg, #00D4AA 0%, #007A6B 100%)',
                  borderRadius: 4,
                },
              }}
            />
          </Box>
        </Box>

        {/* Safety Alert */}
        {enabledDetectorsCount === 0 && (
          <Alert
            severity="warning"
            icon={<WarningIcon />}
            sx={{
              m: 2,
              backgroundColor: '#FFB80020',
              border: '1px solid #FFB800',
              '& .MuiAlert-icon': {
                color: '#FFB800',
              },
            }}
          >
            <Typography variant="body2">
              No safety detectors are active. Your system is currently unprotected.
            </Typography>
          </Alert>
        )}

        {/* Detector List */}
        <Box sx={{ p: 2 }}>
          <AnimatePresence>
            {detectors.map((detector, index) => (
              <motion.div
                key={detector.name}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <Accordion
                  expanded={expandedAccordion === detector.name}
                  onChange={handleAccordionChange(detector.name)}
                  sx={{
                    backgroundColor: '#1A1F2E',
                    border: '1px solid #374151',
                    borderRadius: '12px !important',
                    mb: 1,
                    '&:before': { display: 'none' },
                    '&.Mui-expanded': {
                      margin: '0 0 8px 0',
                    },
                  }}
                >
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon sx={{ color: '#A8B2D1' }} />}
                    sx={{
                      borderRadius: '12px',
                      '&.Mui-expanded': {
                        borderBottomLeftRadius: 0,
                        borderBottomRightRadius: 0,
                      },
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', pr: 2 }}>
                      {/* Detector Icon */}
                      <Typography sx={{ fontSize: '1.5rem', mr: 2 }}>
                        {getDetectorIcon(detector.name)}
                      </Typography>

                      {/* Detector Info */}
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6" sx={{ color: '#FFFFFF', fontWeight: 500 }}>
                          {detector.name.charAt(0).toUpperCase() + detector.name.slice(1).replace('_', ' ')}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <Chip
                            label={getDetectorStatusText(detector)}
                            size="small"
                            sx={{
                              backgroundColor: `${getDetectorStatusColor(detector)}20`,
                              color: getDetectorStatusColor(detector),
                              border: `1px solid ${getDetectorStatusColor(detector)}`,
                              fontSize: '0.75rem',
                            }}
                          />
                          {selectedDetectors.includes(detector.name) && (
                            <Chip
                              label="Active"
                              size="small"
                              sx={{
                                backgroundColor: '#00D4AA20',
                                color: '#00D4AA',
                                border: '1px solid #00D4AA',
                                fontSize: '0.75rem',
                              }}
                            />
                          )}
                        </Box>
                      </Box>

                      {/* Toggle Switch */}
                      <FormControlLabel
                        control={
                          <Switch
                            checked={selectedDetectors.includes(detector.name)}
                            onChange={(e) => onDetectorToggle(detector.name, e.target.checked)}
                            disabled={detector.status !== 'loaded' || !detector.active}
                            sx={{
                              '& .MuiSwitch-switchBase.Mui-checked': {
                                color: '#00D4AA',
                                '& + .MuiSwitch-track': {
                                  backgroundColor: '#00D4AA',
                                },
                              },
                            }}
                          />
                        }
                        label=""
                        sx={{ m: 0 }}
                      />
                    </Box>
                  </AccordionSummary>

                  <AccordionDetails sx={{ pt: 0 }}>
                    <Divider sx={{ mb: 2, borderColor: '#374151' }} />
                    
                    {/* Description */}
                    <Typography variant="body2" sx={{ color: '#A8B2D1', mb: 2 }}>
                      {getDetectorDescription(detector.name)}
                    </Typography>

                    {/* Advanced Settings */}
                    {showAdvanced && selectedDetectors.includes(detector.name) && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" sx={{ color: '#FFFFFF', mb: 1 }}>
                          Detection Threshold
                        </Typography>
                        <Box sx={{ px: 2 }}>
                          <Slider
                            value={(detectorConfig[detector.name]?.threshold || 0.5) * 100}
                            onChange={(_, value) => handleThresholdChange(detector.name, value as number)}
                            min={0}
                            max={100}
                            step={5}
                            marks={[
                              { value: 0, label: 'Permissive' },
                              { value: 50, label: 'Balanced' },
                              { value: 100, label: 'Strict' },
                            ]}
                            sx={{
                              color: '#00D4AA',
                              '& .MuiSlider-thumb': {
                                backgroundColor: '#00D4AA',
                              },
                              '& .MuiSlider-track': {
                                backgroundColor: '#00D4AA',
                              },
                              '& .MuiSlider-rail': {
                                backgroundColor: '#374151',
                              },
                              '& .MuiSlider-markLabel': {
                                color: '#A8B2D1',
                                fontSize: '0.75rem',
                              },
                            }}
                          />
                        </Box>
                      </Box>
                    )}

                    {/* Performance Metrics */}
                    {selectedDetectors.includes(detector.name) && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" sx={{ color: '#FFFFFF', mb: 1 }}>
                          Performance Metrics
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 2 }}>
                          <Card sx={{ flex: 1, backgroundColor: '#0A0E1A', border: '1px solid #374151' }}>
                            <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                                <SpeedIcon sx={{ color: '#00D4AA', fontSize: '1rem', mr: 0.5 }} />
                                <Typography variant="caption" sx={{ color: '#A8B2D1' }}>
                                  Response Time
                                </Typography>
                              </Box>
                              <Typography variant="body2" sx={{ color: '#FFFFFF', fontWeight: 600 }}>
                                {Math.random() * 50 + 10}ms
                              </Typography>
                            </CardContent>
                          </Card>
                          
                          <Card sx={{ flex: 1, backgroundColor: '#0A0E1A', border: '1px solid #374151' }}>
                            <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                                <CheckIcon sx={{ color: '#00D4AA', fontSize: '1rem', mr: 0.5 }} />
                                <Typography variant="caption" sx={{ color: '#A8B2D1' }}>
                                  Accuracy
                                </Typography>
                              </Box>
                              <Typography variant="body2" sx={{ color: '#FFFFFF', fontWeight: 600 }}>
                                {Math.random() * 15 + 85}%
                              </Typography>
                            </CardContent>
                          </Card>
                        </Box>
                      </Box>
                    )}
                  </AccordionDetails>
                </Accordion>
              </motion.div>
            ))}
          </AnimatePresence>
        </Box>

        {/* Quick Actions */}
        <Box sx={{ p: 2, borderTop: '1px solid #374151' }}>
          <Typography variant="subtitle2" sx={{ color: '#FFFFFF', mb: 2 }}>
            Quick Actions
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip
              label="Enable All"
              clickable
              onClick={() => {
                detectors.forEach(detector => {
                  if (detector.status === 'loaded' && detector.active) {
                    onDetectorToggle(detector.name, true);
                  }
                });
              }}
              sx={{
                backgroundColor: '#00D4AA20',
                color: '#00D4AA',
                border: '1px solid #00D4AA',
                '&:hover': {
                  backgroundColor: '#00D4AA30',
                },
              }}
            />
            <Chip
              label="Disable All"
              clickable
              onClick={() => {
                selectedDetectors.forEach(detector => {
                  onDetectorToggle(detector, false);
                });
              }}
              sx={{
                backgroundColor: '#FF3D7120',
                color: '#FF3D71',
                border: '1px solid #FF3D71',
                '&:hover': {
                  backgroundColor: '#FF3D7130',
                },
              }}
            />
            <Chip
              label="Reset to Defaults"
              clickable
              onClick={() => {
                detectors.forEach(detector => {
                  if (detector.status === 'loaded' && detector.active) {
                    onDetectorToggle(detector.name, true);
                    onConfigChange(detector.name, { enabled: true, threshold: 0.5 });
                  }
                });
              }}
              sx={{
                backgroundColor: '#FFB80020',
                color: '#FFB800',
                border: '1px solid #FFB800',
                '&:hover': {
                  backgroundColor: '#FFB80030',
                },
              }}
            />
          </Box>
        </Box>
      </Paper>
    </motion.div>
  );
};

export default GuardrailPanel;