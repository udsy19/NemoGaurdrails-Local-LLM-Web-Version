import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Alert,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  AlertTriangle,
  Zap,
  Settings,
  X,
  ArrowRight,
  Wifi,
  Server,
} from 'lucide-react';

interface PortConflictDialogProps {
  open: boolean;
  onClose: () => void;
  provider: {
    id: string;
    display_name: string;
    port: number;
  } | null;
  conflictData: {
    port_status: {
      available: boolean;
      port: number;
      in_use_by: string | null;
      process_info: any;
      can_override: boolean;
    };
    suggested_actions: string[];
  } | null;
  onForceEnable: () => void;
  onUseNextPort: () => void;
}

const PortConflictDialog: React.FC<PortConflictDialogProps> = ({
  open,
  onClose,
  provider,
  conflictData,
  onForceEnable,
  onUseNextPort,
}) => {
  // Don't render if provider or conflictData is null
  if (!provider || !conflictData) {
    return null;
  }
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          backgroundColor: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '12px',
        },
      }}
    >
      <DialogTitle sx={{ color: '#ffffff', display: 'flex', alignItems: 'center', gap: 2 }}>
        <AlertTriangle size={24} style={{ color: '#f59e0b' }} />
        Port Conflict Detected
      </DialogTitle>

      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Conflict Information */}
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Box>
              <Typography variant="body1" sx={{ fontWeight: 600, mb: 1 }}>
                Cannot enable {provider.display_name} on port {provider.port}
              </Typography>
              <Typography variant="body2">
                Port {provider.port} is currently in use by: {conflictData.port_status.in_use_by}
              </Typography>
            </Box>
          </Alert>

          {/* Current Provider Info */}
          <Box sx={{ 
            p: 2, 
            backgroundColor: 'rgba(255, 255, 255, 0.02)', 
            borderRadius: '8px',
            border: '1px solid rgba(255, 255, 255, 0.06)'
          }}>
            <Typography variant="subtitle1" sx={{ color: '#ffffff', mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Server size={16} />
              {provider.display_name}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip
                label={`Port ${provider.port}`}
                size="small"
                sx={{ backgroundColor: '#f59e0b20', color: '#f59e0b' }}
              />
              <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                Proxy server port
              </Typography>
            </Box>
          </Box>

          {/* Conflict Details */}
          <Box sx={{ 
            p: 2, 
            backgroundColor: 'rgba(239, 68, 68, 0.05)', 
            borderRadius: '8px',
            border: '1px solid rgba(239, 68, 68, 0.2)'
          }}>
            <Typography variant="subtitle1" sx={{ color: '#ef4444', mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <AlertTriangle size={16} />
              Conflict Details
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography variant="body2" sx={{ color: '#ffffff' }}>
                <strong>Port:</strong> {conflictData.port_status.port}
              </Typography>
              <Typography variant="body2" sx={{ color: '#ffffff' }}>
                <strong>Used by:</strong> {conflictData.port_status.in_use_by}
              </Typography>
              {conflictData.port_status.process_info && (
                <Typography variant="body2" sx={{ color: '#ffffff' }}>
                  <strong>Process:</strong> {conflictData.port_status.process_info.name} (PID: {conflictData.port_status.process_info.pid})
                </Typography>
              )}
              <Typography variant="body2" sx={{ color: '#ffffff' }}>
                <strong>Can override:</strong> {conflictData.port_status.can_override ? 'Yes' : 'No'}
              </Typography>
            </Box>
          </Box>

          <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.06)' }} />

          {/* Resolution Options */}
          <Box>
            <Typography variant="subtitle1" sx={{ color: '#ffffff', mb: 2 }}>
              Choose how to resolve this conflict:
            </Typography>
            
            <List sx={{ p: 0 }}>
              {/* Force Enable Option */}
              <ListItem
                sx={{
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 255, 255, 0.06)',
                  mb: 1,
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: 'rgba(239, 68, 68, 0.05)',
                    border: '1px solid rgba(239, 68, 68, 0.2)',
                  },
                }}
                onClick={onForceEnable}
              >
                <ListItemIcon>
                  <Zap size={20} style={{ color: '#ef4444' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Force Enable (Kill Process)"
                  secondary="Terminate the conflicting process and start the proxy server"
                  primaryTypographyProps={{ color: '#ffffff' }}
                  secondaryTypographyProps={{ color: '#a1a1aa' }}
                />
                <ArrowRight size={16} style={{ color: '#a1a1aa' }} />
              </ListItem>

              {/* Use Next Available Port Option */}
              <ListItem
                sx={{
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 255, 255, 0.06)',
                  mb: 1,
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: 'rgba(16, 185, 129, 0.05)',
                    border: '1px solid rgba(16, 185, 129, 0.2)',
                  },
                }}
                onClick={onUseNextPort}
              >
                <ListItemIcon>
                  <Settings size={20} style={{ color: '#10b981' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Use Next Available Port"
                  secondary="Find and use the next available port automatically"
                  primaryTypographyProps={{ color: '#ffffff' }}
                  secondaryTypographyProps={{ color: '#a1a1aa' }}
                />
                <ArrowRight size={16} style={{ color: '#a1a1aa' }} />
              </ListItem>

              {/* Cancel Option */}
              <ListItem
                sx={{
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 255, 255, 0.06)',
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: 'rgba(107, 114, 128, 0.05)',
                    border: '1px solid rgba(107, 114, 128, 0.2)',
                  },
                }}
                onClick={onClose}
              >
                <ListItemIcon>
                  <X size={20} style={{ color: '#6b7280' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Cancel"
                  secondary="Keep the provider disabled and resolve manually"
                  primaryTypographyProps={{ color: '#ffffff' }}
                  secondaryTypographyProps={{ color: '#a1a1aa' }}
                />
                <ArrowRight size={16} style={{ color: '#a1a1aa' }} />
              </ListItem>
            </List>
          </Box>
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 3, justifyContent: 'flex-end' }}>
        <Button
          onClick={onClose}
          sx={{ color: '#6b7280', '&:hover': { backgroundColor: 'rgba(107, 114, 128, 0.1)' } }}
        >
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PortConflictDialog;