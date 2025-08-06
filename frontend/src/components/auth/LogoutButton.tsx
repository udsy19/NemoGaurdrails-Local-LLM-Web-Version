import React, { useState } from 'react';
import {
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Fade,
} from '@mui/material';
import { ExitToApp, Person, Security } from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAuthContext } from '../../contexts/AuthContext';

interface LogoutButtonProps {
  variant?: 'icon' | 'button';
  size?: 'small' | 'medium' | 'large';
  showUserInfo?: boolean;
}

const LogoutButton: React.FC<LogoutButtonProps> = ({
  variant = 'icon',
  size = 'medium',
  showUserInfo = true,
}) => {
  const { logout, session, isAuthenticated } = useAuthContext();
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogoutClick = () => {
    setShowConfirm(true);
  };

  const handleConfirmLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
      setShowConfirm(false);
    } catch (err) {
      console.error('Logout failed:', err);
    } finally {
      setIsLoggingOut(false);
    }
  };

  const handleCancelLogout = () => {
    setShowConfirm(false);
  };

  if (!isAuthenticated) {
    return null;
  }

  const userEmail = session?.email || 'User';
  const isLicenseValidated = true; // This should come from auth context

  const LogoutIcon = () => (
    <motion.div
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
    >
      <Tooltip title={`Logout ${userEmail}`}>
        <IconButton
          onClick={handleLogoutClick}
          size={size}
          sx={{
            color: 'rgba(255, 255, 255, 0.8)',
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              borderColor: '#00D4AA',
              color: '#00D4AA',
            },
            transition: 'all 0.2s ease-out',
          }}
        >
          <ExitToApp />
        </IconButton>
      </Tooltip>
    </motion.div>
  );

  const LogoutButtonComponent = () => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <Button
        onClick={handleLogoutClick}
        startIcon={<ExitToApp />}
        variant="outlined"
        size={size}
        sx={{
          color: 'rgba(255, 255, 255, 0.8)',
          borderColor: 'rgba(255, 255, 255, 0.2)',
          '&:hover': {
            borderColor: '#00D4AA',
            backgroundColor: 'rgba(0, 212, 170, 0.1)',
            color: '#00D4AA',
          },
          textTransform: 'none',
        }}
      >
        Logout
      </Button>
    </motion.div>
  );

  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {showUserInfo && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Person sx={{ fontSize: 16, color: 'rgba(255, 255, 255, 0.6)' }} />
            <Typography
              variant="caption"
              sx={{
                color: 'rgba(255, 255, 255, 0.8)',
                fontWeight: 500,
              }}
            >
              {userEmail}
            </Typography>
            {isLicenseValidated && (
              <Security
                sx={{
                  fontSize: 14,
                  color: '#22c55e',
                }}
              />
            )}
          </Box>
        )}
        
        {variant === 'icon' ? <LogoutIcon /> : <LogoutButtonComponent />}
      </Box>

      {/* Logout Confirmation Dialog */}
      <Dialog
        open={showConfirm}
        onClose={handleCancelLogout}
        PaperProps={{
          sx: {
            background: 'rgba(255, 255, 255, 0.02)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
            color: '#ffffff',
          },
        }}
      >
        <DialogTitle sx={{ color: '#ffffff', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ExitToApp sx={{ color: '#00D4AA' }} />
            Confirm Logout
          </Box>
        </DialogTitle>
        
        <DialogContent sx={{ py: 3 }}>
          <Typography sx={{ color: 'rgba(255, 255, 255, 0.8)', mb: 2 }}>
            Are you sure you want to logout from the AI Safety System?
          </Typography>
          
          <Box
            sx={{
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 1,
              p: 2,
              mt: 2,
            }}
          >
            <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
              <strong>Current Session:</strong> {userEmail}
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
              <strong>Status:</strong> {isLicenseValidated ? 'Licensed' : 'Unlicensed'}
            </Typography>
          </Box>
        </DialogContent>
        
        <DialogActions sx={{ p: 3, borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <Button
            onClick={handleCancelLogout}
            variant="outlined"
            disabled={isLoggingOut}
            sx={{
              borderColor: 'rgba(255, 255, 255, 0.2)',
              color: 'rgba(255, 255, 255, 0.8)',
              '&:hover': {
                borderColor: 'rgba(255, 255, 255, 0.4)',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
              },
            }}
          >
            Cancel
          </Button>
          
          <motion.div
            whileHover={!isLoggingOut ? { scale: 1.05 } : {}}
            whileTap={!isLoggingOut ? { scale: 0.95 } : {}}
          >
            <Button
              onClick={handleConfirmLogout}
              variant="contained"
              disabled={isLoggingOut}
              startIcon={!isLoggingOut ? <ExitToApp /> : null}
              sx={{
                background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                color: '#ffffff',
                '&:hover': {
                  background: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
                },
                '&:disabled': {
                  background: 'rgba(255, 255, 255, 0.1)',
                  color: 'rgba(255, 255, 255, 0.3)',
                },
              }}
            >
              {isLoggingOut ? 'Logging out...' : 'Logout'}
            </Button>
          </motion.div>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default LogoutButton;