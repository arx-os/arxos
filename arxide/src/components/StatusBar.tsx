import React from 'react'
import { 
  Box, 
  Paper, 
  Typography, 
  Chip,
  LinearProgress
} from '@mui/material'
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon
} from '@mui/icons-material'

export const StatusBar: React.FC = () => {
  const status = 'ready' // 'ready' | 'building' | 'error'
  const progress = 0

  const getStatusIcon = () => {
    switch (status) {
      case 'ready':
        return <SuccessIcon fontSize="small" color="success" />
      case 'building':
        return <WarningIcon fontSize="small" color="warning" />
      case 'error':
        return <ErrorIcon fontSize="small" color="error" />
      default:
        return <SuccessIcon fontSize="small" color="success" />
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'ready':
        return 'Ready'
      case 'building':
        return 'Building...'
      case 'error':
        return 'Error'
      default:
        return 'Ready'
    }
  }

  return (
    <Paper 
      sx={{ 
        height: 32, 
        display: 'flex', 
        alignItems: 'center',
        px: 2,
        borderRadius: 0,
        borderTop: 1,
        borderColor: 'divider'
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {getStatusIcon()}
        <Typography variant="caption" color="text.secondary">
          {getStatusText()}
        </Typography>
      </Box>

      <Box sx={{ flexGrow: 1 }} />

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Chip 
          label="SVGX" 
          size="small" 
          variant="outlined"
          sx={{ height: 20 }}
        />
        <Typography variant="caption" color="text.secondary">
          Line 1, Col 1
        </Typography>
      </Box>

      {status === 'building' && (
        <Box sx={{ width: 100, ml: 2 }}>
          <LinearProgress 
            variant="determinate" 
            value={progress} 
            size="small"
          />
        </Box>
      )}
    </Paper>
  )
} 